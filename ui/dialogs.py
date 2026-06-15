"""
DevTime v5 — диалоговые окна.
"""

import customtkinter as ctk
from utils import PROJECT_COLORS, color_for_name

EMOJIS = [
    '💻','🚀','🔬','⚡','🛠️','🧠','📊','🤖','🔐','🌐',
    '🎯','📱','🔧','🧪','💡','🏗️','📡','🎮','📈','🧩',
    '🔮','⚙️','🗄️','🧲','📝','🏆','🌿','🎲',
]

# Цвета UI
BG      = "#0f1117"
SURFACE = "#181c28"
SURF2   = "#1e2336"
BORDER  = "#252a3d"
TEXT    = "#e8eaf0"
MUTED   = "#556080"
GREEN   = "#00e676"
ACCENT  = "#4fc3f7"


class _BaseDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, width: int = 420, height: int = 480):
        super().__init__(parent)
        self.title(title)
        self.configure(fg_color=BG)
        self.resizable(False, False)
        self.geometry(f"{width}x{height}")
        self.grab_set()
        self._center(parent)

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + parent.winfo_width()  // 2 - self.winfo_width()  // 2
        y = parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def _label(self, parent, text, size=11, color=MUTED, **kw):
        return ctk.CTkLabel(parent, text=text, text_color=color,
                            font=ctk.CTkFont(size=size), **kw)

    def _entry(self, parent, var, **kw):
        return ctk.CTkEntry(parent, textvariable=var,
                            fg_color=SURF2, border_color=BORDER,
                            text_color=TEXT, font=ctk.CTkFont(size=12),
                            **kw)


# ── Добавить / Редактировать активность ──────────────────────────────────────

