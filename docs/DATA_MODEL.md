# Data Model

Every data type in this system is defined in `core/schemas.py` as a Pydantic model.
This document explains the important types, what their fields mean, and how they
relate to each other.

---

## How types relate to each other

```
Run (top-level container)
  |
  +-- CompanyIntake (user input)
  +-- CompanyUnderstanding (from CompanyProfiler)
  +-- IndustryContext (from IndustryAnalyst)
  +-- PainPoint[] (from PainInvestigator)
  |
  +-- EvidenceItem[] (from grounder + RAG, through PromotionGate)
  |     |
  |     +-- source_type: GOOGLE_SEARCH | WINS_KB | USER_PROVIDED
  |     +-- dimension: technology | scale | revenue | pain_point | ...
  |     +-- relevance_score, confidence_score
  |
  +-- Hypothesis[] (from HypothesisFormer, tested by HypothesisTester)
  |     |
  |     +-- evidence_for[] -----> evidence_ids
  |     +-- evidence_against[] -> evidence_ids
  |     +-- test_results[] (TestResult: finding + confidence impact)
  |     +-- reasoning_chain[] (ReasoningStep: causal chain)
  |     +-- status: FORMING -> TESTING -> VALIDATED | REJECTED
  |
  +-- AdaptiveReport (from ReportSynthesizer)
  |     |
  |     +-- opportunities[] (ReportOpportunity)
  |           |
  |           +-- hypothesis_id -----> links to Hypothesis
  |           +-- evidence_summary --> cites evidence_ids
  |           +-- tier: easy | medium | hard
  |
  +-- AgentState[] (one per agent that ran)
  +-- DerivedInsight[] (conclusions, not raw evidence)
  +-- SpawnRequest[] (new hypotheses discovered during testing)
  +-- UserInteractionPoint[] (questions surfaced to user)
  +-- BudgetConfig + BudgetState (cost tracking)
  +-- config_snapshot (frozen config at run creation)
```

---

## Run

The top-level container. One Run per analysis. Holds everything.

**File**: `core/schemas.py:78`

| Field | Type | Description |
|-------|------|-------------|
| run_id | str | UUID, created at run start |
| status | RunStatus | Current pipeline phase (see State Machine below) |
| created_at | datetime | When the run was created |
| config_snapshot | dict | Frozen copy of config at run creation, never changes after |
| budgets | BudgetConfig | Hard limits (search budget, RAG budget, etc.) |
| budget_state | BudgetState | Mutable counters (queries used so far) |
| company_intake | CompanyIntake | User input: company name, industry, notes |
| company_understanding | CompanyUnderstanding | Output of CompanyProfiler (5 dimensions) |
| industry_context | IndustryContext | Output of IndustryAnalyst (4 dimensions) |
| pain_points | PainPoint[] | Output of PainInvestigator |
| evidence | EvidenceItem[] | All promoted evidence across all phases |
| hypotheses | Hypothesis[] | All hypotheses (forming, testing, validated, rejected) |
| adaptive_report | AdaptiveReport | The final synthesized report |
| agent_states | AgentState[] | Tracking record for each agent that ran |
| derived_insights | DerivedInsight[] | Conclusions drawn from evidence |
| spawn_requests | SpawnRequest[] | New hypotheses discovered during testing |
| user_interactions | UserInteractionPoint[] | Questions surfaced to the user |
| phase_briefings | dict[str, str] | Compressed briefings between phases |
| feedback_history | ReportFeedback[] | User feedback on the report |
| assumptions | AssumptionsDraft | Legacy mode: extracted assumptions |
| reasoning_state | ReasoningState | Legacy mode: field coverage tracking |
| working_memory | dict[str, FieldKnowledge] | Legacy mode: per-field knowledge |
| opportunities | Opportunity[] | Legacy mode: scored opportunities |
| report | dict | Legacy mode: generated report |

---

## RunStatus (State Machine)

All possible statuses a run can be in:

