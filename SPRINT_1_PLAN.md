# Sprint 1 — Foundation + Contracts

> Read this fully before writing any code.
> Every file, schema, and endpoint is specified below.
> Nothing is left ambiguous.

---

## Goal

Repo skeleton, all schemas, config service, run state machine, API shell, backend-driven UI contract, trace emitter. Nothing "works" yet (no RAG, no grounding, no reasoning) — but every interface is defined and the API is running.

---

## Repo structure (what gets created)

```
/
├── api/
│   ├── __init__.py
│   ├── app.py                  # FastAPI entry point
│   └── routes/
│       ├── __init__.py
│       ├── runs.py             # POST/GET /v1/runs, PUT company-intake
│       └── ui.py               # GET /v1/runs/{id}/ui
├── core/
│   ├── __init__.py
│   ├── schemas.py              # ALL Pydantic models
│   ├── config.py               # Config loader + freeze logic
│   ├── run_manager.py          # Run state machine
│   └── events.py               # Trace event type enum
├── services/
│   ├── __init__.py
│   └── trace.py                # Trace event emitter (local JSONL)
├── config/
│   └── defaults.yaml           # All knobs, weights, budgets
├── data/
│   └── wins_kb_seed/           # Empty dir, populated in Sprint 2
├── engines/
│   ├── __init__.py             # Empty, populated in Sprint 4+5
│   ├── thought/                # Placeholder for Sprint 4
│   └── pitch/                  # Placeholder for Sprint 5
├── tests/
│   ├── __init__.py
│   ├── test_schemas.py
│   ├── test_config.py
│   ├── test_run_manager.py
│   └── test_api.py
├── logs/                       # Trace JSONL files (gitignored)
├── requirements.txt
├── .gitignore
├── .env.example
└── SPRINT_PLAN.md              # Already exists
```

Total new files: ~20. Most are small (<100 lines).

---

## File-by-file spec

### 1. `core/schemas.py` — ALL Pydantic models

Every entity in the system. Sprint 1 defines them all. Later sprints use them.

```python
# --- Run ---
class BudgetConfig(BaseModel):
    external_search_query_budget: int    # hard cap on Google Search queries
    external_search_max_calls: int       # defense-in-depth cap on grounding calls
    rag_query_budget: int                # max RAG retrievals
    rag_top_k: int                       # results per RAG query
    rag_min_score: float                 # minimum relevance threshold

class BudgetState(BaseModel):
    external_search_queries_used: int = 0
    external_search_calls_used: int = 0
    rag_queries_used: int = 0

class RunStatus(str, Enum):
    CREATED = "created"
    INTAKE = "intake"
    ASSUMPTIONS_DRAFT = "assumptions_draft"
    ASSUMPTIONS_CONFIRMED = "assumptions_confirmed"
    REASONING = "reasoning"
    SYNTHESIS = "synthesis"
    REPORT = "report"
    PUBLISHED = "published"
    FAILED = "failed"

class Run(BaseModel):
    run_id: str                          # uuid4
    status: RunStatus
    created_at: datetime
    config_snapshot: dict                 # frozen config at run creation
    budgets: BudgetConfig
    budget_state: BudgetState
    company_intake: CompanyIntake | None = None
    assumptions: AssumptionsDraft | None = None

# --- Company intake ---
class CompanyIntake(BaseModel):
    company_name: str
    industry: str
    employee_count_band: str | None = None  # e.g. "100-500"
    notes: str | None = None
    constraints: list[str] = []

# --- Assumptions ---
class Assumption(BaseModel):
    field: str                            # e.g. "primary_workflows"
    value: str                            # model's guess
    confidence: float                     # 0-1
    source: str                           # "grounding" | "user" | "inferred"

class AssumptionsDraft(BaseModel):
    assumptions: list[Assumption]
    open_questions: list[str]             # things the model couldn't determine

# --- Evidence ---
class EvidenceSource(str, Enum):
    WINS_KB = "wins_kb"
    GOOGLE_SEARCH = "google_search"
    USER_PROVIDED = "user_provided"

class EvidenceItem(BaseModel):
    evidence_id: str                      # uuid4
    run_id: str
    source_type: EvidenceSource
    source_ref: str                       # chunk_id or grounding_chunk uri
    title: str
    uri: str | None = None                # for google_search sources
    snippet: str                          # bounded length
    relevance_score: float                # 0-1
    confidence_score: float | None = None # from grounding metadata
    retrieval_meta: dict = {}             # query, rank, timestamps

# --- Opportunity ---
class OpportunityTier(str, Enum):
    EASY = "easy"           # direct match to past win
    MEDIUM = "medium"       # needs adaptation
    HARD = "hard"           # ambitious, novel

class Opportunity(BaseModel):
    opportunity_id: str
    run_id: str
    template_id: str
    name: str
    description: str
    tier: OpportunityTier
    feasibility: float                    # 0-1
    roi: float                            # 0-1
    time_to_value: float                  # 0-1
    confidence: float                     # 0-1
    evidence_ids: list[str]               # links to EvidenceItem
    assumptions: dict                     # what this opp assumes
    rationale: str                        # why this tier
    adaptation_needed: str | None = None  # for medium tier
    risks: list[str] = []

# --- Stage output ---
class StageOutput(BaseModel):
    run_id: str
    stage_name: str
    version: int = 1
    created_at: datetime
    payload: dict                         # stage-specific data

# --- Trace event ---
class TraceEvent(BaseModel):
    event_id: str
    run_id: str
    timestamp: datetime
    event_type: str                       # from EventType enum
    payload: dict = {}

# --- Confidence ---
class FieldConfidence(BaseModel):
    field: str
    evidence_coverage: float              # 0-1
    evidence_strength: float              # 0-1
    source_diversity: float               # 0.5-1.0
    confidence: float                     # computed

class SectionConfidence(BaseModel):
    section: str
    field_confidences: list[FieldConfidence]
    missing_fields: list[str]
    confidence: float                     # computed with gap penalty

# --- UI contract ---
class UIAction(BaseModel):
    id: str
    label: str
    endpoint: str
    method: str                           # GET | POST | PUT
    enabled: bool = True
    confirm: bool = False

class EditableField(BaseModel):
    path: str                             # e.g. "company_intake.industry"
    label: str
    field_type: str                       # text | select | number
    default: str | None = None
    constraints: dict = {}

class BudgetView(BaseModel):
    rag_queries_remaining: int
    external_search_queries_remaining: int
    total_cost_estimate: str              # e.g. "$0.03"

class UIHints(BaseModel):
    stage_title: str
    stage_description: str
    progress: list[dict]                  # [{stage, status}]
    actions: list[UIAction]
    editable_fields: list[EditableField]
    budget_view: BudgetView
    agent_message: str | None = None      # MID question for user
```

