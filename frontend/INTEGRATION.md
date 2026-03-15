# Integration Notes (Prototype)

This prototype is intentionally standalone, but designed to be easy to integrate with JSO dashboards later.

## Current architecture

- Frontend sends requests to Next.js API proxy endpoints:
  - `POST /api/search` forwards multipart payload to backend `/search`
  - `GET /api/health` forwards to backend `/health`
- Browser never directly calls backend URL, reducing CORS and cross-origin complexity.

## Why this is integration-friendly

- UI/state layers are separated:
  - `components/` for presentation
  - `store/searchStore.ts` for search actions and state
- Backend target URL is centralized in `lib/backend.ts` via `NEXT_PUBLIC_BACKEND_URL`.
- Form payload fields exactly match backend contract:
  - `query`
  - `resume`
  - repeated `job_search_intent`
  - repeated `location_preferences`

## Future integration options

1. Route-level embed:
   - Host this Next.js app as a route in the JSO dashboard shell.
2. Module embed:
   - Move `components/` and `store/` into an existing dashboard frontend package.
3. Gateway integration:
   - Keep proxy routes and put auth/session forwarding there when needed.

## Deployment baseline

- Platform: Vercel
- Required env var:
  - `NEXT_PUBLIC_BACKEND_URL`

