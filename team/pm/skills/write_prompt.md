# Skill: Write Prompt

Write or update a prompt file in `prompts/`.

## When to load

Load this skill when: creating a new prompt for any engine or service, updating an existing prompt after an eval failure, or iterating on prompt quality.

---

## Steps

1. Read `SPRINT_PLAN.md` and the relevant sprint plan to understand what the engine does and what output shape it produces.
2. Read `core/schemas.py` to understand the exact output types the engine must return. The prompt must produce output that validates against the schema.
3. Read `config/defaults.yaml` to understand which model this prompt runs on (reasoning_model, synthesis_model, or grounding_model).
4. Write the prompt file to `prompts/<engine_name>.md`. Include:
   - A header block: `# Prompt: <name>`, `Version: X.Y`, `Model: <model>`, `Owner: PM`
   - Role definition: one sentence describing what this agent is
   - Input section: exactly what fields the agent receives
   - Output section: the exact schema it must return (field names, types, constraints)
   - Instructions: numbered steps, specific and actionable
   - Constraints: what the agent must never do
   - Example (if helpful): one input/output pair
5. Update `prompts/VERSIONS.md` with a one-line entry: `vX.Y — <date> — <what changed>`

---

## Input

- `core/schemas.py` (output types)
- `config/defaults.yaml` (which model runs this prompt)
- Sprint plan context (what the engine does)

## Output

- `prompts/<engine_name>.md` — the prompt file
- Updated `prompts/VERSIONS.md`

## Constraints

- Never hardcode company names or specific data in prompts.
- Never write prompts that blend evidence, abstraction, and confidence — these are separate dimensions.
- Output shape must match the Pydantic schema exactly. The backend agent will fail if fields diverge.
- Prompts live in `prompts/`. Never embed prompt text in `.py` files.
- Keep prompts under 150 lines. Long prompts rot.

## Commit cadence

- `docs(prompts): add <engine_name> prompt v1.0`
- `docs(prompts): update <engine_name> prompt to v1.1 after eval iteration`
