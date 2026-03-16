# Sprint 4 — The Rational Strategist

**Author:** PM agent  
**Date:** 2026-03-16  
**Status:** Draft — pending Sai review at sprint council  
**North star:** The system thinks like an AI strategist, not a search engine with a prompt.

---

## AI Native Data Flow — Cross-Cutting Architectural Requirement

**Status:** Required for Sprint 4. DISC-39 is the foundation ticket. All other tickets
in this sprint depend on it.

### What "AI Native" Means Here

Every inter-agent handoff in this pipeline must be a structured, validated artifact
— not a string blob, not an untyped dict, not a JSON string that only gets parsed
at the destination. Each agent receives exactly the fields it needs, in the shape it
expects, validated before it ever touches agent code.

This is enforced by Pydantic models in `orchestrator/schemas.py`. If an agent returns
data that does not conform to its schema, Pydantic rejects it before it enters pipeline
state. The orchestrator retries once. If retry fails, a clean `AgentError` is raised.

### Schema Contracts

All schemas live in `orchestrator/schemas.py`. These are the canonical definitions.
Agent output comments and prompt files reference these types by name.

```python
class Signal(BaseModel):
    signal_id: str          # sig-001, sig-002 ... (orchestrator assigns)
    type: Literal["tech_stack", "data_signal", "ml_signal", "intent_signal",
                  "ops_signal", "industry_hint", "scale_hint"]
    value: str              # "BigQuery", "hiring ML Engineer"
    source: Literal["about_text", "job_posting", "product_page", "careers_page"]
    confidence: float = 1.0
    raw_quote: str = ""     # the verbatim text this signal was extracted from

class SignalSet(BaseModel):
    signals: list[Signal]
    industry: str = "unknown"
    scale: str = "unknown"
    signal_count: int = 0   # len(signals) — orchestrator enforces consistency

class DimensionScore(BaseModel):
    score: float            # 0.0–5.0, must be a valid 0.5 increment
    signals_used: list[str] # signal_ids from the SignalSet that support this score
    rationale: str          # 1–2 sentences citing specific signals

class MaturityResult(BaseModel):
    dimensions: dict[str, DimensionScore]  # keys: data_infrastructure, ml_ai_capability,
                                           #        strategy_intent, operational_readiness
    composite_score: float
    composite_label: str    # Beginner / Developing / Emerging / Advanced / Leading
    composite_rationale: str  # 50 words minimum

class VictoryMatch(BaseModel):
    win_id: str
    engagement_title: str
    match_tier: Literal["DIRECT_MATCH", "CALIBRATION_MATCH", "ADJACENT_MATCH"]
    relevance_note: str
    roi_benchmark: str      # e.g. "14% fuel cost reduction"
    industry: str
    similarity_score: float
    confidence: float       # floor set by match_tier (0.75 / 0.55 / 0.40)

class DataFlow(BaseModel):
    data_inputs: list[str]      # "TMS shipment history (18 months)", "GPS telemetry (needed)"
    model_approach: str          # "XGBoost regression for route scoring"
    output_consumer: str         # "Dispatchers via TMS planning interface"
    feedback_loop: str           # "Weekly retraining on actual vs predicted delivery outcomes"
    value_measurement: str       # "Monthly fuel cost vs prior year baseline"

class UseCase(BaseModel):
    tier: Literal["LOW_HANGING_FRUIT", "MEDIUM_SOLUTION", "HARD_EXPERIMENT"]
    title: str
    description: str
    evidence_signal_ids: list[str]   # signal_ids from SignalSet that ground this use case
    effort: Literal["Low", "Medium", "High"]
    impact: Literal["Low", "Medium", "High"]
    roi_estimate: str
    roi_basis: str          # "Based on win-001: 14% fuel cost reduction"
    rag_benchmark: str | None  # win_id or None for HARD_EXPERIMENT
    confidence: float
    why_this_company: str   # specific to this company — not a generic statement
    data_flow: DataFlow          # AI native data flow — maps client's existing systems to solution
```

**Why `signal_id` matters:**
Signal IDs are the traceability thread. `DimensionScore.signals_used` lists signal IDs.
`UseCase.evidence_signal_ids` lists signal IDs. A human reading the output can trace
every score and every use case back to a verbatim quote in the original scraped text
via `Signal.raw_quote`. This is not optional — it is how we prove the system is not
hallucinating.

### Orchestrator Validation Gates

After each agent returns, the orchestrator runs a typed validation function before
promoting output to pipeline state. These live in `orchestrator/validators.py`.

Pattern:

```python
def validate_signals(result: dict) -> SignalSet:
    """Validate signal extractor output and promote to pipeline state."""
    signal_set = SignalSet(**result)  # Pydantic validates structure
    if len(signal_set.signals) < 3:
        raise ValueError(f"Too few signals: {len(signal_set.signals)}")
    # assign signal_ids if agent did not
    for i, sig in enumerate(signal_set.signals):
        if not sig.signal_id:
            sig.signal_id = f"sig-{i+1:03d}"
    signal_set.signal_count = len(signal_set.signals)
    return signal_set
```

On validation failure: append the Pydantic error message to the prompt and retry once.
On second failure: raise `AgentError` — pipeline stops, clean error returned to caller.

One validator per pipeline stage:

| Validator function    | Validates            | Key guard                                    |
|-----------------------|----------------------|----------------------------------------------|
| `validate_signals`    | `SignalSet`          | >= 3 signals, at least 1 industry_hint       |
| `validate_maturity`   | `MaturityResult`     | all 4 dimensions present, composite formula  |
| `validate_victories`  | `list[VictoryMatch]` | tier values valid, confidence floors held    |
| `validate_use_cases`  | `list[UseCase]`      | >= 2 use cases, first is LOW_HANGING_FRUIT   |
| `validate_report`     | report dict          | all 5 sections non-null, min length checks   |

### Input Context Logging

Every agent call logs what context it received. This is the primary debugging tool.

```python
logger.log(agent_tag, "input_context",
    keys=list(input_data.keys()),
    signal_count=len(input_data.get("signals", [])),
    content_hash=hashlib.md5(
        json.dumps(input_data, sort_keys=True).encode()
    ).hexdigest()[:8]
)
```

The `content_hash` lets you confirm whether two runs received identical input —
critical for diagnosing non-determinism.

### Section-Scoped Context for Report Writer

The report writer does not receive a blob. The orchestrator builds five separate
input dicts, one per section. Each section sees only what it needs.

```python
report_input = {
    "exec_summary_context": {
        "composite_score": maturity.composite_score,
        "composite_label": maturity.composite_label,
        "top_use_case": use_cases[0].model_dump(),
    },
    "current_state_context": {
        "signals": [s.model_dump() for s in signal_set.signals],
        "dimensions": {k: v.model_dump() for k, v in maturity.dimensions.items()},
    },
    "use_cases_context": {
        "use_cases": [uc.model_dump() for uc in use_cases],
        "victory_matches": [vm.model_dump() for vm in victory_matches],
    },
    "roi_context": {
        "use_cases": [uc.model_dump() for uc in use_cases[:3]],
        "victory_matches": [vm.model_dump() for vm in victory_matches],
    },
    "roadmap_context": {
        "maturity": maturity.model_dump(),
        "first_use_case": use_cases[0].model_dump(),
        "second_use_case": use_cases[1].model_dump() if len(use_cases) > 1 else None,
    },
}
```

The model writing the exec summary cannot see ROI figures. The model writing
the roadmap cannot see raw signals. Context scoping is the mechanism that makes
section outputs internally consistent.

### How Each Ticket Changes

| Ticket  | Schema requirement                                                             |
|---------|-------------------------------------------------------------------------------|
| DISC-39 | Creates `orchestrator/schemas.py` (incl. `ToolResult`) + `orchestrator/validators.py` + `orchestrator/tool_registry.py` — foundational |
| DISC-40 | `WebsiteScraperTool` returns `ToolResult`. `SignalExtractorAgent` receives `list[ToolResult]`, returns `SignalSet`. Each signal includes `signal_id` and `raw_quote`. |
| DISC-41 | Returns `MaturityResult`. `signals_used` per dimension are signal IDs.        |
| DISC-42 | Returns `list[VictoryMatch]`. `match_tier` required on every record.          |
| DISC-43 | Returns `list[UseCase]`. `evidence_signal_ids`, `why_this_company`, and `data_flow` required on every item.|
| DISC-44 | Report writer receives section-scoped context dict. One key per report section.|

DISC-39 must complete before DISC-40 begins. All tickets use the types defined
in DISC-39 — they do not define their own schema inline.

---

## Tool Registry & Multi-Source Architecture

**Status:** Required for Sprint 4. Expands DISC-39. Sai's direction: "We need more agents
for signal scraping reliably." The key architectural insight drives the design: scraping is
a TOOL concern (fetch data), signal extraction is an AGENT concern (reason over data).
Multiple tools feed into one agent. Adding a new data source = adding a new tool, not
changing the pipeline.

### The Core Distinction

| Layer | Concern | Changes when |
|-------|---------|--------------|
| Tools | Fetch data from external sources | New data source added |
| SignalExtractorAgent | Reason over fetched data, produce typed signals | Extraction quality improves |
| Rest of pipeline | Unchanged | Not affected by new data sources |

This separation means: adding a LinkedIn Jobs scraper in Sprint 5 requires writing ONE tool
class and registering it. The signal extractor, maturity scorer, victory matcher, and report
writer do not change at all. The orchestrator automatically routes the new tool's output
into the signal extraction step.

### Tool Base Class

All data-fetching tools inherit from `Tool` in `orchestrator/tool_registry.py`:

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Literal

