# End-Goal Report Design — AI Transformation Discovery Agent

**Version:** 1.0  
**Date:** 2026-03-16  
**Owner:** PM  
**Purpose:** Defines the complete final product — every section, every data field, every
screen — so that Frontend and Backend have a concrete target to build toward across sprints.

---

## Who Reads This and Why

**Primary reader:** Tenex consultant preparing for a client meeting  
**Secondary reader:** The prospect company's CFO or CTO who receives the report  
**Decision this report supports:** Should this company invest in AI transformation, in what
specifically, how much will it cost, and what is the plan?

**What makes a CFO trust this report?**
- Every claim traces to evidence from their own website
- Every ROI number has a stated basis (not invented)
- Confidence is honest — not everything is presented as certain
- The maturity score is grounded in named signals, not vibes
- Comparable companies are cited with real outcomes

**What makes a Tenex consultant use this in a meeting?**
- The exec summary can be read aloud in 60 seconds
- The use cases are specific enough to discuss, not so technical as to confuse
- The roadmap is believable — it starts from where the company actually is
- The evidence section answers "how do you know this?" before the CFO asks

---

## Part 1: End-Goal Report — Every Section, Every Field

### Cover Header

Displayed at the top of every report. Always visible.

```
┌─────────────────────────────────────────────────────────────┐
│  [Company Logo scraped from favicon/og:image]               │
│  ACME Logistics Corp                    [Industry: Logistics]│
│                                                              │
│  AI Maturity Score                                           │
│  ████████████░░░░░  2.5 / 5.0   Developing                  │
│                                                              │
│  Analysis date: 2026-03-16    Run ID: a1b2c3d4              │
│  Prepared by Tenex AI Discovery Platform                     │
└─────────────────────────────────────────────────────────────┘
```

**Data fields required:**
- `company_name` — string (inferred from scraped data)
- `company_url` — string
- `company_logo_url` — string | null (scraped from og:image or favicon)
- `industry` — string (from industry_hint signal)
- `maturity_score` — float 0.0–5.0
- `maturity_label` — Beginner | Developing | Emerging | Advanced | Leading
- `analysis_date` — ISO date string
- `run_id` — string

---

### Section 1: Executive Summary

**Audience:** CEO. Non-technical. 30 seconds to read.  
**Purpose:** The single most important thing we found, stated clearly.  
**Length:** 4–5 sentences maximum.

**Content requirements (all must be present):**
1. Maturity score + label in the first sentence with peer comparison
2. The single highest-impact finding (what makes this company interesting)
3. The top 1–2 use cases named in plain English (no jargon)
4. One specific ROI number
5. One closing recommendation: what to do first

**Mock example (Developing company, logistics):**
> ACME Logistics Corp scores 2.5 out of 5 — Developing — placing them ahead of 40% of
> mid-market logistics companies we have assessed. Their strongest signal is a mature
> data engineering team processing 50 million daily shipment events, which is the exact
> foundation needed for predictive ML. The highest-value opportunity is a shipment delay
> prediction model that Tenex has deployed for comparable carriers, reducing late
> deliveries by 18% and saving $2.1M annually. We recommend starting with carrier
> performance scoring in the next 90 days — it can be built on existing data with no
> new infrastructure investment.

**What the exec summary must NOT contain:**
- Technical terms: MLOps, feature store, dbt, ChromaDB, vector embeddings
- Methodology explanation ("we scraped your website and...")
- Vague language without a number ("significant potential")
- More than 5 sentences

**Data fields:**
- `report_sections.exec_summary` — string, 60–120 words

---

### Section 2: AI Maturity Assessment

**Audience:** CTO + senior technical team  
**Purpose:** Show the evidence behind the score. Every number is earned.

**Visual:** Radar chart with four axes. Numeric score per axis. Overall score prominent.

```
                    Data Infrastructure
                           4
                    ┌──────┼──────┐
                    │    ╱ │ ╲    │
 Operational   4────┼──╱───┼───╲──┼────4  ML/AI Capability
 Readiness          │╱     │     ╲│
                    │      ●      │   ● = 2.5 composite
                    │╲     │     ╱│
                    │  ╲   │   ╱  │
                    └──────┼──────┘
                           4
                    Strategy & Intent
```

**Per-dimension display (one block per dimension, 4 total):**

```
Data Infrastructure                                     2.5 / 5.0
━━━━━━━━━━━━━━━━━━━━━━━━━━░░░░░░░░░░░  (50%)

Signals found:
  ✓ Snowflake data warehouse mentioned in engineering blog
  ✓ "50M daily shipment events" cited in job posting
  ✓ dbt + Airflow stack referenced in Senior Data Engineer JD
  ✗ No real-time feature store or ML feature engineering found

What this means: Strong data foundation — the warehouse and pipeline work
exist. The gap is feature engineering infrastructure for ML training.
```

**Data fields per dimension:**
- `dimensions.data_infrastructure.score` — float
- `dimensions.data_infrastructure.signals_used` — list[string]
- `dimensions.data_infrastructure.rationale` — string
- Same structure for ml_ai_capability, strategy_intent, operational_readiness

**Maturity stage context panel:**

```
What "Developing" means for a company your size:

Companies at this stage have invested in data infrastructure but have not
yet deployed production ML models. The typical next step is a single
low-risk predictive model that proves the ML pipeline end-to-end.
Tenex has worked with 12 Developing-stage logistics companies. Average
time to first production model: 6–8 weeks.
```

**Collapsible evidence panel:**
- "Show all 14 signals" — expands to full signal list
- Each signal shows: type, value, source (about_text / job_posting / product_page)
- Signal type is colour-coded: tech_stack (blue), ml_signals (purple), data_signals (green), intent_signals (amber)

**Data fields:**
- `signals` — list[Signal] with type, value, source fields

