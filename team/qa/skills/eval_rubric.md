# Skill: Eval Rubric

Write evaluation rubrics for recommendation quality and implement the eval runner.

## When to load

Load this skill when: defining what "good" output looks like for the thought engine or pitch synthesis, implementing an automated eval, or creating the eval harness for Sprint 7.

---

## Steps

1. Read `core/schemas.py` — specifically `Opportunity`, `EvidenceItem`, `SectionConfidence`. These are what you are evaluating.
2. Define the rubric dimensions. For recommendations, use these four:
   - Evidence grounding: are all opportunity claims backed by specific evidence_ids?
   - Tier accuracy: is the tier (Easy/Medium/Hard) justified by the confidence score and evidence count?
   - ROI basis: is the ROI claim linked to a real measured_impact from a past win? Is the assumption stated?
   - Coverage completeness: what percentage of required fields have evidence? Are gaps flagged?
3. For each dimension, write a scoring guide:
   - 5: complete, all claims backed, no unsupported assertions
   - 4: mostly complete, one minor gap
   - 3: acceptable, one significant gap or one unsupported claim
   - 2: incomplete, multiple gaps
   - 1: poor, claims without evidence, wrong tier classification
4. Write the eval rubric as YAML in `evals/rubrics/<dimension_name>.yaml`. Format:
   ```yaml
   rubric_id: evidence_grounding
   version: 1.0
   dimensions:
     - name: evidence_grounding
       weight: 0.30
       criteria:
         5: "Every opportunity has at least 2 evidence_ids. All claims traceable."
         3: "Opportunities have evidence_ids but one claim lacks backing."
         1: "Opportunities have no evidence_ids or evidence is irrelevant."
   pass_threshold: 3.8
   ```
5. Implement the eval runner in `evals/eval_runner.py`:
   - Load a set of synthetic company bundles from `evals/test_companies.json`.
   - For each company, run the full pipeline (or load cached output).
   - Score each output against the rubrics.
   - Write results to `evals/results/latest.json`.
   - Exit non-zero if average score < pass_threshold.

---

## Input

- `core/schemas.py` (output types to evaluate)
- Sprint plan (what quality means for this sprint's output)

## Output

- Rubric YAML files in `evals/rubrics/`
- Eval runner in `evals/eval_runner.py`
- Synthetic test companies in `evals/test_companies.json` (if not yet created)

## Constraints

- Rubrics evaluate the output shapes defined in schemas.py. They do not evaluate prompt text.
- Pass threshold is 3.8/5.0. This is fixed unless Sai changes it via an ADR.
- Eval runner must run without real API calls when given cached pipeline output.
- Rubric files are versioned (version field in YAML). Never edit a published rubric — increment the version.

## Commit cadence

- `test(evals): add evidence grounding and tier accuracy rubrics`
- `test(evals): add eval runner with synthetic company bundle support`
