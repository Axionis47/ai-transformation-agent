# AI Opportunity Mapper — Master Instructions

> Claude Code reads this file at the start of every session.
> Read this fully before touching anything.

---

## What this system does

Takes a company name and industry, uses Gemini Google Search grounding (not website scraping)
to learn about the company, reasons iteratively over a Wins Knowledge Base of past engagements,
detects missing information and asks the user interactively, and produces 3-tier AI opportunity
recommendations with full traceability, evidence citations, and budget controls.

Target: Tenex onsite interview submission.
Every conclusion is traced to its evidence source.
Budget hard caps on search queries and RAG queries are enforced at runtime.

---

## Architecture philosophy - non-negotiable

These rules govern how every piece of this system is built. No exceptions.

### Agent-Orchestrator pattern (10 rules)

1. Orchestrator controls flow, validates outputs, calls tools, and is the ONLY thing that writes shared state.
2. Agent reads explicit input and returns a structured decision. Never mutates shared state directly.
3. Tool interacts with the outside world and returns data. Never decides workflow or updates state.
4. State holds only committed, validated results. Not every intermediate thought or raw output.
5. Drafts, branch results, and tool responses are temporary until the orchestrator promotes them.
6. Parallel agents all read a snapshot, write separate outputs, merge only through the orchestrator.
7. Linear agents each consume validated prior artifacts and hand back a typed result for the next step.
8. Use structured input/output definitions as the real interface. Not long prose prompts.
9. Prompts guide behavior but should never be the only thing holding components together.
10. For every agent, define what it reads, what it writes, and what fields or decisions it owns.

### Context engineering principles (19 rules)

1. Give the model only the information it needs for the current step.
2. Give the information at the moment it becomes useful, not all at once.
3. Prefer structured context over raw dumps.
4. Separate instructions, data, memory, and tool results clearly.
5. Retrieve context explicitly. Do not rely on hidden memory.
6. Keep the task objective specific and local to the step.
7. Define the expected output shape before the model answers.
8. Pass validated artifacts, not vague prose, between steps.
9. Remove stale, irrelevant, or conflicting context aggressively.
10. Use tools to fetch facts. Use agents to reason over facts.
11. Keep state small, committed, and trustworthy.
12. Treat temporary outputs as working context until validated.
13. Give each agent a scoped view, not the whole system blob.
14. Make timing part of design: right info, right agent, right stage.
15. Add constraints and decision criteria, not just broad goals.
16. Prefer explicit schemas and contracts over prompt-only coordination.
17. Log what context was given so behavior can be debugged and repeated.
18. Version prompts, schemas, and retrieval logic so changes are controlled.
19. When scaling, add better context routing before adding more agent freedom.

---

## Your first action in every session

```
1. Read this file fully
2. Read your AGENT.md from team/<your-role>/AGENT.md
3. Read your assigned Linear ticket — user story, AC checkboxes, linked files
4. Check context utilization — if above 50% before starting, stop and flag PM
5. Confirm your role and context boundary before writing a single line
```

If no ticket is assigned — stop and post a comment to PM in Linear.
Never start work without a ticket.

First session only — run this once after cloning:
```bash
git config core.hooksPath .githooks
chmod +x .githooks/commit-msg
```
This activates the commit-msg hook that enforces conventional commits.

---

## Team roster — 4 agents

| Agent    | Tag  | Subagent Type | Role                                                          |
|----------|------|---------------|---------------------------------------------------------------|
| PM       | [PM] | pm            | Product vision, UX, all docs, prompts, sprint planning, specs |
| Backend  | [BE] | backend       | All Python: core, services, engines, api, requirements.txt    |
| Frontend | [FE] | frontend      | All TypeScript/React: UI components, pages, API integration   |
| QA       | [QA] | qa            | Testing, CI/CD workflows, eval rubrics, verification, sign-off |

### File ownership - strict boundaries

