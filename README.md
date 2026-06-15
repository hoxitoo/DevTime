# DevTime v7 ⌚

Steam-style трекер времени для разработчиков.

![Build](https://github.com/hoxitoo/DevTime/actions/workflows/build.yml/badge.svg)

## Требования

- Python 3.10+
- Windows / macOS / Linux

## Установка и запуск из исходников

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

pip install -r requirements.txt
python app.py
```

## Готовые сборки (standalone)

Не хочешь ставить Python? Скачай собранное приложение:

- **Вкладка [Actions](https://github.com/hoxitoo/DevTime/actions/workflows/build.yml)** →
  последний успешный запуск → раздел *Artifacts* → `DevTime-linux` /
  `DevTime-windows` / `DevTime-macos`.
- **Релизы:** при пуше тега вида `v1.0.0` бинарники автоматически прикрепляются
  к [GitHub Release](https://github.com/hoxitoo/DevTime/releases).

```bash
# создать релиз с бинарниками под все три ОС
git tag v1.0.0
git push origin v1.0.0
```

### Собрать локально

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed \
  --name DevTime --collect-all customtkinter app.py
# результат: dist/DevTime (.exe на Windows, .app на macOS)
```

> `--collect-all customtkinter` обязателен — иначе PyInstaller не упакует
> ассеты темы и приложение упадёт при старте.

## Структура

```
DevTime/
├── app.py              # точка входа + logging init
├── db.py               # весь SQL (SQLite)
├── utils.py            # форматирование + цвета + blend + TimerService
├── requirements.txt
├── .gitignore
├── .github/workflows/
│   └── build.yml       # CI: сборка под Linux/Windows/macOS
└── ui/
    ├── __init__.py
    ├── dialogs.py      # добавление, редактирование, заметки
    └── main_window.py  # Steam-layout: sidebar + hero + detail
```

## Данные

- БД: `~/.devtime/devtime.db` — автомиграция v1–v7
- Логи: `~/.devtime/devtime.log`

## Заметки по архитектуре

**`activities.total_s`** — это кэш суммы сессий, обновляется инкрементально при `log_session()`.
Если сессии редактировались вручную — вызови `db.recalc_total(activity_id)` для пересчёта.

## Changelog

### v7
- Кроссплатформенный выбор шрифтов (Segoe UI → DejaVu/Noto/SF фолбэк)
- Исправлен рендер баннеров: убран неподдерживаемый Tkinter 8-значный hex (альфа) → `utils.blend`
- Быстрый старт ▶ из карточки сайдбара и библиотеки; пер-проектный Pomodoro
- Уведомление о достижении цели; корректные таймзоны (localtime) и streak с грейсом
- CI: сборка standalone-приложения через GitHub Actions (PyInstaller)

### v5
- Исправлен баг: `~/.devtime/` теперь создаётся до настройки `FileHandler` (первый запуск не падал)
- Обновлены версии во всех модулях (было v3/v4)
- Добавлена `DB.recalc_total()` — пересчёт кэша `total_s` из реальных сессий
- Два оставшихся `except Exception` оставлены намеренно: `_export` (показывает ошибку пользователю) и `stop_all` (логирует)

### v4
- Визуальный рефакторинг: hero-баннер, sidebar-карточки с мини-баннерами, rich stats
- Canvas-графики со столбиками-градиентами

### v3
- Steam-layout: sidebar + detail page
- CustomTkinter, заметки к сессии, streak, pomodoro, план дня

### v2
- Добавлены: заметки, streak, pomodoro, план дня

### v1
- MVP: активности, таймер, SQLite, CSV-экспорт


### v6
- Добавлено верхнее меню с разделами «Библиотека проектов» и «Статистика»
- Библиотека теперь показывает статусы проектов: активный / завершён / удалён
- Удаление стало мягким: проект попадает в удалённые и может быть восстановлен
- Добавлена общая статистика по всем проектам и общий график активности
