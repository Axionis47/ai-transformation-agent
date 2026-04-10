# Pipeline

This document walks through the entire 7-phase pipeline in detail.
For each phase: what triggers it, what agent runs, what it reads,
what tools it uses, what it produces, what state transition happens,
and where to find the code.

---

## Overview

```
User enters company + industry
         |
         v
  Phase 1: INTAKE                 (no agent, pure input capture)
         |
         v
  Phase 2: GROUNDING              (CompanyProfiler || IndustryAnalyst)
         |                         parallel, both use Google Search
    [phase synthesis]
         |
         v
  Phase 3: DEEP RESEARCH          (PainInvestigator)
         |                         uses Google Search + RAG
    [phase synthesis]
         |
         v
  Phase 4: HYPOTHESIS FORMATION   (HypothesisFormer)
         |                         uses RAG only
         v
  Phase 5: HYPOTHESIS TESTING     (HypothesisTester x N, parallel)
         |                         uses Google Search + RAG
    [phase synthesis]              confidence-driven second pass
         |
         v
  Phase 6: REPORT SYNTHESIS       (ReportSynthesizer)
         |                         single LLM call, no tools
         v
  Phase 7: REVIEW                 (user approves, investigates, or refines)
         |
         v
      PUBLISHED
```

Between phases 2-3, 3-4, and 5-6, a PhaseSynthesizer compresses
the output into a constant-size briefing. This prevents prompt growth.

---

## Phase 1: Company Intake

**Status transition**: CREATED -> INTAKE

**What happens**:
- User submits company name, industry, optional employee count band, notes, and constraints
- User sets two controls: depth slider (1-10) and confidence threshold (0.3-1.0)
- No LLM call. Pure input capture and validation.

**API endpoint**: `PUT /v1/runs/{id}/company-intake`

**Data stored**: `CompanyIntake` on the Run object

**Code**: `api/routes/runs.py` -> `core/run_manager.update_intake()`

**Trace events**: COMPANY_INTAKE_SAVED

---

## Phase 2: Grounding

**Status transition**: INTAKE -> GROUNDING

**What happens**:
Two agents run in parallel via `asyncio.gather()`. They share a BudgetState
but have no other shared data.

### CompanyProfiler

**File**: `engines/agents/company_profiler.py`
**Prompt**: `prompts/agent_company_profiler.md`
**Tools**: GROUND only (Google Search via Gemini)
**Steps**: 2-12 (scaled by depth slider, base 6)

**Researches 5 dimensions**:
1. what_they_do -- what the company does
2. how_they_make_money -- revenue model
3. size_and_scale -- employee count, revenue, locations
4. technology_landscape -- tech stack, platforms, tools
5. organizational_structure -- teams, departments, hierarchy

**ReAct loop**:
1. THINK: LLM looks at which dimensions are still "unknown", picks the weakest one, formulates a Google Search query
2. ACT: Calls `grounder.ground(query)` which hits Gemini with Google Search tool
3. OBSERVE: New evidence tagged with current dimension (e.g., "technology") and agent ID
4. Repeat until all 5 dimensions filled, budget exhausted, or max steps reached
5. STOP: builds CompanyUnderstanding with confidence = filled_dimensions / 5

**Dedup**: Tracks past queries, stops if LLM generates a duplicate

**Output**: `AgentResult` with:
- `company_understanding`: CompanyUnderstanding (5 dimension values + confidence)
- `evidence_items`: all EvidenceItems from grounding calls
- `derived_insights`: one DerivedInsight per filled dimension

### IndustryAnalyst

**File**: `engines/agents/industry_analyst.py`
**Prompt**: `prompts/agent_industry_analyst.md`
**Tools**: GROUND only (Google Search via Gemini)
**Steps**: 2-8 (scaled by depth slider, base 4)

**Researches 4 dimensions**:
1. key_trends -- list of industry trends
2. competitive_dynamics -- competitive landscape
3. regulatory_landscape -- regulations, compliance
4. ai_adoption_level -- how far the industry has adopted AI

**ReAct loop**: Same pattern as CompanyProfiler. Confidence = filled_dimensions / 4.

