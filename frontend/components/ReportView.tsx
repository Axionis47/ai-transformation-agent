import type { EvidenceItem, Opportunity } from '@/lib/types'
import OpportunityRow from './OpportunityRow'
import EvidenceBlock from './EvidenceBlock'
import DataRow from './DataRow'

interface ReportViewProps {
  report: Record<string, unknown>
  opportunities: Opportunity[]
  evidence: EvidenceItem[]
  fieldCoverage?: Record<string, number>
  budgetRemaining?: { rag: number; search: number }
}

const TIER_ORDER = ['easy', 'medium', 'hard']

export default function ReportView({ report, opportunities, evidence, fieldCoverage, budgetRemaining }: ReportViewProps) {
  const brief = (report.operator_brief ?? {}) as Record<string, unknown>
  const gaps = (report.coverage_gaps ?? []) as string[]

  const sorted = [...opportunities].sort((a, b) => TIER_ORDER.indexOf(a.tier) - TIER_ORDER.indexOf(b.tier))
  const sourceTypes = new Set(evidence.map(e => e.source_type))

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <p className="text-text-muted uppercase tracking-widest mb-2" style={{ fontSize: '12px' }}>Operator Brief</p>
        {typeof brief.company_name === 'string' && <DataRow label="Company" value={brief.company_name} />}
        {typeof brief.industry === 'string' && <DataRow label="Industry" value={brief.industry} />}
        {typeof brief.analysis_confidence === 'number' && <DataRow label="Confidence" value={brief.analysis_confidence} />}
        <DataRow label="Evidence" value={`${evidence.length} items from ${sourceTypes.size} source type${sourceTypes.size !== 1 ? 's' : ''}`} />
      </div>

      {fieldCoverage && Object.keys(fieldCoverage).length > 0 && (
        <div>
          <p className="text-text-muted uppercase tracking-widest mb-2" style={{ fontSize: '12px' }}>Field Coverage</p>
          {Object.entries(fieldCoverage).map(([field, score]) => (
            <DataRow key={field} label={field.replace(/_/g, ' ')} value={(score as number).toFixed(2)} />
          ))}
        </div>
      )}

      <div>
        <p className="text-text-muted uppercase tracking-widest mb-2" style={{ fontSize: '12px' }}>Opportunities</p>
        {sorted.length === 0
          ? <p className="text-text-muted font-mono" style={{ fontSize: '13px' }}>No opportunities found.</p>
          : sorted.map((opp) => <OpportunityRow key={opp.opportunity_id} opportunity={opp} evidence={evidence} />)
        }
      </div>

      {gaps.length > 0 && (
        <div>
          <p className="text-text-muted uppercase tracking-widest mb-2" style={{ fontSize: '12px' }}>Coverage Gaps</p>
          {gaps.map((g, i) => <p key={i} className="text-text-muted font-mono" style={{ fontSize: '13px' }}>{g}</p>)}
        </div>
      )}

      {evidence.length > 0 && (
        <div>
          <p className="text-text-muted uppercase tracking-widest mb-2" style={{ fontSize: '12px' }}>Evidence Annex</p>
          <div className="space-y-2">
            {evidence.map((ev) => <EvidenceBlock key={ev.evidence_id} evidence={ev} />)}
          </div>
        </div>
      )}
    </div>
  )
}
