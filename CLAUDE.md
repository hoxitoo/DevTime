# DevTime — контекст проекта для Claude Code

## Что это

«Steam для разработчиков»: desktop-приложение для трекинга времени по проектам.
Проекты — как игры в библиотеке, часы — как «наиграно», плюс ачивки, XP/уровни
и heatmap активности. Данные локально в SQLite (`~/.devtime/devtime.db`).

## Стек (v8)

- **Ядро:** Python 3.10+, SQLite через стандартный `sqlite3`
- **API:** FastAPI + uvicorn (локальный сервер; в перспективе — облачный бэкенд)
- **Фронтенд:** React 18 + Vite + Tailwind CSS 3, lucide-react, HashRouter
- **Окно:** pywebview (опционально; без него — вкладка браузера)
- **Legacy UI:** CustomTkinter (`python legacy_tk.py`), делит ядро и БД с веб-версией

## Структура файлов

```
DevTime/
├── app.py               # Точка входа v8: uvicorn в потоке + pywebview/браузер.
│                        # Флаги: --browser, --port N, --no-open.
│                        # При выходе flush_running() сохраняет активные сессии.
├── db.py                # Класс DB. ВЕСЬ SQL ТОЛЬКО ЗДЕСЬ (конвенция).
├── utils.py             # fmt_h/fmt_hms/fmt_ts, darken/lighten/blend, TimerService.
├── api/
│   ├── server.py        # create_app(db_path). Все REST-эндпоинты. _db_lock
│   │                    # сериализует доступ к sqlite из тредпула FastAPI.
│   ├── achievements.py  # RULES: 17 ачивок. compute(facts) — детерминированно
│   │                    # из db.get_achievement_facts(), без своего хранилища.
│   └── profile.py       # XP = минуты + 250/ачивка. Уровень: 100·L² XP. Звания.
├── web/                 # React-фронтенд. Сборка: npm run build → web/dist.
│   └── src/
│       ├── store.jsx    # Контекст: activities, поллинг /api/timers раз в 1с,
│       │                # тосты, pomodoro (клиентский, aid → endTs).
│       ├── api.js       # fetch-клиент REST.
│       ├── util.js      # Зеркало utils.py: fmtH, darken, blend, градиенты.
│       ├── components/  # TopBar, Sidebar, ActivityChart, Heatmap, Modal, bits.
│       └── pages/       # Library, Project, Profile, Achievements.
├── legacy_tk.py + ui/   # Классический Tkinter-UI (не развивается, но работает).
└── .github/workflows/build.yml  # CI: npm build → PyInstaller (3 ОС).
```

## Ключевые контракты

### `DB` (db.py) — ядро, UI-агностично
Активности: `get_activities`, `get_activity`, `add_activity`, `update_activity`,
`set_activity_status`, `update_day_plan`, `recalc_total`.
Сессии: `log_session` (инкрементально обновляет кэш `total_s`), `get_sessions`,
`update_session_note`.
Статистика: `get_streak` (с грейсом: серия жива, если работал сегодня ИЛИ вчера),
`get_today_total`, `get_week_total`, `get_daily_totals`, `get_all_daily_totals`,
`get_overall_stats` (исключает deleted), `get_achievement_facts`, `get_overall_streak`.
Все даты — `localtime` (не UTC!).
`DB(path, check_same_thread=False)` — для API-слоя; записи сериализует lock в server.py.

### `TimerService` (utils.py) — активные сессии в памяти
`start/pause/resume/stop/elapsed/is_running/is_paused/is_active/stop_all`.
`stop()` → `{started_at, ended_at, duration_s}`. Не знает о БД и UI.

### REST API (api/server.py)
`GET/POST /api/activities`, `GET/PUT /api/activities/{id}`,
`POST .../plan`, `POST .../status` (сохраняет активную сессию перед сменой),
`POST .../timer` {action: start|pause|resume}, `POST .../stop` {note} →
возвращает `new_achievements` для тостов, `GET /api/timers` (поллинг 1с),
`PUT /api/sessions/{id}/note`, `GET /api/overview|profile|achievements|export.csv`.

## Известные особенности

- **`activities.total_s` — кэш**, обновляется в `log_session()`. Рассинхрон → `db.recalc_total(aid)`.
- **Tkinter Canvas не понимает 8-значный hex** (#RRGGBBAA) — для полупрозрачности
  использовать `utils.blend(fg, bg, alpha)`.
- **Ачивки не хранятся** — всегда вычисляются из фактов. «Новые» ачивки
  определяются diff'ом до/после `log_session` в эндпоинте stop.
- **pywebview опционален**: ImportError → фолбэк на браузер. В PyInstaller-бандле
  web/dist ищется через `sys._MEIPASS` (api/server.py::static_dir).
- **PyInstaller --windowed: sys.stdout/stderr = None** (нет консоли). app.py
  подставляет devnull ДО настройки logging и передаёт uvicorn `log_config=None`,
  иначе краш `'NoneType' has no attribute 'isatty'` на старте. Не убирать.
- **Мягкое удаление**: status='deleted', сессии сохраняются.
- **HashRouter** во фронтенде — чтобы не нужен был SPA-fallback на сервере.

## Сборка и CI

- Фронт: `cd web && npm run build` (обязательно до PyInstaller и до `python app.py`).
- PyInstaller: `--add-data "web/dist:web/dist" --collect-all uvicorn --collect-all webview`
  (на Windows разделитель `;`).
- CI (`build.yml`): job `check` (py_compile + npm build) → матрица 3 ОС → артефакты;
  тег `v*` → GitHub Release.

## Roadmap (следующие фазы)

- Облако: auth + синк поверх существующего FastAPI (api/ уже спроектирован под это)
- Друзья, сравнение часов, лидерборды
- Скриншоты/описание на странице проекта (витрина как в Steam)

## Данные и логи

- БД: `~/.devtime/devtime.db` — автомиграция v1–v8, общая для web и legacy UI
- Логи: `~/.devtime/devtime.log`
