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

- seed_data.json: mixed valid and invalid records for validation coverage.
- test_seed_data_shape.py:
  - checks the real backend seed data has one admin, two instructors, four users, and six courses;
  - verifies widgets are embedded per user.
- test_backend_validation.py:
  - verifies accepted data is inserted;
  - verifies invalid data is rejected;
  - verifies API endpoints return 400 for malformed payloads.
- test_user_settings.py:
  - verifies per-user settings are readable and writable;
  - verifies widgets stay isolated per user.
- test_course_api_history.py:
  - verifies API history records grouped and ungrouped usage;
  - verifies analytics and widgets endpoints remain reachable.

Run all test modules with:

- python run-test/test_all.py

## Frontend tests

Path: run-test/frontend

- test_preview_login_chromedriver.py:
  - opens login preview;
  - signs into a mock admin session;
  - confirms the dashboard loads.
- test_view_titles_chromedriver.py:
  - opens login preview (auth gate aware);
  - signs into mock session;
  - clicks each sidebar view;
  - asserts each view renders the correct page title.

## Local run commands

From repo root:

- All tests: python run-test/test_all.py
- Backend only: python -m unittest discover -s run-test/backend -p "test_*.py"
- Frontend only: python -m unittest discover -s run-test/frontend -p "test_*.py"
