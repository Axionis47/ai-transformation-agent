# Sprint Plan — AI Opportunity Mapper

> Living document. Updated after each sprint completes.
> Next sprint reads this doc to know exactly where to start.

---

## System in one sentence

An interactive agent that reasons over a wins knowledge base and Gemini Google Search grounding to produce evidence-backed AI transformation recommendations for mid-market companies, with full traceability and budget controls.

---

## Architecture — five engines, cleanly separated

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                     │
│  Backend-driven: renders what API tells it to render      │
│  Interactive: user provides info, approves assumptions    │
│  Shows: evidence / abstraction / confidence separately    │
└────────────────────────┬─────────────────────────────────┘
                         │ SSE / REST
┌────────────────────────▼─────────────────────────────────┐
│                    API + RUN MANAGER                      │
│  FastAPI on Cloud Run                                     │
│  Run state machine, config snapshots, budget enforcement  │
│  Backend-driven UI contract (ui_hints, actions, fields)   │
└──┬──────────┬──────────┬──────────┬──────────┬───────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ RAG  │ │GROUNDER│ │THOUGHT │ │ PITCH  │ │ TRACE  │
│SERVICE│ │        │ │ ENGINE │ │SYNTH   │ │ EMIT   │
│      │ │Gemini +│ │        │ │        │ │        │
│Wins  │ │Google  │ │Reason  │ │3-tier  │ │Struct  │
│KB    │ │Search  │ │loop +  │ │recs +  │ │logs +  │
│only  │ │grounding│ │MID +  │ │ROI     │ │trace   │
│      │ │+ budget│ │depth   │ │from    │ │correl  │
│      │ │control │ │control │ │wins    │ │        │
└──────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

Key rules:
- RAG is a completely separate service. Agent calls it like a tool.
- Grounder is a separate module. Agent calls it like a tool.
- Thought engine orchestrates — decides what to ask, when to ask user, when to stop.
- Pitch synthesis is separate from reasoning — translates evidence into client-facing recs.
- Trace emitter is always on. Every action logged.

---

## Sprint 1 — Foundation + Contracts

**Goal:** Repo skeleton, schemas, config, run state machine, API shell with backend-driven UI contract. Nothing works yet, but every interface is defined.

**What gets built:**
- Repo structure: `/services/api`, `/packages/contracts`, `/config`, `/data/wins_kb_seed`
- Pydantic schemas for every pipeline entity (Run, StageOutput, Evidence, Opportunity, TraceEvent)
- Config service: all knobs in one YAML, frozen per run as `config_snapshot`
- Run manager: create run, store config, enforce stage transitions
- FastAPI endpoints: `POST /v1/runs`, `GET /v1/runs/{id}`, `GET /v1/runs/{id}/ui`
- Backend-driven UI contract: `ui_hints`, `actions`, `editable_fields` shape defined
- Trace event emitter (local structured JSON logs, not Cloud Logging yet)

**Success criteria:**
- [ ] `POST /v1/runs` creates a run with config snapshot and returns run_id
- [ ] `GET /v1/runs/{id}/ui` returns ui_hints with stage progress and next action
- [ ] All Pydantic schemas validate sample data without errors
- [ ] Config loads from YAML, freezes per run, is immutable after creation
- [ ] Trace events written to local JSONL for RUN_CREATED, CONFIG_SNAPSHOT_SAVED
- [ ] No hardcoded values — everything in config

**Dependencies:** None. This is the base.

**Status:** COMPLETE (2026-03-23) — 52 tests passing, all endpoints live, 18 commits pushed

---

## Sprint 2 — RAG Service (standalone)

**Goal:** Wins KB as a completely separate, callable service. Ingest synthetic past engagements, retrieve with budget controls. The thought engine will call this as a tool.

**What gets built:**
- Wins KB schema: `engagement_case` with fields (industry, problem, solution_shape, measured_impact, roi_drivers, conditions_for_success, anti_patterns)
- 15-20 synthetic seed engagements (realistic mid-market wins)
- Ingestion pipeline: chunk, embed, store (ChromaDB local for dev, Cloud SQL+pgvector for prod)
- Retrieval endpoint: semantic search with `rag_top_k`, `rag_min_score`, `rag_query_budget`
- Evidence normalization: retrieved chunks become `EVIDENCE_ITEM` objects
- Trace events: RAG_QUERY_EXECUTED, RAG_RESULTS_FILTERED

**Success criteria:**
- [ ] 15+ seed engagements ingested and retrievable
- [ ] Query "customer support automation mid-market" returns relevant engagements ranked by score
- [ ] Budget enforcement: after N queries, retrieval refuses and returns budget_exhausted
- [ ] Each retrieved chunk has evidence_id, source_ref, relevance_score, snippet
- [ ] RAG service is callable as a standalone function — no coupling to thought engine
- [ ] Trace events emitted for every retrieval call

