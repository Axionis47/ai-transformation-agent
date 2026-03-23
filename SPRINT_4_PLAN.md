# Sprint 4 -- Thought Engine (Reasoning Loop + MID)

> The core reasoning agent. Bounded loop, deterministic decisions, tools as services.
> No unbounded LLM freedom. Every action traced.

---

## Goal

Build the iterative reasoning engine that takes a company and its confirmed assumptions, enters a bounded reasoning loop (depth_budget=3), uses RAG and grounder as tools, detects missing information (MID), asks the user when tools cannot fill gaps, and accumulates evidence progressively. Full trace emission for every step.

---

## Dependencies

- Sprint 1: schemas, config, run manager, trace emitter -- COMPLETE
- Sprint 2: RAG retriever (callable tool) -- COMPLETE
- Sprint 3: Grounder (callable tool) -- COMPLETE
- No new pip dependencies required

---

## Architecture -- how the thought engine works

The thought engine is an **orchestrator**, not an LLM agent. It controls flow deterministically. It calls tools (grounder, RAG) and applies algorithmic gap detection (MID). No unbounded LLM reasoning.

```
POST /start (from INTAKE)
       |
       v
+------------------+
| ASSUMPTIONS DRAFT|  <- grounder call: research the company
|                  |  <- extract structured assumptions from response
|                  |  <- identify open questions
+--------+---------+
         |
    user confirms/edits
         |
POST /assumptions/confirm
         |
         v
+------------------+
| REASONING LOOP   |  <- bounded by depth_budget (default 3)
|                  |
|  for each loop:  |
|   1. Assess      |  <- calculate evidence coverage per field
|   2. MID         |  <- find biggest gap
|   3. Decide      |  <- rule-based: grounder / RAG / ask user
|   4. Execute     |  <- call chosen tool
|   5. Accumulate  |  <- add evidence, deduplicate
|   6. Score       |  <- recalculate overall confidence
|   7. Stop check  |  <- threshold met? budget hit? all covered?
|                  |
|  if ask_user:    |
|   -> pause loop  |
|   -> return pending_question
|   -> POST /answer resumes
+--------+---------+
         |
   loop exits (budget or confidence)
         |
         v
  Run stays in REASONING
  Evidence accumulated
  Coverage gaps recorded
  Ready for Sprint 5 (Pitch Synthesis)
```

---

## Files to create

```
engines/thought/
  __init__.py             # Exports: ThoughtEngine, ReasoningLoopResult
  mid.py                  # MID gap detection + coverage scoring
  evidence_acc.py         # Evidence accumulator + dedup + confidence calc
  assumptions.py          # Assumptions draft from grounding results
  reasoning_loop.py       # Main ThoughtEngine class

api/routes/
  thought.py              # POST /start, POST /assumptions/confirm, POST /answer

prompts/
  company_research.md     # Grounding prompt template for assumptions draft
  reasoning_queries.md    # Query templates for reasoning loop

tests/
  test_thought_mid.py           # MID gap detection tests
  test_thought_evidence.py      # Evidence accumulator tests
  test_thought_assumptions.py   # Assumptions draft tests
  test_thought_loop.py          # Full reasoning loop tests
  test_thought_api.py           # API endpoint tests
```

Files to modify:

```
core/schemas.py           # Add: UserQuestion, UserAnswer, ReasoningState, ReasoningLoopResult
                          # Modify: Run (add evidence, reasoning_state fields)
core/run_manager.py       # Add: add_evidence(), update_reasoning_state(), update_assumptions()
api/app.py                # Register thought engine router
```

---

## Schema additions -- core/schemas.py

Add these models after the existing AssumptionsDraft class:

```python
class UserQuestion(BaseModel):
    question_id: str
    run_id: str
    field: str                        # MID field this addresses
    question_text: str
    context: str | None = None        # why we are asking

class UserAnswer(BaseModel):
    question_id: str
    answer_text: str
```

Add these models after existing EvidenceItem:

