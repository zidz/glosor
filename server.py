#!/usr/bin/env python3
import os
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_DIR, "användningslogg.txt")
PORT = int(os.environ.get("ORDOVNING_PORT", "8080"))
IGNORED_IPS = {"10.133.7.1"}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def log_usage(self, feature):
        feature = " ".join(str(feature).split())[:100]
        ip = self.client_address[0]
        if ip in IGNORED_IPS:
            return
        ts = datetime.now().isoformat(timespec="seconds")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("%s %s %s\n" % (ts, ip, feature))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/log":
            qs = parse_qs(parsed.query)
            feature = qs.get("feature", ["okänd"])[0] or "okänd"
            self.log_usage(feature)
            self.send_response(204)
            self.end_headers()
            return
        if parsed.path in ("", "/"):
            self.log_usage("sidvisning")
        super().do_GET()


def main():
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Glosor: port %d, logg %s" % (PORT, LOG_FILE))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
