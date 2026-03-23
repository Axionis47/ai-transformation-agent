# Regression Log

## Sprint 1 — Foundation + Contracts

**Date:** 2026-03-23
**Run command:** `pytest tests/ -q --tb=short`
**Result:** 52 passed, 0 failed

### Test files added
| File | Tests | Result |
|------|-------|--------|
| tests/test_schemas.py | 11 | PASSED |
| tests/test_config.py | 12 | PASSED |
| tests/test_run_manager.py | 13 | PASSED |
| tests/test_api.py | 16 | PASSED |

### Coverage
- core/schemas.py: Run, CompanyIntake, EvidenceItem, Opportunity (all tiers), UIHints, BudgetConfig, RunStatus
- core/config.py: load_config, freeze_config, env var overrides
- core/run_manager.py: create_run, get_run, update_intake, transition (valid + invalid)
- api/app.py + routes: health, POST /v1/runs, GET /v1/runs/{id}, PUT company-intake, GET /ui, GET /trace

### Regressions
None — Sprint 1 baseline established.

### How to test
```
cd /Users/sid47/Desktop/ai-transformation-agent
pytest tests/ -q --tb=short
```

Expected: 52 passed, 0 failed

---

## Sprint 4 -- Thought Engine (Reasoning Loop + MID)

**Date:** 2026-03-23
**Run command:** `pytest tests/ -q --tb=short`
**Result:** 177 passed, 0 failed

### Test files added
| File | Tests | Result |
|------|-------|--------|
| tests/test_thought_mid.py | 8 | PASSED |
| tests/test_thought_evidence.py | 6 | PASSED |
| tests/test_thought_assumptions.py | 5 | PASSED |
| tests/test_thought_loop.py | 8 | PASSED |
| tests/test_thought_api.py | 8 | PASSED |

### Coverage
- engines/thought/mid.py: assess_coverage, detect_gap, field keyword scoring, budget fallback
- engines/thought/evidence_acc.py: add, dedup by source_ref, higher score replaces, get_all sorted, source_types
- engines/thought/assumptions.py: extract_assumptions, open_questions for missing fields, source=grounding
- engines/thought/reasoning_loop.py: run_loop depth budget, confidence threshold stop, grounder called, RAG called, pause for user question, resume after answer, coverage_gaps
- api/routes/thought.py: POST /start (intake->assumptions, confirmed->reasoning), POST /assumptions/confirm, POST /answer, 404 and 409 error cases, budget state updated

### Regressions
None -- 142 Sprint 1-3 tests continue to pass.

### How to test
```
cd /Users/sid47/Desktop/ai-transformation-agent
python3 -m pytest tests/ -q --tb=short
```

Expected: 177 passed, 0 failed
