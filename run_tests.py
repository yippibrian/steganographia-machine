#!/usr/bin/env python3
"""Run the test suite with one command.

The first run creates a private .venv and installs only pytest and PyYAML in
that environment. It does not update the Mac's system Python or global pip.
The project itself is loaded directly from src/, so editable installation is
not needed.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
STAMP = VENV / ".steg-test-dependencies"
DEPENDENCIES = ("PyYAML>=6.0", "pytest>=8.0,<9")


def venv_python() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def dependency_fingerprint() -> str:
    digest = hashlib.sha256()
    digest.update("\n".join(DEPENDENCIES).encode())
    digest.update(f"{sys.version_info.major}.{sys.version_info.minor}".encode())
    return digest.hexdigest()


def run(command: list[str], env=None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True, env=env)


def ensure_environment() -> Path:
    python = venv_python()
    if not python.exists():
        print("Creating a private test environment in .venv ...", flush=True)
        venv.EnvBuilder(with_pip=True).create(VENV)

    fingerprint = dependency_fingerprint()
    installed = STAMP.read_text().strip() if STAMP.exists() else ""
    if installed != fingerprint:
        print("Installing pytest and PyYAML inside .venv ...", flush=True)
        run([str(python), "-m", "pip", "install", "--disable-pip-version-check", *DEPENDENCIES])
        STAMP.write_text(fingerprint + "\n")
    return python


def main() -> int:
    try:
        python = ensure_environment()
        env = os.environ.copy()
        src = str(ROOT / "src")
        env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        command = [str(python), "-m", "pytest", *sys.argv[1:]]
        return subprocess.run(command, cwd=ROOT, env=env).returncode
    except subprocess.CalledProcessError as exc:
        print(f"\nSetup failed with exit code {exc.returncode}.", file=sys.stderr)
        return exc.returncode
    except Exception as exc:
        print(f"\nCould not run tests: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
