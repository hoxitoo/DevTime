"""REST API: полные пользовательские сценарии через TestClient."""
import datetime as dt
import time


def ts(delta_days=0, hour=12):
    d = dt.datetime.now() - dt.timedelta(days=delta_days)
    return d.replace(hour=hour, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")


def make(client, name="Proj", **kw):
    body = {"name": name, "emoji": "💻", "color": "#4fc3f7", "goal_h": 0}
    body.update(kw)
    r = client.post("/api/activities", json=body)
    assert r.status_code == 201
    return r.json()["id"]


def test_create_validation(client):
    assert client.post("/api/activities", json={"name": "  "}).status_code == 422


def test_timer_start_stop_flow(client):
    aid = make(client)
    r = client.post(f"/api/activities/{aid}/timer", json={"action": "start"})
    assert r.status_code == 200 and r.json()["running"] is True
    time.sleep(1.1)
    assert str(aid) in client.get("/api/timers").json()
    r = client.post(f"/api/activities/{aid}/stop", json={"note": "тест"})
    data = r.json()
    assert data["duration_s"] >= 1
    assert any(a["id"] == "first_session" for a in data["new_achievements"])
    # сессия записана
    detail = client.get(f"/api/activities/{aid}").json()
    assert detail["session_count"] == 1
    assert detail["sessions"][0]["note"] == "тест"


def test_start_completed_project_conflict(client):
    aid = make(client)
    client.post(f"/api/activities/{aid}/status", json={"status": "completed"})
    r = client.post(f"/api/activities/{aid}/timer", json={"action": "start"})
    assert r.status_code == 409


def test_delete_with_running_timer_preserves_session(client):
    aid = make(client)
    client.post(f"/api/activities/{aid}/timer", json={"action": "start"})
    time.sleep(1.1)
    r = client.post(f"/api/activities/{aid}/status", json={"status": "deleted"})
    assert r.status_code == 200
    detail = client.get(f"/api/activities/{aid}").json()
    assert detail["session_count"] == 1
    assert detail["running"] is False


def test_manual_session_crud(client):
    aid = make(client)
    # добавление
    r = client.post(f"/api/activities/{aid}/sessions",
                    json={"started_at": ts(1), "duration_min": 30, "note": "забыл таймер"})
    assert r.status_code == 201
    sid = r.json()["session"]["id"]
    assert r.json()["activity"]["total_s"] == 1800
    # правка длительности
    r = client.put(f"/api/sessions/{sid}", json={"duration_s": 600})
    assert r.status_code == 200 and r.json()["duration_s"] == 600
    assert client.get(f"/api/activities/{aid}").json()["total_s"] == 600
    # удаление
    assert client.delete(f"/api/sessions/{sid}").status_code == 200
    assert client.get(f"/api/activities/{aid}").json()["total_s"] == 0
    assert client.delete(f"/api/sessions/{sid}").status_code == 404


def test_manual_session_validation(client):
    aid = make(client)
    bad = [
        {"started_at": "не дата", "duration_min": 30},
        {"started_at": ts(), "duration_min": 0},
        {"started_at": ts(), "duration_min": 100500},
    ]
    for body in bad:
        assert client.post(f"/api/activities/{aid}/sessions", json=body).status_code == 422


def test_day_endpoint(client):
    aid = make(client)
    client.post(f"/api/activities/{aid}/sessions",
                json={"started_at": ts(0, hour=9), "duration_min": 60, "note": "утро"})
    day = dt.date.today().isoformat()
    r = client.get(f"/api/day/{day}").json()
    assert r["total_s"] == 3600
    assert r["sessions"][0]["activity_name"] == "Proj"


def test_week_insights_endpoint(client):
    aid = make(client)
    client.post(f"/api/activities/{aid}/sessions",
                json={"started_at": ts(0), "duration_min": 60})
    r = client.get("/api/insights/week")
    assert r.status_code == 200
    assert {"current_s", "previous_s", "daily", "top_projects"} <= set(r.json())


def test_plan_and_description(client):
    aid = make(client)
    assert client.post(f"/api/activities/{aid}/plan", json={"text": "план"}).status_code == 200
    assert client.post(f"/api/activities/{aid}/description", json={"text": "описание"}).status_code == 200
    detail = client.get(f"/api/activities/{aid}").json()
    assert detail["day_plan"] == "план"
    assert detail["day_plan_date"] == dt.date.today().isoformat()
    assert detail["descr"] == "описание"


def test_profile_and_achievements_endpoints(client):
    aid = make(client)
    client.post(f"/api/activities/{aid}/sessions",
                json={"started_at": ts(0), "duration_min": 61})
    prof = client.get("/api/profile").json()
    assert prof["xp"] >= 61
    items = client.get("/api/achievements").json()
    assert len(items) >= 29
    assert any(a["unlocked"] for a in items)


def test_autosave_persists_running_timer(tmp_path):
    """Crash-safe: активный таймер попадает в running_state на диске."""
    import sqlite3
    from fastapi.testclient import TestClient
    from api.server import create_app

    db_file = str(tmp_path / "autosave.db")
    app = create_app(db_file, autosave_interval=0.2)
    with TestClient(app) as c:
        aid = make(c, "Autosave")
        c.post(f"/api/activities/{aid}/timer", json={"action": "start"})
        time.sleep(1.3)  # несколько тиков автосейва
        conn = sqlite3.connect(db_file)
        row = conn.execute(
            "SELECT elapsed_s FROM running_state WHERE activity_id=?", (aid,)
        ).fetchone()
        conn.close()
        assert row is not None and row[0] >= 1
