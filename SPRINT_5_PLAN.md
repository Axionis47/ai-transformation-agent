# Sprint 5 Plan -- Pitch Synthesis Engine + 3-Tier Recommendations

> Goal: Translate the thought engine's evidence into client-facing recommendations.
> Three tiers: Easy (proven wins), Medium (needs adaptation), Hard (ambitious).
> ROI translated from past wins to this company. Every score explainable.

---

## What we have (Sprint 4 output)

After reasoning completes, the Run object contains:
- `run.evidence`: list of EvidenceItem from WINS_KB, GOOGLE_SEARCH, USER_PROVIDED
- `run.reasoning_state`: ReasoningState with field_coverage, overall_confidence, coverage_gaps
- `run.assumptions`: AssumptionsDraft with confirmed assumptions
- `run.company_intake`: CompanyIntake with company_name, industry, employee_count_band

Evidence items from WINS_KB have `source_ref` = engagement_id (e.g., "eng-001"),
giving us direct pointers to the full engagement data in `data/wins_kb_seed/engagements.json`.

---

## Architecture -- pitch engine as a deterministic pipeline

```
Evidence (from thought engine)
    |
    v
+------------------+
| Template Library |  8 opportunity templates derived from wins KB patterns
+--------+---------+
         |
         v
+------------------+
| Template Matcher |  Scan evidence for win_signals, anti_signals per template
+--------+---------+
         |
         v
+------------------+
| Tier Classifier  |  Easy / Medium / Hard based on industry match + evidence strength
+--------+---------+
         |
         v
+------------------+
| ROI Translator   |  Past engagement measured_impact -> this company's estimated ROI
+--------+---------+
         |
         v
+------------------+
| Scorer           |  feasibility, roi, time_to_value, confidence (4 separate scores)
+--------+---------+
         |
         v
+------------------+
| Report Composer  |  Operator brief + evidence annex + coverage gaps
+------------------+
```

Key design decisions:
- Deterministic, not LLM-based. Template matching uses keyword signals and engagement lookups.
- Each component is a pure function (input -> output). No shared state mutation.
- The PitchEngine class orchestrates the pipeline. Only it calls run_manager.
- Engagement lookup dict passed at construction time for testability.

---

## File plan

### New files (engines/pitch/)

| File | Lines | Purpose |
|------|-------|---------|
| engines/pitch/__init__.py | 4 | Exports PitchEngine |
| engines/pitch/templates.py | ~80 | 8 opportunity templates with win/anti signals |
| engines/pitch/matcher.py | ~70 | Evidence-to-template matching with signal scoring |
| engines/pitch/tier_classifier.py | ~50 | Easy/Medium/Hard classification rules |
| engines/pitch/roi_model.py | ~70 | ROI translation with size and industry scaling |
| engines/pitch/scorer.py | ~50 | Four-dimension scoring using config weights |
| engines/pitch/composer.py | ~70 | Operator brief + evidence annex composition |
| engines/pitch/engine.py | ~80 | PitchEngine orchestrator |

### New files (API + tests)

| File | Lines | Purpose |
|------|-------|---------|
| api/routes/pitch.py | ~80 | POST /synthesize, POST /publish, GET /evidence, GET /report |
| tests/test_pitch_templates.py | ~60 | Template loading and signal definitions |
| tests/test_pitch_matcher.py | ~70 | Signal matching and scoring |
| tests/test_pitch_tier.py | ~50 | Tier classification rules |
| tests/test_pitch_roi.py | ~60 | ROI translation and scaling |
| tests/test_pitch_scorer.py | ~50 | Score computation |
| tests/test_pitch_api.py | ~80 | Endpoint integration tests |

### Modified files

| File | Change |
|------|--------|
| core/schemas.py | Add `opportunities` and `report` fields to Run |
| core/run_manager.py | Add `store_opportunities()` and `store_report()` methods |
| api/app.py | Register pitch router |
| api/routes/ui.py | Update SYNTHESIS hints with opportunity actions |

---

## Component specs

### 1. Template Library (engines/pitch/templates.py)

8 templates derived from the 18 seed engagements:

| template_id | name | solution_shape | workflow_area | covers engagements |
|-------------|------|----------------|---------------|-------------------|
| tpl-support-auto | Customer Support Automation | automation | support | eng-001, eng-011 |
| tpl-finance-auto | Financial Process Automation | automation | finance_ops | eng-005, eng-008, eng-016 |
| tpl-ops-auto | Operations Automation | automation | operations | eng-004, eng-012, eng-018 |
| tpl-fraud-copilot | Risk/Fraud Analysis Copilot | copilot | finance_ops | eng-002 |
| tpl-docs-copilot | Documentation/Content Copilot | copilot | operations | eng-006, eng-015 |
| tpl-predictive-ops | Predictive Analytics | decision_support | operations | eng-009, eng-010, eng-013 |
| tpl-compliance | Compliance/Document Review | decision_support | finance_ops | eng-003 |
| tpl-resource-opt | Resource/Dispatch Optimization | decision_support | operations | eng-007, eng-014, eng-017 |