| Agent    | Owns                                                                                         |
|----------|----------------------------------------------------------------------------------------------|
| PM       | docs/*, prompts/*.md, SPRINT_PLAN.md, SPRINT_N_PLAN.md, config/defaults.yaml (schema only)  |
| Backend  | api/*.py, core/*.py, services/*.py, engines/*.py, requirements.txt                           |
| Frontend | frontend/**/*.ts, frontend/**/*.tsx, frontend/package.json                                   |
| QA       | tests/*, evals/*.py, .github/workflows/*                                                     |

### Skills — load only the one you need

Each agent has skills in `team/<role>/skills/` (local only, gitignored).
Load the matching skill before starting a task. Never load all at once.

#### PM agent (subagent_type: pm)

| Skill file              | When to load                                                    |
|-------------------------|-----------------------------------------------------------------|
| architecture_layers.md  | Documenting system architecture or managing abstraction layers  |
| abstraction_guide.md    | Defining abstraction boundaries or interface contracts          |
| wireframe_storyboard.md | Defining UI flows or planning visual layout                     |
| living_docs.md          | Maintaining sprint docs (SYSTEM_STATE, ARCHITECTURE, etc.)     |
| sprint_planning.md      | Creating tickets or planning sprints                            |
| write_prompt.md         | Creating or iterating prompts in prompts/*.md                  |
| flow_critique.md        | Reviewing pipeline flows or identifying broken paths            |
| write_adr.md            | A decision affects architecture or interfaces                   |
| github_polish.md        | Making repo presentable for Tenex                              |

#### Backend agent (subagent_type: backend)

| Skill file           | When to load                                              |
|----------------------|-----------------------------------------------------------|
| write_agent.md       | Creating or modifying agent/engine files                  |
| model_integration.md | Working with Gemini model calls via services/grounder/    |
| vector_store.md      | Working with services/rag/ files                          |
| api_endpoint.md      | Creating or modifying API endpoints                       |
| structured_logging.md | Implementing trace events via services/trace.py          |
| error_handling.md    | Implementing error handling in engines or services        |

#### Frontend agent (subagent_type: frontend)

| Skill file        | When to load                                                  |
|-------------------|---------------------------------------------------------------|
| page_layout.md    | Building pages in the Next.js app                             |
| api_integration.md | Connecting frontend to backend API                           |
| loading_states.md | Implementing loading indicators or error handling             |
| report_render.md  | Building components to display opportunity recommendations    |

#### QA agent (subagent_type: qa)

| Skill file          | When to load                                              |
|---------------------|-----------------------------------------------------------|
| write_test.md       | Creating or modifying test files                          |
| eval_rubric.md      | Writing eval rubrics or eval runner code                  |
| ci_workflow.md      | Creating or modifying CI workflows                        |
| regression_check.md | Verifying no existing functionality broke                 |
| dry_run_verify.md   | Verifying end-to-end pipeline works                       |

---

## Sai's role — technical director

Sai is not a developer on this project. He is the technical director.
He reviews, approves, and unblocks. He does not write code or tickets.
His job: look at what's built, test it works, guide direction.

### Sprint ceremony — Sai's involvement

```
+-------------------------------------------------------------+
|  SPRINT START - PM + QA pitch to Sai                        |
+-------------------------------------------------------------+
|  PM:         "Here's the backlog, priorities, broken flows"  |
|  QA:         "These features work, these regressed"         |
|  Sai:        Decides what makes the sprint                  |
+-------------------------------------------------------------+
                            |
                            v
+-------------------------------------------------------------+
|  SPRINT EXECUTION - Agents implement                        |
+-------------------------------------------------------------+
|  Backend, Frontend, QA execute tickets                      |
|  PM orchestrates, QA verifies each feature WORKS            |
+-------------------------------------------------------------+
                            |
                            v
+-------------------------------------------------------------+
|  SPRINT END - Sai reviews what works                        |
+-------------------------------------------------------------+
|  Sai:        Tests features using QA's test instructions    |
|  Sai:        Reads docs/SYSTEM_STATE.md (5 minutes)         |
|  PM + QA:    Reviews results, identifies gaps               |
|  Findings:   Feed into next sprint planning                 |
+-------------------------------------------------------------+
```

### Escalation tiers

Tier 1 - PM resolves autonomously, no Sai input needed:
- Context hits 70%, re-brief required
- Recoverable error, retry available
- Eval score below threshold, ticket auto-created
- Missing dependency, add to requirements.txt

Tier 2 - PM surfaces to Sai with a recommendation:
- Architecture decision affecting 2+ agents
- Non-recoverable error after 3 retries
- Eval score not improving after 3 iterations
- Sprint goal at risk

Tier 3 - PM blocks everything, waits for Sai:
- QA regression detected — scores dropped sprint over sprint
- Deploy requires explicit Sai approval comment
- Cost per run exceeds $0.50

### Sai's touchpoints

```
Sprint start  -> PM + QA pitch, Sai decides sprint scope
Mid-sprint    -> PM escalates Tier 2 only, with recommendation
Sprint end    -> Sai TESTS what was built, reads SYSTEM_STATE.md
Deploy        -> Sai posts "approved" on deploy ticket
```

---

## Hard rules — zero exceptions

### Commits — NON-NEGOTIABLE

This is the single most important rule in the project.
Every subagent MUST commit frequently. No exceptions. No batching.

```
MAX 80 LINES PER COMMIT
2-4 COMMITS PER TICKET
COMMIT AFTER EVERY LOGICAL UNIT
```

A logical unit is ONE of:
- One module/file created
- One function added or changed
- One test file written
- One config change
- One bug fix

What triggers an immediate commit:
- You just wrote a new file -> commit it
- You just got tests passing -> commit
- You just added a feature to an existing file -> commit
- You just fixed a bug -> commit

What is NEVER acceptable:
- All changes in one commit at ticket end
- 150+ lines in a single commit
- Multiple unrelated files in one commit
- "WIP" or catch-all commits
- Finishing a ticket with only 1 commit

The orchestrator checks git log after every subagent returns.
If the agent made fewer than 2 commits or any commit exceeds
80 lines — the ticket is rejected and re-assigned.

### Tickets

- One ticket = one session. Never work outside ticket scope.
- Every ticket has a `done_when` field. That is your termination criteria.
- Post a structured output comment to Linear when done.
- No ticket closes without a test certification line in the output comment.
- No ticket closes without QA sign-off comment.

### Commit format — hard gate enforced by hook + CI

Format: `<type>(<scope>): <description min 10 chars>`

Valid types:
```
feat      new feature or capability
fix       bug fix
refactor  code change with no behaviour change
test      adding or updating tests
chore     deps, config, tooling, requirements
docs      documentation only
perf      performance improvement
ci        CI/CD workflow changes
```

Examples:
```
feat(rag): add wins KB ingest pipeline with chromadb
fix(grounder): handle budget exhaustion without raising
refactor(run-manager): extract stage transition validator
test(trace): add emit and get_events coverage
chore(deps): add chromadb and google-genai to requirements
docs(sprint2): add RAG service spec
ci(gate): add pytest check to CI workflow
```

NEVER put in a git commit message:
```
- Agent tags:     [BE], [FE], [QA], [PM]
- Ticket numbers: DISC-08, OPP-12
- Phrases:        "as per ticket", "per PM instructions", "per Linear"
```

Agent tags and ticket numbers go in Linear output comments only.
They never appear in git. Tenex reads git history — it must look like a solo dev.

Size rules:
- Max 80 lines changed per commit — hard limit, no exceptions
- 2 to 4 commits per ticket
- Each commit touches exactly one ticket's scope
- One function, one test file, or one config change per commit
- Never batch multiple unrelated files into one commit

Solo-dev cadence — commit like a human, not a machine:
- Commit at meaningful progress points WITHIN a ticket, not only at the end
- A meaningful point: one module done, one test file passing, one config added
- Never batch all changes into one giant commit at ticket close
- Each commit must be independently coherent — it should make sense on its own
- Each commit must compile and pass tests on its own
- Commit messages read like a developer's thought process, not a task report
- No commit references AI, agents, tickets, or automation — ever
- Git history must tell the story of one developer building incrementally

Push after every commit. Sai needs real-time visibility.

The commit-msg hook rejects any commit that violates the format.
CI also checks every PR commit — no bypass possible.

These conventions are locked for the life of this project.
Changing them requires a Tier 3 escalation — PM blocks all work until Sai decides.

### Code

- Never call a Gemini model directly — always via `services/grounder/`
- Never call a vector store directly — always via `services/rag/`
- Never access run state directly — always via `core/run_manager.py`
- Never emit trace events via print() or logging.* — always via `services/trace.py`
- Never read config via os.environ directly — always via `core/config.py`
- Never hardcode a model name — always read from config snapshot (loaded from env + defaults.yaml)
- Never hardcode a system prompt as a Python string — all prompts in `/prompts/`
- Every engine and service returns typed output or raises a typed error — never raises unhandled exceptions
- Max 200 lines per file — split if longer
- Storage is in-memory dict in Sprints 1-6. Firestore swap happens in Sprint 7. The interface stays the same across the swap.

### Testing — every agent, every ticket

Every ticket output comment must contain:
```
Test certification:
  File: tests/[file]::[test_name]
  Result: PASSED
  Command: pytest tests/[file]::[test_name] -q --tb=short
```

PM does not close a ticket without this line. No exceptions.

Always run tests as:
```
pytest tests/ -q --tb=short
```
Never use -v. It dumps full output and burns context window.

### Definition of Done — enforced by QA

A feature is ONLY complete when ALL of these are true:
```
- Code written and runs without errors
- Unit tests pass
- Feature is VISIBLE — Sai can see it (UI renders OR endpoint returns data)
- Feature is TESTABLE — QA provides test instructions for Sai
- E2E flow works end-to-end (where applicable)
- No regressions in existing features
- Documentation updated (if user-facing)
```

The rule: if Sai cannot see it and test it, it is NOT done.

Every output comment must include:
```
## How to Test This Feature
1. [step]
2. [step]
3. [expected result]
```

### Context management

- Stop at 70% context window utilization
- Before stopping: write partial output comment with exact state, what remains, what next session needs
- Never try to finish a ticket by cramming — partial + re-brief beats context rot
- Linear ticket comments are the handoff mechanism between sessions — write them as if the next session starts completely cold
- Never read files outside the current ticket's scope — every file read burns context permanently

### Logging

- Every model call and tool call logs via `services/trace.py` — no print statements in engine code
- Log event type, run_id, and relevant payload before and after each call
- All events go to `logs/{run_id}.jsonl` — never committed
- In-memory event store supports `GET /v1/runs/{id}/trace`

### Decisions — ADR required

When any agent makes a decision affecting system architecture, another agent's interface,
or a tech stack choice:
1. Post one line to Linear ticket: `DECISION: [what] - see ADR-XXX`
2. Append `docs/decisions/ADR-XXX.md` before closing the ticket
3. Update `docs/decisions/INDEX.md` with one line entry

This is part of AC — ticket cannot close without it if a decision was made.

---

## System architecture — five engines

```
+------------------------------------------------------------------+
|                    FRONTEND (Next.js)                             |
|  Backend-driven: renders what API tells it to render              |
|  Interactive: user provides info, approves assumptions            |
|  Shows: evidence / abstraction / confidence separately            |
+-----------------------------+------------------------------------+
                              | SSE / REST
+-----------------------------v------------------------------------+
|                    API + RUN MANAGER                              |
|  FastAPI on Cloud Run                                             |
|  Run state machine, config snapshots, budget enforcement          |
|  Backend-driven UI contract (ui_hints, actions, fields)           |
+---+----------+----------+----------+----------+------------------+
    |          |          |          |          |
    v          v          v          v          v
+-------+ +--------+ +--------+ +--------+ +--------+
| RAG   | |GROUNDER| |THOUGHT | | PITCH  | | TRACE  |
|SERVICE| |        | | ENGINE | | SYNTH  | | EMIT   |
|       | |Gemini +| |        | |        | |        |
|Wins   | |Google  | |Reason  | |3-tier  | |Struct  |
|KB     | |Search  | |loop +  | |recs +  | |logs +  |
|only   | |grounding| MID +  | |ROI from| |trace   |
|       | |+ budget| |depth   | |wins    | |correl  |
|       | |control | |control | |        | |        |
+-------+ +--------+ +--------+ +--------+ +--------+
```

Key rules:
- RAG is a completely separate service. Engines call it like a tool.
- Grounder is a separate module. Engines call it like a tool.
- Thought engine orchestrates — decides what to ask, when to ask user, when to stop.
- Pitch synthesis is separate from reasoning — translates evidence into client-facing recommendations.
- Trace emitter is always on. Every action is logged with run_id correlation.

---

## Pipeline stages — multi-agent hypothesis pipeline

Orchestrator (`engines/orchestrator.py`) is pure Python control flow — not an LLM agent.
Config: `orchestration.mode: "multi_agent"` in `config/defaults.yaml`.

```
INTAKE → GROUNDING (profiler ‖ analyst) → synthesis
       → DEEP RESEARCH (pain investigator) → synthesis
       → HYPOTHESIS FORMATION → HYPOTHESIS TESTING (parallel, confidence-driven)
       → spawn handling → synthesis → REPORT → REVIEW → PUBLISHED
```

### Stage 1: Company Intake
- User provides company_name, industry, optional notes
- API: PUT /v1/runs/{id}/company-intake
- No model call. Pure input capture.
- Emits: COMPANY_INTAKE_SAVED

### Stage 2: Grounding (parallel)
- CompanyProfiler + IndustryAnalyst run in parallel via asyncio.gather
- Profiler → CompanyUnderstanding (what they do, revenue, scale, tech)
- Analyst → IndustryContext (trends, competition, regulation, AI adoption)
- Both use Gemini grounding + Google Search
- Results promoted to run state by orchestrator
- PhaseSynthesizer compresses outputs into constant-size briefing
- Emits: AGENT_SPAWNED, AGENT_COMPLETED, REASONING_LOOP_STARTED

### Stage 3: Deep Research
- PainInvestigator discovers operational pain points
- Uses grounding + RAG (Wins KB analogous cases)
- Output: list of PainPoint (description, affected_process, severity, workaround)
- PhaseSynthesizer compresses into briefing
- Emits: AGENT_SPAWNED, AGENT_COMPLETED

### Stage 4: Hypothesis Formation
- HypothesisFormer reasons over all prior evidence (context-only, no tool calls)
- Forms up to max_hypotheses (2-10, scaled by depth slider)
- Each hypothesis: statement, category, target_process, causal reasoning chain
- Categories: automation, copilot, decision_support, optimization
- Emits: HYPOTHESIS_FORMED

### Stage 5: Hypothesis Testing (parallel, confidence-driven)
- One HypothesisTester per hypothesis, all in parallel
- Stress-tests via disconfirmation search (grounding + RAG)
- Produces: TestResult (test_type, finding, impact_on_confidence, evidence_ids)
- Confidence-driven depth: low-confidence hypotheses get a second testing pass if budget allows
- Spawn handling: testers can request new hypothesis investigations
- Validation threshold = confidence_slider value; rejection threshold = confidence × 0.3
- PhaseSynthesizer compresses testing results
- Emits: HYPOTHESIS_TESTED, HYPOTHESIS_VALIDATED, HYPOTHESIS_REJECTED, SPAWN_REQUESTED

### Stage 6: Report Synthesis
- ReportSynthesizer: single-shot (MAX_STEPS=1), no ReAct loop
- Input: pre-structured hypothesis blocks with citable evidence IDs (not raw dump); rejected hypotheses as one-line summaries
- Output: AdaptiveReport (executive_summary, opportunities, evidence_annex, what_we_dont_know)
- Structure follows evidence, not a fixed template
- Prompt v2.0 with structured placeholders (`{validated_hypothesis_blocks}`, `{rejected_summaries}`, `{evidence_appendix}`)
- Section-aware feedback: "edit" mode passes previous report JSON, instructs LLM to change only the target section
- Emits: REPORT_STRUCTURE_DECIDED, REPORT_RENDERED

### Stage 7: Review
- User reviews AdaptiveReport
- Actions: approve (→ PUBLISHED), investigate (→ HYPOTHESIS_TESTING), refine (edit/deepen/reinvestigate)
- Refine feedback types: "edit" re-synthesizes report; "deepen" re-tests targeted hypotheses; "reinvestigate" backtracks to DEEP_RESEARCH
- Feedback stored in run.feedback_history
- Emits: RUN_PUBLISHED, PHASE_BACKTRACK

### User controls

| Control | Config key | Range | Effect |
|---------|-----------|-------|--------|
| Depth slider | `reasoning.depth_budget` | 1-10 (default 5) | Scales agent MAX_STEPS and max_hypotheses. Formula: `round(base * depth/5)` clamped per agent. |
| Confidence slider | `reasoning.confidence_threshold` | 0.3-1.0 (default 0.7) | Validation threshold. Rejection = confidence × 0.3. Higher = stricter, fewer validated. |

---

## Repo structure

```
/api
  __init__.py
  app.py                      # FastAPI entry point, includes routers
  /routes
    __init__.py
    runs.py                   # POST /v1/runs, GET /v1/runs/{id}, PUT company-intake, GET trace
    ui.py                     # GET /v1/runs/{id}/ui — backend-driven UI contract

/core
  __init__.py
  schemas.py                  # ALL Pydantic models (Run, Evidence, Opportunity, UIHints, etc.)
  events.py                   # EventType enum — 25 trace event types
  config.py                   # Config loader (defaults.yaml + env overrides) + freeze_config()
  run_manager.py              # Run state machine: create, get, update_intake, transition

/services
  __init__.py
  trace.py                    # Trace event emitter: emit(), get_events()
  /rag                        # Sprint 2: Wins KB retrieval service
  /grounder                   # Sprint 3: Gemini Google Search grounding

/engines
  __init__.py
  /thought                    # Sprint 4: Reasoning loop + MID
  /pitch                      # Sprint 5: 3-tier recommendations + ROI

/config
  defaults.yaml               # All system knobs: budgets, weights, models, GCP

/data
  /wins_kb_seed               # Sprint 2: Synthetic past engagements (15-20 records)

/prompts                      # Sprint 4+: Agent system prompts (PM owns)
  /versions                   # Prompt version log

/tests
  __init__.py
  test_schemas.py
  test_config.py
  test_run_manager.py
  test_api.py
  # Sprint 2+: test_rag.py, test_grounder.py, test_thought.py, test_pitch.py

/evals                        # Sprint 7: Evaluation harness
  /rubrics

/docs
  SYSTEM_STATE.md             # Sai reads this every sprint (5 minutes)
  SPRINT_LOG.md               # Sprint-over-sprint progress
  ARCHITECTURE.md             # System map + Mermaid diagram
  COMPONENT_MAP.md            # File responsibilities + layers
  CONTRACTS.md                # Interface contracts (input/output per service)
  WIREFRAMES.md               # UI layouts + storyboards
  /decisions
    INDEX.md
    ADR-001.md ...

/frontend                     # Sprint 6: Next.js App Router + TypeScript + Tailwind

/logs                         # Trace JSONL files (gitignored, never committed)

/.github/workflows             # CI/CD workflows (QA owns)
/.githooks
  commit-msg                  # Enforces commit format

requirements.txt              # PM maintains, updated each sprint close
.env.example                  # All env vars documented, no real values
.gitignore
SPRINT_PLAN.md                # Master sprint plan — living document
SPRINT_1_PLAN.md              # Sprint 1 detailed spec
SPRINT_N_PLAN.md              # Sprint N detailed specs (added as sprints planned)
CLAUDE.md                     # This file
```

---

## API endpoints

All routers registered in `api/app.py` under `/v1/` prefix. Health at root.

### Core (runs.py)

```
POST /v1/runs                                  Create a new run
GET  /v1/runs/{run_id}                         Get full run state
PUT  /v1/runs/{run_id}/company-intake          Save company intake
GET  /v1/runs/{run_id}/trace                   Get trace events for run
```

### UI contract (ui.py)

```
GET  /v1/runs/{run_id}/ui                      Backend-driven UI hints
```

### Pipeline (thought.py)

```
POST /v1/runs/{run_id}/start                   Triggers multi-agent pipeline (or legacy based on config)
POST /v1/runs/{run_id}/assumptions/confirm      Confirm assumptions
POST /v1/runs/{run_id}/answer                  User answers MID question
```

### RAG (rag.py)

```
POST /v1/runs/{run_id}/rag:query               Query the Wins KB
```

### Grounding (grounding.py)

```
POST /v1/runs/{run_id}/ground                  Run Gemini grounding call
```

### Synthesis (pitch.py)

```
POST /v1/runs/{run_id}/synthesize              Run pitch synthesis
POST /v1/runs/{run_id}/publish                 Publish report
POST /v1/runs/{run_id}/refine                  Refine assumptions/opportunities (legacy)
GET  /v1/runs/{run_id}/evidence                Get all evidence items
GET  /v1/runs/{run_id}/report                  Get the report
GET  /v1/runs/{run_id}/opportunities           Get scored opportunities
```

### Multi-agent (agents.py)

```
GET  /v1/runs/{run_id}/agents                  List all agent states for a run
GET  /v1/runs/{run_id}/hypotheses              List all hypotheses with status/confidence
GET  /v1/runs/{run_id}/hypotheses/{hid}        Get single hypothesis with full reasoning chain
GET  /v1/runs/{run_id}/interactions            List user interaction points (pending/resolved)
POST /v1/runs/{run_id}/interactions/{iid}/respond   Respond to interaction point
POST /v1/runs/{run_id}/review/approve          Approve report → PUBLISHED
POST /v1/runs/{run_id}/review/investigate      Return to HYPOTHESIS_TESTING
POST /v1/runs/{run_id}/report/refine           Refine report (edit/deepen/reinvestigate)
```

### Health

```
GET  /health                                   Returns { "status": "ok" }
```

---

## Data model — key types

All types are in `core/schemas.py`. Do not redefine them elsewhere.

### Core types

```
Run                 — top-level run record, holds all state (including multi-agent fields)
RunStatus           — CREATED | INTAKE | ASSUMPTIONS_DRAFT | ASSUMPTIONS_CONFIRMED
                      | GROUNDING | DEEP_RESEARCH | HYPOTHESIS_FORMATION
                      | HYPOTHESIS_TESTING | REASONING | SYNTHESIS | REPORT
                      | REVIEW | PUBLISHED | FAILED
BudgetConfig        — hard caps loaded from config_snapshot at run creation
BudgetState         — mutable counters (queries used), updated by services
CompanyIntake       — company_name, industry, employee_count_band, notes, constraints
Assumption          — field, value, confidence, source (grounding|user|inferred)
AssumptionsDraft    — list of Assumption + open_questions
```

### Evidence

```
EvidenceItem        — evidence_id, run_id, source_type, source_ref, title, uri, snippet,
                      relevance_score, confidence_score, retrieval_meta, provenance,
                      produced_by, dimension, process_area
                      dimension: "technology"|"scale"|"revenue"|"operations"|"industry"|"pain_point"|"hypothesis_test"
                      process_area: "dispatch"|"billing"|"maintenance"|"tracking"|""
EvidenceSource      — WINS_KB | GOOGLE_SEARCH | USER_PROVIDED
Provenance          — source_evidence_ids, extraction_timestamp, source_type, confidence
```

### Multi-agent hypothesis system

```
Hypothesis          — hypothesis_id, statement, category, target_process, status,
                      confidence, evidence_for, evidence_against, evidence_conditions,
                      analogous_engagements, conditions_for_success, risks, open_questions,
                      test_results, reasoning_chain, formed_by_agent, tested_by_agent,
                      parent_hypothesis_id
HypothesisStatus    — FORMING | TESTING | VALIDATED | REJECTED | NEEDS_USER_INPUT
TestResult          — test_type, finding, impact_on_confidence, evidence_ids
ReasoningStep       — step_type (formed_because|tested_with|contradicted_by|revised_because|validated_by),
                      description, evidence_ids, confidence_delta, timestamp
CompanyUnderstanding — company_name, what_they_do, how_they_make_money, size_and_scale,
                      technology_landscape, organizational_structure, confidence, evidence_ids
IndustryContext     — industry, key_trends, competitive_dynamics, regulatory_landscape,
                      ai_adoption_level, confidence, evidence_ids
PainPoint           — pain_id, description, affected_process, severity, current_workaround,
                      evidence_ids, confidence
AgentState          — agent_id, agent_type, status (pending|running|completed|failed|waiting_user),
                      tool_calls_made, tool_calls_budget, evidence_produced, started_at,
                      completed_at, summary
AgentResult         — agent_id, agent_type, success, evidence_items, summary, spawn_requests,
                      error, derived_insights, company_understanding, industry_context,
                      pain_points, hypotheses, adaptive_report
DerivedInsight      — insight_id, phase, statement, supporting_evidence_ids, confidence,
                      produced_by_agent
SpawnRequest        — requesting_agent, reason, suggested_hypothesis, priority
UserInteractionPoint — interaction_id, run_id, interaction_type (interesting_finding|confirmation|ambiguity),
                      message, context, agent_source, requires_response, response
AgentScope          — COMPANY_PROFILER | INDUSTRY_ANALYST | PAIN_INVESTIGATOR
                      | HYPOTHESIS_FORMER | HYPOTHESIS_TESTER | REPORT_SYNTHESIZER
```

### Report

```
AdaptiveReport      — run_id, executive_summary, key_insight, opportunities, reasoning_chain,
                      confidence_assessment, what_we_dont_know, recommended_next_steps,
                      evidence_annex, agent_activity_summary
ReportOpportunity   — title, hypothesis_id, narrative, tier, confidence, roi_estimate,
                      evidence_summary, analogous_cases, risks, conditions_for_success,
                      recommended_approach
ReportFeedback      — feedback_type (edit|deepen|reinvestigate), target_section, instruction
ReportRefineRequest — feedbacks: list[ReportFeedback]
```

### Legacy / shared

```
Opportunity         — opportunity_id, run_id, template_id, name, description, tier,
                      feasibility, roi, time_to_value, confidence, evidence_ids,
                      assumptions, rationale, adaptation_needed, risks
OpportunityTier     — EASY | MEDIUM | HARD
StageOutput         — run_id, stage_name, version, created_at, payload
TraceEvent          — event_id, run_id, timestamp, event_type, payload
FieldConfidence     — field, evidence_coverage, evidence_strength, source_diversity, confidence
SectionConfidence   — section, field_confidences, missing_fields, confidence
UIHints             — stage_title, stage_description, progress, actions, editable_fields,
                      budget_view, agent_message
UIAction            — id, label, endpoint, method, enabled, confirm
EditableField       — path, label, field_type, default, constraints
BudgetView          — rag_queries_remaining, external_search_queries_remaining, total_cost_estimate
```

---

## Trace events — EventType enum

All 46 event types are in `core/events.py`. Do not define new event types outside that file.

```
Run lifecycle:     RUN_CREATED, CONFIG_SNAPSHOT_SAVED, BUDGETS_INITIALIZED
Inputs:            COMPANY_INTAKE_SAVED, ASSUMPTIONS_DRAFT_CREATED, ASSUMPTIONS_CONFIRMED
Planning:          QUERY_PLAN_CREATED
RAG:               RAG_QUERY_EXECUTED, RAG_RESULTS_FILTERED
Grounding:         GROUNDING_CALL_REQUESTED, GROUNDING_CALL_COMPLETED,
                   GROUNDING_QUERIES_COUNTED, EXTERNAL_BUDGET_EXHAUSTED
Reasoning:         REASONING_LOOP_STARTED, REASONING_LOOP_COMPLETED,
                   MID_GAP_DETECTED, USER_QUESTION_ASKED, USER_ANSWER_RECEIVED,
                   ESCALATION_TRIGGERED, CONTRADICTION_DETECTED,
                   CONFIDENCE_STAGNATION, WORKING_MEMORY_UPDATED
Synthesis:         OPPORTUNITIES_COMPUTED, ROI_MODEL_COMPUTED,
                   CONFIDENCE_COMPUTED, REPORT_RENDERED
Terminal:          RUN_PUBLISHED, STAGE_FAILED, BUDGET_VIOLATION_BLOCKED
Refinement:        REPORT_REFINED, ASSUMPTIONS_CORRECTED, OPPORTUNITIES_REMOVED
Memory:            EVIDENCE_PROMOTED, EVIDENCE_REJECTED, EVIDENCE_CONTRADICTION
Multi-agent:       AGENT_SPAWNED, AGENT_COMPLETED, AGENT_FAILED,
                   HYPOTHESIS_FORMED, HYPOTHESIS_TESTED,
                   HYPOTHESIS_VALIDATED, HYPOTHESIS_REJECTED,
                   USER_INTERACTION_SURFACED, USER_INTERACTION_RESOLVED,
                   SPAWN_REQUESTED, PHASE_BACKTRACK, REPORT_STRUCTURE_DECIDED
```

---

## Config — all knobs in one place

All system knobs live in `config/defaults.yaml`.
Never hardcode a budget, weight, model name, or threshold in Python code.

```yaml
budgets:
  external_search_query_budget: 25   # max Google Search queries total (Gemini uses 5-10 per call)
  external_search_max_calls: 8       # max Gemini grounding calls
  rag_query_budget: 15               # max RAG retrievals
  rag_top_k: 5                       # results per RAG query
  rag_min_score: 0.3                 # minimum relevance threshold

reasoning:
  depth_budget: 5                    # max reasoning loops / depth slider (user can set 1-10)
  confidence_threshold: 0.7          # stop if overall confidence exceeds this
  min_field_coverage: 0.3            # don't stop if any field below this
  stagnation_threshold: 2            # consecutive loops with no improvement
  stagnation_delta: 0.02             # minimum improvement to not count as stagnant

scoring:
  w_roi: 0.30
  w_feasibility: 0.30
  w_ttv: 0.20
  w_confidence: 0.20

confidence:
  evidence_coverage_weight: 0.45
  evidence_strength_weight: 0.35
  source_diversity_weight: 0.20

models:
  reasoning_model: "gemini-2.5-flash"   # thought engine + ReAct steps
  synthesis_model: "gemini-2.5-pro"     # pitch synthesis
  grounding_model: "gemini-2.5-flash"   # Google Search grounding calls

orchestration:
  mode: "multi_agent"                # "legacy" | "multi_agent"

gcp:
  project_id: "plotpointe"
  location: "us-central1"
```

Config is frozen per run via `freeze_config()` in `core/config.py`.
The frozen snapshot is stored on the Run object and never mutated after creation.

---

## Model routing

```
Thought Engine (reasoning loops)
  -> services/grounder/ -> Gemini 2.5 Flash via Vertex AI
  -> REASONING_MODEL env var (default: gemini-2.5-flash)
  -> google_search=GoogleSearch() tool attached when grounding

Pitch Synthesis Engine (opportunity recommendations + report)
  -> Gemini 2.5 Pro via Vertex AI
  -> SYNTHESIS_MODEL env var (default: gemini-2.5-pro)

Grounding calls (company research)
  -> services/grounder/ -> Gemini 2.5 Flash via Vertex AI
  -> GROUNDING_MODEL env var (default: gemini-2.5-flash)
  -> google_search=GoogleSearch() tool attached

RAG retrieval
  -> services/rag/ -> ChromaDB (local dev) / pgvector (prod)
  -> No model call. Vector search only.

Eval scoring (Sprint 7)
  -> evals/judge_client.py -> Vertex AI Gemini directly
  -> EVAL_JUDGE_MODEL env var

Testing / dry-run
  -> Mock provider reads from test fixtures
  -> Zero network calls
```

Swap model via env var — no code changes required:
```
REASONING_MODEL=gemini-2.5-flash
SYNTHESIS_MODEL=gemini-2.5-pro
GROUNDING_MODEL=gemini-2.5-flash
GCP_PROJECT_ID=plotpointe
GCP_LOCATION=us-central1
```

---

## Abstraction rules

Every layer talks to an interface, never an implementation.

| What you need             | Call this                | Never call directly        |
|---------------------------|--------------------------|----------------------------|
| A Gemini model call       | services/grounder/       | google.genai.* directly    |
| RAG retrieval             | services/rag/            | chromadb.*, pgvector.*     |
| Run state                 | core/run_manager.py      | _runs dict directly        |
| Config values             | core/config.py           | os.environ directly        |
| Trace logging             | services/trace.py        | print(), logging.*         |

Every new integration gets an interface defined first.
Implementation second. Always.

---

## Run state machine

Valid transitions only. No stage skipping.

```
CREATED -> INTAKE -> ASSUMPTIONS_DRAFT -> ASSUMPTIONS_CONFIRMED
-> REASONING -> SYNTHESIS -> REPORT -> PUBLISHED

Any state -> FAILED
```

`core/run_manager.py` owns all transitions.
Direct mutation of `run.status` outside `run_manager.py` is prohibited.

---

## Budget enforcement rules

Budget enforcement is non-negotiable. Hard stops, not soft warnings.

### Google Search query budget
- Tracked at the query level, not the API call level
- One Gemini grounding call can trigger multiple Google Search queries
- Count `webSearchQueries` from grounding metadata response
- Decrement `budget_state.external_search_queries_used` per query (not per call)
- When `external_search_queries_used >= external_search_query_budget`: return error with `coverage_gap` flag
- Emit: EXTERNAL_BUDGET_EXHAUSTED, BUDGET_VIOLATION_BLOCKED

### RAG query budget
- Tracked per retrieval call to `services/rag/`
- When `rag_queries_used >= rag_query_budget`: refuse and return budget_exhausted
- Emit: BUDGET_VIOLATION_BLOCKED

### Defense-in-depth
- `external_search_max_calls` caps the number of Gemini grounding API calls regardless of query count
- Prevents runaway costs from a misconfigured budget

---

## Sprint plan reference

Full 7-sprint plan is in `SPRINT_PLAN.md`.
Sprint-specific specs are in `SPRINT_N_PLAN.md` files.
No sprint starts until previous sprint's success criteria are all checked.
After each sprint: update SPRINT_PLAN.md status and check off criteria.

| Sprint | Goal                         |
|--------|------------------------------|
| 1      | Foundation + Contracts       |
| 2      | RAG Service                  |
| 3      | Gemini Grounding             |
| 4      | Thought Engine               |
| 5      | Pitch Synthesis              |
| 6      | Interactive Frontend         |
| 7      | Eval + Observability + Demo  |

---

## Memory architecture — 4 types

| Type       | Where                          | Owner    | Survives session  |
|------------|--------------------------------|----------|-------------------|
| Working    | core/run_manager.py (_runs)    | Backend  | No - per run      |
| Episodic   | team/*/scratchpad.md           | PM       | Yes - per ticket  |
| Semantic   | services/rag/ vector store     | Backend  | Yes - permanent   |
| Procedural | Linear ticket comments + ADRs  | PM       | Yes - permanent   |

