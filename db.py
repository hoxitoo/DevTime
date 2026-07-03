"""
DevTime v7 — слой базы данных.
Весь SQL только здесь.
"""

import sqlite3
import csv
import logging
from datetime import date, timedelta
from pathlib import Path

log = logging.getLogger(__name__)

DATA_DIR = Path.home() / ".devtime"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH  = DATA_DIR / "devtime.db"


class DB:
    def __init__(self, path: str = str(DB_PATH), check_same_thread: bool = True):
        # check_same_thread=False нужен API-слою (FastAPI обслуживает запросы
        # из пула потоков); сериализацию записи обеспечивает api.server._db_lock.
        self.conn = sqlite3.connect(path, check_same_thread=check_same_thread)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def close(self):
        self.conn.close()

    # ── Миграции ─────────────────────────────────────────────────────────────
    def _migrate(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS activities (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            emoji     TEXT DEFAULT '💻',
            color     TEXT DEFAULT '#4fc3f7',
            total_s   INTEGER DEFAULT 0,
            goal_h    REAL DEFAULT 0,
            day_plan  TEXT DEFAULT '',
            status    TEXT DEFAULT 'active',
            created   TEXT DEFAULT (date('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id  INTEGER REFERENCES activities(id) ON DELETE CASCADE,
            started_at   TEXT,
            ended_at     TEXT,
            duration_s   INTEGER DEFAULT 0,
            note         TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions(activity_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_ended    ON sessions(ended_at);
        """)
        safe_alters = [
            "ALTER TABLE activities ADD COLUMN color TEXT DEFAULT '#4fc3f7'",
            "ALTER TABLE activities ADD COLUMN day_plan TEXT DEFAULT ''",
            "ALTER TABLE activities ADD COLUMN status TEXT DEFAULT 'active'",
            "ALTER TABLE sessions ADD COLUMN note TEXT DEFAULT ''",
        ]
        for stmt in safe_alters:
            try:
                self.conn.execute(stmt)
            except sqlite3.OperationalError:
                pass
        self.conn.commit()

    # ── Активности ───────────────────────────────────────────────────────────
    def get_activities(self, include_deleted: bool = False) -> list:
        if include_deleted:
            return self.conn.execute(
                "SELECT * FROM activities ORDER BY total_s DESC, id DESC"
            ).fetchall()
        return self.conn.execute(
            "SELECT * FROM activities WHERE status != 'deleted' ORDER BY total_s DESC, id DESC"
        ).fetchall()

    def get_activity(self, aid: int):
        return self.conn.execute(
            "SELECT * FROM activities WHERE id=?", (aid,)
        ).fetchone()

    def add_activity(self, name: str, emoji: str, color: str, goal_h: float = 0) -> int:
        try:
            cur = self.conn.execute(
                "INSERT INTO activities(name, emoji, color, goal_h, status) VALUES(?,?,?,?,?)",
                (name, emoji, color, goal_h, "active")
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            log.error("add_activity failed: %s", e)
            raise

    def update_activity(self, aid: int, name: str, emoji: str, color: str, goal_h: float):
        try:
            self.conn.execute(
                "UPDATE activities SET name=?, emoji=?, color=?, goal_h=? WHERE id=?",
                (name, emoji, color, goal_h, aid)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            log.error("update_activity failed: %s", e)
            raise

    def set_activity_status(self, aid: int, status: str):
        try:
            self.conn.execute("UPDATE activities SET status=? WHERE id=?", (status, aid))
            self.conn.commit()
        except sqlite3.Error as e:
            log.error("set_activity_status failed: %s", e)
            raise

    def delete_activity(self, aid: int):
        """Мягкое удаление: проект остаётся в библиотеке со статусом deleted."""
        self.set_activity_status(aid, "deleted")

    def restore_activity(self, aid: int):
        self.set_activity_status(aid, "active")

    def complete_activity(self, aid: int):
        self.set_activity_status(aid, "completed")

    def reopen_activity(self, aid: int):
        self.set_activity_status(aid, "active")

    def update_day_plan(self, aid: int, text: str):
        try:
            self.conn.execute(
                "UPDATE activities SET day_plan=? WHERE id=?", (text, aid)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            log.error("update_day_plan failed: %s", e)
            raise

    # ── Сессии ───────────────────────────────────────────────────────────────
    def log_session(self, activity_id: int, started_at: str, ended_at: str,
                    duration_s: int, note: str = "") -> int:
        try:
            cur = self.conn.execute(
                "INSERT INTO sessions(activity_id,started_at,ended_at,duration_s,note)"
                " VALUES(?,?,?,?,?)",
                (activity_id, started_at, ended_at, duration_s, note)
            )
            self.conn.execute(
                "UPDATE activities SET total_s=total_s+? WHERE id=?",
                (duration_s, activity_id)
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            log.error("log_session failed: %s", e)
            raise

    def get_sessions(self, activity_id: int, limit: int = 50) -> list:
        return self.conn.execute("""
            SELECT * FROM sessions WHERE activity_id=?
            ORDER BY started_at DESC LIMIT ?
        """, (activity_id, limit)).fetchall()

    def update_session_note(self, sid: int, note: str):
        try:
            self.conn.execute(
                "UPDATE sessions SET note=? WHERE id=?", (note, sid)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            log.error("update_session_note failed: %s", e)
            raise

    def get_session_note(self, sid: int) -> str:
        row = self.conn.execute(
            "SELECT note FROM sessions WHERE id=?", (sid,)
        ).fetchone()
        return row["note"] if row else ""

    # ── Статистика по проекту ────────────────────────────────────────────────
    def get_daily_totals(self, activity_id: int, days: int = 28) -> list:
        return self.conn.execute("""
            SELECT date(ended_at) as day, SUM(duration_s) as total
            FROM sessions
            WHERE activity_id=? AND ended_at >= date('now', ?, 'localtime')
            GROUP BY day ORDER BY day
        """, (activity_id, f"-{days} days")).fetchall()

    def get_streak(self, activity_id: int) -> int:
        rows = self.conn.execute("""
            SELECT DISTINCT date(ended_at) as day
            FROM sessions WHERE activity_id=?
            ORDER BY day DESC
        """, (activity_id,)).fetchall()
        if not rows:
            return 0
        days = {row["day"] for row in rows}
        today = date.today()
        # Грейс: серия жива, если работал сегодня ИЛИ вчера.
        if str(today) in days:
            cur = today
        elif str(today - timedelta(days=1)) in days:
            cur = today - timedelta(days=1)
        else:
            return 0
        streak = 0
        while str(cur) in days:
            streak += 1
            cur -= timedelta(days=1)
        return streak

    def get_week_total(self, activity_id: int) -> int:
        row = self.conn.execute("""
            SELECT COALESCE(SUM(duration_s), 0) as t FROM sessions
            WHERE activity_id=? AND ended_at >= date('now', '-7 days', 'localtime')
        """, (activity_id,)).fetchone()
        return row["t"] or 0

    def get_today_total(self, activity_id: int) -> int:
        row = self.conn.execute("""
            SELECT COALESCE(SUM(duration_s), 0) as t FROM sessions
            WHERE activity_id=? AND date(ended_at)=date('now', 'localtime')
        """, (activity_id,)).fetchone()
        return row["t"] or 0

    def get_session_count(self, activity_id: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) as c FROM sessions WHERE activity_id=?",
            (activity_id,)
        ).fetchone()
        return row["c"] if row else 0

    # ── Общая статистика ─────────────────────────────────────────────────────
    def get_all_daily_totals(self, days: int = 28) -> list:
        return self.conn.execute("""
            SELECT date(ended_at) as day, SUM(duration_s) as total
            FROM sessions
            WHERE ended_at >= date('now', ?, 'localtime')
            GROUP BY day ORDER BY day
        """, (f"-{days} days",)).fetchall()

    def get_overall_stats(self) -> dict:
        total_row = self.conn.execute("""
            SELECT COALESCE(SUM(CASE WHEN status!='deleted' THEN total_s ELSE 0 END), 0) AS total_s,
                   COUNT(*) AS all_projects,
                   SUM(CASE WHEN status='deleted' THEN 1 ELSE 0 END) AS deleted_projects
            FROM activities
        """).fetchone()
        today_row = self.conn.execute("""
            SELECT COALESCE(SUM(duration_s), 0) AS total
            FROM sessions
            WHERE date(ended_at)=date('now', 'localtime')
        """).fetchone()
        week_row = self.conn.execute("""
            SELECT COALESCE(SUM(duration_s), 0) AS total
            FROM sessions
            WHERE ended_at >= date('now', '-7 days', 'localtime')
        """).fetchone()
        sess_row = self.conn.execute("SELECT COUNT(*) AS total FROM sessions").fetchone()
        return {
            "total_s": total_row["total_s"] or 0,
            "today_s": today_row["total"] or 0,
            "week_s": week_row["total"] or 0,
            "projects": total_row["all_projects"] or 0,
            "deleted_projects": total_row["deleted_projects"] or 0,
            "sessions": sess_row["total"] or 0,
        }

    # ── Факты для ачивок и профиля ───────────────────────────────────────────
    def get_achievement_facts(self) -> dict:
        """Агрегаты по всей БД, из которых считаются ачивки и XP."""
        srow = self.conn.execute("""
            SELECT COUNT(*)                                        AS sessions,
                   COALESCE(SUM(duration_s), 0)                    AS total_s,
                   COALESCE(MAX(duration_s), 0)                    AS longest_s,
                   SUM(CASE WHEN TRIM(COALESCE(note,'')) != ''
                            THEN 1 ELSE 0 END)                     AS notes,
                   SUM(CASE WHEN CAST(strftime('%H', ended_at) AS INTEGER) < 5
                            THEN 1 ELSE 0 END)                     AS night_sessions,
                   SUM(CASE WHEN CAST(strftime('%H', started_at) AS INTEGER) BETWEEN 5 AND 7
                            THEN 1 ELSE 0 END)                     AS early_sessions
            FROM sessions
        """).fetchone()
        arow = self.conn.execute("""
            SELECT COUNT(*)                                              AS projects,
                   SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END)   AS completed,
                   SUM(CASE WHEN goal_h > 0 AND total_s >= goal_h * 3600
                            THEN 1 ELSE 0 END)                           AS goals_reached
            FROM activities WHERE status != 'deleted'
        """).fetchone()
        days_row = self.conn.execute(
            "SELECT COUNT(DISTINCT date(ended_at)) AS d FROM sessions"
        ).fetchone()
        first_row = self.conn.execute(
            "SELECT MIN(date(started_at)) AS d FROM sessions"
        ).fetchone()
        return {
            "sessions":       srow["sessions"] or 0,
            "total_s":        srow["total_s"] or 0,
            "longest_s":      srow["longest_s"] or 0,
            "notes":          srow["notes"] or 0,
            "night_sessions": srow["night_sessions"] or 0,
            "early_sessions": srow["early_sessions"] or 0,
            "projects":       arow["projects"] or 0,
            "completed":      arow["completed"] or 0,
            "goals_reached":  arow["goals_reached"] or 0,
            "active_days":    days_row["d"] or 0,
            "first_day":      first_row["d"],
            "overall_streak": self.get_overall_streak(),
        }

    def get_overall_streak(self) -> int:
        """Серия дней подряд с активностью по ЛЮБОМУ проекту (грейс на сегодня)."""
        rows = self.conn.execute(
            "SELECT DISTINCT date(ended_at) AS day FROM sessions ORDER BY day DESC"
        ).fetchall()
        if not rows:
            return 0
        days = {row["day"] for row in rows}
        today = date.today()
        if str(today) in days:
            cur = today
        elif str(today - timedelta(days=1)) in days:
            cur = today - timedelta(days=1)
        else:
            return 0
        streak = 0
        while str(cur) in days:
            streak += 1
            cur -= timedelta(days=1)
        return streak

    # ── Экспорт ──────────────────────────────────────────────────────────────
    def export_csv(self, path: str) -> int:
        try:
            rows = self.conn.execute("""
                SELECT a.name, a.emoji, s.started_at, s.ended_at,
                       s.duration_s, s.note
                FROM sessions s JOIN activities a ON a.id=s.activity_id
                ORDER BY s.started_at DESC
            """).fetchall()
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Активность","Эмодзи","Начало","Конец","Секунд","Заметка"])
                w.writerows(rows)
            return len(rows)
        except (sqlite3.Error, OSError) as e:
            log.error("export_csv failed: %s", e)
            raise

    # ── Утилита пересчёта кэша ───────────────────────────────────────────────
    def recalc_total(self, activity_id: int):
        try:
            row = self.conn.execute(
                "SELECT COALESCE(SUM(duration_s), 0) as t FROM sessions WHERE activity_id=?",
                (activity_id,)
            ).fetchone()
            real_total = row["t"] if row else 0
            self.conn.execute(
                "UPDATE activities SET total_s=? WHERE id=?",
                (real_total, activity_id)
            )
            self.conn.commit()
            log.info("recalc_total: aid=%s → %ds", activity_id, real_total)
        except sqlite3.Error as e:
            log.error("recalc_total failed: %s", e)
            raise
