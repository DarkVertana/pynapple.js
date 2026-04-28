"""
core/ui.py — Rich-powered terminal styling for pynaple js

Provides pretty-printed output with a consistent visual language:

  ui.ok("message")       ✓  green success
  ui.info("message")     →  blue in-progress
  ui.warn("message")     ⚠  yellow warning
  ui.fail("message")     ✗  red error
  ui.step(1, 2, "msg")   numbered phase header
  ui.banner("title")     branded startup banner
  ui.server_box(...)     server-ready panel
  ui.dim("text")         muted helper text
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich import box

console = Console(highlight=False)
err_console = Console(stderr=True, highlight=False)

BRAND = "pynaple js"
VERSION = "1.0.0"

# Track timing per step
_step_start: float | None = None


# ── Inline markup helpers (return str for embedding) ─────────────────────────
def dim(text: str) -> str:
    return f"[dim]{text}[/dim]"


# ── Status helpers ───────────────────────────────────────────────────────────
def ok(msg: str):
    console.print(f"   [green]●[/green]  {msg}")

def info(msg: str):
    console.print(f"   [blue]◌[/blue]  {msg}")

def warn(msg: str):
    console.print(f"   [yellow]▲[/yellow]  {msg}")

def fail(msg: str):
    err_console.print(f"   [red]✖[/red]  {msg}")


# ── Step counter ─────────────────────────────────────────────────────────────
def step(current: int, total: int, label: str):
    global _step_start

    # Print elapsed time for previous step
    if _step_start is not None:
        elapsed = time.time() - _step_start
        console.print(f"   [dim]done in {elapsed:.1f}s[/dim]")

    _step_start = time.time()

    bar_filled = current
    bar_empty = total - current
    progress = f"[cyan]{'━' * bar_filled}[/cyan][dim]{'─' * bar_empty}[/dim]"

    console.print()
    console.print(f"   {progress}  [bold white]{label}[/bold white]  [dim]({current}/{total})[/dim]")


# ── Banner ───────────────────────────────────────────────────────────────────
_LOGO = r"""[bold cyan]                                      .__
    ______ ___.__.  ____  _____  ____ |  |   ____
    \____ <   |  | /    \ \__  \ \____|  | _/ __ \
    |  |_> >___  ||   |  \ / __ \|  |_> >  |_\  ___/
    |   __// ____||___|  /(____  /  __/|____/\___  >
    |__|   \/          \/      \/|__|            \/[/bold cyan]  [bold white].js[/bold white]"""


def banner(mode: str):
    mode_styles = {
        "dev":   ("[bold green]development[/bold green]", "green"),
        "build": ("[bold magenta]production[/bold magenta]", "magenta"),
    }
    mode_label, accent = mode_styles.get(mode, (f"[bold]{mode}[/bold]", "white"))

    console.print()
    console.print(_LOGO)
    console.print()

    meta = Table.grid(padding=(0, 1))
    meta.add_column(justify="right", style="dim", min_width=10)
    meta.add_column()
    meta.add_row("version", f"[bold]{VERSION}[/bold]")
    meta.add_row("mode", mode_label)
    meta.add_row("python", f"[dim]stdlib + rich[/dim]")
    meta.add_row("frontend", f"[dim]react + esbuild[/dim]")

    panel = Panel(
        meta,
        border_style="dim cyan",
        box=box.ROUNDED,
        padding=(0, 2),
        width=52,
    )
    console.print(panel)


# ── Server box ───────────────────────────────────────────────────────────────
def server_box(mode: str, port: int, host: str = "localhost"):
    accent = "green" if mode == "dev" else "magenta"
    mode_label = f"[bold {accent}]{'development' if mode == 'dev' else 'production'}[/bold {accent}]"
    url = f"http://{host}:{port}"

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="dim", justify="right", min_width=10)
    grid.add_column()

    grid.add_row("status", f"[bold green]ready[/bold green]")
    grid.add_row("local", f"[bold underline cyan]{url}[/bold underline cyan]")
    if mode != "dev":
        grid.add_row("network", f"[dim]http://0.0.0.0:{port}[/dim]")
    grid.add_row("mode", mode_label)

    panel = Panel(
        grid,
        title=f"[bold white] {BRAND} [/bold white]",
        subtitle=f"[dim]press ctrl+c to stop[/dim]",
        title_align="left",
        subtitle_align="left",
        border_style=accent,
        box=box.DOUBLE_EDGE,
        padding=(1, 2),
        width=52,
    )
    console.print()
    console.print(panel)
    console.print()


# ── Shutdown ─────────────────────────────────────────────────────────────────
def stopped():
    console.print()
    console.print(f"   [dim]●[/dim]  [dim]Server stopped — goodbye[/dim]")
    console.print()


# ── Usage ────────────────────────────────────────────────────────────────────
def usage(commands: tuple):
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan")
    grid.add_column(style="dim")

    descriptions = {
        "dev":   "Start development server with hot reload",
        "build": "Build for production and serve",
    }
    for cmd in commands:
        grid.add_row(cmd, descriptions.get(cmd, ""))

    panel = Panel(
        grid,
        title=f"[bold white] {BRAND} [/bold white]",
        subtitle=f"[dim]v{VERSION}[/dim]",
        title_align="left",
        subtitle_align="right",
        border_style="dim",
        box=box.ROUNDED,
        padding=(1, 2),
        width=52,
    )

    console.print()
    console.print(f"   [bold]Usage:[/bold]  [cyan]python3 app.py[/cyan] [dim]<command>[/dim]")
    console.print()
    console.print(panel)
    console.print()
