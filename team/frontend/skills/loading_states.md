# Skill: Loading States

Implement loading indicators, error states, and agent thinking states.

## When to load

Load this skill when: a page needs to show loading state while fetching, when the agent is reasoning and the user is waiting, or when handling error states gracefully.

---

## Steps

1. Identify all async operations on the page:
   - Initial page load (run state fetch)
   - UIHints fetch (called after every user action)
   - SSE stream updates (live reasoning steps)
   - Form submissions (transitions)
2. For each async operation, implement three states: loading, success, error.
3. Loading states:
   - Initial load: show a skeleton layout matching the expected content shape. Not a spinner — a skeleton. The skeleton should have the same structure as the loaded state.
   - After user action (button click): disable the button, show a spinner inside it, keep all other content visible.
   - Agent reasoning (SSE active): show a "Agent is reasoning..." strip at the top with a pulsing indicator. Below it, show the trace events as they arrive — each event is one line with a timestamp.
4. Agent thinking state:
   - When the run status is REASONING and there is no agent_message, show: "Agent is gathering evidence..." with a progress indicator showing the current loop number vs depth_budget.
   - When `agent_message` is non-null, clear the thinking indicator and show the question prominently.
5. Error states:
   - 404 (run not found): full page message "This run was not found" with a link to start a new one.
   - 422 (validation error): show the error message next to the relevant form field.
   - 500 (engine error): show "Analysis failed" with the error message and a "Start a new run" button.
   - SSE dropped: show a banner "Connection lost — reconnecting..." during backoff.

---

## Input

- The page or component that needs loading states
- API call patterns (from `frontend/lib/api.ts`)

## Output

- Loading, success, and error states for every async operation
- Skeleton components for initial page loads
- Agent thinking indicator component

## Constraints

- Never show a blank white screen during loading. Always show a skeleton.
- Do not block the entire UI during an agent action. Only the action's button is disabled.
- Error states must always offer a recovery action (retry or start new).
- The agent thinking indicator must show progress, not just a spinner.

## Commit cadence

- `feat(loading): add skeleton layout for run analysis page`
- `feat(loading): add agent reasoning indicator with loop progress`
- `feat(loading): add error state components with recovery actions`
