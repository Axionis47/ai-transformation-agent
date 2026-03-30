'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { getRun, getTrace, getAgentStates } from '@/lib/api'
import Spinner from '@/components/ui/Spinner'
import Badge from '@/components/ui/Badge'
import type { Run, AgentState } from '@/lib/types'

interface TraceEvent {
  event_id: string
  event_type: string
  timestamp: string
  payload: Record<string, unknown>
}

const PHASE_COLORS: Record<string, string> = {
  grounding: 'text-indigo',
  deep_research: 'text-amber',
  hypothesis_formation: 'text-amber',
  hypothesis_testing: 'text-mint',
  synthesis: 'text-mint',
  review: 'text-mint',
}

const EVENT_LABELS: Record<string, string> = {
  // Multi-agent events
  AGENT_SPAWNED: 'Agent Spawned',
  AGENT_COMPLETED: 'Agent Completed',
  AGENT_FAILED: 'Agent Failed',
  HYPOTHESIS_FORMED: 'Hypothesis Formed',
  HYPOTHESIS_TESTED: 'Hypothesis Tested',
  HYPOTHESIS_VALIDATED: 'Hypothesis Validated',
  HYPOTHESIS_REJECTED: 'Hypothesis Rejected',
  USER_INTERACTION_SURFACED: 'User Interaction',
  USER_INTERACTION_RESOLVED: 'Interaction Resolved',
  SPAWN_REQUESTED: 'Spawn Requested',
  PHASE_BACKTRACK: 'Phase Backtrack',
  REPORT_STRUCTURE_DECIDED: 'Report Structured',
  // Evidence & tools
  GROUNDING_CALL_REQUESTED: 'Google Search',
  GROUNDING_CALL_COMPLETED: 'Ground Result',
  GROUNDING_QUERIES_COUNTED: 'Search Budget',
  RAG_QUERY_EXECUTED: 'KB Search',
  RAG_RESULTS_FILTERED: 'KB Cross-ref',
  EVIDENCE_PROMOTED: 'Evidence Stored',
  EVIDENCE_REJECTED: 'Evidence Rejected',
  EVIDENCE_CONTRADICTION: 'Evidence Conflict',
  // Budget & errors
  EXTERNAL_BUDGET_EXHAUSTED: 'Budget Exhausted',
  BUDGET_VIOLATION_BLOCKED: 'Budget Blocked',
  STAGE_FAILED: 'Stage Failed',
  // Lifecycle
  RUN_CREATED: 'Run Created',
  COMPANY_INTAKE_SAVED: 'Intake Saved',
  REASONING_LOOP_STARTED: 'Loop Started',
  REASONING_LOOP_COMPLETED: 'Loop Completed',
  REPORT_RENDERED: 'Report Rendered',
  REPORT_REFINED: 'Report Refined',
  RUN_PUBLISHED: 'Published',
}

const AGENT_TYPE_LABELS: Record<string, string> = {
  company_profiler: 'Company Profiler',
  industry_analyst: 'Industry Analyst',
  pain_investigator: 'Pain Investigator',
  hypothesis_former: 'Hypothesis Former',
  hypothesis_tester: 'Hypothesis Tester',
  report_synthesizer: 'Report Synthesizer',
}

const FILTERS = ['all', 'agents', 'hypotheses', 'evidence', 'budget'] as const
type Filter = (typeof FILTERS)[number]

function matchesFilter(e: TraceEvent, f: Filter): boolean {
  if (f === 'all') return true
  if (f === 'agents') return e.event_type.includes('AGENT') || e.event_type.includes('SPAWN')
  if (f === 'hypotheses') return e.event_type.includes('HYPOTHESIS')
  if (f === 'evidence') return e.event_type.includes('GROUNDING') || e.event_type.includes('RAG') || e.event_type.includes('EVIDENCE')
  if (f === 'budget') return e.event_type.includes('BUDGET') || e.event_type.includes('EXHAUSTED') || e.event_type.includes('QUERIES_COUNTED')
  return true
}

