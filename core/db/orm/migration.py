"""
core/db/orm/migration.py — schema diff engine, migration file generator, runner

Compares Python model definitions against the live database and generates
versioned migration files with up()/down() functions.
"""

from __future__ import annotations
import importlib
import importlib.util
import sqlite3
import textwrap
from datetime import datetime
from pathlib import Path

from core.db.orm import registry
from core.db.orm.introspect import introspect, get_applied_migrations, TableSchema
from core.db.orm.fields import ForeignKey


MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


# ── Diff operations ──────────────────────────────────────────────────────────

class CreateTable:
    def __init__(self, model_cls):
        self.model_cls = model_cls
        self.table = model_cls.__tablename__

    def up_sql(self) -> str:
        lines = [self.model_cls.table_ddl() + ";"]
        lines.extend(ddl + ";" for ddl in self.model_cls.index_ddls())
        return "\n".join(lines)

    def down_sql(self) -> str:
        # Drop indexes first, then table
        lines = []
        for ddl in self.model_cls.index_ddls():
            idx_name = ddl.split("IF NOT EXISTS ")[1].split(" ON")[0]
            lines.append(f"DROP INDEX IF EXISTS {idx_name};")
        lines.append(f"DROP TABLE IF EXISTS {self.table};")
        return "\n".join(lines)


class DropTable:
    def __init__(self, table_name: str, raw_sql: str):
        self.table = table_name
        self.raw_sql = raw_sql

    def up_sql(self) -> str:
        return f"DROP TABLE IF EXISTS {self.table};"

    def down_sql(self) -> str:
        if self.raw_sql:
            return self.raw_sql + ";"
        return f"-- Cannot recreate {self.table} (no original DDL captured)"


class AddColumn:
    def __init__(self, table_name: str, column_ddl: str, col_name: str):
        self.table = table_name
        self.column_ddl = column_ddl
        self.col_name = col_name

    def up_sql(self) -> str:
        return f"ALTER TABLE {self.table} ADD COLUMN {self.column_ddl};"

    def down_sql(self) -> str:
        return f"ALTER TABLE {self.table} DROP COLUMN {self.col_name};"


class CreateIndex:
    def __init__(self, ddl: str, index_name: str):
        self.ddl = ddl
        self.index_name = index_name

    def up_sql(self) -> str:
        return f"{self.ddl};"

    def down_sql(self) -> str:
        return f"DROP INDEX IF EXISTS {self.index_name};"


class DropIndex:
    def __init__(self, index_name: str):
        self.index_name = index_name

    def up_sql(self) -> str:
        return f"DROP INDEX IF EXISTS {self.index_name};"

    def down_sql(self) -> str:
        return f"-- Cannot recreate index {self.index_name}"


# ── Dependency ordering ──────────────────────────────────────────────────────

def _topological_sort(models: list[type]) -> list[type]:
    """Sort models so that tables with FK dependencies come after their targets."""
    model_map = {m.__name__: m for m in models}
    visited: set[str] = set()
    result: list[type] = []

    def visit(name: str):
        if name in visited:
            return
        visited.add(name)
        model = model_map.get(name)
        if model is None:
            return
        # Visit FK dependencies first
        for col in model._columns:
            if isinstance(col, ForeignKey) and col.references in model_map:
                visit(col.references)
        result.append(model)

    for m in models:
        visit(m.__name__)
    return result


# ── Diff engine ──────────────────────────────────────────────────────────────

def diff(conn: sqlite3.Connection) -> list:
    """Compare registered models against the live database schema.

    Returns a list of operation objects (CreateTable, DropTable, AddColumn, etc.).
    """
    current = introspect(conn)
    models = registry.all_models()
    desired_tables = {m.__tablename__: m for m in models}
    ops: list = []

    # 1) New tables (in dependency order)
    new_models = [m for m in models if m.__tablename__ not in current]
    for model_cls in _topological_sort(new_models):
        ops.append(CreateTable(model_cls))

    # 2) Dropped tables (reverse dependency order)
    for table_name, schema in current.items():
        if table_name not in desired_tables:
            ops.append(DropTable(table_name, schema.raw_sql))

    # 3) Modified tables — check for new columns and indexes
    for table_name, model_cls in desired_tables.items():
        if table_name not in current:
            continue  # already handled as CreateTable

        live_schema = current[table_name]
        live_col_names = {c.name for c in live_schema.columns}
        live_idx_names = {i.name for i in live_schema.indexes}

        # New columns
        for col in model_cls._columns:
            if col.name not in live_col_names:
                ddl = col.to_ddl()
                if isinstance(col, ForeignKey):
                    target = registry.get(col.references)
                    ddl += " " + col.references_clause(target.__tablename__)
                ops.append(AddColumn(table_name, ddl, col.name))

        # New indexes
        for idx_ddl in model_cls.index_ddls():
            idx_name = idx_ddl.split("IF NOT EXISTS ")[1].split(" ON")[0]
            if idx_name not in live_idx_names:
                ops.append(CreateIndex(idx_ddl, idx_name))

        # Dropped indexes
        desired_idx_names = set()
        for idx_ddl in model_cls.index_ddls():
            desired_idx_names.add(idx_ddl.split("IF NOT EXISTS ")[1].split(" ON")[0])
        for idx in live_schema.indexes:
            if idx.name not in desired_idx_names:
                ops.append(DropIndex(idx.name))

    return ops


