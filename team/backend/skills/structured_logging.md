# Skill: Structured Logging

Implement trace events via `services/trace.py`.

## When to load

Load this skill when: adding trace events to a new engine or service, adding a new EventType, or fixing missing trace coverage.

---

## Steps

1. Read `services/trace.py` — understand `emit(run_id, event_type, payload)`. This is the only logging function. Never use `print()` or Python's `logging` module in engine or service code.
2. Read `core/events.py` — all event types are defined here. If you need a new event type, add it to `EventType` in `core/events.py` first.
3. Add trace calls in your engine or service at these points:
   - Before any external call (RAG query, grounding call, model call): emit a "requested" event with the input parameters.
   - After any external call: emit a "completed" event with result metadata (count, score, latency if measurable).
   - At every major decision point: loop started, gap detected, budget checked, stop condition triggered.
   - On error: emit a STAGE_FAILED or BUDGET_VIOLATION_BLOCKED event with error details.
4. Payload format: keep payloads flat and specific. Good: `{"query": "...", "results_count": 5, "min_score": 0.3}`. Bad: `{"data": <entire response object>}`.
5. Never log PII or secrets in trace payloads.

---

## Input

- `services/trace.py` (emit function)
- `core/events.py` (EventType enum)

## Output

- Trace calls at all major steps in your engine/service
- New EventType entries in `core/events.py` if needed

## Constraints

- Every external call gets a before/after trace pair. No silent calls.
- Payloads are flat dicts. No nested objects.
- Never log raw model responses — log metadata (token count, latency, result count).
- `trace.emit()` must never raise. Wrap it in a try/except if there is any risk.

## Commit cadence

Trace calls are part of the engine/service commit. Do not commit trace calls separately unless you are only fixing missing coverage:
- `fix(trace): add missing trace events to grounder service`
