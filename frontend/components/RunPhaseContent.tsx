'use client'

import type { Run, AgentState, Hypothesis } from '@/lib/types'
import AgentActivityPanel from '@/components/AgentActivityPanel'
import HypothesisList from '@/components/HypothesisList'
import IntakeForm from '@/components/IntakeForm'
import Badge from '@/components/ui/Badge'
import type { CompanyIntake, ReasoningConfig } from '@/lib/types'

interface RunPhaseContentProps {
  run: Run
  agents: AgentState[]
  hypotheses: Hypothesis[]
  onIntakeSubmit: (data: CompanyIntake, config: ReasoningConfig) => void
  intakeLoading: boolean
  depth: number
  threshold: number
  onDepthChange: (v: number) => void
  onThresholdChange: (v: number) => void
}

function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-3 mb-1">
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
        <div className="flex-1 border-t border-edge-subtle" />
      </div>
      {subtitle && (
        <p className="text-sm text-ink-tertiary">{subtitle}</p>
      )}
    </div>
  )
}

function SummaryStats({ hypotheses, evidenceCount }: { hypotheses: Hypothesis[]; evidenceCount: number }) {
  const validated = hypotheses.filter(h => h.status === 'validated').length
  const rejected = hypotheses.filter(h => h.status === 'rejected').length
  return (
    <div className="grid grid-cols-3 gap-4 mb-6">
      {[
        { label: 'Validated', value: validated, variant: 'mint' as const },
        { label: 'Rejected', value: rejected, variant: 'rose' as const },
        { label: 'Evidence Items', value: evidenceCount, variant: 'indigo' as const },
      ].map(s => (
        <div key={s.label} className="bg-canvas-raised border border-edge-subtle rounded-md p-4 text-center">
          <p className="text-2xl font-semibold font-mono text-ink">{s.value}</p>
          <p className="text-xs text-ink-tertiary uppercase tracking-wider mt-1">
            <Badge variant={s.variant}>{s.label}</Badge>
          </p>
        </div>
      ))}
    </div>
  )
}

export default function RunPhaseContent({
  run, agents, hypotheses,
  onIntakeSubmit, intakeLoading, depth, threshold, onDepthChange, onThresholdChange,
}: RunPhaseContentProps) {
  const status = run.status.toLowerCase()
  const runId = run.run_id

  // INTAKE
  if (status === 'intake' || status === 'created') {
    return (
      <div className="max-w-3xl mx-auto">
        <SectionTitle title="Company Intake" subtitle="Provide company details to begin analysis." />
        <IntakeForm
          onSubmit={onIntakeSubmit} loading={intakeLoading}
          depth={depth} threshold={threshold}
          onDepthChange={onDepthChange} onThresholdChange={onThresholdChange}
        />
      </div>
    )
  }

  // GROUNDING
  if (status === 'grounding') {
    return (
      <>
        <SectionTitle title="Researching Company & Industry" subtitle="Two agents are researching in parallel..." />
        <AgentActivityPanel agents={agents} />
        <div className="mt-6 bg-canvas-raised border border-edge-subtle rounded-md p-4">
          <div className="flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-mint animate-pulse" />
            <span className="text-sm text-ink-secondary font-mono">
              {run.evidence.length} evidence items collected
            </span>
          </div>
        </div>
      </>
    )
  }

  // DEEP RESEARCH
  if (status === 'deep_research') {
    return (
      <>
        <SectionTitle title="Investigating Pain Points" subtitle="PainPointInvestigator is analyzing operational gaps..." />
        <AgentActivityPanel agents={agents} />
        {run.evidence.length > 0 && (
          <div className="mt-6 bg-canvas-raised border border-edge-subtle rounded-md p-4">
            <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium mb-2">Discovered</p>
            <p className="text-sm text-ink font-mono">{run.evidence.length} evidence items</p>
          </div>
        )}
      </>
    )
  }

  // HYPOTHESIS FORMATION
  if (status === 'hypothesis_formation') {
    return (
      <>
        <SectionTitle title="Forming Hypotheses" subtitle="HypothesisFormer is generating transformation hypotheses..." />
        <AgentActivityPanel agents={agents} />
        {hypotheses.length > 0 && (
          <div className="mt-6">
            <HypothesisList hypotheses={hypotheses} />
          </div>
        )}
      </>
    )
  }

  // HYPOTHESIS TESTING
  if (status === 'hypothesis_testing') {
    const testing = agents.filter(a => a.status === 'running').length
    return (
      <>
        <SectionTitle
          title="Testing Hypotheses"
          subtitle={testing > 0 ? `${testing} testers running in parallel...` : 'Evaluating hypothesis validity...'}
        />
        <AgentActivityPanel agents={agents} />
        <div className="mt-6">
          <HypothesisList hypotheses={hypotheses} />
        </div>
      </>
    )
  }

  // SYNTHESIS / REPORT / REVIEW
  if (status === 'synthesis' || status === 'report' || status === 'review') {
    return (
      <>
        <SectionTitle title="Analysis Complete" />
        <SummaryStats hypotheses={hypotheses} evidenceCount={run.evidence.length} />
        <div className="mb-6">
          <a href={`/run/${runId}/report`}
            className="inline-flex items-center gap-2 bg-mint text-ink-inverse px-6 py-3 text-sm font-semibold rounded-md hover:bg-mint-bright transition-colors">
            View Report
          </a>
        </div>
        {hypotheses.length > 0 && <HypothesisList hypotheses={hypotheses} />}
      </>
    )
  }

  // PUBLISHED
  if (status === 'published') {
    return (
      <>
        <SectionTitle title="Analysis Complete" />
        <div className="flex items-center gap-2 mb-6">
          <Badge variant="mint">Published</Badge>
        </div>
        <SummaryStats hypotheses={hypotheses} evidenceCount={run.evidence.length} />
        <div className="mb-6">
          <a href={`/run/${runId}/report`}
            className="inline-flex items-center gap-2 bg-mint text-ink-inverse px-6 py-3 text-sm font-semibold rounded-md hover:bg-mint-bright transition-colors">
            View Report
          </a>
        </div>
        {hypotheses.length > 0 && <HypothesisList hypotheses={hypotheses} />}
      </>
    )
  }

  // FAILED
  if (status === 'failed') {
    return (
      <div className="bg-rose/10 border border-rose/30 rounded-md p-6 text-center">
        <p className="text-sm text-rose font-medium">This analysis run has failed.</p>
      </div>
    )
  }

  // Fallback
  return (
    <div className="bg-canvas-raised border border-edge-subtle rounded-md p-6 text-center">
      <p className="text-sm text-ink-tertiary">Unknown phase: {run.status}</p>
    </div>
  )
}
