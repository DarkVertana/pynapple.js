#!/usr/bin/env python3
"""
pynaple js — entry point

Usage:
  python3 app.py dev      → unified :2000  (Node build-watch + Python server)
  python3 app.py build    → build → prod server :8000
"""

import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent.resolve()
VENV_DIR     = ROOT / ".python"
REQUIREMENTS = ROOT / "requirements.txt"

if sys.platform == "win32":
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
    VENV_PIP    = VENV_DIR / "Scripts" / "pip.exe"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python"
    VENV_PIP    = VENV_DIR / "bin" / "pip"

COMMANDS = ("dev", "build")

# ── UI import ─────────────────────────────────────────────────────────────────
sys.path.insert(0, str(ROOT))
from core import ui


# ── Helpers ───────────────────────────────────────────────────────────────────
def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)


# ── Python bootstrap ──────────────────────────────────────────────────────────
def ensure_venv():
    if VENV_PYTHON.exists() and VENV_PIP.exists():
        ui.ok("Virtual environment found")
        return
    if VENV_DIR.exists():
        ui.warn("Stale virtual environment — rebuilding")
        shutil.rmtree(VENV_DIR)
    ui.info("Creating virtual environment")
    run([sys.executable, "-m", "venv", str(VENV_DIR)])
    ui.ok("Virtual environment created")


def ensure_py_deps():
    if not REQUIREMENTS.exists():
        ui.warn("requirements.txt not found — skipping")
        return
    ui.info("Installing Python dependencies")
    subprocess.run(
        [str(VENV_PIP), "install", "--quiet", "--upgrade", "pip"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    result = subprocess.run(
        [str(VENV_PIP), "install", "--quiet", "-r", str(REQUIREMENTS)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        ui.ok("Python dependencies installed")
    else:
        ui.fail("Python dependency install failed")
        print(result.stderr)
        sys.exit(1)


def verify_imports():
    packages = ["dotenv"]
    failed = [
        pkg for pkg in packages
        if subprocess.run(
            [str(VENV_PYTHON), "-c", f"import {pkg}"],
            capture_output=True,
        ).returncode != 0
    ]
    if failed:
        ui.fail(f"Failed to import: {', '.join(failed)}")
        print(f"     Try deleting .python/ and re-running\n")
        sys.exit(1)
    ui.ok("Python packages verified")


# ── Node.js bootstrap ─────────────────────────────────────────────────────────
def find_npm() -> str:
    npm = shutil.which("npm")
    if not npm:
        ui.fail("npm not found — install Node.js from https://nodejs.org")
        sys.exit(1)
    return npm


def ensure_node_deps(npm: str):
    if not (ROOT / "package.json").exists():
        ui.warn("package.json not found — skipping")
        return
    ui.info("Syncing Node dependencies")
    run([npm, "install", "--silent"], cwd=ROOT)
    ui.ok("Node dependencies ready")


# ── Launch targets ────────────────────────────────────────────────────────────
def launch_dev(npm: str):
    server_script = ROOT / "core" / "serve" / "server.py"

    # Node watcher: esbuild + tailwindcss (no HTTP)
    watch_proc = subprocess.Popen([npm, "run", "dev"], cwd=ROOT)

    # Python unified server: frontend + API on single port :2000
    server_proc = subprocess.Popen(
        [str(VENV_PYTHON), str(server_script), "dev"]
    )

    def shutdown(sig, frame):
        watch_proc.terminate()
        server_proc.terminate()
        ui.stopped()
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    watch_proc.wait()
    server_proc.wait()


def launch_build(npm: str):
    ui.info("Building frontend")
    result = subprocess.run([npm, "run", "build"], cwd=ROOT)
    if result.returncode != 0:
        ui.fail("Build failed")
        sys.exit(1)
    server_script = ROOT / "core" / "serve" / "server.py"
    ui.info("Starting production server")
    print()
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(server_script), "build"])


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    command = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if not command or command not in COMMANDS:
        ui.usage(COMMANDS)
        sys.exit(1)

    ui.banner(command)

    ui.step(1, 2, "Python environment")
    ensure_venv()
    ensure_py_deps()
    verify_imports()

    ui.step(2, 2, "Node.js")
    npm = find_npm()
    ensure_node_deps(npm)

    # Print final step timing
    if ui._step_start is not None:
        import time
        elapsed = time.time() - ui._step_start
        ui.console.print(f"   [dim]done in {elapsed:.1f}s[/dim]")
        ui._step_start = None

    if command == "dev":
        launch_dev(npm)
    else:
        launch_build(npm)


if __name__ == "__main__":
    main()
