"""
DevTime v7 — главное окно.
Разделы: Библиотека проектов, Статистика, страница проекта.
"""

import time
import logging
import tkinter as tk
import tkinter.font as tkfont
import customtkinter as ctk
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename
from datetime import date, timedelta

from db import DB
from utils import TimerService, fmt_h, fmt_hms, darken, blend, hex_to_rgb
from ui.dialogs import ActivityDialog, NoteDialog, EditNoteDialog

log = logging.getLogger(__name__)

# ── Палитра ───────────────────────────────────────────────────────────────────
BG      = "#0b0d12"
SIDEBAR = "#0f1219"
SURF    = "#151a26"
SURF2   = "#1a2030"
SURF3   = "#1f263a"
BORDER  = "#242d42"
ACCENT  = "#4fc3f7"
GREEN   = "#00e676"
RED     = "#ff5252"
ORANGE  = "#ffab40"
TEXT    = "#dde3f0"
MUTED   = "#4a5570"
MUTED2  = "#2a3350"

# ── Шрифты (кроссплатформенный выбор) ─────────────────────────────────────────
# Дефолты — Windows. Реальные семейства подбираются в _resolve_fonts() после
# создания root: на Linux/macOS Segoe UI нет, нужен фолбэк, иначе эмодзи и
# текст рендерятся неконсистентно.
FONT_UI    = "Segoe UI"
FONT_MONO  = "Courier New"
FONT_EMOJI = "Segoe UI Emoji"


def _resolve_fonts(root):
    """Подбирает доступные семейства шрифтов под текущую ОС."""
    global FONT_UI, FONT_MONO, FONT_EMOJI
    try:
        fams = {f.lower() for f in tkfont.families(root)}
    except Exception as e:  # noqa: BLE001 — не критично, остаёмся на дефолтах
        log.debug("font families unavailable: %s", e)
        return

    def pick(candidates, default):
        for c in candidates:
            if c.lower() in fams:
                return c
        return default

    FONT_UI = pick(
        ["Segoe UI", "SF Pro Text", "Helvetica Neue", "Noto Sans",
         "DejaVu Sans", "Ubuntu", "Cantarell", "Arial"], FONT_UI)
    FONT_MONO = pick(
        ["Courier New", "SF Mono", "JetBrains Mono", "Consolas", "Menlo",
         "DejaVu Sans Mono", "Noto Sans Mono", "Liberation Mono", "monospace"], FONT_MONO)
    FONT_EMOJI = pick(
        ["Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji",
         "Noto Emoji", "Segoe UI Symbol", FONT_UI], FONT_EMOJI)
    log.info("fonts: ui=%s mono=%s emoji=%s", FONT_UI, FONT_MONO, FONT_EMOJI)


def _f(size=11, bold=False):
    return ctk.CTkFont(
        size=size,
        weight="bold" if bold else "normal",
        family=FONT_UI if size > 12 else FONT_MONO,
    )


def _grad_line(canvas, x0, y0, x1, y1, c1, c2, steps=40):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    width = max(x1 - x0, 1)
    for i in range(steps):
        t = i / steps
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        sx = x0 + int(width * i / steps)
        ex = x0 + int(width * (i + 1) / steps)
        canvas.create_rectangle(sx, y0, ex, y1, fill=f"#{r:02x}{g:02x}{b:02x}", outline="")


