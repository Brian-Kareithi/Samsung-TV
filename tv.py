"""Control the Samsung TV "Ict" (UA49N5300) over the local network.

Usage:
  python tv.py info                 # device info
  python tv.py apps                 # list installed apps
  python tv.py key KEY_VOLUP [n]    # send a remote key (n times)
  python tv.py open <app_id>        # launch an app
  python tv.py browse <url>         # open a web page on the TV
"""
import json
import os
import sys
import time

from samsungtvws import SamsungTVWS

HOST = "192.168.0.88"
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tv-token.txt")


def connect():
    # The first connection shows an Allow prompt on the TV; the token is saved for later runs.
    return SamsungTVWS(host=HOST, port=8002, token_file=TOKEN_FILE, timeout=60, name="Claude Remote")


def main(argv):
    if not argv:
        print(__doc__)
        return
    cmd, args = argv[0], argv[1:]
    tv = connect()
    if cmd == "info":
        print(json.dumps(tv.rest_device_info()["device"], indent=2))
    elif cmd == "apps":
        for app in sorted(tv.app_list() or [], key=lambda a: a["name"].lower()):
            print(f'{app["appId"]:<40} {app["name"]}')
    elif cmd == "key":
        tv.send_key(args[0], times=int(args[1]) if len(args) > 1 else 1)
    elif cmd == "open":
        tv.run_app(args[0])
    elif cmd == "browse":
        tv.open_browser(args[0])
        # The ICT screen goes full screen when it sees OK pressed; give the browser time to load first.
        time.sleep(10)
        tv.send_key("KEY_ENTER")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
