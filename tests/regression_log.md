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

## Sprint 6 Baseline — 2026-03-16

### Summary
- Total tests: 140
- All passing: yes
- Command: `PYTHONPATH=/path/to/repo python3 -m pytest tests/ -q --tb=short`

### Eval Run — claude-opus-4-6 via Vertex AI
- Status: BLOCKED — HTTP 429 quota-exhausted on all scoring calls
- Region: us-east5 (only region where model exists in this project)
- All 5 test companies: scores are 0.0 quota-failure artifacts
- Averages: tier_classification=0.0, evidence_grounding=0.0, roi_basis=0.0
- These are NOT real quality scores — they are failure placeholders

### Blocker for Sai
The GCP project `plotpointe` has exhausted the per-minute token quota
for `anthropic-claude-opus-4-6` on Vertex AI. To get real eval scores:
1. Submit a quota increase request at:
   https://cloud.google.com/vertex-ai/docs/generative-ai/quotas-genai
2. Or add a real ANTHROPIC_API_KEY to `.env` and switch judge_client.py
   to use the direct Anthropic API (requires architecture change).

### Dry-run pipeline — confirmed working
- Pipeline produces real use_cases and maturity data from fixtures
- Example: CargoLogik returns 3 use cases, maturity composite_score=2.0
- All 5 pipeline stages execute without errors in dry-run mode

### Test delta vs Sprint 4
- Sprint 4: 79 tests
- Sprint 6: 140 tests (+61 tests added in Sprints 5-6)

### No regressions
- All 140 tests pass
- No previously-passing tests broke
