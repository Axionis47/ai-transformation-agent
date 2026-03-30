# RAG Contract — Wins Knowledge Base

> This document defines what the RAG service provides to consumers (reasoning loop, pitch engine, report composer).
> It is the handoff specification. If it is not in this contract, do not assume it exists.

---

## 1. What is in the store

The Wins KB contains **past engagement records** from completed AI transformation projects.
Each engagement is split into **7 chunk types**, each independently retrievable via semantic search.

### Chunk types

| Chunk Type | What It Contains | When To Query It |
|---|---|---|
| `problem_pattern` | Problem statement, baseline metrics, workflow area, industry context | "Find engagements where the problem looks like X" |
| `solution_approach` | Solution shape, tech stack, timeline, what was built | "What did we build for problems like X?" |
| `preconditions` | Conditions for success, anti-patterns, minimum requirements | "Can this company actually do this?" |
| `outcomes` | Measured impact metrics, ROI drivers, before/after comparison | "What results did we get for similar work?" |
| `discovery_insight` | What the initial hypothesis was, what we actually found, the pivot | "What surprised us? What was the real problem vs the stated one?" |
| `implementation_friction` | What went wrong, delays, integration issues, adoption resistance | "What will go wrong if we do this?" |
| `generalization` | Cross-industry applicability, analogous use cases, tags | "Where else does this pattern apply beyond the original industry?" |

### Metadata on every chunk

Every chunk carries this metadata for filtering and cross-referencing:

```
engagement_id       str     e.g. "eng-007"
chunk_type          str     one of the 7 types above
title               str     engagement title (same across all chunks of one engagement)
industry            str     financial_services | healthcare | logistics | retail | manufacturing | professional_services | technology
company_size_band   str     50-100 | 100-200 | 200-500 | 500-2000 | 2000+
workflow_area       str     support | finance_ops | rev_ops | operations
solution_shape      str     automation | copilot | decision_support
```

### Document IDs

Each chunk has a unique ID: `{engagement_id}::{chunk_type}`

Example: `eng-007::preconditions`, `eng-007::discovery_insight`

This means a query for "logistics dispatch challenges" might return `eng-007::problem_pattern`,
and a follow-up query for "what are the prerequisites for eng-007" can specifically target
`eng-007::preconditions` — enabling multi-hop retrieval.

---

## 2. Chunk content specification

Each chunk is written as natural prose optimized for embedding similarity.
Chunks are self-contained — they include enough context to be useful without reading other chunks.

### problem_pattern

```
[Title]. [Industry] company, [size_band] employees.
Workflow area: [workflow_area].
Problem: [problem statement].
Baseline metrics: [key: value pairs from baseline_metrics].
```

### solution_approach

```
[Title]. Solution type: [solution_shape].
Approach: [solution_shape] for [workflow_area] in [industry].
Tech stack: [tech_stack items].
Timeline: [timeline_weeks] weeks.
```

### preconditions

```
[Title]. Prerequisites for success:
- [condition 1]
- [condition 2]
...
Anti-patterns — do NOT pursue if:
- [anti-pattern 1]
- [anti-pattern 2]
...
```

### outcomes

```
[Title]. [Industry], [size_band] employees.
Measured results:
- [metric: value] for each measured_impact entry
ROI was driven by: [roi_drivers].
```

### discovery_insight

```
[Title].
Initial hypothesis: [what we thought the problem was].
What we actually found: [the real insight].
Key lessons:
- [lesson 1]
- [lesson 2]
```

### implementation_friction

```
[Title]. [Industry], [solution_shape], [timeline_weeks] weeks planned.
What caused friction:
- [friction point 1]
- [friction point 2]
...
```

### generalization

```
[Title]. Originally delivered for [industry] ([workflow_area]).
Generalizes to: [generalized_for text].
Also applicable to: [tags as natural text].
Solution shape: [solution_shape].
```

---

## 3. Query patterns for the reasoning agent

The reasoning loop can query RAG at any point. These are the **expected query patterns** — the prompts should guide the LLM to formulate queries in these shapes.

### Single-hop queries

| Intent | Example Query | Expected Return |
|---|---|---|
| Find similar problems | "manual ticket triage high volume support team" | `problem_pattern` chunks from eng-001, eng-011 |
| Find solutions for a workflow | "automation for accounts payable invoice processing" | `solution_approach` chunks from eng-008 |
| Check feasibility | "prerequisites for scheduling optimization healthcare" | `preconditions` chunks from eng-004 |
| Get outcome evidence | "ROI results claims processing automation" | `outcomes` chunks from eng-005 |
| Understand risks | "implementation friction logistics fleet optimization" | `implementation_friction` chunks from eng-007, eng-009 |
| Find cross-industry patterns | "high volume manual review queue false positives" | `generalization` chunks from eng-002 |

### Multi-hop queries (same retriever, multiple calls)

**Hop pattern: Problem → Solution → Preconditions → Friction**

