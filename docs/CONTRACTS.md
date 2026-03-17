# Interface Contracts

Every input/output contract in the system. Read the code if something looks wrong here.

Source of truth files: `orchestrator/schemas.py`, `orchestrator/state.py`, `agents/base.py`,
`ops/model_client.py`, `rag/vector_store.py`, `orchestrator/tool_registry.py`,
`infra/deploy_target.py`, `app.py`, `frontend/lib/types.ts`.

---

## Pipeline Stage Contracts

The pipeline runs 7 stages in sequence. Each stage reads from `PipelineState`,
writes its output back to state, and returns the updated state on success or
a failed state on error. The orchestrator function is:

```python
run_pipeline(url: str, dry_run: bool = False) -> PipelineState
```

Stage timeout: 60 seconds per stage (constant `_STAGE_TIMEOUT_S`).

---

### Stage 1: Website Scraper

Agent: `ScraperAgent` (agent_tag = `"SCRAPER"`)
Invoked via: `ToolRegistry.get("website_scraper").run(...)`

Input dict:
```python
{
  "url": str,       # company URL to scrape
  "dry_run": bool   # if True, returns fixture from tests/fixtures/sample_company.json
}
```

Output dict on success:
```python
{
  "url": str,
  "name": str,                  # derived from domain, e.g. "Acme"
  "about_text": str,            # up to 5000 chars from /about page
  "job_postings": list[str],    # single-element list with careers page text, or []
  "product_text": str,          # up to 5000 chars from /product or /solutions page
  "tech_stack_mentions": list,  # always [] currently (reserved field)
  "pages_fetched": list[str],   # URL paths that returned 200, e.g. ["/about", "/careers"]
  "last_scraped": None          # reserved, always None currently
}
```

Error codes:
- `SCRAPE_FAIL` - HTTP error during fetch (recoverable=True)
- `TIMEOUT` - stage exceeded 60s (recoverable=False)
- `UNHANDLED_EXCEPTION` - unexpected error (recoverable=False)

Gate after stage: `scraper_quality_gate(company_data)` - see Gates section.
State fields written: `state.company_data`, `state.pages_fetched`

---

### Stage 2: Signal Extractor

Agent: `SignalExtractorAgent` (agent_tag = `"SIGNAL_EXTRACTOR"`)
Model: `VERTEX_FAST_MODEL` env var (default: `gemini-2.5-flash`)
Prompt: `prompts/signal_extractor.md`

Input dict:
```python
{
  "company_data": dict  # output from Stage 1
}
```

Output dict on success (before validation):
```python
# Raw JSON from model, validated into SignalSet shape:
{
  "signals": list[Signal],
  "industry": str,
  "scale": str,
  "confidence_level": "HIGH" | "MEDIUM" | "LOW"
}
```

After `validate_signals()` runs, `confidence_level` and `signal_count` are
set by the validator (not trusted from model output).

Error codes:
- `MODEL_CALL_FAIL` - Vertex AI error (recoverable=True)
- `PARSE_FAIL` - model returned non-JSON (recoverable=True)
- `VALIDATION_FAIL` - output did not match SignalSet schema (recoverable=True)
- `TIMEOUT` - stage exceeded 60s (recoverable=False)

State fields written: `state.signals` (as `dict`), `state.signal_count`

---

### Stage 3: Maturity Scorer

Agent: `MaturityScorerAgent` (agent_tag = `"MATURITY_SCORER"`)
Model: `VERTEX_FAST_MODEL` env var (default: `gemini-2.5-flash`)
Prompt: `prompts/maturity_scorer.md`

Input dict:
```python
{
  "signals": dict  # state.signals (the SignalSet dict from Stage 2)
}
```

Output dict on success (before validation):
```python
# Raw JSON from model, validated into MaturityResult shape:
{
  "dimensions": {
    "data_infrastructure": DimensionScore,
    "ml_ai_capability": DimensionScore,
    "strategy_intent": DimensionScore,
    "operational_readiness": DimensionScore
  },
  "composite_score": float,
  "composite_label": str,  # e.g. "Emerging"
  "composite_rationale": str
}
```

