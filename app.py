#!/usr/bin/env python3
"""
pynapple js — entry point

Usage:
  python3 app.py dev      → unified :2000  (Node build-watch + Python server)
  python3 app.py build    → build → prod server :8000
"""

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



# ── Helpers ───────────────────────────────────────────────────────────────────
def banner(msg: str):
    width = len(msg) + 4
    print(f"\n┌{'─' * width}┐")
    print(f"│  {msg}  │")
    print(f"└{'─' * width}┘\n")


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)


# ── Python bootstrap ──────────────────────────────────────────────────────────
def ensure_venv():
    if VENV_PYTHON.exists() and VENV_PIP.exists():
        print("  ✓  Virtual environment found at .python/")
        return
    if VENV_DIR.exists():
        print("  ⚠  Stale virtual environment — rebuilding …")
        shutil.rmtree(VENV_DIR)
    print("  →  Creating virtual environment at .python/")
    run([sys.executable, "-m", "venv", str(VENV_DIR)])
    print("  ✓  Virtual environment created")


def ensure_py_deps():
    if not REQUIREMENTS.exists():
        print("  ⚠  requirements.txt not found — skipping")
        return
    print("  →  Installing Python dependencies …")
    run([str(VENV_PIP), "install", "--quiet", "--upgrade", "pip"],
        stdout=subprocess.DEVNULL)
    result = run(
        [str(VENV_PIP), "install", "--quiet", "-r", str(REQUIREMENTS)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  ✓  Python dependencies installed")
    else:
        print("  ✗  Python dependency install failed:\n")
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
        print(f"  ✗  Failed to import: {', '.join(failed)}")
        print("     Try deleting .python/ and re-running\n")
        sys.exit(1)
    print("  ✓  Python packages verified")


# ── Node.js bootstrap ─────────────────────────────────────────────────────────
def find_npm() -> str:
    npm = shutil.which("npm")
    if not npm:
        print("  ✗  npm not found — install Node.js from https://nodejs.org")
        sys.exit(1)
    return npm


def ensure_node_deps(npm: str):
    if not (ROOT / "package.json").exists():
        print("  ⚠  package.json not found — skipping")
        return
    print("  →  Syncing Node dependencies …")
    run([npm, "install", "--silent"], cwd=ROOT)
    print("  ✓  Node dependencies ready")


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
        print("\n  Stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    watch_proc.wait()
    server_proc.wait()


def launch_build(npm: str):
    print("  →  Building frontend …")
    result = subprocess.run([npm, "run", "build"], cwd=ROOT)
    if result.returncode != 0:
        print("  ✗  Build failed")
        sys.exit(1)
    server_script = ROOT / "core" / "serve" / "server.py"
    print("\n  Starting production server …\n")
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(server_script), "build"])


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    command = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if not command or command not in COMMANDS:
        print(f"\n  Usage: python3 app.py [{'|'.join(COMMANDS)}]\n")
        sys.exit(1)

    label = {
        "dev":   "pynapple js — Dev",
        "build": "pynapple js — Build",
    }[command]

    banner(label)

    print("[ 1 / 2 ]  Python environment")
    ensure_venv()
    ensure_py_deps()
    verify_imports()

    print("\n[ 2 / 2 ]  Node.js")
    npm = find_npm()
    ensure_node_deps(npm)
    print()
    if command == "dev":
        launch_dev(npm)
    else:
        launch_build(npm)


if __name__ == "__main__":
    main()