### 2. `core/events.py` — Trace event types

```python
class EventType(str, Enum):
    # Run lifecycle
    RUN_CREATED = "RUN_CREATED"
    CONFIG_SNAPSHOT_SAVED = "CONFIG_SNAPSHOT_SAVED"
    BUDGETS_INITIALIZED = "BUDGETS_INITIALIZED"

    # Inputs
    COMPANY_INTAKE_SAVED = "COMPANY_INTAKE_SAVED"
    ASSUMPTIONS_DRAFT_CREATED = "ASSUMPTIONS_DRAFT_CREATED"
    ASSUMPTIONS_CONFIRMED = "ASSUMPTIONS_CONFIRMED"

    # Planning
    QUERY_PLAN_CREATED = "QUERY_PLAN_CREATED"

    # RAG (Sprint 2)
    RAG_QUERY_EXECUTED = "RAG_QUERY_EXECUTED"
    RAG_RESULTS_FILTERED = "RAG_RESULTS_FILTERED"

    # Grounding (Sprint 3)
    GROUNDING_CALL_REQUESTED = "GROUNDING_CALL_REQUESTED"
    GROUNDING_CALL_COMPLETED = "GROUNDING_CALL_COMPLETED"
    GROUNDING_QUERIES_COUNTED = "GROUNDING_QUERIES_COUNTED"
    EXTERNAL_BUDGET_EXHAUSTED = "EXTERNAL_BUDGET_EXHAUSTED"

    # Reasoning (Sprint 4)
    REASONING_LOOP_STARTED = "REASONING_LOOP_STARTED"
    REASONING_LOOP_COMPLETED = "REASONING_LOOP_COMPLETED"
    MID_GAP_DETECTED = "MID_GAP_DETECTED"
    USER_QUESTION_ASKED = "USER_QUESTION_ASKED"
    USER_ANSWER_RECEIVED = "USER_ANSWER_RECEIVED"

    # Synthesis (Sprint 5)
    OPPORTUNITIES_COMPUTED = "OPPORTUNITIES_COMPUTED"
    ROI_MODEL_COMPUTED = "ROI_MODEL_COMPUTED"
    CONFIDENCE_COMPUTED = "CONFIDENCE_COMPUTED"
    REPORT_RENDERED = "REPORT_RENDERED"

    # Terminal
    RUN_PUBLISHED = "RUN_PUBLISHED"
    STAGE_FAILED = "STAGE_FAILED"
    BUDGET_VIOLATION_BLOCKED = "BUDGET_VIOLATION_BLOCKED"
```

