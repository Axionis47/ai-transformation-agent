'use client'

import { useState } from 'react'
import type { Opportunity, EvidenceItem } from '@/lib/types'
import TierBadge from '@/components/ui/TierBadge'
import ScoreBar from '@/components/ui/ScoreBar'

interface OpportunityCardProps {
  opportunity: Opportunity
  evidence?: EvidenceItem[]
}

const TIER_BORDER: Record<string, string> = {
  easy: 'border-l-mint',
  medium: 'border-l-amber',
  hard: 'border-l-rose',
}

export default function OpportunityCard({ opportunity, evidence }: OpportunityCardProps) {
  const [expanded, setExpanded] = useState(true)
  const tier = opportunity.tier.toLowerCase()
  const border = TIER_BORDER[tier] ?? 'border-l-edge'
  const matched = (evidence ?? []).filter(e => opportunity.evidence_ids.includes(e.evidence_id))

  return (
    <div className={`bg-canvas-raised border border-edge-subtle border-l-[3px] ${border} rounded-md overflow-hidden`}>
      <div className="px-5 py-4 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h3 className="text-lg font-semibold text-ink">{opportunity.name}</h3>
            <p className="text-sm text-ink-tertiary font-mono mt-0.5">{opportunity.template_id}</p>
          </div>
          <TierBadge tier={tier} />
        </div>

        <div className="grid grid-cols-4 gap-4 mt-4">
          <ScoreBar label="Feasib." value={opportunity.feasibility} color="mint" />
          <ScoreBar label="ROI" value={opportunity.roi} color="mint" />
          <ScoreBar label="TTV" value={opportunity.time_to_value} color="amber" />
          <ScoreBar label="Confid." value={opportunity.confidence} color="indigo" />
        </div>
      </div>

      {expanded && (
        <div className="px-5 pb-5 border-t border-edge-subtle pt-4 space-y-4">
          <div>
            <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-2 font-medium">Rationale</p>
            <p className="text-base text-ink leading-relaxed max-w-prose">{opportunity.rationale}</p>
          </div>

          {opportunity.adaptation_needed && (
            <div>
              <p className="text-2xs text-amber uppercase tracking-wider mb-2 font-medium">Adaptation Needed</p>
              <p className="text-sm text-ink-secondary leading-relaxed max-w-prose">{opportunity.adaptation_needed}</p>
            </div>
          )}

          {opportunity.risks.length > 0 && (
            <div>
              <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-2 font-medium">Risks</p>
              <ul className="space-y-1.5">
                {opportunity.risks.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-ink-secondary leading-relaxed">
                    <span className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${tier === 'easy' ? 'bg-mint/50' : tier === 'medium' ? 'bg-amber/50' : 'bg-rose/50'}`} />
                    <span className="max-w-prose">{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {matched.length > 0 && (
            <div className="flex items-center gap-2 pt-2 border-t border-edge-subtle">
              <span className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium">Evidence</span>
              <div className="flex flex-wrap gap-1.5">
                {matched.map(e => (
                  <a key={e.evidence_id} href={`#ev-${e.evidence_id}`}
                     className="font-mono text-2xs text-mint hover:text-mint-bright transition-colors bg-mint/10 px-1.5 py-0.5 rounded">
                    {e.title.slice(0, 30)}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