PM is the only agent that sees across all four memory types.
PM decides what gets written where after every session.

---

## Linear ticket format

```
Title: [TAG] Short imperative description
Labels: <agent-tag>, <epic>, <priority p1/p2/p3>, <sprint-n>

User story:
As <who>, I need <what> so that <why>.

done_when:
One sentence. Exact condition that makes this ticket complete.

Acceptance criteria:
- criterion 1
- criterion 2
- criterion 3

Execute with:
  Primary: <subagent_type>
  Collaborators: <subagent_type> (if cross-domain work needed)
  Reason: one line — why this agent and these collaborators

Test certification required: yes/no
Decision required: yes/no

Blocked by: OPP-n (if applicable)
```

### Execute with — hard rules

Every ticket MUST have an `Execute with` block. No exceptions.

- Primary: The subagent that writes the code. Exactly one.
- Collaborators: Other subagents needed for cross-domain work. Can be empty.
- Reason: Why this agent owns the ticket — maps to file ownership rules.

PM must specify the correct subagent_type:
```
backend    -> all Python: api/*.py, core/*.py, services/*.py, engines/*.py
frontend   -> all TypeScript: frontend/**/*.ts, frontend/**/*.tsx
qa         -> tests/*, evals/*.py, .github/workflows/*
pm         -> docs/*, prompts/*.md, SPRINT_*_PLAN.md, config/defaults.yaml
```

