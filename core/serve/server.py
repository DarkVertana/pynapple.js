"""
core/serve/server.py — pynapple js · unified server (stdlib only)

  dev  :2000  ->  pages/.dev/  +  SSE live-reload
  prod :8000  ->  pages/dist/
"""

import mimetypes
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from core.db.database import init_db

ROOT     = Path(__file__).parent.parent.parent
DEV_DIR  = ROOT / "pages" / ".dev"
DIST_DIR = ROOT / "pages" / "dist"

# ── Live-reload broadcast ──────────────────────────────────────────────────────
_reload_clients = []
_reload_lock    = threading.Lock()


_reload_type = "js"   # last signal type: "js" | "css"


def _start_reload_watcher():
    global _reload_type
    reload_file = DEV_DIR / ".reload"
    last = ""

    def _watch():
        global _reload_type
        nonlocal last
        while True:
            time.sleep(0.15)
            try:
                raw = reload_file.read_text() if reload_file.exists() else ""
                if raw and raw != last:
                    last = raw
                    # format: "type:timestamp" or legacy plain timestamp
                    if ":" in raw:
                        _reload_type = raw.split(":", 1)[0]
                    else:
                        _reload_type = "js"
                    with _reload_lock:
                        for ev in list(_reload_clients):
                            ev.set()
            except Exception:
                pass

    threading.Thread(target=_watch, daemon=True).start()


_DEV_HTML = b"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>pynapple js</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>%F0%9F%8D%8D</text></svg>"/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="/bundle.css"/>
  <script>
    const es=new EventSource('/_reload');
    es.onmessage=e=>{
      if(e.data==='css'){
        const l=document.querySelector('link[rel=stylesheet][href*="bundle.css"]');
        if(l){l.href=l.href.replace(/\\?.*$/,'')+'?'+Date.now();}
      } else {
        location.reload();
      }
    };
  </script>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/bundle.js"></script>
</body>
</html>"""


# ── Request handler ────────────────────────────────────────────────────────────
class PynappleHandler(BaseHTTPRequestHandler):
    mode      = "dev"
    serve_dir = DEV_DIR
    verbose   = False

    def log_message(self, fmt, *args):
        if self.verbose:
            print(f"  [{self.address_string()}] {fmt % args}")

    def log_error(self, fmt, *args):
        print(f"  [!] {fmt % args}", file=sys.stderr)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/_reload":
            self._sse_reload()
        elif path in ("/", "/index.html"):
            if self.mode == "dev":
                self._respond(200, "text/html; charset=utf-8", _DEV_HTML)
            else:
                self._serve_file(self.serve_dir / "index.html")
        else:
            self._serve_file(self.serve_dir / path.lstrip("/"))

    def _sse_reload(self):
        self.send_response(200)
        self.send_header("Content-Type",  "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection",    "keep-alive")
        self.end_headers()
        ev = threading.Event()
        with _reload_lock:
            _reload_clients.append(ev)
        try:
            while True:
                if ev.wait(timeout=25):
                    msg = f"data: {_reload_type}\n\n".encode()
                    self.wfile.write(msg)
                    self.wfile.flush()
                    ev.clear()
                else:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with _reload_lock:
                try:
                    _reload_clients.remove(ev)
                except ValueError:
                    pass

    def _serve_file(self, target):
        target = Path(target).resolve()
        if not target.exists() or not target.is_file():
            if self.mode == "dev":
                self._respond(200, "text/html; charset=utf-8", _DEV_HTML)
            else:
                fallback = self.serve_dir / "index.html"
                if fallback.exists():
                    self._serve_file(fallback)
                else:
                    self._respond(404, "text/plain", b"Not found")
            return
        mime, _ = mimetypes.guess_type(str(target))
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",   mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _respond(self, status, mime, body):
        self.send_response(status)
        self.send_header("Content-Type",   mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ── Entry point ────────────────────────────────────────────────────────────────
def run(mode="dev"):
    port = 2000 if mode == "dev" else 8000
    PynappleHandler.mode      = mode
    PynappleHandler.serve_dir = DEV_DIR if mode == "dev" else DIST_DIR
    PynappleHandler.verbose   = (mode == "dev")

    init_db()

    if mode == "dev":
        _start_reload_watcher()

    server = ThreadingHTTPServer(("0.0.0.0", port), PynappleHandler)

    if mode == "dev":
        print("  +------------------------------------------+")
        print("  |  pynapple js  .  unified  :2000          |")
        print(f"  |  http://localhost:{port}                   |")
        print("  +------------------------------------------+\n")
    else:
        print("  +------------------------------------------+")
        print("  |  pynapple js  .  production  :8000       |")
        print(f"  |  http://0.0.0.0:{port}                    |")
        print("  +------------------------------------------+\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "dev")