class ToolResult(BaseModel):
    """Standard output contract for all tools. Every tool returns this."""
    tool_id: str                    # "website_scraper", "job_board", "news_search"
    source_type: Literal[
        "website", "job_board", "news", "tech_detector", "company_profile"
    ]
    content: dict                   # tool-specific structured content
    pages_fetched: list[str]        # URLs actually fetched (empty list if N/A)
    fetch_timestamp: str            # ISO 8601
    success: bool
    error: str | None = None        # populated on partial or full failure

class Tool(ABC):
    """Base class for all data-fetching tools."""
    tool_id: str                    # must be unique, snake_case

    @abstractmethod
    def fetch(self, input_data: dict) -> ToolResult:
        """Fetch data from external source. Returns ToolResult.
        
        Never raises — always returns ToolResult with success=False on error.
        Callers check success before using content.
        """
        ...
```

### ToolRegistry

```python
class ToolRegistry:
    """Register and discover tools. Orchestrator calls these."""
    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, tool: Tool) -> None:
        cls._tools[tool.tool_id] = tool

    @classmethod
    def get(cls, tool_id: str) -> Tool:
        if tool_id not in cls._tools:
            raise KeyError(f"Tool not found: {tool_id}")
        return cls._tools[tool_id]

    @classmethod
    def get_all(cls, category: str | None = None) -> list[Tool]:
        """Return all registered tools, optionally filtered by source_type category."""
        tools = list(cls._tools.values())
        if category:
            tools = [t for t in tools if hasattr(t, 'source_type') and t.source_type == category]
        return tools

    @classmethod
    def list_ids(cls) -> list[str]:
        return list(cls._tools.keys())
```

### ToolResult in orchestrator/schemas.py

`ToolResult` lives in `orchestrator/schemas.py` alongside the pipeline schemas.
It is the output contract for all tools, and the input type for `SignalExtractorAgent`.

```python
class ToolResult(BaseModel):
    tool_id: str
    source_type: Literal["website", "job_board", "news", "tech_detector", "company_profile"]
    content: dict
    pages_fetched: list[str]
    fetch_timestamp: str
    success: bool
    error: str | None = None
```

### Updated Orchestrator Flow

```
TOOL LAYER (orchestrator calls registered tools):
  1. Orchestrator calls ToolRegistry.get_all() → list of registered tools
  2. For each tool: tool.fetch({"url": company_url}) → ToolResult
  3. Orchestrator collects raw_sources: list[ToolResult]
  4. Failed tools (success=False) are logged and excluded from raw_sources
  5. If all tools fail → AgentError raised before signal extraction

AGENT LAYER (unchanged pipeline):
  6. SignalExtractorAgent receives raw_sources: list[ToolResult]
  7. Agent reasons over ALL sources → SignalSet
  8. Steps 2–5 of the pipeline proceed exactly as before
```

### Sprint 4: One Tool, Full Architecture

Sprint 4 ships with ONE registered tool: `WebsiteScraperTool`. This is the existing
scraper logic refactored to implement the `Tool` interface. The architecture is complete
and extensible — Sprint 5 can add new tools without touching any existing code.

**What changes in Sprint 4:**
- `agents/scraper.py` logic extracted into `tools/website_scraper.py` — implements `Tool`
- `orchestrator/tool_registry.py` created with `Tool`, `ToolRegistry`, `ToolResult`
- Orchestrator calls `WebsiteScraperTool.fetch()` → `list[ToolResult]` instead of calling ScraperAgent directly
- `SignalExtractorAgent` receives `raw_sources: list[ToolResult]`, not `company_data: dict`
- `agents/scraper.py` kept as a thin wrapper calling `WebsiteScraperTool` for backward compat

**What does NOT change:**
- Signal extraction logic (same signals, same types, same schema)
- Maturity scoring, victory matching, use case generation, report writing
- All existing tests (scraper wrapper maintains the same public interface)
- Dry-run behavior (tool returns fixture data in dry-run mode)

### WebsiteScraperTool

The existing `ScraperAgent` scraping logic becomes `WebsiteScraperTool`:

```python
class WebsiteScraperTool(Tool):
    tool_id = "website_scraper"

    def fetch(self, input_data: dict) -> ToolResult:
        url = input_data["url"]
        # same logic as current scraper.py: /about, /careers, /product
        # returns ToolResult with content = {
        #   "about_text": str,
        #   "job_postings": list[str],
        #   "product_text": str,
        #   "tech_mentions": list[str]
        # }
```

The `content` dict from `WebsiteScraperTool` is identical to the current `company_data`
dict from `ScraperAgent`. This makes the transition backward-compatible at the content level
— only the wrapper type changes from `dict` to `ToolResult`.

### How SignalExtractorAgent Reads Multiple Sources

When multiple tools are registered, the signal extractor receives a list of `ToolResult`
objects. Each source is clearly labeled by `tool_id` and `source_type`. The prompt
instructs the model to read each source independently before synthesizing signals:

```
Sources available:
  [website_scraper] About page, careers page, product pages
  [job_board] 12 active job postings from LinkedIn
  [news_search] 3 recent press articles

Extract signals from ALL sources. Label each signal's source field with the
source_type it was extracted from. If the same signal appears in multiple sources,
cite the highest-confidence source and note corroboration.
```

The `Signal.source` field literal set is extended in Sprint 5 to include `"job_board"`,
`"news"` etc. In Sprint 4, only `"website"` sources are active.

### Future Tools (Sprint 5+)

These tools can be added without changing ANY existing pipeline code:

| Tool ID | Source Type | What it fetches | Signals it enriches |
|---------|------------|-----------------|---------------------|
| `job_board_tool` | `job_board` | Active job listings from LinkedIn/Indeed | `ml_signals`, `tech_stack`, `scale_hint` |
| `news_search_tool` | `news` | Recent press releases, news articles | `intent_signals`, `scale_hint` |
| `tech_detector_tool` | `tech_detector` | BuiltWith data, GitHub public repos, API docs | `tech_stack`, `ops_signals` |
| `company_profile_tool` | `company_profile` | Employee count, funding, industry from business data APIs | `scale_hint`, `industry_hint` |

**Adding a tool in Sprint 5 is exactly 3 steps:**
1. Write the tool class implementing `Tool.fetch()` → `ToolResult`
2. Register it: `ToolRegistry.register(MyNewTool())`
3. Done — orchestrator calls it automatically, signals get richer

No orchestrator changes. No schema changes. No prompt changes.
The signal extractor automatically processes the new source because it iterates
over `raw_sources: list[ToolResult]` — it does not have a hardcoded source list.

---

## What Changes in Sprint 4

Sprint 3 shipped the victory citation system. The pipeline now says
"based on win-001, we achieved 14% fuel cost reduction." That is a
meaningful upgrade over generic benchmarks.

Sprint 3's remaining gap: the consultant agent receives everything at once
and produces everything at once. Raw scraped text, three victory records,
and a prompt that says "score maturity AND identify use cases AND cite wins
AND estimate ROI." That is four jobs in one model call.

This violates how a real strategist thinks. A strategist does not look at
a company website and immediately generate a recommendation. They observe
first. Then assess. Then match. Then recommend. Each step uses only what
the previous step produced.

Sprint 4 redesigns the consultant stage to follow that rational process.

---

## Part 1 — The Rational Process of an AI Strategist

This is the step-by-step reasoning flow a Tenex consultant would follow
when evaluating a new prospect. Every agent in Sprint 4 corresponds to
one step.

### Step 1 — Observe: Signal Extraction

**What the strategist does:**  
Read the raw content. Extract discrete, factual observations. No opinions.
No recommendations. Just: what do I see?

**Why this step exists as its own agent:**  
Raw scraped HTML is noisy. Job titles are buried in paragraph text. Tech
stack signals are mixed with marketing copy. A model asked to score maturity
AND extract signals simultaneously will miss signals. A model whose only
job is to extract signals will catch more.

**What it reads:**  
- `raw_sources: list[ToolResult]`: output from all registered tools
  - Sprint 4: one item — `WebsiteScraperTool` (about_text, job_postings, product_text, tech_mentions)
  - Sprint 5+: may include job board, news, tech detector — no prompt or agent changes needed
- Each `ToolResult` is labeled by `tool_id` and `source_type` so the model knows the provenance

**What it writes:**  
- `signals`: a structured `SignalSet` of typed, discrete observations
- Each signal carries `signal_id`, `raw_quote`, and `source` (mapped from `ToolResult.source_type`)

**What it does NOT receive:**  
- Victory records (not needed yet — this is observation only)
- Prior analysis (no anchoring bias)
- Any instructions about what to recommend

**Signal types:**

```
tech_stack     → named tools, platforms, cloud vendors mentioned
                 Example: { type: "tech_stack", value: "Snowflake", source: "about_text" }

data_signals   → evidence of data infrastructure, volume, pipelines
                 Example: { type: "data_signals", value: "processes 50M events daily", source: "about_page" }

ml_signals     → evidence of ML capability: roles, pilots, deployed models, vendors
                 Example: { type: "ml_signals", value: "hiring ML Engineer", source: "job_posting" }

intent_signals → strategy and roadmap language about AI
                 Example: { type: "intent_signals", value: "AI-first product roadmap mentioned in CEO letter", source: "about_text" }

ops_signals    → infrastructure and deployment capability signals
                 Example: { type: "ops_signals", value: "Kubernetes-based microservices", source: "tech_mentions" }

industry_hint  → what industry this company operates in (inferred from content)
                 Example: { type: "industry_hint", value: "logistics", confidence: 0.9 }

scale_hint     → company size signals
                 Example: { type: "scale_hint", value: "mid-market", evidence: "200-500 employees mentioned" }