Validation requires all 4 dimension keys to be present. Missing any one
returns `VALIDATION_FAIL`.

Error codes:
- `MODEL_CALL_FAIL` - Vertex AI error (recoverable=True)
- `PARSE_FAIL` - model returned non-JSON (recoverable=True)
- `VALIDATION_FAIL` - missing required dimensions (recoverable=True)
- `TIMEOUT` - stage exceeded 60s (recoverable=False)

State fields written: `state.maturity` (as `dict`)

---

### Stage 4: RAG Query

Agent: `RAGQueryAgent` (agent_tag = `"RAG"`)
No model call. Queries vector store directly.

Input dict:
```python
{
  "company_data": dict  # output from Stage 1 (state.company_data)
}
```

Internal: builds a structured query string from `about_text` and `job_postings`,
detects industry from keyword matching, then calls `VectorStore.query(text, k=3)`.

Output on success:
```python
list[dict]  # up to 3 records from vector store
            # each record has at minimum: id, embed_text, industry
            # may also have: size_label, maturity_at_engagement, results,
            #                industry_benchmark, gap_analysis_template, etc.
```

Error codes:
- `VECTOR_QUERY_FAIL` - ChromaDB error (recoverable=True)
- `TIMEOUT` - stage exceeded 60s (recoverable=False)

State fields written: `state.rag_context`

---

### Stage 5: Victory Matcher

Function (not an agent - no model call): `match_victories(...)`
Deterministic scoring only.

```python
match_victories(
    signals_industry: str,
    signals_scale: str,
    maturity_label: str,
    rag_results: list[dict],
    company_composite_score: float = 0.0,
) -> list[VictoryMatch]
```

Reads: `state.signals["industry"]`, `state.signals["scale"]`,
`state.maturity["composite_label"]`, `state.rag_context`, `state.maturity["composite_score"]`

Output: sorted `list[VictoryMatch]` - sorted by tier then similarity score descending.

Scoring rules:
- `industry_score`: 0.4 (exact match), 0.2 (related cluster), 0.0 (unrelated)
- `maturity_score`: 0.4 (same label), 0.2 (adjacent), 0.0 (distant)
- `size_score`: 0.2 (same), 0.1 (adjacent), 0.0 (different)
- `DIRECT_MATCH`: total >= 0.7 AND industry_score > 0
- `CALIBRATION_MATCH`: total >= 0.4
- `ADJACENT_MATCH`: total < 0.4

Never returns an error. Returns an empty list if `rag_results` is empty.

State fields written: `state.victory_matches` (list of dicts via `.model_dump()`)

---

### Stage 6: Use Case Generator

Agent: `UseCaseGeneratorAgent` (agent_tag = `"USE_CASE_GENERATOR"`)
Model: `VERTEX_MODEL` env var (default: `gemini-2.5-pro`)
Prompt: `prompts/use_case_generator.md`

Input dict:
```python
{
  "signals": dict,          # state.signals
  "maturity": dict,         # state.maturity
  "victory_matches": list   # state.victory_matches
}
```

Output on success (before validation):
```python
list[dict]  # array of UseCase objects
            # model returns JSON array, or {"use_cases": [...]}
```

Validation rules:
- Must have at least 2 use cases, else `VALIDATION_FAIL`
- Any use case with `tier == "HARD_EXPERIMENT"` has `confidence` capped at 0.65

Error codes:
- `MODEL_CALL_FAIL` - Vertex AI error (recoverable=True)
- `PARSE_FAIL` - model returned non-JSON (recoverable=True)
- `VALIDATION_FAIL` - fewer than 2 use cases or schema mismatch (recoverable=True)
- `TIMEOUT` - stage exceeded 60s (recoverable=False)

State fields written: `state.use_cases` (list of dicts via `.model_dump()`),
`state.analysis` (backward-compat dict for report writer)

---

### Stage 7: Report Writer

Agent: `ReportWriterAgent` (agent_tag = `"REPORT"`)
Model: `VERTEX_FAST_MODEL` env var (default: `gemini-2.5-flash`)
Prompt: `prompts/report_writer.md`

Runs 5 sections concurrently (max 3 workers). Each section is one separate model call.

