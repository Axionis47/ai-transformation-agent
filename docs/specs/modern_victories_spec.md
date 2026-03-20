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

## win-022 — Agentic Customer Support (Retail/Ecommerce)

```json
{
  "id": "win-022",
  "engagement_title": "Agentic Customer Support System for Direct-to-Consumer Retailer",
  "industry": "retail",
  "sector_tags": [
    "dtc_ecommerce",
    "customer_support",
    "conversational_ai"
  ],
  "company_profile": {
    "size_employees": 185,
    "size_label": "startup",
    "annual_revenue_usd": "$28M-$38M",
    "geography": "US (nationally distributed)",
    "business_model": "Direct-to-consumer home goods retailer operating primarily online; ~120,000 orders per year with seasonal peaks at 3x baseline volume"
  },
  "problem_statement": "The support team of 12 agents handled 1,800 tickets per week during peak season, with 67% of volume concentrated in four inquiry types: order status, return initiation, product compatibility questions, and shipping address changes. Average first-response time had slipped to 11 hours during peak periods, and CSAT had dropped from 4.2 to 3.6 over the prior two holiday seasons. Hiring seasonal agents was expensive and took 3 weeks of training time the team could not absorb.",
  "solution_summary": "Tenex built a multi-step support agent using GPT-4o with tool use to handle the four high-volume inquiry types end to end. The agent queried the order management system for real-time status, initiated return requests via the 3PL API, checked product compatibility from a structured spec database, and updated shipping addresses within the order window. A confidence-based escalation layer handed off to human agents when the agent detected ambiguity, policy edge cases, or customer frustration signals in the conversation.",
  "results": {
    "primary_metric": {
      "label": "Support tickets handled without human intervention",
      "value": "58% fully resolved by agent",
      "baseline": "0% automation — all tickets handled by human agents",
      "outcome": "1,044 of 1,800 weekly peak tickets resolved without agent involvement"
    },
    "secondary_metrics": [
      {
        "label": "First-response time",
        "value": "Reduced from 11 hours to under 2 minutes for agent-handled tickets"
      },
      {
        "label": "CSAT score",
        "value": "Recovered from 3.6 to 4.1 within first holiday season post-deployment"
      },
      {
        "label": "Human agent capacity freed",
        "value": "Human agents redirected to complex cases; handled ticket volume grew 22% without new hires"
      }
    ],
    "measurement_period": "First full peak season post-deployment (8 weeks)",
    "measurement_basis": "Ticket resolution data from Zendesk; CSAT from post-resolution survey; escalation rate tracked in agent audit log"
  },
  "engagement_details": {
    "duration_months": 3,
    "tenex_team_size": 2,
    "tenex_roles": [
      "AI Engineer",
      "Engagement Lead"
    ],
    "client_team_involvement": "Head of support as primary stakeholder, 1 backend engineer for OMS and 3PL API access, 2 senior support agents for edge case review during testing",
    "delivery_model": "project"
  },
  "tech_stack": {
    "data_sources": [
      "Order management system (real-time API)",
      "3PL returns API",
      "Product compatibility database (structured JSON)",
      "Zendesk ticket history (for escalation pattern training)"
    ],
    "ml_approach": "GPT-4o with function calling for tool use; LangChain agent framework for multi-step orchestration; conversation memory via sliding window context; rule-based escalation layer for policy edge cases",
    "infrastructure": [
      "AWS Lambda for agent runtime",
      "Redis for conversation session state",
      "Zendesk API for ticket management",
      "CloudWatch for agent audit logging"
    ],
    "client_systems_integrated": [
      "Shopify order management API",
      "ShipBob 3PL returns API",
      "Zendesk Support"
    ]
  },
  "maturity_at_engagement": "Beginner",
  "follow_on_engagement": false,
  "lessons_learned": "Escalation criteria need to be tuned conservatively at launch — it is better to over-escalate for the first 4 weeks and tighten thresholds gradually than to under-escalate and lose customer trust on visible failures. Track escalation reasons as a first-class metric.",
  "embed_text": "Retail / DTC Ecommerce — Startup direct-to-consumer home goods retailer, 185 employees, ~$33M revenue, US national\n\nProblem: 12-person support team handled 1,800 tickets per week at peak, 67% concentrated in four inquiry types. First-response time slipped to 11 hours during peak. CSAT dropped from 4.2 to 3.6 over two holiday seasons. Seasonal hiring took 3 weeks of training time the team could not absorb.\n\nSolution: Tenex built a multi-step support agent using GPT-4o with tool use to handle order status, returns, product compatibility, and address changes end to end. Confidence-based escalation layer hands off to human agents on ambiguity, policy edge cases, or frustration signals.\n\nApproach: GPT-4o with function calling, LangChain orchestration, Redis session state, Shopify and ShipBob API integration\n\nResults: 58% of peak tickets fully resolved without human intervention. First-response time: 11 hours to under 2 minutes. CSAT: 3.6 to 4.1 in first peak season post-deployment.",
  "industry_benchmark": "58% automation rate on inbound support volume during peak season for four high-volume inquiry types",
  "success_threshold": "Most applicable when 50%+ of support volume concentrates in 3-5 repeatable inquiry types and order management and fulfillment APIs are accessible for real-time data retrieval.",
  "gap_analysis_template": "Maturity gap of {gap} points from engagement baseline — agentic support ROI is highest when ticket volume exceeds 500 per week and the top inquiry types are clearly defined and API-accessible.",
  "status": "active",
  "ingestion_date": "2026-03-19",
  "applicable_signals": [],
  "solution_category": "agentic_system"
}
```

