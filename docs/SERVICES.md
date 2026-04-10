# Services

This document explains every service in the system: what it does, how it works
internally, how other parts of the system use it, and where the code lives.

---

## Grounder (services/grounder/)

The grounder is how the system searches the internet. It wraps Google's Gemini
LLM with Google Search grounding, enforces budget limits, and converts raw API
responses into typed EvidenceItems.

### Files

| File | What it does |
|------|-------------|
| `client.py` | GeminiClient -- the only file that imports google.genai SDK |
| `grounder.py` | Grounder -- budget-enforced wrapper, evidence normalization |
| `parser.py` | Parses raw Gemini grounding metadata into typed objects |
| `fake_client.py` | FakeGeminiClient -- test double with canned responses |

### GeminiClient (client.py)

The only file that talks to the Gemini API. Two call modes:

**generate(prompt)** -- Pure reasoning. No Google Search, no tools, no budget cost.
Used for ReAct thinking steps, assumption extraction, phase synthesis, and report
generation. Returns `{"text": "..."}`.

**generate_with_grounding(prompt)** -- Attaches the GoogleSearch tool. Gemini
searches Google, then generates a response grounded in the search results. Returns
`{"text": "...", "grounding_metadata": {...}}`.

The grounding metadata contains:
- `web_search_queries`: list of queries Gemini searched for (this is what budget tracks)
- `grounding_chunks`: list of web results (uri + title)
- `grounding_supports`: text segments matched to chunks with confidence scores
- `search_entry_point`: rendered HTML for the search

**Credentials**: Uses Vertex AI with Application Default Credentials (ADC). On Cloud
Run, credentials come from the attached service account via the metadata server. No
key files needed. Locally, uses `gcloud auth application-default login`.

**Config**: Reads `models.grounding_model` (default "gemini-2.5-flash") and
`gcp.project_id` / `gcp.location` from config.

### Grounder (grounder.py)

Wraps GeminiClient with two-layer budget enforcement and evidence extraction.

**reason(prompt, run_id)** -- Calls `client.generate()`. Pure reasoning, no budget
cost. Returns the text string. Falls back to empty string if the model call fails
(e.g., no credentials). This is used by agents for their THINK step.

**ground(prompt, run_id, budget_state)** -- The budget-enforced search call:

```
1. Layer 1: Check query budget
   if budget_state.external_search_queries_used >= query_budget (25):
     return GroundingResult(budget_exhausted=True)

2. Layer 2: Check call budget (defense-in-depth)
   if budget_state.external_search_calls_used >= max_calls (8):
     return GroundingResult(budget_exhausted=True)

3. Call client.generate_with_grounding(prompt)
4. Increment budget_state.external_search_calls_used
5. Parse response with parse_grounding_response()
6. Count search queries from metadata, increment budget_state.external_search_queries_used
7. Normalize grounding chunks into EvidenceItems
8. Return GroundingResult(text, evidence_items, search_queries_used)
```

**Evidence normalization**: For each web result (grounding chunk):
- Finds matching grounding supports (text segments linked to this chunk)
- Calculates relevance_score = average of confidence scores from supports
- Calculates confidence_score = max of confidence scores
- Creates EvidenceItem with source_type=GOOGLE_SEARCH, source_ref=URI

**Trace events emitted**: GROUNDING_CALL_REQUESTED, GROUNDING_QUERIES_COUNTED,
GROUNDING_CALL_COMPLETED, EXTERNAL_BUDGET_EXHAUSTED, BUDGET_VIOLATION_BLOCKED

### Parser (parser.py)

Converts raw Gemini API response dict into typed `ParsedGroundingMetadata`:
- `text`: the LLM's generated text
- `chunks`: list of GroundingChunk (uri, title, domain)
- `supports`: list of GroundingSupport (segment_text, chunk_indices, confidence_scores)
- `search_queries`: list of what Gemini searched for
- `search_query_count`: len(search_queries) -- this is what gets counted against budget

### FakeGeminiClient (fake_client.py)

Test double that activates when real credentials are unavailable or when
`USE_FAKE_CLIENT=1` is set.

**generate()** returns phase-aware ReAct responses: cycles through 4 phases
(PROFILE -> DISCOVER -> MATCH -> FILL/STOP) with realistic field_coverage dicts.
Also handles assumption extraction and opportunity evaluation prompts with
canned JSON responses.

**generate_with_grounding()** pops from a response queue if one was provided,
otherwise returns a default response with industry-specific text (logistics,
healthcare, manufacturing, retail, etc.) and synthetic grounding metadata (2 chunks,
2 supports with confidence scores).

---

## RAG (services/rag/)

The RAG (Retrieval-Augmented Generation) service provides semantic search over
a knowledge base of past consulting engagements. It uses ChromaDB as the vector
store and splits each engagement into 7 independently retrievable chunks.

