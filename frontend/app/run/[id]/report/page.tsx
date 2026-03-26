'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { getRun, getReport } from '@/lib/api'
import TierBadge from '@/components/ui/TierBadge'
import ScoreBar from '@/components/ui/ScoreBar'
import Spinner from '@/components/ui/Spinner'
import type { Run } from '@/lib/types'

interface ReportData {
  operator_brief: {
    company_name: string
    industry: string
    analysis_confidence: number
    opportunities_by_tier: Record<string, ReportOpp[]>
    coverage_gaps: string[]
    budget_usage: { rag_queries_used: number; external_search_queries_used: number }
  }
  evidence_annex: { evidence_id: string; source_type: string; title: string; snippet: string; uri?: string }[]
  metadata: { total_evidence_items: number; total_opportunities: number; reasoning_loops_completed: number }
}

interface ReportOpp {
  opportunity_id: string
  name: string
  description: string
  feasibility: number
  roi: number
  time_to_value: number
  confidence: number
  rationale: string
  adaptation_needed?: string
  evidence_ids: string[]
  risks: string[]
}

export default function ReportPage() {
  const params = useParams()
  const runId = params.id as string
  const [run, setRun] = useState<Run | null>(null)
  const [report, setReport] = useState<ReportData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [r, rpt] = await Promise.all([getRun(runId), getReport(runId)])
        setRun(r)
        setReport(rpt as ReportData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report')
      }
    }
    load()
  }, [runId])

  if (error) return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-rose text-sm">{error}</p>
    </div>
  )
  if (!run || !report) return (
    <div className="min-h-screen flex items-center justify-center"><Spinner size={24} /></div>
  )

  const brief = report.operator_brief
  const meta = report.metadata
  const tiers = ['easy', 'medium', 'hard'] as const

  return (
    <div className="min-h-screen bg-canvas">
      {/* Top bar */}
      <header className="h-11 bg-canvas-raised border-b border-edge-subtle flex items-center px-5 shrink-0">
        <Link href={`/run/${runId}`} className="text-2xs text-ink-tertiary hover:text-ink transition-colors font-mono">
          &larr; Analysis
        </Link>
        <div className="w-px h-4 bg-edge mx-4" />
        <span className="text-2xs font-mono text-ink-tertiary uppercase tracking-[0.15em]">Report</span>
        <div className="flex-1" />
        <span className="text-2xs text-ink-tertiary font-mono tabular">
          {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        </span>
      </header>

      <main className="max-w-5xl mx-auto p-8">
        {/* Header */}
        <div className="mb-10">
          <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium mb-2">AI Opportunity Assessment</p>
          <h1 className="text-2xl font-bold text-ink">{brief.company_name}</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-sm text-ink-secondary font-mono">{brief.industry}</span>
            <div className="w-px h-4 bg-edge" />
            <span className="text-sm text-ink-secondary font-mono">{meta.total_opportunities} opportunities</span>
            <div className="w-px h-4 bg-edge" />
            <span className="text-sm text-ink-secondary font-mono">{meta.reasoning_loops_completed} reasoning loops</span>
            <div className="w-px h-4 bg-edge" />
            <span className="text-sm font-mono tabular text-mint">{(brief.analysis_confidence * 100).toFixed(0)}% understanding</span>
          </div>
        </div>

        {/* Opportunities by tier */}
        {tiers.map(tier => {
          const opps = brief.opportunities_by_tier[tier] || []
          if (opps.length === 0) return null
          return (
            <section key={tier} className="mb-8">
              <div className="flex items-center gap-3 mb-4">
                <TierBadge tier={tier} />
                <span className="text-2xs text-ink-tertiary font-mono">{opps.length} {opps.length === 1 ? 'opportunity' : 'opportunities'}</span>
                <div className="flex-1 border-t border-edge-subtle" />
              </div>
              <div className="space-y-4">
                {opps.map(opp => (
                  <div key={opp.opportunity_id} className="bg-canvas-raised border border-edge-subtle rounded p-5">
                    <h3 className="text-lg font-semibold text-ink mb-1">{opp.name}</h3>
                    <p className="text-sm text-ink-secondary mb-4 max-w-prose">{opp.description}</p>

                    <div className="grid grid-cols-4 gap-4 mb-4">
                      {opp.feasibility > 0 && <ScoreBar label="Feasibility" value={opp.feasibility} color="mint" />}
                      {opp.roi > 0 && <ScoreBar label="ROI" value={opp.roi} color="mint" />}
                      {opp.time_to_value > 0 && <ScoreBar label="Time to Value" value={opp.time_to_value} color="amber" />}
                      {opp.confidence > 0 && <ScoreBar label="Confidence" value={opp.confidence} color="indigo" />}
                    </div>

                    <p className="text-base text-ink leading-relaxed max-w-prose mb-3">{opp.rationale}</p>

                    {opp.adaptation_needed && (
                      <div className="mb-3">
                        <span className="text-2xs text-amber uppercase tracking-wider font-medium">Adaptation: </span>
                        <span className="text-sm text-ink-secondary">{opp.adaptation_needed}</span>
                      </div>
                    )}

                    {opp.risks.length > 0 && (
                      <div>
                        <span className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium">Risks: </span>
                        <span className="text-sm text-ink-secondary">{opp.risks.join(' · ')}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )
        })}

        {/* Coverage Gaps */}
        {brief.coverage_gaps.length > 0 && (
          <section className="mb-8">
            <div className="flex items-center gap-3 mb-4">
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

        {/* Evidence Annex */}
        <section className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium">Evidence Annex</p>
            <span className="text-2xs text-ink-tertiary font-mono">{report.evidence_annex.length} items</span>
            <div className="flex-1 border-t border-edge-subtle" />
          </div>
          <div className="space-y-2">
            {report.evidence_annex.map(ev => (
              <div key={ev.evidence_id} className="bg-canvas-raised border border-edge-subtle rounded p-3 flex gap-3">
                <span className="text-2xs font-mono text-ink-tertiary uppercase shrink-0 w-20">{ev.source_type.replace(/_/g, ' ')}</span>
                <div className="min-w-0">
                  <p className="text-sm text-ink font-medium truncate">{ev.title}</p>
                  <p className="text-2xs text-ink-secondary mt-0.5 line-clamp-2">{ev.snippet}</p>
                  {ev.uri && <a href={ev.uri} target="_blank" rel="noopener" className="text-2xs text-mint hover:text-mint-bright font-mono mt-1 block truncate">{ev.uri}</a>}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Budget Usage */}
        <section className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium">Budget Usage</p>
            <div className="flex-1 border-t border-edge-subtle" />
          </div>
          <div className="flex gap-6">
            <div>
              <span className="text-2xs text-ink-tertiary">RAG Queries</span>
              <p className="text-lg font-mono text-ink tabular">{brief.budget_usage.rag_queries_used}</p>
            </div>
            <div>
              <span className="text-2xs text-ink-tertiary">Search Queries</span>
              <p className="text-lg font-mono text-ink tabular">{brief.budget_usage.external_search_queries_used}</p>
            </div>
            <div>
              <span className="text-2xs text-ink-tertiary">Reasoning Loops</span>
              <p className="text-lg font-mono text-ink tabular">{meta.reasoning_loops_completed}</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
