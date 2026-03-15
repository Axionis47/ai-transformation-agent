# Victory Data Specification

Version: 1.0
Last updated: 2026-03-15
Owner: PM
ADR: ADR-007

This document defines how Tenex delivery wins are recorded, stored, and retrieved.
The victory store is the competitive moat that makes the system smarter with every engagement.
When a consultant cites a result to a CFO, every number traces back to a verified delivery win.

---

## 1. Victory Data Schema

### Purpose

A victory record serves two distinct purposes that must both be satisfied:

1. **Retrieval** — ChromaDB similarity search must surface the right win for a given prospect.
   This means the embedded text must be rich with industry, problem type, company profile,
   and solution approach signals — not just outcome metrics.

2. **Citation** — The Consultant agent must be able to cite the win credibly in a report
   shown to a CFO. Every metric must be specific, every timeline realistic, every claim
   defensible. Vague records produce vague citations.

### Field Definitions

```
REQUIRED FIELDS — every record must have all of these
─────────────────────────────────────────────────────

id
  Type: string
  Format: "win-NNN" (three-digit zero-padded)
  Example: "win-001"
  Purpose: stable reference for citation in reports and RAG matches

engagement_title
  Type: string
  Format: short descriptive phrase, 5–10 words
  Example: "Route Optimization for Regional LTL Carrier"
  Purpose: human-readable label for the win; appears in Consultant citations

industry
  Type: string (controlled vocabulary)
  Values: logistics | financial_services | healthcare | retail | manufacturing |
          professional_services | insurance | energy | real_estate | construction |
          healthtech | fintech | proptech
  Purpose: primary filter for RAG retrieval — must always be populated

company_profile
  Type: object
  Fields:
    size_employees: integer — headcount at time of engagement
    size_label: "startup" | "mid-market" | "enterprise"
      startup:    < 200 employees
      mid-market: 200–2000 employees
      enterprise: > 2000 employees
    annual_revenue_usd: string — approximate range, e.g. "$50M–$100M"
    geography: string — primary operating region, e.g. "US Midwest", "Southeast Asia"
    business_model: string — one sentence describing what the company does
  Purpose: allows Consultant to match wins to prospects of similar size and business model

problem_statement
  Type: string
  Format: 2–3 sentences. Must describe the state BEFORE Tenex arrived.
    Sentence 1: what the operational problem was
    Sentence 2: what the manual or legacy process looked like
    Sentence 3: what the business consequence was (cost, risk, delay)
  Purpose: embedded for retrieval; cited by Consultant to establish "we've seen this before"

solution_summary
  Type: string
  Format: 2–3 sentences. Must describe what Tenex actually built.
    Sentence 1: what was built (system type, data inputs)
    Sentence 2: key technical approach (model type, pipeline, integrations)
    Sentence 3: how it was deployed and operationalised
  Purpose: embedded for retrieval; gives Consultant the "what we built" narrative

results
  Type: object
  Fields:
    primary_metric: object
      label: string — name of the metric, e.g. "Fuel Cost Reduction"
      value: string — exact figure with unit, e.g. "14%"
      baseline: string — the before state, e.g. "$2.1M annual fuel spend"
      outcome: string — the after state, e.g. "$1.8M annual fuel spend"
    secondary_metrics: array of objects, each with label and value
      Minimum 1 secondary metric. Maximum 4.
    measurement_period: string — how long after go-live was performance measured
      Example: "4 months post-deployment", "12 months post-deployment"
    measurement_basis: string — how the result was measured
      Example: "Compared to same 4-month period in prior year", "A/B test vs control group"
  Purpose: specific numbers that Consultant cites; measurement basis prevents hallucination

engagement_details
  Type: object
  Fields:
    duration_months: integer — calendar months from kickoff to production go-live
    tenex_team_size: integer — number of Tenex people on the engagement
    tenex_roles: array of strings — e.g. ["ML Engineer", "Data Engineer", "Engagement Lead"]
    client_team_involvement: string — what the client team contributed
      Example: "2 client data engineers, 1 product manager embedded"
    delivery_model: "staff_aug" | "project" | "retainer"
  Purpose: Consultant calibrates effort estimates for the prospect based on real engagements

tech_stack
  Type: object
  Fields:
    data_sources: array of strings — inputs used, e.g. ["GPS telemetry", "ERP order data"]
    ml_approach: string — model type / approach, e.g. "XGBoost regression", "fine-tuned BERT"
    infrastructure: array of strings — cloud/infra, e.g. ["GCP Vertex AI", "BigQuery", "Airflow"]
    client_systems_integrated: array of strings — what client systems were touched
  Purpose: helps Consultant assess whether prospect has compatible infrastructure

embed_text
  Type: string
  Format: structured concatenation of key fields — see Section 4 (Embedding Strategy)
  Purpose: THIS is the field that gets embedded. Not the full document.
```

