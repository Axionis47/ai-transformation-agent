# System State -- Sprint 8

> Sai reads this at the start of every sprint. 5-minute overview of what exists.

## Current Sprint: 8 (Three-Tier Matching Architecture)

---

### What Works (Sai Can Test)

| Feature | Status | How to Test |
|---------|--------|-------------|
| Full pipeline dry-run (7 stages) | Working | `python orchestrator/pipeline.py --dry-run` |
| POST /v1/analyze endpoint | Working | `curl -X POST http://localhost:8000/v1/analyze -H "Content-Type: application/json" -d '{"url":"https://example.com"}'` |
| GET /v1/trace/{run_id} endpoint | Working | `curl http://localhost:8000/v1/trace/<run_id>` (run_id returned from /analyze) |
| GET /health endpoint | Working | `curl http://localhost:8000/health` — returns `pipeline: "ready"`, `version: "sprint6"` |
| Signal schema — 10 types (tech, data, ml, intent, ops, industry, scale, process, hiring, pain_point) | Working | Schema validates all 10 types; dry-run extracts 12 signals across 9 types |
| Maturity scoring (0-5) with dimension breakdown | Working | Run pipeline, check `analysis.maturity_score` in response |
| Victory matching with gap analysis | Working | Check `use_cases[].gap_analysis` in pipeline output |
| Use case generation with tier classification | Working | Check `use_cases[].tier` field (DIRECT/CALIBRATION/ADJACENT) |
| 5-section report rendering in UI | Working | Run frontend, submit URL, report renders below the form |
| UseCaseCard with maturity-tier coloring | Working | Green = DIRECT, amber = CALIBRATION, blue = ADJACENT |
| TracePanel (collapsible pipeline trace) | Working | Click "Show Pipeline Trace" below report |
| Tool registry (WebsiteScraperTool) | Working | Scraper stage uses registry.get("website_scraper") |
| Stage I/O logging to JSONL | Working | Logs appear in `logs/runs/{run_id}.jsonl` after a run |
| Parallel report section writes | Working | Stage 7 uses ThreadPoolExecutor(max_workers=3); per-section failure isolated |
| Extended scraper — product/solutions pages | Working | Scraper fetches /about, /careers, /products, /solutions, /platform; skips 404s |
| `pages_fetched` and `signal_count` in API response | Working | Check response JSON from /v1/analyze |
| Dockerfile at repo root | Ready | `docker build -t ai-transform-agent .` |
| Cloud Run deploy target (infra/deploy_target.py) | Implemented | Deploy via `gcloud run deploy` — requires GCP credentials |
| 188 tests passing | Green | `pytest tests/ -q --tb=short` |
| MatchResult schema (3 tiers) | Working | `orchestrator/schemas.py` exports MatchResult with DELIVERED/ADAPTATION/AMBITIOUS |
| SolutionSchema + IndustryCaseStudySchema | Working | `rag/schemas.py` validates both library record types |
| Matching layer -- 3 output tracks | Working | `orchestrator/matching_layer.py` match() returns delivered/adaptation/ambitious dicts |
| Library A ingestion CLI | Working | `python rag/ingest_solution.py --file tests/fixtures/sample_solution.json --dry-run` |
| Library B ingestion CLI | Working | `python rag/ingest_industry_case.py --file tests/fixtures/sample_industry_case.json --dry-run` |
| Three synthesis prompts | Working | `prompts/tier1_delivered.md`, `tier2_adaptation.md`, `tier3_ambitious.md` at v1.0 |

---

### How to Start the System

```bash
# Backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
# → http://localhost:3000

# Dry-run pipeline (zero API calls)
python orchestrator/pipeline.py --dry-run

# Run test suite
pytest tests/ -q --tb=short

# Docker build (deploy prep)
docker build -t ai-transform-agent .
docker run -p 8080:8080 --env-file .env ai-transform-agent
```

---

### Deploy Instructions (Cloud Run)

```bash
# Prerequisites: GCP credentials, gcloud CLI authenticated
# Sai approved deploy on DISC-57 — approval on record

# Build and push image
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/ai-transform-agent

# Deploy to Cloud Run
gcloud run deploy ai-transform-agent \
  --image gcr.io/$GCP_PROJECT_ID/ai-transform-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080

# Verify health
curl https://<cloud-run-url>/health
```

Note: Live deploy requires Sai to execute from a GCP-authenticated shell.
`infra/deploy_target.py` wraps the gcloud commands — call `deploy_target.deploy()`.

---

### What Is Not Yet Built (Sprint 7 Items)

| Feature | Notes |
|---------|-------|
| Real eval scores | `claude-sonnet-4-20250514` returned HTTP 404 on Vertex AI for project `plotpointe` in `us-east5` — model not enabled. See Eval Scores section. |
| LinkedInJobScraper (second tool) | Cut from Sprint 6 — dry-run only, no demo value; carries to Sprint 7 |
| Low-signal graceful degradation UI warning | Cut from Sprint 6 — signal_count field now exists in API; frontend banner deferred to Sprint 7 |
| Live Cloud Run URL | Dockerfile and deploy target implemented; live deploy pending GCP credentials and Sai execution |
| Authentication / API key gating | Deferred per ADR-002 |