```python
class ReasoningState(BaseModel):
    current_loop: int = 0
    evidence_ids: list[str] = []
    field_coverage: dict[str, float] = {}
    overall_confidence: float = 0.0
    pending_question: UserQuestion | None = None
    completed: bool = False
    stop_reason: str | None = None
    coverage_gaps: list[str] = []
    loops_completed: int = 0

class ReasoningLoopResult(BaseModel):
    completed: bool
    loops_run: int
    evidence_items: list[EvidenceItem]
    field_coverage: dict[str, float]
    overall_confidence: float
    pending_question: UserQuestion | None = None
    stop_reason: str | None = None
    coverage_gaps: list[str] = []
```

Modify Run model:

```python
class Run(BaseModel):
    # ... existing fields ...
    evidence: list[EvidenceItem] = []
    reasoning_state: ReasoningState | None = None
```

---

## Run manager additions -- core/run_manager.py

```python
def add_evidence(run_id: str, items: list[EvidenceItem]) -> Run:
    """Append evidence items to run. Deduplication is caller's responsibility."""
    run = _require_run(run_id)
    run.evidence.extend(items)
    return run

def update_reasoning_state(run_id: str, state: ReasoningState) -> Run:
    """Store current reasoning loop state on run."""
    run = _require_run(run_id)
    run.reasoning_state = state
    return run

def update_assumptions(run_id: str, assumptions: AssumptionsDraft) -> Run:
    """Store assumptions draft on run."""
    run = _require_run(run_id)
    run.assumptions = assumptions
    return run
```

---

## File-by-file spec

### 1. `engines/thought/mid.py` -- Missing Information Detection

Deterministic gap detection. Compares required fields against accumulated evidence.

```python
from core.schemas import BudgetState, EvidenceItem, FieldConfidence

# Required fields for a complete analysis
REQUIRED_FIELDS = [
    "company_profile",       # what the company does
    "industry_context",      # industry trends and challenges
    "business_processes",    # key workflows
    "pain_points",           # current challenges
    "similar_wins",          # past engagements in similar space
    "scale_indicators",      # company size, volumes, team sizes
]

# Keywords that indicate evidence covers a field
FIELD_KEYWORDS = {
    "company_profile": ["company", "founded", "provides", "offers", "products", "services", "headquartered"],
    "industry_context": ["industry", "market", "sector", "trend", "competitive", "regulation"],
    "business_processes": ["process", "workflow", "operations", "pipeline", "manual", "system"],
    "pain_points": ["challenge", "problem", "issue", "bottleneck", "inefficient", "costly"],
    "similar_wins": ["engagement", "implementation", "automation", "deployed", "roi", "reduction"],
    "scale_indicators": ["employees", "revenue", "customers", "volume", "tickets", "transactions"],
}

# Which tool can fill which gap
FIELD_TOOL_MAP = {
    "company_profile": "ground",
    "industry_context": "ground",
    "business_processes": "ground",
    "pain_points": "ground",
    "similar_wins": "rag",
    "scale_indicators": "ask_user",       # typically user-specific
}

class MIDGap:
    field: str
    coverage: float
    action: str        # "ground" | "rag" | "ask_user"

def assess_coverage(
    evidence: list[EvidenceItem],
    config: dict,
) -> tuple[dict[str, float], float]:
    """Calculate per-field coverage and overall confidence.

    Returns: (field_coverage dict, overall_confidence float)
    """
    # For each required field:
    #   - Search evidence snippets and titles for field keywords
    #   - Score: 0.0 (no match), 0.5 (weak match), 1.0 (strong match)
    #   - Strong = 2+ evidence items mention field keywords
    #   - Weak = 1 evidence item mentions field keywords
    #
    # Overall confidence (weighted from config):
    #   evidence_coverage = avg of field scores
    #   evidence_strength = avg relevance_score across all evidence
    #   source_diversity = len(unique source_types) / 3  (max 3 types)
    #   confidence = coverage * 0.45 + strength * 0.35 + diversity * 0.20

def detect_gap(
    evidence: list[EvidenceItem],
    budget_state: BudgetState,
    config: dict,
) -> MIDGap | None:
    """Find the biggest gap and recommend an action.

    Returns None if all fields have coverage >= 0.5.

    Decision logic:
    1. Calculate per-field coverage
    2. Find field with lowest coverage
    3. Look up preferred tool from FIELD_TOOL_MAP
    4. If preferred tool budget exhausted, fall back:
       ground -> rag -> ask_user
       rag -> ask_user
    5. Return MIDGap with field, coverage, and chosen action
    """
```

