# Root Dev Runner

Run from repository root with Python:

- Backend only:
  - python run-dev.py --mode backend
- Frontend only:
  - python run-dev.py --mode frontend
- Both together (recommended integration mode):
  - python run-dev.py --mode both

Notes:

- If your system uses `python3`, use `python3 run-dev.py --mode both`.

## What Mode both does

1. Seeds backend database and static content from rocky-backend/seed-data.
2. Starts backend server using `ROCKY_API_HOST` and `ROCKY_API_PORT`.
3. Starts frontend dev server using `ROCKY_WEB_HOST`, `ROCKY_WEB_PORT`, and `ROCKY_ALLOWED_HOSTS`.
4. Sets `PUBLIC_API_BASE_URL` for the frontend process to the backend URL derived from `ROCKY_API_HOST` and `ROCKY_API_PORT`.

This makes frontend talk to backend APIs as the single source of truth.
