"""Market Overview Dashboard.

Two modes, both refreshing every config.REFRESH_MINUTES minutes:
  default      serves http://localhost:8050 (start_dashboard.bat)
  --wallpaper  no browser/server - renders the dashboard straight onto
               the Windows desktop background (start_wallpaper.bat)
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


def _apply_wallpaper():
    import wallpaper
    try:
        wallpaper.update(_state["snapshot"])
        print("[wallpaper] desktop background updated")
    except Exception:
        print(f"[wallpaper] FAILED:\n{traceback.format_exc(limit=1)}")


def _refresh_loop(to_wallpaper=False):
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
            if to_wallpaper:
                _apply_wallpaper()
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
    if "--wallpaper" in sys.argv:
        # wallpaper mode: no server, no browser - just refresh + repaint
        print("Market Overview in wallpaper mode "
              f"(desktop background, refresh every {config.REFRESH_MINUTES} min)")
        _load_saved_snapshot()
        if _state["snapshot"]:
            _apply_wallpaper()
        _refresh_loop(to_wallpaper=True)
    else:
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
