# Skill: Dry Run Verify

Verify the system runs end-to-end with mock data.

## When to load

Load this skill when: a sprint delivers a new pipeline stage, PM requests end-to-end verification, or you need to confirm the API is working before Sai tests it.

---

## Steps

1. Understand what "dry run" means for this system: all external calls (Gemini API, ChromaDB) are mocked. The system processes fixture data and returns structured output without spending real budget.
2. Start the API server locally:
   ```
   uvicorn api.app:app --reload --port 8000
   ```
3. Run the end-to-end sequence manually:
   - Create a run: `curl -X POST http://localhost:8000/v1/runs -H "Content-Type: application/json" -d '{"company_name": "Acme Logistics", "industry": "logistics"}'`
   - Capture the `run_id` from the response.
   - Check UI hints: `curl http://localhost:8000/v1/runs/{run_id}/ui`
   - Submit company intake: `curl -X PUT http://localhost:8000/v1/runs/{run_id}/company-intake -H "Content-Type: application/json" -d '{"company_name": "Acme Logistics", "industry": "logistics", "employee_count_band": "100-500"}'`
   - Verify health: `curl http://localhost:8000/health`
4. Verify each response:
   - Every response must match the Pydantic schema (no missing fields, correct types).
   - UI hints must match the current run status.
   - Trace events must appear in `logs/{run_id}.jsonl`.
5. After each sprint adds a new stage, add that stage to the dry run sequence above.
6. Write a dry run report:
   - Stages verified: list
   - Responses correct: yes/no per stage
   - Trace events emitted: yes/no
   - Any failures: list them and raise tickets

---

## Input

- Running API server (uvicorn)
- `core/schemas.py` (expected response shapes)

## Output

- Dry run report posted to the sprint ticket
- Tickets for any failures found

## Constraints

- Dry run never makes real Gemini API calls. If a stage requires Gemini and the mock is not in place, that stage cannot be dry-run verified yet.
- Dry run must work on a fresh checkout with no setup beyond `pip install -r requirements.txt`.
- The `logs/` directory must receive trace events during the dry run. If it is empty, trace is broken.
- Write the dry run sequence in the ticket output comment so Sai can repeat it himself.

## Commit cadence

No commits for dry run verification unless you are fixing a test fixture:
- `test(fixtures): update dry run fixture for sprint N api changes`