The orchestrator (PM) NEVER writes code directly. It spawns the primary
subagent using the Agent tool with the correct subagent_type.

---

## Version control

### Branch strategy

```
main          <- production only
              <- only merges via PR with CI gate passing
              <- never commit directly to main

<tag>/OPP-n-short-description
              <- one branch per ticket
              <- created from main
              <- merged back to main via PR
              <- deleted after merge

Tag prefixes:
  be/   -> backend tickets
  fe/   -> frontend tickets
  qa/   -> QA tickets
  pm/   -> PM/docs tickets

Examples:
  be/OPP-02-rag-service
  fe/OPP-18-opportunity-cards
  qa/OPP-09-api-tests
  pm/OPP-01-sprint-planning
```

Every agent works on `<tag>/OPP-n-*` branches.
Never commit to main directly.

### PR rules

Every PR must have:
```
Title:    <type>(<scope>): short description (reads like a developer wrote it)
Branch:   <tag>/OPP-n-description -> main
Body:
  ## What this does
  [one sentence — plain English, no agent tags]

  ## Why
  [one sentence — the motivation]

  ## Test certification
  [paste from output comment]

  ## Checklist
  - Tests green
  - Max 150 lines changed
  - No secrets or logs committed
  - CI gate passes
  - No agent tags or ticket numbers in commit messages
```

