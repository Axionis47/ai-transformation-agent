'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { getRun, getReport, approveReport, requestDeeperInvestigation, refineReportWithFeedback } from '@/lib/api'
import ReasoningChain from '@/components/ReasoningChain'
import ConfidenceNarrative from '@/components/ConfidenceNarrative'
import FeedbackButton from '@/components/FeedbackButton'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'
import type { Run, AdaptiveReport, ReportOpportunity, ReportFeedback } from '@/lib/types'

const TIER_BORDER: Record<string, string> = { easy: 'border-l-mint', medium: 'border-l-amber', hard: 'border-l-rose' }
const TIER_VARIANT: Record<string, 'mint' | 'amber' | 'rose'> = { easy: 'mint', medium: 'amber', hard: 'rose' }

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium print:text-black">{children}</p>
      <div className="flex-1 border-t border-edge-subtle print:border-gray-300" />
    </div>
  )
}

function OpportunityCard({ opp, onFeedback }: { opp: ReportOpportunity; onFeedback: (fb: ReportFeedback) => void }) {
  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const tier = opp.tier.toLowerCase()
  const pct = Math.round(opp.confidence * 100)
  return (
    <div className={`group bg-canvas-raised border border-edge-subtle rounded-md p-5 border-l-[3px] ${TIER_BORDER[tier] ?? 'border-l-edge'} print:break-inside-avoid print:bg-white print:border-gray-300`}>
      <div className="flex items-center gap-3 mb-2">
        <Badge variant={TIER_VARIANT[tier] ?? 'muted'}>{tier.charAt(0).toUpperCase() + tier.slice(1)}</Badge>
        <span className="font-mono text-2xs text-ink tabular">{pct}%</span>
        <div className="flex-1" />
        <FeedbackButton targetSection={`opportunity:${opp.hypothesis_id}`} onSubmit={onFeedback} />
      </div>
      <h3 className="text-lg font-semibold text-ink print:text-black">{opp.title}</h3>
      <p className="text-sm text-ink-secondary leading-relaxed mt-2 max-w-prose print:text-black">{opp.narrative}</p>
      {opp.conditions_for_success.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          <span className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium mr-1 self-center">Prerequisites</span>
          {opp.conditions_for_success.map((c, i) => (
            <span key={i} className="bg-amber/10 text-amber text-2xs font-mono px-2.5 py-1 rounded">{c}</span>
          ))}
        </div>
      )}
      {opp.risks.length > 0 && (
        <div className="mt-3 bg-rose/10 border border-rose/20 rounded-md p-3 print:bg-white print:border-gray-300">
          <p className="text-2xs text-rose uppercase tracking-wider font-medium mb-1">Risks</p>
          <ul className="space-y-1">
            {opp.risks.map((r, i) => (
              <li key={i} className="text-sm text-ink-secondary flex items-start gap-1.5 print:text-black">
                <span className="mt-1.5 w-1 h-1 bg-rose rounded-full shrink-0" />{r}
              </li>
            ))}
          </ul>
        </div>
      )}
      {opp.recommended_approach && (
        <div className="mt-3">
          <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium mb-1">Recommended Approach</p>
          <p className="text-sm text-ink-secondary leading-relaxed print:text-black">{opp.recommended_approach}</p>
        </div>
      )}
      {opp.evidence_summary && (
        <div className="mt-3">
          <button onClick={() => setEvidenceOpen(!evidenceOpen)}
            className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium flex items-center gap-1.5 hover:text-ink-secondary transition-colors print:hidden">
            <span className={`transition-transform text-[10px] ${evidenceOpen ? 'rotate-90' : ''}`}>&#9654;</span>
            Evidence
          </button>
          {evidenceOpen && (
            <p className="text-sm text-ink-secondary mt-2 border-l-2 border-edge-subtle pl-3 leading-relaxed">{opp.evidence_summary}</p>
          )}
          <p className="hidden print:block text-sm text-black mt-2 border-l-2 border-gray-300 pl-3 leading-relaxed">{opp.evidence_summary}</p>
        </div>
      )}
    </div>
  )
}

