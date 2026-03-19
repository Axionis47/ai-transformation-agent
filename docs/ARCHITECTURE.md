# Architecture Overview

## System Diagram

```
┌───────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js + TypeScript + Tailwind + Neomorphic)      │
│                                                               │
│  URLInput → AnalysisStatus → ReportRenderer + TracePanel     │
└──────────────────────────┬────────────────────────┬──────────┘
        POST /v1/analyze   │     GET /v1/trace/{id} │
                           ▼                        │
┌──────────────────────────────────────────────────────────────┐
│  BACKEND (Cloud Run / FastAPI)                               │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  orchestrator/pipeline.py (7 stages)                │    │
│  │  Stage 1: ToolRegistry → WebsiteScraperTool         │    │
│  │  Stage 2: SignalExtractorAgent                       │    │
│  │  Stage 3: MaturityScorerAgent                        │    │
│  │  Stage 4: VictoryMatcherAgent (gap_analysis)        │    │
│  │  Stage 5: UseCaseGeneratorAgent                      │    │
│  │  Stage 6: ReportWriterAgent                          │    │
│  │  Stage 7: logger.log_agent_call() per stage         │    │
│  └────────────────────────┬────────────────────────────┘    │
│                            │                                 │
│  ┌───────────────┐  ┌──────▼──────────┐  ┌───────────────┐  │
│  │ToolRegistry   │  │orchestrator/    │  │GET /v1/trace  │◀─┘
│  │tool_registry  │  │stage_io.py      │  │endpoint       │
│  └──────┬────────┘  └─────────────────┘  └───────────────┘
│         │ wraps                                             │
│  ┌──────▼────────┐  ┌─────────────────┐                    │
│  │tools/website  │  │ops/model_client │                    │
│  │_scraper.py    │  │ops/logger.py    │                    │
│  └──────┬────────┘  └────────┬────────┘                    │
│         │ wraps              │                              │
│  ┌──────▼────────┐           ▼                              │
│  │agents/*.py    │    VERTEX AI (gemini-2.5)                │
│  └───────────────┘                                          │
│  ┌───────────────┐    logs/runs/{run_id}.jsonl              │
│  │rag/vector_    │                                          │
│  │store.py       │                                          │
└──┴───────┬────────┴─────────────────────────────────────────┘
           ▼
  CHROMADB (in-container)      ANTHROPIC (evals only, JudgeClient)
```

## Two-Library, Three-Track Matching

```
COMPANY ANALYSIS PIPELINE              SOLUTIONS LIBRARIES

  Stage 4: RAG Query ----retrieval----> tenex_delivered (Library A)
                     (separate          industry_cases  (Library B)
                      queries)

  ========== MATCHING LAYER (orchestrator/matching_layer.py) ==========

  Inputs:  SignalSet + MaturityResult
           list[dict] from tenex_delivered
           list[dict] from industry_cases

  TRACK 1 -- DELIVERED     confidence 0.80-0.95    Library A score >= 0.75
  TRACK 2 -- ADAPTATION    confidence 0.55-0.79    Library A score 0.45-0.74
  TRACK 3 -- AMBITIOUS     confidence 0.40-0.65    Library B score >= 0.30

  One Library A record appears in at most one track.
  Library B records only appear in AMBITIOUS.
  =====================================================================

  Stage 6: UseCaseGeneratorAgent -- per-tier synthesis (3 model calls max)
    DELIVERED -> tier1_delivered.md prompt (cite exact win_id, proven metrics)
    ADAPTATION -> tier2_adaptation.md prompt (cite base win, explain gap)
    AMBITIOUS  -> tier3_ambitious.md prompt (cite external company or source)
```

Separation contracts:
- The analysis pipeline produces `SignalSet + MaturityResult`.
- `rag/ingest_solution.py` feeds Library A (`tenex_delivered` collection).
- `rag/ingest_industry_case.py` feeds Library B (`industry_cases` collection).
- `orchestrator/matching_layer.py` is the only bridge between libraries and the pipeline.
- No analysis agent reads either library directly.

