# Regression Log

## Sprint 4 Baseline — 2026-03-16

### Summary
- Total tests: 79
- All passing: yes
- Command: `python3 -m pytest tests/ -q --tb=short`

### Pipeline
- Stages: 7 (up from 4 in Sprint 3)
- New agents: SignalExtractor, MaturityScorer, UseCaseGenerator
- VictoryMatcher: deterministic, no model call

### New test files this sprint
- `tests/test_pipeline_e2e.py` — 3 tests, 7-stage dry-run end-to-end
- `tests/test_api_e2e.py` — 3 tests, Sprint 4 API response shape

### State fields verified in dry-run
- `company_data` — populated with `about_text`
- `signals` — has `signals` list and `signal_count > 0`
- `maturity` — has `composite_score`, `dimensions`, `composite_label`
- `rag_context` — non-empty list
- `victory_matches` — each entry has `match_tier` and `win_id`
- `use_cases` — at least 2, each has `tier` and `data_flow`
- `report` — all 5 sections present and > 50 chars

### Backward compatibility
- `state.analysis` populated with `maturity_score`, `maturity_label` for API consumers

### Fixture coverage
- `tests/fixtures/sample_company.json`
- `tests/fixtures/sample_signals.json`
- `tests/fixtures/sample_maturity.json`
- `tests/fixtures/sample_use_cases.json`
- `tests/fixtures/sample_report.json`
- `tests/fixtures/rag_seeds/victories.json`

### Victory match tiers (deterministic)
- `DIRECT_MATCH`
- `CALIBRATION_MATCH`
- `ADJACENT_MATCH`

### Use case tiers
- `LOW_HANGING_FRUIT`
- `MEDIUM_SOLUTION`
- `HARD_EXPERIMENT`

### Previous baseline
- Sprint 3: 73 tests, 4-stage pipeline
