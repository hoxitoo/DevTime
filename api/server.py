"""
FastAPI-приложение DevTime.
REST поверх ядра (db.py + utils.py) + раздача собранного веб-UI (web/dist).
Вся работа с БД сериализуется через _db_lock — sqlite и FastAPI-тредпул.
"""

import sys
import logging
import tempfile
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db import DB
from utils import TimerService
from api import achievements as ach
from api import profile as prof

log = logging.getLogger(__name__)


def static_dir() -> Optional[Path]:
    """web/dist рядом с исходниками или внутри PyInstaller-бандла."""
    if hasattr(sys, "_MEIPASS"):
        cand = Path(sys._MEIPASS) / "web" / "dist"
    else:
        cand = Path(__file__).resolve().parent.parent / "web" / "dist"
    return cand if (cand / "index.html").exists() else None


# ── Модели запросов ───────────────────────────────────────────────────────────

class ActivityIn(BaseModel):
    name: str
    emoji: str = "💻"
    color: str = "#4fc3f7"
    goal_h: float = 0


class PlanIn(BaseModel):
    text: str = ""


class StatusIn(BaseModel):
    status: str  # active | completed | deleted


class TimerIn(BaseModel):
    action: str  # start | pause | resume


class NoteIn(BaseModel):
    note: str = ""


