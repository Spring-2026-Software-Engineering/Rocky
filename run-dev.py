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
SEED_SCRIPT = BACKEND_DIR / "seed_from_backend.py"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rocky.run-dev")


def log(message: str) -> None:
    logger.info("[run-dev] %s", message)


def _python_can_run_backend(python_exe: Path | str) -> bool:
    probe = (
        "import flask, mongita, pymongo; "
        "assert hasattr(flask, 'Flask'); "
        "print('ok')"
    )
    try:
        result = subprocess.run(
            [str(python_exe), "-c", probe],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_python_executable(require_backend_deps: bool = False) -> str:
    backend_venv = REPO_ROOT / "rocky-backend" / ".venv" / "Scripts" / "python.exe"
    root_venv_windows = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    root_venv_unix = REPO_ROOT / ".venv" / "bin" / "python"

    candidates: list[Path | str] = []
    if backend_venv.exists():
        candidates.append(backend_venv)
    if root_venv_windows.exists():
        candidates.append(root_venv_windows)
    if root_venv_unix.exists():
        candidates.append(root_venv_unix)
    candidates.append(sys.executable)

    if not require_backend_deps:
        return str(candidates[0])

    for candidate in candidates:
        if _python_can_run_backend(candidate):
            return str(candidate)

    raise RuntimeError(
        "No Python interpreter with working backend dependencies was found. "
        "Install dependencies with: pip install -r rocky-backend/requirements.txt"
    )


def get_npm_executable() -> str:
    if os.name == "nt":
        return "npm.cmd"
    return "npm"


def _build_frontend_env(api_base_url: str | None = None) -> dict[str, str]:
    env = os.environ.copy()

    # Validate shared launch config up-front to fail fast with actionable messages.
    frontend_bind()
    allowed_hosts()

    if api_base_url is not None:
        env["PUBLIC_API_BASE_URL"] = api_base_url

    return env


def wait_for_backend(backend_url: str, timeout_seconds: int = 15) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(f"{backend_url}/health", timeout=2):
                return True
        except URLError:
            time.sleep(0.5)
    return False


def run_backend_only() -> int:
    python_exe = get_python_executable(require_backend_deps=True)
    resolved_backend_url = backend_url()
    log(f"Using Python interpreter: {python_exe}")
    log(f"Starting backend only on {resolved_backend_url}")
    return subprocess.call([python_exe, "main.py"], cwd=str(BACKEND_DIR), env=os.environ.copy())


def run_frontend_only() -> int:
    npm_exe = get_npm_executable()
    frontend_host, frontend_port = frontend_bind()
    log("Starting frontend only (backend API should be running separately).")
    env = _build_frontend_env()
    return subprocess.call(
        [npm_exe, "run", "dev", "--", "--host", frontend_host, "--port", frontend_port],
        cwd=str(FRONTEND_DIR),
        env=env,
    )


def run_both() -> int:
    python_exe = get_python_executable(require_backend_deps=True)
    npm_exe = get_npm_executable()
    resolved_backend_url = backend_url()
    frontend_host, frontend_port = frontend_bind()
    log(f"Using Python interpreter: {python_exe}")

    log("Seeding backend with fixture data from rocky-backend/seed-data...")
    subprocess.run([python_exe, str(SEED_SCRIPT)], check=True, cwd=str(REPO_ROOT))

    log(f"Launching backend API on {resolved_backend_url}")
    backend_process = subprocess.Popen([python_exe, "main.py"], cwd=str(BACKEND_DIR), env=os.environ.copy())

    try:
        if not wait_for_backend(resolved_backend_url):
            raise RuntimeError(f"Backend did not become ready on {resolved_backend_url}")

        log("Backend is ready. Starting frontend against backend API...")

        env = _build_frontend_env(api_base_url=resolved_backend_url)

        return subprocess.call(
            [npm_exe, "run", "dev", "--", "--host", frontend_host, "--port", frontend_port],
            cwd=str(FRONTEND_DIR),
            env=env,
        )
    finally:
        if backend_process.poll() is None:
            log("Stopping backend process...")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()


def main() -> int:
    load_project_env(REPO_ROOT, BACKEND_DIR, FRONTEND_DIR)

    parser = argparse.ArgumentParser(description="Cross-platform Rocky dev runner")
    parser.add_argument(
        "--mode",
        choices=["backend", "frontend", "both"],
        default="both",
        help="Which service mode to run",
    )
    args = parser.parse_args()

    try:
        if args.mode == "backend":
            return run_backend_only()
        if args.mode == "frontend":
            return run_frontend_only()
        return run_both()
    except KeyboardInterrupt:
        log("Interrupted by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
