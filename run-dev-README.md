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

1. Seeds backend database with fixture data from rocky-interface/static/local-api.
2. Starts backend server on port 5001.
3. Starts frontend dev server on port 5000 with:
   - PUBLIC_USE_LOCAL_API=false
   - PUBLIC_API_BASE_URL=http://127.0.0.1:5001

This makes frontend talk to backend APIs instead of local-api files.