def create_app(db_path: Optional[str] = None) -> FastAPI:
    app = FastAPI(title="DevTime API", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # vite dev
        allow_methods=["*"], allow_headers=["*"],
    )

    db = DB(db_path, check_same_thread=False) if db_path else DB(check_same_thread=False)
    timer = TimerService()
    lock = threading.Lock()

    app.state.db = db
    app.state.timer = timer
    app.state.lock = lock

    # ── Вспомогательное ──────────────────────────────────────────────────────

    def act_dict(row, with_stats=False) -> dict:
        a = dict(row)
        aid = a["id"]
        a["running"] = timer.is_running(aid)
        a["paused"] = timer.is_paused(aid)
        a["elapsed"] = timer.elapsed(aid)
        if with_stats:
            a["today_s"] = db.get_today_total(aid)
            a["week_s"] = db.get_week_total(aid)
            a["streak"] = db.get_streak(aid)
            a["session_count"] = db.get_session_count(aid)
        return a

    def get_or_404(aid: int):
        row = db.get_activity(aid)
        if not row:
            raise HTTPException(404, "activity not found")
        return row

    def flush_running(note: str = "(авто-стоп)") -> int:
        """Логирует все активные сессии. Вызывается при выходе из приложения."""
        with lock:
            sessions = timer.stop_all()
            for aid, data in sessions.items():
                try:
                    db.log_session(aid, data["started_at"], data["ended_at"],
                                   data["duration_s"], note)
                except Exception as e:  # noqa: BLE001
                    log.error("flush aid=%s: %s", aid, e)
            return len(sessions)

    app.state.flush_running = flush_running

    # ── Активности ───────────────────────────────────────────────────────────

    @app.get("/api/activities")
    def list_activities(include_deleted: bool = True, stats: bool = True):
        with lock:
            rows = db.get_activities(include_deleted=include_deleted)
            return [act_dict(r, with_stats=stats) for r in rows]

    @app.post("/api/activities", status_code=201)
    def add_activity(body: ActivityIn):
        name = body.name.strip()
        if not name:
            raise HTTPException(422, "name is empty")
        with lock:
            aid = db.add_activity(name, body.emoji, body.color, body.goal_h)
            return act_dict(db.get_activity(aid), with_stats=True)

    @app.get("/api/activities/{aid}")
    def activity_detail(aid: int):
        with lock:
            row = get_or_404(aid)
            a = act_dict(row, with_stats=True)
            a["daily"] = [dict(r) for r in db.get_daily_totals(aid, days=28)]
            a["sessions"] = [dict(r) for r in db.get_sessions(aid, limit=50)]
            return a

    @app.put("/api/activities/{aid}")
    def update_activity(aid: int, body: ActivityIn):
        name = body.name.strip()
        if not name:
            raise HTTPException(422, "name is empty")
        with lock:
            get_or_404(aid)
            db.update_activity(aid, name, body.emoji, body.color, body.goal_h)
            return act_dict(db.get_activity(aid), with_stats=True)

    @app.post("/api/activities/{aid}/plan")
    def save_plan(aid: int, body: PlanIn):
        with lock:
            get_or_404(aid)
            db.update_day_plan(aid, body.text.strip())
            return {"ok": True}

    @app.post("/api/activities/{aid}/status")
    def set_status(aid: int, body: StatusIn):
        if body.status not in ("active", "completed", "deleted"):
            raise HTTPException(422, "bad status")
        with lock:
            get_or_404(aid)
            # Не теряем активную сессию при удалении/завершении.
            data = timer.stop(aid)
            if data:
                db.log_session(aid, data["started_at"], data["ended_at"],
                               data["duration_s"], "(сохранено при смене статуса)")
            db.set_activity_status(aid, body.status)
            return act_dict(db.get_activity(aid), with_stats=True)

    # ── Таймер ───────────────────────────────────────────────────────────────

    @app.get("/api/timers")
    def timers_state():
        with lock:
            rows = db.get_activities(include_deleted=False)
            return {
                str(r["id"]): {
                    "running": timer.is_running(r["id"]),
                    "paused": timer.is_paused(r["id"]),
                    "elapsed": timer.elapsed(r["id"]),
                }
                for r in rows if timer.is_active(r["id"])
            }

    @app.post("/api/activities/{aid}/timer")
    def timer_action(aid: int, body: TimerIn):
        with lock:
            row = get_or_404(aid)
            if body.action == "start":
                if row["status"] != "active":
                    raise HTTPException(409, "project is not active")
                timer.start(aid)
            elif body.action == "pause":
                timer.pause(aid)
            elif body.action == "resume":
                timer.resume(aid)
            else:
                raise HTTPException(422, "bad action")
            return act_dict(db.get_activity(aid))

    @app.post("/api/activities/{aid}/stop")
    def timer_stop(aid: int, body: NoteIn):
        with lock:
            get_or_404(aid)
            data = timer.stop(aid)
            if not data:
                raise HTTPException(409, "timer is not active")
            before = ach.unlocked_ids(db.get_achievement_facts())
            sid = db.log_session(aid, data["started_at"], data["ended_at"],
                                 data["duration_s"], body.note.strip())
            after = ach.compute(db.get_achievement_facts())
            fresh = ach.unlocked_ids(db.get_achievement_facts()) - before
            return {
                "session_id": sid,
                "duration_s": data["duration_s"],
                "new_achievements": [a for a in after if a["id"] in fresh],
                "activity": act_dict(db.get_activity(aid), with_stats=True),
            }

    @app.put("/api/sessions/{sid}/note")
    def session_note(sid: int, body: NoteIn):
        with lock:
            db.update_session_note(sid, body.note.strip())
            return {"ok": True}

    # ── Статистика, профиль, ачивки ──────────────────────────────────────────

    @app.get("/api/overview")
    def overview():
        with lock:
            st = db.get_overall_stats()
            st["daily"] = [dict(r) for r in db.get_all_daily_totals(days=28)]
            return st

    @app.get("/api/achievements")
    def achievements():
        with lock:
            return ach.compute(db.get_achievement_facts())

    @app.get("/api/profile")
    def profile_ep():
        with lock:
            facts = db.get_achievement_facts()
            items = ach.compute(facts)
            unlocked = [a for a in items if a["unlocked"]]
            p = prof.compute(facts, len(unlocked))
            p["facts"] = facts
            p["achievements_unlocked"] = len(unlocked)
            p["achievements_total"] = len(items)
            p["recent_achievements"] = unlocked[:6]
            p["heatmap"] = [dict(r) for r in db.get_all_daily_totals(days=371)]
            return p

    @app.get("/api/export.csv")
    def export_csv():
        with lock:
            tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
            tmp.close()
            db.export_csv(tmp.name)
            return FileResponse(tmp.name, filename="devtime_export.csv",
                                media_type="text/csv")

    # ── Статика (собранный фронтенд) ─────────────────────────────────────────

    dist = static_dir()
    if dist:
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="web")
        log.info("serving web UI from %s", dist)
    else:
        log.warning("web/dist не найден — доступен только API (собери фронт: cd web && npm run build)")

    return app