| Status | Value | When |
|--------|-------|------|
| CREATED | "created" | Run just created, no input yet |
| INTAKE | "intake" | Company intake saved |
| GROUNDING | "grounding" | CompanyProfiler + IndustryAnalyst running |
| DEEP_RESEARCH | "deep_research" | PainInvestigator running |
| HYPOTHESIS_FORMATION | "hypothesis_formation" | HypothesisFormer running |
| HYPOTHESIS_TESTING | "hypothesis_testing" | HypothesisTesters running |
| SYNTHESIS | "synthesis" | ReportSynthesizer running |
| REPORT | "report" | Report generated, transitioning to review |
| REVIEW | "review" | User reviewing the report |
| PUBLISHED | "published" | User approved, report is final |
| FAILED | "failed" | Unrecoverable error |
| ASSUMPTIONS_DRAFT | "assumptions_draft" | Legacy: assumptions extracted |
| ASSUMPTIONS_CONFIRMED | "assumptions_confirmed" | Legacy: user confirmed assumptions |
| REASONING | "reasoning" | Legacy: reasoning loop running |

Valid transitions are enforced in `core/run_manager.py:46-66`.

---

## CompanyIntake

User-provided input that starts an analysis.

| Field | Type | Description |
|-------|------|-------------|
| company_name | str | The company being analyzed |
| industry | str | Industry sector |
| employee_count_band | str (optional) | E.g., "100-500", "1000-5000" |
| notes | str (optional) | Free-text context from the user |
| constraints | list[str] | Any constraints (e.g., "no cloud migration") |

---

## EvidenceItem

A single fact or finding from any source. The fundamental unit of knowledge in the system.

**File**: `core/schemas.py:153`

| Field | Type | Description |
|-------|------|-------------|
| evidence_id | str | Unique ID (e.g., "ev-abc123") |
| run_id | str | Which run this belongs to |
| source_type | EvidenceSource | Where it came from (see below) |
| source_ref | str | Specific source reference (URL for web, chunk ID for RAG) |
| title | str | Short title of the finding |
| uri | str (optional) | Web URL if from Google Search |
| snippet | str | The actual content/fact |
| relevance_score | float | 0.0-1.0, how relevant to the analysis |
| confidence_score | float (optional) | 0.0-1.0, internal confidence from the source |
| retrieval_meta | dict | Extra metadata (query used, rank, chunk_type for RAG) |
| provenance | Provenance (optional) | Lineage tracking |
| produced_by | str | Agent ID that created this evidence |
| dimension | str | What aspect it covers (see below) |
| process_area | str | Which business process it relates to |

### EvidenceSource (where evidence comes from)

| Value | Meaning |
|-------|---------|
| GOOGLE_SEARCH | From Gemini grounding with Google Search |
| WINS_KB | From RAG retrieval over past engagements |
| USER_PROVIDED | From user enrichment or manual input |

### Evidence dimensions

| Value | Meaning |
|-------|---------|
| technology | Company's tech stack, platforms, tools |
| scale | Company size, revenue, headcount |
| revenue | Business model, revenue streams |
| operations | Operational processes, workflows |
| industry | Industry-level context |
| pain_point | Operational pain or challenge |
| hypothesis_test | Evidence gathered during hypothesis testing |

### Provenance

Tracks where evidence came from, used for traceability.

| Field | Type | Description |
|-------|------|-------------|
| source_evidence_ids | list[str] | If derived from other evidence, their IDs |
| extraction_timestamp | datetime | When this was captured |
| source_type | str | "raw", "summarized", or "inferred" |
| confidence | float | Confidence in the provenance chain |

---

## Hypothesis

A testable claim about an AI opportunity. The core of the analysis.

**File**: `core/schemas.py:307`