### Files

| File | What it does |
|------|-------------|
| `store.py` | RAGStore -- ChromaDB wrapper (singleton) |
| `retrieval.py` | RAGRetriever -- budget-enforced search with post-processing |
| `ingest.py` | Chunk builders and ingestion pipeline |
| `schemas.py` | EngagementCase and ChunkType definitions |

### RAGStore (store.py)

Thin wrapper around ChromaDB. The only file that imports chromadb.

**Singleton**: `get_rag_store()` returns a module-level singleton. This prevents
multiple ChromaDB clients from fighting over the same SQLite file, which causes
locking errors.

**Setup**: Uses `PersistentClient` with data stored at `./data/chroma_store`.
Collection name: "wins_kb". HNSW index with cosine distance.
Embedding function: `DefaultEmbeddingFunction()` (Sentence Transformers).

**Methods**:
- `add_documents(docs)`: Upsert by ID. Each doc has id, text, metadata.
- `query(query_text, top_k)`: Semantic search. Returns list of {id, text, metadata, score} where score = 1 - cosine_distance.
- `count()`: Number of documents in collection.
- `clear()`: Delete and recreate collection (for tests).

### RAGRetriever (retrieval.py)

Budget-enforced search with post-processing.

**query(query_text, run_id, budget_state)** flow:

```
1. Budget check
   if budget_state.rag_queries_used >= rag_query_budget (15):
     return RAGQueryResult(budget_exhausted=True)

2. Raw semantic search: fetch top_k * 3 results (oversample for filtering)

3. Score filter: keep only results with score >= min_score (0.3)

4. Dedup by engagement: keep highest-scoring chunk per engagement_id
   (prevents 3 chunks from the same past case dominating results)

5. Cap at top_k results

6. Normalize to EvidenceItems:
   source_type = WINS_KB
   source_ref = chunk_id (e.g., "eng-007::preconditions")
   relevance_score = semantic similarity score
   retrieval_meta includes: query, rank, chunk_type, engagement_id

7. Increment budget_state.rag_queries_used

8. Emit RAG_QUERY_EXECUTED trace event
```

**Trace events**: RAG_QUERY_EXECUTED, RAG_RESULTS_FILTERED, BUDGET_VIOLATION_BLOCKED

### Ingest Pipeline (ingest.py)

Converts EngagementCase records into ChromaDB documents.

**7 chunk types** -- each engagement is split into 7 independently retrievable chunks:

| Chunk type | Content | Why it's separate |
|------------|---------|-------------------|
| PROBLEM_PATTERN | Industry, company size, problem, baseline metrics | Matches companies with similar problems |
| SOLUTION_APPROACH | Solution type, tech stack, team, timeline, cost | Matches implementation patterns |
| PRECONDITIONS | Conditions for success, anti-patterns | Identifies prerequisites and deal-breakers |
| OUTCOMES | Before/after metrics, measured impact, ROI drivers | Provides evidence for ROI claims |
| DISCOVERY_INSIGHT | Key learnings from the engagement | Captures tacit knowledge |
| IMPLEMENTATION_FRICTION | What caused delays and problems | Identifies risks |
| GENERALIZATION | How it applies to other industries, buyer persona, triggers | Enables cross-industry matching |

**Why 7 chunks?** A semantic search for "manual dispatch problems" should find the
PROBLEM_PATTERN chunk from a logistics engagement, not the OUTCOMES chunk. Splitting
by aspect allows precise matching -- the search finds the right facet of the right case.

**Chunk ID format**: `{engagement_id}::{chunk_type}` (e.g., "eng-007::preconditions")

**Metadata per chunk**: engagement_id, chunk_type, title, industry, company_size_band,
workflow_area, solution_shape

**Functions**:
- `build_chunks(engagement)`: Generates 7 chunks from one EngagementCase
- `ingest(store, engagements)`: Builds chunks for all engagements, adds to ChromaDB
- `ensure_loaded(store, json_path)`: Idempotent -- loads seed data only if collection is empty

**Seed data**: 22 engagements in `data/wins_kb_seed/engagements.json`.
22 engagements x 7 chunks = 154 total documents in ChromaDB.

---

## Memory (services/memory/)

The memory layer manages evidence lifecycle: storing raw evidence, validating it
before promotion, routing filtered slices to different consumers, detecting
contradictions, and storing derived insights.

### Files

| File | What it does |
|------|-------------|
| `store.py` | EvidenceStore -- per-run evidence storage (singleton) |
| `promotion.py` | PromotionGate -- validates evidence before storing |
| `router.py` | ContextRouter -- serves filtered evidence per consumer |
| `pruning.py` | Dedup, relevance pruning, field-scope filtering |
| `contradiction.py` | Detects conflicting evidence on scale fields |
| `synthesis_store.py` | Stores derived insights and phase briefings |
| `opp_store.py` | Opportunity storage (legacy) |
| `report_store.py` | Report storage (legacy) |
| `types.py` | RecallProfile, FieldKnowledge, RecallRequest definitions |

