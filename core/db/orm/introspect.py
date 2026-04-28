"""
core/db/orm/introspect.py — read live SQLite schema via PRAGMAs

Returns structured data representing the current database state so the
migration engine can diff it against the desired state from Python models.
"""

from __future__ import annotations
import sqlite3
from dataclasses import dataclass, field


@dataclass
class ColumnInfo:
    name: str
    type: str          # "INTEGER", "TEXT", "REAL", "BLOB"
    notnull: bool
    default: str | None
    pk: bool


@dataclass
class ForeignKeyInfo:
    from_col: str
    to_table: str
    to_col: str
    on_delete: str
    on_update: str


@dataclass
class IndexInfo:
    name: str
    columns: list[str]
    unique: bool


@dataclass
class TableSchema:
    name: str
    columns: list[ColumnInfo] = field(default_factory=list)
    foreign_keys: list[ForeignKeyInfo] = field(default_factory=list)
    indexes: list[IndexInfo] = field(default_factory=list)
    raw_sql: str = ""  # the original CREATE TABLE statement


def introspect(conn: sqlite3.Connection) -> dict[str, TableSchema]:
    """Read the full schema of the connected database.

    Returns a dict of table_name → TableSchema, excluding internal tables
    (sqlite_*, _migrations).
    """
    tables: dict[str, TableSchema] = {}

    # Get all user tables
    rows = conn.execute(
        "SELECT name, sql FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name != '_migrations'"
    ).fetchall()

    for row in rows:
        table_name = row[0]
        raw_sql = row[1] or ""
        schema = TableSchema(name=table_name, raw_sql=raw_sql)

        # Columns
        for col in conn.execute(f"PRAGMA table_info({table_name})").fetchall():
            schema.columns.append(ColumnInfo(
                name=col[1],
                type=col[2].upper() if col[2] else "",
                notnull=bool(col[3]),
                default=col[4],
                pk=bool(col[5]),
            ))

        # Foreign keys
        for fk in conn.execute(f"PRAGMA foreign_key_list({table_name})").fetchall():
            schema.foreign_keys.append(ForeignKeyInfo(
                from_col=fk[3],
                to_table=fk[2],
                to_col=fk[4],
                on_update=fk[5].upper() if fk[5] else "NO ACTION",
                on_delete=fk[6].upper() if fk[6] else "NO ACTION",
            ))

        # Indexes (exclude auto-created sqlite_autoindex_*)
        for idx in conn.execute(f"PRAGMA index_list({table_name})").fetchall():
            idx_name = idx[1]
            if idx_name.startswith("sqlite_autoindex_"):
                continue
            idx_unique = bool(idx[2])
            idx_cols = [
                c[2] for c in conn.execute(f"PRAGMA index_info({idx_name})").fetchall()
            ]
            schema.indexes.append(IndexInfo(
                name=idx_name,
                columns=idx_cols,
                unique=idx_unique,
            ))

        tables[table_name] = schema

    return tables


def get_applied_migrations(conn: sqlite3.Connection) -> list[str]:
    """Return list of applied migration names, in order."""
    # Ensure tracking table exists
    conn.execute(
        "CREATE TABLE IF NOT EXISTS _migrations ("
        "    name       TEXT PRIMARY KEY,"
        "    applied_at TEXT NOT NULL DEFAULT (datetime('now'))"
        ")"
    )
    conn.commit()

    rows = conn.execute(
        "SELECT name FROM _migrations ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]
