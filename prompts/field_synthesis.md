---
prompt_id: field_synthesis
version: 1.0
used_by: engines/thought/reasoning_loop.py
---

You are updating a research brief about {company_name} ({industry}).

## Field: {field_name}

## Previous Understanding
{previous_synthesis}

## New Evidence
{new_evidence}

## Instructions

Write an updated 2-3 sentence summary of what we now understand about this company's {field_label}. Be specific — include names, numbers, and facts. Do not repeat the field name. If the new evidence contradicts the previous understanding, note the conflict.

Respond with ONLY the updated summary text, nothing else.