```

**What the orchestrator validates before promoting:**  
- At least 3 signals total
- At least one `industry_hint` signal
- No hallucinated tool names (all tech_stack values traceable to source field)
- No recommendations or scores in the output (wrong job)

---

### Step 2 — Assess: Maturity Scoring

**What the strategist does:**  
Given the signals extracted in Step 1, score each dimension independently.
Then compute the composite. This is judgment applied to structured facts,
not judgment applied to raw text.

**Why this step exists as its own agent:**  
When the current consultant scores maturity from raw text, it anchors on
whatever it reads first. A BigQuery mention near the top inflates data
infrastructure. A recent AI press release inflates strategy. Scoring from
structured, typed signals prevents this anchoring. Each dimension gets
the signals relevant to it, not the whole document.

**What it reads:**  
- `signals`: the typed signal list from Step 1 only
- `analysis_spec`: the dimension scoring criteria (passed as context in the prompt)

**What it writes:**  
- `maturity`: dimension scores + composite + rationale per dimension

**What it does NOT receive:**  
- Victory records (irrelevant to scoring the company's current state)
- Raw scraped text (already extracted in Step 1)

**Maturity output schema:**

```json
{
  "dimensions": {
    "data_infrastructure": { "score": 2.5, "signals_used": ["Snowflake", "50M events daily"], "rationale": "..." },
    "ml_ai_capability":    { "score": 1.5, "signals_used": ["hiring ML Engineer"], "rationale": "..." },
    "strategy_intent":     { "score": 2.0, "signals_used": ["AI-first roadmap"], "rationale": "..." },
    "operational_readiness":{ "score": 2.0, "signals_used": ["Kubernetes"], "rationale": "..." }
  },
  "composite_score": 2.0,
  "composite_label": "Developing",
  "composite_rationale": "string — 50 words minimum citing dimension evidence"
}
```

**What the orchestrator validates before promoting:**  
- All four dimensions present
- Composite score matches the weighted formula (±0.5 tolerance)
- Each dimension cites at least one signal from the signal list
- Score is a valid increment (0.0, 0.5, 1.0 ... 5.0)

---

### Step 3 — Match: Victory Retrieval with Relevance Reasoning

**What the strategist does:**  
Given what we know about this company (signals + maturity), search for
relevant Tenex wins. For each match, reason explicitly about WHY it is
relevant and what confidence the match deserves.

**Why this step is more than cosine similarity:**  
ChromaDB returns the top-k by vector distance. A win with 0.62 similarity
might be the same industry, same size, same problem — a strong match.
A win with 0.71 similarity might be same industry but the company is
5x bigger — a calibration input, not a direct match. Cosine similarity
alone does not distinguish these. A relevance reasoning pass does.

**What it reads:**  
- `signals`: typed signal list from Step 1
- `maturity`: output from Step 2
- `raw_rag_results`: the top-k victory records returned by ChromaDB

**What it writes:**  
- `victory_matches`: annotated victory records, each with a relevance tier
  and explicit reasoning

**Victory match tiers:**

```
DIRECT_MATCH:
  Conditions: same industry AND same size_label AND maturity difference <= 1.0
  Effect: this win becomes the PRIMARY ROI benchmark
  Confidence floor: 0.75

CALIBRATION_MATCH:
  Conditions: same industry BUT different size OR maturity gap > 1.0
  Effect: this win informs ROI direction but requires adjustment
  Confidence floor: 0.55

ADJACENT_MATCH:
  Conditions: different industry but problem type overlaps (e.g., logistics vs manufacturing — both have scheduling problems)
  Effect: this win suggests a use case category is viable, specific numbers require adjustment
  Confidence floor: 0.40
```

**Victory match output schema:**

```json
{
  "victory_matches": [
    {
      "win_id": "win-001",
      "engagement_title": "Route Optimization for Regional LTL Carrier",
      "match_tier": "DIRECT_MATCH",
      "relevance_note": "Same industry (logistics), same size tier (mid-market), maturity at engagement was Developing — matches this prospect",
      "roi_benchmark": { "metric": "14% fuel cost reduction", "basis": "4 months post-deployment" },
      "similarity_score": 0.82,
      "confidence": 0.80
    }
  ]
}
```

**What the orchestrator validates before promoting:**  
- At least 1 victory match (if zero, pipeline continues with ADJACENT_MATCH
  or lower confidence — not a failure)
- Every match tier is one of the three valid values
- Confidence values consistent with tier floors

---

### Step 4 — Recommend: Use Case Generation with Low/Medium/Hard Tiers

**What the strategist does:**  
Given signals, maturity, and matched victories — what should this company do?
Organize recommendations by implementation confidence and effort.

This is the core of what makes the consultant valuable. Not "here are
use cases" but "here is what you can do NOW (low-hanging fruit), what
requires investment (medium), and what is a bet worth taking (hard experiment)."

**Why three tiers instead of one ranked list:**  
A CFO and a CTO read the recommendation differently. The CFO wants to know
what has worked before and what it will cost. The CTO wants to know what is
possible at the frontier. Three tiers serve both audiences. The tier
classification also drives confidence calibration: low-hanging fruit is
cited with high confidence, hard experiments with lower confidence but
explicit upside framing.

**What it reads:**  
- `signals`: typed signal list from Step 1
- `maturity`: dimension scores from Step 2
- `victory_matches`: annotated matches from Step 3 — this is the ONLY source for ROI figures

**What it writes:**  
- `use_cases`: list of use cases with tier classification, ROI, and victory citation

**Tier classification rules:**

```
LOW_HANGING_FRUIT:
  Criteria:
    - At least one DIRECT_MATCH victory in the same industry
    - The use case maps to the victory's problem type
    - Effort is Low (buildable in 4-8 weeks from existing data)
  ROI grounding: use the DIRECT_MATCH victory's primary metric directly
  Confidence: >= 0.75 (floor set by DIRECT_MATCH tier)
  What this tells the consultant: "We have done this. Here are the numbers."

MEDIUM_SOLUTION:
  Criteria:
    - DIRECT_MATCH or CALIBRATION_MATCH exists but requires scaling or adaptation
    - OR two or more strong signals converge on a use case with no direct match
    - Effort is Medium (3-6 months, some data engineering required)
  ROI grounding: use CALIBRATION_MATCH victory adjusted for size/scale
  Confidence: 0.55–0.74
  What this tells the consultant: "We have done something similar. The numbers require adjustment."

HARD_EXPERIMENT:
  Criteria:
    - No direct or calibration victory match
    - Strong convergent signals suggest opportunity (2+ signal types pointing at same use case)
    - The use case is technically feasible given the company's maturity
    - Effort is High (6+ months, new capabilities required)
  ROI grounding: cite ADJACENT_MATCH or state "industry trend basis"
  Confidence: 0.35–0.54
  What this tells the consultant: "We have not done exactly this, but the signals are strong."
```

**Use case output schema:**

```json
{
  "use_cases": [
    {
      "tier": "LOW_HANGING_FRUIT",
      "title": "Carrier Selection Automation Using Historical Shipment Data",
      "description": "Deploy a scoring model on existing shipment history to automate carrier selection",
      "evidence": "Job posting references 'large-scale shipment data in BigQuery'; current process described as manual",
      "effort": "Low",
      "impact": "High",
      "roi_estimate": "12% reduction in per-shipment carrier cost",
      "roi_basis": "win-002 (DIRECT_MATCH) — same industry, same size, 12% carrier cost savings",
      "rag_benchmark": "win-002",
      "confidence": 0.82
    },
    {
      "tier": "MEDIUM_SOLUTION",
      "title": "Demand Forecasting for Warehouse Staffing",
      "description": "...",
      "tier_rationale": "win-010 (CALIBRATION_MATCH) — same use case, larger company; metric adjusted downward for scale",
      "confidence": 0.61
    },
    {
      "tier": "HARD_EXPERIMENT",
      "title": "Real-Time Route Optimization with Dynamic Traffic Integration",
      "description": "...",
      "tier_rationale": "No direct match. Strong signals: GPS telemetry mentioned, TMS infrastructure in place, scale supports live inference.",
      "confidence": 0.45
    }
  ]
}
```

**What the orchestrator validates before promoting:**  
- At least 1 LOW_HANGING_FRUIT use case (if no DIRECT_MATCH exists, requires
  PM review — Tier 2 escalation)
- Minimum 2, maximum 5 total use cases
- All LOW_HANGING_FRUIT items cite a `win_id` in `rag_benchmark`
- No HARD_EXPERIMENT item has confidence > 0.65
- First use case is LOW_HANGING_FRUIT (orchestrator enforces ordering)

---

### Step 5 — Write: Report Generation

**What the strategist does:**  
Take the validated artifacts from Steps 1-4 and write the 5-section report.
The report writer's job is prose composition, not analysis. All the hard
thinking is already done.

**Why this separation matters:**  
The current report writer receives `analysis` — a dict that includes maturity
scores, use cases, and raw notes all at once. The writer has to interpret
what it means and decide what to emphasize. That produces inconsistent
emphasis and occasionally contradicts the consultant analysis.

In Sprint 4, the report writer receives four clean, validated artifacts:
`signals`, `maturity`, `victory_matches`, `use_cases`. Each section draws
from specific artifacts.

**What it reads (section-by-section scoping):**

```
exec_summary    → maturity.composite_score + use_cases[0] only
                  (the highest-priority use case and the score — nothing else)

current_state   → signals + maturity.dimensions
                  (what we observed + what it means — no use cases yet)

use_cases       → use_cases[] + victory_matches[]
                  (structured per-use-case with tier, ROI, and victory citation)

roi_analysis    → use_cases[0:3] + victory_matches (for basis statements)
                  (top 3 use cases only — quantified, with math shown)

