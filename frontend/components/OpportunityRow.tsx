import type { Opportunity, EvidenceItem } from '@/lib/types'

interface OpportunityRowProps {
  opportunity: Opportunity
  evidence?: EvidenceItem[]
}

const TIER_COLORS: Record<string, string> = {
  easy: 'border-tier-easy',
  medium: 'border-tier-medium',
  hard: 'border-tier-hard',
}

const TIER_TEXT: Record<string, string> = {
  easy: 'text-tier-easy',
  medium: 'text-tier-medium',
  hard: 'text-tier-hard',
}

export default function OpportunityRow({ opportunity, evidence }: OpportunityRowProps) {
  const tier = opportunity.tier.toLowerCase()
  const borderColor = TIER_COLORS[tier] ?? 'border-border'
  const textColor = TIER_TEXT[tier] ?? 'text-text-muted'

  return (
    <div className={`border-l-[3px] ${borderColor} pl-3 py-3 bg-surface border border-l-[3px] border-border mb-2`}>
      <div className="flex justify-between items-start mb-1">
        <p className="text-text-primary" style={{ fontSize: '14px', fontWeight: 500 }}>{opportunity.name}</p>
        <span className={`font-mono uppercase ${textColor}`} style={{ fontSize: '12px' }}>{opportunity.tier}</span>
      </div>
      <p className="text-text-muted font-mono mb-2" style={{ fontSize: '12px' }}>{opportunity.template_id}</p>
      <div className="flex gap-4 mb-2">
        {[['FEASIBILITY', opportunity.feasibility], ['ROI', opportunity.roi], ['TTV', opportunity.time_to_value], ['CONFIDENCE', opportunity.confidence]].map(([label, val]) => (
          <span key={label as string} className="font-mono text-text-primary" style={{ fontSize: '13px' }}>
            <span className="text-text-muted" style={{ fontSize: '11px' }}>{label} </span>
            {(val as number).toFixed(2)}
          </span>
        ))}
      </div>
      <div className="border-t border-border pt-2 mb-2">
        <p className="text-text-primary" style={{ fontSize: '14px' }}>{opportunity.rationale}</p>
      </div>
      <div className="flex gap-3">
        <span className="text-text-muted font-mono" style={{ fontSize: '12px' }}>
          Evidence: {opportunity.evidence_ids.map((id) => (
            <a key={id} href={`#${id}`} className="text-accent cursor-pointer hover:underline mr-1">[{id.slice(0, 8)}]</a>
          ))}
        </span>
      </div>
      {opportunity.adaptation_needed && (
        <p className="text-text-muted font-mono mt-1" style={{ fontSize: '12px' }}>Adaptation: {opportunity.adaptation_needed}</p>
      )}
    </div>
  )
}