### 3. `config/defaults.yaml` — All knobs

```yaml
# Budget controls
budgets:
  external_search_query_budget: 5       # max Google Search queries total
  external_search_max_calls: 3          # max Gemini grounding calls
  rag_query_budget: 8                   # max RAG retrievals
  rag_top_k: 5                          # results per RAG query
  rag_min_score: 0.3                    # minimum relevance threshold

# Reasoning controls
reasoning:
  depth_budget: 3                       # max reasoning loops
  confidence_threshold: 0.7             # stop if overall confidence exceeds this

# Scoring weights (opportunity ranking)
scoring:
  w_roi: 0.30
  w_feasibility: 0.30
  w_ttv: 0.20
  w_confidence: 0.20

# Confidence formula weights
confidence:
  evidence_coverage_weight: 0.45
  evidence_strength_weight: 0.35
  source_diversity_weight: 0.20

# Model config
models:
  reasoning_model: "gemini-2.5-flash"   # thought engine
  synthesis_model: "gemini-2.5-pro"     # pitch synthesis
  grounding_model: "gemini-2.5-flash"   # Google Search grounding calls

# GCP
gcp:
  project_id: "plotpointe"
  location: "us-central1"
```

### 4. `core/config.py` — Config loader

- Load `config/defaults.yaml`
- Allow env var overrides for model names and GCP settings
- `freeze_config(overrides) -> dict` — returns immutable config snapshot for a run
- Config snapshot stored on the Run object, never mutated after creation

### 5. `core/run_manager.py` — Run state machine

- `create_run(company_name, industry, config_overrides) -> Run`
  - generates run_id (uuid4)
  - freezes config snapshot
  - sets status = CREATED
  - emits RUN_CREATED + CONFIG_SNAPSHOT_SAVED trace events
  - stores in memory (dict for now, Firestore in Sprint 7)
- `get_run(run_id) -> Run`
- `update_intake(run_id, intake: CompanyIntake) -> Run`
  - sets company_intake, transitions status to INTAKE
  - emits COMPANY_INTAKE_SAVED
- `transition(run_id, new_status) -> Run`
  - validates transition is legal (no skipping stages)
- Valid transitions:
  ```
  CREATED -> INTAKE -> ASSUMPTIONS_DRAFT -> ASSUMPTIONS_CONFIRMED
  -> REASONING -> SYNTHESIS -> REPORT -> PUBLISHED
  Any state -> FAILED
  ```

Storage: in-memory dict for Sprint 1. Swapped to Firestore later. The interface stays the same.

### 6. `api/app.py` — FastAPI entry

```python
app = FastAPI(title="AI Opportunity Mapper", version="0.1.0")
app.include_router(runs_router, prefix="/v1")

@app.get("/health")
def health():
    return {"status": "ok"}
```

### 7. `api/routes/runs.py` — Run endpoints

```
POST /v1/runs
  Body: { "company_name": "Acme Corp", "industry": "logistics" }
  Returns: Run object with run_id, status=created, budgets, config_snapshot
  Emits: RUN_CREATED, CONFIG_SNAPSHOT_SAVED, BUDGETS_INITIALIZED

GET /v1/runs/{run_id}
  Returns: full Run object

PUT /v1/runs/{run_id}/company-intake
  Body: CompanyIntake
  Returns: updated Run with status=intake
  Emits: COMPANY_INTAKE_SAVED
```

### 8. `api/routes/ui.py` — Backend-driven UI contract

```
GET /v1/runs/{run_id}/ui
  Returns: UIHints object

Logic:
  - Look at run.status
  - Return appropriate ui_hints for current stage:

  status=CREATED:
    stage_title: "Company Intake"
    actions: [{ id: "submit_intake", label: "Submit Company Info", endpoint: "/v1/runs/{id}/company-intake", method: "PUT" }]
    editable_fields: [
      { path: "company_name", label: "Company Name", type: "text" },
      { path: "industry", label: "Industry", type: "text" },
      { path: "employee_count_band", label: "Company Size", type: "select" },
      { path: "notes", label: "Additional Notes", type: "text" }
    ]
    budget_view: full budgets remaining

  status=INTAKE:
    stage_title: "Generating Assumptions"
    actions: [{ id: "start_reasoning", label: "Start Analysis", ... }]
    agent_message: null (no question yet)

  status=ASSUMPTIONS_DRAFT:
    stage_title: "Review Assumptions"
    actions: [{ id: "confirm_assumptions", ... }, { id: "edit_assumptions", ... }]
    editable_fields: assumptions as editable fields

  status=REASONING:
    stage_title: "Agent Reasoning"
    agent_message: MID question if pending
    actions: [{ id: "answer_question", ... }] if question pending

  ... and so on for each status
```

