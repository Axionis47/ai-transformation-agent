# Skill: Architecture Review

Review system architecture to confirm engine boundaries are clean and interfaces match what was planned.

## When to load

Load this skill when: a sprint completes and you need to verify no coupling was introduced, a backend agent made a structural decision, or Sai asks about system design.

---

## Steps

1. Read `SPRINT_PLAN.md` — specifically the architecture diagram and the five engine descriptions.
2. Read the sprint plan for the sprint just completed.
3. Check each engine boundary:
   - RAG Service (`services/rag/`): does it expose a callable function? Does it have zero knowledge of the thought engine?
   - Grounder (`services/grounder/`): same check. Is it callable as a standalone tool?
   - Thought Engine (`engines/thought/`): does it call RAG and Grounder as tools? Does it own reasoning state only?
   - Pitch Synthesis (`engines/pitch/`): does it receive thought engine output and nothing else?
   - Trace (`services/trace.py`): is it always-on? Does it never block execution?
4. Check the API layer (`api/`): does it call engines via `core/run_manager.py`? No direct engine imports in routes?
5. Check `config/defaults.yaml`: are all knobs here? No hardcoded values in `.py` files?
6. List any violations found. For each violation, write a ticket for the backend agent.
7. Update `docs/ARCHITECTURE.md` if the review reveals the diagram is out of date.

---

## Input

- `SPRINT_PLAN.md`
- Current sprint plan file
- File listings of `services/`, `engines/`, `api/`, `core/`

## Output

- List of boundary violations (if any) and corresponding tickets
- Updated `docs/ARCHITECTURE.md` if needed

## Constraints

- Do not read implementation details unless you suspect a violation. Every file read costs context.
- If you find a violation, write a ticket. Do not fix it yourself — you do not touch `.py` files.
- A clean sprint has zero boundary violations.

## Commit cadence

- `docs(arch): update architecture diagram after sprint N review`
