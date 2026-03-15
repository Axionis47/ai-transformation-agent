# Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (Vercel)                                                       │
│  Next.js App Router + TypeScript + Tailwind + Neomorphic Design         │
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │  URL Input  │───▶│  Analysis   │───▶│   Report    │                  │
│  │  Component  │    │   Status    │    │   Renderer  │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
└────────────────────────────┬────────────────────────────────────────────┘
                             │ POST /analyze
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  BACKEND (Cloud Run)                                                     │
│  FastAPI + Python 3.11                                                   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  orchestrator/pipeline.py                                        │    │
│  │                                                                   │    │
│  │  URL ──▶ Scraper ──▶ Consultant ──▶ RAG Query ──▶ Report Writer │    │
│  │           │              │              │              │         │    │
│  │           ▼              ▼              ▼              ▼         │    │
│  │      ScrapedData   AnalysisResult  RAGMatches    ReportSections │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │ ops/         │    │ rag/         │    │ infra/       │               │
│  │ model_client │    │ vector_store │    │ health_check │               │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘               │
└─────────┼───────────────────┼───────────────────────────────────────────┘
          │                   │
          ▼                   ▼
┌─────────────────┐   ┌─────────────────┐
│  VERTEX AI      │   │  CHROMADB       │
│  (GCP)          │   │  (In-container) │
│                 │   │                 │
│  gemini-2.5-pro │   │  20 seed        │
│  gemini-2.5-    │   │  solutions      │
│  flash          │   │                 │
└─────────────────┘   └─────────────────┘
```

## Pipeline Flow

```
1. User enters company URL in frontend
2. Frontend POSTs to /analyze endpoint
3. Pipeline orchestrator starts run:
   a. Scraper extracts company data (about, careers, blog, product pages)
   b. Consultant scores AI maturity (0-5) and identifies use cases
   c. RAG queries similar companies from vector store
   d. Report Writer generates 5 sections using RAG matches
4. Pipeline returns full report as JSON
5. Frontend renders report with neomorphic UI components
```

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  DECISION COUNCIL (pitch → approve → review)                    │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                     │
│  │   PM    │    │   DOC   │    │  CONS   │                     │
│  │ [PM]    │    │ [DOC]   │    │ [CONS]  │                     │
│  └─────────┘    └─────────┘    └─────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  EXECUTION AGENTS (implement tickets)                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │ Backend │ │Frontend │ │Prompt   │ │  RAG    │ │ Evals   │  │
│  │ [BE]    │ │ [FE]    │ │Eng [PE] │ │ [RAG]   │ │ [EVAL]  │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│  ┌─────────┐                                                    │
│  │ LLMOps  │                                                    │
│  │ [OPS]   │                                                    │
│  └─────────┘                                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  QUALITY GATE (validate it works)                               │
│  ┌─────────┐                                                    │
│  │   QA    │                                                    │
│  │ [QA]    │                                                    │
│  └─────────┘                                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
ScrapedData
├── url: string
├── company_name: string
├── pages.about: string
├── pages.careers: string
├── pages.blog: string
└── pages.product: string
         │
         ▼
AnalysisResult
├── maturity_score: 0.0-5.0
├── maturity_label: Beginner|Developing|Emerging|Advanced|Leading
├── maturity_rationale: string (cites evidence)
├── top_use_cases: [
│     { title, description, effort, impact, roi_estimate, confidence }
│   ]
└── rag_matches: [StoredSolution]
         │
         ▼
ReportSections
├── exec_summary: string
├── maturity: string
├── use_cases: string
├── roi: string
└── roadmap: string
```

## Model Routing

| Stage | Model | Provider | Cost/Call |
|-------|-------|----------|-----------|
| Consultant | gemini-2.5-pro | Vertex AI | ~$0.005 |
| Report Writer | gemini-2.5-flash | Vertex AI | ~$0.004 |
| RAG Relevance | gemini-2.5-flash | Vertex AI | ~$0.001 |
| Eval Judge | claude-sonnet-4-20250514 | Anthropic | ~$0.04 |

Total pipeline: ~$0.011 | With eval: ~$0.05

## Infrastructure

| Component | Technology | Region |
|-----------|------------|--------|
| Backend | Cloud Run | us-central1 |
| Frontend | Vercel | Edge |
| Models | Vertex AI | us-central1 |
| Vector Store | ChromaDB | In-container |
| Secrets | Secret Manager | Global |
| Logs | Cloud Logging | Global |

## File Ownership

| Directory | Owner Agent |
|-----------|-------------|
| agents/*.py | Backend |
| orchestrator/*.py | Backend |
| ops/*.py | Backend, LLMOps |
| rag/*.py | RAG |
| evals/*.py | Evals |
| infra/*.py | Backend |
| prompts/*.md | Prompt Eng |
| frontend/**/*.ts | Frontend |
| docs/*.md | DOC |
| .github/workflows/*.yml | LLMOps |