**Output**: `AgentResult` with:
- `industry_context`: IndustryContext (4 dimension values + confidence)
- `evidence_items`: all EvidenceItems
- `derived_insights`: one DerivedInsight per filled dimension

### After both agents complete

The orchestrator calls `promote_result()` for each agent's output, which:
- Adds evidence through the PromotionGate (validates, dedupes, stores)
- Saves derived insights to the SynthesisStore
- Updates CompanyUnderstanding and IndustryContext on the Run

Then `synthesize_between_phases("grounding")` is called:
- PhaseSynthesizer uses an LLM to compress both agents' findings into a 3-5 sentence briefing
- Briefing stored in SynthesisStore for the next phase

**Code**: `engines/orchestrator.py:98-113`, `engines/orchestrator_helpers.py:40-60`

**Trace events**: REASONING_LOOP_STARTED, AGENT_SPAWNED (x2), AGENT_COMPLETED (x2), EVIDENCE_PROMOTED (multiple)

---

## Phase 3: Deep Research

**Status transition**: GROUNDING -> DEEP_RESEARCH

### PainInvestigator

**File**: `engines/agents/pain_investigator.py`
**Prompt**: `prompts/agent_pain_investigator.md`
**Tools**: GROUND (Google Search) + RAG (past engagements KB)
**Steps**: 2-12 (scaled by depth slider, base 6)

**What it does**: Discovers operational pain points by combining:
- Google Search for company-specific problems (complaints, known issues, operational challenges)
- RAG retrieval for analogous pain patterns from past consulting engagements

**Context it receives** (via scoped AgentContextProvider):
- Company intake
- CompanyUnderstanding from Phase 2
- IndustryContext from Phase 2
- Grounding phase briefing
- Derived insights from Phase 2
- Focused evidence filtered by dimension (technology + scale)

**ReAct loop**:
1. THINK: LLM reviews company profile, industry context, and existing pain points. Decides whether to search Google (company-specific pain) or RAG (analogous patterns). Formulates query.
2. ACT: Calls `grounder.ground()` or `rag.query()` depending on the action
3. OBSERVE: New evidence tagged with dimension="pain_point" and process_area (e.g., "dispatch", "billing")
4. LLM returns cumulative list of pain_points each step (not incremental)
5. Repeat until enough pain points found or budget exhausted

**Output**: `AgentResult` with:
- `pain_points`: list of PainPoint (description, affected_process, severity, current_workaround, confidence)
- `evidence_items`: all EvidenceItems
- `derived_insights`: one DerivedInsight per pain point

**Confidence formula**: 0.3 + (min(evidence_count, 10) * 0.06), max 0.9

### After agent completes

Orchestrator promotes results, then synthesizes:
- `synthesize_between_phases("deep_research")` produces a 4-6 sentence briefing
- Briefing captures: company overview (from prior briefing), top pain points, which are most amenable to AI, evidence quality assessment

**Code**: `engines/orchestrator.py:115-128`

**Trace events**: REASONING_LOOP_STARTED, AGENT_SPAWNED, AGENT_COMPLETED, EVIDENCE_PROMOTED (multiple)

---

## Phase 4: Hypothesis Formation

**Status transition**: DEEP_RESEARCH -> HYPOTHESIS_FORMATION

### HypothesisFormer

**File**: `engines/agents/hypothesis_former.py`
**Prompt**: `prompts/agent_hypothesis_former.md`
**Tools**: RAG only (no Google Search allowed -- GROUND actions are converted to RAG)
**Steps**: 2-8 (scaled by depth slider, base 4)

**What it does**: Creates testable AI opportunity hypotheses from all accumulated evidence. Uses RAG to find analogous past engagements that validate potential opportunities.

**Context it receives**:
- Everything from prior phases (intake, company understanding, industry context, pain points)
- All briefings and derived insights
- Focused evidence by dimension (pain_point + technology)

**ReAct loop**:
1. THINK: LLM reviews all context. Decides to search RAG for analogous past engagements or output hypotheses. Returns cumulative hypothesis list.
2. ACT: RAG query only. If LLM requests GROUND, it gets converted to RAG.
3. On last step: forced to STOP and output hypotheses regardless of LLM preference
4. After all steps: raw hypotheses registered with HypothesisTracker

