'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { getRun, getReport, getEvidence, approveReport, requestDeeperInvestigation, refineReportWithFeedback } from '@/lib/api'
import ReasoningChain from '@/components/ReasoningChain'
import ConfidenceNarrative from '@/components/ConfidenceNarrative'
import EvidenceAnnex from '@/components/EvidenceAnnex'
import FeedbackButton from '@/components/FeedbackButton'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'
import type { Run, AdaptiveReport, ReportOpportunity, ReportFeedback, EvidenceItem } from '@/lib/types'

const TIER_BORDER: Record<string, string> = { easy: 'border-l-mint', medium: 'border-l-amber', hard: 'border-l-rose' }
const TIER_VARIANT: Record<string, 'mint' | 'amber' | 'rose'> = { easy: 'mint', medium: 'amber', hard: 'rose' }
const TIER_LABEL: Record<string, string> = { easy: 'Quick Win', medium: 'Strategic Initiative', hard: 'Transformation' }
const TIER_TIMELINE: Record<string, string> = { easy: '4-6 weeks', medium: '2-3 months', hard: '6+ months' }

function SectionHeader({ children, action }: { children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium print:text-black">{children}</p>
      <div className="flex-1 border-t border-edge-subtle print:border-gray-300" />
      {action}
    </div>
  )
}

