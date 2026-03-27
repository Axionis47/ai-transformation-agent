'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { getRun, getReport, refineReport, approveReport, requestDeeperInvestigation } from '@/lib/api'
import AdaptiveReportView from '@/components/AdaptiveReportView'
import TierBadge from '@/components/ui/TierBadge'
import ScoreBar from '@/components/ui/ScoreBar'
import Spinner from '@/components/ui/Spinner'
import Badge from '@/components/ui/Badge'
import type { Run, AdaptiveReport } from '@/lib/types'

interface ReportData {
  operator_brief: {
    company_name: string; industry: string; employee_count_band?: string; notes?: string
    analysis_confidence: number
    opportunities_by_tier: Record<string, ReportOpp[]>
    coverage_gaps: string[]
    field_coverage: Record<string, number>
    assumptions: { field: string; value: string; confidence: number; source: string }[]
    budget_usage: { rag_queries_used: number; external_search_queries_used: number }
  }
  evidence_annex: { evidence_id: string; source_type: string; title: string; snippet: string; uri?: string; relevance_score: number; cited_by_opportunities: string[] }[]
  metadata: { total_evidence_items: number; total_opportunities: number; reasoning_loops_completed: number; refinement_count: number }
}

interface ReportOpp {
  opportunity_id: string; name: string; description: string
  feasibility: number; roi: number; time_to_value: number; confidence: number
  rationale: string; adaptation_needed?: string; evidence_ids: string[]; risks: string[]
  data_sufficiency?: string
}

function isAdaptiveReport(data: Record<string, unknown>): data is Record<string, unknown> & AdaptiveReport {
  return typeof data.executive_summary === 'string' && typeof data.key_insight === 'string' && Array.isArray(data.opportunities)
}

