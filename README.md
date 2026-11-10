# Samsung-TV

Idle screen for a Samsung Tizen TV: big clock, Nairobi weather, rotating F1 & Le Mans wallpapers and tech jokes in a blurred card. A Python watcher serves the page and opens it full screen on the TV after a few idle minutes, via samsung-tv-ws-api.

## What it shows

* **Big clock** — current time in Nairobi (East Africa Time), independent of the TV's own clock settings, with seconds and date.
* **Nairobi weather** — temperature, conditions and today's high/low from Open-Meteo (no API key needed), refreshed every 15 minutes.
* **Rotating wallpapers** — Formula 1 and 24 Heures du Mans photos from Wikimedia Commons, with a slow Ken Burns drift and a progress bar per slide.
* **Tech jokes** — a blurred "glass" card (`// tech.joke()`) cycling through a local deck of programming/IT jokes, mixed with jokes from JokeAPI when online.

## How it works

The TV can't report its input or a "No Signal" state, so "idle" means: the TV is on, none of its streaming apps (YouTube, Netflix, Prime Video, Spotify, …) is visible, and the idle screen page itself isn't showing.

1. `ict_screen.py` serves `screen/` on `http://<pc-ip>:8765/` and watches the TV over the local network (Samsung TV WebSocket API, port 8001).
2. After 5 idle minutes it opens the page full screen on the TV browser via `tv.py` (`samsungtvws.SamsungTVWS`, `open_browser` + `KEY_ENTER`).
3. The page pings the watcher every 15 s so it knows the screen is still showing; if someone switches to another input, the watcher waits longer before reopening.

## Files

* `ict_screen.py` — HTTP server + idle watcher; runs on the PC
* `tv.py` — Samsung TV remote control (info, apps, keys, launch apps, browse URL)
* `screen/index.html` — the idle screen (ES5, written for the 2018 Tizen browser)
* `screen/photos.js` — wallpaper list (F1 and Le Mans, with photo credits)
* `screen/quotes.js` — local tech-joke deck
* `screen/img/` — F1 (`f1*.jpg`) and Le Mans (`lm*.jpg`) wallpapers
* `.gitignore` — ignores the TV pairing token, watcher log and `__pycache__`

## Requirements

* Python 3
* `samsungtvws` — `pip install samsungtvws`

## Usage

1. Edit `HOST` in `tv.py` to your TV's IP (default `192.168.0.88`).
2. Run `python ict_screen.py` on a PC reachable by the TV.
3. The first run shows an "Allow" prompt on the TV; the pairing token is saved to `tv-token.txt` (ignored by git).
4. Leave the TV idle for 5 minutes and the screen opens full screen.

TV model: Samsung UA49N5300 (2018 Tizen).
