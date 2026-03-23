# Skill: API Endpoint

Create or modify a FastAPI endpoint in `api/routes/`.

## When to load

Load this skill when: adding a new route, modifying an existing endpoint's request or response shape, or fixing an API behavior bug.

---

## Steps

1. Read `core/schemas.py` — all request and response bodies are Pydantic models defined here. Use them. Never define inline schemas in route files.
2. Read the existing routes in `api/routes/` to understand current patterns before adding a new one.
3. Check `api/app.py` to see which routers are registered and what prefix they use.
4. Write the endpoint:
   - Use FastAPI dependency injection for shared state (run_manager, config, etc.).
   - All business logic lives in `core/run_manager.py` or the relevant service/engine. Route handlers are thin — they validate input, call the logic layer, return the response.
   - Return typed Pydantic models. Never return raw dicts.
   - Raise `HTTPException` with specific status codes for error paths: 404 for not found, 422 for invalid input, 500 for unrecoverable engine errors.
   - If the endpoint triggers state transitions, use `core/run_manager.transition()`. Never mutate run state directly in routes.
5. If adding a new route file, register the router in `api/app.py` with the correct prefix.
6. Document the endpoint in `SPRINT_N_PLAN.md` if it's new — PM needs to know about it.

---

## Input

- `core/schemas.py` (request/response types)
- `core/run_manager.py` (run state transitions)
- Existing route files for pattern reference

## Output

- New or updated route file in `api/routes/`
- Updated `api/app.py` if a new router was added

## Constraints

- Routes are thin. No business logic in route handlers.
- All responses are typed Pydantic models. No raw dicts.
- State transitions only via `core/run_manager.transition()`.
- Every new endpoint has a corresponding test in `tests/test_api.py` (QA writes the test, but you must tell them what to test in the ticket output comment).
- SSE endpoints for real-time updates: use `fastapi.responses.StreamingResponse` with proper event format.

## Commit cadence

- `feat(api): add POST /v1/runs endpoint with config snapshot`
- `feat(api): add GET /v1/runs/{id}/ui backend-driven hints endpoint`
- `fix(api): return 404 when run_id not found instead of 500`
