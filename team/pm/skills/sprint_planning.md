# Skill: Sprint Planning

Create a sprint plan and the Linear tickets that execute it.

## When to load

Load this skill when: creating a new sprint plan, writing tickets for a sprint, grooming the backlog, or reprioritizing work.

---

## Steps

1. Read `SPRINT_PLAN.md` to understand which sprint you are planning and what the previous sprint left behind.
2. Read the previous sprint's plan file (e.g., `SPRINT_N_PLAN.md`) to confirm what was completed and what carries over.
3. Identify the sprint goal in one sentence. The goal must produce something Sai can see and test.
4. List the tickets for this sprint. Each ticket gets:
   - A title: `[TAG] Short imperative description`
   - A user story: As <who>, I need <what> so that <why>.
   - A `done_when` line: one sentence, exact condition for completion.
   - Acceptance criteria: 3-6 checkboxes.
   - An `Execute with` block: primary subagent, any collaborators, reason.
   - `Test certification required: yes/no`
   - `Decision required: yes/no`
5. Order tickets by dependency. Tickets that block others go first.
6. Write the sprint plan to `SPRINT_N_PLAN.md` with all success criteria checkboxes unchecked.
7. Update `SPRINT_PLAN.md`: set the sprint status to IN PROGRESS.
8. Create tickets in Linear.

---

## Input

- `SPRINT_PLAN.md` (sprint goals and architecture context)
- Previous sprint plan file (what's done, what carried over)
- Any open Linear tickets not yet addressed

## Output

- `SPRINT_N_PLAN.md` — full spec for this sprint
- Linear tickets for each piece of work
- Updated `SPRINT_PLAN.md` with sprint status

## Constraints

- Every sprint must deliver something testable. No invisible work.
- Never assign code work to pm subagent_type. Use backend, frontend, or qa.
- Every ticket must have a `done_when` field. This is the termination criteria.
- No ticket covers more than one logical unit of work.
- Never plan more than 6 tickets per sprint — scope creep kills sprints.

## Commit cadence

One commit per planning artifact created:
- `docs(sprintN): add sprint N plan with success criteria`
- `docs(sprintN): add Linear ticket definitions for sprint N`
