# Sprint 8 Plan: Three-Tier Matching Architecture

Version: 2.0
Date: 2026-03-19
Owner: PM
Supersedes: v1.0 (single matching layer, Tenex wins only)

---

## Sprint Goal

Build a three-tier matching system that separates what Tenex has delivered
(Tier 1: confident proof), what Tenex can adapt (Tier 2: adjacent builds),
and what the industry is doing (Tier 3: market intelligence) -- with clear
data separation, independent ingestion pipelines, and distinct UI presentation
for each tier. Every recommendation Sai shows a client must be traceable to
one of these three evidence sources.

---

## What Sai Can See and Test at Sprint End

| Deliverable | How to verify |
|-------------|---------------|
| Delivered solutions ingested from their own CLI | `python rag/ingest_solution.py --file tests/fixtures/sample_solution.json --dry-run` -- validates and logs without writing |
| Industry cases ingested separately | `python rag/ingest_industry_case.py --file tests/fixtures/sample_industry_case.json --dry-run` -- validates and logs |
| Matching layer produces three clearly typed tiers | `python orchestrator/pipeline.py --dry-run` -- logs show DELIVERED / ADAPTATION / AMBITIOUS records with separate confidence bands |
| UI shows three separate tier sections | Navigate to the analysis result -- three panels with different styling: green (Delivered), amber (Adaptation), blue (Ambitious) |
| Each tier synthesized by its own prompt | Three prompt files exist: `prompts/tier1_delivered.md`, `prompts/tier2_adaptation.md`, `prompts/tier3_ambitious.md` |
| Eval covers match quality per tier | `python evals/ci_eval.py` -- reports match_quality scores per tier |
| All existing tests pass | `pytest tests/ -q --tb=short` -- 124+ passing, 0 regressions |

---

## Architecture: Two Libraries, Three Output Tracks

```
COMPANY ANALYSIS PIPELINE                   SOLUTIONS LIBRARIES
(reads the target company)                  (Tenex knowledge base)

  URL                                         +--- LIBRARY A ---+
   |                                          | Delivered        |
   v                                          | Solutions        |
  Stage 1: Scraper                            | (Tenex wins)     |
   |                                          |                  |
   v                                          | ingest_solution  |
  Stage 2: Signal Extractor                   | .py --file       |
   |                                          |                  |
   v                                          | ChromaDB         |
  Stage 3: Maturity Scorer                    | collection:      |
   |                                          | "tenex_delivered"|
   v                                          +------------------+
  Stage 4: RAG Query --------retrieval------> both collections
   |                    (separate queries)
   |                                          +--- LIBRARY B ---+
   v                                          | Industry Cases   |
                                              | (external intel) |
  ============== MATCHING LAYER ============  |                  |
                                              | ingest_industry  |
  orchestrator/matching_layer.py             | _case.py --file  |
                                              |                  |
  Inputs:                                     | ChromaDB         |
    A: SignalSet (industry, scale, maturity)  | collection:      |
    B: list[SolutionRecord]  <-- Library A   | "industry_cases" |
    C: list[IndustryCaseStudy] <-- Library B +------------------+
                                              
  Three output tracks (independent):
  
  TRACK 1 -- DELIVERED                    confidence >= 0.80
    Source: Library A, direct match logic
    Output: list[MatchResult] tier="DELIVERED"
    Synthesis: tier1_delivered.md prompt
    Evidence: exact win_id, proven metrics, client profile
  
  TRACK 2 -- ADAPTATION                   confidence 0.55-0.79
    Source: Library A, adjacent match logic
    Output: list[MatchResult] tier="ADAPTATION"
    Synthesis: tier2_adaptation.md prompt
    Evidence: base solution + gap analysis + adaptation cost estimate
  
  TRACK 3 -- AMBITIOUS                    confidence 0.40-0.65
    Source: Library B, industry signal match
    Output: list[MatchResult] tier="AMBITIOUS"
    Synthesis: tier3_ambitious.md prompt
    Evidence: external case study, industry references, experimental ROI
  
  ==========================================

   |           |           |
   v           v           v
  DELIVERED  ADAPTATION  AMBITIOUS
  use cases  use cases   use cases

   |
   v
  Stage 6: Use Case Generator (per-tier synthesis)
   |
   v
  Stage 7: Report Writer
   |
   v
  API Response --> UI (three separate panels)
```

### Separation contracts

The analysis pipeline produces: `SignalSet + MaturityResult`
Library A (Delivered Solutions) produces: `list[SolutionRecord]`
Library B (Industry Cases) produces: `list[IndustryCaseStudy]`
The matching layer receives all three and produces: `list[MatchResult]` per tier