Method used by pipeline (not `_run`):
```python
generate_section(section_name: str, analysis: dict) -> str | AgentError
```

- `section_name` must be one of: `exec_summary`, `current_state`, `use_cases`,
  `roadmap`, `roi_analysis`
- Returns plain text string on success

Input to each section call (`analysis` dict):
```python
{
  "maturity_score": float,
  "maturity_label": str,
  "dimensions": dict,
  "signals": dict,
  "use_cases": list,
  "victory_matches": list
}
```

Output on success:
```python
{
  "exec_summary": str | None,
  "current_state": str | None,
  "use_cases": str | None,
  "roadmap": str | None,
  "roi_analysis": str | None
}
```

If a section fails, its key is set to `None` (pipeline does not halt on partial
section failure). If the executor itself fails, falls back to single-call
`ReportWriterAgent.run({"analysis": analysis})`.

Error codes (from `generate_section`):
- `INVALID_SECTION` - unknown section name (recoverable=False)
- `MODEL_CALL_FAIL` - Vertex AI error (recoverable=True)

State fields written: `state.report`

---

## Schema Definitions

All schemas are Pydantic models in `orchestrator/schemas.py`.

### Signal
```python
class Signal(BaseModel):
    signal_id: str = ""      # assigned by validate_signals() if empty, e.g. "sig-001"
    type: Literal[
        "tech_stack", "data_signal", "ml_signal",
        "intent_signal", "ops_signal", "industry_hint", "scale_hint"
    ]
    value: str
    source: Literal["about_text", "job_posting", "product_page", "careers_page"]
    confidence: float = 1.0
    raw_quote: str = ""
```

### SignalSet
```python
class SignalSet(BaseModel):
    signals: list[Signal]
    industry: str = "unknown"
    scale: str = "unknown"
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    signal_count: int = 0   # overwritten by validate_signals()
```

### DimensionScore
```python
class DimensionScore(BaseModel):
    score: float
    signals_used: list[str] = []
    rationale: str = ""
```

### MaturityResult
```python
class MaturityResult(BaseModel):
    dimensions: dict[str, DimensionScore]  # must include all 4 required keys
    composite_score: float
    composite_label: str    # one of: Beginner, Developing, Emerging, Advanced, Leading
    composite_rationale: str = ""
```

Required dimension keys: `data_infrastructure`, `ml_ai_capability`,
`strategy_intent`, `operational_readiness`.

### VictoryMatch
```python
class VictoryMatch(BaseModel):
    win_id: str
    engagement_title: str
    match_tier: Literal["DIRECT_MATCH", "CALIBRATION_MATCH", "ADJACENT_MATCH"]
    relevance_note: str = ""
    roi_benchmark: str = ""
    industry: str = ""
    similarity_score: float = 0.0
    confidence: float = 0.5
    gap_analysis: str | None = None
```

### DataFlow
```python
class DataFlow(BaseModel):
    data_inputs: list[str] = []
    model_approach: str = ""
    output_consumer: str = ""
    feedback_loop: str = ""
    value_measurement: str = ""
```

### UseCase
```python
class UseCase(BaseModel):
    tier: Literal["LOW_HANGING_FRUIT", "MEDIUM_SOLUTION", "HARD_EXPERIMENT"]
    title: str
    description: str = ""
    evidence_signal_ids: list[str] = []
    effort: Literal["Low", "Medium", "High"] = "Medium"
    impact: Literal["Low", "Medium", "High"] = "Medium"
    roi_estimate: str = ""
    roi_basis: str = ""
    rag_benchmark: str | None = None
    confidence: float = 0.5   # capped at 0.65 for HARD_EXPERIMENT by validator
    why_this_company: str = ""
    data_flow: DataFlow = DataFlow()
```

---

## PipelineState

Working memory for one pipeline run. Lives in `orchestrator/state.py`.
Created at start of `run_pipeline()`, returned when pipeline ends.

