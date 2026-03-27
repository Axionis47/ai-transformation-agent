---
prompt_id: company_research
version: 2.0
used_by: engines/thought/assumptions.py
---

Research {company_name} in the {industry} industry. Focus on OPERATIONAL details, not marketing copy.
{notes_section}

Find specific answers to these questions:

1. OPERATIONS: What are {company_name}'s core operational workflows? How do they process transactions, handle customer requests, manage compliance? Look for specific volumes (transactions per day, tickets per week, reviews per month).

2. PAIN POINTS: What operational bottlenecks or manual processes does {company_name} have? Look for hiring patterns (are they hiring for repetitive roles?), customer complaints, Glassdoor reviews about process inefficiency, or press about operational challenges.

3. TECHNOLOGY: What is their tech stack? Do they have a data warehouse, ML platform, or existing automation? This determines what AI solutions are feasible.

4. SCALE: How many employees? What's their revenue or transaction volume? Growth rate? This determines which solutions are worth the investment.

5. COMPETITIVE PRESSURE: What are competitors doing with AI/automation that {company_name} might need to match?

6. BUSINESS MODEL: How do they make money? What drives their unit economics? This determines where AI creates the most ROI.

Be factual and specific. Include numbers, names, and dates. Do NOT give generic industry analysis — focus on what is known about THIS specific company.