class MainWindow:
    def __init__(self, root: ctk.CTk, db: DB):
        self.root = root
        self.db = db
        _resolve_fonts(root)
        self.timer = TimerService()
        self.sel_id = None
        self._stop_tick = False
        # Pomodoro теперь пер-проектный: aid -> момент окончания (epoch).
        self._pomos = {}
        self._pomo_aid = None         # для какого проекта сейчас показан _pomo_lbl
        self._view_mode = "project"   # project | library | stats
        self._nav_buttons = {}

        # Сайдбар: поиск и фильтр
        self._sb_search_var = None   # StringVar создаётся в _build
        self._sb_filter = "active"   # active | all

        # Библиотека: сортировка
        self._lib_sort_key = "total_s"   # total_s | name | created | status
        self._lib_sort_asc = False

        # refs для live updates
        self._dt_aid = None
        self._dt_base_s = 0
        self._dt_today_base = 0
        self._dt_time_lbl = None
        self._dt_today_lbl = None
        self._dt_sess_lbl = None
        self._pomo_lbl = None
        self._side_refs = {}

        self._build()
        self._reload_sidebar(keep_detail=False)
        self._set_view("library")
        self._tick()

    # ══════════════════════════════════════════════════════════════════════════
    #  Build
    # ══════════════════════════════════════════════════════════════════════════
    def _build(self):
        self.root.configure(fg_color=BG)

        top = ctk.CTkFrame(self.root, fg_color=SIDEBAR, height=50, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkLabel(top, text="⌚", font=_f(18), text_color=ACCENT).pack(side="left", padx=(14, 4))
        ctk.CTkLabel(top, text="DevTime", font=_f(15, bold=True), text_color=TEXT).pack(side="left", padx=(0, 14))

        nav = ctk.CTkFrame(top, fg_color="transparent")
        nav.pack(side="left", padx=6)

        self._nav_buttons["library"] = ctk.CTkButton(
            nav, text="Библиотека проектов", width=170, height=32,
            fg_color=SURF2, hover_color=SURF3, text_color=TEXT,
            border_width=1, border_color=BORDER, corner_radius=8,
            font=_f(10, bold=True), command=lambda: self._set_view("library")
        )
        self._nav_buttons["library"].pack(side="left", padx=(0, 6))

        self._nav_buttons["stats"] = ctk.CTkButton(
            nav, text="Статистика", width=110, height=32,
            fg_color=SURF2, hover_color=SURF3, text_color=TEXT,
            border_width=1, border_color=BORDER, corner_radius=8,
            font=_f(10, bold=True), command=lambda: self._set_view("stats")
        )
        self._nav_buttons["stats"].pack(side="left")

        ctk.CTkButton(
            top, text="⬇  CSV", width=80, height=30,
            fg_color=SURF2, text_color=MUTED, hover_color=SURF3,
            border_width=1, border_color=BORDER,
            font=_f(10), corner_radius=6, command=self._export
        ).pack(side="right", padx=12)

        body = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0)
        body.pack(fill="both", expand=True)

        self._sb = ctk.CTkFrame(body, fg_color=SIDEBAR, width=230, corner_radius=0)
        self._sb.pack(side="left", fill="y")
        self._sb.pack_propagate(False)

        sbh = ctk.CTkFrame(self._sb, fg_color=SIDEBAR, corner_radius=0)
        sbh.pack(fill="x", padx=12, pady=(12, 6))
        ctk.CTkLabel(sbh, text="БИБЛИОТЕКА", text_color=MUTED, font=_f(9)).pack(side="left")
        ctk.CTkButton(
            sbh, text="＋", width=30, height=30,
            fg_color=ACCENT, text_color="#000", hover_color="#81d4fa",
            font=_f(16, bold=True), corner_radius=8, command=self._add
        ).pack(side="right")

        ctk.CTkFrame(self._sb, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        # ── Поиск ───────────────────────────────────────────────────────────
        search_wrap = ctk.CTkFrame(self._sb, fg_color=SIDEBAR, corner_radius=0)
        search_wrap.pack(fill="x", padx=8, pady=(8, 4))
        self._sb_search_var = ctk.StringVar()
        self._sb_search_var.trace_add("write", lambda *_: self._reload_sidebar(keep_detail=False))
        ctk.CTkEntry(
            search_wrap, textvariable=self._sb_search_var,
            placeholder_text="🔍  Поиск...",
            fg_color=SURF2, border_color=BORDER, text_color=TEXT,
            placeholder_text_color=MUTED, font=_f(10),
            height=30, corner_radius=8,
        ).pack(fill="x")

        # ── Фильтр по статусу ────────────────────────────────────────────────
        filter_wrap = ctk.CTkFrame(self._sb, fg_color=SIDEBAR, corner_radius=0)
        filter_wrap.pack(fill="x", padx=8, pady=(0, 6))
        self._filter_btns = {}
        for fkey, flabel in [("active", "Активные"), ("all", "Все")]:
            b = ctk.CTkButton(
                filter_wrap, text=flabel, height=24,
                fg_color=ACCENT if fkey == self._sb_filter else SURF2,
                text_color="#000" if fkey == self._sb_filter else MUTED,
                hover_color=SURF3, font=_f(9), corner_radius=6,
                command=lambda k=fkey: self._set_sb_filter(k),
            )
            b.pack(side="left", fill="x", expand=True, padx=2)
            self._filter_btns[fkey] = b

        ctk.CTkFrame(self._sb, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        self._slist = ctk.CTkScrollableFrame(
            self._sb, fg_color=SIDEBAR, corner_radius=0,
            scrollbar_button_color=SURF2
        )
        self._slist.pack(fill="both", expand=True)

        ctk.CTkFrame(body, fg_color=BORDER, width=1, corner_radius=0).pack(side="left", fill="y")

        self._dzone = ctk.CTkScrollableFrame(
            body, fg_color=BG, corner_radius=0, scrollbar_button_color=SURF2
        )
        self._dzone.pack(side="left", fill="both", expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  Navigation
    # ══════════════════════════════════════════════════════════════════════════
    def _set_view(self, mode: str):
        self._view_mode = mode
        self._sync_nav_buttons()
        self._render_current_view()

    def _sync_nav_buttons(self):
        for mode, btn in self._nav_buttons.items():
            active = mode == self._view_mode
            btn.configure(
                fg_color=ACCENT if active else SURF2,
                text_color="#000" if active else TEXT,
                border_color=ACCENT if active else BORDER,
            )

    def _render_current_view(self):
        if self._view_mode == "library":
            self._show_library_page()
        elif self._view_mode == "stats":
            self._show_stats_page()
        else:
            if self.sel_id:
                fresh = self.db.get_activity(self.sel_id)
                if fresh:
                    self._show_detail(dict(fresh))
                else:
                    self._show_empty()
            else:
                self._show_empty()

    # ══════════════════════════════════════════════════════════════════════════
    #  Sidebar
    # ══════════════════════════════════════════════════════════════════════════
    def _set_sb_filter(self, key: str):
        self._sb_filter = key
        for k, b in self._filter_btns.items():
            active = k == key
            b.configure(
                fg_color=ACCENT if active else SURF2,
                text_color="#000" if active else MUTED,
            )
        self._reload_sidebar(keep_detail=False)

    def _reload_sidebar(self, keep_detail=True):
        for w in self._slist.winfo_children():
            w.destroy()
        self._side_refs.clear()

        all_acts = self.db.get_activities(include_deleted=False)

        # Фильтр по статусу
        if self._sb_filter == "active":
            acts = [a for a in all_acts if a["status"] == "active"]
        else:
            acts = list(all_acts)

        # Поиск по имени
        query = ""
        if self._sb_search_var:
            query = self._sb_search_var.get().strip().lower()
        if query:
            acts = [a for a in acts if query in a["name"].lower()]

        if not acts:
            msg = "Ничего не найдено" if query else "Нет проектов.\nНажми  ＋"
            ctk.CTkLabel(
                self._slist, text=msg,
                text_color=MUTED, font=_f(11), justify="center"
            ).pack(pady=30)
            if not keep_detail:
                return
        else:
            for a in acts:
                self._sb_card(a)

        if keep_detail and self._view_mode == "project" and self.sel_id:
            ids = [a["id"] for a in acts]
            if self.sel_id in ids:
                fresh = self.db.get_activity(self.sel_id)
                if fresh:
                    self._show_detail(dict(fresh))
            else:
                self.sel_id = None
                self._show_empty()

    def _sb_card(self, act):
        aid = act["id"]
        sel = aid == self.sel_id and self._view_mode == "project"
        run = self.timer.is_running(aid)
        paused = self.timer.is_paused(aid)
        color = act["color"]

        outer = ctk.CTkFrame(
            self._slist,
            fg_color=SURF2 if sel else SIDEBAR,
            corner_radius=10,
            border_width=1,
            border_color=color if sel else BORDER,
            cursor="hand2",
        )
        outer.pack(fill="x", padx=8, pady=4)

        banner = tk.Canvas(outer, height=52, bg=SIDEBAR, highlightthickness=0)
        banner.pack(fill="x")

        can_quickstart = (act["status"] == "active") and not run and not paused

        def _draw(cv=banner, a=act, r=run, p=paused, qs=can_quickstart):
            try:
                if not cv.winfo_exists():
                    return
                cv.delete("all")
            except tk.TclError:
                return
            width = cv.winfo_width() or 210
            dark = darken(a["color"], 0.75)
            _grad_line(cv, 0, 0, width, 52, dark, a["color"])
            cv.create_rectangle(0, 0, 20, 52, fill=dark, outline="", stipple="gray50")
            cv.create_rectangle(width - 20, 0, width, 52, fill=dark, outline="", stipple="gray50")
            cv.create_text(16, 26, text=a["emoji"], font=(FONT_EMOJI, 22), anchor="w")
            cv.create_text(48, 14, text=a["name"][:16], font=(FONT_UI, 11, "bold"), fill="#ffffff", anchor="w")
            base = a["total_s"] + self.timer.elapsed(aid)
            tc = GREEN if r else (ORANGE if p else blend("#ffffff", dark, 0.82))
            cv.create_text(48, 34, text=fmt_h(base), font=(FONT_MONO, 10), fill=tc, anchor="w")
            if r:
                cv.create_oval(width - 18, 20, width - 8, 30, fill=GREEN, outline="")
            elif p:
                cv.create_text(width - 10, 26, text="⏸", font=(FONT_EMOJI, 10), fill=ORANGE, anchor="e")
            elif qs:
                # Быстрый старт прямо из карточки
                cv.create_text(width - 13, 26, text="▶", font=(FONT_UI, 13, "bold"),
                               fill=blend("#ffffff", dark, 0.9), anchor="e", tags="qs")
                # "break" — чтобы клик по ▶ не «проваливался» в открытие карточки
                cv.tag_bind("qs", "<Button-1>", lambda e, i=aid: (self._quick_start(i), "break")[1])

        banner.bind("<Configure>", lambda e: _draw())
        self.root.after(30, _draw)

        self._side_refs[aid] = {"canvas": banner, "draw": _draw, "base": act["total_s"]}

        for w in [outer, banner]:
            w.bind("<Button-1>", lambda e, a=dict(act): self._open_project(a["id"]))
            w.bind("<Button-3>", lambda e, a=dict(act): self._sb_context_menu(e, a))

    def _sb_context_menu(self, event, act):
        menu = tk.Menu(
            self.root, tearoff=0,
            bg=SURF2, fg=TEXT, activebackground=SURF3, activeforeground=TEXT,
            relief="flat", bd=0, font=(FONT_UI, 10)
        )
        if act["status"] == "active":
            if self.timer.is_active(act["id"]):
                menu.add_command(label="  ⏹  Остановить",
                                 command=lambda: self._stop(act["id"]))
            else:
                menu.add_command(label="  ▶  Запустить",
                                 command=lambda: self._quick_start(act["id"]))
            menu.add_separator()
        menu.add_command(label="  ✎  Переименовать", command=lambda: self._rename_dialog(act))
        menu.add_separator()
        menu.add_command(
            label=f"  ✕  Переместить в удалённые «{act['name']}»",
            command=lambda: self._delete(act["id"], act["name"]),
            foreground=RED, activeforeground=RED
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _rename_dialog(self, act):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Переименовать")
        dialog.configure(fg_color=SURF)
        dialog.geometry("320x140")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + self.root.winfo_width() // 2 - 160
        y = self.root.winfo_rooty() + self.root.winfo_height() // 2 - 70
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dialog, text="Новое название:", text_color=MUTED, font=_f(10)).pack(anchor="w", padx=16, pady=(16, 4))
        name_var = ctk.StringVar(value=act["name"])
        entry = ctk.CTkEntry(
            dialog, textvariable=name_var, fg_color=SURF2, border_color=BORDER,
            text_color=TEXT, font=_f(12), width=280
        )
        entry.pack(padx=16, pady=(0, 12))
        entry.focus()
        entry.select_range(0, "end")

        def do_rename():
            new_name = name_var.get().strip()
            if not new_name:
                return
            self.db.update_activity(act["id"], new_name, act["emoji"], act["color"], act["goal_h"])
            dialog.destroy()
            self._reload_sidebar(keep_detail=False)
            if self.sel_id == act["id"]:
                fresh = self.db.get_activity(act["id"])
                if fresh:
                    if self._view_mode == "project":
                        self._show_detail(dict(fresh))
                    else:
                        self._render_current_view()

        bf = ctk.CTkFrame(dialog, fg_color="transparent")
        bf.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkButton(
            bf, text="Отмена", width=100, height=30, fg_color=SURF2,
            text_color=MUTED, hover_color=SURF3, border_width=1,
            border_color=BORDER, corner_radius=6, command=dialog.destroy
        ).pack(side="left")
        ctk.CTkButton(
            bf, text="Сохранить", width=120, height=30, fg_color=ACCENT,
            text_color="#000", hover_color="#81d4fa", corner_radius=6,
            font=_f(11, bold=True), command=do_rename
        ).pack(side="right")

        dialog.bind("<Return>", lambda e: do_rename())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def _open_project(self, aid: int):
        self.sel_id = aid
        self._view_mode = "project"
        self._sync_nav_buttons()
        self._reload_sidebar(keep_detail=False)
        fresh = self.db.get_activity(aid)
        if fresh:
            self._show_detail(dict(fresh))

    # ══════════════════════════════════════════════════════════════════════════
    #  Utility UI
    # ══════════════════════════════════════════════════════════════════════════
    def _clear_detail(self):
        for w in self._dzone.winfo_children():
            w.destroy()
        self._dt_aid = self._dt_time_lbl = self._dt_today_lbl = None
        self._dt_sess_lbl = self._pomo_lbl = None
        self._pomo_aid = None

    def _status_meta(self, act):
        status = act["status"]
        if status == "deleted":
            return "Удалён", RED
        if status == "completed":
            return "Завершён", GREEN
        return "Активный", ACCENT

    def _metric_card(self, parent, title, value, color=TEXT):
        card = ctk.CTkFrame(parent, fg_color=SURF, corner_radius=10, border_width=1, border_color=BORDER)
        card.pack(side="left", fill="both", expand=True, padx=6)
        ctk.CTkLabel(card, text=title, text_color=MUTED, font=_f(9)).pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(card, text=value, text_color=color, font=_f(20, bold=True)).pack(anchor="w", padx=14, pady=(0, 12))
        return card

    def _project_summary_row(self, parent, act, *, show_status_badge=True):
        status_text, status_color = self._status_meta(act)
        row = ctk.CTkFrame(parent, fg_color=SURF, corner_radius=10, border_width=1, border_color=BORDER)
        row.pack(fill="x", pady=4)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=12, pady=10)

        top = ctk.CTkFrame(left, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=f"{act['emoji']}  {act['name']}", text_color=TEXT, font=_f(12, bold=True)).pack(side="left")
        if show_status_badge:
            badge = ctk.CTkFrame(top, fg_color=darken(status_color, 0.65), corner_radius=6)
            badge.pack(side="right")
            ctk.CTkLabel(badge, text=f" {status_text} ", text_color=status_color, font=_f(10, bold=True)).pack()

        mid = ctk.CTkFrame(left, fg_color="transparent")
        mid.pack(fill="x", pady=(6, 0))
        today_s = self.db.get_today_total(act["id"])
        week_s = self.db.get_week_total(act["id"])
        sessions = self.db.get_session_count(act["id"])
        goal_txt = f"{act['goal_h']:.0f}ч" if act["goal_h"] else "—"
        ctk.CTkLabel(
            mid,
            text=f"Всего: {fmt_h(act['total_s'])}   •   Сегодня: {fmt_h(today_s)}   •   Неделя: {fmt_h(week_s)}   •   Сессии: {sessions}   •   Цель: {goal_txt}",
            text_color=MUTED,
            font=_f(10),
            anchor="w",
        ).pack(side="left")

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=10, pady=10)

        if act["status"] == "active" and not self.timer.is_active(act["id"]):
            ctk.CTkButton(
                actions, text="▶", width=40, height=30,
                fg_color=GREEN, text_color="#000", hover_color="#33eb91",
                corner_radius=8, font=_f(13, bold=True),
                command=lambda aid=act["id"]: self._quick_start(aid)
            ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            actions, text="Открыть", width=90, height=30,
            fg_color=SURF2, text_color=TEXT, hover_color=SURF3,
            border_width=1, border_color=BORDER, corner_radius=8,
            command=lambda aid=act["id"]: self._open_project(aid)
        ).pack(side="left", padx=(0, 6))

        if act["status"] == "deleted":
            ctk.CTkButton(
                actions, text="Восстановить", width=110, height=30,
                fg_color=ACCENT, text_color="#000", hover_color="#81d4fa",
                corner_radius=8, command=lambda aid=act["id"]: self._restore(aid)
            ).pack(side="left")
        else:
            ctk.CTkButton(
                actions, text="Удалить", width=90, height=30,
                fg_color=SURF2, text_color=RED, hover_color=SURF3,
                border_width=1, border_color=RED, corner_radius=8,
                command=lambda aid=act["id"], name=act["name"]: self._delete(aid, name)
            ).pack(side="left")

    # ══════════════════════════════════════════════════════════════════════════
    #  Library page
    # ══════════════════════════════════════════════════════════════════════════
    def _sort_acts(self, acts: list) -> list:
        """Сортирует список проектов по текущим _lib_sort_key / _lib_sort_asc."""
        key = self._lib_sort_key
        rev = not self._lib_sort_asc  # по умолчанию убывание
        if key == "total_s":
            return sorted(acts, key=lambda a: a["total_s"], reverse=rev)
        if key == "name":
            return sorted(acts, key=lambda a: a["name"].lower(), reverse=not self._lib_sort_asc)
        if key == "created":
            return sorted(acts, key=lambda a: a.get("created") or "", reverse=rev)
        if key == "status":
            order = {"active": 0, "completed": 1, "deleted": 2}
            return sorted(acts, key=lambda a: order.get(a["status"], 9), reverse=not self._lib_sort_asc)
        return acts

    def _lib_sort_btn(self, parent, label: str, key: str, redraw_fn):
        """Кнопка сортировки с индикатором направления."""
        active = self._lib_sort_key == key
        arrow = (" ↑" if self._lib_sort_asc else " ↓") if active else ""
        b = ctk.CTkButton(
            parent, text=label + arrow,
            height=28, font=_f(10, bold=active),
            fg_color=SURF2 if not active else darken(ACCENT, 0.5),
            text_color=ACCENT if active else MUTED,
            hover_color=SURF3,
            border_width=1,
            border_color=ACCENT if active else BORDER,
            corner_radius=7,
        )
        def _click():
            if self._lib_sort_key == key:
                self._lib_sort_asc = not self._lib_sort_asc
            else:
                self._lib_sort_key = key
                self._lib_sort_asc = False
            redraw_fn()
        b.configure(command=_click)
        return b

    def _show_library_page(self):
        self._clear_detail()

        header = ctk.CTkFrame(self._dzone, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 8))
        ctk.CTkLabel(header, text="Библиотека проектов", text_color=TEXT, font=_f(22, bold=True)).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Все проекты и их текущий статус: активные, завершённые и удалённые.",
            text_color=MUTED, font=_f(11)
        ).pack(anchor="w", pady=(4, 0))

        acts_raw = [dict(a) for a in self.db.get_activities(include_deleted=True)]
        active_count    = sum(1 for a in acts_raw if a["status"] == "active")
        completed_count = sum(1 for a in acts_raw if a["status"] == "completed")
        deleted_count   = sum(1 for a in acts_raw if a["status"] == "deleted")

        cards_row = ctk.CTkFrame(self._dzone, fg_color="transparent")
        cards_row.pack(fill="x", padx=14, pady=(0, 10))
        self._metric_card(cards_row, "Всего проектов", str(len(acts_raw)), ACCENT)
        self._metric_card(cards_row, "Активные",       str(active_count),    ACCENT)
        self._metric_card(cards_row, "Завершённые",    str(completed_count), GREEN)
        self._metric_card(cards_row, "Удалённые",      str(deleted_count),   RED)

        # ── Панель сортировки ────────────────────────────────────────────────
        sort_bar = ctk.CTkFrame(self._dzone, fg_color="transparent")
        sort_bar.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(sort_bar, text="Сортировка:", text_color=MUTED, font=_f(9)).pack(side="left", padx=(0, 8))

        # Список (будет перерисован). Держим ссылку чтобы передать в кнопки.
        lst_container = [None]

        def redraw_list():
            if lst_container[0]:
                lst_container[0].destroy()
            lst = ctk.CTkFrame(self._dzone, fg_color=BG, corner_radius=0)
            lst.pack(fill="x", padx=20, pady=4)
            lst_container[0] = lst
            acts = self._sort_acts(acts_raw)
            if not acts:
                ctk.CTkLabel(lst, text="Проектов пока нет.", text_color=MUTED, font=_f(12)).pack(anchor="w")
                return
            for act in acts:
                self._project_summary_row(lst, act)
            # Обновить кнопки сортировки (стрелки)
            for w in sort_bar.winfo_children():
                if isinstance(w, ctk.CTkButton):
                    w.destroy()
            _build_sort_buttons()

        def _build_sort_buttons():
            for sk, sl in [("total_s", "По времени"), ("name", "По имени"),
                           ("created", "По дате"), ("status", "По статусу")]:
                self._lib_sort_btn(sort_bar, sl, sk, redraw_list).pack(side="left", padx=3)

        _build_sort_buttons()
        redraw_list()

    # ══════════════════════════════════════════════════════════════════════════
    #  Stats page
    # ══════════════════════════════════════════════════════════════════════════
    def _show_stats_page(self):
        self._clear_detail()

        header = ctk.CTkFrame(self._dzone, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 12))
        ctk.CTkLabel(header, text="Статистика", text_color=TEXT, font=_f(22, bold=True)).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Общая статистика по всем проектам. Можно открыть любой проект и посмотреть детали отдельно.",
            text_color=MUTED, font=_f(11)
        ).pack(anchor="w", pady=(4, 0))

        st = self.db.get_overall_stats()
        cards = ctk.CTkFrame(self._dzone, fg_color="transparent")
        cards.pack(fill="x", padx=14, pady=(0, 10))
        self._metric_card(cards, "Общее время", fmt_h(st["total_s"]), ACCENT)
        self._metric_card(cards, "Сегодня", fmt_h(st["today_s"]), GREEN if st["today_s"] else MUTED)
        self._metric_card(cards, "За 7 дней", fmt_h(st["week_s"]), ACCENT)
        self._metric_card(cards, "Сессии", str(st["sessions"]), TEXT)

        chart_wrap = ctk.CTkFrame(self._dzone, fg_color=BG, corner_radius=0)
        chart_wrap.pack(fill="x", padx=20, pady=(4, 12))
        top = ctk.CTkFrame(chart_wrap, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text="📈  ОБЩАЯ АКТИВНОСТЬ", text_color=MUTED, font=_f(9)).pack(side="left")
        ctk.CTkLabel(top, text="28 дней", text_color=MUTED, font=_f(9)).pack(side="right")
        chart = tk.Canvas(chart_wrap, bg=SURF, height=120, highlightthickness=0)
        chart.pack(fill="x", pady=(6, 0))
        chart.bind("<Configure>", lambda e: self._draw_overall_chart(chart))
        self.root.after(60, lambda: self._draw_overall_chart(chart))

        lst = ctk.CTkFrame(self._dzone, fg_color=BG, corner_radius=0)
        lst.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(lst, text="ПРОЕКТЫ", text_color=MUTED, font=_f(9)).pack(anchor="w", pady=(0, 6))
        for act in [dict(a) for a in self.db.get_activities(include_deleted=False)]:
            self._project_summary_row(lst, act, show_status_badge=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  Project detail
    # ══════════════════════════════════════════════════════════════════════════
    def _show_empty(self):
        self._clear_detail()
        f = ctk.CTkFrame(self._dzone, fg_color="transparent")
        f.pack(expand=True, fill="both")
        ctk.CTkLabel(f, text="⌚", font=_f(52), text_color=ACCENT).pack(pady=(80, 8))
        ctk.CTkLabel(f, text="Выбери проект из библиотеки", text_color=TEXT, font=_f(15, bold=True), justify="center").pack()
        ctk.CTkLabel(f, text="или создай новый — нажми  ＋  в левой панели", text_color=MUTED, font=_f(12), justify="center").pack(pady=(4, 0))

    def _show_detail(self, act):
        self._clear_detail()
        aid = act["id"]
        color = act["color"]
        run = self.timer.is_running(aid)
        paused = self.timer.is_paused(aid)
        self._dt_aid = aid

        hero = tk.Canvas(self._dzone, height=180, bg=BG, highlightthickness=0)
        hero.pack(fill="x")

        def _draw_hero(cv=hero):
            try:
                if not cv.winfo_exists():
                    return
                cv.delete("all")
            except tk.TclError:
                return
            width = cv.winfo_width() or 740
            height = 180
            dark = darken(color, 0.82)
            mid = darken(color, 0.55)
            _grad_line(cv, 0, 0, width // 2, height, dark, mid)
            _grad_line(cv, width // 2, 0, width, height, mid, color)
            # Тонкие скан-линии (Tk не умеет альфу → stipple даёт полупрозрачность)
            for y in range(0, height, 4):
                cv.create_line(0, y, width, y, fill="#000000", width=1, stipple="gray25")
            for i in range(40):
                t = i / 40
                yy = height - 60 + int(60 * t)
                cv.create_rectangle(
                    0, yy, width, yy + 2,
                    fill=f"#{int(11*(1-t)):02x}{int(13*(1-t)):02x}{int(18*(1-t)):02x}",
                    outline=""
                )
            cv.create_text(32, height // 2 - 10, text=act["emoji"], font=(FONT_EMOJI, 54), anchor="w")
            cv.create_text(110, height // 2 - 22, text=act["name"], font=(FONT_UI, 22, "bold"), fill="#ffffff", anchor="w")
            if run:
                cv.create_oval(110, height // 2 + 4, 122, height // 2 + 16, fill=GREEN, outline="")
                cv.create_text(128, height // 2 + 10, text="ИДЁТ", font=(FONT_MONO, 10), fill=GREEN, anchor="w")
            elif paused:
                cv.create_text(110, height // 2 + 10, text="⏸ ПАУЗА", font=(FONT_MONO, 10), fill=ORANGE, anchor="w")
            else:
                status_text, status_color = self._status_meta(act)
                cv.create_text(110, height // 2 + 10, text=status_text.upper(), font=(FONT_MONO, 10), fill=status_color, anchor="w")
            cv.create_text(width - 14, height - 12, text=f"с {act['created']}", font=(FONT_MONO, 9), fill=blend("#ffffff", color, 0.5), anchor="se")
            cv.create_text(width - 14, 16, text="✎  ✕", font=(FONT_UI, 11), fill=blend("#ffffff", color, 0.6), anchor="ne", tags="edit_area")
            cv.tag_bind("edit_area", "<Button-1>", lambda e: self._hero_menu(e, act))

        hero.bind("<Configure>", lambda e: _draw_hero())
        self.root.after(30, _draw_hero)

        ctrl = ctk.CTkFrame(self._dzone, fg_color=SURF, corner_radius=0, border_width=0)
        ctrl.pack(fill="x")

        lc = ctk.CTkFrame(ctrl, fg_color="transparent")
        lc.pack(side="left", padx=18, pady=14)

        if run:
            ctk.CTkButton(lc, text="⏸", width=44, height=44, fg_color=SURF2, text_color=ORANGE,
                          hover_color=SURF3, font=_f(20), border_width=1, border_color=ORANGE,
                          corner_radius=10, command=lambda: self._pause(aid)).pack(side="left", padx=(0, 8))
            ctk.CTkButton(lc, text="⏹", width=44, height=44, fg_color=SURF2, text_color=RED,
                          hover_color=SURF3, font=_f(20), border_width=1, border_color=RED,
                          corner_radius=10, command=lambda: self._stop(aid)).pack(side="left", padx=(0, 14))
            self._dt_sess_lbl = ctk.CTkLabel(lc, text=fmt_hms(self.timer.elapsed(aid)), text_color=GREEN, font=_f(26, bold=True))
            self._dt_sess_lbl.pack(side="left")
        elif paused:
            ctk.CTkButton(lc, text="▶", width=44, height=44, fg_color=GREEN, text_color="#000",
                          hover_color="#33eb91", font=_f(20, bold=True), corner_radius=10,
                          command=lambda: self._resume(aid)).pack(side="left", padx=(0, 8))
            ctk.CTkButton(lc, text="⏹", width=44, height=44, fg_color=SURF2, text_color=RED,
                          hover_color=SURF3, font=_f(20), border_width=1, border_color=RED,
                          corner_radius=10, command=lambda: self._stop(aid)).pack(side="left", padx=(0, 14))
            ctk.CTkLabel(lc, text=f"⏸  {fmt_hms(self.timer.elapsed(aid))}", text_color=ORANGE, font=_f(20, bold=True)).pack(side="left")
        else:
            ctk.CTkButton(lc, text="▶  СТАРТ", width=140, height=48, fg_color=GREEN, text_color="#000",
                          hover_color="#33eb91", font=_f(15, bold=True), corner_radius=10,
                          command=lambda: self._start(aid)).pack(side="left")

        rc = ctk.CTkFrame(ctrl, fg_color="transparent")
        rc.pack(side="right", padx=18, pady=14)
        ctk.CTkLabel(rc, text="🍅", font=_f(16), text_color=MUTED).pack(side="left", padx=(0, 6))
        for lab, dur in [("25м", 25 * 60), ("50м", 50 * 60), ("90м", 90 * 60)]:
            ctk.CTkButton(rc, text=lab, width=48, height=32, fg_color=SURF2, text_color=MUTED,
                          hover_color=SURF3, font=_f(11), border_width=1, border_color=BORDER,
                          corner_radius=8, command=lambda d=dur: self._pomo_start(aid, d)).pack(side="left", padx=2)
        end_ts = self._pomos.get(aid)
        if end_ts and end_ts - time.time() > 0:
            rem = int(end_ts - time.time())
            self._pomo_lbl = ctk.CTkLabel(rc, text=f"  ⏱ {fmt_hms(rem)}", text_color=ORANGE, font=_f(12, bold=True))
            self._pomo_lbl.pack(side="left")
            self._pomo_aid = aid

        status = act["status"]
        project_actions = ctk.CTkFrame(self._dzone, fg_color=BG, corner_radius=0)
        project_actions.pack(fill="x", padx=20, pady=(10, 0))
        actions_left = ctk.CTkFrame(project_actions, fg_color="transparent")
        actions_left.pack(side="left")

        if status == "active":
            ctk.CTkButton(
                actions_left, text="Завершить проект", width=160, height=32,
                fg_color=SURF2, text_color=GREEN, hover_color=SURF3,
                border_width=1, border_color=GREEN, corner_radius=8,
                command=lambda: self._complete_project(aid)
            ).pack(side="left")
        elif status == "completed":
            ctk.CTkButton(
                actions_left, text="Вернуть в активные", width=170, height=32,
                fg_color=SURF2, text_color=ACCENT, hover_color=SURF3,
                border_width=1, border_color=ACCENT, corner_radius=8,
                command=lambda: self._reopen_project(aid)
            ).pack(side="left")

        ctk.CTkFrame(self._dzone, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        base_s = act["total_s"] + self.timer.elapsed(aid)
        today_s = self.db.get_today_total(aid) + (self.timer.elapsed(aid) if self.timer.is_active(aid) else 0)
        week_s = self.db.get_week_total(aid)
        streak = self.db.get_streak(aid)
        n_sess = self.db.get_session_count(aid)

        stats_row = ctk.CTkFrame(self._dzone, fg_color=SURF, corner_radius=0)
        stats_row.pack(fill="x")

        stat_items = [
            ("ВСЕГО", fmt_h(base_s), color, True),
            ("СЕГОДНЯ", fmt_h(today_s), GREEN if today_s else MUTED, False),
            ("НЕДЕЛЯ", fmt_h(week_s), ACCENT, False),
            ("🔥 STREAK", f"{streak}д", ORANGE if streak >= 3 else (GREEN if streak else MUTED), False),
            ("СЕССИЙ", str(n_sess), MUTED, False),
        ]

        for i, (label, val, col, is_main) in enumerate(stat_items):
            sf = ctk.CTkFrame(stats_row, fg_color="transparent")
            sf.pack(side="left", padx=16, pady=14, expand=True)
            ctk.CTkLabel(sf, text=label, text_color=MUTED, font=_f(9)).pack()
            tl = ctk.CTkLabel(sf, text=val, text_color=col, font=_f(24 if is_main else 18, bold=True))
            tl.pack()
            if is_main:
                self._dt_time_lbl = tl
                self._dt_base_s = act["total_s"]
            if label == "СЕГОДНЯ":
                self._dt_today_lbl = tl
                self._dt_today_base = self.db.get_today_total(aid)
            if i < len(stat_items) - 1:
                ctk.CTkFrame(stats_row, fg_color=BORDER, width=1, corner_radius=0).pack(side="left", fill="y", pady=8)

        ctk.CTkFrame(self._dzone, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        if act["goal_h"] > 0:
            gf = ctk.CTkFrame(self._dzone, fg_color=BG, corner_radius=0)
            gf.pack(fill="x", padx=20, pady=10)
            done_h = act["total_s"] / 3600
            frac = min(done_h / act["goal_h"], 1.0)
            pct = int(frac * 100)
            gh = ctk.CTkFrame(gf, fg_color="transparent")
            gh.pack(fill="x")
            ctk.CTkLabel(gh, text="🎯  ЦЕЛЬ", text_color=MUTED, font=_f(9)).pack(side="left")
            ctk.CTkLabel(
                gh, text=f"{done_h:.1f} / {act['goal_h']:.0f} ч  ({pct}%)",
                text_color=GREEN if frac >= 1 else color, font=_f(11, bold=True)
            ).pack(side="right")
            pb = ctk.CTkProgressBar(gf, progress_color=GREEN if frac >= 1 else color, fg_color=SURF2, height=12, corner_radius=6)
            pb.pack(fill="x", pady=(6, 0))
            pb.set(frac)
            ctk.CTkFrame(self._dzone, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        cf = ctk.CTkFrame(self._dzone, fg_color=BG, corner_radius=0)
        cf.pack(fill="x", padx=20, pady=10)
        ch = ctk.CTkFrame(cf, fg_color="transparent")
        ch.pack(fill="x")
        ctk.CTkLabel(ch, text="📊  АКТИВНОСТЬ", text_color=MUTED, font=_f(9)).pack(side="left")
        ctk.CTkLabel(ch, text="28 дней", text_color=MUTED, font=_f(9)).pack(side="right")
        chart = tk.Canvas(cf, bg=SURF, height=100, highlightthickness=0)
        chart.pack(fill="x", pady=(6, 0))
        chart.bind("<Configure>", lambda e: self._draw_chart(chart, aid, color))
        self.root.after(60, lambda: self._draw_chart(chart, aid, color))

        ctk.CTkFrame(self._dzone, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        pf = ctk.CTkFrame(self._dzone, fg_color=BG, corner_radius=0)
        pf.pack(fill="x", padx=20, pady=8)
        ph = ctk.CTkFrame(pf, fg_color="transparent")
        ph.pack(fill="x")
        ctk.CTkLabel(ph, text="📌  ПЛАН НА СЕГОДНЯ", text_color=MUTED, font=_f(9)).pack(side="left")
        self._plan_btn = ctk.CTkButton(
            ph, text="Сохранить", width=90, height=26,
            fg_color=SURF2, text_color=MUTED, hover_color=SURF3,
            font=_f(10), border_width=1, border_color=BORDER, corner_radius=6,
            command=lambda: self._save_plan(aid)
        )
        self._plan_btn.pack(side="right")
        self._plan_txt = ctk.CTkTextbox(
            pf, height=64, fg_color=SURF2, border_color=BORDER,
            border_width=1, text_color=TEXT, font=_f(11), corner_radius=8
        )
        self._plan_txt.pack(fill="x", pady=(4, 0))
        if act.get("day_plan"):
            self._plan_txt.insert("1.0", act["day_plan"])

        ctk.CTkFrame(self._dzone, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        sf2 = ctk.CTkFrame(self._dzone, fg_color=BG, corner_radius=0)
        sf2.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(sf2, text="ИСТОРИЯ СЕССИЙ", text_color=MUTED, font=_f(9)).pack(anchor="w", pady=(0, 6))

        sessions = self.db.get_sessions(aid)
        if not sessions:
            ctk.CTkLabel(sf2, text="Нет сессий — нажми СТАРТ", text_color=MUTED, font=_f(11)).pack(anchor="w")
        else:
            for s in sessions:
                self._session_row(sf2, s, color)

    # ══════════════════════════════════════════════════════════════════════════
    #  Charts
    # ══════════════════════════════════════════════════════════════════════════
    def _draw_chart(self, canvas, aid, color):
        try:
            if not canvas.winfo_exists():
                return
            canvas.delete("all")
        except tk.TclError:
            return
        width = canvas.winfo_width() or 680
        height = 100
        rows = self.db.get_daily_totals(aid, days=28)
        dm = {r["day"]: r["total"] for r in rows}
        days = [date.today() - timedelta(days=27 - i) for i in range(28)]
        vals = [dm.get(str(d), 0) for d in days]
        mx = max(vals) if any(vals) else 1
        pl, pr, pb = 6, 6, 22
        bw = (width - pl - pr) / 28

        for i, (d, v) in enumerate(zip(days, vals)):
            x0 = pl + i * bw + bw * 0.12
            x1 = pl + i * bw + bw * 0.88
            frac = v / mx if mx else 0
            bh = max(frac * (height - pb - 8), 2) if v else 0
            today = d == date.today()
            col = GREEN if today else color

            if bh:
                steps = max(int(bh), 4)
                dc = darken(col, 0.4)
                r1, g1, b1 = hex_to_rgb(dc)
                r2, g2, b2 = hex_to_rgb(col)
                for j in range(steps):
                    t = j / steps
                    r = int(r1 + (r2 - r1) * t)
                    g = int(g1 + (g2 - g1) * t)
                    b = int(b1 + (b2 - b1) * t)
                    y0j = height - pb - bh + int(bh * j / steps)
                    y1j = height - pb - bh + int(bh * (j + 1) / steps)
                    canvas.create_rectangle(x0, y0j, x1, y1j, fill=f"#{r:02x}{g:02x}{b:02x}", outline="")

            if today or d.day in (1, 8, 15, 22):
                cx = (x0 + x1) / 2
                canvas.create_text(cx, height - pb + 10, text="сег" if today else d.strftime("%d"),
                                   fill=GREEN if today else MUTED, font=(FONT_MONO, 8))

        canvas.create_line(pl, height - pb, width - pr, height - pb, fill=BORDER, width=1)
        if mx:
            canvas.create_text(width - pr, 6, text=fmt_h(mx), fill=MUTED, font=(FONT_MONO, 8), anchor="ne")

    def _draw_overall_chart(self, canvas):
        try:
            if not canvas.winfo_exists():
                return
            canvas.delete("all")
        except tk.TclError:
            return
        width = canvas.winfo_width() or 680
        height = 120
        rows = self.db.get_all_daily_totals(days=28)
        dm = {r["day"]: r["total"] for r in rows}
        days = [date.today() - timedelta(days=27 - i) for i in range(28)]
        vals = [dm.get(str(d), 0) for d in days]
        mx = max(vals) if any(vals) else 1
        pl, pr, pb = 10, 10, 22
        bw = (width - pl - pr) / 28

        for i, (d, v) in enumerate(zip(days, vals)):
            x0 = pl + i * bw + bw * 0.16
            x1 = pl + i * bw + bw * 0.84
            frac = v / mx if mx else 0
            bh = max(frac * (height - pb - 8), 2) if v else 0
            col = GREEN if d == date.today() else ACCENT
            if bh:
                steps = max(int(bh), 4)
                dc = darken(col, 0.45)
                r1, g1, b1 = hex_to_rgb(dc)
                r2, g2, b2 = hex_to_rgb(col)
                for j in range(steps):
                    t = j / steps
                    r = int(r1 + (r2 - r1) * t)
                    g = int(g1 + (g2 - g1) * t)
                    b = int(b1 + (b2 - b1) * t)
                    y0j = height - pb - bh + int(bh * j / steps)
                    y1j = height - pb - bh + int(bh * (j + 1) / steps)
                    canvas.create_rectangle(x0, y0j, x1, y1j, fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
            if d == date.today() or d.day in (1, 8, 15, 22):
                canvas.create_text((x0 + x1) / 2, height - pb + 10, text="сег" if d == date.today() else d.strftime("%d"),
                                   fill=GREEN if d == date.today() else MUTED, font=(FONT_MONO, 8))

        canvas.create_line(pl, height - pb, width - pr, height - pb, fill=BORDER, width=1)
        canvas.create_text(width - pr, 6, text=fmt_h(mx), fill=MUTED, font=(FONT_MONO, 8), anchor="ne")

    # ══════════════════════════════════════════════════════════════════════════
    #  Session row
    # ══════════════════════════════════════════════════════════════════════════
    def _session_row(self, parent, s, color):
        row = ctk.CTkFrame(parent, fg_color=SURF2, corner_radius=8, border_width=1, border_color=BORDER)
        row.pack(fill="x", pady=2)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", padx=12, pady=6, fill="x", expand=True)

        top = ctk.CTkFrame(left, fg_color="transparent")
        top.pack(fill="x")

        started = (s["started_at"] or "?")[:16]
        dur = fmt_hms(s["duration_s"] or 0)
        note = s["note"] or ""
        nd = (note[:52] + "…") if len(note) > 52 else (note or "—")

        ctk.CTkLabel(top, text=started, text_color=MUTED, font=_f(10), width=120, anchor="w").pack(side="left")

        badge = ctk.CTkFrame(top, fg_color=darken(color, 0.5), corner_radius=4)
        badge.pack(side="left", padx=6)
        ctk.CTkLabel(badge, text=f" {dur} ", text_color=color, font=_f(10, bold=True)).pack()

        nl = ctk.CTkLabel(left, text=nd, text_color=TEXT if note else MUTED, font=_f(10), anchor="w", wraplength=480)
        nl.pack(anchor="w")

        ctk.CTkButton(
            row, text="✎", width=30, height=30,
            fg_color="transparent", text_color=MUTED2, hover_color=SURF3,
            font=_f(12), corner_radius=6,
            command=lambda sid=s["id"], lbl=nl: self._edit_note(sid, lbl)
        ).pack(side="right", padx=8)

        ctk.CTkFrame(parent, fg_color=MUTED2, height=1, corner_radius=0).pack(fill="x", pady=1)

    # ══════════════════════════════════════════════════════════════════════════
    #  Actions
    # ══════════════════════════════════════════════════════════════════════════
    def _start(self, aid):
        act = self.db.get_activity(aid)
        if not act:
            return
        if act["status"] == "deleted":
            messagebox.showwarning("Проект удалён", "Сначала восстанови проект из библиотеки.")
            return
        if act["status"] == "completed":
            messagebox.showinfo("Проект завершён", "Верни проект в активные, чтобы снова запустить таймер.")
            return
        self.timer.start(aid)
        self._reload_sidebar(keep_detail=False)
        self._refresh_detail(aid)

    def _pause(self, aid):
        self.timer.pause(aid)
        self._reload_sidebar(keep_detail=False)
        self._refresh_detail(aid)

    def _resume(self, aid):
        self.timer.resume(aid)
        self._reload_sidebar(keep_detail=False)
        self._refresh_detail(aid)

    def _quick_start(self, aid):
        """Быстрый старт: открыть проект и сразу запустить таймер."""
        self._open_project(aid)
        self._start(aid)

    def _stop(self, aid):
        data = self.timer.stop(aid)
        self._pomos.pop(aid, None)
        if self._pomo_aid == aid:
            self._pomo_lbl = None
            self._pomo_aid = None
        if not data:
            return

        before = self.db.get_activity(aid)
        before_total = before["total_s"] if before else 0
        goal_s = (before["goal_h"] * 3600) if before and before["goal_h"] else 0

        def after_note(note):
            self.db.log_session(aid, data["started_at"], data["ended_at"], data["duration_s"], note)
            self._reload_sidebar(keep_detail=False)
            fresh = self.db.get_activity(aid)
            if fresh:
                self._show_detail(dict(fresh))
                # Уведомление при достижении цели по часам
                if goal_s and before_total < goal_s <= fresh["total_s"]:
                    messagebox.showinfo(
                        "🎯 Цель достигнута!",
                        f"«{fresh['name']}» — пройдено {fresh['goal_h']:.0f} ч. Так держать! 🔥"
                    )

        NoteDialog(self.root, data["duration_s"], after_note)

    def _refresh_detail(self, aid):
        fresh = self.db.get_activity(aid)
        if fresh:
            self._show_detail(dict(fresh))

    def _complete_project(self, aid):
        act = self.db.get_activity(aid)
        if not act:
            return
        if self.timer.is_active(aid):
            messagebox.showinfo("Активная сессия", "Сначала останови или поставь на паузу текущую сессию.")
            return
        if not messagebox.askyesno("Завершить проект", f"Отметить проект «{act['name']}» как завершённый?"):
            return
        self.db.complete_activity(aid)
        self._reload_sidebar(keep_detail=False)
        self._refresh_detail(aid)

    def _reopen_project(self, aid):
        act = self.db.get_activity(aid)
        if not act:
            return
        self.db.reopen_activity(aid)
        self._reload_sidebar(keep_detail=False)
        self._refresh_detail(aid)

    def _save_plan(self, aid):
        self.db.update_day_plan(aid, self._plan_txt.get("1.0", "end").strip())
        self._plan_btn.configure(text_color=GREEN)
        self.root.after(1200, lambda: self._plan_btn.configure(text_color=MUTED))

    def _add(self):
        def on_save(name, emoji, color, goal_h):
            self.db.add_activity(name, emoji, color, goal_h)
            self._reload_sidebar(keep_detail=False)
            self._set_view("library")
        ActivityDialog(self.root, on_save)

    def _edit_activity(self, act):
        def on_save(name, emoji, color, goal_h):
            self.db.update_activity(act["id"], name, emoji, color, goal_h)
            self._reload_sidebar(keep_detail=False)
            fresh = self.db.get_activity(act["id"])
            if fresh:
                self._show_detail(dict(fresh))
        ActivityDialog(self.root, on_save, act=act)

    def _delete(self, aid, name):
        if messagebox.askyesno("Удалить", f"Переместить «{name}» в удалённые?\nСессии сохранятся, проект можно восстановить."):
            # Не теряем активную сессию — сохраняем её перед удалением.
            data = self.timer.stop(aid)
            if data:
                try:
                    self.db.log_session(aid, data["started_at"], data["ended_at"],
                                        data["duration_s"], "(сохранено при удалении)")
                except Exception as e:  # noqa: BLE001
                    log.error("delete: log_session aid=%s: %s", aid, e)
            self._pomos.pop(aid, None)
            self.db.delete_activity(aid)
            if self.sel_id == aid:
                self.sel_id = None
            self._reload_sidebar(keep_detail=False)
            self._set_view("library")

    def _restore(self, aid):
        self.db.restore_activity(aid)
        self._reload_sidebar(keep_detail=False)
        self._set_view("library")

    def _edit_note(self, sid, lbl):
        current = self.db.get_session_note(sid)

        def on_save(note):
            self.db.update_session_note(sid, note)
            nd = (note[:52] + "…") if len(note) > 52 else (note or "—")
            lbl.configure(text=nd, text_color=TEXT if note else MUTED)

        EditNoteDialog(self.root, current, on_save)

    def _pomo_start(self, aid, dur):
        self._pomos[aid] = time.time() + dur
        if not self.timer.is_active(aid):
            self._start(aid)        # _start перерисует детали и покажет таймер
        else:
            self._refresh_detail(aid)

    def _check_pomo(self):
        now = time.time()
        # Сработавшие помодоро (по всем проектам).
        finished = [a for a, end in self._pomos.items() if end - now <= 0]
        for a in finished:
            self._pomos.pop(a, None)
            if self._pomo_aid == a:
                self._pomo_lbl = None
                self._pomo_aid = None
            try:
                self.root.bell()
            except tk.TclError:
                pass
            act = self.db.get_activity(a)
            nm = f"«{act['name']}» — " if act else ""
            messagebox.showinfo("🍅 Pomodoro", f"{nm}время вышло!\nСделай перерыв ☕")

        # Обновляем видимый ярлык текущего проекта.
        if self._pomo_aid and self._pomo_lbl:
            end = self._pomos.get(self._pomo_aid)
            if end:
                try:
                    self._pomo_lbl.configure(text=f"  ⏱ {fmt_hms(max(0, int(end - now)))}")
                except tk.TclError:
                    self._pomo_lbl = None

    def _export(self):
        path = asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="devtime_export.csv")
        if path:
            try:
                n = self.db.export_csv(path)
                messagebox.showinfo("Экспорт", f"Экспортировано {n} сессий:\n{path}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    # ══════════════════════════════════════════════════════════════════════════
    #  Hero menu
    # ══════════════════════════════════════════════════════════════════════════
    def _hero_menu(self, event, act):
        mx = event.x
        width = event.widget.winfo_width()
        if mx > width - 80:
            if mx < width - 30:
                self._edit_activity(act)
            else:
                self._delete(act["id"], act["name"])

    # ══════════════════════════════════════════════════════════════════════════
    #  Tick
    # ══════════════════════════════════════════════════════════════════════════
    def _tick(self):
        if self._stop_tick:
            return

        for aid, refs in self._side_refs.items():
            if self.timer.is_active(aid):
                try:
                    refs["draw"]()
                except tk.TclError:
                    pass

        if self._dt_aid and self.timer.is_active(self._dt_aid) and self._view_mode == "project":
            el = self.timer.elapsed(self._dt_aid)
            for lbl, val in [
                (self._dt_time_lbl, fmt_h(self._dt_base_s + el)),
                (self._dt_today_lbl, fmt_h(self._dt_today_base + el)),
                (self._dt_sess_lbl, fmt_hms(el)),
            ]:
                if lbl:
                    try:
                        lbl.configure(text=val)
                    except tk.TclError:
                        pass

        self._check_pomo()
        self.root.after(1000, self._tick)

    def stop_all(self):
        sessions = self.timer.stop_all()
        for aid, data in sessions.items():
            try:
                self.db.log_session(aid, data["started_at"], data["ended_at"], data["duration_s"], "(авто-стоп)")
            except Exception as e:
                log.error("stop_all aid=%s: %s", aid, e)
        self._stop_tick = True