No analysis agent reads either library directly.
No library ingestion touches the analysis pipeline.
The matching layer is the only bridge.
Tier 1 and Tier 2 both draw from Library A -- different match logic, same data.
Tier 3 draws exclusively from Library B -- never from Library A.
The use case generator receives pre-tiered results -- it does not tier-classify.

---

## Data Models

### SolutionRecord (Library A -- Tenex delivered solutions)

Fields that already exist in victories.json and must be kept:

```
id                      string       "win-001" -- unique, stable, referenced in reports
engagement_title        string       "Route Optimization for Regional LTL Carrier"
industry                string       "logistics" -- lowercase, normalized
sector_tags             list[str]    ["ltl_freight", "route_planning"]
company_profile
  size_employees        int          520
  size_label            string       "mid-market" | "startup" | "enterprise"
  annual_revenue_usd    string       "$70M-$90M"
  geography             string       "US Midwest"
  business_model        string       one paragraph describing client
problem_statement       string       what the client was struggling with
solution_summary        string       what Tenex built and how
results
  primary_metric
    label               string       "Fuel Cost Reduction"
    value               string       "14%"
    baseline            string       starting state
    outcome             string       ending state with numbers
  secondary_metrics     list[dict]   label + value pairs
  measurement_period    string       "4 months post-deployment"
  measurement_basis     string       how the measurement was made
engagement_details
  duration_months       int          4
  tenex_team_size       int          2
  tenex_roles           list[str]    ["ML Engineer", "Engagement Lead"]
  client_team_involvement string     who the client had involved
  delivery_model        string       "project" | "embedded" | "advisory"
tech_stack
  data_sources          list[str]    data feeds used
  ml_approach           string       model type and approach
  infrastructure        list[str]    cloud services
  client_systems_integrated list[str] what client systems were touched
maturity_at_engagement  string       "Developing" | "Emerging" | "Advanced" etc.
follow_on_engagement    bool         true if there was a follow-on
lessons_learned         string       what surprised the team
embed_text              string       the text ChromaDB embeds -- paragraph form
industry_benchmark      string       cited benchmark from the win (for ROI grounding)
success_threshold       string       prerequisites for this solution to work
gap_analysis_template   string       "Maturity gap of {gap} points from baseline..."
```

New required fields (added in Sprint 8):

```
status                  enum         "draft" | "active" | "deprecated"
ingestion_date          string       ISO date "2026-03-19"
solution_category       enum         "predictive_model" | "classification" | "nlp" |
                                     "computer_vision" | "optimization" | "scoring_model"
applicable_signals      list[str]    Signal.type values that make this solution relevant
                                     e.g. ["ops_signal", "process_signal", "data_signal"]
```

### IndustryCaseStudy (Library B -- external market intelligence)

New record type. Not Tenex wins. External companies, published case studies,
industry reports, competitor implementations.

```
id                      string       "ind-001" -- separate ID space from win-NNN
case_title              string       "Amazon Go Cashierless Checkout" or "Starbucks ML Demand Forecasting"
industry                string       "retail" -- same normalization as SolutionRecord
sector_tags             list[str]    ["grocery", "checkout", "computer_vision"]
company_profile
  company_name          string       "Amazon" -- external company name
  company_type          string       "enterprise" | "mid-market" | "startup"
  geography             string       "Global"
  size_hint             string       "large enterprise" -- not exact, estimated from public info
ai_application
  problem_addressed     string       what business problem this solved
  solution_description  string       what was built or deployed
  technology_used       list[str]    ["computer_vision", "edge_computing", "ML"]
  deployment_scale      string       "2,000+ stores globally"
  implementation_year   int          2018 -- when it was deployed
reported_outcomes
  headline_metric       string       "Eliminated checkout wait times"
  supporting_metrics    list[str]    other reported numbers
  source                string       "Amazon press release 2021" | "McKinsey report" | "TechCrunch"
  confidence_in_data    enum         "high" | "medium" | "low" -- how reliable is the source
maturity_signal         string       "Advanced" -- what maturity was needed for this
use_case_category       string       same enum as solution_category on SolutionRecord
applicable_signals      list[str]    Signal.type values that indicate relevance
embed_text              string       paragraph for ChromaDB embedding
status                  enum         "draft" | "active" | "deprecated"
ingestion_date          string       ISO date
```

### MatchResult (matching layer output -- replaces VictoryMatch)

Three match_tier values map to the three tracks. One schema, three tiers.

```
result_id               string       "mr-001" -- ephemeral, per run
source_library          enum         "tenex_delivered" | "industry_cases"
match_tier              enum         "DELIVERED" | "ADAPTATION" | "AMBITIOUS"
confidence              float        tier band enforced:
                                     DELIVERED:   >= 0.80
                                     ADAPTATION:  0.55-0.79
                                     AMBITIOUS:   0.40-0.65
similarity_score        float        0.0-1.0 from scoring dimensions
source_id               string       win-NNN (Library A) or ind-NNN (Library B)
source_title            string       engagement_title or case_title
source_industry         string       industry of the matched record
relevance_note          string       why this record was selected
```