### .gitignore — never commit these

```
.env
*.key
*.pem
service_account.json
logs/
__pycache__/
*.pyc
*.pyo
.venv/
venv/
node_modules/
.next/
dist/
.DS_Store
Thumbs.db
rag/store/
.vscode/
.idea/
```

### .env.example — committed, documents all env vars

```bash
MODEL_PROVIDER=vertex
GCP_PROJECT_ID=plotpointe
GCP_LOCATION=us-central1
REASONING_MODEL=gemini-2.5-flash
SYNTHESIS_MODEL=gemini-2.5-pro
GROUNDING_MODEL=gemini-2.5-flash
EVAL_JUDGE_MODEL=gemini-2.5-pro
VECTOR_STORE=chroma
CHROMA_PERSIST_DIR=./data/chroma_store
```

### Fixture data protection

Fixture files in `tests/fixtures/` are stable references.
They are versioned but never changed mid-sprint.

```
Rule: fixture files only change at sprint boundaries
Rule: changing a fixture requires PM approval
Rule: all tests using that fixture must be re-run after change
Rule: fixture change = new ticket, not an inline edit
```

### Versioning strategy

```
Prompt versions:   X.Y in prompts/*.md headers    <- PM owns
Eval baselines:    sprint_N keys in baselines.json <- QA owns
API versions:      /v1/ URL prefix                 <- Backend owns
ADR versions:      ADR-XXX.md immutable            <- all agents
Sprint plan:       SPRINT_PLAN.md updated in place <- PM owns
```

