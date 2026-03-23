# Skill: CI Workflow

Create or modify GitHub Actions CI/CD workflows in `.github/workflows/`.

## When to load

Load this skill when: adding a new CI check, modifying the existing test workflow, or implementing the Cloud Run deploy pipeline.

---

## Steps

1. Read `.github/workflows/` to understand what workflows already exist before adding a new one.
2. For the test workflow (`ci.yml`):
   - Trigger: on push to any branch, on pull request to main.
   - Steps: checkout, setup Python, install requirements, run `pytest tests/ -q --tb=short`.
   - Fail fast: if tests fail, stop the workflow and report the failure.
   - No secrets required for tests — they mock all external calls.
3. For the eval gate workflow (`eval_gate.yml`):
   - Trigger: on pull request to main only.
   - Steps: checkout, setup Python, install requirements, run eval runner, check score >= 3.8.
   - Fail fast: if eval score is below threshold, block the PR.
4. For the deploy workflow (`deploy.yml`):
   - Trigger: manual only (`workflow_dispatch`) until Sprint 7 completes.
   - Steps: checkout, authenticate to GCP, build Docker image, push to Artifact Registry, deploy to Cloud Run.
   - Requires GCP_PROJECT_ID and GCP credentials as GitHub secrets.
   - Only trigger from main branch.
5. Every workflow file must have a `name:` field and a comment at the top explaining when it runs.

---

## Input

- Existing workflow files (read them before creating a new one)
- Sprint plan (what checks are needed for this sprint)

## Output

- New or updated workflow files in `.github/workflows/`

## Constraints

- Never add secrets directly to workflow files. Use `${{ secrets.NAME }}` for all credentials.
- Test workflows must pass without any real API keys. All external calls are mocked in tests.
- Deploy workflow is manual only until the system is stable (Sprint 7).
- Workflow files are YAML — check indentation carefully. A bad workflow silently fails.

## Commit cadence

- `ci(gate): add test workflow running pytest on push`
- `ci(deploy): add manual cloud run deploy workflow`
