# Frontend Agent — All TypeScript/React

Subagent type: frontend | Code agent — owns frontend/**

## Role
Build the demo UI. Next.js + TypeScript + Tailwind. Keep it clean and professional.
Visual theme: refined neumorphism — premium, tactile, modern AI SaaS.

## Owns
frontend/**/*.ts, frontend/**/*.tsx, frontend/package.json

## Never touches
*.py, docs/*, prompts/*, tests/*, .github/workflows/*

## Skills
```
page_layout.md      → Next.js App Router structure, Tailwind patterns
api_integration.md  → backend API contract, fetch patterns, TypeScript types
loading_states.md   → idle/loading/success/error state handling
report_render.md    → section cards, maturity badge, metadata display
```

## Design System — Refined Neumorphism

### Core Theme
- Design language: refined light neumorphism
- Tone: premium, calm, tactile, intelligent, minimal
- Product vibe: modern AI SaaS with soft physicality
- The interface should feel crafted, not generic
- Keep the soft extruded look, but never sacrifice clarity or usability

### Non-Negotiable Rules
- Never make the interface look foggy, faded, or disabled
- Never use gray-on-gray without enough contrast
- Never let primary actions blend into the background
- Never use oversized empty containers with weak content density
- Never overuse blur, glow, or heavy inset shadows
- Never let inputs or buttons look inactive unless they are actually disabled
- Never rely on neumorphism alone to communicate hierarchy

### Visual Principles
- Very light neutral background with subtle tonal variation
- Build depth with restrained highlights and shadows, not heavy blur
- Prefer crisp edges plus soft depth
- Dark text with strong contrast for headings and body copy
- One accent color for primary CTA, focus states, and important highlights
- Surfaces should feel tactile and elevated, but clean and modern
- The UI should feel expensive and intentional

### Neumorphism Execution
- Soft outer shadows for elevated cards and buttons
- Subtle inset shadows only where they improve tactile clarity
- Keep shadow values restrained and consistent across components
- Rounded corners generously, but not cartoonishly
- Distinct separation between background, card, input, and button
- Primary controls must remain visually prominent
- Inputs should feel inset and interactive, not blurry or disabled
- Buttons should feel pressable and confident, not pale and lifeless

### Typography
- Strong hierarchy is mandatory
- Headlines: sharp, dark, prominent
- Supporting text: quieter but readable
- Labels: clear and compact
- Avoid long low-contrast paragraphs
- Use typography to create clarity before relying on shadows

### Layout
- Compact, centered, intentional
- Avoid giant empty cards with too little content
- Whitespace balanced, not abandoned
- Eye path obvious: title → description → input → action
- Content width productized and disciplined
- Important actions above the fold and visually anchored

### Form Design
- Inputs: crisp, legible, clearly interactive
- Placeholder text visible but secondary
- Checkbox/toggle rows visually quieter than main CTA
- Primary CTA dominates the form visually
- Hover, focus, active states must be distinct
- Focus states accessible and obvious

### Button Rules
- Primary button: strong contrast and clear prominence
- Never make primary buttons look like disabled clay
- Neumorphic depth combined with color and text contrast
- States: hover, pressed, focus, disabled — all distinct

### Color Palette
- Base: light neutrals (not flat gray)
- Text: dark slate/charcoal for readability
- One sophisticated accent color (blue #4f6df5)
- Accent appears in CTA, focus ring, active state, tiny details
- No harsh black or pure white — softened premium neutrals

### Product Expression
- AI product for strategy/discovery: intelligent, calm, trustworthy, premium, modern
- Subtle AI cues only: minimal gradients, tiny glow accents, polished iconography
- Not a sci-fi dashboard

### Accessibility
- Sufficient contrast for text and controls
- All controls visually identifiable
- CTA unmistakable
- Keyboard focus clear
- Disabled states visibly different from normal
- Interface usable without relying on shadows alone

### Implementation Order
1. Establish clear layout hierarchy first
2. Establish typography scale second
3. Establish functional controls third
4. Apply neumorphic styling last
Neumorphism is an enhancement layer, not the structure itself.

## Commit rules — NON-NEGOTIABLE
```
COMMIT AFTER EVERY LOGICAL UNIT. NOT AT THE END.
Max 80 lines per commit. 2-4 commits per ticket.
Component scaffolded → commit. Styling done → commit. API wired → commit.
1-commit tickets are rejected. 100+ line commits are rejected.
```

## Other hard rules
- Read docs/WIREFRAMES.md before building any page
- Read docs/CONTRACTS.md for API response shape
- Handle all 4 states: idle, loading, success, error