```
OPTIONAL FIELDS — include when available
──────────────────────────────────────────

sector_tags
  Type: array of strings — sub-industry tags for finer-grained retrieval
  Example: ["ltl_freight", "last_mile", "cold_chain"]
  Purpose: improves retrieval precision for specialist prospects

maturity_at_engagement
  Type: string — Beginner | Developing | Emerging | Advanced | Leading
  Purpose: Consultant cites this to show ROI is achievable at the prospect's maturity level

client_quote
  Type: string | null
  Format: a realistic paraphrase (never attributed by name)
  Example: "The system paid for itself in the first quarter."
  Purpose: humanises the citation in the report

follow_on_engagement
  Type: boolean
  Purpose: signals that the client came back — indicates strong outcome

lessons_learned
  Type: string — 1–2 sentences on what made this engagement succeed or what to watch for
  Purpose: internal use only — never surfaces in reports
```

---

## 2. Ingestion Guidelines

### Who records wins and when

A Tenex engagement lead records the win within 30 days of go-live confirmation.
"Go-live" means the solution is in production and serving real business decisions.
Pilots, prototypes, and staging deployments are NOT victories — do not record them.

The results must be measurable at the time of recording. If the measurement period
has not elapsed (e.g., "we need 6 months of data"), do not record yet — create a
calendar reminder to record after the measurement window closes.

### Required vs optional

Required fields must be complete before the record is loaded into the store.
A record missing any required field is rejected at ingest — it does not enter the RAG store.

Optional fields should be populated whenever available. A record with more fields
retrieves better because the embed_text is richer. Sparse records are valid but retrieve less precisely.

### What makes a good victory record

A good record is specific enough that a Tenex consultant who was NOT on the engagement
could cite the result credibly to a CFO. Apply this test before submitting:

  "If I showed this to a CFO at a similar company and said 'we did this for a company
  like yours,' would they find it believable and compelling?"

Characteristics of a good record:
- Metrics are specific: "14% fuel cost reduction" not "significant savings"
- Baseline is stated: "from $2.1M to $1.8M annual spend" not just "14%"
- Timeline is realistic: a 3-month engagement that replaced a 15-year process is suspicious
- The problem description sounds like a real pain point, not a marketing slide
- The solution description explains what was actually built, not just the outcome

Characteristics of a bad record:
- Vague metrics: "improved efficiency," "reduced costs," "better outcomes"
- Missing baseline: "reduced time by 30%" with no starting point
- Generic problem: "the company struggled with data silos" — this applies to everyone
- Timeline mismatch: "2-week engagement produced $5M annual savings"
- Solution is a black box: "we built an AI system" with no description of approach

### Minimum viable record

The minimum that will pass ingest validation:
- All required fields populated
- primary_metric.value is a specific number with a unit
- primary_metric.baseline is stated
- measurement_period is specified
- embed_text is generated (see Section 4)
- duration_months is a realistic integer (2–24)

### Metric specificity rules

Every metric must have a number. No exceptions.

Acceptable metric formats:
  Percentage:   "14% reduction in fuel costs"
  Dollar range: "$180K–$220K annual cost avoidance"
  Time:         "From 14 days to 5 days average processing time"
  Ratio:        "3.2x faster than manual process"
  Count:        "Eliminated 90% of stockout events (from ~140/month to ~14/month)"

Not acceptable:
  "Significant improvement"
  "Better performance"
  "Reduced costs"
  "Improved accuracy"
  "Faster processing" (without a starting point and end point)

If the only metric you have is a vague one, go back to the client and get the number.
If the client will not share the number, do not create the record.

### Common mistakes to avoid

1. Confusing the pilot metric with the production metric.
   A pilot on 100 shipments does not generalize to 100,000 shipments.
   Record the production metric only.

2. Reporting the best-case measurement window.
   If performance was 20% better in month 1 but settled at 14% over 6 months,
   record 14%. The sustained result is the credible result.

3. Including results the client did not confirm.
   Do not calculate ROI from your own assumptions and record it as a client result.
   Only record what the client measured and acknowledged.

4. Overstating Tenex's contribution.
   If the client had 3 engineers working on the project alongside 1 Tenex person,
   record that accurately in client_team_involvement.

5. Recording too soon.
   Measure after the model has been in production long enough to accumulate meaningful data.
   For most models: minimum 90 days. For seasonal businesses: minimum one full cycle.

---

## 3. Embedding Strategy

### The core problem

ChromaDB embeds text and finds similar records by cosine similarity.
The quality of retrieval depends entirely on what text gets embedded.

Two failure modes to avoid:

  Failure A — embedding too little:
  Embedding only the outcome ("14% fuel cost reduction") means the system retrieves
  wins that have similar outcomes, not wins that solved similar problems with similar approaches.
  A CFO asking about route optimization does not want a record about churn prediction
  just because both mention "14% improvement."

  Failure B — embedding too much:
  Embedding the full JSON document adds noise. Field names, IDs, and metadata
  dilute the semantic signal. The model wastes capacity on "duration_months: 6"
  instead of the meaningful content.

### The embed_text field

Each victory record has a dedicated embed_text field that is the ONLY text embedded.
This field is a structured concatenation of the semantically rich fields.

### embed_text construction template