---

### Section 3: Proven Solutions — Low-Hanging Fruit

**Visual treatment:** GREEN accent. Header: "Proven Solutions — We've Done This"  
**Audience:** CTO + project sponsor  
**Purpose:** These are the recommendations backed by direct Tenex delivery wins.

**Card format (one card per use case in this tier):**

```
┌────────────────────────────────────────────────────────────────┐
│  PROVEN    Shipment Delay Prediction                           │
│  ─────────────────────────────────────────────────────────────│
│  Predict which shipments will be delayed 24–48 hours in        │
│  advance using carrier performance history and weather data.   │
│  Reduces reactive customer service load by routing exceptions  │
│  before they become complaints.                                │
│                                                                │
│  Why this works for ACME:                                      │
│  Job posting for "Sr Data Engineer" references 50M daily       │
│  shipment events in Snowflake — this exact dataset trains the  │
│  delay model. No new data collection required.                 │
│                                                                │
│  Based on: win-003 — Shipment Delay Prediction for Regional    │
│  LTL Carrier (DIRECT_MATCH — same industry, same size tier)    │
│  "18% reduction in late deliveries, $2.1M annual saving        │
│   4 months post-deployment"                                    │
│                                                                │
│  Effort     Impact       ROI Estimate      Confidence          │
│  ────────   ──────────   ───────────────   ──────────          │
│  Low        High         $1.8M–$2.4M/yr    0.85                │
│  8–10 wks   Revenue KPI  (at ACME volume)                      │
│                                                                │
│  Timeline: 10 weeks to production                              │
│                                                                │
│  Data Flow:                                                    │
│  Input:    Snowflake shipment history (18 months) + carrier    │
│            performance records + weather API feed              │
│  Model:    Gradient boosted classifier trained on delay labels  │
│            from historical shipments (XGBoost / LightGBM)     │
│  Output:   Risk score per shipment surfaced in operations      │
│            dashboard 24–48 hrs ahead of expected delivery      │
│  Feedback: Actual delivery outcomes logged weekly; model       │
│            retrained monthly on rolling 6-month window         │
│  Value:    Late delivery rate tracked monthly vs prior year    │
│            baseline; alert if improvement < 8%                 │
│                                                                │
│  [See Full Evidence]   [Implementation Plan]                   │
└────────────────────────────────────────────────────────────────┘
```

