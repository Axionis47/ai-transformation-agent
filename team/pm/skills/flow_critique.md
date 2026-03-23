# Skill: Flow Critique

Review the reasoning loop flow to find broken paths, missing transitions, or UX gaps.

## When to load

Load this skill when: a sprint delivers the thought engine or pitch synthesis, a QA agent reports unexpected behavior, or you are preparing the sprint review.

---

## Steps

1. Read the sprint plan for the sprint being reviewed.
2. Trace the happy path from API entry to final output:
   - `POST /v1/runs` creates run with status=CREATED
   - `PUT /v1/runs/{id}/company-intake` transitions to INTAKE
   - Thought engine loops: RAG query -> grounder query -> MID check -> user question (if needed) -> next loop
   - Pitch synthesis: evidence in -> 3-tier opportunities out
   - `GET /v1/runs/{id}/ui` returns UIHints with correct stage at every step
3. Walk each failure path:
   - Budget exhausted mid-reasoning: does the run continue with coverage_gap flagged?
   - User provides wrong input: does the API return a clear 422?
   - MID detects missing field: does the frontend receive an `agent_message` in UIHints?
   - Depth budget hit: does the engine stop and record what it found?
4. Check that evidence, abstraction, and confidence are never blended in the output. They must be separate fields in the API response.
5. Write a critique doc listing: what works, what is broken, what is missing.
6. For each broken or missing path, write a ticket.

---

## Input

- Sprint plan file for the sprint under review
- `core/schemas.py` (UIHints, Opportunity, EvidenceItem shapes)
- QA test results if available

## Output

- Written flow critique (inline in sprint review doc or as a separate note)
- Tickets for broken paths

## Constraints

- Do not speculate about implementation. If you need to check behavior, ask QA to run a dry-run.
- Every broken path gets a ticket. Nothing stays as a known issue without a ticket.
- The critique is for Sai's sprint review. Write it so Sai can understand the state in 5 minutes.

## Commit cadence

- `docs(review): add sprint N flow critique and gap tickets`