**Dependencies:** Sprint 1 (schemas, config, trace emitter)

**Status:** COMPLETE (2026-03-23) — 108 tests total, 18 seed engagements, budget enforcement working

---

## Sprint 3 — Gemini Grounding + Evidence Layer

**Goal:** Gemini Google Search grounding as a separate, callable tool. Budget enforcement per query (not per call). Unified evidence model across RAG and grounding.

**What gets built:**
- Grounder module: calls Gemini with `google_search=GoogleSearch()` tool
- Budget enforcement: count `webSearchQueries` returned, decrement from budget, hard stop when exhausted
- Parse grounding metadata: extract `grounding_chunks` (uri, title, domain), `grounding_supports` (segment text, confidence scores)
- Unified evidence model: both RAG chunks and grounding chunks normalize into `EVIDENCE_ITEM`
- Trace events: GROUNDING_CALL_REQUESTED, GROUNDING_CALL_COMPLETED, GROUNDING_QUERIES_COUNTED, EXTERNAL_BUDGET_EXHAUSTED
- `searchEntryPoint` handling: flag and store display requirements

**Success criteria:**
- [x] Call grounder with "What does Company X do?" and get a synthesized answer with citations
- [x] Budget tracks queries not calls — if one call triggers 3 Google searches, budget decrements by 3
- [x] After budget exhausted, grounder returns error with coverage_gap flag instead of calling
- [x] Grounding evidence and RAG evidence both produce identical EVIDENCE_ITEM shape
- [x] Confidence scores from grounding metadata are preserved per evidence item
- [x] All grounding activity traced with run_id correlation

**Dependencies:** Sprint 1 (schemas, config, trace). Sprint 2 not required — grounder is independent of RAG.

**Status:** COMPLETE (2026-03-23) — 142 tests total, two-layer budget enforcement, fake client for testing

---

## Sprint 4 — Thought Engine (the reasoning loop)

**Goal:** The core reasoning agent. Takes company name + industry, enters a bounded reasoning loop. Uses RAG and grounder as tools. Detects missing information and asks the user. Builds evidence progressively.

**What gets built:**
- Thought engine: iterative reasoning loop with configurable `depth_budget` (default 3 loops)
- Each loop: assess what's known → identify gaps (MID) → decide action (query RAG / ground / ask user)
- MID (Missing Information Detection): compares current evidence against required fields, identifies biggest gaps
- User interaction: when MID says info is missing and tools can't fill it, emit a user_question action via API
- Evidence accumulator: tracks all evidence gathered across loops, deduplicates, scores
- Stop conditions: confidence threshold met OR depth budget exhausted OR all required fields covered
- Company intake + assumptions draft: first loop produces assumptions, user confirms/edits

**Success criteria:**
- [x] Given "Acme Logistics, logistics industry" — agent completes 3 reasoning loops
- [x] Each loop queries RAG and/or grounder with different, progressively refined questions
- [x] MID correctly identifies that "exception volume" is unknown and asks the user
- [x] User provides answer via API, agent incorporates it and continues
- [x] Evidence accumulates across loops — loop 3 has more evidence than loop 1
- [x] Agent stops when depth budget hit, even if confidence is low (records coverage gaps)
- [x] Full trace of every reasoning step, tool call, and decision

**Dependencies:** Sprint 2 (RAG), Sprint 3 (grounder). Both must be callable as tools.

**Status:** COMPLETE (2026-03-23) — 177 tests total, 18 commits, bounded reasoning loop with MID + evidence accumulation

---

## Sprint 5 — Pitch Synthesis Engine + 3-Tier Recommendations

**Goal:** Translate the thought engine's evidence into client-facing recommendations. Three tiers: easy (proven wins), medium (needs adaptation), hard (ambitious). ROI translated from past wins to this company.

**What gets built:**
- Opportunity template library: versioned templates with problem_pattern, solution_shape, win_signals, anti_signals, roi_drivers
- Template matching: map evidence to templates, fire win_signals, check anti_signals
- 3-tier classification:
  - Easy: direct match to past engagement, high confidence, proven ROI
  - Medium: similar past engagement exists but different industry/scale/context — needs adaptation
  - Hard: novel application, low evidence, high potential but uncertain
- ROI translation: take measured_impact from matched wins, adjust for company size/industry, show assumptions
- Scoring: feasibility, ROI, time-to-value, confidence — all separate, all explainable
- Sensitivity analysis: which assumptions most affect ROI
- Report composer: operator brief + evidence annex

