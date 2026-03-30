from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "rocky-backend"
FRONTEND_DIR = REPO_ROOT / "rocky-interface"
SEED_SCRIPT = BACKEND_DIR / "seed_from_local_api.py"
BACKEND_URL = "http://127.0.0.1:5001"


def log(message: str) -> None:
    print(f"[run-dev] {message}", flush=True)


def _python_can_run_backend(python_exe: Path | str) -> bool:
    probe = (
        "import flask, mongita; "
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


def wait_for_backend(timeout_seconds: int = 15) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(f"{BACKEND_URL}/users", timeout=2):
                return True
        except URLError:
            time.sleep(0.5)
    return False


def run_backend_only() -> int:
    python_exe = get_python_executable(require_backend_deps=True)
    log(f"Using Python interpreter: {python_exe}")
    log(f"Starting backend only on {BACKEND_URL}")
    return subprocess.call([python_exe, "main.py"], cwd=str(BACKEND_DIR))


def run_frontend_only() -> int:
    npm_exe = get_npm_executable()
    log("Starting frontend only in local-api mode (from rocky-interface/.env).")
    return subprocess.call(
        [npm_exe, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5000"],
        cwd=str(FRONTEND_DIR),
    )


def run_both() -> int:
    python_exe = get_python_executable(require_backend_deps=True)
    npm_exe = get_npm_executable()
    log(f"Using Python interpreter: {python_exe}")

    log("Seeding backend with fixture data from rocky-interface/static/local-api...")
    subprocess.run([python_exe, str(SEED_SCRIPT)], check=True, cwd=str(REPO_ROOT))

    log(f"Launching backend API on {BACKEND_URL}")
    backend_process = subprocess.Popen([python_exe, "main.py"], cwd=str(BACKEND_DIR))

    try:
        if not wait_for_backend():
            raise RuntimeError(f"Backend did not become ready on {BACKEND_URL}")

        log("Backend is ready. Starting frontend against backend API...")

        env = os.environ.copy()
        env["PUBLIC_APP_ENV"] = "development"
        env["PUBLIC_API_BASE_URL"] = BACKEND_URL
        env["PUBLIC_USE_LOCAL_API"] = "false"
        env["PUBLIC_ENABLE_DBTEST"] = "true"

        return subprocess.call(
            [npm_exe, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5000"],
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
