# DevTime v6 ⌚

Steam-style трекер времени для разработчиков.

## Требования

- Python 3.10+
- Windows / macOS / Linux

## Установка и запуск

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

pip install -r requirements.txt
python app.py
```

## Структура

```
devtime_v5/
├── app.py              # точка входа + logging init
├── db.py               # весь SQL (SQLite)
├── utils.py            # форматирование + цвета + TimerService
├── requirements.txt
├── .gitignore
└── ui/
    ├── __init__.py
    ├── dialogs.py      # добавление, редактирование, заметки
    └── main_window.py  # Steam-layout: sidebar + hero + detail
```

## Данные

- БД: `~/.devtime/devtime.db` — совместима с v1–v4
- Логи: `~/.devtime/devtime.log`

## Заметки по архитектуре

**`activities.total_s`** — это кэш суммы сессий, обновляется инкрементально при `log_session()`.
Если сессии редактировались вручную — вызови `db.recalc_total(activity_id)` для пересчёта.

## Changelog

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
