from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from run_env import (
    allowed_hosts,
    backend_url,
    frontend_bind,
    load_project_env,
)

REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "rocky-backend"
FRONTEND_DIR = REPO_ROOT / "rocky-interface"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rocky.run-production")


def log(message: str) -> None:
    logger.info("[run-production] %s", message)


def get_python_executable() -> str:
    backend_venv = REPO_ROOT / "rocky-backend" / ".venv" / "Scripts" / "python.exe"
    root_venv_windows = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    root_venv_unix = REPO_ROOT / ".venv" / "bin" / "python"

    for candidate in (backend_venv, root_venv_windows, root_venv_unix):
        if candidate.exists():
            return str(candidate)

    return sys.executable


def get_npm_executable() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def wait_for_backend(backend_url: str, timeout_seconds: int = 30) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(f"{backend_url}/health", timeout=2):
                return True
        except URLError:
            time.sleep(0.5)
    return False


def build_frontend(npm_exe: str) -> None:
    log("Installing frontend dependencies...")
    subprocess.run([npm_exe, "ci"], cwd=str(FRONTEND_DIR), check=True)

    log("Building frontend production bundle...")
    env = os.environ.copy()
    subprocess.run([npm_exe, "run", "build"], cwd=str(FRONTEND_DIR), env=env, check=True)


def run_backend_and_preview() -> int:
    python_exe = get_python_executable()
    npm_exe = get_npm_executable()
    resolved_backend_url = backend_url()
    frontend_host, frontend_port = frontend_bind()
    allowed_hosts()

    if not os.getenv("ROCKY_MONGODB_URI"):
        raise RuntimeError("ROCKY_MONGODB_URI must be set for production mode.")

    build_frontend(npm_exe)

    backend_env = os.environ.copy()

    log("Launching backend API in production mode...")
    backend_process = subprocess.Popen([python_exe, "main.py"], cwd=str(BACKEND_DIR), env=backend_env)

    try:
        if not wait_for_backend(resolved_backend_url):
            raise RuntimeError("Backend did not become healthy in time.")

        log("Backend is healthy. Launching frontend preview server...")
        frontend_env = os.environ.copy()

        return subprocess.call(
            [npm_exe, "run", "preview", "--", "--host", frontend_host, "--port", frontend_port],
            cwd=str(FRONTEND_DIR),
            env=frontend_env,
        )
    finally:
        if backend_process.poll() is None:
            log("Stopping backend process...")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()


def run_backend_only() -> int:
    python_exe = get_python_executable()
    resolved_backend_url = backend_url()
    if not os.getenv("ROCKY_MONGODB_URI"):
        raise RuntimeError("ROCKY_MONGODB_URI must be set for production mode.")

    backend_env = os.environ.copy()

    log(f"Starting backend production service only on {resolved_backend_url}...")
    return subprocess.call([python_exe, "main.py"], cwd=str(BACKEND_DIR), env=backend_env)


def main() -> int:
    load_project_env(REPO_ROOT, BACKEND_DIR, FRONTEND_DIR)

    # Fail fast for required shared launch config.
    backend_url()
    frontend_bind()
    allowed_hosts()

    parser = argparse.ArgumentParser(description="Rocky production runner")
    parser.add_argument(
        "--mode",
        choices=["backend", "both"],
        default="both",
        help="Run backend only or backend plus frontend preview",
    )
    args = parser.parse_args()

    try:
        if args.mode == "backend":
            return run_backend_only()
        return run_backend_and_preview()
    except KeyboardInterrupt:
        log("Interrupted by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
