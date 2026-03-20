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

## Sprint 8 Regression Check — 2026-03-19

### Tests
- Total: 231 passing, 0 failing
- Command: `python3 -m pytest tests/ -q --tb=short`
- New test: `tests/test_matching_layer.py::test_win001_scores_higher_with_pain_and_tech_signals`

### Matching Layer — New Scoring Dimensions (Sprint 8)
Three new scoring channels added to `orchestrator/matching_layer.py`:
- `_pain_point_score`: keyword overlap between company pain_point signals and victory problem_statement/solution_summary. Weight: 0.0-0.15.
- `_tech_stack_score`: token overlap between company tech_stack signals and victory tech_stack fields. Weight: 0.0-0.15.
- Broadened sector_bonus: now checks 6 signal types (pain_point, hiring_signal, intent_signal, industry_hint, process_signal, ops_signal) with fuzzy substring matching. Weight: 0.1 max.

### Integration Test Result — win-001 score lift
- Baseline (industry+maturity only): score=1.000, tier=DELIVERED
- Rich signals (+ pain_point "manual route planning" + tech_stack "BigQuery"): score=1.310, tier=DELIVERED
- Score delta: +0.310 (well above the 0.1 minimum threshold)
- win-001 stays DELIVERED in both cases; rich signals produce a measurably higher confidence match.

### Pipeline
- Dry-run: PASS (exit code 0)
- All 7 stages execute without errors in dry-run mode

### Eval Scores
- No eval run this sprint (quota blocker from Sprint 6 still applies)
- Baseline scores unchanged from Sprint 6 (0.0 quota-failure artifacts, not real scores)

### Test delta vs Sprint 6
- Sprint 6: 140 tests
- Sprint 8: 231 tests (+91 tests added in Sprints 7-8)

### Verdict: PASS
- All 231 tests pass
- Dry-run pipeline completes successfully
- No previously-passing tests broke
- New scoring dimensions verified to produce measurable score lift (delta >= 0.1)
