"""
DevTime v8 — точка входа.
Поднимает локальный FastAPI-сервер и открывает UI:
  - в нативном окне (pywebview), если он установлен;
  - иначе — во вкладке браузера по умолчанию.

Запуск:  python app.py [--browser] [--port N] [--no-open]
Классический Tkinter-интерфейс остался доступен: python legacy_tk.py
"""

import argparse
import logging
import socket
import sys
import threading
import webbrowser
from pathlib import Path

_DATA_DIR = Path.home() / ".devtime"
_DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(_DATA_DIR / "devtime.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("devtime")

import uvicorn
from api.server import create_app


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def try_start_tray(url: str, on_quit) -> bool:
    """Иконка в системном трее (опционально: pip install pystray pillow).

    Открыть / Выход. Возвращает False, если pystray недоступен.
    """
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    try:
        img = Image.new("RGB", (64, 64), "#0b0d12")
        d = ImageDraw.Draw(img)
        d.ellipse([8, 8, 56, 56], outline="#4fc3f7", width=5)
        d.line([32, 32, 32, 16], fill="#4fc3f7", width=4)   # часовая стрелка
        d.line([32, 32, 44, 38], fill="#00e676", width=4)   # минутная
        menu = pystray.Menu(
            pystray.MenuItem("Открыть DevTime", lambda: webbrowser.open(url), default=True),
            pystray.MenuItem("Выход", lambda icon: (on_quit(), icon.stop())),
        )
        icon = pystray.Icon("devtime", img, "DevTime", menu)
        threading.Thread(target=icon.run, daemon=True, name="tray").start()
        log.info("трей-иконка запущена")
        return True
    except Exception as e:  # noqa: BLE001 — трей не критичен
        log.warning("трей недоступен: %s", e)
        return False


def main():
    ap = argparse.ArgumentParser(description="DevTime — Steam для разработчиков")
    ap.add_argument("--browser", action="store_true", help="открыть в браузере вместо нативного окна")
    ap.add_argument("--port", type=int, default=0, help="порт сервера (0 = свободный)")
    ap.add_argument("--no-open", action="store_true", help="только сервер, ничего не открывать")
    args = ap.parse_args()

    port = args.port or free_port()
    url = f"http://127.0.0.1:{port}"

    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True, name="uvicorn").start()

    log.info("DevTime запущен: %s", url)

    def shutdown():
        n = app.state.flush_running()
        if n:
            log.info("сохранено активных сессий: %d", n)
        server.should_exit = True

    use_webview = not args.browser and not args.no_open
    if use_webview:
        try:
            import webview  # pywebview — опционален
        except ImportError:
            use_webview = False
            log.info("pywebview не установлен — открываю в браузере (pip install pywebview)")

    try:
        if use_webview:
            try_start_tray(url, shutdown)
            window = webview.create_window(
                "DevTime", url, width=1280, height=820, min_size=(960, 640),
                background_color="#0b0d12",
            )
            window.events.closed += shutdown
            webview.start()
        else:
            stop_evt = threading.Event()
            try_start_tray(url, lambda: (shutdown(), stop_evt.set()))
            if not args.no_open:
                webbrowser.open(url)
            # Держим процесс: Ctrl+C или «Выход» в трее
            stop_evt.wait()
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()