### 2. `engines/thought/evidence_acc.py` -- Evidence Accumulator

Tracks evidence across loops. Deduplicates by source_ref.

```python
from core.schemas import EvidenceItem, EvidenceSource

class EvidenceAccumulator:
    def __init__(self, initial: list[EvidenceItem] | None = None) -> None:
        self._items: dict[str, EvidenceItem] = {}  # keyed by source_ref for dedup
        if initial:
            for item in initial:
                self.add(item)

    def add(self, item: EvidenceItem) -> bool:
        """Add evidence item. Returns True if new, False if duplicate."""
        if item.source_ref in self._items:
            # Keep the one with higher relevance score
            existing = self._items[item.source_ref]
            if item.relevance_score > existing.relevance_score:
                self._items[item.source_ref] = item
            return False
        self._items[item.source_ref] = item
        return True

    def add_many(self, items: list[EvidenceItem]) -> int:
        """Add multiple items. Returns count of new items added."""
        return sum(1 for item in items if self.add(item))

    def get_all(self) -> list[EvidenceItem]:
        """Return all evidence items sorted by relevance."""
        return sorted(self._items.values(), key=lambda e: e.relevance_score, reverse=True)

    def get_ids(self) -> list[str]:
        """Return all evidence IDs."""
        return [item.evidence_id for item in self._items.values()]

    def count(self) -> int:
        return len(self._items)

    def source_types(self) -> set[str]:
        """Return unique source types present."""
        return {item.source_type.value for item in self._items.values()}
```

### 3. `engines/thought/assumptions.py` -- Assumptions Draft Generator

Extracts structured assumptions from grounding results.

```python
from core.schemas import Assumption, AssumptionsDraft, EvidenceItem

# Fields to extract from grounding text
ASSUMPTION_FIELDS = [
    ("company_description", "What the company does"),
    ("industry_segment", "Specific industry segment"),
    ("company_size", "Approximate company size"),
    ("key_products", "Main products or services"),
    ("technology_stack", "Technology landscape"),
    ("business_model", "How the company makes money"),
]

def extract_assumptions(
    grounding_text: str,
    evidence_items: list[EvidenceItem],
) -> AssumptionsDraft:
    """Parse grounding response into structured assumptions.

    Strategy:
    1. Split grounding text into sentences
    2. For each assumption field, find sentences containing relevant keywords
    3. Use matched sentence as value, grounding confidence as confidence
    4. Fields with no match become open_questions

    Returns AssumptionsDraft with assumptions and open_questions.
    """
    # For each field in ASSUMPTION_FIELDS:
    #   - Search grounding_text for field-relevant keywords
    #   - If found: Assumption(field=name, value=matched_sentence,
    #               confidence=avg evidence confidence, source="grounding")
    #   - If not found: add to open_questions
    #
    # Confidence per assumption:
    #   - If evidence_items have confidence_score, use average
    #   - Otherwise default 0.5
```

### 4. `engines/thought/reasoning_loop.py` -- Main Thought Engine

The core orchestrator. Calls tools, applies MID, manages loop.

