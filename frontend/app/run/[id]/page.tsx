'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'next/navigation'
import ProgressRail from '@/components/ProgressRail'
import BudgetPills from '@/components/BudgetPills'
import StageSection from '@/components/StageSection'
import AssumptionsReview from '@/components/AssumptionsReview'
import ReasoningView from '@/components/ReasoningView'
import ReportView from '@/components/ReportView'
import DataRow from '@/components/DataRow'
import { getRun, startRun, confirmAssumptions, answerQuestion, synthesize, publish } from '@/lib/api'
import { stageStatus, getDepthBudget } from '@/lib/stage-utils'
import type { Run, AssumptionsDraft, BudgetView } from '@/lib/types'

export default function RunPage() {
  const params = useParams()
  const runId = params.id as string
  const [run, setRun] = useState<Run | null>(null)
  const [loadingMsg, setLoadingMsg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchRun = useCallback(async () => {
    try { setRun(await getRun(runId)) } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load run')
    }
  }, [runId])

  useEffect(() => { fetchRun() }, [fetchRun])

  async function doAction(msg: string, fn: () => Promise<unknown>) {
    setLoadingMsg(msg); setError(null)
    try { await fn(); await fetchRun() } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed')
    } finally { setLoadingMsg(null) }
  }

  const handleStart = () => doAction('Researching company and generating assumptions...', () => startRun(runId))
  const handleConfirm = (edited: AssumptionsDraft) => doAction('Confirming assumptions...', async () => { await confirmAssumptions(runId, edited); await startRun(runId) })
  const handleAnswer = (qId: string, ans: string) => doAction('Answering question and continuing analysis...', () => answerQuestion(runId, qId, ans))
  const handleSynthesize = () => doAction('Synthesizing opportunities...', () => synthesize(runId))
  const handlePublish = () => doAction('Publishing report...', () => publish(runId))

  if (!run) return (
    <main className="min-h-screen p-6">
      <p className="text-text-muted font-mono" style={{ fontSize: '13px' }}>{error ?? 'Loading run...'}</p>
    </main>
  )

  const { company_intake: intake, assumptions, reasoning_state: reasoning, status, budgets, budget_state } = run
  const budget: BudgetView = { rag_queries_remaining: budgets.rag_query_budget - budget_state.rag_queries_used, external_search_queries_remaining: budgets.external_search_query_budget - budget_state.external_search_queries_used, total_cost_estimate: '$0.00' }
  const depthBudget = getDepthBudget(run.config_snapshot as Record<string, unknown>)

  const s1 = stageStatus(status, ['created', 'intake'])
  const s2 = stageStatus(status, ['assumptions_draft'])
  const s3 = stageStatus(status, ['assumptions_confirmed', 'reasoning'])
  const s4 = stageStatus(status, ['synthesis'])
  const s5 = stageStatus(status, ['report', 'published'])
  const progress = [
    { stage: 'intake', status: s1 }, { stage: 'assumptions_draft', status: s2 },
    { stage: 'reasoning', status: s3 }, { stage: 'synthesis', status: s4 }, { stage: 'report', status: s5 },
  ]

  return (
    <main className="min-h-screen flex">
      <ProgressRail progress={progress} />
      <BudgetPills budget={budget} ragTotal={budgets.rag_query_budget} searchTotal={budgets.external_search_query_budget} />
      <div className="flex-1 p-6 max-w-3xl">
        <div className="flex gap-4 mb-6 border-b border-border pb-3">
          <span className="text-text-primary" style={{ fontSize: '18px', fontWeight: 600 }}>{intake?.company_name ?? 'New Run'}</span>
          {intake?.industry && <span className="text-text-muted font-mono self-end" style={{ fontSize: '13px' }}>{intake.industry}</span>}
          {reasoning && <span className="text-text-muted font-mono self-end" style={{ fontSize: '13px' }}>confidence: {reasoning.overall_confidence.toFixed(2)}</span>}
        </div>
        {error && <div className="border border-tier-hard bg-surface p-3 mb-4 rounded-sm"><p className="font-mono text-tier-hard" style={{ fontSize: '13px' }}>{error}</p></div>}

        <StageSection title="INTAKE" stageNumber={1} status={s1} summary={intake ? `${intake.company_name}, ${intake.industry}` : undefined}>
          {intake && <div className="space-y-0"><DataRow label="Company" value={intake.company_name} /><DataRow label="Industry" value={intake.industry} />{intake.employee_count_band && <DataRow label="Size" value={intake.employee_count_band} />}{intake.notes && <DataRow label="Notes" value={intake.notes} />}</div>}
          {status === 'intake' && <button onClick={handleStart} disabled={!!loadingMsg} className="mt-3 bg-accent text-white px-4 py-2 text-sm font-medium rounded-sm disabled:opacity-50">{loadingMsg ?? 'Start Analysis'}</button>}
        </StageSection>

        <StageSection title="ASSUMPTIONS" stageNumber={2} status={s2} summary={assumptions ? `${assumptions.assumptions.length} assumptions confirmed` : undefined}>
          {assumptions && s2 === 'active' && <AssumptionsReview assumptions={assumptions} onConfirm={handleConfirm} loading={!!loadingMsg} />}
          {s2 === 'completed' && assumptions && <div className="space-y-0">{assumptions.assumptions.map((a) => <DataRow key={a.field} label={a.field} value={`${a.value} [${a.source}]`} />)}</div>}
          {loadingMsg && s2 === 'active' && <p className="text-text-muted font-mono mt-2" style={{ fontSize: '12px' }}>{loadingMsg}</p>}
        </StageSection>

        <StageSection title="REASONING" stageNumber={3} status={s3} summary={reasoning ? `Loop ${reasoning.loops_completed}/${depthBudget}, confidence ${reasoning.overall_confidence.toFixed(2)}` : undefined}>
          {(s3 === 'active' || s3 === 'completed') && <ReasoningView reasoningState={reasoning} onAnswer={handleAnswer} loading={!!loadingMsg} depthBudget={depthBudget} />}
          {reasoning?.completed && status === 'reasoning' && <button onClick={handleSynthesize} disabled={!!loadingMsg} className="mt-3 bg-accent text-white px-4 py-2 text-sm font-medium rounded-sm disabled:opacity-50">{loadingMsg ?? 'Synthesize Opportunities'}</button>}
        </StageSection>

        <StageSection title="SYNTHESIS" stageNumber={4} status={s4} summary="Opportunities computed">
          {s4 === 'active' && loadingMsg && <p className="text-text-muted font-mono" style={{ fontSize: '12px' }}>{loadingMsg}</p>}
        </StageSection>

        <StageSection title="REPORT" stageNumber={5} status={s5} summary={status === 'published' ? 'Published' : undefined}>
          {(s5 === 'active' || s5 === 'completed') && <ReportView report={run.report} opportunities={run.opportunities} evidence={run.evidence} />}
          {status === 'report' && <button onClick={handlePublish} disabled={!!loadingMsg} className="mt-3 bg-accent text-white px-4 py-2 text-sm font-medium rounded-sm disabled:opacity-50">{loadingMsg ?? 'Publish Report'}</button>}
          {status === 'published' && <p className="font-mono text-tier-easy mt-2" style={{ fontSize: '13px' }}>Report published.</p>}
        </StageSection>
      </div>
    </main>
  )
}
