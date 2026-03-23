# Skill: Page Layout

Build a new page in the Next.js App Router.

## When to load

Load this skill when: creating a new page file, building the main analysis page, or restructuring an existing page's layout.

---

## Steps

1. Read `core/schemas.py` to understand the data shapes this page will render.
2. Decide the page route. Pages live in `frontend/app/<route>/page.tsx`.
3. Build the page layout:
   - Use App Router conventions: `page.tsx` for the page, `layout.tsx` for shared wrappers.
   - Desktop-first. No responsive design required. Minimum viewport: 1280px wide.
   - Use Tailwind for styling. No external UI component libraries unless they are already in `package.json`.
   - Structure: top navigation (if needed), main content area, no sidebars unless the ticket specifies one.
4. For the main analysis page (`/runs/[id]`), follow this layout:
   - Header: run ID, status badge, budget remaining (always visible)
   - Agent message area: full width, prominent, only shown when `agent_message` is non-null
   - Stage progress: compact horizontal indicator
   - Main content: switches based on current stage (form, evidence panel, recommendations, etc.)
5. Extract reusable pieces into `frontend/components/`. Pages compose components — they do not contain inline JSX logic.
6. Use TypeScript types that match `core/schemas.py`. Define them in `frontend/lib/types.ts`.

---

## Input

- `core/schemas.py` (Python) translated to TypeScript types
- Sprint plan (what this page must show)
- Any wireframes or storyboards from PM

## Output

- `frontend/app/<route>/page.tsx`
- Any new components in `frontend/components/`
- Type definitions in `frontend/lib/types.ts`

## Constraints

- Pages are thin. Logic lives in hooks (`frontend/hooks/`) or API client (`frontend/lib/api.ts`).
- No hardcoded run IDs, company names, or any dynamic data in page components.
- Keep page files under 100 lines. Extract components if it grows larger.
- Desktop-first. Do not spend time on mobile layouts.

## Commit cadence

- `feat(pages): add run analysis page with stage-based layout`
- `feat(components): add budget view header component`