| Field | Type | Description |
|-------|------|-------------|
| hypothesis_id | str | Unique ID (e.g., "hyp-abc123") |
| statement | str | The claim (e.g., "AI dispatch optimization could reduce idle time by 20%") |
| category | str | "automation", "copilot", "decision_support", or "optimization" |
| target_process | str | Which business process this targets |
| status | HypothesisStatus | Current lifecycle state (see below) |
| confidence | float | 0.0-1.0, evolves during testing |
| evidence_for | list[str] | Evidence IDs that support this hypothesis |
| evidence_against | list[str] | Evidence IDs that contradict it |
| evidence_conditions | list[str] | Evidence IDs for prerequisites/caveats |
| analogous_engagements | list[str] | Past engagement IDs that are similar |
| conditions_for_success | list[str] | What must be true for this to work |
| risks | list[str] | Known risks |
| open_questions | list[str] | Unresolved questions |
| test_results | TestResult[] | Record of every test performed |
| reasoning_chain | ReasoningStep[] | Full causal chain (why it was formed, how it evolved) |
| formed_by_agent | str | Which agent created it |
| tested_by_agent | str | Which agent tested it |
| parent_hypothesis_id | str (optional) | If spawned from another hypothesis |

### HypothesisStatus (lifecycle)

```
FORMING -> TESTING -> VALIDATED
                   -> REJECTED
                   -> NEEDS_USER_INPUT
```

| Status | When |
|--------|------|
| FORMING | Just created by HypothesisFormer, not yet tested |
| TESTING | Being tested by HypothesisTester, confidence adjusting |
| VALIDATED | Passed testing, confidence meets threshold |
| REJECTED | Failed testing, confidence below rejection threshold |
| NEEDS_USER_INPUT | Testing blocked, needs user to provide information |

### TestResult

One test performed on a hypothesis.

| Field | Type | Description |
|-------|------|-------------|
| test_type | str | "evidence_search", "analogous_case", "counter_evidence", "prerequisite" |
| finding | str | What the test found |
| impact_on_confidence | float | -0.20 to +0.20, clamped. Positive = supporting, negative = contradicting |
| evidence_ids | list[str] | Evidence that this test produced |

### ReasoningStep

One step in a hypothesis's causal chain. This is what makes the analysis traceable.

| Field | Type | Description |
|-------|------|-------------|
| step_type | str | "formed_because", "tested_with", "contradicted_by", "revised_because", "validated_by" |
| description | str | Human-readable explanation |
| evidence_ids | list[str] | Evidence linked to this step |
| confidence_delta | float | How much confidence changed at this step |
| timestamp | datetime | When this step occurred |

**Example chain**:
```
formed_because: "Manual dispatch with 3 drivers per zone suggests routing optimization opportunity" (+50%)
tested_with: "Test 1: Found similar fleet company reduced idle time 18% with AI routing" (+12%)
contradicted_by: "Test 2: Company uses legacy TMS that may not integrate with modern APIs" (-8%)
tested_with: "Test 3: RAG shows 3 past engagements with TMS integration succeeded" (+10%)
validated_by: "Confidence held at 64% after 3 tests"
Final confidence: 64% -- validated
```

### Tier classification (for report)

The HypothesisTracker classifies validated hypotheses into tiers:

| Tier | Criteria |
|------|----------|
| easy | No conditions, confidence >= 0.7, at least 1 analogous engagement |
| medium | Has conditions, OR confidence >= 0.5 |
| hard | Everything else |

---

## CompanyUnderstanding

Output of the CompanyProfiler agent. What we know about the company.

| Field | Type | Description |
|-------|------|-------------|
| company_name | str | Company name |
| what_they_do | str | Business description |
| how_they_make_money | str | Revenue model |
| size_and_scale | str | Employee count, revenue, locations |
| technology_landscape | str | Tech stack, platforms, tools |
| organizational_structure | str | Teams, departments |
| confidence | float | filled_dimensions / 5 |
| evidence_ids | list[str] | Evidence that supports this understanding |

---

## IndustryContext

Output of the IndustryAnalyst agent. What we know about the industry.

| Field | Type | Description |
|-------|------|-------------|
| industry | str | Industry name |
| key_trends | list[str] | Major industry trends |
| competitive_dynamics | str | Competitive landscape |
| regulatory_landscape | str | Regulations, compliance |
| ai_adoption_level | str | How far the industry has adopted AI |
| confidence | float | filled_dimensions / 4 |
| evidence_ids | list[str] | Evidence that supports this context |

---

## PainPoint

An operational pain point discovered by PainInvestigator.

