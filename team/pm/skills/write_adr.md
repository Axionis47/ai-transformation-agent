# Skill: Write ADR

Write an Architecture Decision Record when a decision affects system architecture, an agent interface, or a tech stack choice.

## When to load

Load this skill when: any agent makes a decision that changes how two components talk to each other, a new library is added to `requirements.txt`, or a sprint plan changes an interface that was already defined.

---

## Steps

1. Identify the decision. Write one sentence: "We decided to <X> instead of <Y>."
2. Create `docs/decisions/ADR-NNN.md` where NNN is the next sequential number.
3. Write the ADR with these sections:
   - `# ADR-NNN: <Title>`
   - `Status: Accepted` (or Proposed / Superseded)
   - `Date: YYYY-MM-DD`
   - `Context`: What situation forced this decision? 2-4 sentences.
   - `Decision`: What was decided? One clear paragraph.
   - `Alternatives considered`: What else was on the table? Why rejected?
   - `Consequences`: What does this change? What gets easier, what gets harder?
   - `Affected files`: List the files or modules this decision touches.
4. Append one line to `docs/decisions/INDEX.md`:
   `| ADR-NNN | Title | Date | Status |`
5. Post a one-line note on the related Linear ticket: `DECISION: <what> — see ADR-NNN`

---

## Input

- Understanding of the decision made (read the relevant ticket or agent output)
- `docs/decisions/INDEX.md` (to find the next ADR number)

## Output

- `docs/decisions/ADR-NNN.md`
- Updated `docs/decisions/INDEX.md`

## Constraints

- ADRs are immutable once merged. Never edit a merged ADR. Supersede it with a new one.
- Keep ADRs short. Context + decision + consequences fits in 30 lines.
- Every architectural decision gets an ADR. No exceptions.
- The ticket that triggered the decision cannot close without the ADR being written.

## Commit cadence

- `docs(decisions): add ADR-NNN for <topic>`