Each template has:
```python
@dataclass
class OpportunityTemplate:
    template_id: str
    name: str
    description: str
    solution_shape: str       # automation | copilot | decision_support
    workflow_area: str         # support | finance_ops | operations | rev_ops
    win_signals: list[str]     # keywords in evidence that suggest this applies
    anti_signals: list[str]    # keywords that suggest it does not apply
    roi_drivers: list[str]     # what drives ROI for this pattern
    typical_timeline_weeks: int
    applicable_industries: list[str]  # industries with proven wins
    engagement_ids: list[str]  # linked seed engagements
```

### 2. Template Matcher (engines/pitch/matcher.py)

Algorithm:
1. For each template, scan ALL evidence items (snippet + title) for win_signals
2. Count win_signal_hits and anti_signal_hits
3. Track which WINS_KB evidence items match (these carry engagement_ids)
4. match_score = win_signal_hits / len(win_signals) if no anti_signals fired
5. If anti_signal hit, apply 0.5 penalty per hit
6. Return matches with score > 0.1, sorted descending

Output:
```python
@dataclass
class TemplateMatch:
    template: OpportunityTemplate
    match_score: float                 # 0.0 to 1.0
    win_signal_hits: list[str]         # which signals fired
    anti_signal_hits: list[str]        # which anti-signals fired
    matched_evidence_ids: list[str]    # evidence_ids that contributed
    matched_engagement_ids: list[str]  # wins KB engagement_ids found in evidence
```

### 3. Tier Classifier (engines/pitch/tier_classifier.py)

Rules (deterministic, no LLM):

**Easy** (all must be true):
- At least one matched_engagement_id exists
- At least one matched engagement is in the same industry as the company
- match_score >= 0.4

**Medium** (any of):
- Matched engagement exists but different industry (needs adaptation)
- match_score between 0.2 and 0.4 with same industry
- Matched engagement exists but different company_size_band

**Hard** (fallback):
- No matched engagements, or match_score < 0.2
- Opportunity inferred from grounding/user evidence only

Output: OpportunityTier enum (EASY | MEDIUM | HARD)

For Medium tier, also returns `adaptation_needed` string explaining what's different.

### 4. ROI Translator (engines/pitch/roi_model.py)

Algorithm:
1. For each matched engagement_id, load full engagement from lookup dict
2. Extract measured_impact dict
3. Apply size_scaling_factor:
   - Same band = 1.0
   - One band smaller = 0.6
   - One band larger = 1.3
   - Two+ bands different = 0.4
4. Apply industry_factor:
   - Same industry = 1.0
   - Adjacent (e.g., healthcare <-> financial_services) = 0.8
   - Different = 0.6
5. Compute estimated_savings from primary roi_driver metric * scaling
6. Sensitivity: vary each factor +/- 20%, measure impact on estimated ROI

Size bands ordering: ["50-100", "100-200", "200-500", "500-2000", "2000+"]

Output:
```python
@dataclass
class ROIEstimate:
    primary_metric: str          # e.g., "triage_time_reduction_pct"
    base_value: float            # from past engagement
    adjusted_value: float        # after scaling
    size_factor: float
    industry_factor: float
    source_engagement_id: str
    timeline_weeks: int
    assumptions: dict            # what we assumed for the scaling
    sensitivity: dict            # which assumptions matter most
```

### 5. Scorer (engines/pitch/scorer.py)

Uses weights from config/defaults.yaml:
```yaml
scoring:
  w_roi: 0.30
  w_feasibility: 0.30
  w_ttv: 0.20
  w_confidence: 0.20
```

Per-dimension scoring:
- **feasibility**: anti_signal_count == 0 -> 0.9, 1 hit -> 0.6, 2+ -> 0.3. Boost 0.1 if engagement in same industry.
- **roi**: Maps adjusted ROI value to 0-1 scale. >50% improvement -> 0.9, 20-50% -> 0.7, <20% -> 0.5, no data -> 0.3.
- **time_to_value**: <=8 weeks -> 0.9, 9-12 -> 0.7, 13-16 -> 0.5, >16 -> 0.3.
- **confidence**: Average relevance_score of matched evidence items.