function OpportunityCard({ opp, onFeedback, highlighted, isStartingPoint, defaultOpen }: {
  opp: ReportOpportunity; onFeedback: (fb: ReportFeedback) => void;
  highlighted?: boolean; isStartingPoint?: boolean; defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen ?? false)
  const tier = opp.tier.toLowerCase()
  const pct = Math.round(opp.confidence * 100)
  const hasDetails = opp.conditions_for_success.length > 0 || opp.risks.length > 0 || opp.recommended_approach || opp.evidence_summary

  return (
    <div className={`group bg-canvas-raised border border-edge-subtle rounded-md border-l-[3px] ${TIER_BORDER[tier] ?? 'border-l-edge'} print:break-inside-avoid print:bg-white print:border-gray-300 transition-all duration-500 ${highlighted ? 'ring-1 ring-mint/40 bg-mint/5' : ''}`}>
      {/* Clickable header */}
      <div className="p-5 cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="flex items-center gap-3 mb-2">
          {isStartingPoint && (
            <span className="inline-flex items-center gap-1 bg-mint/15 text-mint text-2xs font-semibold px-2 py-0.5 rounded-full">
              <span className="w-1 h-1 bg-mint rounded-full" />Start Here
            </span>
          )}
          <Badge variant={TIER_VARIANT[tier] ?? 'muted'}>{TIER_LABEL[tier] ?? tier}</Badge>
          <span className="font-mono text-2xs text-ink-tertiary">{TIER_TIMELINE[tier]}</span>
          <div className="flex-1" />
          <span className="font-mono text-sm text-ink tabular">{pct}%</span>
          {hasDetails && (
            <span className={`text-ink-tertiary text-xs transition-transform ${open ? 'rotate-90' : ''}`}>&#9654;</span>
          )}
        </div>
        <h3 className="text-base font-semibold text-ink print:text-black leading-snug">{opp.title}</h3>
        <p className="text-sm text-ink-secondary leading-relaxed mt-2 max-w-prose print:text-black">{opp.narrative}</p>
      </div>

      {/* Expandable detail sections */}
      <div className={`grid transition-all duration-300 ${open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}>
        <div className="overflow-hidden">
          <div className="px-5 pb-5 border-t border-edge-subtle pt-4 space-y-4">
            {opp.recommended_approach && (
              <div>
                <p className="text-2xs text-mint uppercase tracking-wider font-medium mb-2">Implementation Plan</p>
                <p className="text-sm text-ink-secondary leading-relaxed print:text-black whitespace-pre-line">{opp.recommended_approach}</p>
              </div>
            )}
            {opp.conditions_for_success.length > 0 && (
              <div>
                <p className="text-2xs text-amber uppercase tracking-wider font-medium mb-2">Prerequisites</p>
                <ul className="space-y-1.5">
                  {opp.conditions_for_success.map((c, i) => (
                    <li key={i} className="text-sm text-ink-secondary flex items-start gap-2">
                      <span className="mt-1.5 w-1.5 h-1.5 bg-amber rounded-full shrink-0" />{c}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {opp.risks.length > 0 && (
              <div>
                <p className="text-2xs text-rose uppercase tracking-wider font-medium mb-2">Risks</p>
                <ul className="space-y-1.5">
                  {opp.risks.map((r, i) => (
                    <li key={i} className="text-sm text-ink-secondary flex items-start gap-2">
                      <span className="mt-1.5 w-1.5 h-1.5 bg-rose rounded-full shrink-0" />{r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {opp.evidence_summary && (
              <div>
                <p className="text-2xs text-indigo uppercase tracking-wider font-medium mb-2">Supporting Evidence</p>
                <div className="border-l-2 border-indigo/20 pl-3">
                  <p className="text-sm text-ink-secondary leading-relaxed">{opp.evidence_summary}</p>
                  <a href="#evidence-annex" className="text-2xs text-indigo hover:underline font-mono mt-1.5 inline-block">
                    View full evidence ↓
                  </a>
                </div>
              </div>
            )}
            <div className="flex justify-end pt-1 print:hidden">
              <FeedbackButton targetSection={`opportunity:${opp.hypothesis_id}`} onSubmit={onFeedback} />
            </div>
          </div>
        </div>
      </div>

      {/* Print: always show details */}
      <div className="hidden print:block px-5 pb-5 border-t border-gray-300 pt-4 space-y-3">
        {opp.recommended_approach && <p className="text-sm text-black leading-relaxed">{opp.recommended_approach}</p>}
        {opp.evidence_summary && <p className="text-sm text-black leading-relaxed border-l-2 border-gray-300 pl-3">{opp.evidence_summary}</p>}
      </div>
    </div>
  )
}

export default function ReportPage() {
  const params = useParams()
  const router = useRouter()
  const runId = params.id as string
  const [run, setRun] = useState<Run | null>(null)
  const [approved, setApproved] = useState(false)
  const [report, setReport] = useState<AdaptiveReport | null>(null)
  const [evidence, setEvidence] = useState<EvidenceItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [reviewAction, setReviewAction] = useState<string | null>(null)
  const [refining, setRefining] = useState(false)
  const [lastEdited, setLastEdited] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [r, rpt, ev] = await Promise.all([getRun(runId), getReport(runId), getEvidence(runId).catch(() => [] as EvidenceItem[])])
      setRun(r)
      setEvidence(ev)
      if (rpt && typeof rpt.key_insight === 'string' && Array.isArray(rpt.opportunities)) {
        setReport(rpt as unknown as AdaptiveReport)
      }
    } catch (err) { setError(err instanceof Error ? err.message : 'Failed to load report') }
  }, [runId])

  useEffect(() => { load() }, [load])

  async function handleApprove() {
    setReviewAction('approving'); setError(null)
    try { await approveReport(runId); setApproved(true); await load() }
    catch (err) { setError(err instanceof Error ? err.message : 'Approval failed') }
    finally { setReviewAction(null) }
  }
  async function handleInvestigate() {
    setReviewAction('investigating'); setError(null)
    try { await requestDeeperInvestigation(runId); router.push(`/run/${runId}`) }
    catch (err) { setError(err instanceof Error ? err.message : 'Investigation request failed'); setReviewAction(null) }
  }
  async function handleFeedback(feedback: ReportFeedback) {
    setRefining(true); setError(null); setLastEdited(null)
    try {
      await refineReportWithFeedback(runId, [feedback]); await load()
      setLastEdited(feedback.target_section); setTimeout(() => setLastEdited(null), 3000)
    } catch (err) { setError(err instanceof Error ? err.message : 'Report refinement failed') }
    finally { setRefining(false) }
  }

  const feedbackCount = run?.feedback_history?.length ?? 0
  const hl = (section: string) => lastEdited === section ? 'ring-1 ring-mint/40 bg-mint/5 transition-all duration-500' : 'transition-all duration-500'

  // Loading / error / empty states
  const shell = (child: React.ReactNode) => <div className="min-h-screen bg-canvas flex items-center justify-center">{child}</div>
  if (!run && !error) return shell(<div className="flex flex-col items-center gap-3"><Spinner size={24} /><span className="text-2xs text-ink-tertiary font-mono">Loading report...</span></div>)
  if (error && !report) return shell(<p className="text-rose text-sm font-mono">{error}</p>)
  if (!report) return shell(<div className="text-center"><p className="text-ink-secondary text-sm">Report not yet generated.</p><Link href={`/run/${runId}`} className="text-mint text-2xs font-mono mt-2 inline-block hover:text-mint-bright">&larr; Back to run</Link></div>)

  const sorted = [...report.opportunities].sort((a, b) => b.confidence - a.confidence)
  const avgConfidence = sorted.length > 0 ? sorted.reduce((sum, o) => sum + o.confidence, 0) / sorted.length : 0

  return (
    <div className="min-h-screen bg-canvas print:bg-white">
      {/* Sticky header */}
      <header className="h-11 bg-canvas-raised border-b border-edge-subtle flex items-center px-5 sticky top-0 z-20 print:hidden">
        <Link href={`/run/${runId}`} className="text-2xs text-ink-tertiary hover:text-ink transition-colors font-mono">&larr; Back to Run</Link>
        <div className="w-px h-4 bg-edge mx-4" />
        <span className="text-2xs font-mono text-ink-tertiary uppercase tracking-[0.15em]">Analysis Report</span>
        {feedbackCount > 0 && <span className="ml-2"><Badge variant="indigo">Refined {feedbackCount}x</Badge></span>}
        <div className="flex-1" />
        <span className="text-2xs font-mono text-ink-tertiary mr-4">{sorted.length} opportunities &middot; {evidence.length} evidence</span>
        <button onClick={handleApprove} disabled={!!reviewAction || approved}
          className="bg-mint text-ink-inverse px-4 py-1.5 text-2xs font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors">
          {approved ? 'Approved' : 'Approve'}
        </button>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8 pb-24 print:p-0 print:max-w-none">
        {error && <div className="bg-rose/10 border border-rose/20 rounded-md p-3 mb-6"><p className="text-sm text-rose font-mono">{error}</p></div>}
        {refining && (
          <div className="bg-mint/10 border border-mint/20 rounded-md p-3 mb-6 flex items-center gap-3">
            <Spinner size={14} /><p className="text-sm text-mint font-mono">Regenerating report...</p>
          </div>
        )}

        {/* 1. KEY INSIGHT — the headline */}
        <section className="mb-10">
          <p className="text-lg font-semibold text-ink leading-snug print:text-black">{report.key_insight}</p>
        </section>

        {/* 2. EXECUTIVE SUMMARY — the context */}
        <section className={`mb-10 group rounded-md p-5 -mx-5 ${hl('executive_summary')}`}>
          <div className="flex items-center gap-3 mb-3">
            <SectionHeader action={<FeedbackButton targetSection="executive_summary" onSubmit={handleFeedback} />}>Executive Summary</SectionHeader>
          </div>
          <p className="text-sm text-ink leading-relaxed max-w-prose print:text-black">{report.executive_summary}</p>
        </section>

        {/* 3. OPPORTUNITIES — the recommendations (interactive) */}
        <section className="mb-10">
          <SectionHeader>Opportunities ({sorted.length})</SectionHeader>
          <div className="space-y-3">
            {sorted.map((opp, i) => (
              <OpportunityCard key={opp.hypothesis_id || i} opp={opp} onFeedback={handleFeedback}
                highlighted={lastEdited === `opportunity:${opp.hypothesis_id}`}
                isStartingPoint={i === 0} defaultOpen={i === 0} />
            ))}
          </div>
        </section>

        {/* 4. IMPLEMENTATION ROADMAP — sequenced next steps */}
        {report.recommended_next_steps.length > 0 && (
          <section className={`mb-10 group rounded-md p-5 -mx-5 ${hl('next_steps')}`}>
            <SectionHeader action={<FeedbackButton targetSection="next_steps" onSubmit={handleFeedback} />}>Implementation Roadmap</SectionHeader>
            <ol className="space-y-3">
              {report.recommended_next_steps.map((step, i) => (
                <li key={i} className="flex items-start gap-3 text-sm text-ink print:text-black">
                  <span className="bg-indigo/15 text-indigo font-semibold text-xs w-6 h-6 flex items-center justify-center rounded-full shrink-0 mt-0.5">{i + 1}</span>
                  <span className="leading-relaxed">{step}</span>
                </li>
              ))}
            </ol>
          </section>
        )}

        {/* 5. HOW WE REACHED THESE CONCLUSIONS — reasoning chain */}
        {report.reasoning_chain.length > 0 && (
          <section className="mb-10">
            <SectionHeader>How We Reached These Conclusions</SectionHeader>
            <ReasoningChain steps={report.reasoning_chain} />
          </section>
        )}

        {/* 6. CONFIDENCE ASSESSMENT */}
        <section className={`mb-10 group rounded-md p-5 -mx-5 ${hl('confidence')}`}>
          <SectionHeader action={<FeedbackButton targetSection="confidence" onSubmit={handleFeedback} />}>Confidence Assessment</SectionHeader>
          <ConfidenceNarrative assessment={report.confidence_assessment} confidence={avgConfidence} />
        </section>

        {/* 7. OPEN QUESTIONS — honesty about gaps */}
        {report.what_we_dont_know.length > 0 && (
          <section className={`mb-10 bg-amber/5 border border-amber/15 rounded-md p-5 group print:bg-white print:border-gray-300 ${hl('unknowns')}`}>
            <SectionHeader action={<FeedbackButton targetSection="unknowns" onSubmit={handleFeedback} />}>Open Questions &amp; Readiness Gaps</SectionHeader>
            <ul className="space-y-2">
              {report.what_we_dont_know.map((item, i) => (
                <li key={i} className="text-sm text-ink-secondary flex items-start gap-2 print:text-black leading-relaxed">
                  <span className="mt-1.5 w-1.5 h-1.5 bg-amber rounded-full shrink-0" />{item}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* 8. EVIDENCE ANNEX — drill-down */}
        {evidence.length > 0 && <EvidenceAnnex evidence={evidence} />}
      </main>

      {/* Footer actions */}
      <footer className="fixed bottom-0 left-0 right-0 bg-canvas-raised border-t border-edge-subtle px-6 py-3 flex items-center justify-end gap-3 z-20 print:hidden">
        {approved ? (
          <div className="flex items-center gap-3">
            <Badge variant="mint">Report Approved</Badge>
            <Link href={`/run/${runId}`} className="text-sm text-mint font-mono hover:text-mint-bright transition-colors">Back to Run</Link>
          </div>
        ) : (
          <>
            <button onClick={handleApprove} disabled={!!reviewAction}
              className="bg-mint text-ink-inverse px-6 py-2.5 text-sm font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors flex items-center gap-2">
              {reviewAction === 'approving' ? <><Spinner size={14} />Approving...</> : 'Approve Report'}
            </button>
            <button onClick={handleInvestigate} disabled={!!reviewAction}
              className="bg-transparent border border-amber text-amber px-6 py-2.5 text-sm font-semibold rounded-md disabled:opacity-40 hover:bg-amber/10 transition-colors flex items-center gap-2">
              {reviewAction === 'investigating' ? <><Spinner size={14} />Requesting...</> : 'Investigate Deeper'}
            </button>
          </>
        )}
      </footer>
    </div>
  )
}