For DELIVERED tier (Track 1):

```
proven_metrics
  primary_label         string       "Fuel Cost Reduction"
  primary_value         string       "14%"
  measurement_period    string       "4 months post-deployment"
client_profile_summary  string       "Mid-market LTL carrier, 520 employees, US Midwest"
engagement_duration     int          months
tech_approach           string       ml_approach from the win record
gap_analysis            string | null  from gap_analysis_template with substitution
```

For ADAPTATION tier (Track 2):

```
base_solution_id        string       win-NNN -- the solution being adapted
adaptation_notes        string       what stays the same, what changes
gap_from_base           float        maturity distance from the base engagement
estimated_scope_delta   string       "30% more effort -- different industry domain"
adjusted_roi_range      string       adapted ROI estimate with discount factor stated
```

For AMBITIOUS tier (Track 3):

```
industry_examples       list[str]    company names or case study references
source_citations        list[str]    where the data comes from
deployment_scale        string       how widely adopted this is in the sector
implementation_maturity string       "early adopter" | "mainstream" | "emerging"
experimental_roi_range  string       "15-35% efficiency gain -- industry estimate range"
```

---

## Sprint 8 Tickets

### Dependency order

```
DISC-66 (BE) -- SolutionRecord schema + IndustryCaseStudy schema + MatchResult schema   [p1, no deps]
DISC-67 (BE) -- Delivered solutions ingestion CLI (Library A)                            [p1, needs DISC-66]
DISC-74 (BE) -- Industry cases ingestion CLI (Library B)                                 [p1, needs DISC-66]
DISC-68 (BE) -- Matching layer: 3-channel logic with two ChromaDB collections           [p1, needs DISC-66]
DISC-70 (BE) -- Fix tier_classification eval score                                       [p1, no deps]
DISC-75 (PM) -- Three synthesis prompts (one per tier)                                   [p1, no deps]
DISC-76 (BE) -- Use case generator: per-tier synthesis using tier prompts                [p2, needs DISC-68 + DISC-75]
DISC-77 (FE) -- UI: three-tier recommendation display with visual separation             [p2, needs DISC-68]
DISC-69 (QA) -- Match quality eval rubric (per-tier version)                             [p2, needs DISC-68]
DISC-71 (PM) -- ADR-011 for 3-tier architecture + update solution spec                  [p2, needs DISC-68]
DISC-72 (QA) -- Eval runner: add match_quality dimension per tier                        [p3, needs DISC-69 + DISC-68]
DISC-73 (FE) -- Solution browser: list view of Library A records                         [p3, needs DISC-67]
```

---

### DISC-66 [BE]: Schema definitions for 3-tier architecture

**User story:** As a developer, I need typed schemas for SolutionRecord, IndustryCaseStudy,
and MatchResult so that both ingestion pipelines and the matching layer share one
source of truth.

**done_when:** `rag/schemas.py` exports `SolutionSchema`, `IndustryCaseStudySchema`, and
`MatchResult` as Pydantic models, and all 20 existing victories.json records pass
`SolutionSchema` validation after a one-time backfill script runs.

**Acceptance criteria:**
- `rag/schemas.py` defines `SolutionSchema` (Pydantic) with all existing fields plus:
  `status` (enum: draft/active/deprecated), `ingestion_date` (ISO date string),
  `solution_category` (enum: predictive_model/classification/nlp/computer_vision/optimization/scoring_model),
  `applicable_signals` (list of Signal.type strings from orchestrator/schemas.py)
- `rag/schemas.py` defines `IndustryCaseStudySchema` (Pydantic) with all fields listed
  in the data model section of this plan
- `orchestrator/schemas.py` gains `MatchResult` replacing `VictoryMatch`, with fields
  described in the data model section, including per-tier optional blocks
- `VictoryMatch` kept as alias for backwards compatibility (deprecated comment added)
- Backfill script `rag/backfill_solutions.py` reads victories.json and adds missing
  fields with sensible defaults: status="active", ingestion_date=today,
  solution_category derived from ml_approach heuristic, applicable_signals=[]
- All 20 existing wins pass `SolutionSchema` validation after backfill
- Validation errors are human-readable: "win-007: missing field 'ingestion_date'"

**Execute with:**
  Primary: backend
  Collaborators: none
  Reason: Python schema work in rag/ and orchestrator/, BE ownership

**Test certification required:** yes
**Decision required:** yes (MatchResult replaces VictoryMatch -- architecture decision)
**Blocked by:** none
**Priority:** p1

---

### DISC-67 [BE]: Delivered solutions ingestion CLI (Library A)

