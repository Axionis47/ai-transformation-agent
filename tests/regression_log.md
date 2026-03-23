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
