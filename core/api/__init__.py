"""
core/api — JSON API route dispatcher

Each sub-module exposes handler functions that receive the raw
BaseHTTPRequestHandler and use `_json_respond` / `_read_json` helpers.
"""

import json


def read_body(handler) -> bytes:
    """Read the full request body."""
    length = int(handler.headers.get("Content-Length", 0))
    return handler.rfile.read(length) if length else b""


def read_json(handler) -> dict:
    """Read and parse the JSON request body."""
    raw = read_body(handler)
    return json.loads(raw) if raw else {}


def json_respond(handler, data, status: int = 200):
    """Send a JSON response."""
    body = json.dumps(data, default=str).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


def json_error(handler, message: str, status: int = 400):
    """Send a JSON error response."""
    json_respond(handler, {"error": message}, status)
