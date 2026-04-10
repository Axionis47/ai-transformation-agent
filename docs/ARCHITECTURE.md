# Architecture

This document explains how the system is structured, what each layer does,
what rules govern communication between layers, and how data flows through
the pipeline.

---

## Layers

The system has 5 layers. Each layer has a specific job and strict boundaries
on what it can and cannot do.

```
+-----------------------------------------------------------------+
|  LAYER 1: FRONTEND                                              |
|  Next.js app. Renders what the API tells it to render.          |
|  Polls for updates. Sends user actions back to the API.         |
+-----------------------------------------------------------------+
                              |
                         HTTP (REST)
                              |
+-----------------------------------------------------------------+
|  LAYER 2: API                                                   |
|  FastAPI routes. Thin handlers that validate input and           |
|  delegate to engines. Never contains business logic.             |
+-----------------------------------------------------------------+
                              |
+-----------------------------------------------------------------+
|  LAYER 3: ENGINES                                               |
|  Orchestrator (pure Python control flow, no LLM)                |
|  Research Agents (LLM-powered, ReAct loops)                     |
|  Context Provider, Hypothesis Tracker, Phase Synthesizer        |
+-----------------------------------------------------------------+
                              |
+-----------------------------------------------------------------+
|  LAYER 4: SERVICES                                              |
|  Grounder (Gemini + Google Search), RAG (ChromaDB),             |
|  Memory (evidence store, promotion, routing),                   |
|  Trace (event logging)                                          |
+-----------------------------------------------------------------+
                              |
+-----------------------------------------------------------------+
|  LAYER 5: STORAGE                                               |
|  Pluggable backend: in-memory dict (dev) or Firestore (prod)    |
|  Swapped at app startup. Same interface either way.             |
+-----------------------------------------------------------------+
```

---

## What each layer owns

### Layer 1: Frontend (frontend/)
- Renders UI based on run status and backend-driven UIHints
- Sends user input (intake, slider values, feedback) to the API
- Polls the API for run state and trace events
- Never decides what happens next. The backend drives all workflow.

### Layer 2: API (api/)
- Validates HTTP input (request bodies, path params)
- Delegates to engines or services
- Returns JSON responses
- Spawns the pipeline in a background thread when POST /start is called
- Contains no business logic, no LLM calls, no direct state mutations

### Layer 3: Engines (engines/)
- **Orchestrator** (orchestrator.py): Pure Python. Controls which agents run, in what order, whether to backtrack. The only thing that writes to run_manager (the state machine). Never calls an LLM.
- **Research Agents** (agents/): LLM-powered. Each runs a ReAct loop (THINK, ACT, OBSERVE). Each returns a typed AgentResult. Never writes to shared state directly.
- **Context Provider** (context_provider.py): Assembles scoped context per agent. Each agent only sees what its scope allows.
- **Hypothesis Tracker** (hypothesis_tracker.py): Manages hypothesis lifecycle and reasoning chains.
- **Phase Synthesizer** (phase_synthesis.py): Compresses phase outputs into constant-size briefings using an LLM. Prevents prompt size from growing with evidence count.

### Layer 4: Services (services/)
- **Grounder** (grounder/): Talks to Gemini via Vertex AI. Two modes: pure reasoning (no budget cost) and grounded search (budget-tracked). Parses grounding metadata into EvidenceItems.
- **RAG** (rag/): Talks to ChromaDB. Semantic search over past engagement chunks. Budget-tracked.
- **Memory** (memory/): Evidence lifecycle management. EvidenceStore holds raw evidence. PromotionGate validates before storing. ContextRouter serves filtered slices to different consumers.
- **Trace** (trace.py): Emits structured events to JSONL files and in-memory store. 46 event types covering every decision point.

### Layer 5: Storage (services/storage/)
- Persistence abstraction via StorageProtocol
- MemoryStore: in-memory dict, used in dev/test, lost on restart
- FirestoreStore: Google Cloud Firestore, used in production, handles large evidence sets via sub-collections
- Swapped at app startup based on config (storage.backend setting)

---

## Communication rules

These rules are enforced by code structure, not just convention.

### Rule 1: Only the orchestrator writes to run_manager

No agent, no service, no route handler mutates run state directly.
All state changes go through `core/run_manager.py` functions, and
only the orchestrator (or the API layer for intake/review actions) calls them.

Agents return `AgentResult` objects. The orchestrator calls
`promote_result()` to write those results into run state.

### Rule 2: Agents never see each other

Agents don't know about other agents. They receive a scoped context
briefing (via AgentContextProvider) and return a typed result. The
orchestrator handles sequencing and data handoff.

### Rule 3: Services never decide workflow

The grounder searches Google. The RAG service searches ChromaDB.
The memory service stores and filters evidence. None of them decide
what happens next. That's the orchestrator's job.

### Rule 4: Every external call is budget-tracked

Grounder tracks search queries (25 max) and API calls (8 max).
RAG tracks retrieval calls (15 max). When a budget runs out, the
service returns a `budget_exhausted` flag and the agent continues
with whatever evidence it already has.

