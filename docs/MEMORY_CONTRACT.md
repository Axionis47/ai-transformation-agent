# Memory Contract — Agent Memory Architecture

> This document defines how memory works in the multi-agent system.
> It is the handoff specification for the orchestration loop.
> If it is not in this contract, do not assume it exists.

---

## 1. Two kinds of memory

Every agent has access to two kinds of memory:

### Shared memory (per run, visible to all agents)

Persists on the Run object and in singleton stores. The orchestrator controls
what gets written here. Agents read from shared memory at the start of their
turn and write back through the promotion gate when they have validated findings.

| Store | What it holds | Interface | Persisted on Run? |
|---|---|---|---|
| `EvidenceStore` | Validated evidence items from all sources | `get_evidence_store()` | Yes (`run.evidence`) |
| `WorkingMemory` | Per-field synthesized understanding | `run.working_memory` | Yes (dict of FieldKnowledge) |
| `Hypotheses` | Shared hypothesis space | `run.hypotheses` | Yes (list of strings) |
| `OpportunityStore` | Synthesized opportunities | `get_opportunity_store()` | Yes (`run.opportunities`) |
| `ReportStore` | Composed reports | `get_report_store()` | Yes (`run.report`) |

### Private memory (per agent invocation, dies when agent finishes)

Each agent's internal scratch space. Not visible to other agents.
Raw work stays here until the agent decides to promote it.

| Component | What it holds | Lifecycle |
|---|---|---|
| `EvidenceAccumulator` | Raw evidence collected during this agent's work | Created per invocation, discarded after |
| Internal reasoning state | Which gap am I filling, what query to try next | Lives only in the agent's context |
| Draft outputs | Half-formed opportunities, tentative scores | Not shared until validated |

---

## 2. Evidence lifecycle

Evidence flows through a strict pipeline. No shortcuts.

```
Agent produces raw evidence (RAG result, Google Search result, user answer)
    │
    ▼
EvidenceAccumulator (private scratch — deduped by source_ref)
    │
    ▼ agent returns structured output to orchestrator
    │
    ▼
PromotionGate (validation pipeline)
    ├── Schema check: evidence_id and source_type present?
    ├── Relevance threshold: score >= 0.3?
    ├── Contradiction detection: conflicts with existing evidence?
    └── Dedup: same evidence_id already in store? keep higher score
    │
    ▼
EvidenceStore (canonical shared memory)
    │
    ▼
run.evidence (API compat — only promoted items, never raw)
```

### Key rules

- **Only promoted items reach shared memory.** The gate may reject items for low relevance or missing fields. `run.evidence` only contains accepted items.
- **Canonical source is EvidenceStore.** Always read from `get_evidence_store().get_all(run_id)`, never from `run.evidence` directly. The run field is for API responses only.
- **Evidence is immutable once promoted.** No agent can modify evidence in the store. They can add new evidence that supersedes it, but the original stays.

---

## 3. EvidenceItem schema

Every piece of evidence in the system uses this schema:

```python
class EvidenceItem:
    evidence_id: str            # UUID, unique per item
    run_id: str                 # which run this belongs to
    source_type: EvidenceSource # WINS_KB | GOOGLE_SEARCH | USER_PROVIDED
    source_ref: str             # origin ID (e.g., "eng-007::preconditions", URL, answer-id)
    title: str                  # human-readable label
    uri: str | None             # URL for web sources
    snippet: str                # text excerpt (max 500 chars)
    relevance_score: float      # 0.0–1.0 (cosine similarity or assigned)
    confidence_score: float | None
    retrieval_meta: dict        # source-specific metadata:
                                #   RAG: {query, rank, chunk_type, engagement_id}
                                #   Search: {search_query, domain}
                                #   User: {question_id}
    provenance: Provenance | None  # derivation trail
    produced_by: str            # which agent created this ("researcher", "architect", etc.)
```

### Provenance

```python
class Provenance:
    source_evidence_ids: list[str]  # what evidence was this derived from?
    source_type: str                # "raw" | "summarized" | "inferred"
    confidence: float
```

---

## 4. Working memory (shared synthesized state)

Working memory holds the team's **agreed understanding** — one synthesis per required field.
It is NOT raw evidence. It is what the evidence means.

### Required fields

```
company_profile     — What the company does, products, market position
industry_context    — Industry trends, challenges, competitive landscape
business_processes  — Key workflows, operational patterns, how work gets done
pain_points         — Operational challenges, inefficiencies, bottlenecks
similar_wins        — Which past engagements match, how closely
scale_indicators    — Company size, revenue, transaction volumes, team sizes
```

### FieldKnowledge structure

```python
class FieldKnowledge:
    field: str                  # one of the 6 required fields
    synthesis: str              # one-paragraph synthesized understanding
    evidence_ids: list[str]     # which evidence items support this synthesis
    confidence: float           # 0.0–1.0
    last_updated_loop: int      # which reasoning loop last updated this
```

### How agents use working memory

