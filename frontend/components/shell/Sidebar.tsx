'use client'

import type { Run, AgentState } from '@/lib/types'

interface SidebarProps {
  run: Run
  agents?: AgentState[]
}

const PHASES = [
  { id: 'INTAKE', label: 'Intake' },
  { id: 'GROUNDING', label: 'Grounding' },
  { id: 'DEEP_RESEARCH', label: 'Research' },
  { id: 'HYPOTHESIS_FORMATION', label: 'Hypotheses' },
  { id: 'HYPOTHESIS_TESTING', label: 'Testing' },
  { id: 'SYNTHESIS', label: 'Synthesis' },
  { id: 'REVIEW', label: 'Report' },
]

const PHASE_ORDER = PHASES.map(p => p.id)

function phaseStatus(phaseId: string, currentPhase: string): 'completed' | 'active' | 'pending' {
  const current = currentPhase.toUpperCase()
  const currentIdx = PHASE_ORDER.indexOf(current)
  const phaseIdx = PHASE_ORDER.indexOf(phaseId)
  if (currentIdx < 0) return 'pending'
  if (phaseIdx < currentIdx) return 'completed'
  if (phaseIdx === currentIdx) return 'active'
  return 'pending'
}

function PhaseDot({ status }: { status: 'completed' | 'active' | 'pending' }) {
  if (status === 'completed') return <div className="w-1.5 h-1.5 rounded-full bg-mint shrink-0" />
  if (status === 'active') return <div className="w-1.5 h-1.5 rounded-full bg-mint shrink-0 animate-pulse-slow" />
  return <div className="w-1.5 h-1.5 rounded-full bg-edge-subtle shrink-0" />
}

function BudgetMeter({ label, used, total }: { label: string; used: number; total: number }) {
  const remaining = Math.max(0, total - used)
  const pct = total > 0 ? Math.min(100, (used / total) * 100) : 0
  const exhausted = remaining === 0
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-2xs font-mono text-ink-tertiary uppercase">{label}</span>
        <span className={`text-2xs font-mono tabular ${exhausted ? 'text-rose' : 'text-ink-secondary'}`}>
          {remaining}/{total}
        </span>
      </div>
      <div className="h-1 bg-edge-subtle rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${exhausted ? 'bg-rose' : pct > 70 ? 'bg-amber' : 'bg-mint'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export default function Sidebar({ run, agents = [] }: SidebarProps) {
  const searchUsed = run.budget_state.external_search_queries_used || 0
  const searchTotal = run.budgets.external_search_query_budget
  const ragUsed = run.budget_state.rag_queries_used || 0
  const ragTotal = run.budgets.rag_query_budget

  return (
    <aside className="w-56 bg-canvas shrink-0 sticky top-14 h-[calc(100vh-56px)] overflow-y-auto hidden md:block">
      <nav className="px-5 pt-6 pb-4">
        <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-4 font-medium">Phases</p>
        <div className="relative">
          {PHASES.map((phase, i) => {
            const status = phaseStatus(phase.id, run.status)
            const phaseAgents = agents.filter(a =>
              a.agent_type.toLowerCase().includes(phase.id.toLowerCase().replace('_', ''))
              || (phase.id === 'GROUNDING' && (a.agent_type === 'company_profiler' || a.agent_type === 'industry_analyst'))
              || (phase.id === 'DEEP_RESEARCH' && a.agent_type === 'pain_investigator')
              || (phase.id === 'HYPOTHESIS_FORMATION' && a.agent_type === 'hypothesis_former')
              || (phase.id === 'HYPOTHESIS_TESTING' && a.agent_type === 'hypothesis_tester')
              || (phase.id === 'SYNTHESIS' && a.agent_type === 'report_synthesizer')
            )
            const isLast = i === PHASES.length - 1

            return (
              <div key={phase.id} className="relative flex items-start gap-3">
                {!isLast && (
                  <div className="absolute left-[2.5px] top-[10px] w-px bg-edge-subtle" style={{ height: 'calc(100% + 4px)' }} />
                )}
                <div className="relative z-10 mt-[5px]">
                  <PhaseDot status={status} />
                </div>
                <div className="flex items-center gap-2 pb-5 min-w-0">
                  <span className={`text-xs font-medium uppercase tracking-wider ${
                    status === 'active' ? 'text-mint font-semibold' : status === 'completed' ? 'text-ink' : 'text-ink-tertiary'
                  }`}>
                    {phase.label}
                  </span>
                  {phaseAgents.length > 0 && (status === 'active' || status === 'completed') && (
                    <span className="text-2xs font-mono text-ink-tertiary">
                      {phaseAgents.length}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </nav>

      {/* Budget — always shown from real run data */}
      <div className="px-5 pb-4">
        <div className="border-t border-edge-subtle pt-4">
          <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-3 font-medium">Budget</p>
          <div className="space-y-3">
            <BudgetMeter label="Search" used={searchUsed} total={searchTotal} />
            <BudgetMeter label="RAG" used={ragUsed} total={ragTotal} />
          </div>
        </div>
      </div>
    </aside>
  )
}
