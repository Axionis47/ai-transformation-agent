# System State — AI Transformation Agent

> Last updated: 2026-03-28 (sprints G-K: progressive evidence, user controls, feedback, frontend redesign)
> Read time: 5 minutes

---

## What works now

Full multi-agent hypothesis-driven pipeline, end to end:

```
INTAKE → GROUNDING (profiler ‖ analyst) → synthesis
       → DEEP RESEARCH (pain investigator) → synthesis
       → HYPOTHESIS FORMATION → HYPOTHESIS TESTING (parallel per hypothesis)
       → confidence-driven retest → spawn handling → synthesis
       → REPORT SYNTHESIS → REVIEW → PUBLISHED
```

- Orchestrator drives all phases as pure Python control flow (not an LLM agent)
- Inter-phase synthesis compresses phase output into constant-size briefings via LLM
- Agents run ReAct loops (THINK → ACT → OBSERVE) with scoped context
- Hypotheses carry full causal reasoning chains, not just pass/fail
- Report is adaptive — structure follows evidence, not a fixed template
- **User controls wired**: depth slider (1-10) scales agent steps + hypothesis count; confidence slider (0.3-1.0) controls validation/rejection thresholds
- **Progressive evidence focus**: evidence tagged by dimension/process_area; agents query focused evidence via dimension filters; phase-aware promotion thresholds
- **Report feedback system**: inline editing, targeted re-test, section highlighting; 3 feedback types (edit/deepen/reinvestigate) with appropriate backtracking
- **Evidence annex in report**: filterable, source-linked, scroll-to anchors
- **Interaction modal**: mid-run finding surfacing between agents and user
- **Frontend redesigned**: new sidebar + header shell, phase-based run page, adaptive report page with feedback controls

---

## Pipeline flow (detailed)

| # | Phase | Status | Agent(s) | What happens |
|---|-------|--------|----------|--------------|
| 1 | **Intake** | INTAKE | — | User provides company_name, industry, optional notes. No model call. |
| 2 | **Grounding** | GROUNDING | CompanyProfiler ‖ IndustryAnalyst | Two agents run in parallel. Profiler builds CompanyUnderstanding; Analyst builds IndustryContext. Both use Gemini grounding + Google Search. |
| — | *synthesis* | — | PhaseSynthesizer | LLM compresses grounding outputs into a constant-size briefing for later phases. |
| 3 | **Deep Research** | DEEP_RESEARCH | PainInvestigator | Discovers operational pain points with severity, workarounds, process mapping. Uses grounding + RAG. |
| — | *synthesis* | — | PhaseSynthesizer | Compresses deep research into briefing. |
| 4 | **Hypothesis Formation** | HYPOTHESIS_FORMATION | HypothesisFormer | Reasons over all prior evidence to form hypotheses. Context-only (no tool calls). Produces up to max_hypotheses (scaled by depth). |
| 5 | **Hypothesis Testing** | HYPOTHESIS_TESTING | HypothesisTester (×N, parallel) | One tester per hypothesis, all in parallel. Stress-tests via disconfirmation search (grounding + RAG). Confidence-driven depth: low-confidence hypotheses get a second pass if budget allows. Spawn requests handled if budget remains. |
| — | *synthesis* | — | PhaseSynthesizer | Compresses testing results into briefing. |
| 6 | **Report** | REPORT → SYNTHESIS | ReportSynthesizer | Single-shot: hypotheses + reasoning chains + evidence → AdaptiveReport. Structure follows evidence, not template. |
| 7 | **Review** | REVIEW | — | User reviews report. Can approve (→ PUBLISHED), investigate (→ HYPOTHESIS_TESTING), or refine (edit/deepen/reinvestigate). |

---

## User controls

| Control | Range | Effect |
|---------|-------|--------|
| **Depth slider** | 1-10 (default 5) | Scales agent MAX_STEPS: profiler 2-12, analyst 2-8, investigator 2-12, former 2-8, tester 2-8. Also scales max_hypotheses (2-10). Formula: `step = max(lo, min(hi, round(base * depth/5)))` |
| **Confidence slider** | 0.3-1.0 (default 0.7) | Sets validation threshold for hypotheses. Rejection threshold = confidence × 0.3. Higher = stricter validation, fewer validated hypotheses. |

