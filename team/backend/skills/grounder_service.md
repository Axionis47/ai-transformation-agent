# Skill: Grounder Service

Build or modify the Gemini Google Search grounding service in `services/grounder/`.

## When to load

Load this skill when: implementing the grounder module, modifying grounding budget enforcement, parsing grounding metadata, or fixing grounding output normalization.

---

## Steps

1. Read `core/schemas.py` — specifically `EvidenceItem`, `EvidenceSource`, `BudgetConfig`, `BudgetState`.
2. Read `config/defaults.yaml` — `external_search_query_budget` and `external_search_max_calls` are the budget knobs.
3. Budget logic (this is the most important part — read carefully):
   - `external_search_max_calls`: hard cap on the number of Gemini grounding API calls made.
   - `external_search_query_budget`: hard cap on the total number of Google Search queries triggered. One Gemini call can trigger multiple Google searches. Count `webSearchQueries` from the grounding metadata, not the number of API calls.
   - Before each call: check both caps. If either is exhausted, return a `GroundingBudgetExhausted` result with a `coverage_gap` flag. Do not make the call.
   - After each call: count `webSearchQueries` in the grounding metadata. Decrement from `external_search_query_budget`. Update `budget_state`.
4. Making the grounding call:
   - Use `google.genai` with the `GoogleSearch()` tool enabled.
   - Model comes from `config_snapshot["models"]["grounding_model"]`. Never hardcode.
   - Pass the query text as the prompt. The model will use Google Search to ground its answer.
5. Parsing the response:
   - Extract `grounding_metadata.grounding_chunks`: each chunk has `uri`, `title`, `web.domain`.
   - Extract `grounding_metadata.grounding_supports`: each support has segment text and confidence scores.
   - Extract `grounding_metadata.search_entry_point`: store it, flag it for frontend display requirements.
   - Normalize each grounding chunk into an `EvidenceItem` with `source_type=EvidenceSource.GOOGLE_SEARCH`, `confidence_score` from grounding_supports where available.
6. Emit trace events: `GROUNDING_CALL_REQUESTED`, `GROUNDING_CALL_COMPLETED`, `GROUNDING_QUERIES_COUNTED` (with count), `EXTERNAL_BUDGET_EXHAUSTED` (if applicable).

---

## Input

- `core/schemas.py` (EvidenceItem, BudgetConfig, BudgetState)
- `config/defaults.yaml` (budget and model knobs)

## Output

- `services/grounder/` module with `ground(query, config_snapshot, budget_state) -> list[EvidenceItem] | GroundingBudgetExhausted`
- Trace events for every grounding call and budget check

## Constraints

- Grounder has zero knowledge of the thought engine. It is a standalone callable.
- Budget is tracked by query count, not call count. Count `webSearchQueries` after every call.
- Never let a call proceed when either budget cap is exhausted.
- `searchEntryPoint` must be preserved in the evidence item metadata. The frontend needs it for Google's display requirements.
- Return typed output. Never return raw API dicts.

## Commit cadence

- `feat(grounder): add gemini grounding call with google search tool`
- `feat(grounder): add query-level budget enforcement and coverage gap flag`
- `feat(grounder): normalize grounding chunks into evidence items`
