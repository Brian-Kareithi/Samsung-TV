"""Serve the ICT screen and put it on the TV whenever the TV sits idle.

The TV can't report its input or a "No Signal" state, so "idle" means: the TV is on,
none of its streaming apps is on screen, and the screen page itself isn't showing.

Usage:
  python ict_screen.py
"""
import functools
import http.server
import json
import os
import socket
import threading
import time
import urllib.request
from datetime import datetime

from tv import HOST
from tv import main as tv_main

PORT = 8765
SCREEN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screen")
CHECK_EVERY = 15              # seconds between checks
IDLE_MINUTES = 5              # idle this long -> open the screen
DISMISSED_IDLE_MINUTES = 15   # someone left the screen for another input: give them longer
PING_FRESH = 45               # the page pings every 15s while it is visible
APPS = {
    "111299001912": "YouTube",
    "11101200001": "Netflix",
    "3201512006785": "Prime Video",
    "3201606009684": "Spotify",
    "11091000000": "Facebook Watch",
    "3201710015037": "Gallery",
}

last_ping = 0.0
full_screen = None


def log(msg):
    print(f"{datetime.now():%H:%M:%S}  {msg}", flush=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_ping, full_screen
        if self.path.startswith("/ping"):
            last_ping = time.time()
            fs = "fs=1" in self.path
            if fs != full_screen:
                log("full screen" if fs else "not full screen")
                full_screen = fs
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def end_headers(self):
        if self.path.endswith((".html", ".js")) or self.path == "/":
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass


def local_ip():
    # The address this PC uses to reach the TV, so a new DHCP lease doesn't break the URL.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((HOST, 8001))
        return s.getsockname()[0]


def get_json(path):
    with urllib.request.urlopen(f"http://{HOST}:8001/api/v2/{path}", timeout=4) as r:
        return json.load(r)


def tv_is_on():
    try:
        get_json("")
        return True
    except OSError:
        return False


def visible_app():
    for app_id, name in APPS.items():
        try:
            if get_json(f"applications/{app_id}").get("visible"):
                return name
        except (OSError, ValueError):
            pass
    return None


def open_full_screen(url):
    tv_main(["browse", url])


def watch():
    idle_since = None
    screen_was_showing = False
    threshold = IDLE_MINUTES
    while True:
        try:
            if not tv_is_on():
                if idle_since or screen_was_showing:
                    log("TV is off")
                idle_since, screen_was_showing, threshold = None, False, IDLE_MINUTES
            else:
                showing = time.time() - last_ping < PING_FRESH
                app = None if showing else visible_app()
                if showing:
                    if not screen_was_showing:
                        log("screen is showing")
                    idle_since, threshold = None, IDLE_MINUTES
                elif app:
                    if idle_since or screen_was_showing:
                        log(f"in use: {app}")
                    idle_since = None
                else:
                    if screen_was_showing:
                        log(f"screen was closed - waiting {DISMISSED_IDLE_MINUTES} min before reopening")
                        threshold = DISMISSED_IDLE_MINUTES
                    if idle_since is None:
                        idle_since = time.time()
                    elif time.time() - idle_since >= threshold * 60:
                        url = f"http://{local_ip()}:{PORT}/"
                        log(f"idle for {threshold} min - opening {url}")
                        open_full_screen(url)
                        idle_since, threshold = None, IDLE_MINUTES
                screen_was_showing = showing
        except Exception as e:  # keep watching through network blips
            log(f"error: {e}")
        time.sleep(CHECK_EVERY)


def main():
    handler = functools.partial(Handler, directory=SCREEN_DIR)
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log(f"serving http://{local_ip()}:{PORT}/ - opening it after {IDLE_MINUTES} idle minutes")
    watch()


if __name__ == "__main__":
    main()
