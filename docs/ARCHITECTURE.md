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

## Pipeline Flow (7 Stages)

```
1. POST /v1/analyze → pipeline starts, run_id generated
2. Stage 1: ToolRegistry.get("website_scraper").run(url) → ScrapedData
3. Stage 2: SignalExtractorAgent → typed signals with raw_quote citations
4. Stage 3: MaturityScorerAgent → maturity_score (0-5) + dimension_scores
5. Stage 4: VictoryMatcherAgent → RAG matches with tier + gap_analysis
6. Stage 5: UseCaseGeneratorAgent → use cases (DIRECT/CALIBRATION/ADJACENT)
7. Stage 6: ReportWriterAgent → 5-section report
   Stage 7: All I/O logged per stage to logs/runs/{run_id}.jsonl
8. GET /v1/trace/{run_id} → TracePanel in frontend fetches and renders
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
  → ExtractedSignals { signals[{ signal_id, type, value, raw_quote }] }
  → AnalysisResult { maturity_score, dimension_scores, company_composite_score }
  → VictoryMatches { matches[{ win_id, tier, gap_analysis, confidence }] }
  → ReportSections { exec_summary, maturity, use_cases, roi, roadmap }
```

## Model Routing

| Stage | Model | Provider | Cost/Call |
|-------|-------|----------|-----------|
| Signal Extractor | gemini-2.5-flash | Vertex AI | ~$0.001 |
| Maturity Scorer | gemini-2.5-flash | Vertex AI | ~$0.002 |
| Victory Matcher | gemini-2.5-flash | Vertex AI | ~$0.002 |
| Use Case Generator | gemini-2.5-pro | Vertex AI | ~$0.005 |
| Report Writer | gemini-2.5-flash | Vertex AI | ~$0.004 |
| Eval Judge | claude-sonnet-4-20250514 | Anthropic | ~$0.04 |

Total pipeline: ~$0.011 | With eval: ~$0.05

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