export default function ReportPage() {
  const params = useParams()
  const runId = params.id as string
  const [run, setRun] = useState<Run | null>(null)
  const [report, setReport] = useState<AdaptiveReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reviewAction, setReviewAction] = useState<string | null>(null)
  const [refining, setRefining] = useState(false)

  const load = useCallback(async () => {
    try {
      const [r, rpt] = await Promise.all([getRun(runId), getReport(runId)])
      setRun(r)
      if (rpt && typeof rpt.key_insight === 'string' && Array.isArray(rpt.opportunities)) {
        setReport(rpt as unknown as AdaptiveReport)
      }
    } catch (err) { setError(err instanceof Error ? err.message : 'Failed to load report') }
  }, [runId])

  useEffect(() => { load() }, [load])

  async function handleApprove() {
    setReviewAction('approving'); setError(null)
    try { await approveReport(runId); await load() }
    catch (err) { setError(err instanceof Error ? err.message : 'Approval failed') }
    finally { setReviewAction(null) }
  }
  async function handleInvestigate() {
    setReviewAction('investigating'); setError(null)
    try { await requestDeeperInvestigation(runId); await load() }
    catch (err) { setError(err instanceof Error ? err.message : 'Investigation request failed') }
    finally { setReviewAction(null) }
  }

  async function handleFeedback(feedback: ReportFeedback) {
    setRefining(true); setError(null)
    try {
      await refineReportWithFeedback(runId, [feedback])
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Report refinement failed')
    } finally { setRefining(false) }
  }

  const feedbackCount = run?.feedback_history?.length ?? 0

  const shell = (child: React.ReactNode) => <div className="min-h-screen bg-canvas flex items-center justify-center">{child}</div>
  if (!run && !error) return shell(<div className="flex flex-col items-center gap-3"><Spinner size={24} /><span className="text-2xs text-ink-tertiary font-mono">Loading report...</span></div>)
  if (error && !report) return shell(<p className="text-rose text-sm font-mono">{error}</p>)
  if (!report) return shell(<div className="text-center"><p className="text-ink-secondary text-sm">Report not yet generated.</p><Link href={`/run/${runId}`} className="text-mint text-2xs font-mono mt-2 inline-block hover:text-mint-bright">&larr; Back to run</Link></div>)

  const sorted = [...report.opportunities].sort((a, b) => b.confidence - a.confidence)

  return (
    <div className="min-h-screen bg-canvas print:bg-white">
      {/* Sticky header */}
      <header className="h-11 bg-canvas-raised border-b border-edge-subtle flex items-center px-5 sticky top-0 z-20 print:hidden">
        <Link href={`/run/${runId}`} className="text-2xs text-ink-tertiary hover:text-ink transition-colors font-mono">&larr; Back to Run</Link>
        <div className="w-px h-4 bg-edge mx-4" />
        <span className="text-2xs font-mono text-ink-tertiary uppercase tracking-[0.15em]">Adaptive Report</span>
        {feedbackCount > 0 && (
          <span className="ml-2"><Badge variant="indigo">Refined {feedbackCount}x</Badge></span>
        )}
        <div className="flex-1" />
        <button onClick={handleApprove} disabled={!!reviewAction}
          className="bg-mint text-ink-inverse px-4 py-1.5 text-2xs font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors">
          Approve
        </button>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8 pb-24 print:p-0 print:max-w-none">
        {error && <div className="bg-rose/10 border border-rose/20 rounded-md p-3 mb-6"><p className="text-sm text-rose font-mono">{error}</p></div>}
        {refining && (
          <div className="bg-mint/10 border border-mint/20 rounded-md p-3 mb-6 flex items-center gap-3">
            <Spinner size={14} />
            <p className="text-sm text-mint font-mono">Regenerating report...</p>
          </div>
        )}
        <section className="bg-indigo/10 border border-indigo/20 rounded-md p-6 mb-8 print:bg-white print:border-gray-300">
          <p className="text-xs text-indigo uppercase tracking-wider font-medium mb-2 print:text-black">Key Insight</p>
          <p className="text-lg font-semibold text-ink leading-snug print:text-black">{report.key_insight}</p>
        </section>
        <section className="mb-8 group">
          <div className="flex items-center gap-3 mb-3">
            <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium print:text-black">Executive Summary</p>
            <FeedbackButton targetSection="executive_summary" onSubmit={handleFeedback} />
          </div>
          <p className="text-sm text-ink leading-relaxed max-w-prose print:text-black">{report.executive_summary}</p>
        </section>
        <section className="mb-8">
          <SectionHeader>Opportunities ({sorted.length})</SectionHeader>
          <div className="space-y-4">{sorted.map((opp, i) => <OpportunityCard key={i} opp={opp} onFeedback={handleFeedback} />)}</div>
        </section>
        {report.reasoning_chain.length > 0 && (
          <section className="mb-8">
            <SectionHeader>Reasoning Chain</SectionHeader>
            <ReasoningChain steps={report.reasoning_chain} />
          </section>
        )}
        {report.what_we_dont_know.length > 0 && (
          <section className="mb-8 bg-amber/10 border border-amber/20 rounded-md p-5 group print:bg-white print:border-gray-300">
            <div className="flex items-center gap-3 mb-3">
              <p className="text-xs text-amber uppercase tracking-wider font-medium print:text-black">What We Don&apos;t Know</p>
              <FeedbackButton targetSection="unknowns" onSubmit={handleFeedback} />
            </div>
            <ul className="space-y-1.5">
              {report.what_we_dont_know.map((item, i) => (
                <li key={i} className="text-sm text-ink-secondary flex items-start gap-2 print:text-black">
                  <span className="mt-1.5 w-1.5 h-1.5 bg-amber rounded-full shrink-0" />{item}
                </li>
              ))}
            </ul>
          </section>
        )}
        {report.recommended_next_steps.length > 0 && (
          <section className="mb-8 group">
            <div className="flex items-center gap-3 mb-4">
              <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium print:text-black">Recommended Next Steps</p>
              <div className="flex-1 border-t border-edge-subtle print:border-gray-300" />
              <FeedbackButton targetSection="next_steps" onSubmit={handleFeedback} />
            </div>
            <ol className="space-y-2">
              {report.recommended_next_steps.map((step, i) => (
                <li key={i} className="flex items-start gap-3 text-sm text-ink print:text-black">
                  <span className="bg-indigo/15 text-indigo font-semibold text-xs w-6 h-6 flex items-center justify-center rounded-full shrink-0">{i + 1}</span>
                  {step}
                </li>
              ))}
            </ol>
          </section>
        )}
        <section className="mb-8 group">
          <div className="flex items-center gap-3 mb-4">
            <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium print:text-black">Confidence Assessment</p>
            <div className="flex-1 border-t border-edge-subtle print:border-gray-300" />
            <FeedbackButton targetSection="confidence" onSubmit={handleFeedback} />
          </div>
          <ConfidenceNarrative assessment={report.confidence_assessment} confidence={0} />
        </section>
      </main>
      <footer className="fixed bottom-0 left-0 right-0 bg-canvas-raised border-t border-edge-subtle px-6 py-3 flex items-center justify-end gap-3 z-20 print:hidden">
        <button onClick={handleApprove} disabled={!!reviewAction}
          className="bg-mint text-ink-inverse px-6 py-2.5 text-sm font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors flex items-center gap-2">
          {reviewAction === 'approving' ? <><Spinner size={14} />Approving...</> : 'Approve Report'}
        </button>
        <button onClick={handleInvestigate} disabled={!!reviewAction}
          className="bg-transparent border border-amber text-amber px-6 py-2.5 text-sm font-semibold rounded-md disabled:opacity-40 hover:bg-amber/10 transition-colors flex items-center gap-2">
          {reviewAction === 'investigating' ? <><Spinner size={14} />Requesting...</> : 'Investigate Deeper'}
        </button>
      </footer>
    </div>
  )
}