Composite score = w_roi * roi + w_feasibility * feasibility + w_ttv * ttv + w_confidence * confidence.

### 6. Report Composer (engines/pitch/composer.py)

Produces a dict with three sections:

```python
{
    "operator_brief": {
        "company_name": str,
        "industry": str,
        "analysis_confidence": float,
        "opportunities_by_tier": {
            "easy": [...],
            "medium": [...],
            "hard": [...]
        },
        "coverage_gaps": [...],
        "budget_usage": {...}
    },
    "evidence_annex": [
        {"evidence_id": str, "source_type": str, "title": str, "snippet": str, "uri": str}
    ],
    "metadata": {
        "total_evidence_items": int,
        "total_opportunities": int,
        "reasoning_loops_completed": int,
        "run_id": str
    }
}
```

### 7. PitchEngine Orchestrator (engines/pitch/engine.py)

```python
class PitchEngine:
    def __init__(self, config: dict, engagement_lookup: dict[str, dict]):
        self._config = config
        self._engagements = engagement_lookup
        self._templates = get_templates()

    def synthesize(
        self, run_id: str, evidence: list[EvidenceItem],
        assumptions: AssumptionsDraft, company_intake: CompanyIntake,
        field_coverage: dict[str, float]
    ) -> list[Opportunity]:
        # 1. Match templates against evidence
        # 2. Classify tier for each match
        # 3. Translate ROI for each match
        # 4. Score each opportunity
        # 5. Build Opportunity objects
        # 6. Emit trace events
        # 7. Return sorted by composite score

    def compose_report(
        self, run_id: str, opportunities: list[Opportunity],
        evidence: list[EvidenceItem], reasoning_state: ReasoningState,
        company_intake: CompanyIntake
    ) -> dict:
        # Delegates to composer module
```

### 8. API Endpoints (api/routes/pitch.py)

```
POST /v1/runs/{run_id}/synthesize
  Validates: run.status == REASONING, reasoning_state.completed == True
  Transitions: REASONING -> SYNTHESIS -> REPORT
  Returns: { opportunities: [...], tier_counts: {...} }
  Emits: OPPORTUNITIES_COMPUTED, ROI_MODEL_COMPUTED, CONFIDENCE_COMPUTED, REPORT_RENDERED

POST /v1/runs/{run_id}/publish
  Validates: run.status == REPORT
  Transitions: REPORT -> PUBLISHED
  Returns: Run
  Emits: RUN_PUBLISHED

GET /v1/runs/{run_id}/evidence
  Returns: list[EvidenceItem]

GET /v1/runs/{run_id}/report
  Returns: report dict

GET /v1/runs/{run_id}/opportunities
  Returns: list[Opportunity]
```

---

## Schema changes

### Run model additions:
```python
class Run(BaseModel):
    ...
    opportunities: list[Opportunity] = []
    report: dict = {}
```

### run_manager additions:
```python
def store_opportunities(run_id: str, opportunities: list[Opportunity]) -> Run:
def store_report(run_id: str, report: dict) -> Run:
```

---

## Trace events (all already defined in core/events.py)

| Event | When |
|-------|------|
| OPPORTUNITIES_COMPUTED | After template matching + tier classification |
| ROI_MODEL_COMPUTED | After ROI translation |
| CONFIDENCE_COMPUTED | After scoring |
| REPORT_RENDERED | After report composition |
| RUN_PUBLISHED | After publish endpoint called |

---

## Commit plan (12 commits)

| # | Message | Files | Lines |
|---|---------|-------|-------|
| 1 | feat(schemas): add opportunity storage and report fields to Run | core/schemas.py | ~10 |
| 2 | feat(run-manager): add opportunity and report storage methods | core/run_manager.py | ~15 |
| 3 | feat(pitch): add opportunity template library with signal definitions | engines/pitch/templates.py, engines/pitch/__init__.py | ~80 |
| 4 | feat(pitch): add template matcher with evidence signal scoring | engines/pitch/matcher.py | ~70 |
| 5 | feat(pitch): add tier classifier with industry and evidence rules | engines/pitch/tier_classifier.py | ~50 |
| 6 | feat(pitch): add ROI translation model with scaling factors | engines/pitch/roi_model.py | ~70 |
| 7 | feat(pitch): add opportunity scorer and report composer | engines/pitch/scorer.py, engines/pitch/composer.py | ~80 |
| 8 | feat(pitch): add pitch engine orchestrator for synthesis flow | engines/pitch/engine.py | ~80 |
| 9 | feat(api): add synthesis publish and report endpoints | api/routes/pitch.py, api/app.py | ~80 |
| 10 | test(pitch): add template and matcher tests | tests/test_pitch_templates.py, tests/test_pitch_matcher.py | ~70 |
| 11 | test(pitch): add tier classifier ROI model and scorer tests | tests/test_pitch_tier.py, tests/test_pitch_roi.py, tests/test_pitch_scorer.py | ~70 |
| 12 | test(pitch-api): add synthesis and publish endpoint tests | tests/test_pitch_api.py | ~80 |