---

## Commit examples — solo dev style

These are what commits look like in git. No agent tags, no ticket numbers.

```
feat(core): add pydantic schemas and run state machine
feat(api): add run creation and UI hints endpoints
feat(rag): add wins KB ingest pipeline with chromadb
feat(grounder): add gemini google search grounding with budget tracking
feat(thought): add reasoning loop with MID gap detection
feat(pitch): add 3-tier opportunity template matching
test(run-manager): add stage transition and budget validation tests
test(api): add run creation and ui hints endpoint tests
fix(grounder): count search queries from metadata not api calls
chore(deps): add chromadb and google-genai to requirements
docs(arch): update architecture diagram with five engines
```

---

## Sprint-end documentation loop — mandatory

After all sprint tickets close, PM runs this loop before the sprint is closed:

```
1. SYSTEM_STATE.md   -> what works, what's broken, how to test
2. SPRINT_LOG.md     -> metrics, what worked, what didn't, carryovers
3. ARCHITECTURE.md   -> system map reflects current state
4. COMPONENT_MAP.md  -> file map matches actual repo
5. CONTRACTS.md      -> contracts match actual service interfaces
6. WIREFRAMES.md     -> UI layouts match what Frontend built (Sprint 6+)
7. README.md         -> repo landing page is current and professional
8. decisions/INDEX   -> all sprint ADRs indexed
```

