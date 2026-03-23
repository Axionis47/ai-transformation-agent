# Skill: Regression Check

Verify that nothing broke after a sprint delivers new code.

## When to load

Load this skill when: a sprint completes and you need to confirm no existing functionality regressed, a backend agent made changes to core modules, or PM asks for a sprint review verification.

---

## Steps

1. Run the full test suite: `pytest tests/ -q --tb=short`. Record the pass/fail count.
2. Compare to the previous sprint's pass count. If any previously passing test now fails, that is a regression. Do not proceed until it is investigated.
3. Run the test suite for each module that was changed this sprint, individually:
   ```
   pytest tests/test_schemas.py -q --tb=short
   pytest tests/test_config.py -q --tb=short
   pytest tests/test_run_manager.py -q --tb=short
   pytest tests/test_api.py -q --tb=short
   ```
   Check that each module's tests still pass.
4. If the sprint added a new engine or service, run its specific test file to confirm the new functionality works.
5. Check the trace output: if possible, run a quick API call and confirm trace events are being emitted to `logs/`.
6. Write a regression report with:
   - Total tests: N
   - Passing: N
   - Failing: N (list them)
   - New tests added this sprint: N
   - Any regressions: yes/no. If yes, list them and raise a ticket.
7. Post the regression report to the sprint review ticket as a comment.

---

## Input

- Current test suite in `tests/`
- Previous sprint's test results (from sprint review doc)

## Output

- Regression report posted to the sprint review ticket
- Tickets for any regressions found

## Constraints

- Never sign off on a sprint with open regressions. All must be fixed before sprint closes.
- If a test was deleted rather than fixed, that is a regression. Raise a ticket.
- Never use `-v` flag with pytest. Use `-q --tb=short`.
- Regression check runs after all sprint tickets are marked Done, before sprint closes.

## Commit cadence

- No commits needed for regression checks unless you add a new test to cover a gap found:
  - `test(regression): add coverage for run manager edge case found in sprint N review`