**Hypothesis registration**:
- Each raw hypothesis (from LLM JSON) is registered via `tracker.form()`
- Creates a Hypothesis with status=FORMING, initial reasoning chain entry
- Max hypotheses capped by depth slider (2-10, base 5)
- Evidence IDs linked (from LLM-cited IDs or fallback to collected evidence)

**Output**: `AgentResult` with:
- `hypotheses`: list of Hypothesis objects (statement, category, target_process, confidence, evidence_for)
- `evidence_items`: RAG retrieval results
- `derived_insights`: one per hypothesis

**Confidence formula**: 0.3 + (min(evidence_for_count, 6) * 0.08), max 0.85

**Code**: `engines/orchestrator.py:130-147`

**Trace events**: REASONING_LOOP_STARTED, AGENT_SPAWNED, AGENT_COMPLETED, HYPOTHESIS_FORMED (multiple)

---

## Phase 5: Hypothesis Testing

**Status transition**: HYPOTHESIS_FORMATION -> HYPOTHESIS_TESTING

This is the most complex phase. It has three sub-steps: initial testing, confidence-driven retesting, and spawn handling.

### Step 5a: Initial parallel testing

One HypothesisTester instance per hypothesis, all running in parallel via `asyncio.gather()`.

**File**: `engines/agents/hypothesis_tester.py`
**Prompt**: `prompts/agent_hypothesis_tester.md`
**Tools**: GROUND (Google Search) + RAG (past engagements)
**Steps**: 2-8 (scaled by depth slider, base 4)

**What it does**: Stress-tests a single hypothesis using a disconfirmation strategy. The agent actively searches for evidence that would disprove the hypothesis.