# ── Migration file generator ─────────────────────────────────────────────────

def _next_migration_number() -> int:
    """Return the next migration number based on existing files."""
    existing = sorted(MIGRATIONS_DIR.glob("[0-9]*.py"))
    if not existing:
        return 1
    last = existing[-1].stem
    num = int(last.split("_")[0])
    return num + 1


def generate_migration(conn: sqlite3.Connection, name: str = "auto") -> Path | None:
    """Diff models vs DB, generate a migration file if there are changes."""
    ops = diff(conn)
    if not ops:
        return None

    num = _next_migration_number()
    filename = f"{num:04d}_{name}.py"
    filepath = MIGRATIONS_DIR / filename

    up_parts = []
    down_parts = []

    for op in ops:
        up_parts.append(op.up_sql())
    for op in reversed(ops):
        down_parts.append(op.down_sql())

    up_sql = "\n".join(up_parts)
    down_sql = "\n".join(down_parts)

    migration_name = f"{num:04d}_{name}"

    content = textwrap.dedent(f'''\
        """
        Migration: {migration_name}
        Generated: {datetime.now().isoformat(timespec="seconds")}
        """


        def up(conn):
            conn.executescript("""
        {textwrap.indent(up_sql, "        ")}
            """)


        def down(conn):
            conn.executescript("""
        {textwrap.indent(down_sql, "        ")}
            """)
    ''')

    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    # Ensure __init__.py exists
    init_file = MIGRATIONS_DIR / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

    filepath.write_text(content)
    return filepath


# ── Migration runner ─────────────────────────────────────────────────────────

def _load_migration(filepath: Path):
    """Import a migration file as a module."""
    spec = importlib.util.spec_from_file_location(filepath.stem, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_pending_migrations(conn: sqlite3.Connection) -> list[Path]:
    """Return migration files not yet applied, in order."""
    applied = set(get_applied_migrations(conn))
    all_files = sorted(MIGRATIONS_DIR.glob("[0-9]*.py"))
    return [f for f in all_files if f.stem not in applied]


def migrate_up(conn: sqlite3.Connection, steps: int | None = None) -> list[str]:
    """Apply pending migrations. Returns list of applied migration names."""
    pending = get_pending_migrations(conn)
    if steps is not None:
        pending = pending[:steps]

    applied_names = []
    for filepath in pending:
        mod = _load_migration(filepath)
        mod.up(conn)
        conn.execute(
            "INSERT INTO _migrations (name) VALUES (?)",
            (filepath.stem,),
        )
        conn.commit()
        applied_names.append(filepath.stem)

    return applied_names


def migrate_down(conn: sqlite3.Connection, steps: int = 1) -> list[str]:
    """Roll back the last N applied migrations. Returns rolled-back names."""
    applied = get_applied_migrations(conn)
    if not applied:
        return []

    to_rollback = applied[-steps:]
    rolled_back = []

    for name in reversed(to_rollback):
        filepath = MIGRATIONS_DIR / f"{name}.py"
        if not filepath.exists():
            raise FileNotFoundError(f"Migration file not found: {filepath}")
        mod = _load_migration(filepath)
        mod.down(conn)
        conn.execute("DELETE FROM _migrations WHERE name = ?", (name,))
        conn.commit()
        rolled_back.append(name)

    return rolled_back


def migration_status(conn: sqlite3.Connection) -> list[tuple[str, bool]]:
    """Return all migrations with their applied status."""
    applied = set(get_applied_migrations(conn))
    all_files = sorted(MIGRATIONS_DIR.glob("[0-9]*.py"))
    return [(f.stem, f.stem in applied) for f in all_files]
