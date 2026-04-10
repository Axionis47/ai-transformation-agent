# System Overview

## What this application does

AI Opportunity Mapper takes a company name and industry as input, researches the company
using Google Search (via Gemini), compares findings against a knowledge base of past
consulting engagements, forms and stress-tests hypotheses about where AI could help,
and produces a ranked report of AI transformation opportunities with full evidence chains.

The output is an evidence-backed assessment that would traditionally require weeks of
consulting work, delivered in minutes with every claim traced to its source.

---

## How it works

The system runs a 7-phase pipeline for each analysis:

### Phase 1: Company Intake
User provides company name, industry, and optional notes. Two user controls affect
the entire pipeline:
- **Depth** (1-10): scales how many steps each agent takes and how many hypotheses get formed
- **Confidence threshold** (0.3-1.0): controls how strict validation and rejection are

### Phase 2: Grounding
Two research agents run in parallel:
- **CompanyProfiler** researches the company across 5 dimensions: what they do, how they make money, size and scale, technology landscape, organizational structure
- **IndustryAnalyst** researches the industry across 4 dimensions: key trends, competitive dynamics, regulatory landscape, AI adoption level

Both use Gemini with Google Search grounding. After both complete, a PhaseSynthesizer
compresses their outputs into a constant-size briefing for the next phase.

### Phase 3: Deep Research
**PainInvestigator** discovers operational pain points using two tools:
- Google Search grounding (current company-specific problems)
- RAG retrieval (analogous problems from past engagements)

Output: a list of pain points with severity ratings and current workarounds.

### Phase 4: Hypothesis Formation
**HypothesisFormer** creates testable AI opportunity claims from all accumulated evidence.
Uses RAG only (past engagement patterns), no web search. Each hypothesis includes a
statement, category (automation/copilot/decision_support/optimization), target process,
and causal reasoning chain.

### Phase 5: Hypothesis Testing
One **HypothesisTester** per hypothesis, all running in parallel. Each tester uses a
disconfirmation strategy: it actively tries to find evidence against the hypothesis.
Confidence adjusts up or down based on findings. Low-confidence hypotheses get a second
testing round if budget allows. Testers can also request new hypothesis investigations
(spawn requests) if they discover something unexpected.

After testing, hypotheses are finalized:
- Confidence >= threshold: validated
- Confidence < threshold * 0.3: rejected
- Between: validated with conditions

### Phase 6: Report Synthesis
**ReportSynthesizer** produces an AdaptiveReport in a single LLM call:
- Executive summary and key insight
- Ranked opportunities (Easy/Medium/Hard tiers) with confidence, ROI estimates, evidence
- Reasoning chain showing how conclusions were reached
- What we don't know (gaps and uncertainties)
- Recommended next steps
- Evidence annex linking every claim to its source

### Phase 7: Review
User reviews the report and can:
- **Approve** to publish
- **Investigate** to return to hypothesis testing
- **Refine** with three feedback types:
  - *Edit*: re-synthesize report with specific wording changes
  - *Deepen*: re-test targeted hypotheses with more depth
  - *Reinvestigate*: go back to deep research for a full re-run
- **Enrich**: add new evidence, which triggers re-testing of affected hypotheses

---

## Architecture

```
+----------------------------------------------------------+
|                    FRONTEND (Next.js)                     |
|  Home page (intake form) | Run dashboard | Report view   |
+-----------------------------+----------------------------+
                              | HTTP (REST)
+-----------------------------v----------------------------+
|                    API (FastAPI)                          |
|  7 route files under api/routes/                         |
|  Thin handlers -- delegate to engines and services       |
+----+----------+----------+----------+---+----------------+
     |          |          |          |   |
     v          v          v          v   v
+---------+ +--------+ +------+ +------+ +-------+
|ORCHESTR-| |THOUGHT | |PITCH | |AGENTS| |CONTEXT|
|ATOR     | |ENGINE  | |ENGINE| |(x6)  | |PROVID.|
|(pure    | |(legacy)| |(leg.)| |      | |       |
| Python) | |        | |      | |      | |       |
+---------+ +--------+ +------+ +------+ +-------+
     |          |                  |         |
     v          v                  v         v
+---------+ +--------+ +------------------+ +--------+
|GROUNDER | |RAG     | |MEMORY            | |TRACE   |
|Gemini + | |ChromaDB| |EvidenceStore     | |JSONL + |
|Google   | |vector  | |PromotionGate     | |in-mem  |
|Search   | |search  | |ContextRouter     | |        |
+---------+ +--------+ +------------------+ +--------+
                              |
                    +---------+---------+
                    |    STORAGE        |
                    | MemoryStore (dev) |
                    | Firestore (prod)  |
                    +-------------------+
```

**Design rules:**
- The Orchestrator is pure Python control flow. It never calls an LLM. It controls which agents run, in what order, and promotes their results to shared state.
- Agents use LLMs (Gemini) via a ReAct loop (THINK, ACT, OBSERVE, repeat). They never write to shared state directly. They return typed results.
- The Orchestrator is the only thing that writes to run_manager (the state machine).
- Services (grounder, RAG, memory, trace) handle external integrations. They never decide workflow.
- Each agent gets scoped context via AgentContextProvider, so it only sees the data relevant to its task.
- Between phases, a PhaseSynthesizer compresses outputs into constant-size briefings, preventing prompt size from growing with evidence depth.

---

## Repository structure

