# Sprint 2 — RAG Service (standalone)

> RAG is a completely separate service. The thought engine calls it like a tool.
> No coupling to any other engine.

---

## Goal

Wins KB as a standalone, callable service. Ingest synthetic past engagements, retrieve with budget controls, normalize results into EvidenceItem objects, emit trace events.

---

## Files to create

```
services/rag/
  __init__.py
  schemas.py          # EngagementCase model for KB records
  store.py            # ChromaDB wrapper (abstraction layer)
  ingest.py           # Load seed JSON, chunk, embed, store
  retrieval.py        # Semantic search with budget enforcement

data/wins_kb_seed/
  engagements.json    # 15-20 synthetic mid-market engagement records

api/routes/
  rag.py              # POST /v1/runs/{id}/rag:query endpoint

tests/
  test_rag_store.py
  test_rag_ingest.py
  test_rag_retrieval.py
  test_rag_api.py
```

---

## File-by-file spec

### 1. `services/rag/schemas.py` — Wins KB record schema

```python
class EngagementCase(BaseModel):
    engagement_id: str              # e.g. "eng-001"
    title: str                      # e.g. "Customer Support Triage Automation"
    industry: str                   # e.g. "financial_services"
    company_size_band: str          # e.g. "200-500"
    problem: str                    # what the client struggled with
    workflow_area: str              # support | finance_ops | rev_ops | operations
    solution_shape: str             # copilot | automation | decision_support
    tech_stack: list[str]           # e.g. ["zendesk", "salesforce"]
    timeline_weeks: int             # how long the engagement took
    measured_impact: dict           # e.g. {"time_saved_pct": 40, "error_reduction_pct": 25}
    roi_drivers: list[str]          # e.g. ["ticket_volume", "resolution_time"]
    conditions_for_success: list[str]
    anti_patterns: list[str]        # when NOT to recommend this
    tags: list[str]                 # searchable keywords
```

### 2. `data/wins_kb_seed/engagements.json` — 15-20 synthetic records

Cover these verticals and workflow areas:
- Financial services: support triage, fraud detection, compliance review
- Healthcare: patient scheduling, claims processing, clinical documentation
- Logistics: dispatch optimization, invoice exception handling, fleet maintenance
- Retail: inventory forecasting, customer service automation, returns processing
- Manufacturing: quality inspection, predictive maintenance, supplier management
- Professional services: proposal generation, time tracking automation, resource allocation

Each record must be realistic, specific, with concrete measured_impact numbers.
These are SYNTHETIC (not real client data). They represent the kind of wins a consulting firm would have.

### 3. `services/rag/store.py` — ChromaDB wrapper

Abstraction over ChromaDB. Never import chromadb outside this file.

```python
class RAGStore:
    def __init__(self, persist_dir: str = "./data/chroma_store"):
        # Initialize ChromaDB persistent client
        # Create or get "wins_kb" collection with cosine similarity

    def add_documents(self, docs: list[dict]) -> int:
        # Add documents to collection
        # Each doc has: id, text (combined fields for embedding), metadata
        # Returns count of documents added

    def query(self, query_text: str, top_k: int = 5) -> list[dict]:
        # Semantic search
        # Returns list of {id, text, metadata, score}
        # Score is distance converted to similarity (1 - distance)

    def count(self) -> int:
        # Return number of documents in collection

    def clear(self) -> None:
        # Delete and recreate collection (for testing)
```

Use ChromaDB's default embedding function (all-MiniLM-L6-v2).
persist_dir configurable, defaults to ./data/chroma_store.

### 4. `services/rag/ingest.py` — Ingestion pipeline

```python
def load_engagements(json_path: str = None) -> list[EngagementCase]:
    # Load from data/wins_kb_seed/engagements.json by default
    # Validate each record against EngagementCase schema
    # Return list of validated records

def build_document_text(engagement: EngagementCase) -> str:
    # Combine key fields into a single searchable text:
    # "{title}. Industry: {industry}. Problem: {problem}.
    #  Solution: {solution_shape}. Impact: {measured_impact}.
    #  Conditions: {conditions_for_success}."
    # This is what gets embedded for semantic search

def ingest(store: RAGStore, engagements: list[EngagementCase]) -> int:
    # For each engagement:
    #   - Build document text
    #   - Create metadata dict (all fields except problem text)
    #   - Add to store
    # Return count ingested

def ensure_loaded(store: RAGStore) -> int:
    # If store.count() == 0, load and ingest seed data
    # Return count
    # Idempotent — safe to call multiple times
```

