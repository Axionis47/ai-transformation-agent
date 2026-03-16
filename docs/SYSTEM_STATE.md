# System State — Sprint 5

> Sai reads this at the start of every sprint. 5-minute overview of what exists.

## Current Sprint: 5 (Eval Framework + Tool Registry + Trace Panel)

---

### What Works (Sai Can Test)

| Feature | Status | How to Test |
|---------|--------|-------------|
| Full pipeline dry-run (7 stages) | Working | `python orchestrator/pipeline.py --dry-run` |
| POST /v1/analyze endpoint | Working | `curl -X POST http://localhost:8000/v1/analyze -H "Content-Type: application/json" -d '{"url":"https://example.com"}'` |
| GET /v1/trace/{run_id} endpoint | Working | `curl http://localhost:8000/v1/trace/<run_id>` (run_id returned from /analyze) |
| GET /health endpoint | Working | `curl http://localhost:8000/health` |
| Maturity scoring (0-5) with dimension breakdown | Working | Run pipeline, check `analysis.maturity_score` in response |
| Victory matching with gap analysis | Working | Check `use_cases[].gap_analysis` in pipeline output |
| Use case generation with tier classification | Working | Check `use_cases[].tier` field (DIRECT/CALIBRATION/ADJACENT) |
| 5-section report rendering in UI | Working | Run frontend, submit URL, report renders below the form |
| UseCaseCard with maturity-tier coloring | Working | Green = DIRECT, amber = CALIBRATION, blue = ADJACENT |
| TracePanel (collapsible pipeline trace) | Working | Click "Show Pipeline Trace" below report |
| Storybook stories (UseCaseCard, TracePanel) | Working | `cd frontend && npm run storybook` |
| Tool registry (WebsiteScraperTool) | Working | Scraper stage uses registry.get("website_scraper") |
| Stage I/O logging to JSONL | Working | Logs appear in `logs/runs/{run_id}.jsonl` after a run |
| Eval rubrics (3 dimensions) | Defined | See `evals/rubrics/` — requires ANTHROPIC_API_KEY to run |
| 117 tests passing | Green | `pytest tests/ -q --tb=short` |

---

### How to Start the System

```bash
# Backend
pip install -r requirements.txt
uvicorn infra.app:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
# → http://localhost:3000

# Dry-run pipeline (zero API calls)
python orchestrator/pipeline.py --dry-run

# Run test suite
pytest tests/ -q --tb=short
```

---

### What Is Not Yet Built (Sprint 6 Items)

| Feature | Notes |
|---------|-------|
| Second pipeline tool (e.g. job board scraper) | Tool registry is ready to accept it |
| Real eval scores | Requires ANTHROPIC_API_KEY — placeholders are 0.0 in baselines.json |
| Authentication / API key gating | Deferred per ADR-002 |
| Production deploy to Cloud Run | Requires Sai to approve deploy ticket |
| Parallel report section writes | 5 sections currently sequential; parallel would cut ~30s |
| Product/solutions page scraping | Scraper fetches /about and /careers only — product pages deferred |
| Low-signal graceful degradation UI warning | Pipeline continues with reduced confidence but UI has no warning banner yet |

---

### Eval Scores — Sprint 5

Real eval scoring requires `ANTHROPIC_API_KEY` set in the environment.
Current baselines.json contains placeholder 0.0 values.

| Dimension | Sprint 5 Score | Threshold | Status |
|-----------|---------------|-----------|--------|
| tier_classification | 0.0 (placeholder) | >= 3.8 | Unscored |
| evidence_grounding | 0.0 (placeholder) | >= 3.8 | Unscored |
| roi_basis | 0.0 (placeholder) | >= 3.8 | Unscored |

To run real evals: `ANTHROPIC_API_KEY=<key> python evals/ci_eval.py`

---

### Test Progression

| Sprint | Test Count | Delta |
|--------|------------|-------|
| Sprint 4 | 79 | baseline |
| Sprint 5 | 117 | +38 |

Zero regressions. All 117 tests pass.

---

### Cost Per Run

| Mode | Cost |
|------|------|
| Dry-run (fixtures only) | $0.00 |
| Live pipeline (Vertex AI) | ~$0.011 |
| Live pipeline + eval judge | ~$0.05 |
| Hard limit (budget_config.yaml) | $0.50 |

---

### Decisions Locked

| ADR | Decision |
|-----|----------|
| ADR-001 | Infrastructure: Cloud Run + Vertex AI + ChromaDB |
| ADR-002 | No auth for MVP — defer |
| ADR-003 | ChromaDB in-container as vector store |
| ADR-004 | Vertex primary, Ollama fallback, Anthropic evals-only |
| ADR-005 | Secrets via GCP Secret Manager |
| ADR-006 | Analysis Specification v1.0 (5-dimension maturity scoring) |
| ADR-007 | Victory data schema and RAG seed strategy |
| ADR-008 | Tool registry as orchestrator-level abstraction |

---

### Sprint 5 Files Added

```
orchestrator/tool_registry.py     ← Tool ABC + ToolRegistry singleton
orchestrator/stage_io.py          ← per-stage I/O summary builders
tools/__init__.py
tools/website_scraper.py          ← WebsiteScraperTool wrapping ScraperAgent
evals/judge_client.py             ← JudgeClient → Anthropic scoring
evals/ci_eval.py                  ← eval runner against 5 test companies
evals/test_companies.json
evals/baselines.json
evals/rubrics/tier_classification.yaml
evals/rubrics/evidence_grounding.yaml
evals/rubrics/roi_basis.yaml
frontend/components/TracePanel.tsx
frontend/components/TraceStageRow.tsx
frontend/stories/TracePanel.stories.tsx
tests/fixtures/rag_seeds/README.md
docs/decisions/ADR-008.md
docs/specs/sprint5_plan.md
docs/specs/sprint5_tickets.md
```

---

### Blockers

None. No Tier 2 or Tier 3 conditions active.

---

### Next Sprint Goals (Sprint 6)

1. Run real eval scores — establish first scored baseline
2. Add product/solutions page to scraper (fix signal starvation)
3. Low-signal degradation warning in UI
4. Second pipeline tool registration (job board or news source)
5. Parallel report section writes (close 90s SLA gap)
6. Production deploy ticket (Sai approval required)