Both are set via `config.reasoning.depth_budget` and `config.reasoning.confidence_threshold`, wired from frontend sliders through the run config snapshot.

---

## Research agents (6)

| Agent | File | What it does | Tools | Runs in |
|---|---|---|---|---|
| **CompanyProfiler** | `engines/agents/company_profiler.py` | Builds factual CompanyUnderstanding (what they do, revenue, scale, tech) | GROUND | Grounding (parallel) |
| **IndustryAnalyst** | `engines/agents/industry_analyst.py` | Builds IndustryContext (trends, competition, regulation, AI adoption) | GROUND | Grounding (parallel) |
| **PainInvestigator** | `engines/agents/pain_investigator.py` | Discovers operational pain points with severity and workarounds | GROUND + RAG | Deep Research |
| **HypothesisFormer** | `engines/agents/hypothesis_former.py` | Forms hypotheses from evidence — reasons, does not template-match | context only | Hypothesis Formation |
| **HypothesisTester** | `engines/agents/hypothesis_tester.py` | Stress-tests one hypothesis via disconfirmation search (one per hypothesis, parallel) | GROUND + RAG | Hypothesis Testing |
| **ReportSynthesizer** | `engines/agents/report_synthesizer.py` | Single-shot: hypotheses + reasoning chains → AdaptiveReport | context only | Report |

All agents extend `BaseResearchAgent` (`engines/agents/base.py`):
- ReAct loop with configurable MAX_STEPS (scaled by depth slider)
- Returns typed `AgentResult` — never mutates shared state
- Budget-aware: checks remaining budget before every tool call
- Traced: emits AGENT_SPAWNED, step events, AGENT_COMPLETED/FAILED

---

## Context & synthesis layer

| Component | File | Purpose |
|---|---|---|
| **AgentContextProvider** | `engines/context_provider.py` | Scoped, pull-based context per agent. Each scope sees only what it needs (e.g., profiler sees intake only; former sees everything). Supports `query_evidence(dimension, process_area)` for focused retrieval. Builds constant-size text briefings via `build_context_briefing()`. |
| **SynthesisStore** | `services/memory/synthesis_store.py` | Stores derived insights and inter-phase briefings. Not raw evidence — conclusions drawn from evidence. Later agents read insights instead of re-deriving. In-memory singleton (module-level dicts). |
| **HypothesisTracker** | `engines/hypothesis_tracker.py` | Hypothesis lifecycle: form → test → revise → validate/reject. Tracks full causal reasoning chain per hypothesis. Converts validated hypotheses to ReportOpportunity. Provides `get_low_confidence(threshold)` for confidence-driven depth. |
| **PhaseSynthesizer** | `engines/phase_synthesis.py` | LLM-powered compression between phases. Produces constant-size briefings so later agents get context, not data dumps. |
| **Orchestrator** | `engines/orchestrator.py` | Pure Python pipeline controller. Only thing that writes to run_manager. Manages parallel dispatch, result promotion, synthesis timing, user-control scaling. |
| **OrchestratorHelpers** | `engines/orchestrator_helpers.py` | promote_result(), synthesize_between_phases(), test_hypotheses(), handle_spawns(), generate_report() |

### Context scoping rules

| Agent Scope | Can see |
|---|---|
| COMPANY_PROFILER | intake, evidence |
| INDUSTRY_ANALYST | intake, evidence |
| PAIN_INVESTIGATOR | intake, company_understanding, industry_context, briefings, insights, evidence |
| HYPOTHESIS_FORMER | all of above + pain_points |
| HYPOTHESIS_TESTER | all of above + hypotheses |
| REPORT_SYNTHESIZER | all of above + hypotheses |

---

## Progressive evidence focus

Evidence is now tagged and filterable:

- **EvidenceItem.dimension** — `"technology"` | `"scale"` | `"revenue"` | `"operations"` | `"industry"` | `"pain_point"` | `"hypothesis_test"`
- **EvidenceItem.process_area** — `"dispatch"` | `"billing"` | `"maintenance"` | `"tracking"` | `""` (if not process-specific)
- **EvidenceItem.produced_by** — which agent produced the evidence

**Phase-aware promotion thresholds** (`services/memory/promotion.py`):
- Grounding: relevance >= 0.3 (cast wide net)
- Deep Research: relevance >= 0.4 (more selective)
- Hypothesis Testing: relevance >= 0.5 (high bar for test evidence)