roadmap         → maturity + use_cases[0] + use_cases[1]
                  (build Phase 1 from the lowest-effort use case, Phase 2 from the next)
```

**What it does NOT receive:**  
- Raw scraped text (already processed in Step 1)
- Full victory records (only the matched victories are needed)
- The other sections' content (no cross-contamination)

This is the same output schema as today. No changes to the report JSON contract.

---

## Part 2 — Agent Contracts

### SignalExtractorAgent

```
Input:
  raw_sources: list[ToolResult]   # output from all registered tools (Sprint 4: WebsiteScraperTool only)
                                   # each ToolResult has: tool_id, source_type, content, pages_fetched

Output:
  signals: list[SignalRecord]     # SignalSet validated by validate_signals
  # SignalRecord = { signal_id, type, value, source, confidence, raw_quote }

Prompt file:   prompts/signal_extractor.md
Model:         gemini-2.5-flash (signal extraction is structured, fast task)
Dry-run:       return signals from tests/fixtures/sample_signals.json
Timeout:       20 seconds (faster than consultant — structured extraction)

Context it does NOT receive:
  - No victory records
  - No maturity scoring criteria
  - No recommendation instructions

Note: The agent iterates over ALL ToolResult items in raw_sources.
Each source is clearly labeled by tool_id and source_type in the prompt.
In Sprint 4, raw_sources contains exactly one item (website_scraper).
In Sprint 5+, it may contain multiple items — no code changes needed.
```

### MaturityScorerAgent

```
Input:
  signals: list[SignalRecord]  # from SignalExtractorAgent only

Output:
  maturity: MaturityResult
  # MaturityResult = { dimensions: {dim: {score, signals_used, rationale}}, composite_score, composite_label, composite_rationale }

Prompt file:   prompts/maturity_scorer.md
Model:         gemini-2.5-flash (scoring from structured input — well-defined task)
Dry-run:       return maturity from tests/fixtures/sample_maturity.json
Timeout:       20 seconds

Context it does NOT receive:
  - No raw scraped text
  - No victory records
  - No use case instructions
```

### VictoryMatcherAgent  (currently: RAGQueryAgent — extended, not replaced)

```
Input:
  signals: list[SignalRecord]
  maturity: MaturityResult
  raw_rag_results: list[dict]  # top-k from ChromaDB (tool output)

Output:
  victory_matches: list[VictoryMatch]
  # VictoryMatch = { win_id, engagement_title, match_tier, relevance_note, roi_benchmark, similarity_score, confidence }

Note: ChromaDB query is a TOOL call, not an agent call.
  The orchestrator calls the vector store tool to get raw_rag_results.
  VictoryMatcherAgent receives tool output + signals + maturity — reasons over them.

Prompt file:   prompts/victory_matcher.md
Model:         gemini-2.5-flash (relevance reasoning — structured input/output)
Dry-run:       return victory_matches from tests/fixtures/sample_victory_matches.json
Timeout:       25 seconds

Context it does NOT receive:
  - No raw scraped text
  - No use case generation instructions
```

### UseCaseGeneratorAgent  (currently: part of ConsultantAgent)

```
Input:
  signals: list[SignalRecord]
  maturity: MaturityResult
  victory_matches: list[VictoryMatch]

Output:
  use_cases: list[UseCase]
  # UseCase = { tier, title, description, evidence, effort, impact, roi_estimate, roi_basis, rag_benchmark, confidence }

Prompt file:   prompts/use_case_generator.md
Model:         gemini-2.5-pro (this is the highest-reasoning step — frontier model)
Dry-run:       return use_cases from tests/fixtures/sample_use_cases.json
Timeout:       40 seconds (higher — reasoning-intensive)

Context it does NOT receive:
  - No raw scraped text
  - No report writing instructions
  - No section formatting
```

### ReportWriterAgent  (existing — input changes only)

```
Input (changed from current):
  signals: list[SignalRecord]      # replaces raw company_data
  maturity: MaturityResult         # same structure, now separate artifact
  victory_matches: list[VictoryMatch]
  use_cases: list[UseCase]

Output (unchanged):
  report: { exec_summary, current_state, use_cases, roi_analysis, roadmap }

Prompt file:   prompts/report_writer.md  (version bumped to 3.0)
Model:         gemini-2.5-flash (prose generation — already fast)
Dry-run:       existing fixture
Timeout:       40 seconds
```

---

## Part 3 — Context Routing Diagram

This shows what information each agent sees, and critically, what it does NOT see.

```
TOOL LAYER (orchestrator calls registered tools before agent pipeline):
  URL → ToolRegistry.get_all()
          → WebsiteScraperTool.fetch(url) → ToolResult(tool_id="website_scraper", ...)
          [future Sprint 5+: JobBoardTool, NewsSearchTool, TechDetectorTool]
         ↓
         Orchestrator merges: raw_sources = [ToolResult, ToolResult, ...]
         Failed tools logged and excluded. If ALL fail → AgentError.
         ↓
         [scraper_quality_gate] ← deterministic, checks raw_sources non-empty
         ↓ PASS

STEP 1: SIGNAL EXTRACTION
  Input:  raw_sources: list[ToolResult]   ← NOT company_data dict
  Agent:  SignalExtractorAgent
  Output: signals[]
  ─────────────────────────────────────────────────────────────
  DOES NOT SEE: victory records, maturity criteria, use cases

STEP 2: MATURITY SCORING
  Input:  signals[] only
  Agent:  MaturityScorerAgent
  Output: maturity { dimensions{}, composite_score, label }
  ─────────────────────────────────────────────────────────────
  DOES NOT SEE: raw text, victory records, use case instructions

STEP 3: RAG QUERY (tool) + VICTORY MATCHING (agent)
  Tool:   vector_store.query(query_text) → raw_rag_results[]
           query_text built from: signals.industry_hint + signals.scale_hint + top 3 signals
  Input:  signals[] + maturity + raw_rag_results[]
  Agent:  VictoryMatcherAgent
  Output: victory_matches[] with tier, relevance_note, confidence
  ─────────────────────────────────────────────────────────────
  DOES NOT SEE: raw scraped text, use case instructions, report format

STEP 4: USE CASE GENERATION
  Input:  signals[] + maturity + victory_matches[]
  Agent:  UseCaseGeneratorAgent
  Output: use_cases[] with tier LOW/MEDIUM/HARD, ROI, victory citation
  ─────────────────────────────────────────────────────────────
  DOES NOT SEE: raw scraped text, report sections, other use cases' prose

STEP 5: REPORT WRITING
  Input (scoped per section):
    exec_summary  ← maturity + use_cases[0]
    current_state ← signals + maturity.dimensions
    use_cases     ← use_cases[] + victory_matches[]
    roi_analysis  ← use_cases[0:3] + victory_matches[]
    roadmap       ← maturity + use_cases[0:2]
  Agent:  ReportWriterAgent
  Output: report { 5 sections }
  ─────────────────────────────────────────────────────────────
  DOES NOT SEE: raw scraped text, intermediate reasoning

ORCHESTRATOR COMMITS STATE AT EACH STEP:
  state.signals          ← after Step 1 validates
  state.maturity         ← after Step 2 validates
  state.victory_matches  ← after Step 3 validates
  state.use_cases        ← after Step 4 validates
  state.report           ← after Step 5 validates
```

---

## Part 4 — Low/Medium/Hard Classification Design

### Classification Logic

The three tiers are determined by two inputs: the victory match tier from Step 3
and the effort/complexity of the use case given the company's current maturity.

```
                           VICTORY MATCH TIER
                    DIRECT      CALIBRATION   ADJACENT / NONE
                   ──────────────────────────────────────────
EFFORT    Low    │ LOW_HANGING  MEDIUM        MEDIUM
                 │ FRUIT
          Medium │ MEDIUM       MEDIUM        HARD_EXPERIMENT
          High   │ MEDIUM       HARD_EXPERIMENT  HARD_EXPERIMENT
```

The effort rating itself is derived from the company's maturity:

```
Maturity Beginner (0.0–1.0):
  Low effort = use existing spreadsheet/export data, model fits in 4 weeks
  Medium effort = requires first data pipeline — realistic in 3 months
  High effort = anything requiring ML infrastructure from scratch

Maturity Developing (1.0–2.0):
  Low effort = scoring model on existing warehouse data
  Medium effort = real-time feature store or new integration
  High effort = foundation model deployment or multi-system ML pipeline

Maturity Emerging (2.0–3.0):
  Low effort = productionizing an existing pilot
  Medium effort = scaling to new business unit
  High effort = replatforming to ML-first architecture

Maturity Advanced+ (3.0–5.0):
  Low effort = additive features to existing ML platform
  Medium effort = new domain requiring new data collection
  High effort = frontier research or proprietary model development
```

### UI Visibility Rule

The tier classification is a first-class UI concept, not metadata.
Each use case card in the frontend shows its tier as a colored label:

```
LOW_HANGING_FRUIT   → green label  — "Proven"
MEDIUM_SOLUTION     → amber label  — "Achievable"
HARD_EXPERIMENT     → blue label   — "Frontier"
```

A Tenex consultant showing this to a CFO reads the green cards first.
The CFO knows the green ones have real precedent. The blue ones are bets.
This is the product insight that makes Sprint 4 visible and useful.

### Confidence Display

Each use case shows its confidence as a percentage in the UI.
Below 0.55: show a "lower confidence" indicator.
Above 0.75: no indicator (confident recommendation).

---

## Part 5 — Sprint 4 Tickets

### Execution Order

```
DISC-39 [BE] Pydantic schema contracts + tool registry + orchestrator validation gates  ← NEW, blocks all
    ↓