```python
from core.schemas import (
    AssumptionsDraft, BudgetState, CompanyIntake,
    EvidenceItem, ReasoningLoopResult, ReasoningState, UserQuestion,
)
from core.events import EventType
from services.trace import emit

class ThoughtEngine:
    def __init__(
        self,
        grounder,           # Grounder instance
        rag_retriever,      # RAGRetriever instance
        config: dict,       # frozen config_snapshot
    ) -> None:
        # Extract: reasoning.depth_budget, reasoning.confidence_threshold
        # Store grounder and rag_retriever as tools

    def generate_assumptions(
        self,
        run_id: str,
        intake: CompanyIntake,
        budget_state: BudgetState,
    ) -> AssumptionsDraft:
        """Stage 2: Research company via grounder, produce assumptions draft.

        1. Build company research prompt from intake fields
        2. Call self.grounder.ground(prompt, run_id, budget_state)
        3. If budget_exhausted: return minimal assumptions with open_questions
        4. Parse grounding response via assumptions.extract_assumptions()
        5. Emit ASSUMPTIONS_DRAFT_CREATED
        6. Return AssumptionsDraft
        """

    def run_loop(
        self,
        run_id: str,
        intake: CompanyIntake,
        assumptions: AssumptionsDraft,
        budget_state: BudgetState,
        existing_evidence: list[EvidenceItem] | None = None,
        start_loop: int = 0,
    ) -> ReasoningLoopResult:
        """Stage 3: Iterative reasoning loop.

        Loop runs from start_loop to depth_budget:

        1. Emit REASONING_LOOP_STARTED
        2. Assess coverage via mid.assess_coverage()
        3. Check stop: confidence >= threshold
        4. Detect gap via mid.detect_gap()
        5. If no gap: stop (all fields covered)
        6. Emit MID_GAP_DETECTED
        7. Execute action:
           - "ground": build grounding query, call grounder
           - "rag": build RAG query, call retriever
           - "ask_user": build UserQuestion, pause loop
        8. Add new evidence to accumulator
        9. Emit REASONING_LOOP_COMPLETED
        10. Continue to next loop

        After loop exits:
        - Record stop_reason: "confidence_met" | "depth_budget_exhausted" | "all_fields_covered"
        - Record coverage_gaps: fields still below 0.5 coverage
        - Return ReasoningLoopResult
        """

    def _build_grounding_query(self, gap_field: str, intake: CompanyIntake) -> str:
        """Build grounding prompt from query templates in prompts/reasoning_queries.md."""
        # Templates per field loaded from prompts file
        # Variables filled from intake: company_name, industry

    def _build_rag_query(
        self, gap_field: str, intake: CompanyIntake, assumptions: AssumptionsDraft
    ) -> str:
        """Build RAG query from templates and company context."""
        # Combines industry, problem area, company characteristics

    def _build_user_question(self, gap_field: str, intake: CompanyIntake) -> UserQuestion:
        """Create a structured question for the user."""
        # Maps gap field to a human-readable question
        # Example: scale_indicators -> "How many employees does {company_name} have?"
```

### 5. `engines/thought/__init__.py`

Export: ThoughtEngine, ReasoningLoopResult (re-exported from schemas)

### 6. `api/routes/thought.py` -- Endpoints

```
POST /v1/runs/{run_id}/start
  When status=INTAKE:
    -> generate assumptions draft
    -> transition to ASSUMPTIONS_DRAFT
    -> return AssumptionsDraft

  When status=ASSUMPTIONS_CONFIRMED:
    -> start reasoning loop
    -> transition to REASONING
    -> return ReasoningLoopResult

  Otherwise: 409 Conflict

POST /v1/runs/{run_id}/assumptions/confirm
  Body: { "assumptions": [...], "open_questions": [...] }  (optional edits)
  When status=ASSUMPTIONS_DRAFT:
    -> store confirmed assumptions
    -> transition to ASSUMPTIONS_CONFIRMED
    -> return updated Run
  Otherwise: 409 Conflict

POST /v1/runs/{run_id}/answer
  Body: { "question_id": "...", "answer_text": "..." }
  When status=REASONING and pending_question exists:
    -> create USER_PROVIDED evidence from answer
    -> emit USER_ANSWER_RECEIVED
    -> resume reasoning loop from next iteration
    -> return ReasoningLoopResult
  Otherwise: 400 Bad Request (no pending question) or 409 Conflict
```

Logic for each endpoint:
1. Get run from run_manager (404 if not found)
2. Validate current status (409 if wrong state)
3. Create ThoughtEngine with grounder + retriever from run config
4. Call engine method
5. Store results on run via run_manager
6. Return result

