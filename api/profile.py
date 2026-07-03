"""
Профиль «игрока»: XP, уровень, звание.
XP = минуты за кодом (1 мин = 1 XP) + 250 XP за каждую ачивку.
Порог уровня растёт квадратично: суммарно 100·L² XP до уровня L
(L1 — 100 XP, L5 — 2500, L10 — 10000 ≈ 166 часов).
"""

import math

XP_PER_ACHIEVEMENT = 250

RANKS = [
    (0,  "Новичок"),
    (3,  "Джуниор"),
    (6,  "Мидл"),
    (10, "Сеньор"),
    (15, "Архитектор"),
    (20, "Легенда"),
    (30, "Гранд-мастер"),
]


def rank_for(level: int) -> str:
    name = RANKS[0][1]
    for lvl, title in RANKS:
        if level >= lvl:
            name = title
    return name


def compute(facts: dict, n_achievements: int) -> dict:
    xp = facts["total_s"] // 60 + n_achievements * XP_PER_ACHIEVEMENT
    level = int(math.isqrt(xp // 100))
    cur_floor = 100 * level * level
    nxt = 100 * (level + 1) * (level + 1)
    span = nxt - cur_floor
    return {
        "xp": xp,
        "level": level,
        "rank": rank_for(level),
        "next_level_xp": nxt,
        "level_pct": int((xp - cur_floor) / span * 100) if span else 0,
        "xp_to_next": nxt - xp,
    }
