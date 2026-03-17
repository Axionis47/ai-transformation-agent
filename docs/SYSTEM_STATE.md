# System State

What works, what doesn't, and how to test it. Updated 2026-03-17.

## Current Sprint

Sprint 7 - Documentation. No code changes this sprint.

---

## What Works (You Can Test These)

| Feature | Status | How to Test |
|---------|--------|-------------|
| POST /v1/analyze endpoint | Working | `curl -X POST http://localhost:8000/v1/analyze -H "Content-Type: application/json" -d '{"url":"https://example.com"}'` |
| GET /v1/trace/{run_id} | Working | `curl http://localhost:8000/v1/trace/<run_id>` (run_id from /analyze response) |
| GET /health | Working | `curl http://localhost:8000/health` - returns status, version, model_provider, pipeline |
| Full pipeline dry-run (7 stages) | Working | `python3 orchestrator/pipeline.py --dry-run --url https://example.com` |
| Maturity scoring (0-5, dimension breakdown) | Working | Run pipeline, check `analysis.maturity_score` in response |
| Victory matching with gap analysis | Working | Check `use_cases[].gap_analysis` in pipeline output |
| Use case generation with tier classification | Working | Check `use_cases[].tier` (DIRECT / CALIBRATION / ADJACENT) |
| 5-section report rendering in UI | Working | Submit URL in frontend, report renders at /analysis/[runId] |
| UseCaseCard with maturity-tier coloring | Working | Green = DIRECT, amber = CALIBRATION, blue = ADJACENT |
| TracePanel (collapsible pipeline trace) | Working | Click "Show Pipeline Trace" below report |
| Section navigation bar (sticky) | Working | Visible when scrolling report results page |
| Home link in header | Working | Header logo link returns to / from any page |
| Tool registry (WebsiteScraperTool) | Working | Scraper stage uses `registry.get("website_scraper")` |
| Stage I/O logging to JSONL | Working | Logs appear in `logs/runs/{run_id}.jsonl` after a run |
| Parallel report section writes | Working | Stage 7 uses ThreadPoolExecutor(max_workers=3); per-section failure isolated |
| Extended scraper - /about /careers /products /solutions /platform | Working | pages_fetched field in API response lists which pages returned content |
| pages_fetched and signal_count in API response | Working | Check JSON from POST /v1/analyze |
| Dockerfile at repo root | Ready to build | `docker build -t ai-transform-agent .` |
| Cloud Run deploy target | Implemented | `infra/deploy_target.py` wraps gcloud - requires GCP credentials to execute |
| 140 tests passing | Green | `python3 -m pytest tests/ -q --tb=short` |
| CI/CD on GitHub Actions | Configured | CI on PRs to main; CD triggers after CI passes |

---

## How to Start

### Backend

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

The entry point is `app.py` at the repo root. Not `infra/app.py`.

### Frontend

```bash
cd frontend && npm install && npm run dev
# Opens http://localhost:3000
```

### Dry Run (no API calls, uses fixtures)

```bash
python3 orchestrator/pipeline.py --dry-run --url https://example.com
```

### Run Tests

```bash
python3 -m pytest tests/ -q --tb=short
```

140 tests, all passing. Takes about 33 seconds locally.

### Docker

```bash
docker build -t ai-transform-agent .
docker run -p 8080:8080 --env-file .env ai-transform-agent
```

Dockerfile uses `uvicorn app:app` on port 8080.

---

## Deploy

CD workflow (`.github/workflows/cd.yml`) deploys to Cloud Run automatically after CI passes on `main`.

Manual deploy:
```bash
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/ai-transform-agent
gcloud run deploy ai-transform-agent \
  --image gcr.io/$GCP_PROJECT_ID/ai-transform-agent \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

Live URL: not yet deployed. Requires Sai to run from a GCP-authenticated shell or CI secrets to be set.

---

## What Is Not Built Yet

| Feature | Notes |
|---------|-------|
| Live Cloud Run URL | Dockerfile and deploy target done; live deploy requires GCP credentials |
| LinkedInJobScraper (second tool) | Cut from Sprint 6; no demo value yet |
| Low-signal warning banner in UI | signal_count field exists in API; frontend banner not built |
| Authentication / API key gating | Deferred per ADR-002 |
| E2E timing validation on live URL | Can't measure until Cloud Run is deployed |

---

## Eval Scores

From `evals/baselines.json`. Sprint 6 scores are real - judge ran against `anthropic.AnthropicVertex`.

| Dimension | Sprint 6 Average | Threshold | Status |
|-----------|-----------------|-----------|--------|
| tier_classification | 3.67 | >= 3.8 | Below threshold |
| evidence_grounding | 3.20 | >= 3.8 | Below threshold |
| roi_basis | 3.07 | >= 3.8 | Below threshold |

All three dimensions are below the 3.8 threshold. Prompt engineering iteration is needed in Sprint 7 or Sprint 8 to close this gap.

Sprint 5 scores were 0.0 (ANTHROPIC_API_KEY not set - placeholder run). Sprint 6 was the first real scored eval.

---

## Test Count

| Sprint | Count | Delta |
|--------|-------|-------|
| Sprint 4 | 79 | baseline |
| Sprint 5 | 117 | +38 |
| Sprint 6 | 140 | +23 |

Test files: 20 files in `tests/`. Run command: `python3 -m pytest tests/ -q --tb=short`.

---

## Cost Per Run

| Mode | Cost |
|------|------|
| Dry-run (fixtures only) | $0.00 |
| Live pipeline (Vertex AI) | ~$0.011 |
| Live pipeline + eval judge | ~$0.05 |
| Hard limit (ops/budget_config.yaml) | $0.50 |

---

## Decisions Locked

| ADR | What Was Decided |
|-----|-----------------|
| ADR-001 | Infrastructure: Cloud Run + Vertex AI + ChromaDB |
| ADR-002 | No auth for MVP - deferred |
| ADR-003 | ChromaDB in-container as vector store |
| ADR-004 | Vertex primary, Ollama fallback, Anthropic evals-only |
| ADR-005 | Secrets via GCP Secret Manager |
| ADR-006 | Analysis Specification v1.0 - 5-dimension maturity scoring |
| ADR-007 | Victory data schema and RAG seed strategy |
| ADR-008 | Tool registry as orchestrator-level abstraction |
| ADR-009 | Parallel report section generation via ThreadPoolExecutor |
| ADR-010 | Cloud Run as production deploy target with zero-secrets-in-image policy |

---

## Known Issues

| Issue | Detail |
|-------|--------|
| Eval scores below threshold | All 3 dimensions below 3.8. Sprint 6 was first real run; scores need improvement via prompt iteration |
| Old docs referenced wrong startup command | Previous SYSTEM_STATE.md said `uvicorn infra.app:app`. Correct command is `uvicorn app:app`. The entry point is `app.py` at the repo root, not inside `infra/` |
| `evals/ci_eval.py` still writes to `sprint_6` key | The `_SPRINT` constant is hardcoded to `"sprint_6"` - needs a bump to `sprint_7` before next eval run |
| Stale `page 2.tsx` in repo | `frontend/app/page 2.tsx` exists as an untracked file - likely a copy artifact, not used |
| No live deploy URL | Demo requires live URL; Cloud Run deploy has not been executed yet |
