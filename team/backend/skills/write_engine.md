# Skill: Write Engine

Create or modify an engine in `engines/thought/` or `engines/pitch/`.

## When to load

Load this skill when: implementing the thought engine reasoning loop, implementing pitch synthesis, or modifying engine behavior after a sprint review.

---

## Steps

1. Read `core/schemas.py` — every input and output type for your engine is defined here.
2. Read `config/defaults.yaml` — your engine uses `depth_budget`, `confidence_threshold`, and model names from config. Read them via `core/config.py`, never hardcode.
3. Read the prompt file for your engine from `prompts/`. The prompt file defines the output shape. Your engine parses that output into the schema.
4. Write the engine module. Follow this structure:
   - One main function with a typed signature: inputs are Pydantic models, output is a Pydantic model or raises a typed error.
   - Engine state (e.g., evidence accumulator, loop counter) is local to the function call. Never stored globally.
   - Services (RAG, grounder) are called by importing and calling their typed function. No business logic inside service calls.
   - Stop conditions are explicit: check confidence threshold, depth budget, and coverage completeness. Do not loop indefinitely.
5. Add trace events at every major step: loop started, tool called, gap detected, loop completed, engine stopped. Use `services/trace.py`.
6. Handle errors: if a service call fails, catch it, log it via trace, and continue with reduced evidence. Never crash the engine on a single service failure.
7. Max 200 lines per file. If the engine logic exceeds that, extract helpers into a separate module in the same directory.

---

## Input

- `core/schemas.py` (input/output types)
- `config/defaults.yaml` (budget and model config)
- Prompt file from `prompts/`
- Sprint plan for this engine (describes what it must do)

## Output

- Engine module(s) in `engines/thought/` or `engines/pitch/`
- Trace events emitted at every major step

## Constraints

- Engines never import from each other. Thought engine does not import pitch synthesis.
- Engines never call model providers directly. All model calls go through `core/config.py` model settings + the relevant service.
- Engines never write to `services/trace.py` internal state directly. They call `trace.emit()` only.
- All prompts are read from `prompts/*.md` at runtime. Never as inline strings.
- Return typed output. Never return raw dicts.

## Commit cadence

- `feat(thought): add iterative reasoning loop with depth budget control`
- `feat(thought): add mid gap detection with user question emission`
- `feat(pitch): add 3-tier opportunity classifier with roi translation`