### Rule 5: Evidence goes through a promotion gate

Raw evidence from grounder or RAG does not go directly into run state.
It flows through a PromotionGate that validates:
1. Schema check (evidence_id and source_type present)
2. Phase-aware relevance threshold (grounding: 0.3, deep_research: 0.4, hypothesis_testing: 0.5)
3. Contradiction detection (catches conflicting evidence on scale fields)
4. Dedup (replaces lower-scoring duplicates)

Only promoted evidence becomes part of the run's official evidence list.

---

## Scoped context (who sees what)

Each agent gets an AgentContextProvider that limits what data it can access.
This is defined in `engines/context_provider.py` via the `_SCOPE_ACCESS` dict.

```
Agent                  Can see
-----                  -------
CompanyProfiler        intake, evidence
IndustryAnalyst        intake, evidence
PainInvestigator       intake, company_understanding, industry_context,
                       briefings, insights, evidence
HypothesisFormer       all of the above + pain_points
HypothesisTester       all of the above + hypotheses
ReportSynthesizer      all of the above + hypotheses
```

Early agents (profiler, analyst) start with minimal context so they
research with fresh eyes. Later agents (tester, synthesizer) see
accumulated results from all prior phases.

The context provider also builds a `build_context_briefing()` method
that creates a compact text representation of everything the agent can see.
This briefing is constant-size regardless of how much evidence exists,
because it shows top-3 evidence per dimension and truncates snippets.

---

## Phase synthesis (how context stays manageable)

Between each phase, the orchestrator calls `PhaseSynthesizer` to compress
the phase's outputs into a short briefing (3-6 sentences).

```
Grounding phase completes
  -> PhaseSynthesizer.synthesize_grounding()
  -> 3-5 sentence briefing stored in SynthesisStore
  -> PainInvestigator reads this briefing instead of raw evidence

Deep research phase completes
  -> PhaseSynthesizer.synthesize_research()
  -> 4-6 sentence briefing
  -> HypothesisFormer reads this briefing

Hypothesis testing completes
  -> PhaseSynthesizer.synthesize_testing()
  -> 3-5 sentence briefing
  -> ReportSynthesizer reads this briefing
```

The synthesizer uses the grounder's `reason()` method (pure LLM, no search,
no budget cost) to compress. If the LLM is unavailable, it falls back to
truncating the raw context to 500 characters.

This prevents a common problem: as the pipeline runs, evidence accumulates
and prompts grow without bound. Phase synthesis keeps each agent's input
at a predictable size.

---

## Evidence flow (full lifecycle)

```
Google Search (grounder)          Past engagements (RAG)
        |                                   |
        v                                   v
  GroundingResult                    RAGQueryResult
  (raw EvidenceItems)                (raw EvidenceItems)
        |                                   |
        +-----------------------------------+
                         |
                         v
                  PromotionGate
          (schema check, relevance filter,
           contradiction detection, dedup)
                         |
                         v
                   EvidenceStore
            (per-run, sorted by relevance)
                         |
                         v
                   ContextRouter
          (filtered slices per consumer)
                    /    |    \
                   v     v     v
              Thought  Pitch  Report
              (15 max) (25 max) (linked only)
```

Different consumers get different evidence slices:
- **Thought loops**: 15 items max, 0.3 min relevance, broad coverage
- **MID assessment**: 20 items max, 0.0 min relevance (needs to see gaps)
- **Pitch synthesis**: 25 items max, 0.3 min relevance
- **Report composition**: only evidence linked to specific opportunities

---

## The ReAct loop (how agents think)

Every research agent follows the same pattern, defined in `engines/agents/base.py`:

```
for step in range(MAX_STEPS):
    thought = _think(context_briefing)    # LLM decides what to do
    if thought.action == "STOP":
        break
    observation = _act(thought)           # Execute tool (GROUND or RAG)
    _observe(observation)                 # Process results
    context_briefing = _update_context()  # Add new evidence to briefing
```

Each `_think()` call sends the current context briefing to the LLM along with
the agent's system prompt (from prompts/). The LLM responds with an action:
- **GROUND**: search Google via Gemini grounding
- **RAG**: search past engagements via ChromaDB
- **STOP**: agent is done (enough evidence collected or budget exhausted)

The `_act()` method executes the chosen tool and returns an observation string.
The `_observe()` method lets subclasses extract domain-specific insights.

Each agent subclass overrides `_think()` to customize its reasoning prompt
and `_build_result()` to return domain-specific output (CompanyUnderstanding,
PainPoints, Hypotheses, AdaptiveReport, etc.).

---

## Depth scaling (how user controls affect agents)

The user sets a depth slider (1-10, default 5). This scales how many ReAct
steps each agent gets and how many hypotheses are formed.

Formula: `max(2, min(cap, round(base * depth / 5.0)))`

