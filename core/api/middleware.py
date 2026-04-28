"""
core/api/middleware.py — JWT authentication middleware

Usage:
    from core.api.middleware import require_auth, require_admin

    def my_handler(handler):
        user = require_auth(handler)
        if not user:
            return  # 401 already sent

    def admin_handler(handler):
        user = require_admin(handler)
        if not user:
            return  # 401/403 already sent
"""

import os
import jwt
from core.api import json_error
from core.db.orm.client import Client
import core.db.models  # noqa: F401

db = Client()

JWT_SECRET = os.environ.get("JWT_SECRET", "pynaple-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"


def get_current_user(handler):
    """Extract and validate JWT from Authorization header. Returns user or None."""
    auth_header = handler.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = db.user.find_unique(where={"id": int(user_id)})
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def require_auth(handler):
    """Middleware: returns user or sends 401 and returns None."""
    user = get_current_user(handler)
    if not user:
        json_error(handler, "Authentication required", 401)
        return None
    return user


def require_admin(handler):
    """Middleware: returns admin user or sends 401/403 and returns None."""
    user = require_auth(handler)
    if not user:
        return None
    if user.role != "admin":
        json_error(handler, "Admin access required", 403)
        return None
    return user
