"""Launch the tutor in a native desktop window, serving the bundled React UI locally."""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND_DIST = ROOT / "frontend" / "dist"
HOST = "127.0.0.1"
PORT = int(os.getenv("TUTOR_PORT", "8000"))


def wait_for_server(url: str, timeout: float = 30) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    return False


def main() -> int:
    if not FRONTEND_DIST.joinpath("index.html").exists():
        print("The desktop interface has not been built. Run the setup script again.")
        return 1

    try:
        import webview
        import uvicorn
    except ImportError as exc:
        print(f"Missing desktop dependency: {exc}. Run start_desktop.bat to install it.")
        return 1

    with socket.socket() as probe:
        if probe.connect_ex((HOST, PORT)) == 0:
            print(f"Port {PORT} is already in use. Close the other tutor server or set TUTOR_PORT.")
            return 1

    os.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))
    config = uvicorn.Config("app.main:app", host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="tutor-api", daemon=True)
    thread.start()

    url = f"http://{HOST}:{PORT}/"
    if not wait_for_server(url):
        server.should_exit = True
        print("The tutor service did not start. Check backend/.env and the Python dependencies.")
        return 1

    try:
        webview.create_window(
            "Learnwell — Adaptive AI Tutor",
            url,
            width=1440,
            height=920,
            min_size=(900, 650),
            background_color="#f8fafc",
        )
        webview.start()
    finally:
        server.should_exit = True
        thread.join(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
