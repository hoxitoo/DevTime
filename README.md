# DevTime v8 ⌚

Steam для разработчиков: проекты — как игры, часы за кодом — как «наиграно»,
ачивки, уровни и heatmap активности.

![Build](https://github.com/hoxitoo/DevTime/actions/workflows/build.yml/badge.svg)

## Что внутри

- **Библиотека** — сетка «капсул» проектов, быстрый старт ▶ прямо с карточки
- **Страница проекта** — hero-баннер, кнопка ИГРАТЬ, live-таймер, цель с
  прогрессом, график активности за 28 дней, план дня, история сессий
- **Ачивки** — 17 достижений от «Первого коммита» до «Ветерана» (500 ч)
- **Профиль** — уровень и XP, звание (Новичок → Легенда), heatmap за год
  как на GitHub, витрина ачивок
- **Pomodoro** — 25/50/90 минут в контексте проекта
- Всё локально: SQLite в `~/.devtime/devtime.db`, без аккаунтов и облака

## Архитектура

```
DevTime/
├── app.py              # точка входа: локальный сервер + окно (pywebview/браузер)
├── db.py               # ядро: весь SQL (SQLite)
├── utils.py            # ядро: форматирование, цвета, TimerService
├── api/                # FastAPI-слой (REST) — в перспективе облачный бэкенд
│   ├── server.py       # эндпоинты + раздача web/dist
│   ├── achievements.py # движок ачивок (считается из фактов БД)
│   └── profile.py      # XP, уровни, звания
├── web/                # фронтенд: React + Vite + Tailwind (Steam-тёмная тема)
│   └── src/            # pages: Library, Project, Profile, Achievements
├── legacy_tk.py + ui/  # классический Tkinter-интерфейс (python legacy_tk.py)
└── .github/workflows/  # CI: Vite + PyInstaller под Linux/Windows/macOS
```

Ядро (`db.py`, `utils.py`) не знает про UI — им пользуются и веб-версия,
и legacy-Tkinter. Данные общие.

## Запуск из исходников

```bash
# 1. Фронтенд (однократно после изменений в web/)
cd web && npm install && npm run build && cd ..

# 2. Python-зависимости
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
pip install -r requirements.txt

# 3. Запуск
python app.py            # нативное окно (pywebview) или браузер
python app.py --browser  # принудительно в браузере
python legacy_tk.py      # классический Tkinter-UI
```

Для разработки фронтенда: `python app.py --no-open --port 8765` +
`cd web && npm run dev` (Vite-прокси на `/api` уже настроен).

## Готовые сборки (standalone)

- **[Actions](https://github.com/hoxitoo/DevTime/actions/workflows/build.yml)** →
  последний успешный запуск → *Artifacts* → `DevTime-linux` / `DevTime-windows` / `DevTime-macos`.
- **Релизы:** пуш тега `v1.0.0` собирает бинарники и прикрепляет к
  [GitHub Release](https://github.com/hoxitoo/DevTime/releases).

### Собрать локально

```bash
cd web && npm ci && npm run build && cd ..
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name DevTime \
  --add-data "web/dist:web/dist" \
  --collect-all uvicorn --collect-all webview \
  app.py
# Windows: в --add-data разделитель ';' вместо ':'
```

## Данные

- БД: `~/.devtime/devtime.db` — автомиграция v1–v8, общая для обеих версий UI
- Логи: `~/.devtime/devtime.log`
- Экспорт: кнопка CSV в топбаре (или `GET /api/export.csv`)

## Changelog

### v8
- Полная переработка UI: React + Vite + Tailwind поверх FastAPI, вид клиента Steam
- Библиотека-сетка капсул, hero-страница проекта с кнопкой ИГРАТЬ
- Ачивки (17), профиль с XP/уровнями/званиями, heatmap активности за год
- Пер-проектный Pomodoro, тосты о достижениях, live-обновление таймеров
- Нативное окно через pywebview (опционально), фолбэк — браузер
- Tkinter-версия сохранена как `legacy_tk.py`
- CI собирает фронтенд (Node 22) + PyInstaller под 3 ОС

### v7
- Кроссплатформенные шрифты, фикс 8-значного hex в Canvas, быстрый старт ▶
- Пер-проектный Pomodoro, уведомление о цели, таймзоны (localtime), streak-грейс
- CI: сборка standalone через GitHub Actions

### v6
- Верхнее меню «Библиотека» / «Статистика», статусы проектов, мягкое удаление

### v5 и раньше
- MVP: активности, таймер, SQLite, CSV; заметки, streak, pomodoro, план дня;
  Steam-layout на CustomTkinter
