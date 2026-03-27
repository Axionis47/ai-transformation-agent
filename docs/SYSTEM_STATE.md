# System State — AI Transformation Agent

> Last updated: 2026-03-27 (multi-agent architecture)
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

---

## Research Agents (6)

| Agent | File | What it does | Tools | Runs in |
|---|---|---|---|---|
| **CompanyProfiler** | `engines/agents/company_profiler.py` | Builds factual CompanyUnderstanding (what they do, revenue, scale, tech) | GROUND | Grounding (parallel) |
| **IndustryAnalyst** | `engines/agents/industry_analyst.py` | Builds IndustryContext (trends, competition, regulation, AI adoption) | GROUND | Grounding (parallel) |
| **PainInvestigator** | `engines/agents/pain_investigator.py` | Discovers operational pain points with severity and workarounds | GROUND + RAG | Deep Research |
| **HypothesisFormer** | `engines/agents/hypothesis_former.py` | Forms hypotheses from evidence — reasons, does not template-match | context only | Hypothesis Formation |
| **HypothesisTester** | `engines/agents/hypothesis_tester.py` | Stress-tests one hypothesis via disconfirmation search (one per hypothesis, parallel) | GROUND + RAG | Hypothesis Testing |
| **ReportSynthesizer** | `engines/agents/report_synthesizer.py` | Single-shot: hypotheses + reasoning chains → AdaptiveReport | context only | Report |

All agents extend `BaseResearchAgent` (`engines/agents/base.py`):
- ReAct loop with configurable MAX_STEPS (default 8, tester 6, report 1)
- Returns typed `AgentResult` — never mutates shared state
- Budget-aware: checks remaining budget before every tool call
- Traced: emits AGENT_SPAWNED, step events, AGENT_COMPLETED/FAILED

---

## Key Infrastructure

| Component | File | Purpose |
|---|---|---|
| **AgentContextProvider** | `engines/context_provider.py` | Scoped, pull-based context per agent. Each scope sees only what it needs (e.g., profiler sees intake only; former sees everything). |
| **SynthesisStore** | `services/memory/synthesis_store.py` | Stores derived insights and inter-phase briefings. Not raw evidence — conclusions drawn from evidence. |
| **HypothesisTracker** | `engines/hypothesis_tracker.py` | Hypothesis lifecycle: form → test → revise → validate/reject. Tracks full causal reasoning chain per hypothesis. Converts validated hypotheses to ReportOpportunity. |
| **PhaseSynthesizer** | `engines/phase_synthesis.py` | LLM-powered compression between phases. Produces constant-size briefings so later agents get context, not data dumps. |
| **Orchestrator** | `engines/orchestrator.py` | Pure Python pipeline controller. Only thing that writes to run_manager. Manages parallel dispatch, result promotion, synthesis timing. |
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

## New API Endpoints

All in `api/routes/agents.py`, mounted on `/v1/`:

| Endpoint | Method | Purpose |
|---|---|---|
| `/runs/{id}/agents` | GET | List all agent states for a run |
| `/runs/{id}/hypotheses` | GET | List all hypotheses with status/confidence |
| `/runs/{id}/hypotheses/{hid}` | GET | Get single hypothesis with full reasoning chain |
| `/runs/{id}/interactions` | GET | List user interaction points (pending/resolved counts) |
| `/runs/{id}/interactions/{iid}/respond` | POST | Respond to a user interaction point |
| `/runs/{id}/review/approve` | POST | Approve report → transition to PUBLISHED |
| `/runs/{id}/review/investigate` | POST | Return to HYPOTHESIS_TESTING for deeper investigation |

Previous endpoints (runs.py, ui.py) remain unchanged and working.

---

## New Frontend Components (7)

| Component | File | What it renders |
|---|---|---|
| **AgentActivityPanel** | `components/AgentActivityPanel.tsx` | Live agent states with parallel execution display |
| **HypothesisList** | `components/HypothesisList.tsx` | Filterable list of hypotheses by status |
| **HypothesisCard** | `components/cards/HypothesisCard.tsx` | Single hypothesis with confidence bar and status badge |
| **PhaseProgress** | `components/PhaseProgress.tsx` | Non-linear phase progress indicator |
| **ConfidenceNarrative** | `components/ConfidenceNarrative.tsx` | Human-readable confidence display (high/moderate/low) |
| **ReasoningChain** | `components/ReasoningChain.tsx` | Visual reasoning chain (formed → tested → validated) |
| **AdaptiveReportView** | `components/AdaptiveReportView.tsx` | Full report with evidence-linked opportunities |

