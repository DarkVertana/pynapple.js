"""
Migration: 0002_add_posts
Generated: 2026-03-14T19:53:14
"""


def up(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    excerpt TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    published INTEGER NOT NULL DEFAULT 0,
    author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_posts_author_id ON posts(author_id);
    """)


def down(conn):
    conn.executescript("""
        DROP INDEX IF EXISTS idx_posts_author_id;
DROP TABLE IF EXISTS posts;
    """)
