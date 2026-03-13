"""
core/db/database.py — SQLite connection + schema bootstrap
"""

import sqlite3
import threading
from pathlib import Path

ROOT       = Path(__file__).parent.parent.parent
DB_PATH    = ROOT / "store.db"
SCHEMA_SQL = Path(__file__).parent / "schema.sql"

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
    """Run schema.sql to create all tables (idempotent)."""
    sql = SCHEMA_SQL.read_text()
    conn = get_conn()
    conn.executescript(sql)
    conn.commit()
    print("  ✓  Database ready →", DB_PATH)


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