**Focused querying**: `AgentContextProvider.query_evidence(dimension="technology", top_k=3)` — agents pull only what they need. `build_context_briefing()` groups evidence summaries by dimension (technology, operations, scale, pain_point).

---

## Report system

**AdaptiveReport** — structure follows evidence, not a fixed template:
- `executive_summary` — top-level narrative
- `key_insight` — the single most important finding
- `opportunities` — list of ReportOpportunity (title, narrative, tier, confidence, risks, conditions, approach)
- `reasoning_chain` — how we got from evidence to conclusions
- `confidence_assessment` — what we're confident about and why
- `what_we_dont_know` — explicitly stated gaps
- `recommended_next_steps` — actionable items
- `evidence_annex` — filterable, source-linked evidence list
- `agent_activity_summary` — what each agent did

**Feedback system** (3 types via `POST /v1/runs/{id}/report/refine`):
- **edit** — re-runs ReportSynthesizer with feedback context, stays at REVIEW
- **deepen** — targeted re-test of specific hypotheses (by hypothesis_id), then re-generates report
- **reinvestigate** — backtracks to DEEP_RESEARCH for full re-run

Feedback is stored in `run.feedback_history` (list of ReportFeedback).

---

## API endpoints

### Core (runs.py)

| Endpoint | Method | Purpose |
|---|---|---|
| `/v1/runs` | POST | Create a new run |
| `/v1/runs/{id}` | GET | Get full run state |
| `/v1/runs/{id}/company-intake` | PUT | Save company intake |
| `/v1/runs/{id}/trace` | GET | Get trace events for run |

### UI contract (ui.py)

| Endpoint | Method | Purpose |
|---|---|---|
| `/v1/runs/{id}/ui` | GET | Backend-driven UI hints (stage-aware actions, fields, budget) |

### Pipeline (thought.py)

| Endpoint | Method | Purpose |
|---|---|---|
| `/v1/runs/{id}/start` | POST | Triggers the multi-agent pipeline (or legacy reasoning loop based on orchestration.mode) |
| `/v1/runs/{id}/assumptions/confirm` | POST | Confirm assumptions |
| `/v1/runs/{id}/answer` | POST | User answers MID question |

### RAG (rag.py)

| Endpoint | Method | Purpose |
|---|---|---|
| `/v1/runs/{id}/rag:query` | POST | Query the Wins KB |

### Grounding (grounding.py)

| Endpoint | Method | Purpose |
|---|---|---|
| `/v1/runs/{id}/ground` | POST | Run Gemini grounding call |

### Synthesis (pitch.py)

| Endpoint | Method | Purpose |
|---|---|---|
| `/v1/runs/{id}/synthesize` | POST | Run pitch synthesis |
| `/v1/runs/{id}/publish` | POST | Publish the report |
| `/v1/runs/{id}/refine` | POST | Refine assumptions/opportunities (legacy) |
| `/v1/runs/{id}/evidence` | GET | Get all evidence items |
| `/v1/runs/{id}/report` | GET | Get the report |
| `/v1/runs/{id}/opportunities` | GET | Get scored opportunities |

### Multi-agent (agents.py)

| Endpoint | Method | Purpose |
|---|---|---|
| `/v1/runs/{id}/agents` | GET | List all agent states for a run |
| `/v1/runs/{id}/hypotheses` | GET | List all hypotheses with status/confidence |
| `/v1/runs/{id}/hypotheses/{hid}` | GET | Get single hypothesis with full reasoning chain |
| `/v1/runs/{id}/interactions` | GET | List user interaction points (pending/resolved counts) |
| `/v1/runs/{id}/interactions/{iid}/respond` | POST | Respond to a user interaction point |
| `/v1/runs/{id}/review/approve` | POST | Approve report → transition to PUBLISHED |
| `/v1/runs/{id}/review/investigate` | POST | Return to HYPOTHESIS_TESTING for deeper investigation |
| `/v1/runs/{id}/report/refine` | POST | Refine report via feedback (edit/deepen/reinvestigate) |

### Health

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Health check |

---

## Frontend (redesigned)

### Shell

| Component | File | What it renders |
|---|---|---|
| **Sidebar** | `components/shell/Sidebar.tsx` | Navigation sidebar with run list |
| **Header** | `components/shell/Header.tsx` | Top header bar |