```python
class PipelineState(BaseModel):
    run_id: str           # 8-char UUID prefix, e.g. "a1b2c3d4"
    url: str = ""
    dry_run: bool = False

    # Stage outputs - None until that stage completes
    company_data: dict | None = None
    rag_context: list[dict] | None = None
    analysis: dict | None = None      # backward compat only
    report: dict | None = None

    # Sprint 4+ stage outputs
    signals: dict | None = None
    maturity: dict | None = None
    victory_matches: list[dict] | None = None
    use_cases: list[dict] | None = None

    # Scraper metadata
    pages_fetched: list[str] | None = None
    signal_count: int | None = None

    # Run metadata
    status: PipelineStatus    # PENDING | RUNNING | COMPLETE | FAILED
    error: dict | None = None # {"code": str, "message": str, "agent": str}
    cost_usd: float = 0.0
    elapsed_seconds: float = 0.0
```

### PipelineStatus
```python
class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
```

---

## Abstraction Layer Contracts

### BaseAgent

All pipeline agents inherit from `BaseAgent` (in `agents/base.py`).

```python
class BaseAgent(ABC):
    agent_tag: str = "BASE"   # override in each subclass

    @property
    def dry_run(self) -> bool:
        # reads DRY_RUN env var

    def run(self, input_data: dict) -> Any | AgentError:
        # public method - never raises, wraps _run()

    @abstractmethod
    def _run(self, input_data: dict) -> Any:
        # implement in subclass
```

Callers use `run()`, never `_run()` directly.
`run()` catches all exceptions and returns `AgentError(code="UNHANDLED_EXCEPTION", ...)`.

### AgentError

```python
@dataclass
class AgentError:
    code: str           # error code string - see per-agent codes above
    message: str        # human-readable description
    recoverable: bool = True   # True = retry may help, False = fatal
    agent_tag: str = ""        # which agent produced this error
```

Never raised. Always returned. Callers check `isinstance(result, AgentError)`.

### ModelClient

Abstract interface in `ops/model_client.py`. All model calls go through this.

```python
class ModelClient(ABC):
    def complete(self, prompt: str, system: str = "", model: str = "") -> str | AgentError:
        # prompt: the user turn content
        # system: system instruction (optional)
        # model: override model name (optional, defaults to env var)
        # returns: raw text string on success, AgentError on failure
```

Implementations: `VertexProvider`, `MockProvider`
Factory: `get_model_client() -> ModelClient`
- Returns `MockProvider` if `DRY_RUN=true`
- Returns `VertexProvider` if `MODEL_PROVIDER=vertex` (default)
- Returns `MockProvider` as fallback for unknown providers

`VertexProvider` strips markdown code fences from responses before returning.
Response MIME type is `application/json`, temperature=0.2.

### VectorStore

Abstract interface in `rag/vector_store.py`. All RAG operations go through this.

```python
class VectorStore(ABC):
    def add(self, docs: list[dict]) -> None | AgentError:
        # docs: list of dicts with optional keys: "id", "text", plus any metadata
        # id defaults to str(index) if missing
        # text defaults to json.dumps(doc) if missing
        # returns None on success, AgentError on failure

    def query(self, text: str, k: int = 3) -> list[dict] | AgentError:
        # text: query string
        # k: number of results (default 3)
        # returns: list of result dicts, each with "text" key plus any metadata
```

Implementations: `ChromaStore`, `MockStore`
Factory: `get_vector_store() -> VectorStore`
- Returns `MockStore` if `DRY_RUN=true`
- Returns `ChromaStore` if `VECTOR_STORE=chroma` (default)

`ChromaStore` persists to `CHROMA_PERSIST_DIR` env var (default: `./rag/store`).
Collection name: `ai_solutions`.

Error codes from ChromaStore:
- `VECTOR_ADD_FAIL` - add operation failed (recoverable=True, agent_tag="RAG")
- `VECTOR_QUERY_FAIL` - query operation failed (recoverable=True, agent_tag="RAG")

### Tool / ToolRegistry

Defined in `orchestrator/tool_registry.py`.

```python
class Tool(ABC):
    tool_id: str   # class attribute, must be set in subclass

    def run(self, input_data: dict) -> dict | AgentError:
        # same contract as BaseAgent.run()
        # never raises
```