class ActivityDialog(_BaseDialog):
    """
    Используется и для добавления, и для редактирования.
    act=None → добавление, act=dict → редактирование.
    """

    def __init__(self, parent, on_save, act=None):
        mode = "Редактировать" if act else "Новый проект"
        super().__init__(parent, mode, width=440, height=520)
        self.on_save = on_save
        self._emoji  = act["emoji"]  if act else "💻"
        self._color  = act["color"]  if act else PROJECT_COLORS[0]

        self._build(act)

    def _build(self, act):
        pad = {"padx": 20, "pady": 4}

        self._label(self, "ПРОЕКТ", size=10).pack(anchor="w", padx=20, pady=(18, 8))

        # Название
        self._label(self, "Название").pack(anchor="w", **pad)
        self._name = ctk.StringVar(value=act["name"] if act else "")
        self._entry(self, self._name, width=380).pack(padx=20, pady=(0, 8))

        # Эмодзи
        self._label(self, "Иконка").pack(anchor="w", **pad)
        ef = ctk.CTkFrame(self, fg_color="transparent")
        ef.pack(padx=20, pady=(0, 8))
        self._emoji_btns = {}
        for i, em in enumerate(EMOJIS):
            b = ctk.CTkButton(
                ef, text=em, width=36, height=36,
                fg_color=SURF2 if em != self._emoji else ACCENT,
                hover_color=BORDER, text_color=TEXT,
                font=ctk.CTkFont(size=16),
                command=lambda x=em: self._pick_emoji(x)
            )
            b.grid(row=i // 10, column=i % 10, padx=2, pady=2)
            self._emoji_btns[em] = b

        # Цвет акцента
        self._label(self, "Цвет акцента").pack(anchor="w", **pad)
        cf = ctk.CTkFrame(self, fg_color="transparent")
        cf.pack(padx=20, pady=(0, 8), anchor="w")
        self._color_btns = {}
        for i, col in enumerate(PROJECT_COLORS):
            b = ctk.CTkButton(
                cf, text="", width=26, height=26,
                fg_color=col, hover_color=col,
                border_width=3 if col == self._color else 0,
                border_color=TEXT,
                command=lambda c=col: self._pick_color(c)
            )
            b.grid(row=0, column=i, padx=3)
            self._color_btns[col] = b

        # Цель
        self._label(self, "Цель (ч, 0 = нет)").pack(anchor="w", **pad)
        self._goal = ctk.StringVar(value=str(act["goal_h"]) if act else "0")
        self._entry(self, self._goal, width=100).pack(anchor="w", padx=20, pady=(0, 16))

        # Кнопки
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(bf, text="Отмена", fg_color=SURF2, text_color=MUTED,
                      hover_color=BORDER, command=self.destroy,
                      width=100).pack(side="left")
        ctk.CTkButton(bf, text="Сохранить →", fg_color=ACCENT, text_color="#000",
                      hover_color="#7dd8f8", font=ctk.CTkFont(weight="bold"),
                      command=self._submit, width=140).pack(side="right")

        self.bind("<Return>", lambda e: self._submit())

    def _pick_emoji(self, em):
        for e, b in self._emoji_btns.items():
            b.configure(fg_color=ACCENT if e == em else SURF2)
        self._emoji = em

    def _pick_color(self, col):
        for c, b in self._color_btns.items():
            b.configure(border_width=3 if c == col else 0)
        self._color = col

    def _submit(self):
        name = self._name.get().strip()
        if not name:
            return
        try:
            goal = float(self._goal.get() or 0)
        except ValueError:
            goal = 0
        self.on_save(name, self._emoji, self._color, goal)
        self.destroy()


# ── Заметка к сессии ─────────────────────────────────────────────────────────

class NoteDialog(_BaseDialog):
    def __init__(self, parent, duration_s: int, on_save, existing_note: str = ""):
        from utils import fmt_hms
        super().__init__(parent, "Заметка к сессии", width=400, height=230)
        self.on_save = on_save

        ctk.CTkLabel(
            self,
            text=f"Сессия завершена: {fmt_hms(duration_s)}",
            text_color=GREEN, font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=16, pady=(16, 2))

        ctk.CTkLabel(
            self, text="Что делал? (Ctrl+Enter — сохранить, Esc — пропустить)",
            text_color=MUTED, font=ctk.CTkFont(size=10)
        ).pack(anchor="w", padx=16, pady=(0, 6))

        self._txt = ctk.CTkTextbox(
            self, height=80, fg_color=SURF2, border_color=BORDER,
            text_color=TEXT, font=ctk.CTkFont(size=12), border_width=1
        )
        self._txt.pack(fill="x", padx=16, pady=(0, 12))
        if existing_note:
            self._txt.insert("1.0", existing_note)
        self._txt.focus()

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkButton(bf, text="Пропустить", fg_color=SURF2, text_color=MUTED,
                      hover_color=BORDER, command=self._skip, width=110).pack(side="left")
        ctk.CTkButton(bf, text="Сохранить →", fg_color=GREEN, text_color="#000",
                      hover_color="#33eb91", font=ctk.CTkFont(weight="bold"),
                      command=self._save, width=130).pack(side="right")

        self.bind("<Control-Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self._skip())

    def _save(self):
        self.on_save(self._txt.get("1.0", "end").strip())
        self.destroy()

    def _skip(self):
        self.on_save("")
        self.destroy()


# ── Редактировать заметку сессии ─────────────────────────────────────────────

class EditNoteDialog(_BaseDialog):
    def __init__(self, parent, current_note: str, on_save):
        super().__init__(parent, "Заметка", width=380, height=210)
        self.on_save = on_save

        ctk.CTkLabel(self, text="Заметка к сессии:", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=14, pady=(14, 4))

        self._txt = ctk.CTkTextbox(
            self, height=90, fg_color=SURF2, border_color=BORDER,
            text_color=TEXT, font=ctk.CTkFont(size=12), border_width=1
        )
        self._txt.pack(fill="x", padx=14, pady=(0, 10))
        if current_note:
            self._txt.insert("1.0", current_note)
        self._txt.focus()

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=14, pady=(0, 14))
        ctk.CTkButton(bf, text="Отмена", fg_color=SURF2, text_color=MUTED,
                      hover_color=BORDER, command=self.destroy, width=90).pack(side="left")
        ctk.CTkButton(bf, text="Сохранить", fg_color=GREEN, text_color="#000",
                      hover_color="#33eb91", font=ctk.CTkFont(weight="bold"),
                      command=self._save, width=110).pack(side="right")
        self.bind("<Control-Return>", lambda e: self._save())

    def _save(self):
        self.on_save(self._txt.get("1.0", "end").strip())
        self.destroy()