**User story:** As a Tenex engagement lead, I need a CLI to add a new delivered solution
to Library A so that the wins library grows after each engagement without hand-editing JSON.

**done_when:** `python rag/ingest_solution.py --file solution.json` validates against
`SolutionSchema`, embeds, and upserts into the `tenex_delivered` ChromaDB collection.
A sample fixture solution passes in dry-run mode.

**Acceptance criteria:**
- `rag/ingest_solution.py` accepts `--file <path>` and `--dry-run` flags
- Writes to ChromaDB collection named `"tenex_delivered"` -- not the existing `"ai_solutions"`
  collection (separate collections are the architecture contract)
- Validates against `SolutionSchema` before touching the store
- On validation failure: prints field errors, exits non-zero, nothing written
- On success: generates embed_text if absent, upserts, prints confirmation with record ID
- `--dry-run`: validates and logs what would happen, does not call ChromaDB
- Idempotent: upsert by id (same file twice does not duplicate)
- Exit codes: 0 = success, 1 = validation failure, 2 = store write failure
- `rag/ingest.py` `ensure_seeds_loaded()` updated to use `tenex_delivered` collection
  and validate through `SolutionSchema` before loading
- `tests/fixtures/sample_solution.json` added: one valid SolutionRecord for testing
- `rag/vector_store.py` `ChromaStore` extended to support named collections
  (currently hardcoded to `"ai_solutions"` -- must accept collection_name param)

**Execute with:**
  Primary: backend
  Collaborators: none
  Reason: Python CLI in rag/ and vector_store.py update, BE ownership

**Test certification required:** yes
**Decision required:** no
**Blocked by:** DISC-66
**Priority:** p1

---

### DISC-74 [BE]: Industry cases ingestion CLI (Library B)

**User story:** As a Tenex researcher, I need a CLI to add industry case studies to
Library B so that the Ambitious tier has a growing evidence base of what other companies
in a client's space have done with AI.

**done_when:** `python rag/ingest_industry_case.py --file case.json` validates against
`IndustryCaseStudySchema`, embeds, and upserts into the `industry_cases` ChromaDB
collection. A sample fixture case passes in dry-run mode.

**Acceptance criteria:**
- `rag/ingest_industry_case.py` accepts `--file <path>` and `--dry-run` flags
- Writes to ChromaDB collection named `"industry_cases"` -- separate from `"tenex_delivered"`
- Validates against `IndustryCaseStudySchema` before touching the store
- Same validation/exit-code behavior as ingest_solution.py (consistent CLI contract)
- `--dry-run` validates and logs without calling ChromaDB
- Idempotent: upsert by id
- `tests/fixtures/rag_seeds/industry_cases.json` added: 5 seed records covering
  retail, logistics, healthcare, financial_services, manufacturing industries
- `tests/fixtures/sample_industry_case.json` added: one valid IndustryCaseStudy for testing
- `rag/ingest.py` `ensure_seeds_loaded()` updated to also load industry_cases.json
  into the `industry_cases` collection on startup
- `MockStore` updated to return from industry_cases.json when queried with
  collection parameter "industry_cases"

**Execute with:**
  Primary: backend
  Collaborators: none
  Reason: new Python CLI in rag/, parallel to ingest_solution.py, BE ownership

**Test certification required:** yes
**Decision required:** no
**Blocked by:** DISC-66
**Priority:** p1

---

### DISC-68 [BE]: Matching layer with 3-channel logic

**User story:** As a developer, I need the matching layer to query both ChromaDB
collections and produce three clearly typed output tracks so that the use case
generator and UI can treat Delivered, Adaptation, and Ambitious recommendations
as distinct evidence types.

**done_when:** `orchestrator/matching_layer.py` exports `match()` that returns
`dict[str, list[MatchResult]]` with keys `"delivered"`, `"adaptation"`, `"ambitious"`,
each populated from the correct library with confidence within the correct band.

**Acceptance criteria:**
- `orchestrator/matching_layer.py` contains `match()`:
  ```
  def match(
      signals: SignalSet,
      maturity: MaturityResult,
      delivered_results: list[dict],    # from "tenex_delivered" collection
      industry_results: list[dict],     # from "industry_cases" collection
  ) -> dict[str, list[MatchResult]]:
  ```
- Function docstring documents all three tracks, confidence bands, and scoring dimensions
- Track 1 (DELIVERED): scoring same as existing victory_matcher + sector_tag_bonus + applicable_signals bonus.
  Threshold: total >= 0.75 AND industry_score > 0. Confidence: 0.80-0.95.
- Track 2 (ADAPTATION): same Library A records, different threshold (0.45-0.74).
  A record that scored below DELIVERED threshold becomes an ADAPTATION candidate.
  Confidence mapped to 0.55-0.79 range. Gap analysis computed and stored in adaptation_notes.
