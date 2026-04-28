"""
core/db/seed.py — populate the database with sample data using pynaple ORM

Usage:
  python3 -m core.db.seed
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import bcrypt

from core import ui
from core.db.database import init_db
from core.db.orm.client import Client
import core.db.models  # noqa: F401  — register models


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def seed():
    init_db()
    db = Client()

    # ── Categories ────────────────────────────────────────────────────────
    categories = [
        {"name": "Electronics", "slug": "electronics"},
        {"name": "Clothing",    "slug": "clothing"},
        {"name": "Books",       "slug": "books"},
        {"name": "Home",        "slug": "home"},
    ]
    for cat in categories:
        if not db.category.find_unique(where={"slug": cat["slug"]}):
            db.category.create(data=cat)

    # Build lookup
    cat_map = {}
    for cat in categories:
        cat_map[cat["slug"]] = db.category.find_unique(where={"slug": cat["slug"]}).id

    # ── Products ──────────────────────────────────────────────────────────
    products = [
        {"name": "Wireless Headphones",     "description": "Over-ear noise-cancelling headphones with 30h battery.",        "price": 79.99,  "stock": 50,  "image_url": "https://placehold.co/400x300?text=Headphones",  "category_id": cat_map["electronics"]},
        {"name": "Mechanical Keyboard",     "description": "TKL mechanical keyboard with RGB and hot-swap switches.",       "price": 119.99, "stock": 30,  "image_url": "https://placehold.co/400x300?text=Keyboard",     "category_id": cat_map["electronics"]},
        {"name": "USB-C Hub 7-in-1",        "description": "7 ports: HDMI 4K, 3×USB-A, SD, MicroSD, PD 100W.",            "price": 39.99,  "stock": 100, "image_url": "https://placehold.co/400x300?text=USB+Hub",      "category_id": cat_map["electronics"]},
        {"name": "Classic White Tee",       "description": "100% organic cotton, unisex fit, pre-shrunk.",                  "price": 19.99,  "stock": 200, "image_url": "https://placehold.co/400x300?text=White+Tee",    "category_id": cat_map["clothing"]},
        {"name": "Cargo Pants",             "description": "Durable ripstop fabric, 6 pockets, slim fit.",                  "price": 54.99,  "stock": 80,  "image_url": "https://placehold.co/400x300?text=Cargo+Pants",  "category_id": cat_map["clothing"]},
        {"name": "Hoodie — Midnight",       "description": "French terry cotton blend, kangaroo pocket.",                   "price": 64.99,  "stock": 60,  "image_url": "https://placehold.co/400x300?text=Hoodie",       "category_id": cat_map["clothing"]},
        {"name": "Clean Code",              "description": "Robert C. Martin — the classic software craftsmanship book.",   "price": 34.99,  "stock": 40,  "image_url": "https://placehold.co/400x300?text=Clean+Code",   "category_id": cat_map["books"]},
        {"name": "The Pragmatic Programmer","description": "Hunt & Thomas — your journey to mastery.",                      "price": 42.99,  "stock": 35,  "image_url": "https://placehold.co/400x300?text=Pragmatic",    "category_id": cat_map["books"]},
        {"name": "Ceramic Desk Plant",      "description": "Low-maintenance succulent in a minimal white pot.",             "price": 24.99,  "stock": 75,  "image_url": "https://placehold.co/400x300?text=Plant",        "category_id": cat_map["home"]},
        {"name": "LED Desk Lamp",           "description": "Dimmable, 3 color temps, USB-A charging port.",                 "price": 44.99,  "stock": 55,  "image_url": "https://placehold.co/400x300?text=Desk+Lamp",    "category_id": cat_map["home"]},
    ]
    for p in products:
        if not db.product.find_unique(where={"name": p["name"]}):
            db.product.create(data=p)

    # ── Admin user ────────────────────────────────────────────────────────
    if not db.user.find_unique(where={"email": "admin@store.com"}):
        db.user.create(data={
            "name": "Admin",
            "email": "admin@store.com",
            "password_hash": _hash("admin123"),
            "role": "admin",
        })
        ui.ok(f"Admin user created {ui.dim('→')} admin@store.com / admin123")

    ui.ok(f"Seeded {len(products)} products, {len(categories)} categories")


if __name__ == "__main__":
    seed()
