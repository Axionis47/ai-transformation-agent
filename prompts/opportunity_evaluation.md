---
prompt_id: opportunity_evaluation
version: 1.0
used_by: engines/pitch/matcher.py
---

You are evaluating whether an AI opportunity template fits a specific company.

## Company Context
Company: {company_name}
Industry: {industry}
Size: {employee_count_band}

## Confirmed Assumptions
{assumptions_summary}

## Opportunity Template
Name: {template_name}
Description: {template_description}
Solution type: {solution_shape}
Workflow area: {workflow_area}
Typical timeline: {timeline_weeks} weeks
Applicable industries: {applicable_industries}

## Past Engagements (from our wins database)
{engagement_summaries}

## Evidence Collected
{evidence_items}

## Reasoning Context (what the research phase discovered and why)
{reasoning_context}

## Confidence Rubric

Score your confidence using these definitions — do not default to 0.75:
- 0.0–0.2: Highly speculative — no supporting evidence found
- 0.2–0.4: Plausible but weak — significant unknowns remain
- 0.4–0.6: Moderate — some proven elements, gaps in validation
- 0.6–0.8: Strong — similar successes exist, evidence supports fit
- 0.8–1.0: Very high — directly proven in similar context with strong evidence

## Instructions

Evaluate whether this opportunity is a good fit for {company_name}. Think through:

1. Does the evidence suggest this company has the problem this template solves?
2. Is there evidence of the workflows, volumes, or pain points that make this valuable?
3. Do past engagements in similar industries validate this approach?
4. What risks or blockers exist?
5. What tier does this fall into?
   - **EASY**: Strong evidence match + same industry past engagement + proven ROI
   - **MEDIUM**: Partial evidence or different industry past engagement — state exactly what adaptation is needed
   - **HARD**: Speculative — low evidence but high potential; flag specific uncertainties

Respond ONLY with this JSON (no other text):
```json
{{
  "fit_score": 0.75,
  "tier": "EASY",
  "reasoning": "Detailed explanation of why this tier and score",
  "supporting_evidence_ids": ["evidence_id_1", "evidence_id_2"],
  "matched_engagement_ids": ["eng-001"],
  "risks": ["risk 1", "risk 2"],
  "adaptation_needed": "null for EASY, specific adaptation for MEDIUM, null for HARD",
  "feasibility": 0.8,
  "roi_score": 0.7,
  "time_to_value": 0.9,
  "confidence": 0.0,
  "rationale": "One-paragraph explanation of the opportunity and why it fits"
}}
```
