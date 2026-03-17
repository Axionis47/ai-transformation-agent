# Skill: Page Layout

Load when: building pages in the Next.js app.

## Stack

- Next.js App Router (app/ directory)
- TypeScript
- Tailwind CSS with custom neumorphic design tokens
- No external UI library — keep it lightweight

## Page structure

```
app/
  layout.tsx       ← root layout with persistent header, Inter font
  page.tsx         ← landing page with hero + input form
  globals.css      ← Tailwind imports + neumorphic utility classes
```

## Design Tokens (tailwind.config.ts)

```typescript
colors: {
  neo: {
    bg: "#e8ecf1",       // Base background
    surface: "#edf1f5",  // Card surface (slight lift)
    dark: "#bec8d4",     // Shadow dark side
    light: "#ffffff",    // Shadow light side
    text: "#1e293b",     // Primary text (slate-800)
    muted: "#64748b",    // Secondary text (slate-500)
  },
  accent: {
    DEFAULT: "#4f6df5",  // Primary blue
    hover: "#3b5de7",    // Hover state
    light: "#e8ecff",    // Subtle accent bg
  }
}
```

## Shadow System

```
neo-raised   → cards, containers (prominent lift)
neo-flat     → subtle elements (light lift)
neo-inset    → inputs, wells (pressed in)
neo-btn      → buttons at rest (pressable)
neo-btn-pressed → buttons when active
```

## Layout Rules

- Max content width: 4xl (896px) centered
- Background: neo-bg with subtle tonal variation
- Persistent header with branding
- Main content area with balanced padding
- Typography hierarchy established before shadows applied
- Compact, intentional whitespace — never abandoned or excessive

## Implementation Order

1. Layout hierarchy (header, main, sections)
2. Typography scale (headings, body, labels)
3. Functional controls (inputs, buttons)
4. Neumorphic enhancement (shadows, depth)
