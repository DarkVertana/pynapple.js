"""
core/db/database.py — SQLite connection + ORM migration bootstrap
"""

import sqlite3
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core import ui

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "store.db"

# One connection per thread (SQLite is not thread-safe by default)
_local = threading.local()


def get_conn() -> sqlite3.Connection:
    """Return a per-thread SQLite connection with row_factory set."""
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        _local.conn = conn
    return _local.conn


def init_db():
    """Apply pending ORM migrations (auto-creates tables on first run)."""
    # Import models so they register with the ORM registry
    import core.db.models  # noqa: F401
    from core.db.orm.migration import migrate_up, get_pending_migrations

    conn = get_conn()
    pending = get_pending_migrations(conn)

    if pending:
        ui.info(f"Applying {len(pending)} migration(s)")
        applied = migrate_up(conn)
        for name in applied:
            ui.ok(name)

    ui.ok(f"Database ready {ui.dim('→')} {ui.dim(str(DB_PATH))}")


# ── Raw query helpers (still available as escape hatches) ─────────────────────

def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    """SELECT — returns list of Row objects."""
    return get_conn().execute(sql, params).fetchall()


def query_one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    """SELECT — returns single Row or None."""
    return get_conn().execute(sql, params).fetchone()


def execute(sql: str, params: tuple = ()) -> int:
    """INSERT / UPDATE / DELETE — returns lastrowid."""
    conn = get_conn()
    cur  = conn.execute(sql, params)
    conn.commit()
    return cur.lastrowid


def execute_many(sql: str, rows: list[tuple]):
    """Bulk INSERT / UPDATE."""
    conn = get_conn()
    conn.executemany(sql, rows)
    conn.commit()
