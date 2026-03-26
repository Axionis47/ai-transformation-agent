'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Header from '@/components/shell/Header'
import Sidebar from '@/components/shell/Sidebar'
import AssumptionCard from '@/components/cards/AssumptionCard'
import OpportunityCard from '@/components/cards/OpportunityCard'
import EvidenceCard from '@/components/cards/EvidenceCard'
import ReasoningStage from '@/components/stages/ReasoningStage'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'
import { getRun, startRun, confirmAssumptions, answerQuestion, synthesize, publish } from '@/lib/api'
import { stageStatus, getDepthBudget } from '@/lib/stage-utils'
import type { Run, AssumptionsDraft, Assumption } from '@/lib/types'

export default function RunPage() {
  const params = useParams()
  const runId = params.id as string
  const [run, setRun] = useState<Run | null>(null)
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [editedAssumptions, setEditedAssumptions] = useState<Map<string, string>>(new Map())

  const fetchRun = useCallback(async () => {
    try { setRun(await getRun(runId)) } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load run')
    }
  }, [runId])

  useEffect(() => { fetchRun() }, [fetchRun])

  async function doAction(msg: string, fn: () => Promise<unknown>) {
    setLoading(msg); setError(null)
    try { await fn(); await fetchRun() } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed')
    } finally { setLoading(null) }
  }

  const handleStart = () => doAction('Researching...', () => startRun(runId))
  const handleConfirm = () => {
    const edited: Assumption[] = (run?.assumptions?.assumptions ?? []).map(a => ({
      ...a,
      value: editedAssumptions.get(a.field) ?? a.value,
    }))
    const draft: AssumptionsDraft = { assumptions: edited, open_questions: run?.assumptions?.open_questions ?? [] }
    doAction('Confirming and starting reasoning...', async () => { await confirmAssumptions(runId, draft); await startRun(runId) })
  }
  const handleAnswer = (qId: string, ans: string) => doAction('Continuing analysis...', () => answerQuestion(runId, qId, ans))
  const handleSynthesize = () => doAction('Synthesizing opportunities...', () => synthesize(runId))
  const handlePublish = () => doAction('Publishing...', () => publish(runId))

  if (!run) return (
    <div className="min-h-screen flex items-center justify-center">
      {error ? <p className="text-rose text-sm">{error}</p> : <Spinner size={24} />}
    </div>
  )

  const { company_intake: intake, assumptions, reasoning_state: reasoning, status, budgets, budget_state } = run
  const depthBudget = getDepthBudget(run.config_snapshot as Record<string, unknown>)
  const ragRemaining = budgets.rag_query_budget - budget_state.rag_queries_used
  const searchRemaining = budgets.external_search_query_budget - budget_state.external_search_queries_used

  const s = (targets: string[]) => stageStatus(status, targets)
  const s1 = s(['created', 'intake'])
  const s2 = s(['assumptions_draft'])
  const s3 = s(['assumptions_confirmed', 'reasoning'])
  const s4 = s(['synthesis'])
  const s5 = s(['report', 'published'])

  const stages = [
    { id: 'intake', label: 'Intake', status: s1 },
    { id: 'assumptions', label: 'Assumptions', status: s2 },
    { id: 'reasoning', label: 'Reasoning', status: s3 },
    { id: 'synthesis', label: 'Synthesis', status: s4 },
    { id: 'report', label: 'Report', status: s5 },
  ] as { id: string; label: string; status: 'completed' | 'active' | 'pending' }[]

  return (
    <div className="min-h-screen bg-canvas">
      <Header
        companyName={intake?.company_name} industry={intake?.industry} sizeBand={intake?.employee_count_band}
        confidence={reasoning?.overall_confidence}
        ragRemaining={ragRemaining} ragTotal={budgets.rag_query_budget}
        searchRemaining={searchRemaining} searchTotal={budgets.external_search_query_budget}
      />
      <div className="flex">
        <Sidebar
          stages={stages} fieldCoverage={reasoning?.field_coverage}
          ragRemaining={ragRemaining} ragTotal={budgets.rag_query_budget}
          searchRemaining={searchRemaining} searchTotal={budgets.external_search_query_budget}
        />
        <main className="flex-1 min-w-0 p-6 lg:p-8">
          {error && (
            <div className="mb-6 bg-rose/10 border border-rose/30 rounded-md p-4">
              <p className="text-sm text-rose">{error}</p>
            </div>
          )}

          {/* INTAKE */}
          <section id="stage-intake" className="mb-8">
            <SectionHeader title="Intake" status={s1} />
            {intake && (
              <div className="bg-canvas-raised border border-edge-subtle rounded-md p-4 grid grid-cols-2 gap-4">
                <Field label="Company" value={intake.company_name} />
                <Field label="Industry" value={intake.industry} />
                {intake.employee_count_band && <Field label="Size" value={intake.employee_count_band} />}
                {intake.notes && <Field label="Notes" value={intake.notes} span2 />}
              </div>
            )}
            {status === 'intake' && (
              <ActionButton onClick={handleStart} loading={loading} label="Start Analysis" loadingLabel="Researching company..." />
            )}
          </section>

          {/* ASSUMPTIONS */}
          <section id="stage-assumptions" className="mb-8">
            <SectionHeader title="Assumptions" status={s2} extra={assumptions ? `${assumptions.assumptions.length} fields` : undefined} />
            {assumptions && (s2 === 'active' || s2 === 'completed') && (
              <div className="space-y-3">
                {assumptions.assumptions.map(a => (
                  <AssumptionCard key={a.field} assumption={a}
                    onUpdate={s2 === 'active' ? (val) => setEditedAssumptions(prev => new Map(prev).set(a.field, val)) : undefined} />
                ))}
                {assumptions.open_questions.length > 0 && (
                  <div className="bg-canvas-raised border border-edge-subtle rounded-md p-4">
                    <p className="text-2xs text-amber uppercase tracking-wider mb-2 font-medium">Open Questions</p>
                    {assumptions.open_questions.map((q, i) => (
                      <p key={i} className="text-sm text-ink-secondary leading-relaxed">{q}</p>
                    ))}
                  </div>
                )}
              </div>
            )}
            {s2 === 'active' && (
              <ActionButton onClick={handleConfirm} loading={loading} label="Confirm & Start Reasoning" loadingLabel="Starting reasoning..." />
            )}
          </section>

          {/* REASONING */}
          <section id="stage-reasoning" className="mb-8">
            <SectionHeader title="Reasoning" status={s3}
              extra={reasoning ? `${reasoning.loops_completed} loops, ${(reasoning.overall_confidence * 100).toFixed(0)}% confidence` : undefined} />
            {(s3 === 'active' || s3 === 'completed') && (
              <ReasoningStage state={reasoning} depthBudget={depthBudget} onAnswer={handleAnswer} loading={!!loading} />
            )}
            {reasoning?.completed && status === 'reasoning' && (
              <ActionButton onClick={handleSynthesize} loading={loading} label="Synthesize Opportunities" loadingLabel="Evaluating templates..." />
            )}
            {!reasoning?.completed && reasoning?.escalation_reason && status === 'reasoning' && (
              <div className="mt-4 flex items-center gap-3">
                <ActionButton onClick={handleSynthesize} loading={loading} label="Skip and Synthesize" loadingLabel="Evaluating templates..." />
                <span className="text-2xs text-ink-tertiary">Proceed with current evidence — gaps will be noted in the report</span>
              </div>
            )}
          </section>

          {/* SYNTHESIS + REPORT */}
          <section id="stage-synthesis" className="mb-8">
            <SectionHeader title="Opportunities" status={s4 === 'completed' || s5 !== 'pending' ? 'completed' : s4}
              extra={run.opportunities.length > 0 ? `${run.opportunities.length} found` : undefined} />
            {s4 === 'active' && loading && (
              <div className="flex items-center gap-3 py-4"><Spinner /><span className="text-sm text-ink-secondary">Evaluating opportunity templates...</span></div>
            )}
            {run.opportunities.length > 0 && (
              <div className="space-y-3">
                {run.opportunities.map(opp => (
                  <OpportunityCard key={opp.opportunity_id} opportunity={opp} evidence={run.evidence} />
                ))}
              </div>
            )}
          </section>

          <section id="stage-report" className="mb-8">
            <SectionHeader title="Report" status={s5} />
            {(s5 === 'active' || s5 === 'completed') && run.evidence.length > 0 && (
              <div>
                <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-3 font-medium">Evidence Annex</p>
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                  {run.evidence.map(ev => (
                    <EvidenceCard key={ev.evidence_id} evidence={ev} />
                  ))}
                </div>
              </div>
            )}
            {status === 'report' && (
              <ActionButton onClick={handlePublish} loading={loading} label="Publish Report" loadingLabel="Publishing..." />
            )}
            {status === 'published' && (
              <div className="mt-4 bg-mint/10 border border-mint/30 rounded-md p-4 flex items-center justify-between">
                <p className="text-sm text-mint font-medium">Report published and ready for review.</p>
                <a href={`/run/${runId}/report`}
                  className="bg-mint text-ink-inverse px-5 py-2 text-sm font-semibold rounded hover:bg-mint-bright transition-colors">
                  View Report
                </a>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  )
}

function SectionHeader({ title, status, extra }: { title: string; status: string; extra?: string }) {
  const color = status === 'active' ? 'text-mint' : status === 'completed' ? 'text-ink-secondary' : 'text-ink-tertiary'
  return (
    <div className="flex items-center gap-3 mb-4">
      <h2 className={`text-lg font-semibold ${status === 'pending' ? 'text-ink-tertiary' : 'text-ink'}`}>{title}</h2>
      <div className="flex-1 border-t border-edge-subtle" />
      {extra && <span className="text-2xs text-ink-tertiary font-mono">{extra}</span>}
      <Badge variant={status === 'active' ? 'mint' : status === 'completed' ? 'muted' : 'muted'}>
        {status.toUpperCase()}
      </Badge>
    </div>
  )
}

function Field({ label, value, span2 }: { label: string; value: string; span2?: boolean }) {
  return (
    <div className={span2 ? 'col-span-2' : ''}>
      <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-1 font-medium">{label}</p>
      <p className="text-base text-ink">{value}</p>
    </div>
  )
}

function ActionButton({ onClick, loading, label, loadingLabel }: { onClick: () => void; loading: string | null; label: string; loadingLabel: string }) {
  return (
    <button onClick={onClick} disabled={!!loading}
      className="mt-4 bg-mint text-ink-inverse px-5 py-2.5 text-sm font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors flex items-center gap-2">
      {loading ? <><Spinner size={14} />{loadingLabel}</> : label}
    </button>
  )
}