---

## win-023 — RAG Knowledge Base (Professional Services)

```json
{
  "id": "win-023",
  "engagement_title": "Internal Knowledge Retrieval System for Management Consultancy",
  "industry": "professional_services",
  "sector_tags": [
    "management_consulting",
    "knowledge_management",
    "internal_tooling"
  ],
  "company_profile": {
    "size_employees": 310,
    "size_label": "mid-market",
    "annual_revenue_usd": "$65M-$85M",
    "geography": "US (offices in New York, Chicago, San Francisco)",
    "business_model": "Independent management consultancy specialising in operational transformation for mid-market industrials and healthcare systems; 140 billable consultants across 3 offices"
  },
  "problem_statement": "Consultants spent an estimated 6-8 hours per week searching for prior engagement deliverables — slide decks, process maps, benchmarking studies, and client-facing models — stored across SharePoint, email, and personal drives with no consistent taxonomy. Senior consultants fielded repeated questions from junior staff that could have been answered by existing internal knowledge, and new hire ramp time to self-sufficient was averaging 5 months. The firm estimated 15-20% of billable work was being redone from scratch when prior deliverables existed.",
  "solution_summary": "Tenex built a RAG-based knowledge retrieval system indexing 4,200 prior engagement documents — presentations, models, benchmarking studies, and process frameworks. Documents were chunked and embedded using text-embedding-3-large, stored in Pinecone, and retrieved via a LangChain retrieval pipeline. A GPT-4o generation layer synthesised answers with citations back to source documents. The system was deployed as a Slack slash command and an internal web app, so consultants could query in natural language and receive sourced answers with links to original files.",
  "results": {
    "primary_metric": {
      "label": "Time spent searching for prior work",
      "value": "71% reduction",
      "baseline": "6-8 hours per consultant per week on internal knowledge search and retrieval",
      "outcome": "1.8-2.3 hours per consultant per week — measured via time-tracking survey"
    },
    "secondary_metrics": [
      {
        "label": "New hire ramp time to self-sufficient",
        "value": "Reduced from 5 months to 3.1 months average across first 2 new hire cohorts post-deployment"
      },
      {
        "label": "Duplicate work estimated reduction",
        "value": "Estimated 60% reduction in from-scratch rework based on document retrieval audit"
      },
      {
        "label": "System adoption",
        "value": "81% of consultants active weekly users at 90-day mark"
      }
    ],
    "measurement_period": "4 months post-deployment",
    "measurement_basis": "Time-tracking survey (consultant self-report, n=98); new hire ramp measured by manager assessment at 90 and 180 days; adoption from system access logs"
  },
  "engagement_details": {
    "duration_months": 4,
    "tenex_team_size": 3,
    "tenex_roles": [
      "AI Engineer",
      "Data Engineer",
      "Engagement Lead"
    ],
    "client_team_involvement": "1 knowledge management director as primary stakeholder, 1 IT administrator for SharePoint access, 3 senior consultants as subject matter experts for retrieval quality evaluation",
    "delivery_model": "project"
  },
  "tech_stack": {
    "data_sources": [
      "SharePoint document library (4,200 documents)",
      "Email attachment archive (selective — partner-approved only)",
      "Internal project database for engagement metadata"
    ],
    "ml_approach": "OpenAI text-embedding-3-large for chunked document embedding; Pinecone vector store for retrieval; LangChain retrieval pipeline with hybrid search (dense + BM25); GPT-4o for answer synthesis with citation tracking",
    "infrastructure": [
      "Pinecone serverless index",
      "AWS Lambda for retrieval API",
      "Slack API for slash command integration",
      "Vercel for internal web app hosting"
    ],
    "client_systems_integrated": [
      "Microsoft SharePoint",
      "Slack Workspace",
      "Microsoft Entra ID (authentication)"
    ]
  },
  "maturity_at_engagement": "Beginner",
  "follow_on_engagement": true,
  "lessons_learned": "Chunking strategy had more impact on retrieval quality than embedding model choice. Documents with inconsistent formatting required custom chunking logic per document type. Spend week 1 on document profiling before building the ingestion pipeline.",
  "embed_text": "Professional Services / Management Consulting — Mid-market independent consultancy, 310 employees, ~$75M revenue, US (NY, Chicago, SF)\n\nProblem: Consultants spent 6-8 hours per week searching for prior engagement deliverables across SharePoint, email, and personal drives with no consistent taxonomy. New hire ramp to self-sufficient averaged 5 months. Estimated 15-20% of billable work was redone from scratch when prior deliverables existed.\n\nSolution: Tenex built a RAG knowledge retrieval system indexing 4,200 prior engagement documents. Chunks embedded with text-embedding-3-large, stored in Pinecone, retrieved via LangChain hybrid search. GPT-4o synthesises answers with citations to source documents. Deployed as Slack slash command and internal web app.\n\nApproach: RAG pipeline with hybrid search (dense + BM25), OpenAI embeddings, Pinecone, GPT-4o synthesis\n\nResults: Knowledge search time: 71% reduction (6-8 hours to 1.8-2.3 hours per week). New hire ramp: 5 months to 3.1 months. 81% weekly active usage at 90 days.",
  "industry_benchmark": "71% reduction in consultant knowledge search time, recovering 4-6 billable hours per consultant per week",
  "success_threshold": "Most applicable when the firm has at least 1,000 prior engagement documents in accessible storage and consultants are spending 5+ hours per week on internal knowledge search.",
  "gap_analysis_template": "Maturity gap of {gap} points from engagement baseline — RAG knowledge retrieval ROI scales directly with document volume and consultant headcount; breakeven typically occurs within 3 months.",
  "status": "active",
  "ingestion_date": "2026-03-19",
  "applicable_signals": [],
  "solution_category": "rag_pipeline"
}
```