| Field | Type | Description |
|-------|------|-------------|
| pain_id | str | Unique ID (e.g., "pp-abc123") |
| description | str | What the problem is |
| affected_process | str | Which process (e.g., "dispatch", "billing") |
| severity | str | "high", "medium", or "low" |
| current_workaround | str | How the company currently handles it |
| evidence_ids | list[str] | Supporting evidence |
| confidence | float | How confident we are this is a real pain point |

---

## AdaptiveReport

The final client-facing output. Produced by ReportSynthesizer.

**File**: `core/schemas.py:403`

| Field | Type | Description |
|-------|------|-------------|
| run_id | str | Which run this report is for |
| executive_summary | str | High-level summary for executives |
| key_insight | str | The single most important finding |
| opportunities | ReportOpportunity[] | Ranked list of AI opportunities |
| reasoning_chain | list[str] | How the analysis reached its conclusions |
| confidence_assessment | str | Overall confidence in the recommendations |
| what_we_dont_know | list[str] | Gaps and uncertainties |
| recommended_next_steps | list[str] | What to do next |
| evidence_annex | list[dict] | Evidence references for citation |
| agent_activity_summary | list[dict] | What each agent did |

### ReportOpportunity

One AI opportunity recommendation within the report.

| Field | Type | Description |
|-------|------|-------------|
| title | str | Opportunity name |
| hypothesis_id | str | Links back to the Hypothesis it came from |
| narrative | str | Full explanation of the opportunity |
| tier | str | "easy", "medium", or "hard" |
| confidence | float | How confident we are |
| roi_estimate | dict (optional) | Estimated return on investment |
| evidence_summary | str | Summary of supporting evidence with cited IDs |
| analogous_cases | list[dict] | Similar past engagements |
| risks | list[str] | Known risks |
| conditions_for_success | list[str] | What must be true |
| recommended_approach | str | How to implement |

---

## Budget Types

### BudgetConfig (hard limits, set at run creation)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| external_search_query_budget | int | 25 | Max Google Search queries |
| external_search_max_calls | int | 8 | Max Gemini grounding API calls |
| rag_query_budget | int | 15 | Max RAG retrieval calls |
| rag_top_k | int | 5 | Results per RAG query |
| rag_min_score | float | 0.3 | Minimum relevance for RAG results |

### BudgetState (mutable counters, updated during pipeline)

| Field | Type | Description |
|-------|------|-------------|
| external_search_queries_used | int | Google Search queries consumed |
| external_search_calls_used | int | Gemini API calls consumed |
| rag_queries_used | int | RAG retrieval calls consumed |
| total_tool_calls_used | int | Total tool calls across all agents |

---

## Agent Types

### AgentState

Tracking record for one agent's execution.

| Field | Type | Description |
|-------|------|-------------|
| agent_id | str | Unique agent ID |
| agent_type | str | "company_profiler", "hypothesis_tester", etc. |
| status | str | "pending", "running", "completed", "failed", "waiting_user" |
| tool_calls_made | int | How many tool calls this agent made |
| tool_calls_budget | int | Max tool calls allowed |
| evidence_produced | list[str] | Evidence IDs this agent created |
| started_at | datetime (optional) | When agent started |
| completed_at | datetime (optional) | When agent finished |
| summary | str | Human-readable summary of what agent did |

### AgentResult

What an agent returns to the orchestrator. Never written to run state directly.

| Field | Type | Description |
|-------|------|-------------|
| agent_id | str | Which agent produced this |
| agent_type | str | Agent type |
| success | bool | Whether agent completed without error |
| evidence_items | EvidenceItem[] | Evidence collected |
| derived_insights | DerivedInsight[] | Conclusions drawn |
| summary | str | Human-readable summary |
| spawn_requests | SpawnRequest[] | New hypotheses discovered |
| error | str (optional) | Error message if failed |
| company_understanding | CompanyUnderstanding (optional) | Set by CompanyProfiler |
| industry_context | IndustryContext (optional) | Set by IndustryAnalyst |
| pain_points | PainPoint[] | Set by PainInvestigator |
| hypotheses | Hypothesis[] | Set by HypothesisFormer |
| adaptive_report | AdaptiveReport (optional) | Set by ReportSynthesizer |