---

## New Schemas

Added to `core/schemas.py` for the multi-agent system:

- **Hypothesis** — statement, category, confidence, evidence_for/against, reasoning_chain, test_results
- **HypothesisStatus** — FORMING | TESTING | VALIDATED | REJECTED | NEEDS_USER_INPUT
- **TestResult** — test_type, finding, impact_on_confidence, evidence_ids
- **ReasoningStep** — step_type (formed_because, tested_with, contradicted_by, revised_because, validated_by)
- **CompanyUnderstanding** — what_they_do, revenue model, scale, tech landscape
- **IndustryContext** — trends, competitive dynamics, regulatory landscape, AI adoption
- **PainPoint** — description, affected_process, severity, workaround
- **AgentState** — agent_id, type, status, tool_calls, evidence_produced, summary
- **AgentResult** — typed output from every agent (evidence, insights, domain outputs)
- **DerivedInsight** — conclusions drawn from evidence, not raw evidence
- **SpawnRequest** — agent requests additional hypothesis investigation
- **UserInteractionPoint** — mid-pipeline user interaction (interesting_finding, confirmation, ambiguity)
- **AdaptiveReport** — executive_summary, opportunities, reasoning_chain, what_we_dont_know
- **ReportOpportunity** — title, narrative, tier, confidence, risks, conditions_for_success
- **AgentScope** — enum controlling per-agent context visibility
- **RunStatus** additions: GROUNDING, DEEP_RESEARCH, HYPOTHESIS_FORMATION, HYPOTHESIS_TESTING, REVIEW

---

## How to Test

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

# See full run state (includes adaptive_report)
curl http://localhost:8000/v1/runs/{RUN_ID}

# Approve report
curl -X POST http://localhost:8000/v1/runs/{RUN_ID}/review/approve
```

### Run tests

```bash
pytest tests/ -q --tb=short
```

---

## What's NOT Done Yet

| Gap | Impact | Notes |
|---|---|---|
| Storage persistence | Medium | All state is in-memory dicts. Firestore swap is Sprint 7. Interfaces are stable. |
| Eval rubrics | Medium | Framework exists but rubrics not written. No automated quality scoring yet. |
| SSE streaming | Medium | Pipeline runs synchronously. No real-time progress push to frontend. Frontend polls. |
| Cloud deployment | Low | Local dev only. Cloud Run config not set up. |
| Multi-hop RAG chaining | Low | RAG supports it, but agents don't chain queries across steps yet. |

---

## Known Issues

| Issue | Severity | Detail |
|---|---|---|
| HypothesisTracker is in-memory per Orchestrator instance | Medium | Not persisted across restarts. State lost if server restarts mid-pipeline. |
| SynthesisStore uses module-level dicts | Low | Works for single-process, breaks with multiple workers. |
| Budget shared across parallel agents | Low | Parallel agents (profiler + analyst) share a BudgetState. No lock — minor race condition possible. |
| Report synthesizer MAX_STEPS=1 | Info | Intentional: single-shot synthesis, no ReAct loop. Not a bug. |
| Spawn requests processed once | Low | If spawned hypotheses generate further spawn requests, they are not recursively handled. |

---

## Data Layer (unchanged)

| Asset | Count | Status |
|---|---|---|
| Past engagements | 22 records | Complete (7 industries, 3 solution shapes) |
| RAG chunks | 154 (22 x 7) | Indexed in ChromaDB |
| Prompt templates | 7 agent prompts + 1 synthesis | Current |

---

## Services (unchanged)

| Service | Status |
|---|---|
| RAG (ChromaDB) | Functional |
| Grounder (Gemini + Google Search) | Functional |
| Memory (evidence stores, promotion gate) | Functional |
| Trace (structured event logging) | Functional |

---

## Contract Documents

- `docs/RAG_CONTRACT.md` — chunk types, query patterns, success criteria
- `docs/MEMORY_CONTRACT.md` — shared vs private memory, evidence lifecycle, context routing