---

## win-024 — AI Workflow Automation (Healthcare)

```json
{
  "id": "win-024",
  "engagement_title": "LLM Clinical Documentation Automation for Ambulatory Surgery Center",
  "industry": "healthcare",
  "sector_tags": [
    "ambulatory_surgery",
    "clinical_documentation",
    "administrative_automation"
  ],
  "company_profile": {
    "size_employees": 220,
    "size_label": "mid-market",
    "annual_revenue_usd": "$45M-$60M",
    "geography": "US Mid-Atlantic",
    "business_model": "Multi-specialty ambulatory surgery center operating 6 operating rooms across 2 locations; 18 surgeons and 40 clinical staff; 8,400 procedures annually"
  },
  "problem_statement": "Clinical staff spent 35-45 minutes per procedure on post-procedure documentation — operative notes, discharge summaries, and insurance prior authorisation letters — most of which was templated content with procedure-specific variable fields. Surgeons were completing documentation after hours to avoid impacting procedure throughput, and documentation turnaround for prior authorisation averaged 3.8 days, delaying scheduled cases and causing 6-8% of bookings to fall through before insurance clearance.",
  "solution_summary": "Tenex built an LLM-powered documentation workflow that pre-populated operative notes, discharge summaries, and prior authorisation letters from structured procedure data pulled from the EHR. Claude claude-3-5-sonnet-20241022 generated draft documents following specialty-specific templates approved by the medical director. Clinical staff reviewed and attested to generated drafts rather than composing from scratch. A compliance guardrail layer blocked generation when required clinical data fields were missing from the EHR record, preventing incomplete submissions.",
  "results": {
    "primary_metric": {
      "label": "Post-procedure documentation time per case",
      "value": "68% reduction",
      "baseline": "35-45 minutes per procedure across 8,400 annual procedures",
      "outcome": "11-15 minutes per procedure — clinical staff reviewing and attesting generated drafts"
    },
    "secondary_metrics": [
      {
        "label": "Prior authorisation turnaround",
        "value": "Reduced from 3.8 days to 1.1 days average"
      },
      {
        "label": "Case fall-through rate before insurance clearance",
        "value": "Reduced from 6.8% to 2.4% of scheduled cases"
      },
      {
        "label": "After-hours documentation by surgeons",
        "value": "Eliminated for 91% of standard procedure types within 60 days of deployment"
      }
    ],
    "measurement_period": "5 months post-deployment",
    "measurement_basis": "EHR audit log timestamps for documentation completion; authorisation turnaround from revenue cycle system; fall-through rate from scheduling system; surgeon after-hours activity from EHR login timestamps"
  },
  "engagement_details": {
    "duration_months": 4,
    "tenex_team_size": 2,
    "tenex_roles": [
      "AI Engineer",
      "Engagement Lead"
    ],
    "client_team_involvement": "Medical director for template approval and compliance sign-off, 1 clinical informatics specialist for EHR API access, 2 surgical coordinators as subject matter experts during testing",
    "delivery_model": "project"
  },
  "tech_stack": {
    "data_sources": [
      "EHR structured procedure data (real-time API)",
      "Approved specialty-specific documentation templates (18 templates across 6 specialties)",
      "Prior authorisation payer requirement database"
    ],
    "ml_approach": "Claude claude-3-5-sonnet-20241022 API for document generation using structured prompting with specialty templates; deterministic compliance guardrail layer checking required field presence before generation; no fine-tuning — prompt-only approach",
    "infrastructure": [
      "HIPAA-compliant AWS environment (VPC, encryption at rest and in transit)",
      "AWS Lambda for generation workflow",
      "Audit logging to CloudTrail for compliance",
      "Internal web app for draft review and attestation"
    ],
    "client_systems_integrated": [
      "ModMed EHR REST API",
      "Revenue cycle management system (read-only for auth status)",
      "Fax API for prior authorisation submission"
    ]
  },
  "maturity_at_engagement": "Developing",
  "follow_on_engagement": true,
  "lessons_learned": "Medical director sign-off on every template before deployment was non-negotiable — clinical staff would not use the tool without it. Build the template approval workflow into week 1, not as an afterthought. HIPAA compliance architecture review added 3 weeks but prevented post-launch issues.",
  "embed_text": "Healthcare — Mid-market ambulatory surgery center, 220 employees, ~$52M revenue, US Mid-Atlantic, 8,400 procedures annually\n\nProblem: Clinical staff spent 35-45 minutes per procedure on post-procedure documentation. Surgeons completed documentation after hours. Prior authorisation turnaround averaged 3.8 days, causing 6.8% of bookings to fall through before insurance clearance.\n\nSolution: Tenex built an LLM documentation workflow using Claude claude-3-5-sonnet-20241022 to pre-populate operative notes, discharge summaries, and prior auth letters from EHR structured data. Clinical staff review and attest to generated drafts. Compliance guardrails block generation when required EHR fields are missing.\n\nApproach: Claude API with structured specialty templates, HIPAA-compliant AWS, ModMed EHR integration, deterministic compliance layer\n\nResults: Documentation time: 68% reduction (35-45 min to 11-15 min per case). Prior auth turnaround: 3.8 days to 1.1 days. Case fall-through rate: 6.8% to 2.4%.",
  "industry_benchmark": "68% reduction in post-procedure documentation time, recovering 20-30 minutes per case across all procedure volume",
  "success_threshold": "Most applicable when clinical documentation follows specialty templates with structured variable fields, EHR API is accessible, and documentation volume exceeds 5,000 procedures annually.",
  "gap_analysis_template": "Maturity gap of {gap} points from engagement baseline — clinical documentation automation ROI is direct when prior authorisation delays are causing case fall-through and documentation is templated and structured.",
  "status": "active",
  "ingestion_date": "2026-03-19",
  "applicable_signals": [],
  "solution_category": "llm_workflow"
}
```

