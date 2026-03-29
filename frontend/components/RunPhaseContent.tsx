'use client'

import Link from 'next/link'
import type { Run, AgentState, Hypothesis, CompanyIntake } from '@/lib/types'
import AgentActivityPanel from '@/components/AgentActivityPanel'
import HypothesisList from '@/components/HypothesisList'
import IntakeForm from '@/components/IntakeForm'
import Badge from '@/components/ui/Badge'

interface RunPhaseContentProps {
  run: Run
  agents: AgentState[]
  hypotheses: Hypothesis[]
  onIntakeSubmit: (data: CompanyIntake) => void
  intakeLoading: boolean
  depth: number
  threshold: number
}

function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-3 mb-1">
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
        <div className="flex-1 border-t border-edge-subtle" />
      </div>
      {subtitle && <p className="text-sm text-ink-tertiary">{subtitle}</p>}
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
        { label: 'Evidence', value: evidenceCount, variant: 'indigo' as const },
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

function CompanyUnderstandingPanel({ run }: { run: Run }) {
  const cu = (run as Record<string, unknown>).company_understanding as Record<string, unknown> | undefined
  if (!cu || !cu.what_they_do) return null
  return (
    <div className="mt-6 bg-canvas-raised border border-edge-subtle rounded-md p-5">
      <p className="text-xs text-indigo uppercase tracking-wider font-medium mb-3">Company Understanding</p>
      <div className="space-y-2 text-sm text-ink-secondary">
        {cu.what_they_do && <p><span className="text-ink-tertiary font-mono text-2xs mr-2">DOES</span>{cu.what_they_do as string}</p>}
        {cu.how_they_make_money && <p><span className="text-ink-tertiary font-mono text-2xs mr-2">REVENUE</span>{cu.how_they_make_money as string}</p>}
        {cu.size_and_scale && <p><span className="text-ink-tertiary font-mono text-2xs mr-2">SCALE</span>{cu.size_and_scale as string}</p>}
        {cu.technology_landscape && <p><span className="text-ink-tertiary font-mono text-2xs mr-2">TECH</span>{cu.technology_landscape as string}</p>}
      </div>
    </div>
  )
}

