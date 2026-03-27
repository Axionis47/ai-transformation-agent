'use client'

interface SidebarProps {
  currentPhase: string
  completedPhases: string[]
  agentCounts?: Record<string, number>
  searchUsed?: number
  searchTotal?: number
  ragUsed?: number
  ragTotal?: number
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

function phaseStatus(
  phaseId: string,
  currentPhase: string,
  completedPhases: string[],
): 'completed' | 'active' | 'pending' {
  if (completedPhases.includes(phaseId)) return 'completed'
  if (phaseId === currentPhase) return 'active'
  return 'pending'
}

function PhaseDot({ status }: { status: 'completed' | 'active' | 'pending' }) {
  if (status === 'completed') {
    return <div className="w-1.5 h-1.5 rounded-full bg-mint shrink-0" />
  }
  if (status === 'active') {
    return <div className="w-1.5 h-1.5 rounded-full bg-mint shrink-0 animate-pulse-slow" />
  }
  return <div className="w-1.5 h-1.5 rounded-full bg-edge-subtle shrink-0" />
}

function BudgetMeter({ label, used, total }: { label: string; used: number; total: number }) {
  const remaining = Math.max(0, total - used)
  const exhausted = remaining === 0
  return (
    <div className="flex items-center justify-between">
      <span className="text-2xs font-mono text-ink-tertiary uppercase">{label}</span>
      <span className={`text-2xs font-mono tabular ${exhausted ? 'text-rose' : 'text-ink-secondary'}`}>
        {remaining}/{total}
      </span>
    </div>
  )
}

export default function Sidebar({
  currentPhase,
  completedPhases,
  agentCounts,
  searchUsed = 0,
  searchTotal,
  ragUsed = 0,
  ragTotal,
}: SidebarProps) {
  return (
    <aside className="w-56 bg-canvas shrink-0 sticky top-16 h-[calc(100vh-64px)] overflow-y-auto hidden md:block">
      <nav className="px-5 pt-6 pb-4">
        <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-4 font-medium">
          Phases
        </p>
        <div className="relative">
          {PHASES.map((phase, i) => {
            const status = phaseStatus(phase.id, currentPhase, completedPhases)
            const count = agentCounts?.[phase.id]
            const isLast = i === PHASES.length - 1

            return (
              <div key={phase.id} className="relative flex items-start gap-3">
                {/* Connecting line */}
                {!isLast && (
                  <div
                    className="absolute left-[2.5px] top-[10px] w-px bg-edge-subtle"
                    style={{ height: 'calc(100% + 4px)' }}
                  />
                )}

                {/* Dot column */}
                <div className="relative z-10 mt-[5px]">
                  <PhaseDot status={status} />
                </div>

                {/* Label + agent count */}
                <div className="flex items-center gap-2 pb-5 min-w-0">
                  <span
                    className={`text-xs font-medium uppercase tracking-wider ${
                      status === 'active'
                        ? 'text-mint font-semibold'
                        : status === 'completed'
                        ? 'text-ink'
                        : 'text-ink-tertiary'
                    }`}
                  >
                    {phase.label}
                  </span>
                  {count != null && count > 0 && (status === 'active' || status === 'completed') && (
                    <span className="text-2xs font-mono text-ink-tertiary">
                      {count} agent{count !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </nav>

      {/* Budget consumption */}
      {(searchTotal != null || ragTotal != null) && (
        <div className="px-5 pb-4">
          <div className="border-t border-edge-subtle pt-4">
            <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-3 font-medium">
              Budget
            </p>
            <div className="space-y-2">
              {searchTotal != null && (
                <BudgetMeter label="Search" used={searchUsed} total={searchTotal} />
              )}
              {ragTotal != null && (
                <BudgetMeter label="RAG" used={ragUsed} total={ragTotal} />
              )}
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}
