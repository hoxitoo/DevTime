"""
DevTime v5 — утилиты и сервис таймера.
"""

import time
import logging
from datetime import datetime
from typing import Optional

log = logging.getLogger(__name__)

# ── Форматирование ────────────────────────────────────────────────────────────

def fmt_h(seconds: int) -> str:
    """1h 23m или 45m или 12s"""
    s = int(seconds)
    if s < 60:   return f"{s}с"
    if s < 3600: return f"{s // 60}м"
    h = s // 3600
    m = (s % 3600) // 60
    return f"{h}ч {m}м" if m else f"{h}ч"

def fmt_h_dec(seconds: int) -> str:
    """12.3ч — для больших чисел"""
    return f"{seconds / 3600:.1f}ч"

def fmt_hms(seconds: int) -> str:
    """00:32:15"""
    s = int(seconds)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"

def fmt_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ts_from_time(t: float) -> str:
    return datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")


# ── Цвета проектов ────────────────────────────────────────────────────────────

PROJECT_COLORS = [
    "#4fc3f7",  # голубой
    "#7c4dff",  # фиолетовый
    "#00e676",  # зелёный
    "#ffab40",  # оранжевый
    "#f06292",  # розовый
    "#4db6ac",  # бирюзовый
    "#ff5252",  # красный
    "#aed581",  # лайм
    "#ba68c8",  # сиреневый
    "#4fc3f7",  # снова голубой
]

def color_for_name(name: str) -> str:
    """Детерминированный цвет по имени проекта."""
    idx = sum(ord(c) for c in name) % len(PROJECT_COLORS)
    return PROJECT_COLORS[idx]

def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lighten(hex_color: str, factor: float = 0.3) -> str:
    r, g, b = hex_to_rgb(hex_color)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"

def darken(hex_color: str, factor: float = 0.4) -> str:
    r, g, b = hex_to_rgb(hex_color)
    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Сервис таймера ────────────────────────────────────────────────────────────

class _Session:
    """Одна активная сессия. Хранит реальный started_at через все паузы."""
    __slots__ = ("real_started_ts", "segment_start_ts", "accumulated_s", "paused")

    def __init__(self):
        now = time.time()
        self.real_started_ts: float = now
        self.segment_start_ts: float = now
        self.accumulated_s: int = 0
        self.paused: bool = False

    def elapsed(self) -> int:
        if self.paused:
            return self.accumulated_s
        return self.accumulated_s + int(time.time() - self.segment_start_ts)

    def do_pause(self):
        self.accumulated_s += int(time.time() - self.segment_start_ts)
        self.paused = True

    def do_resume(self):
        self.segment_start_ts = time.time()
        self.paused = False


class TimerService:
    def __init__(self):
        self._sessions: dict[int, _Session] = {}

    def start(self, aid: int) -> bool:
        if aid in self._sessions:
            return False
        self._sessions[aid] = _Session()
        return True

    def pause(self, aid: int) -> bool:
        s = self._sessions.get(aid)
        if s is None or s.paused:
            return False
        s.do_pause()
        return True

    def resume(self, aid: int) -> bool:
        s = self._sessions.get(aid)
        if s is None or not s.paused:
            return False
        s.do_resume()
        return True

    def stop(self, aid: int) -> Optional[dict]:
        s = self._sessions.pop(aid, None)
        if s is None:
            return None
        if not s.paused:
            s.accumulated_s += int(time.time() - s.segment_start_ts)
        return {
            "started_at": ts_from_time(s.real_started_ts),
            "ended_at":   fmt_ts(),
            "duration_s": max(s.accumulated_s, 1),
        }

    def elapsed(self, aid: int) -> int:
        s = self._sessions.get(aid)
        return s.elapsed() if s else 0

    def is_running(self, aid: int) -> bool:
        s = self._sessions.get(aid)
        return s is not None and not s.paused

    def is_paused(self, aid: int) -> bool:
        s = self._sessions.get(aid)
        return s is not None and s.paused

    def is_active(self, aid: int) -> bool:
        return aid in self._sessions

    def stop_all(self) -> dict[int, dict]:
        result = {}
        for aid in list(self._sessions.keys()):
            data = self.stop(aid)
            if data:
                result[aid] = data
        return result