**Context it receives**:
- Everything from prior phases
- The specific hypothesis being tested
- Evidence focused on the hypothesis's target process
- Confirmed findings from prior phases (so it doesn't re-research known facts)
- Known pain points

**ReAct loop**:
1. THINK: LLM reviews hypothesis, existing evidence, and current confidence. Decides which test dimension to explore (market fit, prerequisites, analogous cases, regulation, ROI). Formulates a disconfirmation query.
2. ACT: GROUND or RAG
3. OBSERVE: New evidence tagged with dimension="hypothesis_test" and process_area matching hypothesis target
4. LLM returns test_result JSON with: test_type, finding, impact_on_confidence (-0.20 to +0.20)
5. HypothesisTracker records the test and adjusts confidence
6. LLM returns recommendation: continue, validate, validate_with_conditions, reject

**Early stop conditions**:
- Confidence drops below rejection threshold -> REJECTED
- LLM recommends validate_with_conditions and provides conditions -> VALIDATED (with conditions)
- LLM recommends validate, confidence > threshold, and 3+ tests done -> VALIDATED
- Duplicate query detected -> STOP

**Spawn requests**: If the tester discovers a new potential opportunity during testing, it can emit a SpawnRequest with a suggested_hypothesis. These are handled after all testing completes.

**Output per tester**: `AgentResult` with:
- `hypotheses`: [the tested hypothesis with updated status/confidence]
- `evidence_items`: evidence from testing
- `derived_insights`: summary of test outcome
- `spawn_requests`: any new hypotheses discovered

### Step 5b: Confidence-driven depth

After the initial round, if budget remains, the orchestrator checks for low-confidence hypotheses (below the validation threshold) and re-tests them:

```python
if has_budget(budget, config):
    low = tracker.get_low_confidence(validate_threshold)
    if low:
        await test_hypotheses(run_id, low, budget, ...)
```

This gives borderline hypotheses a second chance with fresh queries.

### Step 5c: Spawn handling

If any tester emitted spawn requests, the orchestrator:
1. Forms each suggested hypothesis via the tracker
2. Adds them to the run
3. Tests them (if budget allows)

### Finalization

After all testing, any hypotheses still in TESTING or FORMING status are force-resolved:
- Confidence >= validation threshold -> VALIDATED
- Confidence < rejection threshold (threshold * 0.3) -> REJECTED
- Between thresholds -> VALIDATED with conditions

All finalized hypotheses are synced to run state via `rm.add_hypotheses()`.

Then `synthesize_between_phases("hypothesis_testing")` compresses results.

**Code**: `engines/orchestrator.py:148-202`, `engines/orchestrator_helpers.py:84-144`

**Trace events**: REASONING_LOOP_STARTED, AGENT_SPAWNED (x N), HYPOTHESIS_TESTED, HYPOTHESIS_VALIDATED, HYPOTHESIS_REJECTED, SPAWN_REQUESTED

---

## Phase 6: Report Synthesis

**Status transition**: HYPOTHESIS_TESTING -> SYNTHESIS -> REPORT

### ReportSynthesizer

**File**: `engines/agents/report_synthesizer.py`
**Prompt**: `prompts/agent_report_synthesizer.md`
**Tools**: None (single LLM call via grounder.reason(), no search, no RAG)
**Steps**: 1 (single shot, no ReAct loop)

**What it does**: Takes all validated hypotheses with their full reasoning chains and synthesizes them into a client-facing AdaptiveReport. This is a single LLM call, not an iterative loop.

**Input construction**:
The agent builds structured input blocks:
1. **Validated hypothesis blocks**: For each validated/testing hypothesis, a formatted block with statement, category, confidence, reasoning chain, evidence citations, conditions, and risks
2. **Rejected summary**: One-line summaries of rejected hypotheses
3. **Key insights**: Derived insights from all phases

Each hypothesis block includes actual evidence citations (evidence_id + snippet + source type + relevance score) so the LLM can reference specific evidence in the report.

**Context it receives**:
- Full context briefing (intake, company understanding, industry context, pain points, insights, evidence)
- All hypotheses (validated sorted by confidence first, then rejected)
- Phase briefings from all prior synthesis steps

**Output parsing**:
The LLM returns JSON with: executive_summary, key_insight, opportunities (list), reasoning_chain, confidence_assessment, what_we_dont_know, recommended_next_steps.

Each opportunity includes: title, hypothesis_id, narrative, tier (easy/medium/hard), confidence, evidence_summary with cited IDs, risks, conditions_for_success, recommended_approach.

**Fallback**: If the LLM fails or returns unparseable output, a fallback report is built directly from hypothesis data (statement as title, tracker narrative as body).

**Feedback mode**: When the user provides feedback on a previous report, the synthesizer receives both the previous report JSON and the feedback instructions. The prompt tells the LLM to change only targeted sections and return all other sections identical.

**Output**: `AgentResult` with:
- `adaptive_report`: AdaptiveReport

The orchestrator stores the report via `rm.store_adaptive_report()` and transitions to REVIEW.

**Code**: `engines/orchestrator.py:204-220`, `engines/orchestrator_helpers.py:147-177`

**Trace events**: AGENT_SPAWNED, AGENT_COMPLETED, REPORT_STRUCTURE_DECIDED

---

## Phase 7: Review

**Status transition**: REPORT -> REVIEW -> PUBLISHED (or backtrack)

**What happens**: The user reviews the AdaptiveReport and decides what to do next.

### Action: Approve

**API endpoint**: `POST /v1/runs/{id}/review/approve`
**Transition**: REVIEW -> PUBLISHED
**What it does**: Marks the run as published. Report is final.

### Action: Investigate

**API endpoint**: `POST /v1/runs/{id}/review/investigate`
**Transition**: REVIEW -> HYPOTHESIS_TESTING
**What it does**: Returns to hypothesis testing to re-examine specific hypotheses.

### Action: Refine

**API endpoint**: `POST /v1/runs/{id}/report/refine`
**What it does**: Depends on the feedback type.

Three feedback types in `ReportFeedback`:

1. **edit** -- Re-synthesize the report with specific wording/content changes
   - Stays at REVIEW status
   - Calls `generate_report()` with the feedback + previous report
   - Synthesizer operates in editing mode (changes only targeted sections)

2. **deepen** -- Re-test targeted hypotheses with more depth
   - Re-runs HypothesisTesters for specified hypotheses
   - Force-validates/rejects based on thresholds
   - Re-synthesizes report with updated hypothesis data
   - Stays at REVIEW

3. **reinvestigate** -- Full backtrack
   - Transition: REVIEW -> DEEP_RESEARCH
   - Re-runs from Phase 3 (PainInvestigator) forward
   - Complete re-analysis with accumulated context

### Action: Enrich

**API endpoint**: `POST /v1/runs/{id}/enrich`
**What it does**: User (or analyst) adds new evidence to the run.

**Flow** (handled in `engines/enrichment.py` + `api/routes/agents.py`):
1. `prepare_enrichment()` converts user inputs to EvidenceItems with source_type=USER_PROVIDED
2. Auto-detects affected hypotheses by matching dimension and process area
3. Snapshots pre-enrichment confidence for comparison
4. Adds evidence through run_manager (goes through PromotionGate)
5. Re-tests only affected hypotheses
6. Force-validates/rejects based on thresholds
7. Re-generates report
8. Returns confidence deltas (before/after per hypothesis)

**Enrichment categories**: technology, financials, operations, pain_points, constraints, corrections, additional_context

Each category maps to an evidence dimension (e.g., technology -> "technology", corrections -> "hypothesis_test").

**Code**: `api/routes/agents.py`, `engines/enrichment.py`

**Trace events**: RUN_PUBLISHED (on approve), PHASE_BACKTRACK (on reinvestigate)

---

## Cross-cutting: The ReAct Loop

All research agents (except ReportSynthesizer) follow this loop defined in `engines/agents/base.py`:

```
1. Build context briefing from AgentContextProvider
2. For each step (up to MAX_STEPS):
   a. THINK: Send context + system prompt to LLM via grounder.reason()
      LLM returns JSON: {action, query, reasoning, ...domain fields}
   b. If action == "STOP": break
   c. ACT: Execute the tool
      - GROUND: grounder.ground(query) -> GroundingResult with evidence
      - RAG: rag.query(query) -> RAGQueryResult with evidence
   d. OBSERVE: Tag new evidence, extract domain-specific insights
   e. Update context briefing with latest findings
3. Build typed AgentResult from accumulated evidence and domain data
```

The LLM responds with JSON that includes the action, query, reasoning, and
any domain-specific fields (current_assessment, pain_points, test_result, hypotheses).
JSON is extracted from the LLM response by `core/json_parser.py` which handles
markdown code fences and embedded JSON.

---

## Cross-cutting: Budget Sharing

All agents in a run share a single `BudgetState` object. This means:
- CompanyProfiler and IndustryAnalyst (running in parallel) compete for the same search budget
- Later agents may have less budget if earlier agents used more
- Each agent checks remaining budget before every tool call
- When budget runs out, the agent works with what it has

Budget is tracked at two levels for Google Search:
- **Query level**: Each Gemini grounding call can trigger multiple Google Search queries. The actual query count is extracted from grounding metadata.
- **Call level**: Defense-in-depth cap on total Gemini API calls regardless of query count.

---

## Cross-cutting: Depth Scaling

The user's depth slider (1-10, default 5) scales every agent's step count using:

```
scale = depth / 5.0
agent_steps = max(2, min(cap, round(base * scale)))
max_hypotheses = max(2, min(10, round(5 * scale)))
```

At depth 1: every agent gets minimum 2 steps, max 2 hypotheses. Fast, shallow.
At depth 10: agents get maximum steps, up to 10 hypotheses. Thorough, expensive.

The confidence threshold (0.3-1.0, default 0.7) controls:
- Validation threshold = confidence_threshold
- Rejection threshold = confidence_threshold * 0.3
- Higher threshold = stricter validation, fewer hypotheses pass, more get "validated with conditions"

---

## Cross-cutting: Phase Synthesis

After phases 2, 3, and 5, the orchestrator calls PhaseSynthesizer to compress outputs.

**File**: `engines/phase_synthesis.py`

**How it works**:
1. Gathers the phase's key outputs (company understanding, pain points, hypotheses, etc.)
2. Formats them as structured text
3. Calls `grounder.reason()` (pure LLM, no search, no budget cost) to compress into 3-6 sentences
4. Stores the briefing in SynthesisStore
5. Next phase's agents read this briefing via `context_provider.get_phase_briefing()`

**Why it matters**: Without synthesis, each phase would pass raw evidence to the next, and prompts would grow without bound. Synthesis keeps agent inputs at a predictable size while preserving the important information.

**Fallback**: If the LLM is unavailable, the raw context is truncated to 500 characters.
