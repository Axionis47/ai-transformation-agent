# Skill: API Integration

Connect the frontend to the backend API, including SSE streaming for real-time updates.

## When to load

Load this skill when: wiring a page to an API endpoint, implementing SSE for live reasoning progress, or fixing an API call that returns wrong data.

---

## Steps

1. Read `core/schemas.py` to understand what the API returns. Define matching TypeScript types in `frontend/lib/types.ts`.
2. All API calls go through `frontend/lib/api.ts`. Never call `fetch` directly in components or pages. The api client is the single integration point.
3. For REST calls:
   - `GET /v1/runs/{id}` — fetch current run state
   - `GET /v1/runs/{id}/ui` — fetch UIHints for current stage
   - `POST /v1/runs` — create a new run
   - `PUT /v1/runs/{id}/company-intake` — submit company info
4. For SSE (real-time reasoning progress):
   - Connect to `GET /v1/runs/{id}/stream` (when implemented in Sprint 4+).
   - Use the browser's `EventSource` API.
   - Parse each event as a `TraceEvent` and update the UI state.
   - Handle reconnection: if the SSE connection drops, reconnect with exponential backoff (max 3 retries).
   - Close the connection when the run reaches a terminal state (PUBLISHED or FAILED).
5. Error handling in api.ts:
   - 404: return null, component shows "run not found"
   - 422: return the validation error, component shows it on the relevant form field
   - 500: return a generic error, component shows "analysis failed" with the error message
   - Network error: treat as 500

---

## Input

- `core/schemas.py` (Python) translated to TypeScript types in `frontend/lib/types.ts`
- API base URL from environment variable `NEXT_PUBLIC_API_URL`

## Output

- `frontend/lib/api.ts` — API client with all endpoint functions
- `frontend/lib/types.ts` — TypeScript types matching backend schemas
- SSE hook in `frontend/hooks/useRunStream.ts` (if implementing SSE)

## Constraints

- Never call `fetch` directly in components. Always use `frontend/lib/api.ts`.
- API base URL must come from `NEXT_PUBLIC_API_URL` environment variable. Never hardcode.
- SSE connections must be closed on component unmount. No memory leaks.
- TypeScript types must exactly match the Pydantic schemas in `core/schemas.py`. If they diverge, the UI will show wrong data.

## Commit cadence

- `feat(api-client): add run creation and ui hints fetch functions`
- `feat(api-client): add sse stream hook for real-time reasoning updates`