### EvidenceStore (store.py)

Per-run evidence storage. Separate from the Run object (Run.evidence holds
the items, but EvidenceStore is the canonical store).

**Storage**: In-memory dict of dicts: `{run_id -> {evidence_id -> EvidenceItem}}`

**Singleton**: `get_evidence_store()` returns a module-level instance.

**Key behaviors**:
- `add(run_id, item)`: If item already exists with lower score, replaces it. Returns True if new.
- `get_all(run_id)`: Returns all items sorted by relevance_score descending.
- `get_filtered(run_id, min_relevance, max_items, source_types)`: Filtered view.
- `prune(run_id, min_relevance, max_items)`: Removes low-scoring items.

### PromotionGate (promotion.py)

Evidence does not go directly into the store. It flows through a validation pipeline first.

**Pipeline** (4 stages):

```
1. Schema check: evidence_id and source_type must be present
   -> reject if missing

2. Phase-aware relevance threshold:
   grounding:          0.3
   deep_research:      0.4
   hypothesis_testing: 0.5
   enrichment:         0.3
   -> reject if below threshold

3. Contradiction detection:
   Checks if new evidence conflicts with existing on scale fields
   -> emits EVIDENCE_CONTRADICTION trace event if found

4. Dedup via store.add():
   Store replaces lower-scoring duplicates automatically
```

Later pipeline phases have higher thresholds (0.5 for hypothesis_testing vs 0.3 for
grounding). This means evidence quality requirements increase as the analysis deepens.

**Returns**: PromotionResult with accepted/rejected counts and rejection reasons.
**Trace events**: EVIDENCE_PROMOTED, EVIDENCE_REJECTED per item.

### ContradictionDetector (contradiction.py)

Checks for conflicting evidence from different sources on scale-related fields
(employee_count, revenue, headcount, company_size).

**Resolution logic**:
- USER_PROVIDED vs anything else: USER_PROVIDED wins (user is the authority on their own company)
- GOOGLE_SEARCH vs WINS_KB: flagged for review (ambiguous, need human judgment)
- Same source type: no conflict possible

**Scope**: Only checks scale fields. Two pieces of evidence about "technology" from
different sources are not treated as contradictions.

### ContextRouter (router.py)

Different parts of the system need different evidence slices. The router provides
pre-configured filtering profiles.

**Generic recall**: `recall(run_id, evidence, profile: RecallProfile)` -- takes a
RecallProfile (max_items, min_relevance, source_types, field_scope) and returns
filtered evidence.

**Pre-built recall methods**:

| Method | Consumer | Max items | Min relevance | Notes |
|--------|----------|-----------|---------------|-------|
| recall_for_thought | Reasoning loop | 15 | 0.3 | Broad coverage, no field scope |
| recall_for_mid | MID assessment | 20 | 0.0 | Low threshold to see gaps |
| recall_for_pitch | Pitch synthesis | 25 | 0.3 | High quality evidence only |
| recall_for_report | Report | 30 | -- | Only linked evidence (by opportunity evidence_ids) |

Each method deduplicates by source, prunes by relevance, and emits a QUERY_PLAN_CREATED
trace event logging what was returned vs dropped.

### SynthesisStore (synthesis_store.py)

Stores two things that are not raw evidence:

