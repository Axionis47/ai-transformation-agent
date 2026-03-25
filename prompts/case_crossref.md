---
prompt_id: case_crossref
version: 2.0
used_by: engines/thought/reasoning_loop.py
---

A past AI engagement was found that may be relevant to {company_name} ({industry}).

## Company Context
{company_summary}

## Past Engagement
Title: {eng_title}
Industry: {eng_industry}, Size: {eng_size}
Problem: {eng_problem}
Solution: {eng_solution}
Impact: {eng_impact}

## Discovery Insight
{discovery_insight}

## Lessons Learned
{lessons_learned}

## Implementation Friction
{implementation_friction}

## Baseline Metrics (what the client looked like before)
{baseline_metrics}

## Conditions for Success
{conditions_list}

## Anti-Patterns
{anti_patterns_list}

## Instructions
Cross-reference this past case against {company_name}. Be specific.

1. RELEVANCE: Why does this case match? What patterns are similar?
2. TRANSFERABLE: Which results and approaches would work for {company_name}?
3. NOT TRANSFERABLE: What's different? Why can't we copy-paste?
4. CONDITIONS CHECK: For each condition, is it MET, UNMET, or UNKNOWN for {company_name}?
5. ANTI-PATTERN CHECK: For each anti-pattern, is it TRIGGERED or SAFE for {company_name}?
6. IMPLEMENTATION RISK: Based on the friction this engagement hit, what similar friction should we expect with {company_name}?
7. BASELINE COMPARISON: How do {company_name}'s likely volumes compare to the engagement's baseline? Does scale help or hurt?

Respond ONLY with this JSON (no other text):
```json
{{
  "relevance": "One sentence on why this case matches",
  "conditions_check": [
    {{"condition": "the condition text", "status": "MET|UNMET|UNKNOWN", "reasoning": "why"}}
  ],
  "anti_pattern_check": [
    {{"pattern": "the anti-pattern text", "status": "TRIGGERED|SAFE", "reasoning": "why"}}
  ],
  "transferable": ["what applies to this client"],
  "needs_adaptation": ["what's different and why"],
  "implementation_risks": ["specific friction risks for this client based on past lessons"],
  "baseline_comparison": "how this client's scale compares to the engagement baseline"
}}
```