```
[Industry] [Company profile: size, business model]

Problem: [problem_statement — verbatim from the field]

Solution: [solution_summary — verbatim from the field]

Approach: [ml_approach] using [data_sources joined with commas]

Results: [primary_metric.label]: [primary_metric.value] ([measurement_period]).
[Each secondary metric on its own line: label: value]
```

Example constructed embed_text for a logistics win:

```
Logistics — Mid-market regional LTL carrier, ~$80M revenue, 520 employees, US Midwest

Problem: The carrier manually dispatched routes using a combination of driver experience
and a legacy TMS system. Route planners spent 3–4 hours per day on manual adjustments.
Fuel costs had risen 18% year-over-year and route efficiency was deteriorating as the
network grew to 38 delivery hubs.

Solution: Tenex built an ML-based route optimisation engine ingesting GPS telemetry,
delivery time windows, driver shift constraints, and historical traffic patterns.
The model used XGBoost regression trained on 18 months of historical routes.
Deployed as a REST API integrated into the existing TMS, with route suggestions surfaced
to dispatchers in the planning interface.

Approach: XGBoost regression using GPS telemetry, ERP order data, real-time traffic feeds

Results: Fuel Cost Reduction: 14% ($294K annual savings on $2.1M fuel spend) (4 months post-deployment).
On-time delivery rate: improved from 87% to 94%
Dispatcher planning time: reduced from 3.5 hours/day to 45 minutes/day
```

### Why this structure works

The embed_text leads with industry and company profile — the first signals the similarity
search uses to filter candidates. The problem statement uses natural language that matches
how a prospect's scraped content might describe their situation. The solution and approach
add technical specificity that lets the retrieval distinguish between different types of
solutions in the same industry. The results confirm the use case category.

### Metadata fields — filter, do not embed

The following fields go into ChromaDB metadata for filtering but are NOT embedded:

```
id                    — exact match lookup
industry              — filter: retrieve only logistics wins for a logistics prospect
size_label            — filter: match company size tier
maturity_at_engagement — filter: show wins relevant to prospect's current maturity
delivery_model        — filter: match engagement type
duration_months       — range filter: find wins deliverable in prospect's timeframe
```

### Retrieval query construction

When the Consultant agent queries the RAG store, the query text should follow
the same structure as embed_text — not a keyword search:

```
[Industry] [prospect size and business model description]

Problem: [the pain point identified in the prospect's scraped data]

Looking for: similar delivery win with quantified results
```

This query structure aligns with the embed_text structure, maximising cosine similarity
between the query and the right wins.

---

## 4. Simulated Victory Cases

See victories.json for the full 20-record dataset in load-ready JSON format.

Below is a summary of the 20 cases by industry for reference:

| ID      | Industry              | Engagement Title                                        | Primary Metric               |
|---------|-----------------------|---------------------------------------------------------|------------------------------|
| win-001 | Logistics             | Route Optimization for Regional LTL Carrier             | 14% fuel cost reduction      |
| win-002 | Logistics             | Carrier Scoring for B2B Supply Chain SaaS               | 12% per-shipment cost savings |
| win-003 | Logistics             | Shipment Delay Prediction for Cold Chain Distributor    | 63% reduction in late deliveries |
| win-004 | Financial Services    | Fraud Detection for Mid-Market Payment Processor        | 31% more fraud caught        |
| win-005 | Financial Services    | Credit Risk Scoring for Regional Business Lender        | 22% reduction in default rate |
| win-006 | Financial Services    | AML Transaction Monitoring for Community Bank           | 68% reduction in false positives |
| win-007 | Healthcare            | Clinical Triage NLP for Urgent Care Network             | 35% reduction in wait times  |
| win-008 | Healthcare            | Readmission Risk Prediction for Regional Health System  | 19% reduction in 30-day readmissions |
| win-009 | Healthcare            | Prior Authorization Automation for HealthTech Platform  | From 4.2 days to 18 hours avg approval |
| win-010 | Retail                | Demand Forecasting for E-commerce Fulfillment Provider  | 25% reduction in overstaffing costs |
| win-011 | Retail                | Churn Prediction for Mid-Market Specialty Retailer      | 18% churn reduction          |
| win-012 | Manufacturing         | Computer Vision Defect Detection for Auto Parts Maker   | 30% more defects caught      |
| win-013 | Manufacturing         | Predictive Maintenance for Industrial Equipment OEM     | 31% reduction in unplanned downtime |
| win-014 | Professional Services | Contract Review Automation for Mid-Market Law Firm      | 70% reduction in review time |
| win-015 | Professional Services | Resource Scheduling Optimization for IT Consulting Firm | 11% increase in billable utilization |
| win-016 | Insurance             | Claims Processing Automation for P&C Insurer            | From 14 days to 5 days avg processing |
| win-017 | Insurance             | Underwriting Risk Scoring for Commercial Lines Insurer  | 17% improvement in loss ratio |
| win-018 | Energy                | Grid Demand Forecasting for Regional Utility            | 9% reduction in reserve margin costs |
| win-019 | Real Estate           | Lease Renewal Churn Prediction for PropTech Platform    | 24% improvement in retention |
| win-020 | Construction          | Predictive Maintenance for Heavy Equipment Rental Fleet | 28% reduction in unplanned downtime |
