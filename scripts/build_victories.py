"""Generate tests/fixtures/rag_seeds/victories.json with 12 representative victories."""
from __future__ import annotations

import json
from pathlib import Path

OUTPUT = (
    Path(__file__).resolve().parent.parent
    / "tests" / "fixtures" / "rag_seeds" / "victories.json"
)

VICTORIES = [
    {
        "id": "win-001",
        "engagement_title": "Invoice Processing Automation",
        "industry": "financial_services",
        "sector_tags": ["accounts_payable", "invoice_processing", "erp_integration", "document_ai"],
        "company_profile": {
            "size_employees": 320,
            "size_label": "mid-market",
            "annual_revenue_usd": "$50M-$80M",
            "geography": "US Southeast",
            "business_model": "Regional commercial lender processing invoices across 12 business units",
        },
        "problem_statement": (
            "The AP team processed 3,000 invoices per month manually, averaging 15 minutes per invoice "
            "for data entry, PO matching, and exception handling. Invoice errors required an additional "
            "4 hours per incident to resolve, and month-end close was delayed by 3 days due to processing backlog."
        ),
        "solution_summary": (
            "Built an LLM-based extraction pipeline that reads PDF invoices, pulls line items and vendor details "
            "using structured output, matches against open POs in the ERP, and routes exceptions to a human queue. "
            "Straight-through invoices post automatically; exceptions are reviewed in a lightweight web UI."
        ),
        "results": {
            "primary_metric": {
                "label": "Straight-Through Processing Rate",
                "value": "82%",
                "baseline": "0% automated — all 3,000 invoices processed manually each month",
                "outcome": "2,460 invoices per month processed without human touch",
            },
            "secondary_metrics": [
                {"label": "Labor savings", "value": "$340K/year (equivalent to 2.1 FTE)"},
                {"label": "Month-end close", "value": "Reduced from 3-day delay to same-day close"},
                {"label": "Invoice error rate", "value": "Reduced from 4.2% to 0.6%"},
            ],
            "measurement_period": "6 months post-deployment",
            "measurement_basis": "Compared to 6-month pre-deployment baseline from AP system logs",
        },
        "engagement_details": {
            "duration_months": 3,
            "tenex_team_size": 2,
            "tenex_roles": ["AI Engineer", "Engagement Lead"],
            "client_team_involvement": "1 AP manager as domain expert; 1 ERP admin for API access",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["PDF invoices (S3)", "ERP purchase orders (REST API)", "Vendor master data"],
            "ml_approach": "Claude API with structured output for extraction; rule-based PO matching engine",
            "infrastructure": ["AWS Lambda", "S3", "PostgreSQL", "FastAPI review UI"],
            "client_systems_integrated": ["SAP ERP REST API", "AP team email queue"],
        },
        "maturity_at_engagement": "Developing",
        "follow_on_engagement": True,
        "lessons_learned": (
            "PDF quality varies wildly — invest time in pre-processing (deskew, denoise) before LLM extraction. "
            "The PO matching rules needed two rounds of tuning based on AP manager feedback before trust was earned."
        ),
        "embed_text": (
            "Financial Services — Mid-market commercial lender, 320 employees, ~$65M revenue, US Southeast\n\n"
            "Problem: AP team processed 3,000 invoices/month manually at 15 min each. Zero automation. "
            "Month-end close delayed 3 days from processing backlog.\n\n"
            "Solution: LLM extracts invoice line items and vendor details, matches to POs, routes exceptions to human queue. "
            "Straight-through invoices post automatically. Built with Claude API structured output, PDF parsing, ERP REST API.\n\n"
            "Results: 82% straight-through processing rate (from 0%), $340K/year labor savings, "
            "month-end close delay eliminated. 6 months post-deployment."
        ),
        "industry_benchmark": "82% straight-through processing on 3,000 invoices/month",
        "success_threshold": "Applicable when invoice volume exceeds 500/month and an ERP API is accessible.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — AP automation ROI is achievable in 3 months "
            "with structured invoice flow and ERP API access."
        ),
        "applicable_signals": [
            "process_signal", "ops_signal", "pain_point", "tech_stack", "data_signal", "intent_signal"
        ],
        "solution_category": "document_intelligence",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
    {
        "id": "win-002",
        "engagement_title": "Customer Support Agent",
        "industry": "ecommerce",
        "sector_tags": ["customer_support", "ticket_automation", "returns_management", "conversational_ai"],
        "company_profile": {
            "size_employees": 55,
            "size_label": "startup",
            "annual_revenue_usd": "$8M-$15M",
            "geography": "US",
            "business_model": "Direct-to-consumer ecommerce brand selling home goods, 40,000 orders/month",
        },
        "problem_statement": (
            "A 6-person support team handled 400 tickets per day with a 23-minute average resolution time. "
            "35% of tickets were repeat questions about order status, returns, and shipping. "
            "The team worked overtime during sale periods and CSAT had dropped to 3.2 out of 5."
        ),
        "solution_summary": (
            "Built a multi-step support agent using GPT-4o with function calling. "
            "The agent handles returns initiation, order tracking lookups, and FAQ responses autonomously. "
            "Complex or sensitive tickets are escalated to the human team with a full context summary."
        ),
        "results": {
            "primary_metric": {
                "label": "Auto-Resolution Rate",
                "value": "64%",
                "baseline": "0% — all 400 daily tickets handled manually",
                "outcome": "256 tickets/day resolved without human involvement",
            },
            "secondary_metrics": [
                {"label": "Average resolution time", "value": "Reduced from 23 min to 4 min"},
                {"label": "CSAT score", "value": "Improved from 3.2 to 4.1 out of 5"},
                {"label": "Support team overtime", "value": "Eliminated during sale periods"},
            ],
            "measurement_period": "3 months post-deployment",
            "measurement_basis": "Helpdesk system logs compared to 3-month pre-deployment baseline",
        },
        "engagement_details": {
            "duration_months": 3,
            "tenex_team_size": 2,
            "tenex_roles": ["AI Engineer", "Engagement Lead"],
            "client_team_involvement": "Support manager for escalation rule design; 2 agents for testing",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["Order management system (REST API)", "Returns policy docs", "FAQ knowledge base"],
            "ml_approach": "GPT-4o with function calling; LangChain agent framework; Redis for conversation memory",
            "infrastructure": ["AWS ECS", "Redis", "PostgreSQL"],
            "client_systems_integrated": ["Shopify order API", "Zendesk for escalated ticket handoff"],
        },
        "maturity_at_engagement": "Beginner",
        "follow_on_engagement": True,
        "lessons_learned": (
            "Escalation rules are the hardest part — too aggressive and agents resent the bot, "
            "too loose and customers get wrong answers. Budget a full week for escalation tuning with the team."
        ),
        "embed_text": (
            "Ecommerce — Startup DTC brand, 55 employees, ~$12M revenue, US\n\n"
            "Problem: 6-person support team, 400 tickets/day, 23-minute resolution. "
            "35% repeat questions. CSAT 3.2/5.\n\n"
            "Solution: Multi-step support agent using GPT-4o with function calling. "
            "Handles returns, order tracking, FAQ. Escalates complex cases to humans with context summary.\n\n"
            "Results: 64% auto-resolution rate, avg resolution 4 min, CSAT from 3.2 to 4.1. "
            "3 months post-deployment."
        ),
        "industry_benchmark": "64% ticket auto-resolution rate on 400 daily support tickets",
        "success_threshold": "Best fit when order management system has an API and ticket volume exceeds 150/day.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — support automation ROI is strong at this scale in 3 months."
        ),
        "applicable_signals": [
            "process_signal", "pain_point", "ops_signal", "tech_stack", "intent_signal", "scale_hint"
        ],
        "solution_category": "conversational_ai",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
    {
        "id": "win-003",
        "engagement_title": "Consultant Knowledge Base",
        "industry": "professional_services",
        "sector_tags": ["knowledge_management", "internal_search", "document_retrieval", "rag"],
        "company_profile": {
            "size_employees": 280,
            "size_label": "mid-market",
            "annual_revenue_usd": "$40M-$60M",
            "geography": "US Northeast",
            "business_model": "Management consulting firm, 200 billable consultants across 4 practice areas",
        },
        "problem_statement": (
            "Consultants spent 8 hours per week searching for past proposals, case studies, and methodology "
            "documents scattered across SharePoint, email, and network drives. "
            "15,000 documents with no consistent tagging meant 45 minutes average to find a relevant precedent."
        ),
        "solution_summary": (
            "Built a RAG system over 15,000 internal documents using OpenAI embeddings and Pinecone. "
            "Consultants query in natural language and receive cited answers with source links. "
            "Claude generates the synthesis; Pinecone handles retrieval."
        ),
        "results": {
            "primary_metric": {
                "label": "Search Time Per Query",
                "value": "Reduced from 45 min to 3 min",
                "baseline": "45 minutes average to find a relevant document",
                "outcome": "3 minutes average with cited answer and source link",
            },
            "secondary_metrics": [
                {"label": "Answer accuracy", "value": "89% rated accurate by consultants in 30-day survey"},
                {"label": "Productivity gain", "value": "$180K/year from recovered billable hours"},
                {"label": "Documents indexed", "value": "15,000 across SharePoint, email, and network drives"},
            ],
            "measurement_period": "30-day post-deployment survey + usage logs",
            "measurement_basis": "Consultant time logs before vs after; 30-day accuracy survey",
        },
        "engagement_details": {
            "duration_months": 2,
            "tenex_team_size": 2,
            "tenex_roles": ["AI Engineer", "Engagement Lead"],
            "client_team_involvement": "IT admin for SharePoint access; 3 consultants for accuracy testing",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["SharePoint (15,000 docs)", "Email archives", "Network drive PDFs and Word docs"],
            "ml_approach": "OpenAI text-embedding-3-large for embeddings; Claude for answer generation",
            "infrastructure": ["AWS (orchestration)", "Pinecone managed vector store", "React frontend"],
            "client_systems_integrated": ["SharePoint API", "Microsoft SSO for access control"],
        },
        "maturity_at_engagement": "Beginner",
        "follow_on_engagement": True,
        "lessons_learned": (
            "Access control is the hardest constraint — consultants should only see documents "
            "they are authorized to view. Implement metadata-level filtering at the Pinecone query layer "
            "before launch, not after."
        ),
        "embed_text": (
            "Professional Services — Mid-market consulting firm, 280 employees, ~$50M revenue, US Northeast\n\n"
            "Problem: Consultants spent 8 hours/week searching 15,000 documents across SharePoint and email. "
            "45 minutes average per query.\n\n"
            "Solution: RAG system over 15,000 docs using OpenAI embeddings, Pinecone vector store, "
            "Claude for generation. Natural language search with cited answers.\n\n"
            "Results: Search time 45 min to 3 min, 89% accuracy, $180K/year productivity gain. "
            "30-day post-deployment."
        ),
        "industry_benchmark": "Search time from 45 min to 3 min across 15,000 internal documents",
        "success_threshold": "Applicable when document volume exceeds 1,000 and content is in searchable format.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — knowledge retrieval ROI is achievable in 2 months "
            "with accessible document store."
        ),
        "applicable_signals": [
            "process_signal", "pain_point", "tech_stack", "data_signal", "ops_signal", "intent_signal"
        ],
        "solution_category": "knowledge_retrieval",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
    {
        "id": "win-004",
        "engagement_title": "Clinical Note Generation",
        "industry": "healthcare",
        "sector_tags": ["clinical_documentation", "ehr_integration", "note_generation", "compliance"],
        "company_profile": {
            "size_employees": 95,
            "size_label": "mid-market",
            "annual_revenue_usd": "$12M-$20M",
            "geography": "US Midwest",
            "business_model": "Outpatient specialty clinic, 15 clinicians seeing 80 patients per day",
        },
        "problem_statement": (
            "15 clinicians spent a combined 40 hours per week on documentation, completing notes 6 or more "
            "hours after the patient visit. Late notes created compliance risk and delayed billing by 2 days. "
            "Clinician burnout surveys cited documentation as the top frustration."
        ),
        "solution_summary": (
            "Built an LLM pipeline that generates structured SOAP notes from a brief post-visit summary "
            "combined with relevant EHR context fetched via FHIR API. "
            "Clinicians review and approve in under 2 minutes; the note posts to Epic automatically."
        ),
        "results": {
            "primary_metric": {
                "label": "Documentation Time Per Clinician",
                "value": "62% reduction",
                "baseline": "2.7 hours/day per clinician on documentation",
                "outcome": "1.0 hours/day per clinician post-deployment",
            },
            "secondary_metrics": [
                {"label": "Note completion time", "value": "From 6+ hours post-visit to within 1 hour"},
                {"label": "Labor savings", "value": "$109K/year from recovered clinician time"},
                {"label": "Billing delay", "value": "Reduced from 2-day lag to same-day submission"},
            ],
            "measurement_period": "4 months post-deployment",
            "measurement_basis": "EHR timestamp logs for note completion; clinician time survey",
        },
        "engagement_details": {
            "duration_months": 3,
            "tenex_team_size": 2,
            "tenex_roles": ["AI Engineer", "Engagement Lead"],
            "client_team_involvement": "2 clinicians for note quality review; IT for Epic FHIR API access",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["Post-visit summaries (dictation or text)", "Epic EHR via FHIR API"],
            "ml_approach": "Claude API with structured prompting and compliance guardrails; audit trail logging",
            "infrastructure": ["GCP Cloud Run", "BigQuery for audit trail"],
            "client_systems_integrated": ["Epic FHIR R4 API", "Clinic scheduling system"],
        },
        "maturity_at_engagement": "Developing",
        "follow_on_engagement": False,
        "lessons_learned": (
            "HIPAA compliance review adds 3 weeks minimum — start the BAA process with the client in week 1. "
            "Clinicians are skeptical of AI-generated notes until they see their own voice reflected back. "
            "Use their actual note examples as few-shot context."
        ),
        "embed_text": (
            "Healthcare — Mid-market outpatient clinic, 95 employees, ~$16M revenue, US Midwest\n\n"
            "Problem: 15 clinicians spent 40 hours/week on documentation. Notes completed 6+ hours post-visit. "
            "Compliance risk and 2-day billing delay.\n\n"
            "Solution: LLM generates structured SOAP notes from visit summary + Epic EHR context via FHIR API. "
            "Clinician reviews and approves in under 2 minutes. Built with Claude API, Epic FHIR, GCP Cloud Run.\n\n"
            "Results: 62% reduction in documentation time, notes within 1 hour, $109K/year savings. "
            "4 months post-deployment."
        ),
        "industry_benchmark": "62% reduction in clinical documentation time across 15 clinicians",
        "success_threshold": "Applicable when EHR has FHIR API access and clinicians have 1+ hours/day on notes.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — clinical note generation ROI is achievable in 3 months "
            "with FHIR API access and clinician buy-in."
        ),
        "applicable_signals": [
            "process_signal", "pain_point", "ops_signal", "tech_stack", "data_signal", "hiring_signal"
        ],
        "solution_category": "llm_workflow",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
    {
        "id": "win-005",
        "engagement_title": "Product Description Generator",
        "industry": "retail",
        "sector_tags": ["product_content", "ecommerce_content", "sku_automation", "brand_voice"],
        "company_profile": {
            "size_employees": 80,
            "size_label": "startup",
            "annual_revenue_usd": "$15M-$25M",
            "geography": "US West",
            "business_model": "Online retailer with 12,000 active SKUs across home, garden, and outdoor categories",
        },
        "problem_statement": (
            "The product team wrote 15 descriptions per day manually, spending 45 minutes each to maintain "
            "brand voice consistency. With 12,000 SKUs and seasonal refreshes, the backlog was 800 descriptions "
            "deep and growing. New product launches were delayed 3 weeks waiting for content."
        ),
        "solution_summary": (
            "Fine-tuned GPT-4o on 800 approved product descriptions to capture brand voice. "
            "The pipeline accepts a product spec sheet and optional image, generates a draft description, "
            "and scores it against a rule-based brand voice rubric before surfacing to the content team for approval."
        ),
        "results": {
            "primary_metric": {
                "label": "Daily Description Throughput",
                "value": "200 descriptions/day (13x increase)",
                "baseline": "15 descriptions/day — all written manually by product team",
                "outcome": "200 descriptions/day with 91% first-draft acceptance rate",
            },
            "secondary_metrics": [
                {"label": "First-draft acceptance rate", "value": "91%"},
                {"label": "Annual savings", "value": "$95K/year from reduced content writing time"},
                {"label": "Launch delay", "value": "New product content delay from 3 weeks to 2 days"},
            ],
            "measurement_period": "3 months post-deployment",
            "measurement_basis": "Content management system logs; team time surveys",
        },
        "engagement_details": {
            "duration_months": 2,
            "tenex_team_size": 2,
            "tenex_roles": ["AI Engineer", "Engagement Lead"],
            "client_team_involvement": "Content lead for fine-tuning data curation; merchandising team for QA",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["Product spec sheets (CSV/PDF)", "Product images", "800 approved description examples"],
            "ml_approach": "GPT-4o fine-tuned on brand voice examples; rule-based brand voice scorer; A/B pipeline",
            "infrastructure": ["GCP Vertex AI (fine-tuning)", "Cloud Functions", "BigQuery"],
            "client_systems_integrated": ["Product catalog API", "CMS content upload API"],
        },
        "maturity_at_engagement": "Beginner",
        "follow_on_engagement": False,
        "lessons_learned": (
            "Fine-tuning data quality matters more than quantity. "
            "100 high-quality, carefully selected exemplars outperformed 800 inconsistently curated ones. "
            "Spend time with the content lead selecting training data before running the fine-tune."
        ),
        "embed_text": (
            "Retail — Startup online retailer, 80 employees, ~$20M revenue, US West\n\n"
            "Problem: Product team wrote 15 descriptions/day manually at 45 min each. "
            "12,000 SKUs, 800-deep backlog, 3-week launch delays.\n\n"
            "Solution: GPT-4o fine-tuned on 800 brand voice examples. Accepts product spec + image, "
            "generates draft, scores against brand rubric before human approval.\n\n"
            "Results: 200 descriptions/day (13x), 91% first-draft acceptance, $95K/year savings. "
            "3 months post-deployment."
        ),
        "industry_benchmark": "200 descriptions/day at 91% acceptance rate vs 15/day manual baseline",
        "success_threshold": "Best fit when SKU count exceeds 500 and brand voice is well-documented.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — content generation ROI is achievable in 2 months "
            "with curated brand examples."
        ),
        "applicable_signals": [
            "process_signal", "pain_point", "ops_signal", "data_signal", "intent_signal", "scale_hint"
        ],
        "solution_category": "generative_content",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
    {
        "id": "win-006",
        "engagement_title": "Contract Review System",
        "industry": "insurance",
        "sector_tags": ["contract_review", "underwriting", "policy_compliance", "document_extraction"],
        "company_profile": {
            "size_employees": 410,
            "size_label": "mid-market",
            "annual_revenue_usd": "$85M-$120M",
            "geography": "US Midwest",
            "business_model": "Commercial lines insurer, 45 underwriters reviewing 200 policies per month",
        },
        "problem_statement": (
            "Underwriters spent 3 hours per policy reviewing contracts against standard templates to identify "
            "deviations in coverage terms, exclusions, and liability limits. "
            "Manual review missed deviations 12% of the time, creating claim exposure, and the review backlog "
            "grew to 3 weeks during peak renewal season."
        ),
        "solution_summary": (
            "Built a contract review system using Claude to extract key clauses from uploaded policy documents, "
            "compare each clause against the standard template, and flag deviations with severity scoring. "
            "Underwriters see a deviation summary first and drill into full text only for flagged items."
        ),
        "results": {
            "primary_metric": {
                "label": "Contract Review Time",
                "value": "From 3 hours to 25 minutes per policy",
                "baseline": "3 hours per policy, 45 underwriters, 200 policies/month",
                "outcome": "25 minutes per policy — 87% time reduction",
            },
            "secondary_metrics": [
                {"label": "Deviation detection rate", "value": "From 88% to 99.2%"},
                {"label": "Annual underwriter time savings", "value": "$420K/year"},
                {"label": "Renewal backlog", "value": "Eliminated — from 3 weeks to same-week review"},
            ],
            "measurement_period": "5 months post-deployment",
            "measurement_basis": "Underwriter time logs; deviation audit against manual re-review sample",
        },
        "engagement_details": {
            "duration_months": 4,
            "tenex_team_size": 3,
            "tenex_roles": ["AI Engineer", "Document Processing Engineer", "Engagement Lead"],
            "client_team_involvement": "2 senior underwriters for template definition; compliance lead for sign-off",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["Policy documents (PDF)", "Standard contract templates", "Historical deviation log"],
            "ml_approach": "Claude API for clause extraction and comparison; rule-based deviation scoring; Unstructured for parsing",
            "infrastructure": ["AWS Lambda", "S3", "PostgreSQL"],
            "client_systems_integrated": ["Policy management system (REST API)", "Underwriter review portal"],
        },
        "maturity_at_engagement": "Developing",
        "follow_on_engagement": True,
        "lessons_learned": (
            "Template standardization was 40% of the project effort. "
            "The client had 12 variations of their standard template across business lines. "
            "Consolidating to 3 canonical templates unlocked the comparison engine."
        ),
        "embed_text": (
            "Insurance — Mid-market commercial lines insurer, 410 employees, ~$100M revenue, US Midwest\n\n"
            "Problem: Underwriters spent 3 hours per policy on manual contract review. "
            "12% deviation miss rate. 3-week backlog in renewal season.\n\n"
            "Solution: Claude extracts clauses, compares to standard templates, flags deviations with severity. "
            "Underwriters review summary first, drill into flagged items only.\n\n"
            "Results: Review time 3 hours to 25 min, deviation detection 88% to 99.2%, $420K/year savings. "
            "5 months post-deployment."
        ),
        "industry_benchmark": "87% review time reduction, deviation detection from 88% to 99.2%",
        "success_threshold": "Applicable when policy volume exceeds 50/month and standard templates are defined.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — contract review automation ROI is achievable in 4 months "
            "with standardized templates and underwriter involvement."
        ),
        "applicable_signals": [
            "process_signal", "pain_point", "ops_signal", "tech_stack", "data_signal", "intent_signal"
        ],
        "solution_category": "document_intelligence",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
    {
        "id": "win-007",
        "engagement_title": "Demand Forecasting Platform",
        "industry": "logistics",
        "sector_tags": ["demand_forecasting", "warehouse_planning", "inventory_management", "time_series"],
        "company_profile": {
            "size_employees": 490,
            "size_label": "mid-market",
            "annual_revenue_usd": "$75M-$110M",
            "geography": "US Midwest",
            "business_model": "Third-party logistics provider operating 6 fulfillment centers, 1,200 SKUs managed",
        },
        "problem_statement": (
            "Warehouse capacity planning was done in spreadsheets based on prior-year actuals and "
            "dispatcher intuition. Forecast error averaged 22%, causing $180K in annual overstocking costs "
            "and 15% more stockouts than the industry median. Seasonal spikes were routinely underestimated."
        ),
        "solution_summary": (
            "Built a demand forecasting platform combining Prophet for trend and seasonality with "
            "XGBoost for residual correction. External signals including weather data and local event calendars "
            "are ingested daily via Airflow and fed into the ensemble. Forecasts are served via FastAPI "
            "and visualized in a planning dashboard."
        ),
        "results": {
            "primary_metric": {
                "label": "Forecast Error (MAPE)",
                "value": "Reduced from 22% to 9%",
                "baseline": "22% mean absolute percentage error on 90-day demand forecasts",
                "outcome": "9% MAPE — 59% error reduction",
            },
            "secondary_metrics": [
                {"label": "Overstocking cost avoidance", "value": "$180K/year"},
                {"label": "Stockout reduction", "value": "15% reduction from pre-deployment baseline"},
                {"label": "Planning cycle time", "value": "From 2 days to 4 hours per planning cycle"},
            ],
            "measurement_period": "6 months post-deployment",
            "measurement_basis": "Compared to 18-month historical baseline adjusted for volume growth",
        },
        "engagement_details": {
            "duration_months": 3,
            "tenex_team_size": 2,
            "tenex_roles": ["ML Engineer", "Engagement Lead"],
            "client_team_involvement": "1 data engineer for ERP API access; 2 planners as domain experts",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["Historical order data (18 months)", "Weather API", "Local events calendar", "ERP inventory data"],
            "ml_approach": "Prophet for baseline trend; XGBoost for residual correction; ensemble combination",
            "infrastructure": ["GCP Vertex AI (training)", "BigQuery", "Cloud Run (serving)", "Airflow (orchestration)"],
            "client_systems_integrated": ["ERP inventory API", "Planning dashboard (internal)"],
        },
        "maturity_at_engagement": "Developing",
        "follow_on_engagement": True,
        "lessons_learned": (
            "External signals (weather, events) added 4 percentage points of accuracy improvement. "
            "Worth the integration effort. The bigger unlock was getting 18 months of clean historical data "
            "before modeling — data cleaning took 3 weeks but was the difference maker."
        ),
        "embed_text": (
            "Logistics — Mid-market 3PL provider, 490 employees, ~$90M revenue, US Midwest\n\n"
            "Problem: Demand planning in spreadsheets. 22% forecast error. "
            "$180K/year overstocking, 15% more stockouts than industry median.\n\n"
            "Solution: Prophet + XGBoost ensemble with weather and event signals. "
            "Airflow for daily data ingestion. FastAPI serving. Planning dashboard.\n\n"
            "Results: Forecast error 22% to 9%, $180K/year cost avoidance, 15% stockout reduction. "
            "6 months post-deployment."
        ),
        "industry_benchmark": "22% to 9% MAPE on 90-day demand forecasts",
        "success_threshold": "Applicable when 18+ months of order history is available and ERP data is accessible.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — demand forecasting ROI is achievable in 3 months "
            "with clean historical data and ERP API access."
        ),
        "applicable_signals": [
            "data_signal", "process_signal", "ops_signal", "tech_stack", "pain_point", "ml_signal"
        ],
        "solution_category": "prediction_platform",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
    {
        "id": "win-008",
        "engagement_title": "Intelligent Document Routing",
        "industry": "healthcare",
        "sector_tags": ["fax_routing", "document_classification", "ocr", "workflow_automation"],
        "company_profile": {
            "size_employees": 60,
            "size_label": "startup",
            "annual_revenue_usd": "$6M-$10M",
            "geography": "US Southeast",
            "business_model": "Multi-specialty outpatient clinic receiving 500 inbound faxes per day across 8 departments",
        },
        "problem_statement": (
            "The clinic received 500 faxes per day. Two full-time staff manually sorted documents, "
            "identified the patient, and routed to the correct department queue. "
            "Processing took 4 hours from fax receipt to routing, creating delays in care coordination "
            "and requiring overtime 3 days per week."
        ),
        "solution_summary": (
            "Built a document routing pipeline using GPT-4o Vision to classify each fax by document type "
            "(referral, lab result, prior auth, etc.), extract the patient ID via OCR, "
            "and route to the correct department queue via SQS. "
            "Unrecognized documents are held in a review queue for the two staff members."
        ),
        "results": {
            "primary_metric": {
                "label": "Auto-Routing Accuracy",
                "value": "94%",
                "baseline": "100% manual routing by 2 FTE staff",
                "outcome": "94% of 500 daily faxes routed automatically without human touch",
            },
            "secondary_metrics": [
                {"label": "Staff redeployed", "value": "1.5 FTE redeployed to clinical coordination work"},
                {"label": "Processing time", "value": "From 4 hours to 12 minutes fax-to-routing"},
                {"label": "Overtime", "value": "Eliminated"},
            ],
            "measurement_period": "3 months post-deployment",
            "measurement_basis": "Routing audit sample (500 faxes/week manually verified for 4 weeks post-launch)",
        },
        "engagement_details": {
            "duration_months": 2,
            "tenex_team_size": 2,
            "tenex_roles": ["AI Engineer", "Engagement Lead"],
            "client_team_involvement": "2 routing staff as document labelers; IT for fax gateway integration",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["Inbound fax images (TIFF via fax gateway API)", "Patient demographics (EHR lookup)"],
            "ml_approach": "GPT-4o Vision for document classification; Tesseract OCR for patient ID extraction; rule-based routing engine",
            "infrastructure": ["AWS Lambda", "S3", "SQS for department queues"],
            "client_systems_integrated": ["Fax gateway API (RightFax)", "EHR patient lookup (read-only)"],
        },
        "maturity_at_engagement": "Beginner",
        "follow_on_engagement": False,
        "lessons_learned": (
            "Document label taxonomy needs to be defined with the routing staff, not by engineers. "
            "The initial 12-class taxonomy was too granular — collapsed to 6 classes and accuracy jumped "
            "from 81% to 94%. Simpler taxonomy wins."
        ),
        "embed_text": (
            "Healthcare — Startup outpatient clinic, 60 employees, ~$8M revenue, US Southeast\n\n"
            "Problem: 500 faxes/day, 2 FTE sorting manually, 4-hour processing delay.\n\n"
            "Solution: GPT-4o Vision classifies fax type, Tesseract extracts patient ID, "
            "SQS routes to department queues. Unrecognized held for human review.\n\n"
            "Results: 94% auto-routing accuracy, 1.5 FTE redeployed, processing 4 hours to 12 minutes. "
            "3 months post-deployment."
        ),
        "industry_benchmark": "94% auto-routing accuracy on 500 daily inbound faxes",
        "success_threshold": "Applicable when fax volume exceeds 100/day and patient lookup API is available.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — document routing automation is achievable in 2 months "
            "with fax gateway API access."
        ),
        "applicable_signals": [
            "process_signal", "ops_signal", "pain_point", "tech_stack", "data_signal", "intent_signal"
        ],
        "solution_category": "document_intelligence",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
    {
        "id": "win-009",
        "engagement_title": "Sales Intelligence Copilot",
        "industry": "financial_services",
        "sector_tags": ["financial_advisors", "crm_integration", "meeting_prep", "sales_productivity"],
        "company_profile": {
            "size_employees": 70,
            "size_label": "startup",
            "annual_revenue_usd": "$10M-$18M",
            "geography": "US East",
            "business_model": "Independent wealth management firm, 30 financial advisors managing $1.2B AUM",
        },
        "problem_statement": (
            "Financial advisors spent 2 hours preparing for each client meeting, manually reviewing "
            "scattered notes, email threads, and CRM records to reconstruct the client relationship context. "
            "With 8-10 meetings per week per advisor, preparation consumed 25% of their billable time."
        ),
        "solution_summary": (
            "Built a meeting prep copilot that pulls the last 12 months of client interactions from Salesforce, "
            "summarizes the relationship history, surfaces relevant product opportunities based on portfolio, "
            "and generates suggested talking points. "
            "Advisors receive a one-page brief 30 minutes before each meeting."
        ),
        "results": {
            "primary_metric": {
                "label": "Meeting Preparation Time",
                "value": "From 2 hours to 15 minutes",
                "baseline": "2 hours per meeting, 8-10 meetings/week per advisor",
                "outcome": "15 minutes per meeting — 87% time reduction",
            },
            "secondary_metrics": [
                {"label": "Cross-sell conversion", "value": "18% increase in product attachment rate"},
                {"label": "Advisor NPS", "value": "+22 points post-deployment"},
                {"label": "Time recovered", "value": "7 hours/week per advisor returned to client-facing work"},
            ],
            "measurement_period": "4 months post-deployment",
            "measurement_basis": "Advisor time logs; CRM conversion data compared to prior 4-month period",
        },
        "engagement_details": {
            "duration_months": 3,
            "tenex_team_size": 2,
            "tenex_roles": ["AI Engineer", "Engagement Lead"],
            "client_team_involvement": "2 advisors as power users for testing; Salesforce admin for API access",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["Salesforce CRM (interaction history, portfolio data)", "Email threads (read-only)", "Meeting calendar"],
            "ml_approach": "Claude API for summarization and talking point generation; conversation history pipeline",
            "infrastructure": ["AWS Lambda", "PostgreSQL", "React frontend (advisor brief UI)"],
            "client_systems_integrated": ["Salesforce REST API", "Microsoft Calendar API"],
        },
        "maturity_at_engagement": "Emerging",
        "follow_on_engagement": True,
        "lessons_learned": (
            "Advisors adopted immediately once they saw their own client relationship reflected accurately. "
            "The first demo used real client data from a willing advisor — that one session created 10 more champions. "
            "Never demo with synthetic data when real data is available."
        ),
        "embed_text": (
            "Financial Services — Startup wealth management firm, 70 employees, ~$14M revenue, US East\n\n"
            "Problem: Advisors spent 2 hours/meeting on manual prep across scattered CRM notes and emails. "
            "8-10 meetings/week = 25% of billable time on prep.\n\n"
            "Solution: Copilot pulls 12 months of Salesforce interactions, summarizes relationship, "
            "surfaces product opportunities, generates talking points. One-page brief 30 min before meeting.\n\n"
            "Results: Prep time 2 hours to 15 min, 18% cross-sell increase, advisor NPS +22. "
            "4 months post-deployment."
        ),
        "industry_benchmark": "Meeting prep from 2 hours to 15 minutes for financial advisors",
        "success_threshold": "Applicable when CRM has 12+ months of interaction history and API is accessible.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — sales copilot ROI is achievable in 3 months "
            "with CRM API access and advisor engagement."
        ),
        "applicable_signals": [
            "process_signal", "pain_point", "tech_stack", "ops_signal", "intent_signal", "data_signal"
        ],
        "solution_category": "copilot",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
    {
        "id": "win-010",
        "engagement_title": "Quality Inspection System",
        "industry": "manufacturing",
        "sector_tags": ["quality_control", "visual_inspection", "defect_detection", "computer_vision"],
        "company_profile": {
            "size_employees": 380,
            "size_label": "mid-market",
            "annual_revenue_usd": "$60M-$90M",
            "geography": "US Midwest",
            "business_model": "Precision parts manufacturer, 3 production lines running 2 shifts/day, 8,000 parts/day",
        },
        "problem_statement": (
            "Manual visual inspection caught 91% of defects across 8,000 parts per day. "
            "3 inspectors per shift were needed, and inspector fatigue on the second shift "
            "caused the miss rate to increase by 35% in the final 2 hours. "
            "Defect escapes cost $230K annually in customer returns and rework."
        ),
        "solution_summary": (
            "Deployed a computer vision system using a fine-tuned ResNet-50 model on production line cameras. "
            "The model classifies each part in real time, flags defects with bounding boxes, "
            "and triggers an alert to the line supervisor dashboard within 400ms. "
            "Edge inference runs on NVIDIA Jetson devices mounted at each inspection station."
        ),
        "results": {
            "primary_metric": {
                "label": "Defect Detection Rate",
                "value": "From 91% to 99.4%",
                "baseline": "91% detection rate, 3 manual inspectors per shift",
                "outcome": "99.4% detection — inspector fatigue effect eliminated",
            },
            "secondary_metrics": [
                {"label": "Inspectors redeployed", "value": "2 inspectors redeployed to complex assembly work"},
                {"label": "Quality cost reduction", "value": "$230K/year from reduced returns and rework"},
                {"label": "Alert latency", "value": "Defect alert to supervisor within 400ms of detection"},
            ],
            "measurement_period": "6 months post-deployment",
            "measurement_basis": "Defect log audit compared to 12-month pre-deployment baseline",
        },
        "engagement_details": {
            "duration_months": 4,
            "tenex_team_size": 3,
            "tenex_roles": ["ML Engineer", "Edge Infrastructure Engineer", "Engagement Lead"],
            "client_team_involvement": "2 quality engineers as domain experts; production manager for line access",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["Production line camera images (labeled defect archive)", "Part geometry specs"],
            "ml_approach": "Fine-tuned ResNet-50 for defect classification; bounding box detection; edge inference",
            "infrastructure": ["NVIDIA Jetson edge devices (on-premise)", "GCP Vertex AI (model training)", "Grafana dashboard"],
            "client_systems_integrated": ["Production line PLC (alert trigger)", "Quality management system"],
        },
        "maturity_at_engagement": "Developing",
        "follow_on_engagement": True,
        "lessons_learned": (
            "Labeling 5,000 training images was the critical path — the client had unlabeled archives. "
            "Budget 4 weeks for labeling with quality engineers before modeling starts. "
            "Edge deployment on Jetson requires a dry-run of the full inference pipeline before production installation."
        ),
        "embed_text": (
            "Manufacturing — Mid-market precision parts maker, 380 employees, ~$75M revenue, US Midwest\n\n"
            "Problem: 91% manual defect detection, inspector fatigue, $230K/year in escapes. "
            "3 inspectors per shift required.\n\n"
            "Solution: Fine-tuned ResNet-50 on production line cameras. Edge inference on NVIDIA Jetson. "
            "Real-time defect detection with 400ms alert latency.\n\n"
            "Results: Detection rate 91% to 99.4%, 2 inspectors redeployed, $230K/year quality savings. "
            "6 months post-deployment."
        ),
        "industry_benchmark": "Defect detection from 91% to 99.4% on 8,000 parts/day production line",
        "success_threshold": "Applicable when labeled defect image archive exists and production line cameras are accessible.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — visual inspection automation is achievable in 4 months "
            "with labeled image data and camera access."
        ),
        "applicable_signals": [
            "process_signal", "ops_signal", "pain_point", "data_signal", "tech_stack", "ml_signal"
        ],
        "solution_category": "computer_vision",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
    {
        "id": "win-011",
        "engagement_title": "Compliance Report Generator",
        "industry": "financial_services",
        "sector_tags": ["regulatory_reporting", "compliance_automation", "transaction_reporting", "narrative_generation"],
        "company_profile": {
            "size_employees": 350,
            "size_label": "mid-market",
            "annual_revenue_usd": "$55M-$80M",
            "geography": "US East",
            "business_model": "Registered investment advisor, $2.4B AUM, 4 compliance staff managing 6 regulatory reports per quarter",
        },
        "problem_statement": (
            "The compliance team spent 5 days per quarter generating regulatory reports from transaction data, "
            "manually writing narrative sections, and populating templates from multiple data sources. "
            "Each report took 2-3 people working full-time for 2 days, creating concentration risk "
            "and leaving no buffer for ad hoc regulatory requests."
        ),
        "solution_summary": (
            "Built an LLM report generation pipeline: SQL queries extract relevant transactions by report type, "
            "Claude generates narrative sections from structured data summaries, "
            "and Jinja templates populate the formatted report. "
            "A compliance officer reviews the draft and approves before submission."
        ),
        "results": {
            "primary_metric": {
                "label": "Report Generation Time",
                "value": "From 5 days to 4 hours per quarter",
                "baseline": "5 business days per quarter across 2-3 compliance staff",
                "outcome": "4 hours with one compliance officer for final review",
            },
            "secondary_metrics": [
                {"label": "Compliance findings", "value": "Zero findings in 3 subsequent audits post-deployment"},
                {"label": "Staff concentration risk", "value": "Any team member can now generate the report"},
                {"label": "Ad hoc request capacity", "value": "Team handles 3x more ad hoc regulatory inquiries"},
            ],
            "measurement_period": "3 quarters post-deployment",
            "measurement_basis": "Time logs; regulatory audit results; team capacity surveys",
        },
        "engagement_details": {
            "duration_months": 3,
            "tenex_team_size": 2,
            "tenex_roles": ["AI Engineer", "Engagement Lead"],
            "client_team_involvement": "Lead compliance officer for report structure definition; IT for database access",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["Transaction database (PostgreSQL)", "Trade records", "Client account data"],
            "ml_approach": "Claude API for narrative generation from structured summaries; SQL extraction; Jinja templates",
            "infrastructure": ["AWS Lambda", "PostgreSQL", "Internal web app for review and approval"],
            "client_systems_integrated": ["Portfolio management system (DB access)", "Regulatory submission portal"],
        },
        "maturity_at_engagement": "Emerging",
        "follow_on_engagement": False,
        "lessons_learned": (
            "Compliance officers are the hardest stakeholders to convince — they own the report signature. "
            "Run the system in parallel for 2 full reporting cycles before replacing the manual process. "
            "The parallel run builds trust faster than any demo."
        ),
        "embed_text": (
            "Financial Services — Mid-market RIA, 350 employees, ~$65M revenue, US East\n\n"
            "Problem: Compliance team spent 5 days/quarter generating regulatory reports manually. "
            "2-3 staff, full-time for 2 days per report cycle.\n\n"
            "Solution: SQL extracts transactions, Claude generates narrative sections, "
            "Jinja templates populate formatted report. Compliance officer reviews and approves.\n\n"
            "Results: 5 days to 4 hours, zero findings in 3 audits, 3x ad hoc capacity. "
            "3 quarters post-deployment."
        ),
        "industry_benchmark": "Quarterly report generation from 5 days to 4 hours for RIA compliance",
        "success_threshold": "Applicable when report structure is defined and transaction data is in a queryable database.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — compliance report automation is achievable in 3 months "
            "with structured transaction data and compliance officer involvement."
        ),
        "applicable_signals": [
            "process_signal", "pain_point", "ops_signal", "data_signal", "tech_stack", "intent_signal"
        ],
        "solution_category": "llm_workflow",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
    {
        "id": "win-012",
        "engagement_title": "Internal HR Policy Copilot",
        "industry": "professional_services",
        "sector_tags": ["hr_automation", "employee_self_service", "policy_qa", "slack_integration"],
        "company_profile": {
            "size_employees": 240,
            "size_label": "mid-market",
            "annual_revenue_usd": "$35M-$55M",
            "geography": "US West",
            "business_model": "Technology consulting firm, 180 billable staff, HR team of 4 managing all people operations",
        },
        "problem_statement": (
            "The HR team answered 200 employee questions per week about benefits, PTO policy, expense reimbursement, "
            "and parental leave. 35% were repeat questions answered identically each time. "
            "HR staff spent 15 hours per week on policy Q&A instead of strategic people work, "
            "and new employees in the first 90 days generated 40% of the volume."
        ),
        "solution_summary": (
            "Built a RAG chatbot over the employee handbook, benefits guides, and HR policy documents "
            "using OpenAI embeddings and ChromaDB. "
            "Employees ask questions in a dedicated Slack channel; the bot answers with cited policy text. "
            "Claude generates the answer; escalation to HR is one click away."
        ),
        "results": {
            "primary_metric": {
                "label": "Questions Auto-Answered",
                "value": "71%",
                "baseline": "0% automated — 200 questions/week handled by HR team manually",
                "outcome": "142 of 200 weekly questions answered by bot without HR involvement",
            },
            "secondary_metrics": [
                {"label": "HR time reclaimed", "value": "15 hours/week returned to strategic work"},
                {"label": "Employee satisfaction", "value": "+12 points on quarterly engagement survey"},
                {"label": "New hire question volume", "value": "40% reduction in first-90-day HR questions"},
            ],
            "measurement_period": "4 months post-deployment",
            "measurement_basis": "Slack bot interaction logs; HR time survey; quarterly engagement survey",
        },
        "engagement_details": {
            "duration_months": 2,
            "tenex_team_size": 2,
            "tenex_roles": ["AI Engineer", "Engagement Lead"],
            "client_team_involvement": "HR lead for document curation; IT for Slack App approval",
            "delivery_model": "project",
        },
        "tech_stack": {
            "data_sources": ["Employee handbook (PDF)", "Benefits guide (PDF)", "HR policy documents (30 files)"],
            "ml_approach": "OpenAI embeddings for retrieval; Claude for answer generation; ChromaDB vector store",
            "infrastructure": ["AWS ECS", "ChromaDB managed", "Slack Bot API"],
            "client_systems_integrated": ["Slack workspace API", "HRIS (read-only for org chart)"],
        },
        "maturity_at_engagement": "Beginner",
        "follow_on_engagement": False,
        "lessons_learned": (
            "Policy documents need to be split at the section level, not the page level. "
            "Page-level chunking created answers that combined unrelated policy clauses. "
            "Section-level chunking with metadata tags (policy name, effective date) dramatically improved accuracy."
        ),
        "embed_text": (
            "Professional Services — Mid-market tech consulting firm, 240 employees, ~$45M revenue, US West\n\n"
            "Problem: HR team answered 200 questions/week. 35% repeat. 15 hours/week on policy Q&A.\n\n"
            "Solution: RAG chatbot over employee handbook and HR policies using OpenAI embeddings, "
            "ChromaDB, Claude for answers. Slack integration with one-click HR escalation.\n\n"
            "Results: 71% of questions auto-answered, 15 hours/week reclaimed, employee satisfaction +12. "
            "4 months post-deployment."
        ),
        "industry_benchmark": "71% auto-answer rate on 200 weekly HR policy questions",
        "success_threshold": "Applicable when HR policy documents are current and employee count exceeds 100.",
        "gap_analysis_template": (
            "Maturity gap of {gap} points — HR policy copilot is achievable in 2 months "
            "with curated policy documents and Slack access."
        ),
        "applicable_signals": [
            "process_signal", "pain_point", "ops_signal", "intent_signal", "data_signal", "hiring_signal"
        ],
        "solution_category": "knowledge_retrieval",
        "status": "active",
        "ingestion_date": "2026-03-20",
    },
]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(VICTORIES, indent=2))
    print(f"Wrote {len(VICTORIES)} victories to {OUTPUT}")


if __name__ == "__main__":
    main()