Sprint is NOT closed until all 8 docs are current.
SPRINT_PLAN.md must also have all sprint success criteria checked off.
Sai reads SYSTEM_STATE + SPRINT_LOG in 5 minutes — that is the test.

---

## Sprint deliverable rule

Every sprint MUST produce something Sai can see and test.
No invisible work. No "infrastructure only" sprints without visible output.

Sprint 1: `POST /v1/runs` returns a run_id. `GET /v1/runs/{id}/ui` returns UIHints.
Sprint 2: RAG query returns ranked wins from the KB.
Sprint 3: Grounder returns synthesized company profile with citations.
Sprint 4: Full reasoning loop runs, emits MID question, accepts user answer.
Sprint 5: 3-tier opportunity report generated from evidence.
Sprint 6: Browser end-to-end: enter company, answer questions, see recommendations.
Sprint 7: 25-company eval harness runs, metrics dashboard visible in Cloud Logging.

---

## Termination criteria

### Single agent call
Done when:
1. Structured output satisfies all AC checkboxes
2. Test certification line is in output comment
3. "How to Test" instructions included
4. Feature is visible and testable by Sai

If context hits 70% before done — stop, write partial output comment, stop session.

### Eval retry loop (Sprint 7)
Stop when score >= 3.8/5 OR 3 retry iterations attempted.
After 3 retries — post block comment, escalate to Sai (Tier 2).