```
Hop 1: "logistics company manual dispatch spreadsheets overtime"
        → eng-007::problem_pattern (0.87 relevance)

Hop 2: "eng-007 solution approach dispatch optimization"
        → eng-007::solution_approach (decision_support, samsara, 9 weeks)

Hop 3: "prerequisites dispatch optimization fleet telematics"
        → eng-007::preconditions (needs: telematics, dispatcher buy-in, documented delivery windows)

Hop 4: "implementation friction dispatch routing logistics resistance"
        → eng-007::implementation_friction (API rate limits, data format inconsistency, dispatcher resistance)
```

**Hop pattern: Discovery → Cross-industry → Analogous outcomes**

```
Hop 1: "initial hypothesis wrong real problem was different"
        → eng-007::discovery_insight (thought it was fuel, actually overtime)
        → eng-001::discovery_insight (thought it was speed, actually rework)

Hop 2: "high volume rework loops misrouting" (generalize the pattern)
        → eng-001::generalization (any company with high-volume inbound routing)
        → eng-008::generalization (any org with high-volume vendor invoices)

Hop 3: "results triage automation financial services 200-500"
        → eng-001::outcomes (87% triage time reduction, 76% rerouting error reduction)
```

---

## 4. What consumers receive

Every RAG query returns a list of `EvidenceItem` objects. Each contains:

```python
evidence_id:        str     UUID (unique per query result)
run_id:             str     current run
source_type:        EvidenceSource.WINS_KB
source_ref:         str     "{engagement_id}::{chunk_type}" e.g. "eng-007::preconditions"
title:              str     engagement title
snippet:            str     chunk text (first 500 chars)
relevance_score:    float   cosine similarity (0.0 - 1.0)
retrieval_meta:     dict    {"query": str, "rank": int, "chunk_type": str, "engagement_id": str}
provenance:         Provenance(source_type="raw", confidence=relevance_score)
```

### Metadata-based filtering (post-retrieval)

Consumers can filter results by metadata after retrieval:
- By `chunk_type`: "give me only preconditions chunks"
- By `engagement_id`: "give me all chunks from eng-007"
- By `industry`: "only healthcare engagements"
- By `solution_shape`: "only automation solutions"

---

## 5. Success criteria

These are the measurable, testable criteria that define "RAG is working correctly."

### SC-1: Chunk completeness
- 22 engagements x 7 chunk types = **154 chunks** in the store
- Every engagement has exactly 7 chunks
- No duplicate IDs

### SC-2: Chunk isolation
- Query "prerequisites for scheduling optimization" returns `preconditions` chunks, NOT `problem_pattern` chunks as top result
- Different chunk types from the same engagement have different embeddings and rank differently for different queries

### SC-3: Cross-engagement retrieval
- Query "high volume manual review queue" returns chunks from multiple engagements (eng-001, eng-002, eng-005, eng-008) not just one
- Results span industries when the problem pattern is cross-industry

### SC-4: Multi-hop coherence
- Given eng-007::problem_pattern from hop 1, a follow-up query using terms from that chunk retrieves eng-007::preconditions or eng-007::solution_approach (same engagement, different facet)
- Cross-reference by engagement_id in metadata enables exact follow-up

### SC-5: Relevance scoring
- Top result for a well-formed query has relevance >= 0.5
- Results below 0.3 are filtered out (existing min_score threshold)
- Irrelevant chunks (wrong industry, wrong problem) score below 0.4

### SC-6: Metadata integrity
- Every chunk has all 7 metadata fields populated
- engagement_id matches the source engagement
- chunk_type matches the actual content

### SC-7: Reasoning agent contract
- The reasoning loop can formulate a query, get results, extract `engagement_id` and `chunk_type` from `source_ref`, and use those to formulate the next query
- This enables: "I found a matching problem pattern → now get preconditions for that same engagement"

---

## 6. What RAG does NOT provide

- **Company-specific data**: RAG has past engagements only. Current company research comes from the Grounder (Google Search).
- **Recommendations**: RAG returns evidence. The Pitch engine synthesizes recommendations.
- **Confidence assessments**: RAG returns relevance scores. Confidence is computed by the reasoning loop.
- **Filtered views**: RAG returns raw results. The ContextRouter filters for each engine's budget.

---

## 7. Integration with reasoning loop prompts

The reasoning loop prompt (`prompts/reasoning_react.md`) should tell the LLM:

1. **What chunk types exist** — so it can formulate targeted queries
2. **That source_ref contains `engagement_id::chunk_type`** — so it can cross-reference
3. **Multi-hop is just multiple RAG calls** — query, read result, formulate next query from what you learned
4. **Budget awareness** — each RAG call costs 1 query from the budget

Example prompt guidance:
```
When you choose RAG, your query searches a database of 22 past AI engagements.
Each engagement is stored as 7 separate chunks:
  problem_pattern, solution_approach, preconditions, outcomes,
  discovery_insight, implementation_friction, generalization.

Results include a source_ref like "eng-007::preconditions".
Use the engagement_id to query for other facets of the same engagement.
Example: if you find eng-007::problem_pattern matches, your next RAG query
could target "prerequisites conditions eng-007 dispatch optimization" to
get the preconditions for that specific engagement.
```
