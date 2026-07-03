"""Движок ачивок и профиль (XP/уровни)."""
from api import achievements as ach
from api import profile as prof

EMPTY = {k: 0 for k in (
    "sessions", "total_s", "longest_s", "notes", "night_sessions",
    "early_sessions", "projects", "completed", "goals_reached",
    "active_days", "overall_streak")}


def facts(**kw):
    f = dict(EMPTY)
    f.update(kw)
    return f


def test_no_facts_no_unlocks():
    assert ach.unlocked_ids(facts()) == set()


def test_first_session_unlocks():
    ids = ach.unlocked_ids(facts(sessions=1))
    assert "first_session" in ids and len(ids) == 1


def test_hours_ladder():
    ids = ach.unlocked_ids(facts(total_s=100 * 3600))
    assert {"first_hour", "h10", "h50", "h100"} <= ids
    assert "h500" not in ids and "h1000" not in ids


def test_progress_pct():
    items = {a["id"]: a for a in ach.compute(facts(total_s=5 * 3600))}
    assert items["h10"]["pct"] == 50
    assert items["h10"]["unlocked"] is False


def test_unlocked_sorted_first():
    items = ach.compute(facts(sessions=1))
    assert items[0]["unlocked"] is True


def test_long_tail_rules_present():
    ids = {r[0] for r in ach.RULES}
    assert {"h1000", "streak100", "days365", "sessions500", "marathon8"} <= ids
    assert len(ach.RULES) >= 29


def test_diff_detects_new_unlock():
    before = ach.unlocked_ids(facts(sessions=99))
    after = ach.unlocked_ids(facts(sessions=100))
    assert after - before == {"sessions100"}


def test_profile_levels_monotonic():
    p0 = prof.compute(facts(), 0)
    assert p0["xp"] == 0 and p0["level"] == 0 and p0["rank"] == "Новичок"
    p1 = prof.compute(facts(total_s=3600), 2)  # 60 XP + 500 XP
    assert p1["xp"] == 60 + 2 * prof.XP_PER_ACHIEVEMENT
    assert p1["level"] >= p0["level"]
    assert p1["next_level_xp"] > p1["xp"]
    assert 0 <= p1["level_pct"] <= 100


def test_rank_progression():
    assert prof.rank_for(0) == "Новичок"
    assert prof.rank_for(12) == "Сеньор"
    assert prof.rank_for(35) == "Гранд-мастер"