### Sprint
Done when:
1. All cycle tickets are Done with QA sign-off
2. Every feature is visible and testable by Sai
3. Eval scores >= previous sprint baseline (Sprint 7+)
4. Sprint-end documentation loop completed
5. PM has pitched next sprint to Sai
6. SPRINT_PLAN.md success criteria checked off

A sprint is NOT done if Sai cannot test what was built.

---

## Subagent spawn protocol — MANDATORY

The orchestrator (you, Claude Code) NEVER writes code directly.
You are the PM. You spawn subagents. This is non-negotiable.

### The rule

```
NEVER write .py files directly     -> spawn backend subagent
NEVER write .ts/.tsx files directly -> spawn frontend subagent
NEVER write test files directly    -> spawn qa subagent
NEVER write prompts directly       -> spawn pm subagent

If you catch yourself editing code — STOP. Spawn the correct subagent.
The ONLY files you may edit directly: SPRINT_PLAN.md, CLAUDE.md, .gitignore
```

### Spawn syntax

```
Agent(subagent_type="backend", prompt="Your ticket: [details]. Done when: [criteria].")
Agent(subagent_type="frontend", prompt="Your ticket: [details]. Done when: [criteria].")
Agent(subagent_type="qa", prompt="Your ticket: [details]. Done when: [criteria].")
Agent(subagent_type="pm", prompt="Your ticket: [details]. Done when: [criteria].")
```

### Context passed to every spawn

Every subagent prompt MUST include:
```
1. What to build         -> exact files, functions, interfaces
2. What to read first    -> which existing files to understand before writing
3. Done when             -> termination criteria (specific, testable)
4. Commit rules          -> max 80 lines, push after each, solo-dev style
5. What NOT to do        -> boundaries (don't touch other agent's files)
6. Which skill to load   -> team/<role>/skills/<skill>.md (if applicable)
```

### Parallel vs sequential — hard rules

```
Code agents (backend, frontend) — STRICTLY one at a time.
  Never run Backend and Frontend simultaneously.
  Wait for one to finish before spawning the other.

Non-code agents (PM, QA) — parallel allowed.
  Can run alongside any agent, including code agents.
  They only read and review — no file write conflicts.
```

### Return contract

Every spawned agent returns structured output.
No side-channel communication. No partial returns without context hit.

### Commit contract

Every code agent (backend, frontend) MUST commit within the agent session.
Max 80 lines per commit. 2-4 commits per ticket. Solo-dev style.
The orchestrator verifies git log after agent returns.
If the agent made fewer than 2 commits or any commit exceeds
80 lines — the ticket is rejected and re-assigned.

### Post-spawn verification

After every subagent returns, the orchestrator MUST:
```
1. Check git log — correct number of commits? Size under 80 lines each?
2. Check test output — did QA pass? Were tests run?
3. Check file boundaries — did the agent stay in its owned files?
4. Check success criteria — does the output match done_when?
```

If any check fails, the orchestrator does NOT move on.
It either re-spawns the agent with corrections or escalates.

---

## Collaboration protocol — who does what

```
PM        -> defines what to build, writes docs/prompts/specs, orchestrates sprints
Backend   -> builds it (all Python: api, core, services, engines)
Frontend  -> renders it (all TypeScript: Next.js pages, components)
QA        -> verifies it works (tests, evals, CI, sign-off)
```

### Problem -> Owner mapping

```
RAG quality / relevance      -> Backend fixes retrieval, QA verifies results
Grounding accuracy           -> Backend fixes grounder, PM checks prompts, QA verifies
Reasoning loop quality       -> PM writes prompt, Backend integrates, QA evals
Recommendation quality       -> PM diagnoses, Backend fixes pitch engine, QA verifies
UI/UX issues                 -> PM specifies, Frontend implements, QA tests
Budget enforcement           -> Backend implements, QA verifies edge cases
Confidence scoring           -> Backend implements formula, PM validates weights, QA tests
Deploy readiness             -> Backend + QA collaborate, PM signs off
```

### Cross-agent boundary rule

If your fix touches another agent's files, you MUST raise a ticket for that agent.
No exceptions. A backend agent does not edit frontend files.
A QA agent does not edit source code. A PM agent does not write Python.

### Sprint feedback loop

```
Sprint N executes
       |
       v
PM reviews results:
  - Are recommendations correct? Quality gaps?
  - Are flows broken? UX issues?
QA verifies:
  - Does it actually work? Regressions?
       |
       v
PM + QA identify:
  - What works (Sai can test)
  - What's broken (needs fixing)
  - What's missing (next sprint)
       |
       v
PM pitches Sprint N+1 to Sai
```

---

## ROI context

- Traditional AI opportunity assessment: $50K-$200K, 3-6 weeks
- This system: evidence-backed recommendations in under 2 minutes, fully traced
- Demo headline: "A $50K consulting engagement in 2 minutes, with every claim traced to evidence"
- Tenex framing: engineers arrive at client with maturity context and top 3 prioritised
  opportunities already identified — day one is strategy, not discovery