---

### Eval Scores — Sprint 6

Eval scoring attempted via `evals/ci_eval.py`. Judge client was updated to use
`anthropic.AnthropicVertex` (no ANTHROPIC_API_KEY required). However, model
`claude-sonnet-4-20250514` returned HTTP 404 on Vertex AI for project `plotpointe`
in region `us-east5` — the model is not enabled in this project/region combination.

| Dimension | Sprint 7 | Sprint 8 Target | Status |
|-----------|----------|-----------------|--------|
| tier_classification | 3.67 | >= 3.80 | Below target (DISC-70 in progress) |
| evidence_grounding | 4.67 | >= 3.80 | Passing |
| roi_basis | 3.80 | >= 3.80 | Passing |
| match_quality_delivered | -- | >= 3.50 | New rubric (DISC-72) |
| match_quality_adaptation | -- | >= 3.00 | New rubric (DISC-72) |
| match_quality_ambitious | -- | >= 2.80 | New rubric (DISC-72) |

**Sprint 7 resolution options (PM recommendation — Sai decides):**
1. Enable Claude model access: GCP Console → Model Garden → Claude → Enable API
2. Switch judge to Gemini (already available on Vertex, lower quality as judge)
3. Use a different Vertex region where Claude is enabled (e.g. `us-central1`)

---

### Test Progression

| Sprint | Test Count | Delta |
|--------|------------|-------|
| Sprint 4 | 79 | baseline |
| Sprint 5 | 117 | +38 |
| Sprint 6 | 140 | +23 |
| Post-sprint 6 cleanup | 124 | recount |
| Sprint 8 | 188 | +64 |

Zero regressions. All tests pass.

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
| ADR-009 | Parallel report section generation via ThreadPoolExecutor |
| ADR-010 | Cloud Run as production deploy target with zero-secrets-in-image policy |
| ADR-011 | Three-tier matching architecture: two ChromaDB collections, three output tracks |

---

### Sprint 6 Files Added

```
agents/report_writer.py           ← generate_section() added for per-section writes
orchestrator/pipeline.py          ← Stage 7 uses ThreadPoolExecutor(max_workers=3)
evals/judge_client.py             ← switched to anthropic.AnthropicVertex
evals/ci_eval.py                  ← updated to _SPRINT = "sprint_6"
evals/baselines.json              ← sprint_6 key added (scores 0.0, pending_deploy)
app.py                            ← AnalyzeSuccess model extended with pages_fetched, signal_count
infra/deploy_target.py            ← fully implemented with gcloud CLI commands
infra/health_check.py             ← returns pipeline: "ready", version: "sprint6"
Dockerfile                        ← python:3.11-slim, uvicorn on port 8080
.dockerignore                     ← excludes secrets, logs, frontend, .git
requirements.txt                  ← google-auth>=2.29.0 added
docs/decisions/ADR-009.md         ← parallel report write decision
docs/decisions/ADR-010.md         ← Cloud Run deploy target decision
docs/decisions/INDEX.md           ← ADR-009 and ADR-010 indexed
```

---

### Blockers

| Item | Status |
|------|--------|
| Eval judge model not accessible on Vertex AI (`us-east5`, project `plotpointe`) | Tier 2 — PM surfacing to Sai with recommendation (see Eval Scores section) |

---

### Sprint 6 Tickets and Outcomes

| Ticket | Title | Status | Notes |
|--------|-------|--------|-------|
| DISC-54 | Parallel Report Writes | Done | ThreadPoolExecutor(3), per-section isolation |
| DISC-53 | Extended Scraper + Judge Client Fix | Done | pages_fetched + signal_count in API; judge on AnthropicVertex |
| DISC-52 | Eval Baseline | Done | sprint_6 key added; scores 0.0 due to model-not-enabled on Vertex |
| DISC-57 | Cloud Run Deploy Prep | Done | Dockerfile, deploy_target.py, health check; Sai approved |
| DISC-55 | LinkedInJobScraper | Cut to Sprint 7 | No demo value in Sprint 6 |
| DISC-56 | Low-signal warning banner | Cut to Sprint 7 | signal_count field now in API; frontend work deferred |

---

### Next Sprint Goals (Sprint 7)

1. Resolve eval scoring — enable Claude on Vertex or switch judge to Gemini (Sai decides)
2. Execute live Cloud Run deploy — Sai runs gcloud from authenticated shell
3. LinkedInJobScraper — dry-run tool registration (carried from Sprint 6)
4. Low-signal warning banner in UI (carried from Sprint 6)
5. Prompt engineering iteration — improve report quality using real eval scores as gate
6. E2E timing measurement — validate 90s SLA on live Cloud Run URL