### Phase-based run page (`app/run/[id]/page.tsx`)

| Component | File | What it renders |
|---|---|---|
| **RunPhaseContent** | `components/RunPhaseContent.tsx` | Phase-aware content switching based on run status |
| **PhaseProgress** | `components/PhaseProgress.tsx` | Non-linear phase progress indicator |
| **AgentActivityPanel** | `components/AgentActivityPanel.tsx` | Live agent states with parallel execution display |
| **HypothesisList** | `components/HypothesisList.tsx` | Filterable list of hypotheses by status |
| **HypothesisCard** | `components/cards/HypothesisCard.tsx` | Single hypothesis with confidence bar and status badge |
| **ConfidenceNarrative** | `components/ConfidenceNarrative.tsx` | Human-readable confidence display (high/moderate/low) |
| **ReasoningChain** | `components/ReasoningChain.tsx` | Visual reasoning chain (formed → tested → validated) |
| **InteractionModal** | `components/InteractionModal.tsx` | Mid-run finding surfacing — user responds to agent questions |

### Adaptive report page (`app/run/[id]/report/page.tsx`)

| Component | File | What it renders |
|---|---|---|
| **AdaptiveReportView** | `components/AdaptiveReportView.tsx` | Full report with evidence-linked opportunities |
| **EvidenceAnnex** | `components/EvidenceAnnex.tsx` | Filterable evidence list with source links and scroll-to anchors |
| **FeedbackButton** | `components/FeedbackButton.tsx` | Inline feedback controls (edit/deepen/reinvestigate) per section |

### Existing components (still functional)

IntakeForm, AssumptionsReview, ReasoningView, ReportView, OpportunityRow, EvidenceBlock, ProgressRail, BudgetPills, StageSection, DataRow, plus UI primitives (ScoreBar, Badge, Spinner, TierBadge), cards (EvidenceCard, AssumptionCard, OpportunityCard).

---

## Schemas (all in `core/schemas.py`)

### Multi-agent system

- **Hypothesis** — statement, category, target_process, confidence, evidence_for/against, evidence_conditions, analogous_engagements, conditions_for_success, risks, open_questions, test_results, reasoning_chain, formed_by_agent, tested_by_agent, parent_hypothesis_id
- **HypothesisStatus** — FORMING | TESTING | VALIDATED | REJECTED | NEEDS_USER_INPUT
- **TestResult** — test_type, finding, impact_on_confidence, evidence_ids
- **ReasoningStep** — step_type (formed_because, tested_with, contradicted_by, revised_because, validated_by), description, evidence_ids, confidence_delta
- **CompanyUnderstanding** — company_name, what_they_do, how_they_make_money, size_and_scale, technology_landscape, organizational_structure, confidence, evidence_ids
- **IndustryContext** — industry, key_trends, competitive_dynamics, regulatory_landscape, ai_adoption_level, confidence, evidence_ids
- **PainPoint** — pain_id, description, affected_process, severity, current_workaround, evidence_ids, confidence
- **AgentState** — agent_id, agent_type, status, tool_calls_made, tool_calls_budget, evidence_produced, started_at, completed_at, summary
- **AgentResult** — typed output from every agent (evidence, insights, domain outputs, spawn_requests)
- **DerivedInsight** — insight_id, phase, statement, supporting_evidence_ids, confidence, produced_by_agent
- **SpawnRequest** — requesting_agent, reason, suggested_hypothesis, priority
- **UserInteractionPoint** — interaction_id, run_id, interaction_type, message, context, agent_source, requires_response, response
- **AdaptiveReport** — run_id, executive_summary, key_insight, opportunities, reasoning_chain, confidence_assessment, what_we_dont_know, recommended_next_steps, evidence_annex, agent_activity_summary
- **ReportOpportunity** — title, hypothesis_id, narrative, tier, confidence, roi_estimate, evidence_summary, analogous_cases, risks, conditions_for_success, recommended_approach
- **ReportFeedback** — feedback_type (edit/deepen/reinvestigate), target_section, instruction
- **AgentScope** — enum controlling per-agent context visibility (6 scopes)
- **EvidenceItem additions** — dimension, process_area, produced_by fields
- **RunStatus additions** — GROUNDING, DEEP_RESEARCH, HYPOTHESIS_FORMATION, HYPOTHESIS_TESTING, REVIEW