function eventBorderColor(type: string): string {
  if (type.includes('AGENT_SPAWNED')) return 'border-l-indigo'
  if (type.includes('AGENT_COMPLETED')) return 'border-l-mint'
  if (type.includes('AGENT_FAILED') || type.includes('STAGE_FAILED')) return 'border-l-rose'
  if (type.includes('HYPOTHESIS_VALIDATED')) return 'border-l-mint'
  if (type.includes('HYPOTHESIS_REJECTED')) return 'border-l-rose'
  if (type.includes('HYPOTHESIS')) return 'border-l-amber'
  if (type.includes('EXHAUSTED') || type.includes('BLOCKED')) return 'border-l-rose'
  if (type.includes('EVIDENCE')) return 'border-l-mint'
  if (type.includes('GROUNDING') || type.includes('RAG')) return 'border-l-indigo'
  return 'border-l-edge-subtle'
}

function BudgetMeter({ label, used, total }: { label: string; used: number; total: number }) {
  const pct = total > 0 ? Math.min(100, (used / total) * 100) : 0
  const exhausted = used >= total
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-2xs font-mono text-ink-tertiary uppercase">{label}</span>
        <span className={`text-2xs font-mono tabular ${exhausted ? 'text-rose' : 'text-ink-secondary'}`}>
          {Math.max(0, total - used)}/{total}
        </span>
      </div>
      <div className="h-1 bg-edge-subtle rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${exhausted ? 'bg-rose' : pct > 70 ? 'bg-amber' : 'bg-mint'}`}
          style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function TracePage() {
  const params = useParams()
  const runId = params.id as string
  const [run, setRun] = useState<Run | null>(null)
  const [events, setEvents] = useState<TraceEvent[]>([])
  const [agents, setAgents] = useState<AgentState[]>([])
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<Filter>('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [r, t, a] = await Promise.all([
        getRun(runId),
        getTrace(runId),
        getAgentStates(runId).catch(() => [] as AgentState[]),
      ])
      setRun(r)
      setEvents(t as unknown as TraceEvent[])
      setAgents(a)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trace')
    }
  }, [runId])

  useEffect(() => { load() }, [load])

  if (error) return <div className="min-h-screen flex items-center justify-center"><p className="text-rose text-sm">{error}</p></div>
  if (!run) return <div className="min-h-screen flex items-center justify-center"><Spinner size={24} /></div>

  const searchUsed = run.budget_state.external_search_queries_used || 0
  const searchTotal = run.budgets.external_search_query_budget
  const ragUsed = run.budget_state.rag_queries_used || 0
  const ragTotal = run.budgets.rag_query_budget
  const filtered = events.filter(e => matchesFilter(e, filter))

  return (
    <div className="min-h-screen bg-canvas">
      <header className="h-12 bg-canvas-raised border-b border-edge-subtle flex items-center px-6 shrink-0 sticky top-0 z-20">
        <Link href={`/run/${runId}`} className="text-2xs text-ink-tertiary hover:text-ink transition-colors font-mono">&larr; Analysis</Link>
        <div className="w-px h-4 bg-edge mx-4" />
        <span className="text-2xs font-mono text-ink-tertiary uppercase tracking-[0.15em]">Trace</span>
        <div className="flex-1" />
        <Link href={`/run/${runId}/report`} className="text-2xs text-mint hover:text-mint-bright transition-colors font-mono">Report &rarr;</Link>
      </header>

      <div className="flex">
        {/* Left: Agent Activity + Budget */}
        <aside className="w-72 bg-canvas-raised border-r border-edge-subtle shrink-0 sticky top-12 h-[calc(100vh-48px)] overflow-y-auto hidden lg:block">
          <div className="p-4">
            <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium mb-4">Agents</p>
            {agents.length > 0 ? (
              <div className="space-y-3">
                {agents.map(agent => {
                  const label = AGENT_TYPE_LABELS[agent.agent_type] || agent.agent_type
                  const isRunning = agent.status === 'running'
                  const isCompleted = agent.status === 'completed'
                  const isFailed = agent.status === 'failed'
                  return (
                    <div key={agent.agent_id} className="border border-edge-subtle rounded-md p-3">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-2xs text-ink-secondary uppercase tracking-wider font-medium">{label}</span>
                        <Badge variant={isCompleted ? 'mint' : isFailed ? 'rose' : isRunning ? 'amber' : 'muted'}>
                          {agent.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 text-2xs font-mono text-ink-tertiary">
                        <span>{agent.tool_calls_made} calls</span>
                        <span>{agent.evidence_produced.length} evidence</span>
                      </div>
                      {agent.summary && (
                        <p className="text-2xs text-ink-secondary mt-1.5 line-clamp-2">{agent.summary}</p>
                      )}
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="text-2xs text-ink-tertiary">No agents spawned yet.</p>
            )}

            {/* Budget — from run state */}
            <div className="mt-6 border-t border-edge-subtle pt-4">
              <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium mb-3">Budget</p>
              <div className="space-y-3">
                <BudgetMeter label="Search" used={searchUsed} total={searchTotal} />
                <BudgetMeter label="RAG" used={ragUsed} total={ragTotal} />
              </div>
            </div>
          </div>
        </aside>

        {/* Right: Event Timeline */}
        <main className="flex-1 min-w-0 p-6">
          <div className="max-w-4xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-xl font-semibold text-ink">Event Trace</h1>
                <p className="text-sm text-ink-secondary mt-1">{events.length} events · {run.company_intake?.company_name}</p>
              </div>
              <button onClick={load} className="text-2xs text-ink-tertiary hover:text-mint transition-colors font-mono">Refresh</button>
            </div>

            <div className="flex gap-2 mb-6">
              {FILTERS.map(f => (
                <button key={f} onClick={() => setFilter(f)}
                  className={`text-2xs font-mono px-3 py-1.5 rounded transition-colors ${filter === f ? 'bg-canvas-overlay text-ink border border-edge' : 'text-ink-tertiary hover:text-ink-secondary'}`}>
                  {f.toUpperCase()}
                </button>
              ))}
            </div>

            <div className="space-y-1">
              {filtered.map((ev, i) => {
                const label = EVENT_LABELS[ev.event_type] || ev.event_type.replace(/_/g, ' ')
                const p = (ev.payload || {}) as Record<string, string | number | boolean | null>
                const phase = (p.phase as string) || ''
                const phaseColor = PHASE_COLORS[phase.toLowerCase()] || 'text-ink-tertiary'
                const isExpanded = expandedId === ev.event_id
                const isError = ev.event_type.includes('FAILED') || ev.event_type.includes('EXHAUSTED') || ev.event_type.includes('REJECTED')

                return (
                  <div key={ev.event_id || i}
                    className={`border-l-2 pl-4 py-2 cursor-pointer hover:bg-canvas-raised/50 transition-colors ${eventBorderColor(ev.event_type)}`}
                    onClick={() => setExpandedId(isExpanded ? null : ev.event_id)}>
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="text-2xs font-mono text-ink-tertiary w-16 shrink-0 tabular">
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : ''}
                      </span>
                      <span className={`text-2xs font-medium ${isError ? 'text-rose' : 'text-ink-secondary'}`}>
                        {label}
                      </span>
                      {phase && <span className={`text-2xs font-mono ${phaseColor}`}>{phase}</span>}
                      {p.agent_type && (
                        <span className="text-2xs font-mono text-indigo">
                          {AGENT_TYPE_LABELS[p.agent_type as string] || p.agent_type}
                        </span>
                      )}
                      {p.agent_id && (
                        <span className="text-2xs font-mono text-ink-tertiary">{(p.agent_id as string).slice(0, 8)}</span>
                      )}
                      {p.hypothesis_id && (
                        <span className="text-2xs font-mono text-amber">{(p.hypothesis_id as string).slice(0, 8)}</span>
                      )}
                      {p.confidence !== undefined && (
                        <span className="text-2xs font-mono text-mint">{Math.round((p.confidence as number) * 100)}%</span>
                      )}
                      {p.opportunities !== undefined && (
                        <span className="text-2xs font-mono text-mint">{p.opportunities} opps</span>
                      )}
                      {p.error && (
                        <span className="text-2xs text-rose truncate max-w-xs">{String(p.error).slice(0, 60)}</span>
                      )}
                    </div>

                    {isExpanded && (
                      <div className="mt-2 ml-[76px] bg-canvas-raised border border-edge-subtle rounded-md p-3">
                        <pre className="text-2xs text-ink-secondary font-mono whitespace-pre-wrap break-words leading-relaxed">
                          {JSON.stringify(p, null, 2).slice(0, 2000)}
                        </pre>
                      </div>
                    )}
                  </div>
                )
              })}

              {filtered.length === 0 && (
                <p className="text-2xs text-ink-tertiary font-mono py-8 text-center">No events for this filter.</p>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