### 5. `services/rag/retrieval.py` — Search with budget enforcement

```python
class RAGRetriever:
    def __init__(self, store: RAGStore, config: dict):
        # config is the frozen config_snapshot from a run
        # Extract: rag_top_k, rag_min_score, rag_query_budget

    def query(
        self,
        query_text: str,
        run_id: str,
        budget_state: BudgetState,
    ) -> RAGQueryResult:
        # 1. Check budget: if budget_state.rag_queries_used >= rag_query_budget
        #    -> return RAGQueryResult(results=[], budget_exhausted=True)
        #    -> emit BUDGET_VIOLATION_BLOCKED trace event
        #
        # 2. Call store.query(query_text, top_k=rag_top_k)
        #
        # 3. Filter by rag_min_score
        #    -> emit RAG_RESULTS_FILTERED with count before/after
        #
        # 4. Convert to list[EvidenceItem]:
        #    - evidence_id: uuid4
        #    - run_id: from param
        #    - source_type: EvidenceSource.WINS_KB
        #    - source_ref: engagement_id from metadata
        #    - title: engagement title from metadata
        #    - snippet: truncated document text (max 500 chars)
        #    - relevance_score: similarity score
        #    - retrieval_meta: {"query": query_text, "rank": i}
        #
        # 5. Increment budget_state.rag_queries_used += 1
        #
        # 6. Emit RAG_QUERY_EXECUTED trace event
        #
        # 7. Return RAGQueryResult

class RAGQueryResult(BaseModel):
    results: list[EvidenceItem]
    query: str
    budget_exhausted: bool = False
    filtered_count: int = 0      # how many were below min_score
```

### 6. `api/routes/rag.py` — RAG query endpoint

```
POST /v1/runs/{run_id}/rag:query
  Body: { "query": "customer support automation mid-market" }
  Returns: RAGQueryResult

  Logic:
  1. Get run from run_manager
  2. Get or create RAGRetriever (use run's config_snapshot)
  3. Call retriever.query() with run's budget_state
  4. Update run's budget_state
  5. Return results
```

Register this router in api/app.py.

### 7. `services/rag/__init__.py`

Export: RAGStore, RAGRetriever, RAGQueryResult, ensure_loaded, EngagementCase

---

## Dependencies to add to requirements.txt

```
chromadb==0.5.23
```

ChromaDB includes its own embedding model (all-MiniLM-L6-v2), no separate embedding dependency needed.

---

## Commit plan (~8 commits)

```
1.  feat(rag): add engagement case schema for wins knowledge base
    -> services/rag/schemas.py, services/rag/__init__.py

2.  feat(rag): add synthetic seed engagements for mid-market wins
    -> data/wins_kb_seed/engagements.json

3.  feat(rag): add chromadb store wrapper with query and ingest
    -> services/rag/store.py

4.  feat(rag): add ingestion pipeline with document text builder
    -> services/rag/ingest.py

5.  feat(rag): add retrieval service with budget enforcement
    -> services/rag/retrieval.py

6.  feat(api): add rag query endpoint for wins kb search
    -> api/routes/rag.py + register in api/app.py

7.  chore(deps): add chromadb to requirements
    -> requirements.txt

8.  test(rag): add store, ingest, retrieval, and api tests
    -> tests/test_rag_*.py (QA agent handles this)
```

---

## Success criteria

- [ ] 15+ seed engagements ingested and retrievable
- [ ] Query "customer support automation mid-market" returns relevant engagements ranked by score
- [ ] Budget enforcement: after N queries, retrieval refuses and returns budget_exhausted
- [ ] Each retrieved chunk has evidence_id, source_ref, relevance_score, snippet
- [ ] RAG service is callable as a standalone function — no coupling to thought engine
- [ ] Trace events emitted for every retrieval call

---

## What this sprint does NOT touch

- No Gemini calls (Sprint 3)
- No reasoning loop (Sprint 4)
- No opportunity mapping (Sprint 5)
- No frontend (Sprint 6)
- No modifications to core/schemas.py (EvidenceItem already exists)
- No modifications to core/events.py (RAG events already defined)
