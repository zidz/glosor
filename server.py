#!/usr/bin/env python3
import hashlib
import hmac
import http.cookies
import os
import secrets
import threading
import time
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_DIR, "användningslogg.txt")
PORT = int(os.environ.get("ORDOVNING_PORT", "8080"))
IGNORED_IPS = {"10.133.7.1"}
#IGNORED_IPS = {}

SECRET_FILE = os.path.join(APP_DIR, ".log_secret")
TOKEN_TTL = 30 * 86400  # 30 dagar
COOKIE_NAME = "glosor_log"
FEATURES = {
    "sidvisning",
    "öppna_läxa",
    "ta_bort_läxa",
    "arkivera_läxa",
    "återställa_läxa",
    "visa_arkiv",
    "exportera_läxor",
    "importera_läxor",
    "skapa_ny_läxa",
    "spara_ny_läxa",
    "ändra_läxa",
    "spara_ändringar",
    "klassiskt_förhör",
    "flervalsquiz",
    "matcha_orden",
    "lyssna_och_stava",
}
RATE_LIMIT = 120  # loggeven per timme per IP
RATE_WINDOW = 3600
_rate = {}
_rate_lock = threading.Lock()


def load_secret():
    if not os.path.exists(SECRET_FILE):
        secret = secrets.token_hex(32)
        fd = os.open(SECRET_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(secret)
    with open(SECRET_FILE, encoding="utf-8") as f:
        return f.read().strip()


SECRET = load_secret()


def _sign(ip, exp):
    msg = ("%s.%d" % (ip, exp)).encode("utf-8")
    return hmac.new(SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def make_token(ip):
    exp = int(time.time()) + TOKEN_TTL
    return "%d.%s" % (exp, _sign(ip, exp))


def valid_token(ip, tok):
    try:
        exp_s, sig = tok.rsplit(".", 1)
        exp = int(exp_s)
    except (ValueError, AttributeError):
        return False
    if exp < time.time():
        return False
    return hmac.compare_digest(sig, _sign(ip, exp))


def rate_ok(ip):
    now = time.time()
    with _rate_lock:
        ts = [t for t in _rate.get(ip, []) if now - t < RATE_WINDOW]
        if len(ts) >= RATE_LIMIT:
            _rate[ip] = ts
            return False
        ts.append(now)
        _rate[ip] = ts
        return True


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def client_ip(self):
        xff = self.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[0].strip()
        return self.client_address[0]

    def cookie_token(self):
        try:
            cookies = http.cookies.SimpleCookie(self.headers.get("Cookie", ""))
            morsel = cookies.get(COOKIE_NAME)
            if morsel:
                return morsel.value
        except http.cookies.CookieError:
            pass
        return None

    def log_usage(self, feature):
        feature = " ".join(str(feature).split())[:100]
        ip = self.client_ip()
        if ip in IGNORED_IPS:
            return
        ts = datetime.now().isoformat(timespec="seconds")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("%s %s %s\n" % (ts, ip, feature))

    def handle_log(self):
        ip = self.client_ip()
        tok = self.cookie_token()
        if not tok or not valid_token(ip, tok):
            self.send_error(403)
            return
        if not rate_ok(ip):
            self.send_error(429)
            return
        qs = parse_qs(urlparse(self.path).query)
        feature = qs.get("feature", ["okänd"])[0] or "okänd"
        feature = " ".join(feature.split())[:100]
        if feature not in FEATURES:
            feature = "okänd"
        self.log_usage(feature)
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/log":
            self.handle_log()
            return
        if parsed.path in ("", "/"):
            self.log_usage("sidvisning")
            ip = self.client_ip()
            tok = self.cookie_token()
            if not tok or not valid_token(ip, tok):
                self._set_cookie = make_token(ip)
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/log":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            self.handle_log()
            return
        self.send_error(405)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        cookie = getattr(self, "_set_cookie", None)
        if cookie:
            self.send_header("Set-Cookie", "%s=%s; Path=/; Max-Age=%d; HttpOnly; SameSite=Lax" % (COOKIE_NAME, cookie, TOKEN_TTL))
        super().end_headers()


def main():
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Glosor: port %d, logg %s" % (PORT, LOG_FILE))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