```python
class ToolRegistry:
    def register(self, tool: Tool) -> None:
        # keyed by tool.tool_id

    def get(self, tool_id: str) -> Tool:
        # raises KeyError if tool_id not registered

    def list_ids(self) -> list[str]:
        # returns all registered tool IDs
```

Singleton: `from orchestrator.tool_registry import registry`
Registered tools at import time: `website_scraper` (wraps ScraperAgent)

### DeployTarget

Abstract interface in `infra/deploy_target.py`.

```python
class DeployTarget(ABC):
    def deploy(self, image_uri: str) -> DeployResult:
        # image_uri: container image URI
        # returns DeployResult

    def get_service_url(self) -> str | None:
        # returns live URL or None

    def health_check(self) -> bool:
        # returns True if /health returns 200
```

```python
@dataclass
class DeployResult:
    success: bool
    service_url: str | None
    revision: str | None
    error: str | None
```

Implementation: `GCPCloudRunTarget`
Factory: `get_deploy_target() -> DeployTarget`
- Returns `GCPCloudRunTarget` if `DEPLOY_TARGET=gcp` (default)
- Raises `ValueError` for unknown targets

`GCPCloudRunTarget` uses `gcloud` CLI. Requires `GCP_PROJECT_ID`, `GCP_LOCATION` env vars.
Service: `ai-transform-agent`, region: `us-central1`, image: `gcr.io/plotpointe/ai-transform-agent:latest`

### JudgeClient

Defined in `evals/judge_client.py`. Used only by eval pipeline, not by main pipeline.

```python
class JudgeClient:
    def score(self, rubric_path: str, output: dict) -> float:
        # rubric_path: path to YAML rubric file with "judge_prompt_template" key
        # output: dict of values to substitute into template
        # returns: float 1.0-5.0, or 0.0 on any error
        # never raises
```

Model: `EVAL_JUDGE_MODEL` env var (default: `gemini-2.5-pro`)
Max output tokens: 256
Expects `SCORE: X` pattern in model response.
Returns 0.0 on init failure, missing rubric, template error, or no SCORE pattern found.

---

## API Contracts

### POST /v1/analyze

Request body (`AnalyzeRequest`):
```json
{
  "url": "https://example.com",
  "dry_run": false
}
```

Success response (HTTP 200, `AnalyzeSuccess`):
```json
{
  "run_id": "a1b2c3d4",
  "status": "complete",
  "elapsed_seconds": 45.2,
  "cost_usd": 0.011,
  "report": {
    "exec_summary": "...",
    "current_state": "...",
    "use_cases": "...",
    "roadmap": "...",
    "roi_analysis": "..."
  },
  "analysis": {
    "maturity_score": 2.8,
    "maturity_label": "Developing",
    "dimensions": {...},
    "use_cases": [...]
  },
  "rag_context": [...],
  "signals": {...},
  "maturity": {...},
  "victory_matches": [...],
  "use_cases": [...],
  "pages_fetched": ["/about", "/careers"],
  "signal_count": 7
}
```

Error response (HTTP 422 for thin scrape, HTTP 500 for all others):
```json
{
  "detail": {
    "error": {
      "code": "SCRAPE_THIN",
      "message": "Scraped content too thin (23 words)...",
      "agent": "SCRAPER"
    }
  }
}
```

Status code mapping:
- `SCRAPE_THIN` code - 422
- All other failures - 500

---

### GET /v1/trace/{run_id}

Path parameter: `run_id` - must match `^[a-zA-Z0-9\-]+$`

Success response (HTTP 200):
```json
{
  "run_id": "a1b2c3d4",
  "stages": [
    { ...jsonl log entry... },
    { ...jsonl log entry... }
  ]
}
```

Error responses:
- HTTP 400: invalid `run_id` format
- HTTP 404: no log file found for that `run_id`

Log entries are read from `logs/runs/{run_id}.jsonl`. Each line is one JSON object.

---

### GET /health

No parameters.

Success response (HTTP 200, `HealthResponse`):
```json
{
  "status": "healthy",
  "version": "sprint6",
  "model_provider": "vertex",
  "pipeline": "ready"
}
```

Values come from env vars: `SERVICE_VERSION` (default: `"sprint6"`),
`MODEL_PROVIDER` (default: `"vertex"`).