function IndustryContextPanel({ run }: { run: Run }) {
  const ic = (run as Record<string, unknown>).industry_context as Record<string, unknown> | undefined
  if (!ic || !ic.industry) return null
  const trends = (ic.key_trends as string[] | undefined) ?? []
  return (
    <div className="mt-4 bg-canvas-raised border border-edge-subtle rounded-md p-5">
      <p className="text-xs text-indigo uppercase tracking-wider font-medium mb-3">Industry Context</p>
      <div className="space-y-2 text-sm text-ink-secondary">
        {ic.ai_adoption_level && <p><span className="text-ink-tertiary font-mono text-2xs mr-2">AI ADOPTION</span>{ic.ai_adoption_level as string}</p>}
        {ic.competitive_dynamics && <p><span className="text-ink-tertiary font-mono text-2xs mr-2">COMPETITION</span>{ic.competitive_dynamics as string}</p>}
        {trends.length > 0 && (
          <div>
            <span className="text-ink-tertiary font-mono text-2xs mr-2">TRENDS</span>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {trends.slice(0, 5).map((t, i) => (
                <span key={i} className="bg-indigo/10 text-indigo text-2xs font-mono px-2 py-0.5 rounded">{t}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function PainPointsPanel({ run }: { run: Run }) {
  const pps = (run as Record<string, unknown>).pain_points as Array<Record<string, unknown>> | undefined
  if (!pps || pps.length === 0) return null
  return (
    <div className="mt-6 bg-canvas-raised border border-edge-subtle rounded-md p-5">
      <p className="text-xs text-amber uppercase tracking-wider font-medium mb-3">Discovered Pain Points ({pps.length})</p>
      <div className="space-y-3">
        {pps.map((pp, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${
              pp.severity === 'high' ? 'bg-rose' : pp.severity === 'medium' ? 'bg-amber' : 'bg-mint'
            }`} />
            <div>
              <p className="text-sm text-ink">{pp.description as string}</p>
              <p className="text-2xs text-ink-tertiary font-mono mt-0.5">
                {pp.affected_process as string}
                {pp.severity && <> &middot; {(pp.severity as string).toUpperCase()}</>}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function RunPhaseContent({
  run, agents, hypotheses, onIntakeSubmit, intakeLoading, depth, threshold,
}: RunPhaseContentProps) {
  const status = run.status.toLowerCase()
  const runId = run.run_id

  // INTAKE
  if (status === 'intake' || status === 'created') {
    return (
      <div className="max-w-3xl mx-auto">
        <SectionTitle title="Company Intake" subtitle="Provide company details to begin analysis." />
        <IntakeForm
          onSubmit={(data) => onIntakeSubmit(data)}
          loading={intakeLoading}
          depth={depth} threshold={threshold}
          onDepthChange={() => {}} onThresholdChange={() => {}}
        />
      </div>
    )
  }

  // GROUNDING
  if (status === 'grounding') {
    return (
      <>
        <SectionTitle title="Researching Company & Industry" subtitle="CompanyProfiler and IndustryAnalyst running in parallel..." />
        <AgentActivityPanel agents={agents} />
        <div className="mt-6 bg-canvas-raised border border-edge-subtle rounded-md p-4">
          <div className="flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-mint animate-pulse" />
            <span className="text-sm text-ink-secondary font-mono">{run.evidence.length} evidence items collected</span>
          </div>
        </div>
        <CompanyUnderstandingPanel run={run} />
        <IndustryContextPanel run={run} />
      </>
    )
  }

  // DEEP RESEARCH
  if (status === 'deep_research') {
    return (
      <>
        <SectionTitle title="Investigating Pain Points" subtitle="PainInvestigator analyzing operational gaps..." />
        <AgentActivityPanel agents={agents} />
        <div className="mt-6 bg-canvas-raised border border-edge-subtle rounded-md p-4">
          <div className="flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-mint animate-pulse" />
            <span className="text-sm text-ink-secondary font-mono">{run.evidence.length} evidence items</span>
          </div>
        </div>
        <CompanyUnderstandingPanel run={run} />
        <IndustryContextPanel run={run} />
        <PainPointsPanel run={run} />
      </>
    )
  }

  // HYPOTHESIS FORMATION
  if (status === 'hypothesis_formation') {
    return (
      <>
        <SectionTitle title="Forming Hypotheses" subtitle="Generating transformation hypotheses from evidence..." />
        <AgentActivityPanel agents={agents} />
        <CompanyUnderstandingPanel run={run} />
        <PainPointsPanel run={run} />
        {hypotheses.length > 0 && <div className="mt-6"><HypothesisList hypotheses={hypotheses} /></div>}
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
        <div className="mt-6"><HypothesisList hypotheses={hypotheses} /></div>
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
          <Link href={`/run/${runId}/report`}
            className="inline-flex items-center gap-2 bg-mint text-ink-inverse px-6 py-3 text-sm font-semibold rounded-md hover:bg-mint-bright transition-colors">
            View Report
          </Link>
        </div>
        {hypotheses.length > 0 && <HypothesisList hypotheses={hypotheses} />}
      </>
    )
  }

  // PUBLISHED
  if (status === 'published') {
    return (
      <>
        <SectionTitle title="Analysis Published" />
        <div className="flex items-center gap-2 mb-6"><Badge variant="mint">Published</Badge></div>
        <SummaryStats hypotheses={hypotheses} evidenceCount={run.evidence.length} />
        <div className="mb-6">
          <Link href={`/run/${runId}/report`}
            className="inline-flex items-center gap-2 bg-mint text-ink-inverse px-6 py-3 text-sm font-semibold rounded-md hover:bg-mint-bright transition-colors">
            View Report
          </Link>
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

  return (
    <div className="bg-canvas-raised border border-edge-subtle rounded-md p-6 text-center">
      <p className="text-sm text-ink-tertiary">Phase: {run.status}</p>
    </div>
  )
}
