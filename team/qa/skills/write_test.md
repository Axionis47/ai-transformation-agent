# Skill: Write Test

Create or update pytest test files in `tests/`.

## When to load

Load this skill when: a new backend module needs test coverage, a bug was fixed and needs a regression test, or AC requires test certification.

---

## Steps

1. Read `core/schemas.py` to understand the data shapes you are testing.
2. Read the module under test. Understand its function signatures, inputs, outputs, and error paths.
3. Write tests in the appropriate file:
   - `tests/test_schemas.py` — Pydantic model validation
   - `tests/test_config.py` — config loading and freeze
   - `tests/test_run_manager.py` — run state machine transitions
   - `tests/test_api.py` — FastAPI endpoint behavior (use TestClient)
   - `tests/test_rag.py` — RAG retrieval and budget enforcement
   - `tests/test_grounder.py` — grounder calls and budget tracking
   - `tests/test_thought_engine.py` — reasoning loop behavior
   - `tests/test_pitch_engine.py` — 3-tier opportunity generation
4. For each module, cover:
   - Happy path: valid input produces expected output with correct schema
   - Error paths: invalid input, missing required fields, budget exhaustion
   - Edge cases: empty results, max budget hit, all optional fields absent
   - State transitions (for run_manager): valid transitions succeed, invalid transitions raise
5. Use fixtures for shared setup. Define them in `tests/conftest.py`.
6. Mock external calls (Gemini API, ChromaDB) using `unittest.mock.patch`. Tests must never make real network calls.
7. Run tests before committing: `pytest tests/ -q --tb=short`. Fix all failures first.

---

## Input

- `core/schemas.py` (data shapes)
- The module under test
- Sprint plan (which behaviors are required)

## Output

- Test file in `tests/` with coverage for happy path, error paths, and edge cases
- Fixtures in `tests/conftest.py` if reusable setup is needed

## Constraints

- Tests never make real network calls. Mock everything external.
- Never use `-v` flag with pytest. Use `-q --tb=short`.
- Test files are under 200 lines. Split if larger.
- Each test function tests exactly one behavior. No multi-assertion tests that blend concerns.
- Tests do not modify source code. If you found a bug, write a failing test and raise a ticket.

## Commit cadence

- `test(run-manager): add state transition and budget init coverage`
- `test(rag): add budget exhaustion and min-score filter edge cases`