### 7. `prompts/company_research.md` -- Grounding Prompt Template

```markdown
---
prompt_id: company_research
version: 1.0
used_by: engines/thought/assumptions.py
---

Research this company and provide factual information:

Company: {company_name}
Industry: {industry}
{notes_section}

Answer these questions based on publicly available information:
1. What does {company_name} do? Describe their main products and services.
2. What specific segment of the {industry} industry are they in?
3. How large is the company (employees, revenue if public)?
4. What technology or platforms do they use?
5. What are the main business challenges companies like this face?
6. What is their business model?

Be specific and factual. Cite sources where possible.
```

### 8. `prompts/reasoning_queries.md` -- Query Templates

```markdown
---
prompt_id: reasoning_queries
version: 1.0
used_by: engines/thought/reasoning_loop.py
---

## Grounding query templates

company_profile: What does {company_name} do? Describe their core products, services, and market position.
industry_context: What are the major trends, challenges, and opportunities in the {industry} industry for mid-market companies?
business_processes: What are the key business processes and operational workflows at {company_name} or similar {industry} companies?
pain_points: What operational challenges and inefficiencies do {industry} companies like {company_name} typically face?
scale_indicators: How large is {company_name}? Number of employees, revenue, customer base, or transaction volumes.

## RAG query templates

similar_wins: {industry} {pain_area} automation implementation mid-market
comparable_scale: {employee_count_band} company {industry} AI transformation

## User question templates

company_profile: Can you describe what {company_name} does in your own words?
business_processes: What are the main workflows or processes at {company_name} that take the most time?
pain_points: What are the biggest operational challenges at {company_name} right now?
scale_indicators: Roughly how many employees does {company_name} have, and what is the approximate volume of {volume_type} you handle?
```

---

## API registration -- api/app.py

Add to imports and router registration:

```python
from api.routes.thought import router as thought_router
app.include_router(thought_router, prefix="/v1")
```

---

## Prompt loading

The thought engine loads prompt templates from `/prompts/` at init. Simple file read, variable substitution via str.format(). No prompt versioning runtime needed for Sprint 4 -- version is in the file header for tracking.

```python
def load_prompt(name: str) -> str:
    path = Path(__file__).parent.parent.parent / "prompts" / f"{name}.md"
    text = path.read_text()
    # Strip YAML frontmatter (between --- markers)
    if text.startswith("---"):
        _, _, text = text.split("---", 2)
    return text.strip()
```

---

## Testing strategy

All tests use FakeGeminiClient for grounder and a mock RAG retriever. Zero real API calls.

### test_thought_mid.py (~8 tests)
- Empty evidence returns 0.0 coverage for all fields
- Evidence with company keywords scores company_profile field
- Evidence with industry keywords scores industry_context field
- MID returns gap for field with lowest coverage
- MID returns None when all fields have coverage >= 0.5
- MID suggests "ground" for company_profile gap
- MID suggests "rag" for similar_wins gap
- MID falls back to "ask_user" when grounder budget exhausted

### test_thought_evidence.py (~6 tests)
- Accumulator adds new evidence items
- Accumulator deduplicates by source_ref
- Duplicate with higher score replaces existing
- get_all returns items sorted by relevance
- source_types returns unique types
- count tracks item count correctly

### test_thought_assumptions.py (~5 tests)
- Assumptions extracted from grounding text with field coverage
- Open questions generated for fields not found in text
- Confidence derived from evidence item scores
- Empty grounding text returns all fields as open questions
- Source set to "grounding" for all extracted assumptions

### test_thought_loop.py (~8 tests)
- Loop completes depth_budget iterations
- Loop stops early when confidence threshold met
- Loop queries grounder for company-related gaps
- Loop queries RAG for similar_wins gap
- Loop pauses with pending_question for ask_user gaps
- After pause, loop resumes from correct position with answer as evidence
- Evidence count increases across loops
- Coverage gaps recorded when loop exits with low confidence

