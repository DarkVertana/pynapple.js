"""
Migration: 0003_add_cover_image
Generated: 2026-03-14T20:02:36
"""


def up(conn):
    conn.executescript("""
        ALTER TABLE posts ADD COLUMN cover_image TEXT NOT NULL DEFAULT '';
    """)


def down(conn):
    conn.executescript("""
        ALTER TABLE posts DROP COLUMN cover_image;
    """)