---

## win-025 — Generative Content Pipeline (Ecommerce)

```json
{
  "id": "win-025",
  "engagement_title": "Automated Product Content Generation for Specialty Outdoor Retailer",
  "industry": "ecommerce",
  "sector_tags": [
    "specialty_retail",
    "product_content",
    "generative_ai"
  ],
  "company_profile": {
    "size_employees": 95,
    "size_label": "startup",
    "annual_revenue_usd": "$14M-$20M",
    "geography": "US (nationally distributed; HQ Denver, CO)",
    "business_model": "DTC specialty outdoor and hiking gear retailer; 3,800 active SKUs across apparel, equipment, and footwear; primary sales channel is owned ecommerce site"
  },
  "problem_statement": "The merchandising team of 4 wrote all product descriptions, category page copy, and email campaign content manually. With 3,800 active SKUs and 400-600 new SKUs introduced annually, the team was 6-8 weeks behind on new product listings, which delayed catalog launches and suppressed search ranking for new arrivals. Email campaign copy required 3-4 days of writing time per campaign and limited the team to 2 campaigns per month during peak season.",
  "solution_summary": "Tenex built a generative content pipeline using GPT-4o fine-tuned on 800 hand-curated product descriptions that the merchandising team selected as brand voice exemplars. The pipeline ingested structured product attributes from the PIM system and generated product descriptions, meta descriptions, and email snippet variants in the brand voice. A content moderation layer checked outputs against a brand guidelines ruleset before surfacing to the merchandising team for single-click approval or light editing. A/B test integration automatically routed approved variants through the ecommerce platform's built-in experiment framework.",
  "results": {
    "primary_metric": {
      "label": "New SKU listing time",
      "value": "82% reduction",
      "baseline": "45-60 minutes per SKU for full content package (description, meta, email snippet)",
      "outcome": "8-12 minutes per SKU — merchandiser reviewing and approving generated content"
    },
    "secondary_metrics": [
      {
        "label": "New SKU catalog lag",
        "value": "Reduced from 6-8 week backlog to same-week listing for new arrivals"
      },
      {
        "label": "Email campaign output",
        "value": "Increased from 2 campaigns per month to 6 per month without adding headcount"
      },
      {
        "label": "Organic search ranking for new SKUs",
        "value": "Average position for new arrivals improved from page 4 to page 2 within 60 days (measured by SEMrush)"
      }
    ],
    "measurement_period": "4 months post-deployment",
    "measurement_basis": "PIM system timestamps for listing completion; campaign send data from Klaviyo; SEMrush position tracking for 120 new SKUs launched post-deployment"
  },
  "engagement_details": {
    "duration_months": 3,
    "tenex_team_size": 2,
    "tenex_roles": [
      "AI Engineer",
      "Engagement Lead"
    ],
    "client_team_involvement": "Head of merchandising as primary stakeholder, 2 senior copywriters for brand voice curation and output evaluation, 1 developer for PIM API integration",
    "delivery_model": "project"
  },
  "tech_stack": {
    "data_sources": [
      "PIM system structured product attributes (real-time API)",
      "800 curated brand voice exemplar descriptions",
      "Brand guidelines document (PDF, parsed to ruleset)"
    ],
    "ml_approach": "GPT-4o fine-tuned on 800 brand voice exemplars for description generation; rule-based content moderation layer checking brand guideline compliance; A/B test variant routing via Shopify experiment API",
    "infrastructure": [
      "AWS Lambda for generation pipeline",
      "S3 for content draft storage",
      "Internal review dashboard (Next.js)",
      "Klaviyo API for email variant delivery"
    ],
    "client_systems_integrated": [
      "Akeneo PIM REST API",
      "Shopify storefront (content publishing API)",
      "Klaviyo email platform",
      "SEMrush API for ranking tracking"
    ]
  },
  "maturity_at_engagement": "Beginner",
  "follow_on_engagement": false,
  "lessons_learned": "Fine-tuning on brand voice exemplars was worth the 2-week investment — zero-shot GPT-4o outputs required heavy editing and had low team adoption. The quality bar for the 800 exemplars was the determining factor in output quality. Merchandisers curated the training set themselves over 3 days, which also built ownership of the tool.",
  "embed_text": "Ecommerce / Specialty Retail — Startup specialty outdoor gear retailer, 95 employees, ~$17M revenue, Denver CO, 3,800 active SKUs\n\nProblem: Merchandising team of 4 wrote all product descriptions manually. With 3,800 SKUs and 400-600 new SKUs annually, the team ran 6-8 weeks behind on new listings, delaying catalog launches and suppressing search ranking. Email campaigns limited to 2 per month during peak season.\n\nSolution: Tenex built a generative content pipeline using GPT-4o fine-tuned on 800 brand voice exemplars. Pipeline ingests PIM attributes and generates descriptions, meta descriptions, and email snippets. Content moderation layer checks brand guideline compliance. A/B variants routed through Shopify experiments.\n\nApproach: GPT-4o fine-tuning on brand exemplars, PIM integration, rule-based content moderation, Shopify A/B testing\n\nResults: New SKU listing time: 82% reduction (60 min to 10 min per SKU). Catalog lag eliminated. Email campaigns: 2 to 6 per month. Organic search: page 4 to page 2 for new arrivals.",
  "industry_benchmark": "82% reduction in new SKU content production time, enabling same-week catalog launch for new arrivals at 3,800+ SKU scale",
  "success_threshold": "Most applicable when the catalog exceeds 1,000 SKUs with structured attributes in a PIM system and the merchandising team is running more than 8 weeks behind on content production.",
  "gap_analysis_template": "Maturity gap of {gap} points from engagement baseline — generative content pipeline ROI accelerates with SKU volume; at 1,000+ SKUs the time savings compound across every new product launch.",
  "status": "active",
  "ingestion_date": "2026-03-19",
  "applicable_signals": [],
  "solution_category": "generative_pipeline"
}
```

---