```
Agent               Base steps    Depth=1    Depth=5    Depth=10
-----               ----------    -------    -------    --------
CompanyProfiler     6             2          6          12
IndustryAnalyst     4             2          4          8
PainInvestigator    6             2          6          12
HypothesisFormer    4             2          4          8
HypothesisTester    4             2          4          8
Max hypotheses      5             2          5          10
```

The confidence threshold (0.3-1.0, default 0.7) controls:
- **Validation threshold**: hypothesis must reach this confidence to be validated
- **Rejection threshold**: confidence_threshold * 0.3 (e.g., 0.21 at default)
- Hypotheses between the thresholds are "validated with conditions"

---

## State machine

All run state transitions are enforced in `core/run_manager.py`.
The `VALID_TRANSITIONS` dict defines every legal move.

```
Multi-agent pipeline (normal flow):
  CREATED -> INTAKE -> GROUNDING -> DEEP_RESEARCH -> HYPOTHESIS_FORMATION
  -> HYPOTHESIS_TESTING -> SYNTHESIS -> REPORT -> REVIEW -> PUBLISHED

Backtracking (user-triggered from REVIEW):
  REVIEW -> HYPOTHESIS_TESTING    (investigate specific hypotheses)
  REVIEW -> DEEP_RESEARCH         (reinvestigate from scratch)

Backtracking (pipeline-internal):
  HYPOTHESIS_TESTING -> HYPOTHESIS_FORMATION
  HYPOTHESIS_TESTING -> DEEP_RESEARCH
  DEEP_RESEARCH -> GROUNDING

Legacy pipeline (orchestration.mode = "legacy"):
  CREATED -> INTAKE -> ASSUMPTIONS_DRAFT -> ASSUMPTIONS_CONFIRMED
  -> REASONING -> SYNTHESIS -> REPORT -> PUBLISHED

Terminal:
  Any state -> FAILED
```

Every mutation to run state calls `_persist(run)` which saves to the
storage backend. Config is frozen at run creation and never changes
after that, so each run has an immutable record of its settings.

---

## Storage abstraction

```
core/run_manager.py
  uses _store: StorageProtocol
                |
         +------+------+
         |             |
    MemoryStore    FirestoreStore
    (dict)         (Firestore)
```

`StorageProtocol` defines 4 methods: save_run, get_run, list_runs, delete_run.

At app startup (`api/app.py`), the config is loaded. If `storage.backend`
is "firestore", a FirestoreStore is created and injected via `init_storage()`.
Otherwise the default MemoryStore is used.

FirestoreStore handles large evidence sets by splitting evidence into
a sub-collection when count exceeds 150 items (Firestore has a 1MB doc limit).
On read, it reassembles the evidence from the sub-collection.

---

## Tracing

Every significant action emits a trace event via `services/trace.py`.

Events are:
- Written to `logs/{run_id}.jsonl` (one line per event, append-only)
- Stored in an in-memory dict for fast API access
- Queryable via `GET /v1/runs/{run_id}/trace`

The 46 event types (defined in `core/events.py`) cover:
- Run lifecycle: RUN_CREATED, CONFIG_SNAPSHOT_SAVED
- Evidence: EVIDENCE_PROMOTED, EVIDENCE_REJECTED, EVIDENCE_CONTRADICTION
- Agents: AGENT_SPAWNED, AGENT_COMPLETED, AGENT_FAILED
- Hypotheses: HYPOTHESIS_FORMED, HYPOTHESIS_TESTED, HYPOTHESIS_VALIDATED, HYPOTHESIS_REJECTED
- Budget: EXTERNAL_BUDGET_EXHAUSTED, BUDGET_VIOLATION_BLOCKED
- Pipeline: REASONING_LOOP_STARTED, PHASE_BACKTRACK, STAGE_FAILED
- Terminal: RUN_PUBLISHED

The frontend polls the trace endpoint to show live progress during pipeline execution.

---

## Key files

| File | What it does |
|------|-------------|
| `engines/orchestrator.py` | Pipeline controller. Drives all 7 phases. Pure Python, no LLM. |
| `engines/agents/base.py` | ReAct loop template. All 6 agents extend this. |
| `engines/context_provider.py` | Scoped context per agent. Controls who sees what. |
| `engines/phase_synthesis.py` | Compresses phase outputs into briefings. |
| `engines/hypothesis_tracker.py` | Hypothesis lifecycle and reasoning chains. |
| `core/run_manager.py` | State machine. All state mutations go through here. |
| `core/schemas.py` | Every data type in the system (~40 Pydantic models). |
| `services/grounder/grounder.py` | Gemini + Google Search with budget enforcement. |
| `services/rag/retrieval.py` | ChromaDB search with budget enforcement. |
| `services/memory/promotion.py` | Validates evidence before it enters the store. |
| `services/memory/router.py` | Serves filtered evidence slices per consumer. |
| `services/memory/store.py` | Per-run evidence storage with dedup. |
| `services/trace.py` | Event logging (JSONL + in-memory). |
| `api/app.py` | FastAPI setup, storage init, route registration. |