### test_thought_api.py (~8 tests)
- POST /start from INTAKE returns assumptions draft
- POST /start from wrong status returns 409
- POST /assumptions/confirm transitions to ASSUMPTIONS_CONFIRMED
- POST /start from ASSUMPTIONS_CONFIRMED returns reasoning result
- POST /answer with valid question continues reasoning
- POST /answer without pending question returns 400
- Budget state updated through full reasoning flow
- Unknown run_id returns 404

**Total: ~35 new tests. Target: 142 + 35 = ~177 tests.**

---

## Commit plan (~12 commits)

```
1.  feat(schemas): add reasoning state and user question models
    -> core/schemas.py (UserQuestion, UserAnswer, ReasoningState, ReasoningLoopResult, Run fields)

2.  feat(run-manager): add evidence and reasoning state update methods
    -> core/run_manager.py (add_evidence, update_reasoning_state, update_assumptions)

3.  feat(thought): add MID gap detection with field coverage scoring
    -> engines/thought/mid.py

4.  feat(thought): add evidence accumulator with dedup and sorting
    -> engines/thought/evidence_acc.py

5.  feat(thought): add assumptions draft generator from grounding
    -> engines/thought/assumptions.py

6.  feat(prompts): add company research and reasoning query templates
    -> prompts/company_research.md, prompts/reasoning_queries.md

7.  feat(thought): add reasoning loop with bounded depth and stop conditions
    -> engines/thought/reasoning_loop.py

8.  feat(thought): add package exports
    -> engines/thought/__init__.py

9.  feat(api): add thought engine endpoints for start, confirm, answer
    -> api/routes/thought.py + api/app.py registration

10. test(thought): add MID gap detection and evidence accumulator tests
    -> tests/test_thought_mid.py, tests/test_thought_evidence.py

11. test(thought): add assumptions draft and reasoning loop tests
    -> tests/test_thought_assumptions.py, tests/test_thought_loop.py

12. test(thought-api): add thought engine endpoint integration tests
    -> tests/test_thought_api.py
```

---

## MID algorithm detail

### Required fields

| Field | Description | Primary tool | Fallback |
|-------|-------------|-------------|----------|
| company_profile | What the company does | grounder | ask_user |
| industry_context | Industry trends/challenges | grounder | rag |
| business_processes | Key workflows | grounder | ask_user |
| pain_points | Current operational challenges | grounder | ask_user |
| similar_wins | Past engagements in similar space | rag | (none) |
| scale_indicators | Size, volumes, team counts | ask_user | grounder |

### Coverage scoring

For each field:
- Scan all evidence snippets + titles for field keywords
- Score: 0.0 (zero matches), 0.5 (1 match), 1.0 (2+ matches)

Overall confidence (from config/defaults.yaml weights):
```
evidence_coverage  = mean(field_scores)                          * 0.45
evidence_strength  = mean(evidence.relevance_score for all)      * 0.35
source_diversity   = len(unique_source_types) / 3                * 0.20
overall_confidence = coverage + strength + diversity
```

### Gap prioritization

1. Sort fields by coverage (ascending)
2. Skip fields with coverage >= 0.5
3. First uncovered field with available tool budget wins
4. If preferred tool budget exhausted, try fallback
5. If no tool available, ask user

### Budget-aware decision

```
if gap.preferred_tool == "ground" and budget.external_search_queries_used >= budget_limit:
    if gap.field in ["industry_context"]:
        action = "rag"  # industry context can come from wins KB
    else:
        action = "ask_user"

if gap.preferred_tool == "rag" and budget.rag_queries_used >= rag_limit:
    action = "ask_user"
```

---

## User question flow detail

### Pause

```
Loop detects gap: scale_indicators (user-specific)
  -> MID returns action="ask_user"
  -> Engine builds UserQuestion:
       question_id: uuid
       field: "scale_indicators"
       question_text: "Roughly how many employees does Acme Corp have?"
       context: "We need company size to match against similar past engagements"
  -> Emit USER_QUESTION_ASKED
  -> Return ReasoningLoopResult(completed=False, pending_question=question, ...)
  -> API stores reasoning_state on run via run_manager
  -> UI shows question to user
```

