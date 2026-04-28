"""
core/db/migrate.py — migration CLI for pynaple ORM

Usage:
    python -m core.db.migrate generate [name]   Generate a new migration
    python -m core.db.migrate up                 Apply all pending migrations
    python -m core.db.migrate down               Roll back the last migration
    python -m core.db.migrate status             Show migration status
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import ui
from core.db.database import get_conn
from core.db.orm.migration import (
    generate_migration,
    migrate_up,
    migrate_down,
    migration_status,
    get_pending_migrations,
)

# Import models so they register with the registry
import core.db.models  # noqa: F401


def cmd_generate(name: str = "auto"):
    ui.info("Comparing models against database")
    conn = get_conn()
    filepath = generate_migration(conn, name)
    if filepath:
        ui.ok(f"Migration created {ui.dim('→')} {filepath.name}")
    else:
        ui.ok("No changes detected — database is up to date")


def cmd_up():
    conn = get_conn()
    pending = get_pending_migrations(conn)
    if not pending:
        ui.ok("No pending migrations")
        return
    ui.info(f"Applying {len(pending)} migration(s)")
    applied = migrate_up(conn)
    for name in applied:
        ui.ok(name)
    ui.ok(f"Applied {len(applied)} migration(s)")


def cmd_down():
    conn = get_conn()
    ui.info("Rolling back last migration")
    rolled = migrate_down(conn)
    if not rolled:
        ui.warn("No migrations to roll back")
        return
    for name in rolled:
        ui.ok(f"Rolled back {ui.dim('→')} {name}")


def cmd_status():
    conn = get_conn()
    statuses = migration_status(conn)
    if not statuses:
        ui.warn("No migration files found")
        return
    for name, applied in statuses:
        if applied:
            ui.ok(name)
        else:
            ui.info(f"{name} {ui.dim('(pending)')}")


def main():
    commands = ("generate", "up", "down", "status")
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        opts = " | ".join(commands)
        ui.console.print(f"\n  [bold]Usage:[/bold]  python -m core.db.migrate [{opts}] \\[name]\n")
        sys.exit(1)

    cmd = sys.argv[1]
    ui.console.print(f"\n  [bold]pynaple orm[/bold] [dim]·[/dim] migrate {cmd}\n")

    if cmd == "generate":
        name = sys.argv[2] if len(sys.argv) > 2 else "auto"
        cmd_generate(name)
    elif cmd == "up":
        cmd_up()
    elif cmd == "down":
        cmd_down()
    elif cmd == "status":
        cmd_status()

    print()


if __name__ == "__main__":
    main()