DISC-40 [BE] Signal extractor agent + scraper-to-tool refactor + new pipeline state fields
    ↓
DISC-41 [BE] Maturity scorer refactor — signals in, scores out
    ↓
DISC-42 [BE] Victory matcher agent — relevance reasoning over RAG results
    ↓
DISC-43 [BE] Use case generator agent — three-tier classification
    ↓
DISC-44 [FE] Three-tier use case UI — Low/Medium/Hard cards
    ↓ (parallel after DISC-43)
DISC-45 [QA] Sprint 4 eval — tier classification accuracy + report coherence
```

---

### DISC-39 — [BE] Pydantic Schema Contracts + Orchestrator Validation Gates

**Priority:** P0 — foundation for every other Sprint 4 ticket. Nothing proceeds without this.
**Execute with:** Primary: backend
**Blocked by:** nothing

**User story:**
As the pipeline orchestrator, I need every inter-agent handoff to be a typed,
validated artifact so that a schema violation is caught immediately at the
boundary — before bad data propagates to the next agent and produces a
confidently wrong output.

**What it builds:**

`orchestrator/schemas.py` — new file:
- `Signal`, `SignalSet`, `DimensionScore`, `MaturityResult`, `VictoryMatch`, `DataFlow`, `UseCase`
- `ToolResult` — standard output contract for all tools (see Tool Registry section above)
- All schemas as defined in the "AI Native Data Flow" and "Tool Registry" sections above
- `model_config = ConfigDict(extra="forbid")` on every model — no silent extra fields
- Typed literals for `type`, `source`, `match_tier`, `tier`, `effort`, `impact`, `source_type`

`orchestrator/tool_registry.py` — new file:
- `Tool` abstract base class with `tool_id: str` and `fetch(input_data: dict) -> ToolResult`
- `ToolRegistry` class: `register()`, `get()`, `get_all()`, `list_ids()`
- `WebsiteScraperTool` — implements `Tool`, wraps existing scraper logic
  - `tool_id = "website_scraper"`
  - `fetch()` returns `ToolResult` with `content` dict matching current `company_data` structure
  - Dry-run: returns `ToolResult` built from `tests/fixtures/sample_company.json`
- Bootstrap call at pipeline startup: `ToolRegistry.register(WebsiteScraperTool())`

`orchestrator/validators.py` — new file:
- `validate_signals(result: dict) -> SignalSet`
- `validate_maturity(result: dict) -> MaturityResult`
- `validate_victories(result: dict | list) -> list[VictoryMatch]`
- `validate_use_cases(result: dict | list) -> list[UseCase]`
- `validate_report(result: dict) -> dict`
- Each validator: (1) Pydantic parse, (2) business rule checks, (3) signal_id
  auto-assignment where needed, (4) raises `AgentError` on second failure
- Retry logic: on first `ValidationError`, return the error string so the
  orchestrator can append it to the prompt and retry the agent call

`orchestrator/pipeline.py` updated:
- Import and call validators at each step transition
- Add `input_context` logging call before each agent invocation (see pattern above)
- Section-scoped report_input dict built from typed `.model_dump()` calls

`requirements.txt` updated:
- `pydantic>=2.0` added (Pydantic v2 — not v1)

`tests/test_schemas.py` — new test file:
- Round-trip tests: valid input passes, invalid input raises `ValidationError`
- Extra field test: schema rejects extra keys
- Business rule tests: `validate_signals` rejects < 3 signals, `validate_use_cases`
  enforces first item is LOW_HANGING_FRUIT, `validate_victories` enforces confidence floors

**done_when:**
`tests/test_schemas.py` passes. `orchestrator/schemas.py`, `orchestrator/validators.py`,
and `orchestrator/tool_registry.py` exist and are importable. `from orchestrator.schemas
import Signal, SignalSet, MaturityResult, VictoryMatch, UseCase, ToolResult` works without
error. `from orchestrator.tool_registry import ToolRegistry, WebsiteScraperTool` works
without error. All existing tests green.

**Acceptance criteria:**
- `orchestrator/schemas.py` exists with all 6 pipeline models plus `ToolResult`
- All models use `extra="forbid"` — no silent extra fields
- `orchestrator/tool_registry.py` exists with `Tool` ABC, `ToolRegistry`, `WebsiteScraperTool`
- `WebsiteScraperTool.fetch()` returns `ToolResult` with same `content` structure as current `company_data`
- `WebsiteScraperTool` dry-run mode returns `ToolResult` built from `tests/fixtures/sample_company.json`
- `orchestrator/validators.py` exists with 5 validator functions
- Retry pattern implemented: validator returns `(None, error_str)` on first fail,
  raises `AgentError` on second
- `tests/test_schemas.py` covers: valid round-trip, extra field rejection,
  business rule enforcement per validator, `ToolResult` schema validation
- `tests/test_tool_registry.py` covers: `WebsiteScraperTool.fetch()` returns correct `ToolResult` shape,
  failed fetch returns `ToolResult(success=False)` not an exception, registry `get_all()` returns
  registered tools, dry-run returns fixture data
- `pydantic>=2.0` in requirements.txt
- All existing tests green

**Visible deliverable:**
`pytest tests/test_schemas.py tests/test_tool_registry.py -q --tb=short` passes with all tests green.
`python -c "from orchestrator.schemas import UseCase, ToolResult; print(ToolResult.__fields__)"` prints
the field list without error.

**Test certification format:**
`pytest tests/test_schemas.py -q --tb=short`

---

### DISC-40 — [BE] Signal Extractor Agent + Scraper-to-Tool Refactor

**Priority:** P1 — foundation for every subsequent ticket  
**Execute with:** Primary: backend  
**Blocked by:** nothing

**User story:**  
As the pipeline, I need to pre-extract typed, discrete signals from ALL raw tool
outputs before any analysis occurs, so downstream agents receive structured facts
regardless of which or how many data sources contributed — and so that adding a
new data source in Sprint 5 requires zero changes to signal extraction or downstream agents.

**What it builds:**

`tools/website_scraper.py` — refactored from `agents/scraper.py`:
- Implements `Tool` base class from `orchestrator/tool_registry.py`
- `tool_id = "website_scraper"`
- `fetch({"url": str}) -> ToolResult` — same scraping logic, new return type
- `content` dict is identical to current `company_data`: `{about_text, job_postings, product_text, tech_mentions}`
- Dry-run: returns `ToolResult` built from `tests/fixtures/sample_company.json`
- Registered at pipeline startup: `ToolRegistry.register(WebsiteScraperTool())`

`agents/scraper.py` — updated to thin wrapper:
- `ScraperAgent.run()` now calls `WebsiteScraperTool.fetch()` internally
- Public interface unchanged — backward compat for any existing test that calls ScraperAgent directly
- Deprecation comment added: "Scraping logic has moved to tools/website_scraper.py"

`agents/signal_extractor.py` — new agent:
- Receives `raw_sources: list[ToolResult]` (not `company_data: dict`)
- Iterates over all `ToolResult` items, extracts signals from each `content` dict
- Labels each signal's `source` field using the `ToolResult.source_type`
- Calls `prompts/signal_extractor.md` with tool-sourced content clearly labeled
- Returns `SignalSet` validated by `validate_signals`
- Signal types: `tech_stack`, `data_signal`, `ml_signal`, `intent_signal`, `ops_signal`, `industry_hint`, `scale_hint`
- Dry-run: returns signals from `tests/fixtures/sample_signals.json`

`prompts/signal_extractor.md` — new prompt (v1.0):
- System: "Extract only what you observe. No recommendations. No scores."
- Input template: scraped text fields labeled by source
- Output: JSON array of SignalRecord objects
- Explicit guard: "Do not invent signals. Only cite what appears verbatim in the input."

`orchestrator/state.py` updated:
- Add `raw_sources: list[dict] | None = None` field  ← new: holds ToolResult dicts from tool layer
- Add `signals: list[dict] | None = None` field
- Add `maturity: dict | None = None` field  
- Add `victory_matches: list[dict] | None = None` field
- Add `use_cases: list[dict] | None = None` field
- Existing `rag_context` field kept for backward compatibility during Sprint 4
- Existing `company_data` field kept for backward compatibility (tools populate raw_sources; company_data deprecated)

`tests/fixtures/sample_signals.json` — new fixture:
- 8–12 signals covering all types, based on the existing `sample_company.json` content
- Used by dry-run mode and agent unit tests

**done_when:**  
Running `python orchestrator/pipeline.py --url https://example.com --dry-run` with
DISC-40 integrated produces a `state.raw_sources` list with at least 1 `ToolResult`,
and `state.signals` with at least 6 typed signals. All existing tests still pass.

**Acceptance criteria:**
- `tools/website_scraper.py` exists, implements `Tool`, `tool_id = "website_scraper"`
- `WebsiteScraperTool.fetch()` returns `ToolResult` — does NOT raise on scrape failure
- `agents/scraper.py` updated to thin wrapper calling `WebsiteScraperTool` — public interface unchanged
- `agents/signal_extractor.py` exists, follows BaseAgent contract
- `SignalExtractorAgent` receives `raw_sources: list[ToolResult]` not `company_data: dict`
- Agent output conforms to `SignalSet` schema from `orchestrator/schemas.py` — validated by `validate_signals`
- Every `Signal` in the output includes `signal_id` (e.g. "sig-001") and `raw_quote` (verbatim source text)
- `prompts/signal_extractor.md` exists at version 1.0 — prompt reads from labeled tool sources, not a flat dict
- `orchestrator/state.py` has `raw_sources` and the four new pipeline state fields
- `tests/fixtures/sample_signals.json` exists with 8+ signals, each with `signal_id` and `raw_quote`
- `tests/test_signal_extractor.py` covers: correct types returned, no invented signals (input with no tech mentions returns zero tech_stack signals), dry-run uses fixture, `validate_signals` rejects output with < 3 signals, agent handles `list[ToolResult]` input with 1 item and with 2+ items
- All existing tests green

