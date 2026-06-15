# DevTime — контекст проекта для Claude Code

## Что это

Desktop-приложение на Python для трекинга времени по проектам в Steam-стиле.
Тёмный UI: сайдбар со списком проектов слева, страница проекта справа.
Данные хранятся локально в SQLite (`~/.devtime/devtime.db`).

## Стек

- **Python 3.10+**
- **CustomTkinter** (`pip install customtkinter`) — единственная внешняя зависимость
- **tkinter** — встроен в Python, используется для Canvas (графики, баннеры)
- **SQLite** через стандартный `sqlite3`

## Структура файлов

```
devtime/
├── app.py              # Точка входа. Настройка logging, создание CTk root,
│                       # инициализация DB и MainWindow, on_close handler.
├── db.py               # Класс DB. Весь SQL только здесь.
├── utils.py            # fmt_h/fmt_hms/fmt_ts — форматирование времени.
│                       # darken/lighten/hex_to_rgb — цветовые утилиты.
│                       # TimerService + _Session — бизнес-логика таймера.
└── ui/
    ├── dialogs.py      # Диалоги: ActivityDialog, NoteDialog, EditNoteDialog.
    └── main_window.py  # Главное окно. 1150+ строк. Содержит всё UI:
                        # топбар, сайдбар, три экрана, страница проекта.
```

## База данных

### Таблица `activities`

| Поле       | Тип     | Описание |
|------------|---------|----------|
| `id`       | INTEGER | PK |
| `name`     | TEXT    | Название проекта |
| `emoji`    | TEXT    | Эмодзи-иконка |
| `color`    | TEXT    | HEX-цвет акцента, например `#4fc3f7` |
| `total_s`  | INTEGER | **Кэш** суммы сессий. Обновляется инкрементально в `log_session()`. При рассинхроне — вызвать `db.recalc_total(aid)` |
| `goal_h`   | REAL    | Цель в часах (0 = нет цели) |
| `day_plan` | TEXT    | Заметка «план на сегодня» |
| `status`   | TEXT    | `active` / `completed` / `deleted` |
| `created`  | TEXT    | Дата создания `YYYY-MM-DD` |

### Таблица `sessions`

| Поле          | Тип     | Описание |
|---------------|---------|----------|
| `id`          | INTEGER | PK |
| `activity_id` | INTEGER | FK → activities.id, ON DELETE CASCADE |
| `started_at`  | TEXT    | `YYYY-MM-DD HH:MM:SS` — реальное время начала (не теряется при паузах) |
| `ended_at`    | TEXT    | `YYYY-MM-DD HH:MM:SS` |
| `duration_s`  | INTEGER | Чистое время без пауз |
| `note`        | TEXT    | Заметка к сессии |

### Миграции

`DB._migrate()` использует `CREATE TABLE IF NOT EXISTS` + безопасные `ALTER TABLE` в `try/except sqlite3.OperationalError`. Новые колонки добавлять туда же.

## Ключевые классы и их контракты

### `TimerService` (utils.py)

Управляет активными сессиями в памяти. **Не знает о БД и UI.**

```python
timer.start(aid)    # → bool, False если уже идёт
timer.pause(aid)    # → bool
timer.resume(aid)   # → bool
timer.stop(aid)     # → {"started_at", "ended_at", "duration_s"} | None
timer.elapsed(aid)  # → int секунд (включая паузы)
timer.is_running(aid)  # активна и не на паузе
timer.is_paused(aid)   # на паузе
timer.is_active(aid)   # running OR paused
timer.stop_all()    # → {aid: session_data} — при закрытии приложения
```

`_Session` хранит `real_started_ts` (никогда не меняется), `segment_start_ts` (обновляется при resume), `accumulated_s` (растёт при паузах), `paused: bool`.

### `DB` (db.py)

Методы для активностей: `get_activities(include_deleted)`, `get_activity(aid)`, `add_activity`, `update_activity`, `set_activity_status`, `delete_activity` (мягкое — ставит status=deleted), `restore_activity`, `complete_activity`, `reopen_activity`, `update_day_plan`, `recalc_total`.

