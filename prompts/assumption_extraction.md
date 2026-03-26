---
prompt_id: assumption_extraction
version: 1.0
used_by: engines/thought/assumptions.py
---

You are analyzing research about {company_name} in the {industry} industry.

## Research Text
{grounding_text}

## Evidence Sources
{evidence_summary}

## Instructions

Extract structured assumptions from the research. For each of these fields, determine what the research tells us:

1. **company_description**: What the company does, core products/services
2. **industry_segment**: Specific segment within {industry}
3. **company_size**: Employee count, revenue, scale indicators
4. **key_products**: Main products or services offered
5. **technology_stack**: Technology, platforms, infrastructure used
6. **business_model**: How the company generates revenue

For each field:
- Extract the most specific, factual statement from the research
- Rate confidence using this rubric — do NOT default to high values:
  - 0.9-1.0: Direct from official source (company website, SEC filing, press release with date)
  - 0.7-0.8: Multiple sources agree but no official confirmation
  - 0.5-0.6: Single source or general industry knowledge applied to this company
  - 0.3-0.4: Inferred from indirect signals, not directly stated
  - 0.1-0.2: Educated guess, very little supporting evidence
- Explain your confidence rating — cite what supports it and what's uncertain
- If no information is available, list it as an open question with a suggested follow-up query

Respond ONLY with this JSON (no other text):
```json
{{
  "assumptions": [
    {{
      "field": "company_description",
      "value": "Clear, specific statement about what the company does",
      "confidence": 0.65,
      "confidence_reasoning": "Why you're this confident — cite what supports it",
      "source_quote": "Exact quote or paraphrase from the research text"
    }}
  ],
  "open_questions": [
    {{
      "field": "technology_stack",
      "reason": "Why this information is missing",
      "suggested_query": "A specific search query to find this information"
    }}
  ]
}}
```