### AgentScope

Controls what context an agent can see via AgentContextProvider.

| Scope | Can access |
|-------|-----------|
| COMPANY_PROFILER | intake, evidence |
| INDUSTRY_ANALYST | intake, evidence |
| PAIN_INVESTIGATOR | intake, company_understanding, industry_context, briefings, insights, evidence |
| HYPOTHESIS_FORMER | all above + pain_points |
| HYPOTHESIS_TESTER | all above + hypotheses |
| REPORT_SYNTHESIZER | all above + hypotheses |

---

## Supporting Types

### DerivedInsight

A conclusion drawn from evidence. Not raw evidence itself. Stored in SynthesisStore.

| Field | Type | Description |
|-------|------|-------------|
| insight_id | str | Unique ID |
| phase | str | Which phase produced this (e.g., "grounding", "hypothesis_testing") |
| statement | str | The conclusion (e.g., "Their dispatch is manual, costing ~15% efficiency") |
| supporting_evidence_ids | list[str] | Raw evidence this was derived from |
| confidence | float | How confident we are in this conclusion |
| produced_by_agent | str | Which agent drew this conclusion |

### SpawnRequest

A new hypothesis discovered during testing. Created by HypothesisTester when it finds something unexpected.

| Field | Type | Description |
|-------|------|-------------|
| requesting_agent | str | Which tester found this |
| reason | str | Why this should be investigated |
| suggested_hypothesis | str | The hypothesis statement |
| priority | str | "high", "medium", or "low" |

### UserInteractionPoint

A question surfaced to the user mid-pipeline.

| Field | Type | Description |
|-------|------|-------------|
| interaction_id | str | Unique ID |
| run_id | str | Which run |
| interaction_type | str | "interesting_finding", "confirmation", or "ambiguity" |
| message | str | The question or finding |
| context | dict | Additional context |
| agent_source | str | Which agent surfaced this |
| requires_response | bool | Whether the pipeline is blocked waiting for an answer |
| response | str (optional) | User's response once provided |

### ReportFeedback

User feedback on the report during review.

| Field | Type | Description |
|-------|------|-------------|
| feedback_type | str | "edit" (change wording), "deepen" (re-test), "reinvestigate" (full re-run) |
| target_section | str | Which section to change (e.g., "executive_summary", "opportunity:{hyp_id}") |
| instruction | str | What the user wants changed |

### Enrichment types

| Type | Description |
|------|-------------|
| EnrichmentCategory | technology, financials, operations, pain_points, constraints, corrections, additional_context |
| EnrichmentInput | One piece of new evidence: category, title, detail, affected_hypothesis_ids, confidence |
| EnrichResponse | Result of enrichment: evidence_added, hypotheses_affected, deltas (confidence before/after) |
| HypothesisDelta | Per-hypothesis comparison: confidence_before, confidence_after, status_before, status_after |

---

## UI Contract Types

These types drive the frontend from the backend. The frontend renders
whatever the API tells it to render.

### UIHints

Returned by `GET /v1/runs/{id}/ui`. Tells the frontend what to show.

| Field | Type | Description |
|-------|------|-------------|
| stage_title | str | Display title for current stage |
| stage_description | str | What's happening |
| progress | list[dict] | Pipeline progress indicators |
| actions | UIAction[] | Buttons the user can click |
| editable_fields | EditableField[] | Form fields to display |
| budget_view | BudgetView | Remaining budget counters |
| agent_message | str (optional) | Message from an agent (e.g., a question) |

### UIAction

A button in the UI.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Action identifier |
| label | str | Button text |
| endpoint | str | API endpoint to call |
| method | str | HTTP method |
| enabled | bool | Whether the button is clickable |
| confirm | bool | Whether to show a confirmation dialog |

### TraceEvent

One entry in the audit trail.

| Field | Type | Description |
|-------|------|-------------|
| event_id | str | UUID |
| run_id | str | Which run |
| timestamp | datetime | When it happened |
| event_type | str | One of 46 EventType values |
| payload | dict | Event-specific data |