### Resume

```
POST /answer with { question_id, answer_text }
  -> Validate question_id matches pending question
  -> Create EvidenceItem:
       source_type: USER_PROVIDED
       source_ref: question_id
       snippet: answer_text
       relevance_score: 1.0 (user is authoritative)
       confidence_score: 1.0
  -> Emit USER_ANSWER_RECEIVED
  -> Load reasoning_state from run
  -> Resume loop: ThoughtEngine.run_loop(
       ..., existing_evidence=run.evidence,
       start_loop=reasoning_state.current_loop + 1)
  -> Store new results, return ReasoningLoopResult
```

---

## Evidence normalization across sources

All three source types produce identical EvidenceItem objects:

| Field | WINS_KB (RAG) | GOOGLE_SEARCH (Grounder) | USER_PROVIDED |
|-------|---------------|--------------------------|---------------|
| source_type | WINS_KB | GOOGLE_SEARCH | USER_PROVIDED |
| source_ref | engagement_id | chunk URI | question_id |
| title | engagement title | chunk title | question field |
| uri | None | chunk URI | None |
| snippet | document text | support text | answer text |
| relevance_score | cosine similarity | avg confidence | 1.0 |
| confidence_score | None | max confidence | 1.0 |
| retrieval_meta | {query, rank} | {query, domain} | {question_id, field} |

The pitch engine (Sprint 5) consumes all three types identically.

---

## Trace events used

All pre-defined in core/events.py. No new event types needed.

| Event | When | Payload |
|-------|------|---------|
| ASSUMPTIONS_DRAFT_CREATED | After grounding + parsing | {fields_count, open_questions_count} |
| ASSUMPTIONS_CONFIRMED | User confirms assumptions | {fields_count, edits_made} |
| REASONING_LOOP_STARTED | Start of each loop | {loop, depth_budget, evidence_count} |
| REASONING_LOOP_COMPLETED | End of each loop | {loop, action_taken, new_evidence_count} |
| MID_GAP_DETECTED | Gap found by MID | {field, coverage, action} |
| USER_QUESTION_ASKED | Loop pauses for user | {question_id, field, question_text} |
| USER_ANSWER_RECEIVED | User provides answer | {question_id, answer_length} |

Plus existing events fired by grounder (GROUNDING_CALL_REQUESTED, etc.) and RAG (RAG_QUERY_EXECUTED, etc.) when called as tools.

---

## Stop conditions

The reasoning loop exits when ANY of these is true:

| Condition | stop_reason value | What happens |
|-----------|-------------------|--------------|
| Overall confidence >= 0.7 | "confidence_met" | Clean exit, ready for synthesis |
| Loop count >= depth_budget (3) | "depth_budget_exhausted" | Exit with coverage_gaps recorded |
| All fields have coverage >= 0.5 | "all_fields_covered" | Clean exit, ready for synthesis |
| Pending user question | (not completed) | Pauses, waits for POST /answer |

---

## Success criteria

- [ ] Given "Acme Logistics, logistics industry" -- engine completes 3 reasoning loops
- [ ] Each loop queries RAG and/or grounder with different, progressively refined questions
- [ ] MID correctly identifies gaps and asks the user when tools cannot fill them
- [ ] User provides answer via POST /answer, engine incorporates it and continues
- [ ] Evidence accumulates across loops -- loop 3 has more evidence than loop 1
- [ ] Engine stops when depth budget hit, even if confidence is low (records coverage gaps)
- [ ] Full trace of every reasoning step, tool call, and decision

---

## What this sprint does NOT touch

- No RAG service changes (Sprint 2)
- No grounder service changes (Sprint 3)
- No frontend changes (Sprint 6)
- No opportunity mapping (Sprint 5)
- No modifications to core/events.py (reasoning events already defined)
- No modifications to config/defaults.yaml (reasoning knobs already defined)
- No new pip dependencies