**Visible deliverable:**  
`python orchestrator/pipeline.py --url https://example.com --dry-run` prints the signals
list in pipeline output or logging. Sai can see what the system observed.

**Test certification format:**  
`pytest tests/test_signal_extractor.py -q --tb=short`

---

### DISC-41 — [BE] Maturity Scorer Refactor

**Priority:** P1 — refactors existing consultant stage  
**Execute with:** Primary: backend  
**Blocked by:** DISC-40 (needs `state.signals` populated)

**User story:**  
As the pipeline, I need maturity scoring to operate on structured signals only —
not raw text — so the score is grounded in typed evidence rather than whatever
the model reads first.

**What it builds:**

`agents/maturity_scorer.py` — new agent (extracted from consultant.py):
- Receives `signals: list[dict]`
- Calls `prompts/maturity_scorer.md`
- Returns `maturity: dict` matching MaturityResult schema
- Dry-run: returns from `tests/fixtures/sample_maturity.json`
- Model: gemini-2.5-flash (structured scoring task, not complex reasoning)

`prompts/maturity_scorer.md` — new prompt (v1.0):
- Receives typed signals, not raw text
- Scores each dimension independently before computing composite
- Requires citing specific signal values as evidence for each dimension score
- Guard: "Only score based on the signals provided. Do not infer capabilities not in the signal list."

`tests/fixtures/sample_maturity.json` — new fixture based on sample_signals.json

`agents/consultant.py` updated:
- Remove maturity scoring logic (now delegated to MaturityScorerAgent)
- Remove dimension scoring from consultant.md prompt
- Consultant now receives `signals + maturity + victory_matches` as input (not raw text + rag_context)
- Note: this is a transitional state — consultant.py will be further refactored in DISC-43

`orchestrator/pipeline.py` updated:
- Insert MaturityScorerAgent step after SignalExtractorAgent
- Validate `state.maturity` has four dimensions before continuing
- Pass `state.signals` to MaturityScorerAgent, not `state.company_data`

`tests/fixtures/sample_maturity.json` — new fixture

**done_when:**  
Dry-run pipeline produces `state.maturity` with four dimension scores and a composite
score. Consultant agent no longer performs maturity scoring. All existing dry-run tests pass.

**Acceptance criteria:**
- `agents/maturity_scorer.py` exists, follows BaseAgent contract
- Agent output conforms to `MaturityResult` schema from `orchestrator/schemas.py` — validated by `validate_maturity`
- Each `DimensionScore.signals_used` contains signal_ids drawn from the input `SignalSet` — not arbitrary strings
- `prompts/maturity_scorer.md` exists at v1.0
- `orchestrator/state.py.maturity` field populated after pipeline step 2 (stored as `MaturityResult`)
- `tests/test_maturity_scorer.py` covers: composite calculation, all four dimensions required, signal-grounded rationale, `validate_maturity` rejects missing dimensions
- `agents/consultant.py` no longer contains dimension scoring code
- All existing tests green

**Visible deliverable:**  
Dry-run pipeline log shows a maturity step completing with `composite_score`,
`composite_label`, and all four dimension scores visible.

---

### DISC-42 — [BE] Victory Matcher Agent

**Priority:** P1 — provides grounded ROI benchmarks  
**Execute with:** Primary: backend  
**Blocked by:** DISC-41 (needs `state.maturity` for match calibration)

**User story:**  
As the use case generator, I need victory matches to come annotated with a relevance
tier (DIRECT, CALIBRATION, ADJACENT) so I can calibrate ROI confidence correctly
instead of treating all three cosine-similarity results as equally applicable.

**What it builds:**

`agents/victory_matcher.py` — new agent:
- Receives `signals`, `maturity`, `raw_rag_results` (from ChromaDB tool)
- Calls `prompts/victory_matcher.md`
- Returns `victory_matches: list[dict]` with tier annotation
- Each match: `{ win_id, engagement_title, match_tier, relevance_note, roi_benchmark, similarity_score, confidence }`
- Dry-run: returns from `tests/fixtures/sample_victory_matches.json`

`prompts/victory_matcher.md` — new prompt (v1.0):
- Input: company signals + maturity + raw ChromaDB results
- Task: annotate each result with DIRECT_MATCH / CALIBRATION_MATCH / ADJACENT_MATCH
- Criteria for each tier defined explicitly in the prompt
- Guard: "Only assign DIRECT_MATCH if industry, size_label, AND maturity gap <= 1.0 all hold."

`orchestrator/pipeline.py` updated:
- Build RAG query from `state.signals` (industry_hint + scale_hint + top data/ml signals)
  instead of raw company_data string concatenation
- Pass `raw_rag_results` to VictoryMatcherAgent alongside `signals` and `maturity`
- Store result in `state.victory_matches`

`tests/fixtures/sample_victory_matches.json` — new fixture

The existing `agents/rag_query.py` query construction logic is superseded by the new
orchestrator step. `rag_query.py` stays as the tool wrapper for ChromaDB calls.
Its query construction is updated to use signals instead of raw text.

**done_when:**  
Dry-run pipeline produces `state.victory_matches` with at least 1 match annotated
with a tier. At least 1 match in the logistics fixture test has tier `DIRECT_MATCH`.
All existing tests green.

**Acceptance criteria:**
- `agents/victory_matcher.py` exists, follows BaseAgent contract
- Agent output conforms to `list[VictoryMatch]` schema — validated by `validate_victories`
- Every `VictoryMatch` includes `match_tier` as one of the three valid literals
- Confidence values meet tier floors: DIRECT >= 0.75, CALIBRATION >= 0.55, ADJACENT >= 0.40
- `prompts/victory_matcher.md` exists at v1.0
- `orchestrator/state.py.victory_matches` populated after pipeline step 3 (stored as list of `VictoryMatch`)
- `tests/test_victory_matcher.py` covers: DIRECT_MATCH criteria, ADJACENT_MATCH fallback, empty RAG results handled gracefully, confidence floor enforcement
- `agents/rag_query.py` query text now constructed from `signals` not raw text
- All existing tests green

**Visible deliverable:**  
API response includes `victory_matches` with `match_tier` field visible for each match.
Sai can see that the logistics fixture returns a `DIRECT_MATCH` win.

---

### DISC-43 — [BE] Use Case Generator Agent — Three-Tier Classification

**Priority:** P1 — the core strategic output  
**Execute with:** Primary: backend  
**Blocked by:** DISC-42 (needs annotated victory_matches)

**User story:**  
As a Tenex consultant preparing for a client meeting, I need the recommendations
organized into proven, achievable, and experimental tiers, so I can lead the
conversation with what has worked before and save the frontier opportunities for
the right moment in the discussion.

**What it builds:**

`agents/use_case_generator.py` — new agent (extracts use case logic from consultant.py):
- Receives `signals`, `maturity`, `victory_matches`
- Calls `prompts/use_case_generator.md` with gemini-2.5-pro
- Returns `use_cases: list[dict]` with tier, title, description, evidence, effort, impact,
  roi_estimate, roi_basis, rag_benchmark, confidence, data_flow
- `data_flow` maps client's EXISTING systems to the proposed AI solution:
  - `data_inputs`: list the client's named data sources from signals (not generic labels)
  - `model_approach`: concrete approach drawn from victory tech_stack or industry pattern
  - `output_consumer`: the specific role (not department) that uses the output and how
  - `feedback_loop`: mechanism by which the model improves post-deployment
  - `value_measurement`: specific metric, measurement cadence, and baseline comparison
