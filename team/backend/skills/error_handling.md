# Skill: Error Handling

Implement error handling in engines and services.

## When to load

Load this skill when: adding error handling to a new engine, fixing an unhandled exception, or implementing retry logic for external calls.

---

## Steps

1. Understand the error categories for this system:
   - Budget exhausted: not an error, a typed result. Return a specific typed object (`BudgetExhausted`, `GroundingBudgetExhausted`). Never raise an exception for budget exhaustion.
   - External service failure (ChromaDB, Gemini API): catch at the service boundary, emit STAGE_FAILED trace, return a typed error result. Do not crash the engine.
   - Invalid input (schema validation): Pydantic raises `ValidationError` — let it propagate to FastAPI which converts it to 422. Do not swallow it.
   - Unrecoverable engine failure: raise `EngineError` (define this in `core/`) with a message and run_id. FastAPI catches it and returns 500.
2. For every external call in a service, wrap it:
   ```python
   try:
       result = external_call(...)
   except ExternalServiceError as e:
       trace.emit(run_id, EventType.STAGE_FAILED, {"error": str(e), "stage": "rag_retrieve"})
       return ServiceUnavailableResult(reason=str(e))
   ```
3. Engine-level error handling: if a service returns an error result (not an exception), the engine continues with reduced evidence and marks the coverage gap. It does not stop.
4. Define typed error/result objects in `core/schemas.py`:
   - `BudgetExhaustedResult(reason: str, budget_type: str)` for budget limits
   - `ServiceUnavailableResult(reason: str)` for external call failures
5. Emit `STAGE_FAILED` before returning any error result so the trace captures the failure.

---

## Input

- `core/schemas.py` (existing result types)
- `core/events.py` (STAGE_FAILED, BUDGET_VIOLATION_BLOCKED)
- `services/trace.py` (emit function)

## Output

- Typed error result objects in `core/schemas.py`
- Try/except blocks at all external call boundaries
- Trace events for all error paths

## Constraints

- Never use bare `except:` or `except Exception:` without re-raising or logging.
- Never crash an engine because one service call failed. Degrade gracefully.
- Budget exhaustion is not an error. It is an expected state. Handle it with a typed result, not an exception.
- All error paths emit a trace event. Silent failures are not acceptable.

## Commit cadence

- `feat(core): add typed error result models for budget exhaustion and service failures`
- `fix(rag): handle chromadb connection error gracefully with typed result`