---

## Validation and Gate Contracts

### scraper_quality_gate

```python
scraper_quality_gate(company_data: dict) -> tuple[bool, str]
```

Returns `(True, "")` on pass. Returns `(False, reason)` on fail.

Fail conditions (in order checked):
1. `company_data` is empty/falsy - "Scraper returned empty data."
2. Combined word count of `about_text + product_text + careers_text + job_postings` < 50
3. Combined text contains error keywords (`404 not found`, `access denied`, `page not found`,
   `403 forbidden`, `robot`, `captcha`, `cloudflare`) AND word count < 200
4. No `about_text` AND no `job_postings` - content is present but useless

Fired by: pipeline after Stage 1. On fail, pipeline aborts with `SCRAPE_THIN` error code.
Only fires in live mode (skipped when `dry_run=True`).

---

### validate_signals

```python
validate_signals(result: dict, agent_tag: str = "SIGNAL_EXTRACTOR") -> SignalSet | AgentError
```

- Parses raw dict into `SignalSet`
- Assigns `signal_id` to any signal missing one (format: `sig-001`, `sig-002`, ...)
- Sets `signal_count = len(signals)`
- Sets `confidence_level`: `HIGH` if >= 6 signals, `MEDIUM` if >= 3, `LOW` otherwise
- Returns `AgentError(code="VALIDATION_FAIL", recoverable=True)` if parsing fails

---

### validate_maturity

```python
validate_maturity(result: dict, agent_tag: str = "MATURITY_SCORER") -> MaturityResult | AgentError
```

- Parses raw dict into `MaturityResult`
- Checks for all 4 required dimension keys
- Returns `AgentError(code="VALIDATION_FAIL", recoverable=True)` if any required
  dimension is missing or parsing fails

Required dimensions: `data_infrastructure`, `ml_ai_capability`,
`strategy_intent`, `operational_readiness`

---

### validate_use_cases

```python
validate_use_cases(result: list[dict], agent_tag: str = "USE_CASE_GENERATOR") -> list[UseCase] | AgentError
```

- Parses each dict into a `UseCase`
- Requires at least 2 use cases
- Caps `confidence` at 0.65 for any use case with `tier == "HARD_EXPERIMENT"`
- Returns `AgentError(code="VALIDATION_FAIL", recoverable=True)` on schema mismatch
  or fewer than 2 use cases

---

## Frontend Type Contract

Key TypeScript interfaces in `frontend/lib/types.ts` that mirror backend schemas.

```typescript
interface Signal {
  signal_id: string;
  type: string;
  value: string;
  source: string;
  confidence: number;
  raw_quote: string;
}

interface SignalSet {
  signals: Signal[];
  industry: string;
  scale: string;
  confidence_level: "HIGH" | "MEDIUM" | "LOW";
  signal_count: number;
}

interface DimensionScore {
  score: number;
  signals_used: string[];
  rationale: string;
}

interface MaturityResult {
  dimensions: Record<string, DimensionScore>;
  composite_score: number;
  composite_label: string;
  composite_rationale: string;
}

interface TieredUseCase {
  tier: "LOW_HANGING_FRUIT" | "MEDIUM_SOLUTION" | "HARD_EXPERIMENT";
  title: string;
  description: string;
  evidence_signal_ids: string[];
  effort: "Low" | "Medium" | "High";
  impact: "Low" | "Medium" | "High";
  roi_estimate: string;
  roi_basis: string;
  rag_benchmark: string | null;
  confidence: number;
  why_this_company: string;
  data_flow: DataFlow;
}

interface VictoryMatch {
  win_id: string;
  engagement_title: string;
  match_tier: "DIRECT_MATCH" | "CALIBRATION_MATCH" | "ADJACENT_MATCH";
  relevance_note: string;
  roi_benchmark: string;
  industry: string;
  similarity_score: number;
  confidence: number;
  gap_analysis?: string;
}

interface ReportSections {
  exec_summary: string;
  current_state: string;
  use_cases: string;
  roadmap: string;
  roi_analysis: string;
}

interface AnalyzeSuccess {
  run_id: string;
  status: "complete";
  elapsed_seconds: number;
  cost_usd: number;
  report: ReportSections;
  maturity: MaturityResult;
  signals?: SignalSet;
  victory_matches?: VictoryMatch[];
  use_cases?: TieredUseCase[];
  analysis?: { maturity_score?: number; maturity_label?: string; ... };
  rag_context?: VictoryMatch[];
  pages_fetched?: string[];
  signal_count?: number;
}
```

