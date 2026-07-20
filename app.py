"""Market Overview Dashboard.

Serves http://localhost:8050 and refreshes Yahoo Finance data in a
background thread every config.REFRESH_MINUTES minutes.
Run via start_dashboard.bat (or: .venv\\Scripts\\python.exe app.py).
"""

import json
import socket
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

from flask import Flask, render_template

import config
import fetcher

app = Flask(__name__)

_SNAPSHOT_FILE = Path(__file__).resolve().parent / "data" / "last_snapshot.json"

_state = {"snapshot": None, "error": None}


def _load_saved_snapshot():
    """Show the previous session's data immediately on startup (with its
    original timestamp) while the first fresh fetch runs in the background."""
    try:
        _state["snapshot"] = json.loads(_SNAPSHOT_FILE.read_text(encoding="utf-8"))
        print(f"[startup] showing cached data from {_state['snapshot']['updated']}")
    except Exception:
        pass


def _refresh_loop():
    while True:
        try:
            _state["snapshot"] = fetcher.fetch_snapshot()
            _state["error"] = None
            print(f"[refresh] data updated @ {_state['snapshot']['updated']}")
            try:
                _SNAPSHOT_FILE.parent.mkdir(exist_ok=True)
                _SNAPSHOT_FILE.write_text(
                    json.dumps(_state["snapshot"]), encoding="utf-8"
                )
            except Exception:
                pass
        except Exception:
            _state["error"] = traceback.format_exc(limit=1)
            print(f"[refresh] FAILED:\n{_state['error']}")
        time.sleep(config.REFRESH_MINUTES * 60)


@app.route("/")
def index():
    return render_template(
        "index.html",
        snapshot=_state["snapshot"],
        error=_state["error"],
        refresh_minutes=config.REFRESH_MINUTES,
        page_reload_seconds=config.PAGE_RELOAD_SECONDS,
    )


def _port_in_use(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


if __name__ == "__main__":
    url = f"http://localhost:{config.PORT}"
    open_browser = "--no-browser" not in sys.argv
    if _port_in_use(config.PORT):
        print(f"Dashboard already running - opening {url}")
        if open_browser:
            webbrowser.open(url)
    else:
        _load_saved_snapshot()
        threading.Thread(target=_refresh_loop, daemon=True).start()
        if open_browser:
            threading.Timer(1.5, lambda: webbrowser.open(url)).start()
        print(f"Serving Market Overview Dashboard at {url}")
        app.run(host="127.0.0.1", port=config.PORT)
