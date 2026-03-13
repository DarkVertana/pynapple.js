"""
core/db/seed.py — populate the database with sample data

Usage:
  python3 -m core.db.seed
"""

import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.db.database import init_db, execute, execute_many, query_one


def _hash(password: str) -> str:
    salt = os.urandom(16).hex()
    h    = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"{salt}:{h.hex()}"


def seed():
    init_db()

    # ── Categories ────────────────────────────────────────────────────────────
    categories = [
        ("Electronics", "electronics"),
        ("Clothing",    "clothing"),
        ("Books",       "books"),
        ("Home",        "home"),
    ]
    for name, slug in categories:
        if not query_one("SELECT id FROM categories WHERE slug = ?", (slug,)):
            execute("INSERT INTO categories (name, slug) VALUES (?, ?)", (name, slug))

    cat = {
        s: query_one("SELECT id FROM categories WHERE slug = ?", (s,))["id"]
        for _, s in categories
    }

    # ── Products ──────────────────────────────────────────────────────────────
    products = [
        ("Wireless Headphones",  "Over-ear noise-cancelling headphones with 30h battery.", 79.99,  50, "https://placehold.co/400x300?text=Headphones",  cat["electronics"]),
        ("Mechanical Keyboard",  "TKL mechanical keyboard with RGB and hot-swap switches.", 119.99, 30, "https://placehold.co/400x300?text=Keyboard",     cat["electronics"]),
        ("USB-C Hub 7-in-1",     "7 ports: HDMI 4K, 3×USB-A, SD, MicroSD, PD 100W.",     39.99, 100, "https://placehold.co/400x300?text=USB+Hub",      cat["electronics"]),
        ("Classic White Tee",    "100% organic cotton, unisex fit, pre-shrunk.",            19.99, 200, "https://placehold.co/400x300?text=White+Tee",    cat["clothing"]),
        ("Cargo Pants",          "Durable ripstop fabric, 6 pockets, slim fit.",            54.99,  80, "https://placehold.co/400x300?text=Cargo+Pants",  cat["clothing"]),
        ("Hoodie — Midnight",    "French terry cotton blend, kangaroo pocket.",             64.99,  60, "https://placehold.co/400x300?text=Hoodie",       cat["clothing"]),
        ("Clean Code",           "Robert C. Martin — the classic software craftsmanship book.", 34.99, 40, "https://placehold.co/400x300?text=Clean+Code", cat["books"]),
        ("The Pragmatic Programmer", "Hunt & Thomas — your journey to mastery.",            42.99,  35, "https://placehold.co/400x300?text=Pragmatic",    cat["books"]),
        ("Ceramic Desk Plant",   "Low-maintenance succulent in a minimal white pot.",       24.99,  75, "https://placehold.co/400x300?text=Plant",        cat["home"]),
        ("LED Desk Lamp",        "Dimmable, 3 color temps, USB-A charging port.",           44.99,  55, "https://placehold.co/400x300?text=Desk+Lamp",    cat["home"]),
    ]
    for name, desc, price, stock, img, cat_id in products:
        if not query_one("SELECT id FROM products WHERE name = ?", (name,)):
            execute(
                "INSERT INTO products (name, description, price, stock, image_url, category_id) VALUES (?,?,?,?,?,?)",
                (name, desc, price, stock, img, cat_id),
            )

    # ── Admin user ────────────────────────────────────────────────────────────
    if not query_one("SELECT id FROM users WHERE email = ?", ("admin@store.com",)):
        execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
            ("Admin", "admin@store.com", _hash("admin123"), "admin"),
        )
        print("  ✓  Admin user created  →  admin@store.com / admin123")

    print(f"  ✓  Seeded {len(products)} products, {len(categories)} categories")


if __name__ == "__main__":
    seed()
