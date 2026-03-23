---
prompt_id: reasoning_queries
version: 1.0
used_by: engines/thought/reasoning_loop.py
---

## Grounding query templates

company_profile: What does {company_name} do? Describe their core products, services, and market position.
industry_context: What are the major trends, challenges, and opportunities in the {industry} industry for mid-market companies?
business_processes: What are the key business processes and operational workflows at {company_name} or similar {industry} companies?
pain_points: What operational challenges and inefficiencies do {industry} companies like {company_name} typically face?
scale_indicators: How large is {company_name}? Number of employees, revenue, customer base, or transaction volumes.

## RAG query templates

similar_wins: {industry} {pain_area} automation implementation mid-market
comparable_scale: {employee_count_band} company {industry} AI transformation

## User question templates

company_profile: Can you describe what {company_name} does in your own words?
business_processes: What are the main workflows or processes at {company_name} that take the most time?
pain_points: What are the biggest operational challenges at {company_name} right now?
scale_indicators: Roughly how many employees does {company_name} have, and what is the approximate volume of {volume_type} you handle?