## Pipeline Flow (7 Stages)

```
1. POST /v1/analyze -> pipeline starts, run_id generated
2. Stage 1: ToolRegistry.get("website_scraper").run(url) -> ScrapedData
3. Stage 2: SignalExtractorAgent -> typed signals with raw_quote citations
4. Stage 3: MaturityScorerAgent -> composite_score + composite_label
5. Stage 4: RAGQueryAgent -> queries tenex_delivered + industry_cases separately
6. Stage 5: matching_layer.match() -> dict: delivered/adaptation/ambitious lists
7. Stage 6: UseCaseGeneratorAgent -> per-tier synthesis (up to 3 model calls)
8. Stage 7: ReportWriterAgent -> 5-section report (parallel ThreadPoolExecutor)
   All I/O logged per stage to logs/runs/{run_id}.jsonl
9. GET /v1/trace/{run_id} -> TracePanel in frontend fetches and renders
```

## Tool Registry Pattern

```
pipeline.py
  registry.get("website_scraper").run(url)
        ↓
orchestrator/tool_registry.py   (Tool ABC + ToolRegistry singleton)
        ↓
tools/website_scraper.py        (WebsiteScraperTool)
        ↓ wraps
agents/scraper.py               (ScraperAgent, unchanged)
```

To add a tool in Sprint 6: create `tools/new_tool.py`,
call `registry.register(NewTool())` — no changes to `pipeline.py`.

## Stage I/O Logging Flow

```
ops/logger.log_agent_call(stage, input_summary, output_summary, run_id)
  → logs/runs/{run_id}.jsonl (append-only, never committed)
  → GET /v1/trace/{run_id} parses and returns stage list
  → frontend TracePanel renders collapsible rows
```

## Eval Judge Flow

```
evals/ci_eval.py (5 test companies from test_companies.json)
  → evals/judge_client.py (JudgeClient → Anthropic claude-sonnet-4-20250514)
  → scores 3 rubrics: tier_classification, evidence_grounding, roi_basis
  → writes to evals/baselines.json (sprint-keyed history)
```

## Data Flow

```
ScrapedData { url, company_name, pages }
  -> SignalSet { signals[{ signal_id, type, value, raw_quote }], industry, scale }
  -> MaturityResult { composite_score, composite_label, dimension_scores }
  -> dict[str, list[MatchResult]] { delivered[], adaptation[], ambitious[] }
  -> list[UseCase] (ordered: DELIVERED first, ADAPTATION, AMBITIOUS last)
  -> ReportSections { exec_summary, maturity, use_cases, roi, roadmap }
```

## Model Routing

| Stage | Model | Provider | Cost/Call |
|-------|-------|----------|-----------|
| Signal Extractor | gemini-2.5-flash | Vertex AI | ~$0.001 |
| Maturity Scorer | gemini-2.5-flash | Vertex AI | ~$0.002 |
| Use Case Generator (per tier) | gemini-2.5-pro | Vertex AI | ~$0.005 each |
| Report Writer | gemini-2.5-flash | Vertex AI | ~$0.004 |
| Eval Judge | claude-sonnet-4-20250514 | Anthropic | ~$0.04 |

Total pipeline: ~$0.018 (3 use case calls) | With eval: ~$0.06

## Infrastructure

| Component | Technology | Region |
|-----------|------------|--------|
| Backend | Cloud Run | us-central1 |
| Frontend | Vercel | Edge |
| Models | Vertex AI | us-central1 |
| Vector Store | ChromaDB | In-container |
| Eval Judge | Anthropic API | Global |
| Secrets | Secret Manager | Global |

## File Ownership

| Directory | Owner |
|-----------|-------|
| agents/*.py, orchestrator/*.py, tools/*.py, ops/*.py, rag/*.py, infra/*.py | Backend |
| evals/*.py, evals/rubrics/*.yaml, .github/workflows/*.yml | QA |
| prompts/*.md, docs/*.md | PM |
| frontend/**/*.ts, frontend/**/*.tsx | Frontend |
