# Rocky Interface (Frontend Developer Guide)

This README is for developers working in the SvelteKit frontend under `rocky-interface`.

## What this project owns

- UI rendering and user interaction.
- Route and frame navigation.
- Frontend API client calls.
- Proxying requests through SvelteKit server routes to the Flask backend.

The frontend does not directly own private data. The backend is the source of truth.

## Prerequisites

- Node.js 20+
- npm

## Local setup

Install dependencies:

```sh
npm install
```

Create env file:

1. Copy `.env.example` to `.env`
2. Set at least:
   - `PUBLIC_APP_ENV=development`
   - `PUBLIC_API_BASE_URL=http://127.0.0.1:5001`

## Run frontend locally

```sh
npm run dev
```

Optional open in browser:

```sh
npm run dev -- --open
```

## Build and preview

```sh
npm run build
npm run preview
```

## Backend integration expectations

- Frontend should call local proxy routes under `src/routes/api/backend/[...path]/+server.ts`.
- Proxy adds authenticated user headers for backend authorization checks.
- Do not add direct local JSON data reads for protected data.

## Key folders

- `src/lib/components`: reusable UI components.
- `src/lib/components/views`: frame-level views (dashboard, courses, users, analytics, etc.).
- `src/lib/api`: frontend API wrappers.
- `src/routes`: page routes and API proxy routes.
- `src/lib/stores`: app state stores.

## Role behavior to preserve

- Admin: can access all frames and manage users/analytics/courses.
- Non-admin: limited frames and course access based on backend-authorized data.

When changing UI behavior, keep backend-enforced permissions as the final authority.
