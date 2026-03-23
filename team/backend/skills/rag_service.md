# Skill: RAG Service

Build or modify the wins KB retrieval service in `services/rag/`.

## When to load

Load this skill when: implementing RAG retrieval, adding or updating seed engagements, modifying budget enforcement, or fixing retrieval quality.

---

## Steps

1. Read `core/schemas.py` — specifically `EvidenceItem`, `EvidenceSource`, `BudgetConfig`, `BudgetState`.
2. Read `config/defaults.yaml` — `rag_query_budget`, `rag_top_k`, `rag_min_score` are the budget knobs. Read them from the run's config snapshot. Never hardcode.
3. Ingestion:
   - Seed engagements live in `data/wins_kb_seed/`. Each engagement is a structured JSON following the engagement_case schema (industry, problem, solution_shape, measured_impact, roi_drivers, conditions_for_success, anti_patterns).
   - Chunk each field that will be retrieved semantically. Embed using the configured embedding model.
   - Store in ChromaDB local (`rag/store/` — gitignored).
   - Ingestion is idempotent: upsert, do not duplicate.
4. Retrieval:
   - Accept a query string and a `BudgetState` reference.
   - Check `budget_state.rag_queries_used` against `budget_config.rag_query_budget`. If budget exhausted, return a budget_exhausted result immediately. Do not query.
   - Query ChromaDB with the embedding, filter by `rag_min_score`, return top `rag_top_k` results.
   - Increment `rag_queries_used` on the BudgetState after each query.
   - Normalize each result into an `EvidenceItem` with `source_type=EvidenceSource.WINS_KB`.
5. Emit trace events: `RAG_QUERY_EXECUTED` (with query text and result count), `RAG_RESULTS_FILTERED` (with count before and after score filter).

---

## Input

- `core/schemas.py` (EvidenceItem, BudgetConfig, BudgetState)
- `config/defaults.yaml` (budget knobs)
- `data/wins_kb_seed/` (seed engagement JSON files)

## Output

- `services/rag/` module with `ingest()` and `retrieve(query, budget_config, budget_state) -> list[EvidenceItem] | BudgetExhausted`
- Trace events for every retrieval call

## Constraints

- RAG service has zero knowledge of the thought engine. It is a standalone callable.
- Budget is enforced inside the service. The caller never bypasses it.
- Never store embeddings anywhere other than `rag/store/` (gitignored).
- `rag_min_score` filtering happens inside the service, not in the caller.
- Return typed output. Never return raw ChromaDB dicts.

## Commit cadence

- `feat(rag): add wins kb ingestion with chromadb upsert`
- `feat(rag): add semantic retrieval with budget enforcement`
- `feat(rag): normalize retrieved chunks into evidence items`
