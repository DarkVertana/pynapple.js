"""
core/api/upload.py — file upload endpoint

POST /api/upload   → multipart/form-data image upload → returns { "url": "/uploads/..." }
"""

import os
import time
import hashlib
from pathlib import Path

from core.api import json_respond, json_error

UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
MAX_SIZE    = 5 * 1024 * 1024  # 5 MB


def _parse_multipart(handler) -> tuple[bytes, str]:
    """Parse a multipart/form-data body and extract the first file.

    Returns (file_bytes, original_filename).
    """
    content_type = handler.headers.get("Content-Type", "")
    if "boundary=" not in content_type:
        raise ValueError("Missing multipart boundary")

    boundary = content_type.split("boundary=")[1].strip()
    if boundary.startswith('"') and boundary.endswith('"'):
        boundary = boundary[1:-1]

    length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(length)

    boundary_bytes = f"--{boundary}".encode()
    parts = body.split(boundary_bytes)

    for part in parts:
        if b"Content-Disposition" not in part:
            continue
        # Split headers from body
        if b"\r\n\r\n" in part:
            header_section, file_data = part.split(b"\r\n\r\n", 1)
        elif b"\n\n" in part:
            header_section, file_data = part.split(b"\n\n", 1)
        else:
            continue

        headers_str = header_section.decode("utf-8", errors="replace")
        if 'filename="' not in headers_str:
            continue

        # Extract filename
        filename = ""
        for h in headers_str.split("\r\n"):
            if "filename=" in h:
                filename = h.split('filename="')[1].split('"')[0]
                break

        # Strip trailing boundary markers
        if file_data.endswith(b"\r\n"):
            file_data = file_data[:-2]
        if file_data.endswith(b"--\r\n"):
            file_data = file_data[:-4]
        if file_data.endswith(b"--"):
            file_data = file_data[:-2]
        if file_data.endswith(b"\r\n"):
            file_data = file_data[:-2]

        return file_data, filename

    raise ValueError("No file found in upload")


def upload_file(handler):
    """Handle POST /api/upload — save file, return URL."""
    try:
        file_data, filename = _parse_multipart(handler)
    except ValueError as e:
        return json_error(handler, str(e))

    if len(file_data) > MAX_SIZE:
        return json_error(handler, f"File too large (max {MAX_SIZE // 1024 // 1024}MB)")

    # Validate extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        return json_error(handler, f"File type '{ext}' not allowed. Use: {', '.join(ALLOWED_EXT)}")

    # Generate unique filename: timestamp-hash.ext
    file_hash = hashlib.md5(file_data).hexdigest()[:8]
    safe_name = f"{int(time.time())}-{file_hash}{ext}"

    # Save
    UPLOADS_DIR.mkdir(exist_ok=True)
    dest = UPLOADS_DIR / safe_name
    dest.write_bytes(file_data)

    url = f"/uploads/{safe_name}"
    json_respond(handler, {"url": url}, 201)