**Reading (any agent):**
```python
run = run_manager.get_run(run_id)
for field, fk in run.working_memory.items():
    # fk.synthesis = "Acme Logistics uses manual spreadsheet-based dispatch..."
    # fk.confidence = 0.72
    # fk.evidence_ids = ["ev-001", "ev-003", "ev-007"]
```

**Writing (via orchestrator after agent completes):**
```python
run_manager.update_working_memory(
    run_id,
    fields=working_memory.get_all_fields(),  # dict[str, FieldKnowledge]
    hypotheses=working_memory.hypotheses,     # list[str]
)
```

### Briefing format

Working memory can produce a structured briefing for any LLM prompt:

```
COMPANY PROFILE [72% confidence, 3 sources]:
  Acme Logistics operates a regional fleet of 120 trucks...

INDUSTRY CONTEXT [58% confidence, 2 sources]:
  Regional logistics companies face...

PAIN POINTS [not yet researched]

WORKING HYPOTHESES:
  - Dispatch optimization is the primary opportunity based on overtime costs
  - Fleet maintenance may be a secondary play given breakdown frequency
```

This briefing is ~1-2KB regardless of how much evidence exists — that's the compression.

---

## 5. Context routing

Agents don't see all shared memory. Each agent gets a **scoped view** filtered
by what it needs, under hard budget constraints.

### Generic recall (for any agent)

```python
from services.memory.router import ContextRouter, RecallProfile

router = ContextRouter()

# Define what this agent needs
profile = RecallProfile(
    name="solution_architect",
    max_items=20,
    min_relevance=0.3,
    source_types=["wins_kb"],      # only past engagements
    field_scope=["similar_wins"],   # only evidence about matching wins
)

# Get filtered evidence
evidence, dropped = router.recall(run_id, all_evidence, profile)
```

### Pre-built recall profiles

| Consumer | Max Items | Min Relevance | Scope | Why |
|---|---|---|---|---|
| Thought Loop | 15 | 0.3 | broad (no field filter) | Needs overall picture |
| MID Assessment | 20 | 0.0 | broad | Must see gaps (low items = gap signal) |
| Pitch Synthesis | 25 | 0.3 | broad | Needs evidence for scoring |
| Report Composer | 30 | n/a | only linked evidence | Only what supports recommendations |

### Custom profiles for new agents

Any new agent defines its own `RecallProfile`:

```python
# Gap Analyst — wants to see everything including low-confidence items
gap_profile = RecallProfile(name="gap_analyst", max_items=30, min_relevance=0.0)

# Solution Architect — only wants past engagement matches
architect_profile = RecallProfile(
    name="solution_architect",
    max_items=15,
    min_relevance=0.4,
    source_types=["wins_kb"],
)
```

---

## 6. Contradiction detection

When new evidence enters the store, the PromotionGate checks for contradictions
against existing evidence.

### Current scope

- Checks USER_PROVIDED vs non-USER_PROVIDED on scale fields
- Scale fields: employee_count, revenue, headcount, company_size, employees
- Resolution: USER_PROVIDED always wins (user is authority on their company)
- Contradictions emit `EVIDENCE_CONTRADICTION` trace events

### Multi-agent extension

When multiple agents produce evidence about the same field:
- Evidence from the same agent replaces (dedup by source_ref, keep higher score)
- Evidence from different agents about the same field → contradiction check
- `produced_by` field on EvidenceItem enables per-agent tracing

---

## 7. Pruning and forgetting

Evidence is pruned at three boundaries:

### Boundary 1: Loop-level (private)
Inside the reasoning loop, EvidenceAccumulator is capped at 20 items.
Lowest-relevance items are dropped at each loop boundary.

### Boundary 2: Promotion gate (shared)
Items below 0.3 relevance are rejected and never enter shared memory.

### Boundary 3: Context routing (per-agent view)
Each agent's RecallProfile caps what it sees. Evidence exists in the store
but may not be in a specific agent's view if it falls below that agent's
min_relevance or max_items.

