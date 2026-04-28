"""
core/api/auth.py — Authentication API endpoints

POST   /api/auth/login     → login with email + password, returns JWT
POST   /api/auth/register  → create account, returns JWT
GET    /api/auth/me         → get current user (requires auth)
POST   /api/auth/logout    → invalidate token (client-side)
"""

import datetime
import bcrypt
import jwt

from core.api import read_json, json_respond, json_error
from core.api.middleware import JWT_SECRET, JWT_ALGORITHM, require_auth
from core.db.orm.client import Client
import core.db.models  # noqa: F401

db = Client()

TOKEN_EXPIRY_HOURS = 72


def _hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def _create_token(user_id: int, role: str) -> str:
    """Create a JWT token for a user."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _user_to_dict(user) -> dict:
    """Serialize user for API response (excludes password_hash)."""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at,
    }


# ── POST /api/auth/login ────────────────────────────────────────────────────

def login(handler):
    data = read_json(handler)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return json_error(handler, "Email and password are required")

    user = db.user.find_unique(where={"email": email})
    if not user or not _verify_password(password, user.password_hash):
        return json_error(handler, "Invalid email or password", 401)

    token = _create_token(user.id, user.role)
    json_respond(handler, {
        "token": token,
        "user": _user_to_dict(user),
    })


# ── POST /api/auth/register ─────────────────────────────────────────────────

def register(handler):
    data = read_json(handler)
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name:
        return json_error(handler, "Name is required")
    if not email:
        return json_error(handler, "Email is required")
    if len(password) < 6:
        return json_error(handler, "Password must be at least 6 characters")

    existing = db.user.find_unique(where={"email": email})
    if existing:
        return json_error(handler, "Email already registered", 409)

    user = db.user.create(data={
        "name": name,
        "email": email,
        "password_hash": _hash_password(password),
        "role": "customer",
    })

    token = _create_token(user.id, user.role)
    json_respond(handler, {
        "token": token,
        "user": _user_to_dict(user),
    }, 201)


# ── GET /api/auth/me ─────────────────────────────────────────────────────────

def me(handler):
    user = require_auth(handler)
    if not user:
        return
    json_respond(handler, {"user": _user_to_dict(user)})


# ── POST /api/auth/logout ───────────────────────────────────────────────────

def logout(handler):
    # JWT is stateless — client discards the token.
    # This endpoint exists for API completeness.
    json_respond(handler, {"ok": True})
