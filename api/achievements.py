"""
Движок ачивок. Всё считается детерминированно из фактов БД
(db.get_achievement_facts) — отдельного хранилища не нужно,
состояние всегда согласовано с данными.
"""

H = 3600

# (id, emoji, название, описание, ключ факта, цель)
RULES = [
    ("first_session", "🎬", "Первый коммит",      "Заверши первую сессию",              "sessions",       1),
    ("first_hour",    "⏱️", "Разогрев",           "Наработай первый час",               "total_s",        1 * H),
    ("h10",           "🔟", "Десятка",            "10 часов в проектах",                "total_s",        10 * H),
    ("h50",           "⚡", "Полсотни",           "50 часов в проектах",                "total_s",        50 * H),
    ("h100",          "💯", "Клуб 100",           "100 часов в проектах",               "total_s",        100 * H),
    ("h500",          "🏆", "Ветеран",            "500 часов в проектах",               "total_s",        500 * H),
    ("marathon",      "🏃", "Марафонец",          "Одна сессия длиннее 4 часов",        "longest_s",      4 * H),
    ("streak3",       "🔥", "Серия ×3",           "3 дня подряд с активностью",         "overall_streak", 3),
    ("streak7",       "🧨", "Неделя огня",        "7 дней подряд с активностью",        "overall_streak", 7),
    ("streak30",      "💪", "Железная дисциплина", "30 дней подряд с активностью",      "overall_streak", 30),
    ("night_owl",     "🦉", "Ночная смена",       "Сессия, законченная после полуночи", "night_sessions", 1),
    ("early_bird",    "🌅", "Ранняя пташка",      "Сессия, начатая до 8 утра",          "early_sessions", 1),
    ("collector",     "📚", "Коллекционер",       "5 проектов в библиотеке",            "projects",       5),
    ("finisher",      "🏁", "Финишер",            "Заверши первый проект",              "completed",      1),
    ("goal",          "🎯", "Цель взята",         "Достигни цели по часам",             "goals_reached",  1),
    ("scribe",        "✍️", "Летописец",          "10 заметок к сессиям",               "notes",          10),
    ("days30",        "📅", "30 дней в деле",     "30 разных дней с активностью",       "active_days",    30),
]


def compute(facts: dict) -> list[dict]:
    """Список ачивок с прогрессом. Разблокированные — первыми."""
    out = []
    for aid, icon, title, desc, key, target in RULES:
        value = facts.get(key, 0) or 0
        unlocked = value >= target
        out.append({
            "id": aid,
            "icon": icon,
            "title": title,
            "desc": desc,
            "value": min(value, target),
            "target": target,
            "pct": min(100, int(value / target * 100)) if target else 0,
            "unlocked": unlocked,
            "time_based": key in ("total_s", "longest_s"),
        })
    out.sort(key=lambda a: (not a["unlocked"], -a["pct"]))
    return out


def unlocked_ids(facts: dict) -> set[str]:
    return {a["id"] for a in compute(facts) if a["unlocked"]}
