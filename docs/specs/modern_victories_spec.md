# Modern AI Victory Library Spec

Version: 1.0
Date: 2026-03-19
Owner: PM
Purpose: Spec for 6 new victory entries (win-021 through win-026) covering
modern LLM and agentic AI solutions. Backend agent translates this to JSON
and appends to tests/fixtures/rag_seeds/victories.json.

Do NOT modify victories.json directly from this file. Backend agent owns that.

---

## Schema Notes

These entries follow the same schema as win-001 through win-020.
All field names and types are identical. Refer to victory_data_spec.md
for field definitions and validation rules.

Key differences from existing entries:
- ml_approach references LLM APIs (Claude, GPT-4) and orchestration frameworks
- solution_category uses new values: llm_extraction, agentic_system, rag_pipeline,
  llm_workflow, generative_pipeline, model_orchestration
- applicable_signals: [] (empty, consistent with existing entries)
- status: "active", ingestion_date: "2026-03-19"

---

## win-021 — LLM Document Processing (Insurance)

```json
{
  "id": "win-021",
  "engagement_title": "LLM-Based Claims Document Extraction for Regional Insurer",
  "industry": "insurance",
  "sector_tags": [
    "property_casualty",
    "claims_processing",
    "document_extraction"
  ],
  "company_profile": {
    "size_employees": 430,
    "size_label": "mid-market",
    "annual_revenue_usd": "$120M-$150M",
    "geography": "US Southeast",
    "business_model": "Regional property and casualty insurer writing personal and commercial lines across 8 states; claims handled in-house by 60 adjusters"
  },
  "problem_statement": "Adjusters manually reviewed an average of 14 documents per claim — police reports, contractor estimates, medical summaries, and correspondence — extracting key facts into the claims system by hand. Each document review took 18-25 minutes and introduced transcription errors that caused downstream disputes. The claims backlog had grown 34% year-over-year as policy volume increased without headcount to match.",
  "solution_summary": "Tenex built an LLM-based document extraction pipeline using Claude claude-3-5-sonnet-20241022 to parse unstructured claims documents and output structured JSON matching the claims system schema. The pipeline handled PDF, scanned image (via OCR pre-processing), and Word document inputs. Adjusters reviewed extracted fields in a side-by-side view, correcting errors rather than transcribing from scratch. Extraction confidence scores flagged low-certainty fields for mandatory human review.",
  "results": {
    "primary_metric": {
      "label": "Document review time per claim",
      "value": "73% reduction",
      "baseline": "18-25 minutes per document, 14 documents average per claim",
      "outcome": "5-7 minutes per document — adjusters reviewing and correcting rather than transcribing"
    },
    "secondary_metrics": [
      {
        "label": "Transcription error rate",
        "value": "Reduced from 8.4% of fields to 1.1% of fields (87% reduction)"
      },
      {
        "label": "Claims backlog clearance",
        "value": "Backlog reduced 41% within 90 days of deployment without adding headcount"
      },
      {
        "label": "Adjuster satisfaction",
        "value": "Tool rated useful or very useful by 84% of adjusters at 60-day survey"
      }
    ],
    "measurement_period": "90 days post-deployment",
    "measurement_basis": "Time-tracked by claims system audit log; error rate from manual QA sample of 500 claims pre and post deployment"
  },
  "engagement_details": {
    "duration_months": 3,
    "tenex_team_size": 2,
    "tenex_roles": [
      "AI Engineer",
      "Engagement Lead"
    ],
    "client_team_involvement": "1 senior adjuster as subject matter expert for field validation, 1 IT engineer for claims system API access",
    "delivery_model": "project"
  },
  "tech_stack": {
    "data_sources": [
      "PDF claims documents (scanned and native)",
      "Word and email correspondence",
      "Claims system field schema"
    ],
    "ml_approach": "Claude claude-3-5-sonnet-20241022 API for extraction with structured output (JSON mode); Tesseract OCR pre-processing for scanned documents; confidence scoring via logprob sampling",
    "infrastructure": [
      "AWS Lambda for document ingestion",
      "S3 for document storage",
      "FastAPI service for adjuster review UI backend",
      "AWS RDS for extraction audit log"
    ],
    "client_systems_integrated": [
      "Guidewire ClaimCenter REST API",
      "Document management system (SharePoint)"
    ]
  },
  "maturity_at_engagement": "Beginner",
  "follow_on_engagement": true,
  "lessons_learned": "Confidence thresholds need calibration per document type — a threshold that works for contractor estimates is too aggressive for handwritten police reports. Spend week 2 on per-type calibration before showing adjusters the tool.",
  "embed_text": "Insurance — Mid-market regional property and casualty insurer, 430 employees, ~$135M revenue, US Southeast\n\nProblem: Adjusters manually reviewed 14 documents per claim — police reports, contractor estimates, medical summaries — taking 18-25 minutes per document with an 8.4% transcription error rate. Claims backlog grew 34% year-over-year without headcount to match.\n\nSolution: Tenex built an LLM extraction pipeline using Claude claude-3-5-sonnet-20241022 to parse unstructured claims documents into structured JSON matching the claims system schema. Adjusters review and correct extracted fields rather than transcribing. Confidence scores flag low-certainty fields for mandatory human review.\n\nApproach: LLM API with structured output (JSON mode), OCR pre-processing, confidence scoring, Guidewire ClaimCenter integration\n\nResults: Document review time: 73% reduction (18-25 min to 5-7 min per document). Transcription error rate: 8.4% to 1.1%. Claims backlog: 41% reduction in 90 days without adding headcount.",
  "industry_benchmark": "73% reduction in document review time per claim across 14-document average claim file",
  "success_threshold": "Most applicable when claims volume exceeds 500 per month, adjusters spend more than 30% of time on document review, and a claims system with an accessible API is in place.",
  "gap_analysis_template": "Maturity gap of {gap} points from engagement baseline — LLM document extraction ROI is strongest when claims volume is high and manual transcription errors are causing downstream disputes.",
  "status": "active",
  "ingestion_date": "2026-03-19",
  "applicable_signals": [],
  "solution_category": "llm_extraction"
}
```

---
