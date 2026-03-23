# Skill: Evidence Panel

Build the evidence/abstraction/confidence views and the 3-tier recommendation display.

## When to load

Load this skill when: building the evidence panel component, building the 3-tier recommendations view, or displaying confidence scores and source types.

---

## Steps

1. Read `core/schemas.py` for these types: `EvidenceItem`, `EvidenceSource`, `Opportunity`, `OpportunityTier`, `SectionConfidence`, `FieldConfidence`.
2. Evidence panel layout — three columns, never blended:
   - Column 1: Evidence — list of `EvidenceItem` objects. Each row shows: source type badge (WINS_KB | GOOGLE_SEARCH | USER_PROVIDED), snippet, title, URI link (if available), relevance_score as a 0-1 bar.
   - Column 2: Abstraction — the model's interpretation of the evidence. This comes from the thought engine's output, not from raw evidence. It is the reasoning layer.
   - Column 3: Confidence — `SectionConfidence` breakdown. Show each field's `evidence_coverage`, `evidence_strength`, `source_diversity`. Missing fields are shown as gaps with a red indicator.
3. Source type badges:
   - WINS_KB: blue badge "Past Win"
   - GOOGLE_SEARCH: green badge "Web"
   - USER_PROVIDED: grey badge "You"
4. 3-tier recommendations display:
   - Easy tier: green section header. "Proven — direct match to past engagement."
   - Medium tier: yellow section header. "Adaptable — similar past win, needs modification."
   - Hard tier: red section header. "Ambitious — novel application, low evidence."
   - Each opportunity card: name, description, tier badge, feasibility/roi/time-to-value/confidence as four score bars, expandable section showing evidence links and rationale.
   - Medium tier cards must show `adaptation_needed` text. Hard tier cards must show `risks` list.
5. ROI sensitivity: for each opportunity, show the key assumptions as editable fields. When the user changes a value, call `PUT /v1/runs/{id}/assumptions` and re-fetch the opportunity.
6. Budget dashboard: always visible in the page header. Show `rag_queries_remaining` and `external_search_queries_remaining` as progress bars depleting from full to empty.

---

## Input

- `core/schemas.py` Python types translated to TypeScript in `frontend/lib/types.ts`
- Sprint 5 plan (pitch synthesis output shapes)

## Output

- `frontend/components/EvidencePanel.tsx` — three-column evidence view
- `frontend/components/OpportunityCard.tsx` — individual opportunity with scores
- `frontend/components/RecommendationsView.tsx` — 3-tier grouped display
- `frontend/components/BudgetDashboard.tsx` — budget remaining indicator

## Constraints

- Evidence, abstraction, and confidence are always in separate columns. Never merge them.
- Opportunity tiers must be visually distinct. Color is not enough — use section labels.
- Missing evidence fields (from `missing_fields`) must be clearly marked as gaps, not hidden.
- Score bars are visual only. Do not show raw float values next to bars — round to a descriptive label (High / Medium / Low).
- Easy tier opportunities must cite the specific past engagement from the wins KB.

## Commit cadence

- `feat(evidence-panel): add three-column evidence abstraction confidence layout`
- `feat(recommendations): add 3-tier opportunity cards with score breakdowns`
- `feat(budget): add budget dashboard with depleting progress bars`
