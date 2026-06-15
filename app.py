"""
DevTime v6 — точка входа.
Запуск: python app.py
Зависимости: pip install customtkinter
"""

import logging
import sys
from pathlib import Path

# Папка данных должна существовать ДО настройки FileHandler
_DATA_DIR = Path.home() / ".devtime"
_DATA_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(_DATA_DIR / "devtime.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)

import customtkinter as ctk
from db import DB
from ui.main_window import MainWindow

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def main():
    db   = DB()
    root = ctk.CTk()
    root.title("DevTime")
    root.geometry("960x660")
    root.minsize(800, 520)

    app = MainWindow(root, db)

    def on_close():
        # Останавливаем таймеры и сохраняем все активные сессии
        app.stop_all()
        db.close()
        # Снимаем grab со всех дочерних окон перед destroy.
        # Если открыт CTkToplevel (диалог), его StringVar при уничтожении
        # вызывает "TypeError: unhashable type: 'StringVar'" — grab_release
        # позволяет окну закрыться чисто.
        for child in root.winfo_children():
            try:
                child.grab_release()
            except Exception:
                pass
        try:
            root.destroy()
        except Exception:
            pass  # ошибки при разрушении виджетов не критичны

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