- Track 3 (AMBITIOUS): Library B records scored against company signals:
  industry_match (0-0.4) + signal_type_overlap (0-0.4, count of matching applicable_signals) +
  company_size_hint_match (0-0.2). Threshold: any score >= 0.30. Confidence: 0.40-0.65.
- A Library A record can only appear in DELIVERED or ADAPTATION, never both.
  The higher-scoring track wins. A record at 0.76 is DELIVERED, not ADAPTATION.
- Result dict always has all three keys. Empty list if no matches for that tier.
- `orchestrator/victory_matcher.py` becomes a thin wrapper:
  calls `matching_layer.match()` then flattens results for backwards compatibility
- `orchestrator/stage_io.py` updated to log per-tier match counts
- `agents/rag_query.py` updated to query both collections separately and return both lists
- `tests/test_matching_layer.py` added: unit tests for each track's threshold logic

**Execute with:**
  Primary: backend
  Collaborators: none
  Reason: orchestrator/ and agents/ Python work, BE ownership

**Test certification required:** yes
**Decision required:** yes (two-collection RAG is an architecture change -- ADR-011)
**Blocked by:** DISC-66
**Priority:** p1

---

### DISC-70 [BE]: Fix tier_classification eval score

**User story:** As the PM, I need tier_classification eval score to reach >= 3.80
so that all eval dimensions are above threshold at sprint close.

**done_when:** Running `python evals/ci_eval.py` with sprint_8 key produces
tier_classification average >= 3.80 across all test companies.

**Acceptance criteria:**
- Root cause investigated: judge does not clearly connect signal evidence to tier assignment
  in use case rationale. The fix is in the `why_this_company` content of fixture use cases.
- Each LOW_HANGING_FRUIT use case in `tests/fixtures/sample_analysis.json` adds explicit
  tier rationale in `why_this_company`: names the tier, references maturity score range,
  cites at least 2 signal IDs with their values
- If fixture fix is insufficient, `prompts/use_case_generator.md` updated to v1.2 to
  require tier rationale in why_this_company. Logged in prompts/VERSIONS.md.
- `evals/ci_eval.py` updated to `_SPRINT = "sprint_8"` with new entry in baselines.json
- Actual eval run executed, score confirmed >= 3.80 before ticket closes
- evidence_grounding and roi_basis still >= 3.80 (no regressions)

**Execute with:**
  Primary: backend
  Collaborators: pm (if prompt change needed)
  Reason: fixture files and eval runner are BE+QA scope; prompts are PM if needed

**Test certification required:** yes
**Decision required:** no
**Blocked by:** none (independent)
**Priority:** p1

---

### DISC-75 [PM]: Three synthesis prompts (one per tier)

**User story:** As the use case generator agent, I need a dedicated synthesis prompt
for each tier so that Delivered, Adaptation, and Ambitious use cases have distinct
evidence requirements, tone, and ROI grounding rules.

**done_when:** Three prompt files exist in `prompts/` with distinct synthesis rules,
evidence requirements, and output schemas per tier. Each logged in VERSIONS.md.

**Acceptance criteria:**

`prompts/tier1_delivered.md` (DELIVERED tier):
- Role: synthesize a specific use case from a proven Tenex delivery
- Evidence required: win_id, exact primary metric, measurement period, client profile summary
- ROI rule: cite exact proven metric. No ranges. No projections. This happened.
- Confidence: always >= 0.80 (DIRECT evidence)
- why_this_company: cite specific company signals + how they match the win's client profile
- Output format: same UseCase JSON schema, tier="LOW_HANGING_FRUIT"
- Includes example showing correct win citation format

`prompts/tier2_adaptation.md` (ADAPTATION tier):
- Role: synthesize a use case from an adjacent Tenex delivery, describing the adaptation
- Evidence required: base win_id, what is the same, what changes, adaptation cost estimate
- ROI rule: cite base win metric then apply stated discount factor. "Base win: 14% fuel reduction.
  Adapted estimate: 8-12% -- different industry adds delivery risk."
- Confidence: 0.55-0.79 (adaptation adds uncertainty)
- why_this_company: explain the gap, not just the fit
- Output format: UseCase JSON with tier="MEDIUM_SOLUTION" and adaptation_context field
- Includes example showing discount factor pattern

`prompts/tier3_ambitious.md` (AMBITIOUS tier):
- Role: synthesize a use case from industry evidence -- NOT a Tenex win
- Evidence required: at least one named company or published case study reference
- ROI rule: state range, cite industry source, explicitly label as estimate. Never cite Tenex wins.
- Confidence: 0.40-0.65 (hard cap -- this is experimental)
- why_this_company: industry trend + company signals that suggest readiness
- Output format: UseCase JSON with tier="HARD_EXPERIMENT" and industry_references field
- Includes example showing industry citation format