Методы для сессий: `log_session`, `get_sessions(aid, limit)`, `update_session_note`, `get_session_note`.

Статистика: `get_streak(aid)`, `get_today_total(aid)`, `get_week_total(aid)`, `get_daily_totals(aid, days)`, `get_all_daily_totals(days)`, `get_overall_stats()`.

### `MainWindow` (ui/main_window.py)

Три режима через `self._view_mode`: `"library"` | `"stats"` | `"project"`.
Переключение: `_set_view(mode)` → `_sync_nav_buttons()` → `_render_current_view()`.

Состояние:
```python
self.sel_id        # int | None — выбранный проект
self.timer         # TimerService
self._sb_filter    # "active" | "all" — фильтр сайдбара
self._sb_search_var  # ctk.StringVar — строка поиска
self._lib_sort_key   # "total_s" | "name" | "created" | "status"
self._lib_sort_asc   # bool — направление сортировки в библиотеке
```

Live-обновление (тик 1 сек): `_tick()` обновляет Canvas-карточки сайдбара через `refs["draw"]()` и labels страницы деталей. Исключения `tk.TclError` — норма (виджет уничтожен при смене экрана), логируются через `log.debug`.

## UI-паттерны

**Цвета** (константы в `main_window.py`):
```python
BG="#0b0d12", SIDEBAR="#0f1219", SURF="#151a26", SURF2="#1e2336", SURF3="#1f263a"
BORDER="#242d42", ACCENT="#4fc3f7", GREEN="#00e676", RED="#ff5252", ORANGE="#ffab40"
TEXT="#dde3f0", MUTED="#4a5570", MUTED2="#2a3350"
```

**Шрифт**: `_f(size, bold)` → `ctk.CTkFont`. До 12px — Courier New, выше — Segoe UI.

**Градиенты**: `_grad_line(canvas, x0, y0, x1, y1, c1, c2)` — рисует горизонтальный градиент полосками. Используется в hero-баннере и карточках сайдбара.

**Баннер проекта**: `tk.Canvas` высотой 180px с трёхцветным градиентом (darken×0.82 → darken×0.55 → color). Перерисовывается при `<Configure>` и через `root.after(30, draw)`.

**Карточки сайдбара**: `tk.Canvas` высотой 52px внутри `ctk.CTkFrame`. Обновляются каждую секунду через `refs["draw"]()` в `_tick()`.

**Диалоги**: наследуются от `_BaseDialog(ctk.CTkToplevel)`. `grab_set()` при открытии. Центрируются через `_center(parent)`.

## Известные особенности

**`activities.total_s` — кэш, не истина.** Обновляется инкрементально в `log_session()`. Если сессию удалить или отредактировать вручную — вызвать `db.recalc_total(aid)`.

**Закрытие окна**: `on_close()` в `app.py` делает `grab_release()` на дочерних окнах перед `root.destroy()`. Это workaround известного бага CustomTkinter — `StringVar` внутри `CTkToplevel` вызывает `TypeError: unhashable type: 'StringVar'` при уничтожении. Не убирать без проверки.

**Мягкое удаление**: `delete_activity()` ставит `status='deleted'`, не удаляет запись. Сессии сохраняются. Восстановление через `restore_activity()`.

**Статус `completed`**: проект нельзя запустить (`_start()` проверяет статус). Возврат в active через `_reopen_project()`.

## Что планировалось добавить (бэклог)

- Heatmap 7×4 вместо барчарта на странице статистики
- Быстрый старт ▶ прямо из карточки в библиотеке
- Уведомление при достижении цели по часам
- Разбить `main_window.py` на `ui/sidebar.py`, `ui/detail_panel.py`, `ui/charts.py`

## Данные и логи

- БД: `~/.devtime/devtime.db`
- Логи: `~/.devtime/devtime.log`
- Совместимость БД: v1–v7 (автомиграция при старте)