```
api/                  FastAPI application
  app.py              Entry point, CORS, health check, route registration
  routes/             7 route files: runs, ui, agents, thought, pitch, grounding, rag

core/                 Data models and state management
  config.py           Loads config/defaults.yaml + environment variable overrides
  schemas.py          All Pydantic models (~40 types)
  run_manager.py      Run state machine with valid transitions and persistence
  events.py           46 trace event types

engines/              Pipeline logic
  orchestrator.py     Pure Python pipeline controller (7 phases)
  agents/             6 research agents built on a shared ReAct loop base
    base.py           BaseResearchAgent template
    company_profiler.py
    industry_analyst.py
    pain_investigator.py
    hypothesis_former.py
    hypothesis_tester.py
    report_synthesizer.py
  context_provider.py Scoped context assembly per agent
  hypothesis_tracker.py  Hypothesis lifecycle management
  phase_synthesis.py  Between-phase output compression
  orchestrator_helpers.py  Result promotion, tester spawning, feedback handling
  enrichment.py       Post-analysis evidence injection and re-testing
  thought/            Legacy single-agent reasoning loop
  pitch/              Legacy opportunity scoring and tiering

services/             External integrations
  grounder/           Gemini + Google Search with budget enforcement
  rag/                ChromaDB vector search over past engagements
  memory/             Evidence store, promotion gate, context router
  storage/            Pluggable persistence: in-memory (dev) or Firestore (prod)
  trace.py            Structured event logging (JSONL + in-memory)

frontend/             Next.js 14 + React 18 + TypeScript + Tailwind
  app/page.tsx        Home page with intake form
  app/run/[id]/       Run dashboard, report view, trace log, enrichment
  lib/api.ts          HTTP client for backend
  lib/types.ts        TypeScript type definitions

config/defaults.yaml  All system configuration
prompts/              Agent system prompts (loaded at runtime)
data/wins_kb_seed/    22 past engagement records for RAG knowledge base
tests/                28 test files
```

---

## Configuration

All configuration lives in `config/defaults.yaml` with environment variable overrides.
Config is frozen (snapshotted) when a run is created, so each run has an immutable record
of its settings.

### Key settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `budgets.external_search_query_budget` | 25 | Max Google Search queries per run |
| `budgets.external_search_max_calls` | 8 | Max Gemini grounding API calls |
| `budgets.rag_query_budget` | 15 | Max RAG vector search calls |
| `reasoning.depth_budget` | 5 | Base depth (user sets 1-10, scales agent steps) |
| `reasoning.confidence_threshold` | 0.7 | Validation threshold (user sets 0.3-1.0) |
| `orchestration.mode` | multi_agent | Pipeline mode: "multi_agent" or "legacy" |
| `storage.backend` | memory | Persistence: "memory" or "firestore" |
| `models.reasoning_model` | gemini-2.5-flash | Model for agent ReAct loops |
| `models.synthesis_model` | gemini-2.5-pro | Model for report synthesis |
| `models.grounding_model` | gemini-2.5-flash | Model for Google Search grounding |

### Environment variables

```
GCP_PROJECT_ID=plotpointe
GCP_LOCATION=us-central1
REASONING_MODEL=gemini-2.5-flash
SYNTHESIS_MODEL=gemini-2.5-pro
GROUNDING_MODEL=gemini-2.5-flash
```

---

## Budget system

Three hard caps enforced before every external call:

1. **Search query budget (25)** -- counted per Google Search query extracted from Gemini grounding metadata, not per API call. One Gemini call can trigger multiple searches.
2. **Search call budget (8)** -- caps Gemini grounding API calls as a defense-in-depth layer.
3. **RAG query budget (15)** -- caps ChromaDB vector search calls.

When a budget runs out, the service returns a `budget_exhausted` flag and the agent
works with whatever evidence it has already collected.

---

## Run state machine

```
CREATED -> INTAKE -> GROUNDING -> DEEP_RESEARCH -> HYPOTHESIS_FORMATION
  -> HYPOTHESIS_TESTING -> SYNTHESIS -> REPORT -> REVIEW -> PUBLISHED

Backtracking (user-triggered):
  REVIEW -> HYPOTHESIS_TESTING (investigate)
  REVIEW -> DEEP_RESEARCH (reinvestigate)
  HYPOTHESIS_TESTING -> HYPOTHESIS_FORMATION
  HYPOTHESIS_TESTING -> DEEP_RESEARCH

Any state -> FAILED (on unrecoverable error)
```

All transitions enforced in `core/run_manager.py`. No state skipping allowed.

---

## Running locally

```bash
./dev.sh              # Starts backend (:8000) + frontend (:3000)
./dev.sh --fresh      # Same, but clears ChromaDB for fresh RAG ingest
```

Requirements:
- Python 3.11+ with `pip install -r requirements.txt`
- Node 20+ with `cd frontend && npm install`
- For real Gemini calls: GCP Application Default Credentials
- Without credentials: system falls back to FakeGeminiClient with synthetic responses

---

## Tech stack

- **Backend**: Python 3.11, FastAPI, Pydantic, Uvicorn
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **LLM**: Google Gemini (2.5 Flash for reasoning, 2.5 Pro for synthesis) via Vertex AI
- **Vector search**: ChromaDB (local dev), designed for pgvector swap
- **Persistence**: In-memory (dev), Google Cloud Firestore (prod)
- **Deployment**: Docker multi-stage build, Google Cloud Run

---

## Related documentation

| Document | Contents |
|----------|----------|
| docs/ARCHITECTURE.md | Layer design, ownership rules, scoped context |
| docs/PIPELINE.md | All 7 phases in full detail |
| docs/DATA_MODEL.md | Every data type and its relationships |
| docs/SERVICES.md | Grounder, RAG, Memory, Storage, Trace internals |
| docs/API_REFERENCE.md | Every HTTP endpoint |
| docs/FRONTEND.md | Pages, components, user flow |