All three prompts:
- Logged in `prompts/VERSIONS.md` at v1.0
- Free of AI writing patterns (no "leverage", "streamline", "robust")
- Follow write_prompt.md skill format

**Execute with:**
  Primary: pm
  Collaborators: none
  Reason: prompts/*.md is PM ownership

**Test certification required:** no (prompts are not executable)
**Decision required:** no
**Blocked by:** none
**Priority:** p1

---

### DISC-76 [BE]: Use case generator: per-tier synthesis

**User story:** As a developer, I need the use case generator to synthesize each tier
using the correct prompt so that Delivered use cases cite proven wins, Adaptation use
cases explain the gap, and Ambitious use cases cite industry evidence.

**done_when:** `agents/use_case_generator.py` reads the three tier prompts and makes
separate synthesis calls per tier, returning a flat `list[UseCase]` ordered
DELIVERED first, ADAPTATION second, AMBITIOUS third.

**Acceptance criteria:**
- `agents/use_case_generator.py` reads the three prompt files instead of one
- Three model calls made per pipeline run (one per tier) if matches exist for that tier
- Each call receives only the MatchResult records for that tier -- no cross-contamination
- Empty tier = skip the call, no empty use cases returned
- Return list is ordered: DELIVERED (LOW_HANGING_FRUIT), ADAPTATION (MEDIUM_SOLUTION),
  AMBITIOUS (HARD_EXPERIMENT)
- Minimum 1 use case total returned. If no matches in any tier, returns single AMBITIOUS
  use case using general industry signals.
- `tests/fixtures/sample_analysis.json` updated to contain use cases from all three tiers
- Dry-run still works: MockProvider returns per-tier fixture use cases
- All existing use case generator tests still pass

**Execute with:**
  Primary: backend
  Collaborators: none
  Reason: agents/use_case_generator.py is BE ownership

**Test certification required:** yes
**Decision required:** no
**Blocked by:** DISC-68, DISC-75
**Priority:** p2

---

### DISC-77 [FE]: Three-tier recommendation UI

**User story:** As Sai in a client demo, I need the analysis result to show three clearly
separated recommendation sections -- Delivered, Adaptation, and Ambitious -- so a client
can see immediately which recommendations are proven, which are adapted, and which are
exploratory.

**done_when:** The analysis result page shows three visually distinct sections. Each
section has a header explaining what it means. Each use case card shows tier-appropriate
evidence (win citation for Delivered, adaptation notes for Adaptation, industry references
for Ambitious).

**Acceptance criteria:**

Three named sections, in order:
1. Delivered -- "Tenex has built this" -- green left border, checkmark header icon
2. Adaptation -- "Tenex has built something close" -- amber left border, wrench icon
3. Ambitious -- "Your industry is doing this" -- blue left border, arrow-up icon

Each section header includes:
- Section name (large, clear)
- One-sentence description of what the tier means
- Count of recommendations in this tier (e.g. "2 recommendations")

UseCase cards per section:
- DELIVERED: show win ID as a badge ("win-003"), show exact proven metric prominently,
  show client profile match ("Similar: mid-market logistics, 500 employees")
- ADAPTATION: show "Based on win-NNN" reference, show adaptation notes,
  show adjusted ROI with discount factor visible
- AMBITIOUS: show industry examples (company names / source), show "estimated" label
  on ROI, confidence badge styled differently to signal experimental nature

Section separation:
- Each section is visually distinct -- a labeled divider or card header, not just color
- If a section has no results, it is not rendered (no empty states mid-page)
- Section order is fixed: Delivered, Adaptation, Ambitious (top to bottom)

Current `UseCaseCard.tsx` and `UseCaseTierSection.tsx` refactored to support these
three named sections. The existing LOW_HANGING_FRUIT / MEDIUM_SOLUTION / HARD_EXPERIMENT
labels remain on individual cards but the section headers use plain English names.

No new backend endpoint needed -- the existing `POST /v1/analyze` response includes
tier in each use case.

**Execute with:**
  Primary: frontend
  Collaborators: none
  Reason: TypeScript/React components in frontend/, FE ownership

**Test certification required:** yes
**Decision required:** no
**Blocked by:** DISC-68 (needs three-tier output schema confirmed)
**Priority:** p2

---

### DISC-69 [QA]: Match quality eval rubric (per-tier version)

**User story:** As the PM, I need a rubric that measures whether the matching layer
correctly assigned records to the right tier so that match quality is measurable
per sprint.

**done_when:** `evals/rubrics/match_quality.yaml` defines 1-5 rubrics for each tier
that a judge can score from a company profile and the matching layer output.

**Acceptance criteria:**
- `evals/rubrics/match_quality.yaml` covers three sub-rubrics:
  one for DELIVERED tier quality, one for ADAPTATION, one for AMBITIOUS
- DELIVERED rubric: is the top record same industry? Is confidence >= 0.80?
  Does the win_id exist and match a real record? Are the cited metrics consistent
  with the source record?
- ADAPTATION rubric: is the base win plausibly adjacent? Does adaptation_notes
  explain the gap? Is the adjusted ROI lower than the base win ROI?
- AMBITIOUS rubric: does the case study match the company's industry? Is at least
  one named company or source cited? Is confidence within 0.40-0.65?
- Score anchors defined for each rubric (1=wrong, 3=plausible, 5=correct+well-justified)
- Judge prompt template provided: company profile summary + per-tier top match records
- File follows format of existing rubrics in evals/rubrics/

**Execute with:**
  Primary: qa
  Collaborators: none
  Reason: evals/rubrics/ is QA ownership

**Test certification required:** no (YAML spec)
**Decision required:** no
**Blocked by:** DISC-68
**Priority:** p2

---

### DISC-71 [PM]: ADR-011 for 3-tier architecture + update specs

**User story:** As a developer joining the project, I need the architecture decision
and data specs to document the 3-tier matching system so that changes to either library
or the matching layer have a clear contract to reference.

**done_when:** ADR-011 documents the three-tier architecture decision, the two-collection
RAG design, and the MatchResult contract. All spec and index files updated.

**Acceptance criteria:**
- `docs/decisions/ADR-011.md` created: "Three-Tier Matching Architecture"
  - Context: why single matching tier was insufficient
  - Decision: separate Tenex-won (Library A) from industry intelligence (Library B)
  - Three tiers with confidence bands and evidence sources
  - Two ChromaDB collections: tenex_delivered and industry_cases
  - MatchResult schema replacing VictoryMatch
  - Consequences: three synthesis prompts, per-tier eval rubric
- `docs/decisions/INDEX.md` updated with ADR-011 entry
- `docs/specs/victory_data_spec.md` updated to v2.0:
  - SolutionRecord new fields documented with valid values
  - IndustryCaseStudy documented as a new record type
  - Ingestion CLI commands documented with example
- `docs/ARCHITECTURE.md` updated to reflect two-library diagram from this plan
- `prompts/VERSIONS.md` updated to log the three new tier prompts

**Execute with:**
  Primary: pm
  Collaborators: none
  Reason: docs/ and prompts/VERSIONS.md are PM ownership

**Test certification required:** no
**Decision required:** no (this ticket IS the decision documentation)
**Blocked by:** DISC-68
**Priority:** p2

---

### DISC-72 [QA]: Eval runner: add match_quality dimension per tier

**User story:** As the PM, I need the eval runner to score match quality per tier
so that we can track whether DELIVERED matches are actually strong and AMBITIOUS
matches actually have industry evidence.

**done_when:** `evals/ci_eval.py` scores match_quality for each tier separately
and includes per-tier scores in baselines.json output.

**Acceptance criteria:**
- `_RUBRICS` dict in `ci_eval.py` extended with three match quality keys:
  `"match_quality_delivered"`, `"match_quality_adaptation"`, `"match_quality_ambitious"`
- Judge context for each: company profile + top MatchResult for that tier + rubric
- Sprint_8 baseline includes per-tier match_quality scores
- Baseline targets (first sprint measuring this):
  match_quality_delivered >= 3.50
  match_quality_adaptation >= 3.00
  match_quality_ambitious >= 2.80
- Existing three dimensions (tier_classification, evidence_grounding, roi_basis) unchanged
- Full eval run executed against test companies, scores recorded

**Execute with:**
  Primary: qa
  Collaborators: none
  Reason: evals/ directory is QA ownership

**Test certification required:** yes
**Decision required:** no
**Blocked by:** DISC-69, DISC-68
**Priority:** p3

---

### DISC-73 [FE]: Solution browser: Library A list view

**User story:** As Sai during a demo, I need to browse the delivered solutions library
in the UI so I can show a client the breadth of Tenex's delivery history.

**done_when:** Navigating to `/solutions` shows all active SolutionRecord entries
from Library A as cards, with industry, title, primary metric, and solution category
visible on each card.

**Acceptance criteria:**
- `/solutions` page added using Next.js App Router
- `GET /v1/solutions` backend endpoint returns all records with status="active"
  from the `tenex_delivered` collection (BE must add this endpoint -- collaborator task)
- Each card shows: engagement_title, industry badge, company profile size label,
  primary_metric label and value, solution_category tag
- Loading state: skeleton cards while fetching
- Error state: "Could not load solutions" message if fetch fails
- Page reachable from main nav (link added to header)
- No authentication (consistent with ADR-002)
- Mobile-responsive: cards stack vertically on small screens
- Industry Solutions Library (Library B) is NOT shown here -- this page is Tenex wins only

**Execute with:**
  Primary: frontend
  Collaborators: backend (needs GET /v1/solutions endpoint)
  Reason: TypeScript/React page in frontend/, FE ownership; BE adds one API endpoint

**Test certification required:** yes
**Decision required:** no
**Blocked by:** DISC-67 (needs tenex_delivered collection to exist)
**Priority:** p3

---

## Priority Summary

| Ticket | Priority | Owner | Blocks |
|--------|----------|-------|--------|
| DISC-66 | p1 | BE | DISC-67, DISC-74, DISC-68, DISC-76 |
| DISC-67 | p1 | BE | DISC-73 |
| DISC-74 | p1 | BE | DISC-68 (industry_cases collection) |
| DISC-68 | p1 | BE | DISC-76, DISC-77, DISC-69, DISC-71, DISC-72 |
| DISC-70 | p1 | BE | (sprint close gate) |
| DISC-75 | p1 | PM | DISC-76 |
| DISC-76 | p2 | BE | (use case quality) |
| DISC-77 | p2 | FE | (Sai demo) |
| DISC-69 | p2 | QA | DISC-72 |
| DISC-71 | p2 | PM | (documentation) |
| DISC-72 | p3 | QA | (eval tracking) |
| DISC-73 | p3 | FE | (Sai demo extra) |

---

## Execution Sequence

```
Phase 1 -- Foundation (run in parallel where possible):
  DISC-66 (BE)  -- schemas for all three record types + MatchResult
  DISC-70 (BE)  -- fix tier_classification (independent)
  DISC-75 (PM)  -- write three synthesis prompts (independent)

Phase 2 -- Ingestion pipelines (after DISC-66):
  DISC-67 (BE)  -- Library A ingestion CLI
  DISC-74 (BE)  -- Library B ingestion CLI + seed 5 industry cases

Phase 3 -- Matching layer (after DISC-66):
  DISC-68 (BE)  -- 3-channel matching logic + RAG query update

Phase 4 -- Synthesis + UI (after DISC-68 + DISC-75):
  DISC-76 (BE)  -- per-tier use case synthesis
  DISC-77 (FE)  -- three-tier UI panels

Phase 5 -- Eval + Docs (after DISC-68):
  DISC-69 (QA)  -- per-tier match quality rubric
  DISC-71 (PM)  -- ADR-011 + spec updates

Phase 6 -- Eval runner + browser (after Phase 5):
  DISC-72 (QA)  -- eval runner update
  DISC-73 (FE)  -- solution browser page
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Two ChromaDB collections complicates MockStore | Medium | Medium | MockStore extended to read from both fixture files by collection name |
| Industry cases (Library B) fixture takes time to write | Medium | Low | 5 seed records is enough for testing -- quality over quantity |
| Matching layer 3-channel logic breaks existing victory_matcher tests | Medium | Medium | Keep VictoryMatch as alias, victory_matcher.py wraps matching_layer.py |
| tier_classification still below 3.80 after fixture fix | Low | Medium | Prompt change to use_case_generator.md is the fallback |
| Three model calls per run increases latency | Medium | Medium | Calls are parallelizable within use_case_generator.py -- same ThreadPoolExecutor pattern as report_writer |
| DISC-76 and DISC-77 slip due to DISC-68 dependency | Medium | Low | DISC-77 can use mock data for visual review; DISC-73 is p3 and can slip to Sprint 9 |

---

## Sprint 8 Success Criteria

At sprint close, Sai can:

1. Run `python rag/ingest_solution.py --file tests/fixtures/sample_solution.json --dry-run`
   and see validation pass with fields logged cleanly.

2. Run `python rag/ingest_industry_case.py --file tests/fixtures/sample_industry_case.json --dry-run`
   and see a separate validation pass for an industry case study.

3. Run `python orchestrator/pipeline.py --dry-run` and see three-tier match output in logs:
   - DELIVERED: win-NNN, confidence >= 0.80, proven metric cited
   - ADAPTATION: win-NNN base, adaptation_notes explaining the gap
   - AMBITIOUS: ind-NNN, industry company or source named

4. Open the analysis result in the UI and see three clearly labeled sections:
   "Tenex has built this" / "Tenex has built something close" / "Your industry is doing this"
   Each visually distinct.

5. Run `python evals/ci_eval.py` and see six dimensions all >= threshold:
   - tier_classification >= 3.80
   - evidence_grounding >= 3.80
   - roi_basis >= 3.80
   - match_quality_delivered >= 3.50
   - match_quality_adaptation >= 3.00
   - match_quality_ambitious >= 2.80

6. Run `pytest tests/ -q --tb=short` and see 124+ tests passing, 0 failures.
