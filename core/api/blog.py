"""
core/api/blog.py — Blog post API endpoints

GET    /api/posts          → list all published posts (public)
GET    /api/posts/all      → list all posts including drafts (admin)
GET    /api/posts/:slug    → single post by slug
POST   /api/posts          → create a new post (admin)
PUT    /api/posts/:id      → update a post (admin)
DELETE /api/posts/:id      → delete a post (admin)
"""

import re

from core.api import read_json, json_respond, json_error
from core.api.middleware import require_admin
from core.db.orm.client import Client
import core.db.models  # noqa: F401

db = Client()


def _slugify(title: str) -> str:
    """Convert a title to a URL-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def _post_to_dict(post) -> dict:
    """Convert a Post model instance to a JSON-serialisable dict."""
    d = post.to_dict()
    d["published"] = bool(d["published"])
    return d


# ── GET /api/posts — published posts (public) ────────────────────────────────

def list_posts(handler):
    posts = db.post.find_many(
        where={"published": 1},
        order_by={"created_at": "desc"},
    )
    json_respond(handler, {"posts": [_post_to_dict(p) for p in posts]})


# ── GET /api/posts/all — all posts including drafts (admin) ──────────────────

def list_all_posts(handler):
    user = require_admin(handler)
    if not user:
        return
    posts = db.post.find_many(order_by={"created_at": "desc"})
    json_respond(handler, {"posts": [_post_to_dict(p) for p in posts]})


# ── GET /api/posts/:slug — single post ──────────────────────────────────────

def get_post(handler, slug: str):
    post = db.post.find_unique(where={"slug": slug})
    if not post:
        return json_error(handler, "Post not found", 404)
    json_respond(handler, {"post": _post_to_dict(post)})


# ── POST /api/posts — create ─────────────────────────────────────────────────

def create_post(handler):
    user = require_admin(handler)
    if not user:
        return
    data = read_json(handler)
    title = data.get("title", "").strip()
    if not title:
        return json_error(handler, "Title is required")

    slug = data.get("slug") or _slugify(title)

    # Ensure slug is unique
    if db.post.find_unique(where={"slug": slug}):
        return json_error(handler, f"Slug '{slug}' already exists")

    post = db.post.create(data={
        "title":       title,
        "slug":        slug,
        "excerpt":     data.get("excerpt", ""),
        "body":        data.get("body", ""),
        "cover_image": data.get("cover_image", ""),
        "published":   1 if data.get("published") else 0,
        "author_id":   data.get("author_id"),
    })
    json_respond(handler, {"post": _post_to_dict(post)}, 201)


# ── PUT /api/posts/:id — update ──────────────────────────────────────────────

def update_post(handler, post_id: int):
    user = require_admin(handler)
    if not user:
        return
    existing = db.post.find_unique(where={"id": post_id})
    if not existing:
        return json_error(handler, "Post not found", 404)

    data = read_json(handler)
    update_data = {}

    for key in ("title", "excerpt", "body", "cover_image"):
        if key in data:
            update_data[key] = data[key]

    if "slug" in data:
        new_slug = data["slug"]
        conflict = db.post.find_unique(where={"slug": new_slug})
        if conflict and conflict.id != post_id:
            return json_error(handler, f"Slug '{new_slug}' already exists")
        update_data["slug"] = new_slug

    if "published" in data:
        update_data["published"] = 1 if data["published"] else 0

    if update_data:
        update_data["updated_at"] = "datetime('now')"
        db.post.update(where={"id": post_id}, data=update_data)

    post = db.post.find_unique(where={"id": post_id})
    json_respond(handler, {"post": _post_to_dict(post)})


# ── DELETE /api/posts/:id — delete ────────────────────────────────────────────

def delete_post(handler, post_id: int):
    user = require_admin(handler)
    if not user:
        return
    existing = db.post.find_unique(where={"id": post_id})
    if not existing:
        return json_error(handler, "Post not found", 404)

    db.post.delete(where={"id": post_id})
    json_respond(handler, {"deleted": True})