export default function ReportPage() {
  const params = useParams()
  const runId = params.id as string
  const [run, setRun] = useState<Run | null>(null)
  const [report, setReport] = useState<ReportData | null>(null)
  const [adaptiveReport, setAdaptiveReport] = useState<AdaptiveReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [refining, setRefining] = useState(false)
  const [reviewAction, setReviewAction] = useState<string | null>(null)
  const [context, setContext] = useState('')
  const [removedIds, setRemovedIds] = useState<Set<string>>(new Set())
  const [editingAssumption, setEditingAssumption] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [corrections, setCorrections] = useState<{ field: string; new_value: string }[]>([])

  const load = useCallback(async () => {
    try {
      const [r, rpt] = await Promise.all([getRun(runId), getReport(runId)])
      setRun(r)
      if (isAdaptiveReport(rpt)) {
        setAdaptiveReport(rpt as unknown as AdaptiveReport)
      } else {
        setReport(rpt as unknown as ReportData)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report')
    }
  }, [runId])

  useEffect(() => { load() }, [load])

  async function handleRefine() {
    setRefining(true); setError(null)
    try {
      await refineReport(runId, {
        corrections: corrections.length > 0 ? corrections : undefined,
        removed_opportunity_ids: removedIds.size > 0 ? Array.from(removedIds) : undefined,
        additional_context: context.trim() || undefined,
      })
      setCorrections([]); setRemovedIds(new Set()); setContext('')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Refinement failed')
    } finally { setRefining(false) }
  }

  async function handleApprove() {
    setReviewAction('approving'); setError(null)
    try {
      await approveReport(runId)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approval failed')
    } finally { setReviewAction(null) }
  }

  async function handleInvestigate() {
    setReviewAction('investigating'); setError(null)
    try {
      await requestDeeperInvestigation(runId)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Investigation request failed')
    } finally { setReviewAction(null) }
  }

  function startEdit(field: string, value: string) {
    setEditingAssumption(field); setEditValue(value)
  }
  function saveEdit(field: string) {
    setCorrections(prev => [...prev.filter(c => c.field !== field), { field, new_value: editValue }])
    setEditingAssumption(null)
  }

  const hasPendingChanges = corrections.length > 0 || removedIds.size > 0 || context.trim().length > 0

  if (error && !report && !adaptiveReport) return <div className="min-h-screen flex items-center justify-center"><p className="text-rose text-sm">{error}</p></div>
  if (!run || (!report && !adaptiveReport)) return <div className="min-h-screen flex items-center justify-center"><Spinner size={24} /></div>

  // Adaptive report: render AdaptiveReportView with review actions
  if (adaptiveReport) {
    return (
      <div className="min-h-screen bg-canvas">
        <header className="h-11 bg-canvas-raised border-b border-edge-subtle flex items-center px-5 shrink-0 sticky top-0 z-20">
          <Link href={`/run/${runId}`} className="text-2xs text-ink-tertiary hover:text-ink transition-colors font-mono">&larr; Analysis</Link>
          <div className="w-px h-4 bg-edge mx-4" />
          <span className="text-2xs font-mono text-ink-tertiary uppercase tracking-[0.15em]">Adaptive Report</span>
          <div className="flex-1" />
        </header>
        <main className="max-w-5xl mx-auto p-6 lg:p-8">
          {error && <div className="bg-rose/10 border border-rose/20 rounded p-3 mb-6"><p className="text-sm text-rose font-mono">{error}</p></div>}
          <AdaptiveReportView report={adaptiveReport} />
          <section className="mt-8 border-t border-edge-subtle pt-6 flex items-center gap-4">
            <button onClick={handleApprove} disabled={!!reviewAction}
              className="bg-mint text-ink-inverse px-6 py-2.5 text-sm font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors flex items-center gap-2">
              {reviewAction === 'approving' ? <><Spinner size={14} />Approving...</> : 'Approve Report'}
            </button>
            <button onClick={handleInvestigate} disabled={!!reviewAction}
              className="bg-canvas-raised border border-edge-subtle text-ink px-6 py-2.5 text-sm font-semibold rounded-md disabled:opacity-40 hover:border-amber hover:text-amber transition-colors flex items-center gap-2">
              {reviewAction === 'investigating' ? <><Spinner size={14} />Requesting...</> : 'Investigate Deeper'}
            </button>
          </section>
        </main>
      </div>
    )
  }

  // Legacy report: fall through to existing rendering
  // report is guaranteed non-null here (early return + adaptive guard above)
  const brief = report!.operator_brief
  const meta = report!.metadata
  const tiers = ['easy', 'medium', 'hard'] as const

  return (
    <div className="min-h-screen bg-canvas">
      <header className="h-11 bg-canvas-raised border-b border-edge-subtle flex items-center px-5 shrink-0 sticky top-0 z-20">
        <Link href={`/run/${runId}`} className="text-2xs text-ink-tertiary hover:text-ink transition-colors font-mono">&larr; Analysis</Link>
        <div className="w-px h-4 bg-edge mx-4" />
        <span className="text-2xs font-mono text-ink-tertiary uppercase tracking-[0.15em]">Report</span>
        {meta.refinement_count > 0 && <Badge variant="mint">v{meta.refinement_count + 1}</Badge>}
        <div className="flex-1" />
        {hasPendingChanges && (
          <button onClick={handleRefine} disabled={refining}
            className="bg-mint text-ink-inverse px-4 py-1.5 text-2xs font-semibold rounded disabled:opacity-40 hover:bg-mint-bright transition-colors flex items-center gap-2">
            {refining ? <><Spinner size={12} />Refining...</> : 'Apply Changes'}
          </button>
        )}
      </header>

      <main className="max-w-5xl mx-auto p-6 lg:p-8">
        {error && <div className="bg-rose/10 border border-rose/20 rounded p-3 mb-6"><p className="text-sm text-rose font-mono">{error}</p></div>}

        {/* ── Executive Header ── */}
        <section className="mb-8 border border-edge-subtle rounded bg-canvas-raised p-6">
          <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium mb-3">AI Opportunity Assessment</p>
          <h1 className="text-2xl font-bold text-ink mb-1">{brief.company_name}</h1>
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <Badge>{brief.industry}</Badge>
            {brief.employee_count_band && <Badge variant="muted">{brief.employee_count_band}</Badge>}
            <span className="text-sm font-mono tabular text-mint">{(brief.analysis_confidence * 100).toFixed(0)}% understanding</span>
            <span className="text-2xs text-ink-tertiary font-mono">{meta.total_opportunities} opportunities · {meta.total_evidence_items} evidence items · {meta.reasoning_loops_completed} loops</span>
          </div>
          {brief.notes && <p className="text-sm text-ink-secondary mt-3 border-l-2 border-edge pl-3">{brief.notes}</p>}
        </section>

        {/* ── Field Coverage ── */}
        {Object.keys(brief.field_coverage).length > 0 && (
          <section className="mb-8 border border-edge-subtle rounded bg-canvas-raised p-5">
            <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium mb-3">Field Coverage</p>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-2">
              {Object.entries(brief.field_coverage).map(([field, score]) => (
                <ScoreBar key={field} label={field.replace(/_/g, ' ')} value={score}
                  color={score > 0.6 ? 'mint' : score > 0.3 ? 'amber' : 'rose'} />
              ))}
            </div>
          </section>
        )}

        {/* ── Assumptions (editable) ── */}
        {brief.assumptions.length > 0 && (
          <section className="mb-8 border border-edge-subtle rounded bg-canvas-raised">
            <div className="px-5 py-3 border-b border-edge-subtle flex items-center justify-between">
              <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium">Assumptions</p>
              <span className="text-2xs text-ink-tertiary">Click to correct</span>
            </div>
            <div className="divide-y divide-edge-subtle">
              {brief.assumptions.map(a => {
                const corrected = corrections.find(c => c.field === a.field)
                const isEditing = editingAssumption === a.field
                const displayValue = corrected ? corrected.new_value : a.value
                return (
                  <div key={a.field} className="px-5 py-3 flex items-start gap-4">
                    <div className="w-32 shrink-0">
                      <span className="text-2xs text-ink-tertiary uppercase tracking-wider">{a.field.replace(/_/g, ' ')}</span>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <Badge variant={a.confidence >= 0.8 ? 'mint' : a.confidence >= 0.5 ? 'muted' : 'rose'}>
                          {(a.confidence * 100).toFixed(0)}%
                        </Badge>
                        <span className="text-2xs text-ink-tertiary font-mono">{a.source}</span>
                      </div>
                    </div>
                    <div className="flex-1">
                      {isEditing ? (
                        <div className="flex gap-2">
                          <input type="text" value={editValue} onChange={e => setEditValue(e.target.value)}
                            className="flex-1 bg-canvas-inset border border-edge text-ink text-sm p-2 rounded font-mono focus:border-mint focus:outline-none" />
                          <button onClick={() => saveEdit(a.field)} className="text-2xs text-mint font-medium hover:text-mint-bright">Save</button>
                          <button onClick={() => setEditingAssumption(null)} className="text-2xs text-ink-tertiary hover:text-ink-secondary">Cancel</button>
                        </div>
                      ) : (
                        <p className={`text-sm text-ink cursor-pointer hover:text-mint transition-colors ${corrected ? 'text-mint' : ''}`}
                          onClick={() => startEdit(a.field, displayValue)}>
                          {displayValue}
                          {corrected && <span className="text-2xs text-mint ml-2">(corrected)</span>}
                        </p>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        )}

        {/* ── Opportunities by Tier ── */}
        {tiers.map(tier => {
          const opps = (brief.opportunities_by_tier[tier] || []).filter(o => !removedIds.has(o.opportunity_id))
          if (opps.length === 0) return null
          return (
            <section key={tier} className="mb-8">
              <div className="flex items-center gap-3 mb-4">
                <TierBadge tier={tier} />
                <span className="text-2xs text-ink-tertiary font-mono">{opps.length}</span>
                <div className="flex-1 border-t border-edge-subtle" />
              </div>
              <div className="space-y-4">
                {opps.map(opp => (
                  <div key={opp.opportunity_id} className="bg-canvas-raised border border-edge-subtle rounded p-5 group">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="text-lg font-semibold text-ink">{opp.name}</h3>
                        <p className="text-sm text-ink-secondary mt-1 max-w-prose">{opp.description}</p>
                      </div>
                      <button onClick={() => setRemovedIds(prev => new Set(prev).add(opp.opportunity_id))}
                        className="text-2xs text-ink-tertiary hover:text-rose transition-colors opacity-0 group-hover:opacity-100 shrink-0">
                        Remove
                      </button>
                    </div>
                    <div className="grid grid-cols-4 gap-4 my-4">
                      {opp.feasibility > 0 && <ScoreBar label="Feasibility" value={opp.feasibility} color="mint" />}
                      {opp.roi > 0 && <ScoreBar label="ROI" value={opp.roi} color="mint" />}
                      {opp.time_to_value > 0 && <ScoreBar label="Time to Value" value={opp.time_to_value} color="amber" />}
                      {opp.confidence > 0 && <ScoreBar label="Confidence" value={opp.confidence} color="indigo" />}
                    </div>
                    {opp.data_sufficiency === 'insufficient_data' && (
                      <span className="text-2xs font-mono bg-amber/10 text-amber px-2 py-0.5 rounded uppercase">Insufficient Data</span>
                    )}
                    <p className="text-base text-ink leading-relaxed max-w-prose mt-2">{opp.rationale}</p>
                    {opp.adaptation_needed && (
                      <p className="text-sm text-ink-secondary mt-2"><span className="text-2xs text-amber uppercase font-medium">Adaptation: </span>{opp.adaptation_needed}</p>
                    )}
                    {opp.risks.length > 0 && (
                      <p className="text-sm text-ink-secondary mt-2"><span className="text-2xs text-ink-tertiary uppercase font-medium">Risks: </span>{opp.risks.join(' · ')}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )
        })}

        {/* ── Additional Context ── */}
        <section className="mb-8 border border-edge-subtle rounded bg-canvas-raised p-5">
          <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium mb-2">Add Context</p>
          <p className="text-2xs text-ink-tertiary mb-3">Provide corrections, missing details, or strategic context to improve recommendations.</p>
          <textarea value={context} onChange={e => setContext(e.target.value)} rows={3}
            className="w-full bg-canvas-inset border border-edge text-ink text-sm p-3 rounded font-mono focus:border-mint focus:outline-none resize-none"
            placeholder="e.g. We already have a data platform team. Focus on customer-facing automation..." />
        </section>

        {/* ── Coverage Gaps ── */}
        {brief.coverage_gaps.length > 0 && (
          <section className="mb-8">
            <div className="flex items-center gap-3 mb-3">
              <p className="text-2xs text-amber uppercase tracking-wider font-medium">Coverage Gaps</p>
              <div className="flex-1 border-t border-edge-subtle" />
            </div>
            <div className="flex flex-wrap gap-2">
              {brief.coverage_gaps.map(g => (
                <span key={g} className="text-2xs font-mono bg-amber/10 text-amber px-2.5 py-1 rounded">{g.replace(/_/g, ' ')}</span>
              ))}
            </div>
          </section>
        )}

        {/* ── Evidence Annex ── */}
        <section className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium">Evidence Annex</p>
            <span className="text-2xs text-ink-tertiary font-mono">{report!.evidence_annex.length}</span>
            <div className="flex-1 border-t border-edge-subtle" />
          </div>
          <div className="space-y-2">
            {report!.evidence_annex.map(ev => (
              <div key={ev.evidence_id} className="bg-canvas-raised border border-edge-subtle rounded p-3">
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-2xs font-mono text-ink-tertiary uppercase">{ev.source_type.replace(/_/g, ' ')}</span>
                  <span className="text-2xs font-mono text-mint tabular">{(ev.relevance_score * 100).toFixed(0)}%</span>
                  {ev.cited_by_opportunities.length > 0 && (
                    <div className="flex gap-1">
                      {ev.cited_by_opportunities.map(name => (
                        <span key={name} className="text-2xs bg-canvas-overlay text-ink-secondary px-1.5 py-0.5 rounded">{name.slice(0, 20)}</span>
                      ))}
                    </div>
                  )}
                </div>
                <p className="text-sm text-ink font-medium">{ev.title}</p>
                <p className="text-2xs text-ink-secondary mt-0.5">{ev.snippet}</p>
                {ev.uri && <a href={ev.uri} target="_blank" rel="noopener" className="text-2xs text-mint hover:text-mint-bright font-mono mt-1 block truncate">{ev.uri}</a>}
              </div>
            ))}
          </div>
        </section>

        {/* ── Budget ── */}
        <section className="mb-8 flex gap-6">
          <div><span className="text-2xs text-ink-tertiary block">RAG Queries</span><p className="text-lg font-mono text-ink tabular">{brief.budget_usage.rag_queries_used}</p></div>
          <div><span className="text-2xs text-ink-tertiary block">Search Queries</span><p className="text-lg font-mono text-ink tabular">{brief.budget_usage.external_search_queries_used}</p></div>
          <div><span className="text-2xs text-ink-tertiary block">Reasoning Loops</span><p className="text-lg font-mono text-ink tabular">{meta.reasoning_loops_completed}</p></div>
          {meta.refinement_count > 0 && <div><span className="text-2xs text-ink-tertiary block">Refinements</span><p className="text-lg font-mono text-mint tabular">{meta.refinement_count}</p></div>}
        </section>

        {/* ── Sticky refine bar ── */}
        {hasPendingChanges && (
          <div className="fixed bottom-0 left-0 right-0 bg-canvas-raised border-t border-edge-subtle p-4 flex items-center justify-between z-30">
            <span className="text-sm text-ink-secondary">
              {corrections.length > 0 && `${corrections.length} correction${corrections.length > 1 ? 's' : ''}`}
              {corrections.length > 0 && removedIds.size > 0 && ' · '}
              {removedIds.size > 0 && `${removedIds.size} removed`}
              {(corrections.length > 0 || removedIds.size > 0) && context.trim() && ' · '}
              {context.trim() && 'additional context'}
            </span>
            <button onClick={handleRefine} disabled={refining}
              className="bg-mint text-ink-inverse px-6 py-2 text-sm font-semibold rounded disabled:opacity-40 hover:bg-mint-bright transition-colors flex items-center gap-2">
              {refining ? <><Spinner size={14} />Refining...</> : 'Apply Changes & Regenerate'}
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