Error parsing: `parseApiError(body: unknown) -> string`
- Backend wraps errors as `{ detail: { error: { code, message, agent } } }`
- Frontend maps error codes to user-facing messages via `ERROR_CODE_MAP`
- Known codes: `SCRAPE_FAIL`, `SCRAPE_THIN`, `RAG_ERROR`, `CONSULTANT_ERROR`,
  `REPORT_ERROR`, `UNKNOWN`

`AnalyzeResponse = AnalyzeSuccess | AnalyzeError`

---

## AgentError Contract Reference

```python
@dataclass
class AgentError:
    code: str
    message: str
    recoverable: bool = True
    agent_tag: str = ""
```

Error codes by agent:

| Agent tag         | Code                  | recoverable | When                                      |
|-------------------|-----------------------|-------------|-------------------------------------------|
| SCRAPER           | SCRAPE_FAIL           | True        | HTTP error during fetch                   |
| SCRAPER           | UNHANDLED_EXCEPTION   | False       | Unexpected error in _run()                |
| SCRAPER           | TIMEOUT               | False       | Stage exceeded 60s                        |
| SIGNAL_EXTRACTOR  | MODEL_CALL_FAIL       | True        | Vertex AI call failed                     |
| SIGNAL_EXTRACTOR  | PARSE_FAIL            | True        | Model returned non-JSON                   |
| SIGNAL_EXTRACTOR  | VALIDATION_FAIL       | True        | Output did not match SignalSet            |
| SIGNAL_EXTRACTOR  | TIMEOUT               | False       | Stage exceeded 60s                        |
| MATURITY_SCORER   | MODEL_CALL_FAIL       | True        | Vertex AI call failed                     |
| MATURITY_SCORER   | PARSE_FAIL            | True        | Model returned non-JSON                   |
| MATURITY_SCORER   | VALIDATION_FAIL       | True        | Missing required dimensions               |
| MATURITY_SCORER   | TIMEOUT               | False       | Stage exceeded 60s                        |
| RAG               | VECTOR_QUERY_FAIL     | True        | ChromaDB query failed                     |
| RAG               | TIMEOUT               | False       | Stage exceeded 60s                        |
| USE_CASE_GENERATOR| MODEL_CALL_FAIL       | True        | Vertex AI call failed                     |
| USE_CASE_GENERATOR| PARSE_FAIL            | True        | Model returned non-JSON                   |
| USE_CASE_GENERATOR| VALIDATION_FAIL       | True        | Fewer than 2 use cases or schema mismatch |
| USE_CASE_GENERATOR| TIMEOUT               | False       | Stage exceeded 60s                        |
| REPORT            | INVALID_SECTION       | False       | Unknown section name passed               |
| REPORT            | MODEL_CALL_FAIL       | True        | Vertex AI call failed                     |
| REPORT            | PARSE_FAIL            | True        | Model returned non-JSON (single-call path)|
| REPORT            | INCOMPLETE_REPORT     | True        | Missing sections (single-call path)       |
| OPS               | MODEL_CALL_FAIL       | True        | Vertex AI SDK error in VertexProvider     |
| RAG               | VECTOR_ADD_FAIL       | True        | ChromaDB add failed                       |
| PIPELINE          | SCRAPE_THIN           | False       | Scraper quality gate failed               |
| any               | UNHANDLED_EXCEPTION   | False       | BaseAgent.run() caught unexpected error   |

The pipeline's `_fail()` helper sets `state.status = FAILED` and stores the
error in `state.error = {"code": ..., "message": ..., "agent": ...}`.

The pipeline does NOT retry on any error. `recoverable` is informational -
the caller (or a future retry layer) would use it to decide whether to retry.