1. **DerivedInsight**: Conclusions drawn from evidence (e.g., "Their dispatch is manual,
   costing ~15% efficiency"). Each has insight_id, phase, statement, supporting_evidence_ids,
   confidence, and produced_by_agent.

2. **Phase briefings**: Compressed summaries produced by PhaseSynthesizer between phases
   (e.g., "grounding" -> 3-5 sentence briefing about the company).

**Storage**: Module-level dicts: `_insights[run_id] -> list[DerivedInsight]`,
`_briefings[run_id] -> {phase -> text}`

**Singleton**: `get_synthesis_store()`

**Dedup**: Insights are deduplicated by insight_id.

### Pruning utilities (pruning.py)

Three utility functions used by the router and store:
- `prune_by_relevance(items, min_relevance, max_items)`: Filter by score, sort descending, cap at max
- `deduplicate_by_source(items)`: Keep highest-scoring item per source_ref
- `prune_for_field_scope(items, field_keywords, fields, max_per_field)`: Keep only evidence matching specific field keywords

---

## Storage (services/storage/)

Pluggable persistence backend. The run_manager never talks to a storage implementation
directly -- it talks to `StorageProtocol`.

### Files

| File | What it does |
|------|-------------|
| `protocol.py` | StorageProtocol -- interface (4 methods) |
| `memory_store.py` | MemoryStore -- in-memory dict (dev/test) |
| `firestore_store.py` | FirestoreStore -- Google Cloud Firestore (production) |

### StorageProtocol (protocol.py)

Interface that every storage backend must implement:

| Method | What it does |
|--------|-------------|
| save_run(run) | Persist full run state. Called after every mutation. |
| get_run(run_id) | Load by ID. Returns None if not found. |
| list_runs(limit, offset) | List runs ordered by created_at descending. |
| delete_run(run_id) | Delete a run. Returns True if found. |

### MemoryStore (memory_store.py)

Default backend. Simple dict: `{run_id -> Run}`.

Fast, zero setup, lost on server restart. Used for local development and tests.

### FirestoreStore (firestore_store.py)

Production backend. Persists runs to Google Cloud Firestore.

**Key behaviors**:
- Each run is a Firestore document in the "runs" collection
- Evidence is stored inline in the run document by default
- When evidence count exceeds 150 items (EVIDENCE_THRESHOLD), evidence is split into a sub-collection under the run document to stay under Firestore's 1MB document limit
- On read, if `evidence_split=True`, loads evidence from the sub-collection and reassembles
- list_runs does NOT load evidence for split runs (performance optimization)
- delete_run cleans up evidence sub-collection before deleting the run document
- Batched writes for evidence: 450 documents per batch (Firestore batch limit is 500)

**Backend selection**: Configured in `config/defaults.yaml` under `storage.backend`.
Swapped at app startup in `api/app.py`:

```python
if backend == "firestore":
    store = FirestoreStore(project_id=project_id)
    run_manager.init_storage(store)
```

---

## Trace (services/trace.py)

Structured event logging for debugging and observability. Every significant action
in the system emits a trace event.

### How it works

**emit(run_id, event_type, payload)** does three things:
1. Creates a TraceEvent with UUID, timestamp, event type, and payload
2. Appends it to `logs/{run_id}.jsonl` (one line per event, append-only)
3. Stores it in an in-memory dict for fast access

**get_events(run_id)** returns the in-memory list. If not in memory (e.g., after
server restart), lazy-loads from the JSONL file on disk.

### Event types (46 total, defined in core/events.py)

| Category | Events |
|----------|--------|
| Run lifecycle | RUN_CREATED, CONFIG_SNAPSHOT_SAVED, BUDGETS_INITIALIZED |
| Input | COMPANY_INTAKE_SAVED, ASSUMPTIONS_DRAFT_CREATED, ASSUMPTIONS_CONFIRMED |
| Planning | QUERY_PLAN_CREATED |
| RAG | RAG_QUERY_EXECUTED, RAG_RESULTS_FILTERED |
| Grounding | GROUNDING_CALL_REQUESTED, GROUNDING_CALL_COMPLETED, GROUNDING_QUERIES_COUNTED, EXTERNAL_BUDGET_EXHAUSTED |
| Reasoning | REASONING_LOOP_STARTED, REASONING_LOOP_COMPLETED, MID_GAP_DETECTED, USER_QUESTION_ASKED, USER_ANSWER_RECEIVED, ESCALATION_TRIGGERED, CONTRADICTION_DETECTED, CONFIDENCE_STAGNATION, WORKING_MEMORY_UPDATED |
| Synthesis | OPPORTUNITIES_COMPUTED, ROI_MODEL_COMPUTED, CONFIDENCE_COMPUTED, REPORT_RENDERED |
| Terminal | RUN_PUBLISHED, STAGE_FAILED, BUDGET_VIOLATION_BLOCKED |
| Refinement | REPORT_REFINED, ASSUMPTIONS_CORRECTED, OPPORTUNITIES_REMOVED |
| Memory | EVIDENCE_PROMOTED, EVIDENCE_REJECTED, EVIDENCE_CONTRADICTION |
| Multi-agent | AGENT_SPAWNED, AGENT_COMPLETED, AGENT_FAILED, HYPOTHESIS_FORMED, HYPOTHESIS_TESTED, HYPOTHESIS_VALIDATED, HYPOTHESIS_REJECTED, USER_INTERACTION_SURFACED, USER_INTERACTION_RESOLVED, SPAWN_REQUESTED, PHASE_BACKTRACK, REPORT_STRUCTURE_DECIDED |

### How the frontend uses it

The frontend polls `GET /v1/runs/{run_id}/trace` to show live progress during
pipeline execution. Since the pipeline runs in a background thread, the trace
endpoint is the primary mechanism for the frontend to know what's happening.

### Log files

Stored at `logs/{run_id}.jsonl`. One file per run. JSONL format (one JSON line per event).
The `logs/` directory is gitignored -- trace files are never committed.
