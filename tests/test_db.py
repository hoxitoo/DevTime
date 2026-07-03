"""Ядро: активности, сессии, статистика, автосейв."""
import datetime as dt


def ts(delta_days=0, hour=12):
    d = dt.datetime.now() - dt.timedelta(days=delta_days)
    return d.replace(hour=hour, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")


def test_activity_lifecycle(db):
    aid = db.add_activity("Test", "💻", "#4fc3f7", goal_h=10)
    act = db.get_activity(aid)
    assert act["name"] == "Test" and act["status"] == "active"
    db.complete_activity(aid)
    assert db.get_activity(aid)["status"] == "completed"
    db.delete_activity(aid)
    assert db.get_activity(aid)["status"] == "deleted"
    db.restore_activity(aid)
    assert db.get_activity(aid)["status"] == "active"


def test_log_session_updates_cache(db):
    aid = db.add_activity("A", "💻", "#fff")
    db.log_session(aid, ts(), ts(), 3600, "n")
    assert db.get_activity(aid)["total_s"] == 3600
    assert db.get_today_total(aid) == 3600
    assert db.get_week_total(aid) == 3600


def test_streak_grace(db):
    aid = db.add_activity("A", "💻", "#fff")
    # активность только вчера — грейс держит серию
    db.log_session(aid, ts(1), ts(1), 600, "")
    assert db.get_streak(aid) == 1
    # позавчера + вчера = 2
    db.log_session(aid, ts(2), ts(2), 600, "")
    assert db.get_streak(aid) == 2
    # разрыв три дня назад не учитывается
    db.log_session(aid, ts(5), ts(5), 600, "")
    assert db.get_streak(aid) == 2


def test_streak_zero_when_stale(db):
    aid = db.add_activity("A", "💻", "#fff")
    db.log_session(aid, ts(3), ts(3), 600, "")
    assert db.get_streak(aid) == 0


def test_overall_stats_exclude_deleted(db):
    a1 = db.add_activity("Keep", "💻", "#fff")
    a2 = db.add_activity("Drop", "🗑️", "#fff")
    db.log_session(a1, ts(), ts(), 100, "")
    db.log_session(a2, ts(), ts(), 900, "")
    db.delete_activity(a2)
    assert db.get_overall_stats()["total_s"] == 100


def test_manual_session_and_recalc(db):
    aid = db.add_activity("A", "💻", "#fff")
    sid = db.add_manual_session(aid, ts(1), 1800, "забытая")
    row = db.get_session(sid)
    assert row["duration_s"] == 1800
    assert row["ended_at"] > row["started_at"]
    assert db.get_activity(aid)["total_s"] == 1800


def test_update_session_recalcs_total(db):
    aid = db.add_activity("A", "💻", "#fff")
    sid = db.add_manual_session(aid, ts(1), 3600, "")
    db.update_session(sid, duration_s=600)
    assert db.get_session(sid)["duration_s"] == 600
    assert db.get_activity(aid)["total_s"] == 600


def test_delete_session_recalcs_total(db):
    aid = db.add_activity("A", "💻", "#fff")
    s1 = db.add_manual_session(aid, ts(1), 100, "")
    db.add_manual_session(aid, ts(2), 200, "")
    assert db.delete_session(s1) is True
    assert db.get_activity(aid)["total_s"] == 200
    assert db.delete_session(9999) is False


def test_sessions_by_day(db):
    aid = db.add_activity("A", "💻", "#fff")
    db.add_manual_session(aid, ts(0, hour=9), 600, "утро")
    day = dt.date.today().isoformat()
    rows = db.get_sessions_by_day(day)
    assert len(rows) == 1 and rows[0]["activity_name"] == "A"


def test_week_insights_shape(db):
    aid = db.add_activity("A", "💻", "#fff")
    db.add_manual_session(aid, ts(0), 3600, "")
    ins = db.get_week_insights()
    assert set(ins) == {"week_start", "current_s", "previous_s", "daily", "top_projects"}
    assert ins["current_s"] >= 3600 or ins["previous_s"] >= 3600  # понедельник — граница


def test_running_state_recovery(db):
    aid = db.add_activity("A", "💻", "#fff")
    db.save_running_state({aid: {"started_at": ts(), "elapsed_s": 1234, "paused": False}})
    n = db.recover_running_state()
    assert n == 1
    assert db.get_activity(aid)["total_s"] == 1234
    # повторное восстановление — пусто
    assert db.recover_running_state() == 0


def test_day_plan_dated(db):
    aid = db.add_activity("A", "💻", "#fff")
    db.update_day_plan(aid, "сделать X")
    act = db.get_activity(aid)
    assert act["day_plan"] == "сделать X"
    assert act["day_plan_date"] == dt.date.today().isoformat()


def test_description(db):
    aid = db.add_activity("A", "💻", "#fff")
    db.update_description(aid, "мой проект")
    assert db.get_activity(aid)["descr"] == "мой проект"