**Success criteria:**
- [x] Given thought engine output, produces 3-5 opportunities across all three tiers
- [x] Each opportunity shows: evidence items that support it, template that matched, score breakdown
- [x] Easy tier opportunities cite specific past engagements with measured ROI
- [x] Medium tier opportunities explicitly state what adaptation is needed and why
- [x] Hard tier opportunities show high potential but flag low confidence with reasons
- [x] ROI model recomputes when user changes an assumption (e.g., employee count)
- [x] Operator brief is one readable page with coverage gaps listed

**Dependencies:** Sprint 4 (thought engine produces evidence + company understanding)

**Status:** COMPLETE (2026-03-23) — 212 tests total, 14 commits, 8 templates, 3-tier classification, ROI translation, operator brief

---

## Sprint 6 — Interactive Frontend

**Goal:** The UI. Backend-driven — frontend renders what API says. Interactive — user provides company info, answers agent questions, reviews assumptions, sees evidence/abstraction/confidence separately, gets 3-tier recommendations.

**What gets built:**
- Run creation: company name + industry input form
- Live progress: SSE stream showing agent's reasoning steps in real-time
- Assumptions review: editable fields, user approves/rejects/edits
- Agent questions: when MID triggers a user question, frontend shows it and accepts input
- Evidence panel: all evidence items with source type, confidence, snippet, source URL
- Three separate columns/views: Evidence | Abstraction | Confidence
- 3-tier recommendations: Easy (green) / Medium (yellow) / Hard (red) sections
- Each opportunity: expandable with score breakdown, evidence links, ROI sensitivity
- Budget dashboard: remaining RAG queries, remaining grounding queries
- Trace viewer: timeline of agent actions (collapsible)
- Operator brief: final rendered report with export option

**Success criteria:**
- [ ] End-to-end: enter company name → see agent reason → answer questions → get recommendations
- [ ] Evidence, abstraction, and confidence are visually separate — not blended
- [ ] User can answer agent questions mid-analysis and see agent continue
- [ ] 3 tiers clearly distinguished with evidence backing per opportunity
- [ ] Budget remaining visible at all times
- [ ] Works on laptop screen (responsive not required — desktop-first)
- [ ] Full analysis completes and renders in under 2 minutes

**Dependencies:** Sprint 5 (full backend pipeline working)

**Status:** NOT STARTED

---

## Sprint 7 — Eval, Observability, Demo

**Goal:** Evaluation harness, Cloud Logging integration, demo polish. System is demo-ready.

**What gets built:**
- 25 synthetic company bundles for evaluation
- Evaluation metrics: coverage, evidence strength, opportunity relevance, budget adherence, latency
- Cloud Logging integration: structured logs with trace/spanId correlation
- Log-based metrics: budget usage, confidence trends, latency distributions
- Security: Secret Manager for keys, IAP for access
- CI/CD: Cloud Build trigger on main → Cloud Run deploy
- Demo script: 10-minute walkthrough following the trust-first narrative
- Polish: error states, loading states, edge cases

**Success criteria:**
- [ ] Eval harness runs 25 companies automatically and produces metrics
- [ ] Coverage > 70%, budget adherence > 95% across eval set
- [ ] All trace events visible in Cloud Logging with run_id correlation
- [ ] CI/CD: push to main triggers build and deploy
- [ ] 10-minute demo runs without errors or manual intervention
- [ ] Cost per analysis < $0.50
- [ ] Latency < 2 minutes end-to-end

**Dependencies:** Sprint 6 (everything working end-to-end)

**Status:** NOT STARTED

---

## Sprint tracker

| Sprint | Goal | Status | Completed | Notes |
|--------|------|--------|-----------|-------|
| 1 | Foundation + Contracts | COMPLETE | 2026-03-23 | 52 tests, 18 commits, all endpoints live |
| 2 | RAG Service | COMPLETE | 2026-03-23 | 108 tests, 18 seeds, budget enforcement |
| 3 | Gemini Grounding | COMPLETE | 2026-03-23 | 142 tests, 10 commits, two-layer budget, fake client |
| 4 | Thought Engine | COMPLETE | 2026-03-23 | 177 tests, 18 commits, MID + evidence accumulation + user questions |
| 5 | Pitch Synthesis | COMPLETE | 2026-03-23 | 212 tests, 14 commits, 8 templates, ROI model, operator brief |
| 6 | Frontend | NOT STARTED | — | — |
| 7 | Eval + Demo | NOT STARTED | — | — |

---

## Rules for sprint execution

1. Each sprint starts by reading THIS document — specifically the sprint's section
2. After sprint completes, update this doc: check off success criteria, update status, add notes
3. If a sprint changes the plan for future sprints, update those sections too
4. No sprint starts until the previous sprint's success criteria are ALL checked
5. If a sprint can't meet criteria, document what's missing and why before moving on
6. Architecture stays clean — no sprint introduces coupling between engines
7. Every sprint produces something testable — no invisible work