---

## Test plan (~35 tests)

### test_pitch_templates.py (6 tests)
- templates_load: all 8 templates load with required fields
- templates_unique_ids: no duplicate template_ids
- templates_cover_all_shapes: automation, copilot, decision_support all present
- templates_have_signals: every template has at least 2 win_signals
- templates_have_engagements: every template links to at least 1 engagement_id
- templates_applicable_industries: every template has at least 1 applicable industry

### test_pitch_matcher.py (6 tests)
- match_support_evidence: evidence with "support" + "triage" matches tpl-support-auto
- match_no_evidence: empty evidence returns no matches
- match_anti_signal_penalty: anti_signal hit reduces score
- match_multiple_templates: evidence can match multiple templates
- match_engagement_tracking: WINS_KB evidence links engagement_ids to match
- match_score_ordering: matches returned sorted by score descending

### test_pitch_tier.py (5 tests)
- tier_easy_same_industry: same industry + engagement match = EASY
- tier_medium_different_industry: different industry = MEDIUM with adaptation_needed
- tier_hard_no_engagement: no engagement match = HARD
- tier_medium_low_score: same industry but low score = MEDIUM
- tier_requires_engagement_for_easy: no engagement = never EASY

### test_pitch_roi.py (5 tests)
- roi_same_band_same_industry: no scaling applied
- roi_smaller_band_scales_down: smaller company = lower ROI
- roi_different_industry_discounts: different industry = 0.6x
- roi_no_engagement_returns_none: no matched engagement = no ROI data
- roi_sensitivity_output: sensitivity dict has the right keys

### test_pitch_scorer.py (5 tests)
- scorer_uses_config_weights: weights from config applied correctly
- scorer_no_anti_signals_high_feasibility: clean match = high feasibility
- scorer_short_timeline_high_ttv: <=8 weeks = 0.9 time_to_value
- scorer_composite_formula: composite = weighted sum of 4 dimensions
- scorer_no_evidence_low_confidence: no matched evidence = low confidence

### test_pitch_api.py (8 tests)
- synthesize_from_reasoning: POST /synthesize with completed reasoning works
- synthesize_wrong_status: 409 if not in REASONING
- synthesize_incomplete_reasoning: 400 if reasoning not completed
- publish_from_report: POST /publish transitions to PUBLISHED
- publish_wrong_status: 409 if not in REPORT
- get_evidence_returns_items: GET /evidence returns evidence list
- get_report_returns_report: GET /report returns composed report
- get_opportunities_returns_list: GET /opportunities returns opportunity list

---

## Success criteria

- [ ] Given thought engine output, produces 3-5 opportunities across all three tiers
- [ ] Each opportunity shows: evidence items that support it, template that matched, score breakdown
- [ ] Easy tier opportunities cite specific past engagements with measured ROI
- [ ] Medium tier opportunities explicitly state what adaptation is needed and why
- [ ] Hard tier opportunities show high potential but flag low confidence with reasons
- [ ] ROI model recomputes when user changes an assumption (e.g., employee count)
- [ ] Operator brief is one readable page with coverage gaps listed

---

## Dependencies

- Sprint 4 COMPLETE: Thought engine produces evidence + reasoning state
- core/schemas.py: Opportunity, OpportunityTier already defined
- core/events.py: OPPORTUNITIES_COMPUTED, ROI_MODEL_COMPUTED, CONFIDENCE_COMPUTED, REPORT_RENDERED already defined
- data/wins_kb_seed/engagements.json: 18 seed engagements available for ROI translation
- config/defaults.yaml: scoring weights and confidence weights already defined

---

## Key design rules

1. No LLM calls in the pitch engine. Everything is deterministic and testable.
2. Each component is a pure function: input -> output. No shared state.
3. PitchEngine orchestrates. Only it calls trace events and state updates.
4. Engagement data is passed as a lookup dict, not loaded from disk inside engine code.
5. Templates are hardcoded in Python (not loaded from YAML) -- they're derived from the wins KB patterns and versioned with code.
6. All scores are explainable: each Opportunity carries rationale, evidence_ids, and score breakdown.
7. The API does two transitions in one call: REASONING -> SYNTHESIS -> REPORT. This keeps the frontend simple.