### 9. `services/trace.py` — Trace emitter

- `emit(run_id, event_type, payload) -> TraceEvent`
- Writes to `logs/{run_id}.jsonl` (one JSON line per event)
- Each line: `{"event_id": "...", "run_id": "...", "timestamp": "...", "event_type": "...", "payload": {...}}`
- Also stores in memory list for `GET /v1/runs/{id}/trace` endpoint (Sprint 7 adds Firestore)

### 10. `requirements.txt`

```
fastapi==0.115.0
uvicorn==0.30.0
pydantic==2.9.0
pyyaml==6.0.2
python-dotenv==1.0.1
```

Minimal. Only what Sprint 1 needs. Later sprints add chromadb, google-genai, etc.

### 11. `.gitignore`

```
.env
*.key
*.pem
service_account.json
logs/
__pycache__/
*.pyc
.venv/
venv/
node_modules/
.next/
.DS_Store
rag/store/
```

### 12. `.env.example`

```bash
MODEL_PROVIDER=vertex
GCP_PROJECT_ID=plotpointe
GCP_LOCATION=us-central1
REASONING_MODEL=gemini-2.5-flash
SYNTHESIS_MODEL=gemini-2.5-pro
GROUNDING_MODEL=gemini-2.5-flash
```

---

## Tests (Sprint 1)

### `test_schemas.py`
- Validate Run creation with all required fields
- Validate CompanyIntake accepts partial data (optional fields)
- Validate EvidenceItem with both source types
- Validate Opportunity with all three tiers
- Validate UIHints serializes correctly

### `test_config.py`
- Config loads from defaults.yaml
- Config freeze produces immutable dict
- Missing yaml file raises clear error

### `test_run_manager.py`
- create_run returns valid Run with status=CREATED
- update_intake transitions to INTAKE status
- Invalid transition raises error (e.g. CREATED -> REASONING)
- get_run returns stored run
- Budget state initializes to all zeros

### `test_api.py`
- POST /v1/runs returns 201 with run_id
- GET /v1/runs/{id} returns the run
- GET /v1/runs/{id}/ui returns UIHints with correct stage
- PUT /v1/runs/{id}/company-intake updates the run
- GET /health returns ok
- GET /v1/runs/nonexistent returns 404

---

## Commit plan (4 commits, solo-dev cadence)

```
1. feat(core): add pydantic schemas and config loader           (~80 lines)
   Files: core/schemas.py, core/events.py, core/config.py, config/defaults.yaml

2. feat(core): add run state machine with stage transitions     (~70 lines)
   Files: core/run_manager.py, services/trace.py

3. feat(api): add run endpoints and backend-driven ui contract  (~80 lines)
   Files: api/app.py, api/routes/runs.py, api/routes/ui.py

4. test(sprint1): add schema, config, run manager, api tests   (~80 lines)
   Files: tests/test_schemas.py, tests/test_config.py,
          tests/test_run_manager.py, tests/test_api.py
```

Plus repo skeleton files (.gitignore, .env.example, requirements.txt) in commit 1.

---

## Success criteria (from SPRINT_PLAN.md)

- [ ] `POST /v1/runs` creates a run with config snapshot and returns run_id
- [ ] `GET /v1/runs/{id}/ui` returns ui_hints with stage progress and next action
- [ ] All Pydantic schemas validate sample data without errors
- [ ] Config loads from YAML, freezes per run, is immutable after creation
- [ ] Trace events written to local JSONL for RUN_CREATED, CONFIG_SNAPSHOT_SAVED
- [ ] No hardcoded values — everything in config

---

## What this sprint does NOT touch

- No RAG (Sprint 2)
- No Gemini calls (Sprint 3)
- No reasoning loop (Sprint 4)
- No opportunity mapping (Sprint 5)
- No frontend (Sprint 6)
- No Cloud Logging / Firestore / Cloud Run (Sprint 7)
- No model calls of any kind
- Storage is in-memory dict — swapped later