---

## How to test

### Run the full pipeline

```bash
# Start backend
cd /Users/sid47/Desktop/ai-transformation-agent
python -m uvicorn api.app:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Create a run and start the pipeline
curl -X POST http://localhost:8000/v1/runs \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Acme Logistics", "industry": "logistics"}'

# Save company intake (use run_id from above)
curl -X PUT http://localhost:8000/v1/runs/{RUN_ID}/company-intake \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Acme Logistics", "industry": "logistics", "employee_count_band": "200-500"}'

# Start the multi-agent pipeline
curl -X POST http://localhost:8000/v1/runs/{RUN_ID}/start
```

### Inspect results

```bash
# See agent activity
curl http://localhost:8000/v1/runs/{RUN_ID}/agents

# See hypotheses
curl http://localhost:8000/v1/runs/{RUN_ID}/hypotheses

# See interactions (mid-run findings)
curl http://localhost:8000/v1/runs/{RUN_ID}/interactions

# See full run state (includes adaptive_report)
curl http://localhost:8000/v1/runs/{RUN_ID}

# Approve report
curl -X POST http://localhost:8000/v1/runs/{RUN_ID}/review/approve

# Or refine report with feedback
curl -X POST http://localhost:8000/v1/runs/{RUN_ID}/report/refine \
  -H "Content-Type: application/json" \
  -d '{"feedbacks": [{"feedback_type": "deepen", "target_section": "opportunity:hyp_001", "instruction": "Need more evidence on ROI"}]}'
```

### Run tests

```bash
pytest tests/ -q --tb=short
```

---

## What's NOT done yet

| Gap | Impact | Notes |
|---|---|---|
| Storage persistence | Medium | All state is in-memory dicts (SynthesisStore, EvidenceStore, run_manager). Firestore swap is Sprint 7. Interfaces are stable. |
| PDF export | Medium | AdaptiveReport renders in browser only. No downloadable PDF. |
| Cross-run memory | Medium | Each run is independent. No learning from past runs within the system. RAG has past engagements but no run-to-run memory. |
| SSE streaming | Medium | Pipeline runs synchronously. No real-time progress push to frontend. Frontend polls. |
| Eval rubrics | Medium | Framework exists but rubrics not written. No automated quality scoring yet. |
| Cloud deployment | Low | Local dev only. Cloud Run config not set up. |
| Multi-hop RAG chaining | Low | RAG supports it, but agents don't chain queries across steps yet. |

---

## Known issues

| Issue | Severity | Detail |
|---|---|---|
| HypothesisTracker is in-memory per Orchestrator instance | Medium | Not persisted across restarts. State lost if server restarts mid-pipeline. |
| SynthesisStore uses module-level dicts | Low | Works for single-process, breaks with multiple workers. |
| Budget shared across parallel agents | Low | Parallel agents (profiler + analyst) share a BudgetState. No lock — minor race condition possible. |
| Report synthesizer MAX_STEPS=1 | Info | Intentional: single-shot synthesis, no ReAct loop. Not a bug. |
| Spawn requests processed once | Low | If spawned hypotheses generate further spawn requests, they are not recursively handled. |
| Refine endpoint creates fresh tracker | Low | `report/refine` rebuilds HypothesisTracker from run state — works but loses any tracker-only state. |

---

## Data layer

| Asset | Count | Status |
|---|---|---|
| Past engagements | 22 records | Complete (7 industries, 3 solution shapes) |
| RAG chunks | 154 (22 x 7) | Indexed in ChromaDB |
| Prompt templates | 7 agent prompts + 1 synthesis | Current |

---

## Services

| Service | Status |
|---|---|
| RAG (ChromaDB) | Functional |
| Grounder (Gemini + Google Search) | Functional |
| Memory (evidence stores, promotion gate, contradiction detection) | Functional |
| Synthesis (SynthesisStore, PhaseSynthesizer) | Functional |
| Trace (structured event logging, 46 event types) | Functional |

---

## Contract documents

- `docs/RAG_CONTRACT.md` — chunk types, query patterns, success criteria
- `docs/MEMORY_CONTRACT.md` — shared vs private memory, evidence lifecycle, context routing