**Card data fields:**
- `title` — string
- `description` — string, 2–3 sentences
- `tier` — PROVEN | ACHIEVABLE | FRONTIER
- `why_this_company` — string (evidence-grounded paragraph, specific to this prospect)
- `victory_citation.win_id` — string
- `victory_citation.engagement_title` — string
- `victory_citation.match_tier` — DIRECT_MATCH | CALIBRATION_MATCH | ADJACENT_MATCH
- `victory_citation.roi_benchmark` — string (the actual result from the win)
- `effort` — Low | Medium | High
- `impact` — Low | Medium | High
- `roi_estimate` — string (scaled to this company's volume)
- `roi_basis` — string (how the estimate was derived)
- `confidence` — float 0.0–1.0
- `implementation_weeks` — int
- `data_flow.data_inputs` — list[string] (client's existing data sources that feed the model)
- `data_flow.model_approach` — string (specific model type and training approach)
- `data_flow.output_consumer` — string (role and delivery mechanism — e.g. "Dispatchers via ops dashboard")
- `data_flow.feedback_loop` — string (how model improves post-deployment)
- `data_flow.value_measurement` — string (specific metric, cadence, and baseline comparison)

**Data Flow design note:**
For PROVEN tier, the `data_flow` fields are derived directly from the matched victory record's
`tech_stack.data_sources`, `tech_stack.ml_approach`, and `tech_stack.client_systems_integrated`
fields. The use case generator maps these directly — no inference required.

---

### Section 4: Achievable Opportunities — Medium Effort

**Visual treatment:** AMBER accent. Header: "Achievable Opportunities — Plan for These"  
**Audience:** CTO + technical lead  
**Purpose:** Use cases that require more setup but deliver meaningful value.

**Same card format as Section 3, with additions:**

```
┌────────────────────────────────────────────────────────────────┐
│  ACHIEVABLE    Carrier Performance Scoring                     │
│  ─────────────────────────────────────────────────────────────│
│  ...                                                           │
│                                                                │
│  Calibration note:                                             │
│  Based on win-001 (logistics, enterprise-scale). ACME is       │
│  mid-market — expect 60–70% of the cited ROI at current        │
│  shipment volume. Full impact reaches enterprise benchmarks    │
│  as volume grows.                                              │
│                                                                │
│  What you need first:                                          │
│  ✓ Data already exists in Snowflake                            │
│  ✗ Need: carrier API integration for real-time feed            │
│  ✗ Need: one ML engineer hire or contractor engagement         │
│                                                                │
│  Risk factors:                                                 │
│  • Carrier data quality varies — plan 2–3 weeks data cleaning  │
│  • Stakeholder alignment with carrier relationships team needed│
│                                                                │
│  Data Flow:                                                    │
│  Input:    Snowflake historical shipment records + carrier     │
│            rate cards + new real-time carrier API feed         │
│            (API integration required — see prerequisites)      │
│  Model:    XGBoost regression scoring carriers by cost,        │
│            reliability, and on-time delivery probability       │
│  Output:   Carrier recommendation surfaced to procurement      │
│            manager in TMS at point of shipment booking         │
│  Feedback: Actual vs predicted on-time rates logged per        │
│            carrier; model recalibrated quarterly               │
│  Value:    Per-shipment carrier cost reduction measured        │
│            monthly vs prior year; target > 8% improvement     │
└────────────────────────────────────────────────────────────────┘
```

**Additional data fields:**
- `calibration_note` — string (why the ROI is adjusted from the benchmark)
- `prerequisites` — list[{item, status: "exists" | "needed"}]
- `risk_factors` — list[string]
- `data_flow.data_inputs` — list[string] (client's existing data + what must be acquired)
- `data_flow.model_approach` — string (adapted from CALIBRATION_MATCH victory or strong signal convergence)
- `data_flow.output_consumer` — string (specific role and delivery interface)
- `data_flow.feedback_loop` — string (retraining cadence and feedback source)
- `data_flow.value_measurement` — string (metric, measurement period, target threshold)

**Data Flow design note:**
For ACHIEVABLE tier, `data_flow` is adapted from the CALIBRATION_MATCH victory record's
`tech_stack` fields, adjusted for the client's scale and system landscape. Prerequisites
that are "needed" map to gaps between the victory's `client_systems_integrated` and
the client's current signals.

---

### Section 5: Frontier Experiments — Strategic Bets

**Visual treatment:** BLUE accent. Header: "Frontier Experiments — Invest With Eyes Open"  
**Audience:** CEO + board-level strategy  
**Purpose:** High-upside ideas where evidence is thinner. Honest about uncertainty.

**Card additions:**

```
┌────────────────────────────────────────────────────────────────┐
│  FRONTIER    Dynamic Route Optimisation at Scale               │
│  ─────────────────────────────────────────────────────────────│
│  ...                                                           │
│                                                                │
│  Uncertainty note:                                             │
│  Tenex has not deployed this exact solution for a company at   │
│  ACME's scale. The match is win-007 (logistics, enterprise),   │
│  classified as CALIBRATION_MATCH — same problem type, but      │
│  ACME is 3x smaller. ROI extrapolation carries higher          │
│  uncertainty.                                                  │
│                                                                │
│  Why it's still worth exploring:                               │
│  ACME's 50M daily event volume is unusually large for their    │
│  size tier. This is a competitive asymmetry — a route model    │
│  trained on this data density would outperform competitors.    │
│                                                                │
│  Confidence: 0.50   (lower — this is a frontier bet)          │
│                                                                │
│  Data Flow (proposed — not yet validated):                     │
│  Input:    TMS shipment history + GPS telemetry stream +       │
│            live traffic API + carrier rate cards               │
│            (GPS telemetry collection required — new infra)     │
│  Model:    Reinforcement learning or multi-objective optimizer  │
│            scoring route options by cost, time, reliability    │
│  Output:   Ranked route suggestions to dispatcher planning     │
│            interface; also available via API for TMS auto-book │
│  Feedback: Actual delivery time + fuel cost logged per route;  │
│            model retrained weekly on rolling 3-month window    │
│  Value:    Fuel cost per route vs prior year baseline;         │
│            targeted > 10% reduction over 12 months            │
└────────────────────────────────────────────────────────────────┘
```

**Additional data fields:**
- `uncertainty_note` — string (honest statement of what we don't know)
- `strategic_upside` — string (why the bet is worth making despite uncertainty)
- `data_flow.data_inputs` — list[string] (what the client has + what must be built or acquired)
- `data_flow.model_approach` — string (proposed approach based on signals and industry patterns)
- `data_flow.output_consumer` — string (role and interface — may be proposed, not confirmed)
- `data_flow.feedback_loop` — string (proposed retraining mechanism)
- `data_flow.value_measurement` — string (how success would be measured — stated as hypothesis)

**Data Flow design note:**
For FRONTIER tier, `data_flow` is proposed rather than proven. The use case generator
constructs the data flow from: (a) signals indicating existing data assets, (b)
ADJACENT_MATCH victory's `tech_stack` as a pattern reference, and (c) industry
patterns for the use case type. Data inputs labeled "required" are net-new investments.
The model approach is explicitly framed as a proposal, not a blueprint.

---

### Section 6: ROI Analysis

**Audience:** CFO  
**Purpose:** Show the math. Every number has a basis. Conservative estimates.

**Summary table:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Use Case                  │ Est. Annual Impact  │ Impl. Cost │ Payback     │
│  ──────────────────────────┼─────────────────────┼────────────┼─────────────│
│  Shipment Delay Prediction │ $1.8M – $2.4M       │ $180K–$240K│ 5–8 months  │
│  Carrier Performance Score │ $600K – $900K       │ $120K–$180K│ 3–4 months  │
│  Route Optimisation        │ $3.0M – $5.0M       │ $400K–$600K│ 12–18 months│
│  ──────────────────────────┼─────────────────────┼────────────┼─────────────│
│  TOTAL PORTFOLIO           │ $5.4M – $8.3M       │ $700K–$1.0M│ 8–12 months │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Math transparency panel (collapsible per use case):**

```
Shipment Delay Prediction — how we calculated this:

Volume basis:    50M daily shipment events (from ACME job posting)
Monthly volume:  ~1.5M shipments/month (estimated from events-to-shipment ratio)
Benchmark:       win-003 — 18% reduction in late deliveries at comparable carrier
Conservative:    Using 12% (lower bound, adjusted for ACME's smaller size)
Late delivery rate (industry avg): 8% of shipments → 120K late/month
Improvement:     12% fewer → 14,400 fewer late shipments/month
Cost per late shipment: $10–$14 (carrier penalties + customer service)
Annual saving:   14,400 × 12 months × $12 average = $2.07M
Range shown:     $1.8M–$2.4M (±15% for implementation variance)
```

**Data fields:**
- `roi_analysis.use_cases` — list of per-use-case ROI objects
  - `title`, `annual_impact_low`, `annual_impact_high`, `impl_cost_low`, `impl_cost_high`, `payback_months_low`, `payback_months_high`
  - `math_narrative` — string (the "how we calculated" explanation)
  - `basis` — string (what data source grounds the estimate)
- `roi_analysis.portfolio_summary` — total range + payback
- `roi_analysis.conservative_note` — string ("we used the lower bound of benchmarks...")

---

### Section 7: Implementation Roadmap

**Audience:** CTO + project sponsor  
**Purpose:** A believable plan starting from where the company actually is.

**Visual:** Three-phase horizontal timeline.

```
Phase 1: Foundation           Phase 2: Core               Phase 3: Scale
0 – 90 days                   3 – 6 months                 6 – 12 months
────────────────────          ────────────────────         ────────────────────

OBJECTIVE                     OBJECTIVE                    OBJECTIVE
Prove ML pipeline works       Deliver proven value         Expand and compound
with one low-risk model       via primary use case         the ML investment

BUILD                         BUILD                        BUILD
Carrier performance           Shipment delay               Route optimisation
scoring model                 prediction model             (frontier candidate)

WHO                           WHO                          WHO
1 x ML Engineer               ML Eng + Data Eng            Dedicated ML team (3)
(contract or hire)            (existing team + 1)          platform team support

PROVE IT WORKED               PROVE IT WORKED              PROVE IT WORKED
Carrier score predicts        Late delivery rate drops      Fuel cost per route
actual delay within ±2        by >10% within 60 days       reduces >8% vs baseline
days in backtest

DEPENDENCY                    DEPENDENCY                   DEPENDENCY
None — uses existing          Phase 1 model deployed       Phase 2 in production
Snowflake data                and monitoring in place      with clean data signal
```

**Data fields:**
- `roadmap.phases` — list of 3+ phase objects
  - `phase_name`, `duration`, `objective`, `what_gets_built`, `who_builds_it`
  - `proof_of_success` — string (the measurable outcome that proves Phase N worked)
  - `dependency` — string | null (what must be true before this phase starts)
  - `primary_use_case_id` — string (links to a use case card)

---

### Section 8: Evidence and Sources

**Audience:** Sceptical CTO reviewing the analysis methodology  
**Purpose:** Full traceability — every claim has a source.

**Signal inventory panel:**

```
Analysis based on 18 signals from 4 pages

Pages scraped:
  https://acme-logistics.com/about         (1,247 words extracted)
  https://acme-logistics.com/careers       (8 job postings, 3,412 words)
  https://acme-logistics.com/product       (892 words extracted)
  https://acme-logistics.com/engineering   (2 blog posts, 1,104 words)

Signals extracted:
  Tech stack (5):    Snowflake, dbt, Airflow, Kubernetes, AWS
  Data signals (4):  50M daily events, real-time pipeline, 5TB/month
  ML signals (2):    ML Engineer JD, "predictive ETA" mentioned in product page
  Intent signals (3): CEO letter mentions AI roadmap, investor deck excerpt
  Ops signals (2):   Kubernetes deployment, CI/CD pipeline referenced
  Industry (1):      Logistics (confidence: 0.95)
  Scale (1):         Mid-market, 800–1200 employees (evidence: careers page)

Victory matches used:
  win-003  Shipment Delay — Regional LTL Carrier       DIRECT_MATCH   0.82 similarity
  win-001  Route Optimisation — Mid-market Freight Co  CALIBRATION    0.71 similarity
  win-007  Dynamic Routing — Enterprise Carrier        ADJACENT       0.62 similarity
```

**Data fields:**
- `evidence.scraped_pages` — list[{url, word_count}]
- `evidence.signal_counts_by_type` — dict[type, count]
- `evidence.signals` — full signal list
- `evidence.victory_matches` — list with win_id, tier, similarity_score

---

### Section 9: Footer / Traceability

Always visible at the bottom of the report. Not a primary reading surface — a trust signal.

```
Generated by Tenex AI Discovery Platform v1.x
Run ID: a1b2c3d4 | 2026-03-16 14:22 UTC | 47.3 seconds | $0.011

Model: gemini-2.5-pro (consultant) + gemini-2.5-flash (report writer)
Prompt version: consultant-1.2, report_writer-1.1
RAG results used: 3 of 10 retrieved
Input tokens: 4,847 | Output tokens: 2,103

This analysis is a machine-generated starting point for a Tenex engagement.
All ROI estimates should be validated against client-specific operational data
before being presented as commitments.
```

**Data fields (from `run_metadata`):**
- `run_id`, `analysis_date`, `elapsed_seconds`, `cost_usd`
- `model`, `prompt_version`, `input_tokens`, `output_tokens`
- `rag_results_used`, `scrape_sources`

---

## Part 2: UI Experience Design — Every Screen, Every Interaction

### Screen 1: Input

**Path:** `/`  
**Neomorphic treatment:** neo-raised container, neo-inset URL field

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│          AI Transformation Discovery                                │
│          Tenex — Powered by AI                                      │
│                                                                     │
│   Enter any company URL                                             │
│   ╔═══════════════════════════════════════════════════════════╗    │
│   ║  https://company.com                                       ║    │
│   ╚═══════════════════════════════════════════════════════════╝    │
│                                                                     │
│   [Optional] Focus area:  [ All ▾ ]  Industry override: [ Auto ▾ ] │
│                                                                     │
│   Mode:  ○ Quick (30s — fewer signals)                              │
│          ● Deep  (90s — full analysis)  ← default                  │
│                                                                     │
│   ┌────────────────────────────────────┐                           │
│   │   Analyze this company  →          │   ← neo-raised button     │
│   └────────────────────────────────────┘                           │
│                                                                     │
│   "A $50K consulting engagement for 4 cents in 90 seconds"         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Input validation:**
- URL must begin with http:// or https://
- Inline validation on blur — green check or red message
- "Analyze" button disabled until URL is valid
- On submit: button text changes to "Analyzing..." and disables

**Fields:**
- `url` — required, validated URL string
- `focus_area` — optional: "All" | "Operations" | "Finance" | "Product" | "Customer"
- `industry_override` — optional: auto-detect or manual selection
- `mode` — "quick" | "deep" (default: "deep")

---

### Screen 2: Loading / Progress

**Path:** `/loading` or inline transition  
**Strategy:** Server-Sent Events (SSE) stream from `/analyze/stream` endpoint  
**Requirement:** User sees real-time progress — not a spinner for 90 seconds

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   Analyzing ACME Logistics Corp                                     │
│   https://acme-logistics.com                                        │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ ████████████████████████████░░░░░░░░░░░░  62%               │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   ✓  Observing...     Scraped 4 pages, extracted 1,247 words        │
│   ✓  Extracting...    Found 18 signals across 6 categories          │
│   ►  Assessing...     Scoring maturity dimensions...                │
│   ○  Matching...      (pending)                                     │
│   ○  Recommending...  (pending)                                     │
│   ○  Writing...       (pending)                                     │
│                                                                     │
│   Estimated time remaining: ~35 seconds                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Step names map to pipeline stages:**

| Step label | Pipeline stage | When it completes |
|---|---|---|
| Observing | ScraperAgent | company_data populated |
| Extracting | SignalExtractionAgent | signals populated |
| Assessing | MaturityScoringAgent | maturity populated |
| Matching | VictoryMatchingAgent | victory_matches populated |
| Recommending | ConsultantAgent | use_cases populated |
| Writing | ReportWriterAgent | report populated |

**SSE event format from backend:**
```json
{ "event": "stage_complete", "stage": "signal_extraction",
  "detail": "Found 18 signals across 6 categories", "progress_pct": 45 }
```

**Error state during loading:**
```
✗  Observing...   Could not reach acme-logistics.com (Cloudflare block)

Sorry, we couldn't analyze this website.
The site may be bot-protected. Try a different URL or
paste the company's LinkedIn About URL instead.

[  Try again  ]
```

---

### Screen 3: Report

**Path:** `/report/:run_id`  
**Layout:** Sticky header + scrollable sections + collapsible evidence panels

```
┌────────────── STICKY HEADER ─────────────────────────────────────────┐
│  ACME Logistics Corp    [Logistics]    Developing  2.5 / 5.0         │
│  ──────────────────────────────────────────────────────────────────  │
│  Executive  │  Maturity  │  Proven  │  Achievable  │  Frontier  │ ROI │
└──────────────────────────────────────────────────────────────────────┘

[scrollable body below]

Section 1: Executive Summary
─────────────────────────────────
[4–5 sentence block as designed above]

Section 2: AI Maturity Assessment
─────────────────────────────────
[Radar chart + 4 dimension blocks]
[12 signals found]  [Show all signals ▾]

Section 3: Proven Solutions                    ← GREEN left border
─────────────────────────────────
[Card 1]  [Card 2]

Section 4: Achievable Opportunities            ← AMBER left border
─────────────────────────────────
[Card 1]

Section 5: Frontier Experiments                ← BLUE left border
─────────────────────────────────
[Card 1]

Section 6: ROI Analysis
─────────────────────────────────
[Summary table]
[Show math for Shipment Delay ▾]

Section 7: Implementation Roadmap
─────────────────────────────────
[3-phase visual timeline]

Section 8: Evidence & Sources
─────────────────────────────────
[Collapsible signal inventory]
[Victory match details]

Footer: traceability bar
```

**Visual design principles (neomorphic base):**
- Background: `--neo-bg: #e0e5ec`
- Cards: `--neo-raised` shadow treatment
- Active section in sticky nav: `--neo-inset` pressed state
- Tier colour accents: green `#2d6a4f`, amber `#d4842a`, blue `#1a5276`
- Confidence bars: thin horizontal fill, colour matches tier

---

### Screen 4: Actions Panel

Visible on the report screen as a persistent side panel or bottom bar.

```
┌───────────────────────────────────────────────────────┐
│  Actions                                              │
│  ─────────────────────────────────────────────────── │
│  [ Export as PDF           ]  ← generates PDF        │
│  [ Copy as Markdown        ]  ← clipboard copy       │
│  [ Share link              ]  ← permalink to report  │
│  [ Ask a follow-up...      ]  ← inline chat input    │
│  [ Re-analyze with focus ▾ ]  ← back to input screen │
└───────────────────────────────────────────────────────┘
```

**Follow-up chat:**
- Simple text input: "What would Phase 1 cost if we already have a data engineer?"
- Sends to `/chat` endpoint with `run_id` + `question` + full report as context
- Response rendered inline below the question
- Not a full chat history — single follow-up per report (Sprint 7 scope)

**Share link:**
- Generates a permalink: `/report/a1b2c3d4`
- Report is stored by `run_id` in backend (backend stores `PipelineState` to disk or DB)
- Link is shareable — no auth required (ADR-002 no auth for MVP)

---

## Part 3: Sprint Roadmap — Broad Objectives

### Context: Where We Are Now

- Sprint 0–3: Pipeline infrastructure, dry-run mode, victory citation system
- The rational strategist agent architecture (Sprint 4 plan) is designed
- Frontend: zero components built
- The pipeline runs but nothing is visible to Sai in a browser

---

### Sprint 4: The Rational Pipeline

**North star:** The system thinks like an AI strategist, not a prompt-wrapped search engine.

**Backend objectives:**
- Implement 4-step rational agent sequence: Signal Extraction → Maturity Scoring →
  Victory Matching → Use Case Recommendation
- Each step is a separate agent with a typed input/output contract
- Traceability: every use case traces to a signal ID and a victory match
- Three-tier classification (PROVEN / ACHIEVABLE / FRONTIER) in pipeline output
- PipelineState carries `signals`, `maturity`, `victory_matches`, `tiered_use_cases`

**Backend visible deliverable:**
- `python orchestrator/pipeline.py --dry-run --url https://stripe.com`
- Outputs JSON with signals list, dimension scores, victory matches with tiers,
  tiered use cases — all fields present, all tracing correct

**Prompt engineering objectives:**
- `prompts/signal_extractor.md` — the Observe step prompt
- `prompts/maturity_scorer.md` — the Assess step prompt
- `prompts/victory_matcher.md` — the Match step prompt
- `prompts/use_case_recommender.md` — the Recommend step prompt

**Eval objectives:**
- Establish Sprint 4 baselines for signal extraction recall and precision
- Eval rubric for tier classification accuracy

**What Sai can test at Sprint 4 end:**
```
python orchestrator/pipeline.py --dry-run --url https://stripe.com
```
Output shows: 15+ signals, 4 dimension scores, 3 victory matches with tiers,
3–5 tiered use cases each citing a signal ID and a victory win ID.

---

### Sprint 5: The Report Experience

**North star:** Sai opens a browser, types a URL, and sees the full designed report.

**Backend objectives:**
- `app.py` — FastAPI entry point with `POST /analyze` and `GET /analyze/stream` (SSE)
- `rag/ingest.py` — seed loading on startup
- `ops/logger.py` — JSONL logging for all agent calls
- Per-stage timeouts enforced in pipeline.py
- Cost tracking: `PipelineState.cost_usd` updated by each agent

**Frontend objectives:**
- Screen 1: URL Input + Analyze button
- Screen 2: Loading with SSE progress — 6 step labels, real-time updates
- Screen 3: Full report render — all 8 sections as designed in Part 1 of this doc
  - Sticky header with company name + maturity score
  - Three-tier cards with correct colour accents (green/amber/blue)
  - Radar chart for dimension scores
  - Collapsible evidence panels per section
- Screen 4: Actions — PDF export, copy markdown, share link

**Eval objectives:**
- Full eval suite running in CI against Sprint 5 pipeline output
- Baselines established: exec_summary, use_cases, roi, roadmap
- `evals/baselines.json` populated with Sprint 5 scores

**What Sai can test at Sprint 5 end:**
```
1. Open http://localhost:3000
2. Type https://stripe.com → click Analyze
3. Watch 6-step progress bar
4. See full report with all sections rendered
5. Click "Show all signals" — see 15+ signals
6. Click "Show math" on an ROI item — see the calculation
```

---

### Sprint 6: Polish and Confidence

**North star:** The report is defensible. Every number has a source. Every claim has evidence.

**Backend objectives:**
- Evidence traceability hardened — every ROI figure links to its basis
- Math transparency data fields populated for all ROI estimates
- Confidence calibration reviewed — is 0.85 too high? Eval-guided tuning
- Error handling polished — all AgentError codes produce human-readable messages
- Performance: end-to-end < 90 seconds on real URLs verified

**Frontend objectives:**
- Math transparency panels (Section 6 ROI "show math" panels)
- Follow-up Q&A chat input (single question per report)
- PDF export working
- Responsive layout — works on 1440px and 1280px wide screens
- Error states polished — clear messages for scrape failures, timeouts

**Eval objectives:**
- 3 prompt iteration cycles guided by eval feedback
- Quality gates in CI: PR blocked if eval score drops from baseline
- ROI credibility rubric: does every number have a stated basis?

**What Sai can test at Sprint 6 end:**
```
1. Run report for stripe.com
2. Every ROI number shows its calculation when clicked
3. Every use case shows the specific evidence from the website
4. Ask a follow-up question — get a sensible answer
5. Export as PDF — looks clean
6. Run for a company with no AI signals — report says "Beginner"
   with appropriate low-confidence use cases
```

---

### Sprint 7: Demo Ready

**North star:** The 2-minute Tenex demo runs flawlessly and looks professional.

**Backend objectives:**
- Focus area context (optional input field affects which use cases surface)
- Share/permalink: reports stored and accessible by run_id
- Load testing: 5 concurrent requests without degradation
- GCP Cloud Run deployment configured and tested

**Frontend objectives:**
- Tenex branding finalized: logo, colour palette, typography locked
- Share link UI: copy-to-clipboard, success toast
- Focus area selector on input screen
- Industry override selector on input screen
- Final UI polish pass — spacing, shadows, typography consistent
- Neomorphic design tokens applied consistently throughout

**QA objectives:**
- E2E test suite: input → loading → report for 3 different company URLs
- Regression test against Sprint 5 eval baselines
- Demo rehearsal: time the full flow from URL entry to report
- Accessibility: keyboard navigation for all interactive elements

**Deploy objectives:**
- Cloud Run service live at a real URL (Sai approves deploy ticket)
- Vercel frontend deployed and connected to Cloud Run backend
- Demo URL ready for Tenex submission

**What Sai can test at Sprint 7 end:**
```
1. Open the live URL (not localhost)
2. Enter acme-logistics.com → click Analyze
3. Watch progress → full report in < 90 seconds
4. Share the link — open in a new incognito window — report loads
5. The whole demo is rehearsable in 2 minutes
```

---

## Part 4: The 2-Minute Tenex Demo Script

**Setup:** Laptop open to the live URL. Chrome full-screen. No dev tools visible.

**0:00 — The hook**
> "Traditional AI transformation diagnostics take a consultant 3–6 weeks and cost
> $50,000 to $200,000. We automated the discovery phase. Let me show you."

**0:15 — Input**
> Type `acme-logistics.com` into the URL field. Click Analyze.
> "We scraped their website — about page, careers, product pages."

**0:30 — Loading**
> Progress bar moves. Step labels update in real-time.
> "The system is doing what a consultant would spend a week doing —
> reading their technology signals, scoring their maturity against
> a framework, and matching them to our delivery wins."

**1:00 — Report appears**
> Scroll to maturity score. Radar chart visible.
> "They're Developing — 2.5 out of 5. Here's what that means:
> strong data infrastructure, no production ML yet."

**1:20 — Use cases**
> Point to the green Proven card.
> "The top recommendation: shipment delay prediction. We've done this
> for three comparable carriers. This one specifically — 18% fewer
> late deliveries, $2.1M annual saving, 10 weeks to production."
> Click "Show Evidence". Signal list expands.
> "That recommendation isn't made up. It's grounded in their job
> posting for a senior data engineer mentioning 50 million daily
> shipment events."

**1:45 — The close**
> Click ROI section. Show the table.
> "Total portfolio value: $5 to $8 million annually.
> This report cost 4 cents and took 47 seconds.
> Imagine a Tenex consultant walking into a discovery meeting
> with this already in hand. Day one is strategy, not discovery."

**2:00**

---

## Appendix: Complete API Response Schema (Sprint 5 target)

This is what `POST /analyze` returns when the full end-goal pipeline is complete.
Frontend TypeScript types must be generated from this schema.

```json
{
  "run_id": "a1b2c3d4",
  "status": "complete",
  "elapsed_seconds": 47.3,
  "cost_usd": 0.011,
  "company": {
    "name": "ACME Logistics Corp",
    "url": "https://acme-logistics.com",
    "logo_url": "https://acme-logistics.com/favicon.png",
    "industry": "logistics",
    "size_label": "mid-market",
    "analysis_date": "2026-03-16"
  },
  "signals": [
    { "id": "sig-001", "type": "tech_stack", "value": "Snowflake", "source": "about_text" },
    { "id": "sig-002", "type": "data_signals", "value": "50M daily shipment events", "source": "job_posting" }
  ],
  "maturity": {
    "composite_score": 2.5,
    "composite_label": "Developing",
    "composite_rationale": "Strong data infrastructure with Snowflake and Airflow...",
    "dimensions": {
      "data_infrastructure": { "score": 3.0, "signals_used": ["sig-001", "sig-002"], "rationale": "..." },
      "ml_ai_capability": { "score": 1.5, "signals_used": ["sig-008"], "rationale": "..." },
      "strategy_intent": { "score": 2.5, "signals_used": ["sig-012"], "rationale": "..." },
      "operational_readiness": { "score": 2.5, "signals_used": ["sig-005"], "rationale": "..." }
    }
  },
  "victory_matches": [
    {
      "win_id": "win-003",
      "engagement_title": "Shipment Delay Prediction for Regional LTL Carrier",
      "match_tier": "DIRECT_MATCH",
      "relevance_note": "Same industry, same size tier, similar maturity at engagement",
      "roi_benchmark": "18% reduction in late deliveries, $2.1M annual saving",
      "similarity_score": 0.82,
      "confidence": 0.80
    }
  ],
  "use_cases": [
    {
      "id": "uc-001",
      "title": "Shipment Delay Prediction",
      "tier": "PROVEN",
      "description": "Predict which shipments will be delayed 24–48 hours in advance...",
      "why_this_company": "Job posting sig-002 references 50M daily events — this trains the model",
      "evidence_signal_ids": ["sig-001", "sig-002"],
      "victory_citation": {
        "win_id": "win-003",
        "match_tier": "DIRECT_MATCH",
        "roi_benchmark": "18% reduction in late deliveries, $2.1M annual saving"
      },
      "effort": "Low",
      "impact": "High",
      "roi_estimate": "$1.8M–$2.4M annually",
      "roi_basis": "win-003 benchmark scaled to ACME volume (12% conservative)",
      "confidence": 0.85,
      "implementation_weeks": 10,
      "prerequisites": [],
      "risk_factors": [],
      "data_flow": {
        "data_inputs": [
          "Snowflake shipment history (18 months)",
          "Carrier performance records from TMS",
          "Weather API feed (external)"
        ],
        "model_approach": "Gradient boosted classifier (XGBoost) trained on historical delay labels; features: carrier, route, weather, seasonality",
        "output_consumer": "Operations team via existing dashboard — delay risk score per shipment 24–48 hrs ahead",
        "feedback_loop": "Actual delivery outcomes logged to feature store weekly; model retrained monthly on rolling 6-month window",
        "value_measurement": "Late delivery rate tracked monthly vs prior-year baseline; minimum 8% improvement threshold"
      }
    },
    {
      "id": "uc-002",
      "title": "Carrier Performance Scoring",
      "tier": "ACHIEVABLE",
      "description": "...",
      "calibration_note": "Based on win-001 enterprise benchmark, adjusted 60–70% for mid-market scale",
      "prerequisites": [
        { "item": "Snowflake data warehouse", "status": "exists" },
        { "item": "Carrier API integration", "status": "needed" }
      ],
      "risk_factors": ["Carrier data quality varies — plan 2–3 weeks data cleaning"],
      "effort": "Medium",
      "impact": "High",
      "roi_estimate": "$600K–$900K annually",
      "confidence": 0.65,
      "implementation_weeks": 18,
      "data_flow": {
        "data_inputs": [
          "Snowflake historical shipment records (exists)",
          "Carrier rate cards from procurement system (exists)",
          "Real-time carrier API feed (needed — integration required)"
        ],
        "model_approach": "XGBoost regression scoring carriers by predicted on-time rate, cost, and reliability; adapted from win-001 tech_stack.ml_approach with scale calibration",
        "output_consumer": "Procurement manager via TMS carrier selection screen at point of shipment booking",
        "feedback_loop": "Actual vs predicted on-time rate logged per carrier; model recalibrated quarterly on new performance data",
        "value_measurement": "Per-shipment carrier cost reduction measured monthly vs prior year; target > 8% improvement"
      }
    },
    {
      "id": "uc-003",
      "title": "Dynamic Route Optimisation at Scale",
      "tier": "FRONTIER",
      "uncertainty_note": "CALIBRATION_MATCH only — comparable company was 3x larger",
      "strategic_upside": "50M daily events is unusually dense for this size tier — potential competitive asymmetry",
      "effort": "High",
      "impact": "High",
      "roi_estimate": "$3.0M–$5.0M annually",
      "confidence": 0.50,
      "implementation_weeks": 36,
      "data_flow": {
        "data_inputs": [
          "TMS shipment history (exists)",
          "GPS telemetry stream (needed — new infrastructure investment)",
          "Live traffic API (needed — external integration)",
          "Carrier rate cards (exists)"
        ],
        "model_approach": "Multi-objective optimizer or RL agent scoring route options by cost, transit time, and reliability; proposed based on ADJACENT_MATCH win-007 tech_stack pattern",
        "output_consumer": "Dispatcher via planning interface — ranked route suggestions; also available as API for TMS auto-booking (proposed)",
        "feedback_loop": "Actual delivery time and fuel cost logged per route; model retrained weekly on rolling 3-month window once GPS telemetry is live",
        "value_measurement": "Fuel cost per route vs prior-year baseline; hypothesis: > 10% reduction over 12 months — to be validated in pilot"
      }
    }
  ],
  "roi_analysis": {
    "use_cases": [
      {
        "use_case_id": "uc-001",
        "annual_impact_low": 1800000,
        "annual_impact_high": 2400000,
        "impl_cost_low": 180000,
        "impl_cost_high": 240000,
        "payback_months_low": 5,
        "payback_months_high": 8,
        "math_narrative": "Volume basis: 50M daily events → ~1.5M shipments/month. Benchmark win-003: 18% late delivery reduction. Conservative: 12%. Late rate 8% → 120K late/month. 12% improvement → 14,400 fewer/month. $12 avg cost → $2.07M/yr.",
        "basis": "win-003 benchmark, scaled conservative for ACME size"
      }
    ],
    "portfolio_annual_low": 5400000,
    "portfolio_annual_high": 8300000,
    "portfolio_cost_low": 700000,
    "portfolio_cost_high": 1020000,
    "portfolio_payback_low": 8,
    "portfolio_payback_high": 12,
    "conservative_note": "All estimates use lower bounds of benchmarks. Validated against ACME operational data before client presentation."
  },
  "roadmap": {
    "phases": [
      {
        "phase_name": "Foundation",
        "duration": "0–90 days",
        "objective": "Prove ML pipeline end-to-end with one low-risk model",
        "what_gets_built": "Carrier performance scoring model",
        "who_builds_it": "1 ML Engineer (contract or hire)",
        "proof_of_success": "Carrier score predicts delay within ±2 days in backtest",
        "dependency": null,
        "primary_use_case_id": "uc-002"
      },
      {
        "phase_name": "Core",
        "duration": "3–6 months",
        "objective": "Deliver primary proven solution at production quality",
        "what_gets_built": "Shipment delay prediction model in production",
        "who_builds_it": "ML Eng + Data Eng (existing team + 1)",
        "proof_of_success": "Late delivery rate drops >10% within 60 days of deployment",
        "dependency": "Phase 1 model deployed and monitoring in place",
        "primary_use_case_id": "uc-001"
      },
      {
        "phase_name": "Scale",
        "duration": "6–12 months",
        "objective": "Expand ML investment to frontier candidate",
        "what_gets_built": "Dynamic route optimisation pilot",
        "who_builds_it": "Dedicated ML team (3 engineers)",
        "proof_of_success": "Fuel cost per route reduces >8% vs pre-ML baseline",
        "dependency": "Phase 2 in production with clean signal",
        "primary_use_case_id": "uc-003"
      }
    ]
  },
  "evidence": {
    "scraped_pages": [
      { "url": "https://acme-logistics.com/about", "word_count": 1247 },
      { "url": "https://acme-logistics.com/careers", "word_count": 3412 }
    ],
    "signal_counts_by_type": {
      "tech_stack": 5, "data_signals": 4, "ml_signals": 2,
      "intent_signals": 3, "ops_signals": 2, "industry_hint": 1, "scale_hint": 1
    }
  },
  "report_sections": {
    "exec_summary": "ACME Logistics Corp scores 2.5 out of 5...",
    "current_state": "ACME operates a mature data engineering stack...",
    "use_cases": "Structured use case section text...",
    "roi_analysis": "ROI section text with calculations shown...",
    "roadmap": "Three-phase roadmap text..."
  },
  "run_metadata": {
    "prompt_version": "1.2",
    "model": "gemini-2.5-pro",
    "input_tokens": 4847,
    "output_tokens": 2103,
    "pipeline_cost_usd": 0.011,
    "rag_results_used": 3,
    "scrape_sources": [
      "https://acme-logistics.com/about",
      "https://acme-logistics.com/careers"
    ]
  }
}
```

---

## Summary: What Each Sprint Delivers Toward This End Goal

| Sprint | What gets built | What Sai can see |
|---|---|---|
| Sprint 4 | Rational 4-step pipeline, signals, tiers, traceability | `--dry-run` JSON with signals + tiered use cases |
| Sprint 5 | Full frontend + API layer + SSE progress | Browser: URL → loading → full report |
| Sprint 6 | Math transparency, follow-up Q&A, eval quality gates | Every ROI shows its math, PDF export works |
| Sprint 7 | Live deploy, share links, Tenex branding | Demo URL running, shareable report links |

The end goal is the report designed in Part 1. Every sprint delivers a slice of it.
Sprint 5 is the first time it is visible in a browser. Sprint 7 is the first time
it is live and shareable. The 2-minute demo script in Part 4 is the finish line.