- First use case is always LOW_HANGING_FRUIT (orchestrator enforces if model doesn't)
- Minimum 2, maximum 5 use cases
- Dry-run: returns from `tests/fixtures/sample_use_cases.json`

`prompts/use_case_generator.md` — new prompt (v1.0):
- Input: signals + maturity + victory_matches (annotated with tiers)
- Classification rules for LOW_HANGING_FRUIT / MEDIUM_SOLUTION / HARD_EXPERIMENT
  encoded explicitly in the prompt
- ROI grounding rule: "LOW_HANGING_FRUIT must cite a win_id in rag_benchmark.
  MEDIUM_SOLUTION must cite a win_id or state calibration basis.
  HARD_EXPERIMENT may cite an ADJACENT_MATCH or state 'no direct match — signal basis.'"
- Guard: "Do not assign LOW_HANGING_FRUIT if no DIRECT_MATCH victory exists for this use case."

**Data flow generation rules (for the prompt):**

The prompt must instruct the model to construct `data_flow` as follows:

1. `data_inputs` — map the client's EXISTING data assets from signals to model inputs.
   Use the exact values from `tech_stack` and `data_signals` signal types.
   Label each input as "(exists)" if confirmed by a signal or "(needed)" if required but
   not evidenced. Example: "Snowflake shipment history (exists)", "GPS telemetry (needed)".

2. `model_approach` — specify a concrete model type, not a generic category.
   For LOW_HANGING_FRUIT: use the DIRECT_MATCH victory's `tech_stack.ml_approach` directly.
   For MEDIUM_SOLUTION: adapt the CALIBRATION_MATCH victory's `tech_stack.ml_approach`
     and note the adaptation (e.g., "scaled from enterprise XGBoost implementation").
   For HARD_EXPERIMENT: propose an approach based on ADJACENT_MATCH pattern or
     industry standard for this use case type; prefix with "proposed: ".

3. `output_consumer` — name the specific ROLE (not department) that uses the output,
   and the delivery mechanism. Reference the victory record's `client_systems_integrated`
   for the delivery interface when available.
   Example: "Procurement manager via TMS carrier selection screen" not "procurement team".

4. `feedback_loop` — describe the mechanism by which the model learns from deployment.
   Must include: what data is logged, at what cadence, and what triggers retraining.
   For LOW_HANGING_FRUIT: use the victory's documented feedback pattern.
   For HARD_EXPERIMENT: state the proposed feedback mechanism explicitly.

5. `value_measurement` — state the specific metric, measurement period, and baseline.
   Must be measurable by the client's existing reporting (or state what reporting is needed).
   Example: "Late delivery rate measured monthly vs prior year baseline; alert if < 8% improvement."

**Victory data connection:**
- `tech_stack.data_sources` from the matched victory → `data_flow.data_inputs` (PROVEN/ACHIEVABLE)
- `tech_stack.ml_approach` from the matched victory → `data_flow.model_approach` (PROVEN/ACHIEVABLE)
- `tech_stack.client_systems_integrated` from the matched victory → informs `data_flow.output_consumer`
- For FRONTIER: use ADJACENT_MATCH tech_stack as a pattern reference, not a blueprint

`agents/consultant.py` retired:
- Sprint 4 replaces consultant.py with three specialized agents
- consultant.py kept in repo but no longer called by pipeline.py
- A deprecation comment added to consultant.py pointing to the three replacements

`orchestrator/pipeline.py` updated:
- Pipeline is now 7 steps: Scrape → Gate → Extract Signals → Score Maturity → Match Victories → Generate Use Cases → Write Report
- Each step's input is the prior step's promoted state field only
- Report writer receives `signals + maturity + victory_matches + use_cases`

`tests/fixtures/sample_use_cases.json` — new fixture with 3 use cases (one per tier)

`docs/specs/analysis_spec.md` — updated Section 4 (Use Case Selection Logic):
- Add tier definitions as authoritative classification rules
- Version bumped to 2.0

**done_when:**  
Dry-run pipeline produces `state.use_cases` with at least one use case per tier.
The first use case has `tier: "LOW_HANGING_FRUIT"`. The `rag_benchmark` field
on LOW_HANGING_FRUIT items is non-null. All existing tests green.

**Acceptance criteria:**
- `agents/use_case_generator.py` exists, follows BaseAgent contract
- Agent output conforms to `list[UseCase]` schema — validated by `validate_use_cases`
- Every `UseCase` includes `evidence_signal_ids` (signal_ids from the input SignalSet) and `why_this_company` (non-generic, company-specific sentence)
- Every `UseCase` includes a `data_flow` field with all 5 sub-fields populated (non-empty strings)
- LOW_HANGING_FRUIT use cases: `data_flow.model_approach` traces to the DIRECT_MATCH victory's `tech_stack.ml_approach`
- FRONTIER use cases: `data_flow.model_approach` is prefixed with "proposed: " — never stated as confirmed
- `prompts/use_case_generator.md` exists at v1.0
- `orchestrator/pipeline.py` calls the 8-step sequence (Scrape → Gate → Extract → Score → Match → Generate → Write Report — DISC-39 gate added)
- `state.use_cases` populated with typed `UseCase` objects
- `agents/consultant.py` has deprecation comment (not deleted — backward compat)
- `tests/test_use_case_generator.py` covers: tier assignment logic, LOW_HANGING_FRUIT requires DIRECT_MATCH, HARD_EXPERIMENT confidence floor, ordering rule, `evidence_signal_ids` traceable to input signals, `data_flow` present on all use cases, FRONTIER data_flow.model_approach prefixed with "proposed: "
- All existing tests green, dry-run completes in < 2 seconds

**Visible deliverable:**  
API response `top_use_cases` array contains `tier` field on each item.
Running the dry-run and hitting `/v1/analyze` with curl returns JSON where
`use_cases[0].tier == "LOW_HANGING_FRUIT"`, `use_cases[1].tier == "MEDIUM_SOLUTION"`,
`use_cases[2].tier == "HARD_EXPERIMENT"`.

---

### DISC-44 — [FE] Three-Tier Use Case Cards

**Priority:** P1 — makes Sprint 4 visible to Sai  
**Execute with:** Primary: frontend  
**Blocked by:** DISC-43 (needs `tier` field in API response)

**User story:**  
As a Tenex consultant reviewing the report, I need to immediately see which
recommendations are proven (green), which require investment (amber), and which
are frontier bets (blue), so I can lead the client conversation with the right
level of confidence.

**What it builds:**

`frontend/components/UseCaseTierSection.tsx` — new component:
- Renders use cases grouped by tier in three visual sections
- Section headers:
  - "Proven Solutions" (LOW_HANGING_FRUIT) — green header
  - "Achievable with Investment" (MEDIUM_SOLUTION) — amber header
  - "Frontier Opportunities" (HARD_EXPERIMENT) — blue header
- Each section is collapsible
- Sections are rendered in order: Proven first, then Achievable, then Frontier
- If a tier has no use cases, its section is not rendered

`frontend/components/UseCaseCard.tsx` — updated:
- Add `TierBadge` component: a small colored pill showing "Proven", "Achievable", or "Frontier"
  - LOW_HANGING_FRUIT → green badge labeled "Proven"
  - MEDIUM_SOLUTION → amber badge labeled "Achievable"  
  - HARD_EXPERIMENT → blue badge labeled "Frontier"
- Add confidence display: percentage below the ROI estimate
  - If confidence < 0.55: show "lower confidence" in grey text
  - If confidence >= 0.75: show nothing extra (high confidence is the default)
- Add `roi_basis` field display: small italic text below ROI estimate
  showing the source — e.g., "Based on win-001 (Route Optimization)"

`frontend/lib/types.ts` updated:
- Add `tier: "LOW_HANGING_FRUIT" | "MEDIUM_SOLUTION" | "HARD_EXPERIMENT"` to UseCase type
- Add `roi_basis: string` to UseCase type
- Add `confidence: number` field (already exists, ensure it renders)

`frontend/app/page.tsx` updated:
- Replace flat use case list rendering with `UseCaseTierSection`
- Pass full use_cases array — component handles grouping by tier

**Backend contract change (from DISC-39/DISC-43):**
The API response shape for use cases reflects the `UseCase` Pydantic schema.
Frontend types in `frontend/lib/types.ts` must match: `evidence_signal_ids`,
`why_this_company`, and `roi_basis` are now required fields on the UseCase type.
The `tier` field is a string literal — frontend should treat unknown values as
"HARD_EXPERIMENT" for forward compatibility.

**done_when:**  
Live frontend shows three colored sections in the use cases area. At least one
green "Proven" card appears for a logistics company URL. Confidence is visible
on each card. The amber and blue sections render for medium and hard use cases.

**Acceptance criteria:**  
- `UseCaseTierSection.tsx` exists and renders three sections
- `TierBadge` renders correct color per tier
- `roi_basis` visible on each card
- Confidence percentage visible
- Empty tier section renders nothing (not an error state)
- Mobile-responsive: cards readable on phone screen
- Works with existing dry-run fixture data (if sample_use_cases.json has all three tiers)

**Visible deliverable:**  
Sai opens the frontend, submits any company URL, and sees the use case section
divided into "Proven Solutions", "Achievable with Investment", "Frontier Opportunities"
with colored headers. The first green card has a win ID in the basis text.

---

### DISC-45 — [QA] Sprint 4 Eval — Tier Classification Accuracy

**Priority:** P1 — gates sprint close  
**Execute with:** Primary: qa  
**Blocked by:** DISC-43 and DISC-44 complete

**User story:**  
As the technical director, I need to confirm that the new three-agent consultant
pipeline classifies use cases correctly — Proven items have real wins behind them,
Frontier items are genuinely novel — so I know the system's reasoning is sound
before the Tenex demo.

**What it builds:**

Three-company eval set:
1. A logistics company (expect at least 1 LOW_HANGING_FRUIT matching win-001/002/003)
2. A healthcare company (expect at least 1 LOW_HANGING_FRUIT matching win-007/008/009)
3. A professional services or SaaS company outside the top industry matches
   (expect some MEDIUM_SOLUTION and at least 1 HARD_EXPERIMENT)

New rubric: `evals/rubrics/tier_classification.yaml`:
- Dimension 1 — Tier accuracy: LOW_HANGING_FRUIT items have a DIRECT_MATCH victory (0–5)
- Dimension 2 — ROI grounding: each LOW_HANGING_FRUIT and MEDIUM_SOLUTION item cites a win_id (0–5)
- Dimension 3 — Confidence calibration: HARD_EXPERIMENT confidence <= 0.65, LOW_HANGING_FRUIT >= 0.70 (0–5)
- Dimension 4 — Signal traceability: use case evidence field cites a specific signal from signals[] (0–5)
- Dimension 5 — Ordering: first use case in the response is always LOW_HANGING_FRUIT (0/5 binary)

Sprint 4 pass threshold: all 5 dimensions >= 3.5/5 across all 3 companies.

Regression check: Sprint 3 eval scores (victory citation) must not drop vs Sprint 3 baseline.

`tests/regression_log.md` updated:
- Sprint 3 → Sprint 4 delta table
- Tier classification scores for all 3 companies
- Any regressions flagged with cause

`evals/ci_eval.py` updated:
- Add `tier_classification` rubric
- Gate: fail CI if any tier dimension drops below 3.0

**done_when:**  
All 3 companies evaluated. Tier classification dimensions >= 3.5 average.
No regressions in Sprint 3 victory citation scores. Regression log updated.
QA sign-off posted to Linear.

**Visible deliverable:**  
A markdown table in the Linear comment showing tier classification scores per company.
Example structure:
```
Company               | Tier Accuracy | ROI Grounding | Confidence Cal | Signal Trace | Ordering
Logistics             | 4.5/5         | 5.0/5         | 4.5/5          | 4.0/5        | 5/5
Healthcare            | 4.0/5         | 4.5/5         | 4.0/5          | 3.5/5        | 5/5
Professional Services | 3.5/5         | 3.8/5         | 4.0/5          | 3.5/5        | 5/5
```

---

## Part 6 — What Sai Tests at Sprint 4 End

```
Test 1 — Three-tier use cases visible in UI:
  URL: any mid-market logistics company
  Action: submit URL, wait for report
  Expected: three sections visible — "Proven Solutions" (green), "Achievable with Investment" (amber),
            "Frontier Opportunities" (blue). At least one green card.
  Failure sign: flat list of use cases with no tier differentiation

Test 2 — Proven card has a real win behind it:
  URL: same logistics company
  Action: look at the first green "Proven Solutions" card
  Expected: "Based on win-001 (Route Optimization for Regional LTL Carrier)" visible in ROI basis text
  Failure sign: ROI basis is missing or says "industry benchmark"

Test 3 — Frontier card has honest confidence:
  URL: a company in an industry with fewer wins (e.g., construction or energy)
  Action: look at the blue "Frontier Opportunities" section
  Expected: confidence is below 65%, "lower confidence" indicator visible
  Failure sign: Frontier item shows 90% confidence — the system is overconfident

Test 4 — Maturity scoring is signal-grounded:
  Action: inspect the `current_state` section of the report
  Expected: mentions specific named tools and signals (e.g., "Snowflake data warehouse",
            "hiring for ML Engineer role") — not generic statements
  Failure sign: "The company has a modern data stack" with no specifics

Test 5 — Pipeline coherence:
  URL: any company used in Tests 1–3
  Action: check that the exec_summary, use_cases, and roi_analysis are internally consistent
  Expected: the use case named in exec_summary appears in the use_cases section with the same ROI figure
  Failure sign: exec_summary mentions $500K savings but use_cases say $200K

Test 6 — Eval scores:
  QA presents the tier classification rubric table
  Expected: tier accuracy >= 3.5/5 for all 3 test companies
  Failure sign: scores below 3.0 — the system is misclassifying proven items as frontier
```

---

## Architecture Decisions Required This Sprint

| Decision | ADR |
|----------|-----|
| ConsultantAgent split into three specialized agents (SignalExtractor, MaturityScorer, UseCaseGenerator) | ADR-008 (new) |
| VictoryMatcher uses relevance tiers (DIRECT/CALIBRATION/ADJACENT) not cosine rank alone | Covered by ADR-008 |
| UseCaseGenerator uses gemini-2.5-pro; SignalExtractor and MaturityScorer use gemini-2.5-flash | Covered by ADR-004 update |
| PipelineState extended with raw_sources, signals, maturity, victory_matches, use_cases fields | ADR-009 (new) |
| LOW/MEDIUM/HARD tier classification is a first-class output type and UI concept | ADR-009 |
| Tool registry pattern: scraping is a tool concern, signal extraction is an agent concern | ADR-009 |
| ScraperAgent logic extracted into WebsiteScraperTool; Tool/ToolRegistry as extensibility pattern | ADR-009 |

PM to file ADR-008 and ADR-009 at sprint open, before DISC-39 execution begins.

ADR-009 covers the Pydantic schema contract decision (all inter-agent data flows through
typed `orchestrator/schemas.py` models, validated by `orchestrator/validators.py`) AND
the tool registry architecture decision (scraping is a tool concern; adding a new data
source = adding a new tool, not changing the pipeline or any agents).

---

## What Sprint 4 Does NOT Touch

- **PDF export** — still deferred. Tier UI ships first.
- **Follow-up Q&A** — conversational flow deferred to Sprint 5.
- **50-seed expansion** — 20 wins are sufficient to validate the tier system.
  After Sprint 4 proves the architecture, Sprint 5 can expand the victory set.
- **Agent registry / config YAML** — agent configuration deferred. Sprint 5 if needed.
  Note: `ToolRegistry` ships in Sprint 4 (DISC-39) — but this is a tool registry for
  data-fetching tools, not an agent configuration system.
- **Focus area text box** — useful but not blocking the tier feature. Sprint 5.
- **Authentication** — ADR-002 defers auth to day-2. Not Sprint 4.

---

---

## Future Tools (Sprint 5+) — Zero Pipeline Changes Required

The tool registry architecture means every one of these can be added independently,
in any order, in any sprint. The only constraint: the tool must return a valid `ToolResult`.

### Tool Catalog

| Tool Class | tool_id | Source Type | Data It Fetches | Signals It Enriches |
|------------|---------|-------------|-----------------|---------------------|
| `JobBoardTool` | `job_board` | `job_board` | Active job listings from LinkedIn, Indeed, Greenhouse | `ml_signal` (ML Eng roles), `tech_stack` (tools in JDs), `scale_hint` (hiring velocity) |
| `NewsSearchTool` | `news_search` | `news` | Recent press releases, funding announcements, product news | `intent_signal` (AI strategy language), `scale_hint` (funding = growth), `industry_hint` corroboration |
| `TechDetectorTool` | `tech_detector` | `tech_detector` | BuiltWith data, public GitHub repos, API doc pages | `tech_stack` (confirmed stack vs claimed), `ops_signal` (CI/CD, cloud) |
| `CompanyProfileTool` | `company_profile` | `company_profile` | Employee count, funding rounds, HQ, founded year | `scale_hint` (headcount), `industry_hint` (SIC classification), `intent_signal` (growth stage) |

### Implementation Pattern for Each New Tool

```python
# tools/job_board_tool.py
class JobBoardTool(Tool):
    tool_id = "job_board"

    def fetch(self, input_data: dict) -> ToolResult:
        company_name = input_data.get("company_name", "")
        url = input_data.get("url", "")
        # fetch from LinkedIn/Indeed/Greenhouse API or scraping
        # return ToolResult — never raise
        try:
            postings = self._fetch_postings(company_name)
            return ToolResult(
                tool_id=self.tool_id,
                source_type="job_board",
                content={"postings": postings, "total_count": len(postings)},
                pages_fetched=[f"linkedin.com/jobs/{company_name}"],
                fetch_timestamp=datetime.utcnow().isoformat(),
                success=True,
            )
        except Exception as e:
            return ToolResult(
                tool_id=self.tool_id,
                source_type="job_board",
                content={},
                pages_fetched=[],
                fetch_timestamp=datetime.utcnow().isoformat(),
                success=False,
                error=str(e),
            )
```

Then in pipeline startup:
```python
ToolRegistry.register(WebsiteScraperTool())
ToolRegistry.register(JobBoardTool())   # Sprint 5: add this line
# everything else — unchanged
```

### Signal Coverage Improvement by Tool

Each new tool narrows specific uncertainty gaps:

| Gap | Tool That Closes It |
|-----|---------------------|
| Tech stack claimed vs used | `TechDetectorTool` (BuiltWith vs website copy) |
| ML hiring velocity | `JobBoardTool` (active roles count vs single mention) |
| Scale: headcount is ambiguous from website | `CompanyProfileTool` (exact employee range) |
| Intent: website copy vs actual news | `NewsSearchTool` (press release language is harder to fake) |
| Industry classification confidence | `CompanyProfileTool` (SIC code or NAICS vs inference) |

The signal extractor prompt is updated once per new tool type (to interpret that source's
`content` structure). No other agent changes. No pipeline changes. No schema changes.

## Sprint 4 Definition of Done

Sprint 4 is complete when:

1. All 7 tickets have QA sign-off (DISC-39 through DISC-45)
2. Pipeline runs 8 steps and `state.signals` (as `SignalSet`), `state.maturity` (as `MaturityResult`),
   `state.victory_matches` (as `list[VictoryMatch]`), `state.use_cases` (as `list[UseCase]`),
   `state.report` are all non-null and schema-valid on completion
3. Live frontend shows three-tier use case sections with correct colors
4. A logistics company URL produces at least one "Proven Solutions" card citing win-001/002/003
5. Tier classification eval scores >= 3.5/5 for all 3 test companies
6. No regressions in Sprint 3 victory citation scores
7. Sai has run Tests 1–6 above and confirmed they all pass
8. `docs/SYSTEM_STATE.md`, `ARCHITECTURE.md`, `SPRINT_LOG.md`, `WIREFRAMES.md`,
   `COMPONENT_MAP.md`, `CONTRACTS.md`, and `decisions/INDEX.md` updated

**If the use cases are still a flat list — Sprint 4 is not done.**
**If a "Proven" card does not cite a real Tenex win — Sprint 4 is not done.**
**If inter-agent data flows as untyped dicts with no validation gate — Sprint 4 is not done.**

---

## Cost Impact

| Component | Cost per run |
|-----------|-------------|
| Sprint 3 baseline | ~$0.009 |
| SignalExtractorAgent (gemini-2.5-flash, small task) | ~$0.001 |
| MaturityScorerAgent (gemini-2.5-flash, structured) | ~$0.001 |
| VictoryMatcherAgent (gemini-2.5-flash, reasoning over 3 records) | ~$0.001 |
| UseCaseGeneratorAgent (gemini-2.5-pro, highest reasoning) | ~$0.004 |
| ReportWriterAgent (gemini-2.5-flash, unchanged) | ~$0.004 |
| **Sprint 4 total per run** | **~$0.011** |

Still well under the $0.50 ceiling. The cost increase is ~$0.002 per run
in exchange for significantly higher output quality and reasoning transparency.
