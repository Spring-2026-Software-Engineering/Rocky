# Test Strategy and Automation

This folder centralizes isolated automated tests for both backend and frontend.

## Test Design (best-practice checklist)

- Keep tests isolated from production data by using an in-memory backend database.
- Use deterministic fixture data with both valid and invalid records.
- Validate API behavior for both success and failure paths.
- Use end-to-end browser tests for critical user-path smoke coverage.
- Run everything in CI on pushes and pull requests for fast feedback.

## Backend tests

Path: run-test/backend

- seed_data.json: mixed valid and invalid records.
- rocky-backend/seed_from_local_api.py: single seeding module used by runtime and tests.
- test_backend_validation.py:
  - verifies accepted data is inserted;
  - verifies invalid data is rejected;
  - verifies API endpoints return 400 for malformed payloads.

## Frontend tests

Path: run-test/frontend

- test_view_titles_chromedriver.py:
  - opens login preview (auth gate aware);
  - signs into mock session;
  - clicks each sidebar view;
  - asserts each view renders the correct page title.

## Local run commands

From repo root:

- Backend: python -m unittest discover -s run-test/backend -p "test_*.py"
- Frontend: python -m unittest discover -s run-test/frontend -p "test_*.py"