### What is NOT forgotten
- Working memory synthesis is never pruned (it's already compressed)
- Hypotheses persist until explicitly removed
- Promoted evidence stays in the store for the run's lifetime

---

## 8. Multi-agent orchestration pattern

```
ORCHESTRATOR receives task
    │
    ├── 1. Read shared memory snapshot
    │      evidence = get_evidence_store().get_all(run_id)
    │      wmem = run.working_memory
    │      hypotheses = run.hypotheses
    │
    ├── 2. Decide which agent to invoke
    │      (based on gaps in wmem, phase, budget remaining)
    │
    ├── 3. Build scoped context for that agent
    │      profile = RecallProfile(name="agent_name", ...)
    │      filtered_evidence, _ = router.recall(run_id, evidence, profile)
    │      briefing = build_briefing_from(wmem)
    │
    ├── 4. Invoke agent with scoped context
    │      result = agent.run(
    │          evidence=filtered_evidence,
    │          briefing=briefing,
    │          hypotheses=hypotheses,
    │          budget=remaining_budget,
    │      )
    │
    ├── 5. Promote agent's output to shared memory
    │      run_manager.add_evidence(run_id, result.evidence, source_label="agent_name")
    │      if result.updated_fields:
    │          run_manager.update_working_memory(run_id, result.fields, result.hypotheses)
    │
    └── 6. Repeat or advance to next phase
```

### What the orchestrator controls

- **Which agent runs when** — based on gaps, phase, and budget
- **What each agent sees** — via RecallProfile (scoped view)
- **What reaches shared memory** — via PromotionGate (validation)
- **When to stop** — confidence thresholds, budget exhaustion, stagnation

### What agents control

- **Their own reasoning** — how to fill gaps, what queries to make
- **Their private scratch** — EvidenceAccumulator, internal state
- **What they return** — structured output (evidence + field updates + hypotheses)

---

## 9. Success criteria

### SC-1: Evidence isolation
- Agent A's private accumulator is not visible to Agent B
- Only promoted items appear in shared EvidenceStore
- run.evidence matches EvidenceStore (no orphaned items)

### SC-2: Working memory persistence
- After reasoning loop completes, `run.working_memory` contains FieldKnowledge for all 6 required fields
- Downstream agents can read `run.working_memory` without re-deriving from evidence
- Briefing can be built from persisted working memory

### SC-3: Context scoping
- RecallProfile with max_items=10 returns at most 10 items
- RecallProfile with min_relevance=0.5 returns no items below 0.5
- RecallProfile with source_types=["wins_kb"] returns only WINS_KB items
- Different profiles on the same evidence set return different subsets

### SC-4: Promotion gate correctness
- Items below min_relevance (0.3) are rejected
- Items without evidence_id are rejected
- Accepted count + rejected count = input count
- run.evidence only contains accepted items (not rejected ones)

### SC-5: Contradiction detection
- USER_PROVIDED evidence on scale fields supersedes other sources
- Contradictions emit trace events with field, existing_id, new_id, resolution
- No silent overwrites

### SC-6: Produced-by traceability
- Every EvidenceItem has `produced_by` set to the agent name
- Evidence from different agents can be filtered by `produced_by`
- Trace events include source_label matching the agent

### SC-7: Hypothesis sharing
- Hypotheses added by any agent appear in `run.hypotheses`
- Hypotheses persist across agent invocations within the same run
- Downstream agents can read and extend the hypothesis list

---

## 10. What memory does NOT do

- **No cross-run memory.** Each run is isolated. Past runs don't inform current runs (that's RAG's job — past engagements are in the Wins KB, not in run memory).
- **No agent-to-agent messaging.** Agents communicate only through shared memory, never directly. The orchestrator mediates.
- **No automatic synthesis.** Working memory is updated by the agent that does the reasoning, not automatically. If no agent synthesizes a field, it stays empty.
- **No rollback.** Evidence promotion is one-way. You can add new evidence that supersedes, but you can't un-promote.

---

## 11. Store interfaces (quick reference)

### EvidenceStore
```python
store = get_evidence_store()
store.add(run_id, item) → bool              # True if new
store.add_many(run_id, items) → int          # count of new
store.get_all(run_id) → list[EvidenceItem]   # sorted by relevance DESC
store.get_by_ids(run_id, ids) → list         # specific items
store.get_filtered(run_id, min_relevance, max_items, source_types) → (list, dropped)
store.count(run_id) → int
store.prune(run_id, min_relevance, max_items) → int  # count pruned
```

### RunManager (state orchestrator)
```python
run_manager.create_run(company, industry) → Run
run_manager.get_run(run_id) → Run | None
run_manager.add_evidence(run_id, items, source_label) → Run  # goes through gate
run_manager.get_evidence(run_id) → list[EvidenceItem]         # reads from canonical store
run_manager.update_working_memory(run_id, fields, hypotheses) → Run
run_manager.update_reasoning_state(run_id, state) → Run
run_manager.update_assumptions(run_id, assumptions) → Run
run_manager.store_opportunities(run_id, opportunities) → Run
run_manager.store_report(run_id, report) → Run
run_manager.transition(run_id, new_status) → Run
```

### ContextRouter
```python
router = ContextRouter()
# Generic (any agent):
router.recall(run_id, evidence, RecallProfile(...)) → (list, dropped)
# Pre-built (existing engines):
router.recall_for_thought(run_id, evidence, intake, budget, config) → ThoughtContext
router.recall_for_mid(run_id, evidence, budget, config) → MIDContext
router.recall_for_pitch(run_id, evidence, assumptions, intake, coverage) → PitchContext
router.recall_for_report(run_id, opps, evidence, intake, state, budget) → ReportContext
```

### WorkingMemory (in-engine, then persisted)
```python
wmem = WorkingMemory()
wmem.update_field(field, synthesis, evidence_ids, confidence, loop_idx)
wmem.add_hypothesis("Dispatch optimization is the primary opportunity")
wmem.build_briefing() → str           # structured text for LLM prompt
wmem.get_all_fields() → dict[str, FieldKnowledge]
wmem.classify_evidence(items) → dict[str, list[EvidenceItem]]
```
