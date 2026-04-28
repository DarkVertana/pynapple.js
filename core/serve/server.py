"""
core/serve/server.py — pynaple js · unified server (stdlib only)

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

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.db.database import init_db
from core import ui
from core.api import json_error
from core.api import blog as api_blog
from core.api import upload as api_upload
from core.api import auth as api_auth

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
  <title>pynaple js</title>
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
class PynapleHandler(BaseHTTPRequestHandler):
    mode      = "dev"
    serve_dir = DEV_DIR
    verbose   = False

    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, BrokenPipeError):
            pass

    def log_message(self, fmt, *args):
        if self.verbose:
            print(f"  {ui.dim(self.address_string())}  {fmt % args}")

    def log_error(self, fmt, *args):
        ui.fail(fmt % args)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/_reload":
            self._sse_reload()
        elif path.startswith("/api/"):
            self._route_api("GET", path)
        elif path.startswith("/uploads/"):
            self._serve_upload(path)
        elif path in ("/", "/index.html"):
            if self.mode == "dev":
                self._respond(200, "text/html; charset=utf-8", _DEV_HTML)
            else:
                self._serve_file(self.serve_dir / "index.html")
        else:
            self._serve_file(self.serve_dir / path.lstrip("/"))

    def do_POST(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            self._route_api("POST", path)
        else:
            self._respond(404, "text/plain", b"Not found")

    def do_PUT(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            self._route_api("PUT", path)
        else:
            self._respond(404, "text/plain", b"Not found")

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            self._route_api("DELETE", path)
        else:
            self._respond(404, "text/plain", b"Not found")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _route_api(self, method: str, path: str):
        """Dispatch API requests to the correct handler."""
        try:
            # ── Auth ─────────────────────────────────────────────
            if method == "POST" and path == "/api/auth/login":
                api_auth.login(self)
            elif method == "POST" and path == "/api/auth/register":
                api_auth.register(self)
            elif method == "GET" and path == "/api/auth/me":
                api_auth.me(self)
            elif method == "POST" and path == "/api/auth/logout":
                api_auth.logout(self)

            # ── Blog posts ───────────────────────────────────────
            elif method == "GET" and path == "/api/posts":
                api_blog.list_posts(self)
            elif method == "GET" and path == "/api/posts/all":
                api_blog.list_all_posts(self)
            elif method == "GET" and path.startswith("/api/posts/"):
                slug = path.split("/api/posts/")[1]
                api_blog.get_post(self, slug)
            elif method == "POST" and path == "/api/upload":
                api_upload.upload_file(self)
            elif method == "POST" and path == "/api/posts":
                api_blog.create_post(self)
            elif method == "PUT" and path.startswith("/api/posts/"):
                post_id = int(path.split("/api/posts/")[1])
                api_blog.update_post(self, post_id)
            elif method == "DELETE" and path.startswith("/api/posts/"):
                post_id = int(path.split("/api/posts/")[1])
                api_blog.delete_post(self, post_id)
            else:
                json_error(self, "Not found", 404)
        except Exception as e:
            json_error(self, str(e), 500)

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

    def _serve_upload(self, path: str):
        """Serve files from the uploads/ directory."""
        filename = path.split("/uploads/")[-1]
        # Prevent directory traversal
        if ".." in filename or "/" in filename:
            self._respond(403, "text/plain", b"Forbidden")
            return
        target = ROOT / "uploads" / filename
        if target.exists() and target.is_file():
            mime, _ = mimetypes.guess_type(str(target))
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.end_headers()
            self.wfile.write(data)
        else:
            self._respond(404, "text/plain", b"Not found")

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
    PynapleHandler.mode      = mode
    PynapleHandler.serve_dir = DEV_DIR if mode == "dev" else DIST_DIR
    PynapleHandler.verbose   = (mode == "dev")

    init_db()

    if mode == "dev":
        _start_reload_watcher()

    server = ThreadingHTTPServer(("0.0.0.0", port), PynapleHandler)

    host = "localhost" if mode == "dev" else "0.0.0.0"
    ui.server_box(mode, port, host)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        ui.stopped()
        server.server_close()


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "dev")
