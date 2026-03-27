'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { getRun, getTrace } from '@/lib/api'
import Spinner from '@/components/ui/Spinner'
import ScoreBar from '@/components/ui/ScoreBar'
import Badge from '@/components/ui/Badge'
import type { Run } from '@/lib/types'

interface TraceEvent {
  event_id: string
  event_type: string
  timestamp: string
  payload: Record<string, unknown>
}

const PHASE_COLORS: Record<string, string> = {
  PROFILE: 'text-indigo', DISCOVER: 'text-amber', MATCH: 'text-mint', FILL: 'text-ink-secondary',
}

const EVENT_LABELS: Record<string, string> = {
  REASONING_LOOP_STARTED: 'Loop Started',
  REASONING_LOOP_COMPLETED: 'Loop Completed',
  MID_GAP_DETECTED: 'Gap Detected',
  GROUNDING_CALL_REQUESTED: 'Google Search',
  GROUNDING_CALL_COMPLETED: 'Ground Result',
  GROUNDING_QUERIES_COUNTED: 'Search Budget',
  RAG_QUERY_EXECUTED: 'KB Search',
  RAG_RESULTS_FILTERED: 'KB Cross-ref',
  WORKING_MEMORY_UPDATED: 'Memory Updated',
  ESCALATION_TRIGGERED: 'Escalation',
  CONFIDENCE_STAGNATION: 'Stagnation',
  EXTERNAL_BUDGET_EXHAUSTED: 'Budget Exhausted',
  CONTRADICTION_DETECTED: 'Contradiction',
  EVIDENCE_PROMOTED: 'Evidence Stored',
}

export default function TracePage() {
  const params = useParams()
  const runId = params.id as string
  const [run, setRun] = useState<Run | null>(null)
  const [events, setEvents] = useState<TraceEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [r, t] = await Promise.all([getRun(runId), getTrace(runId)])
      setRun(r)
      setEvents(t as unknown as TraceEvent[])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trace')
    }
  }, [runId])

  useEffect(() => { load() }, [load])

  if (error) return <div className="min-h-screen flex items-center justify-center"><p className="text-rose text-sm">{error}</p></div>
  if (!run) return <div className="min-h-screen flex items-center justify-center"><Spinner size={24} /></div>

  // Extract memory snapshots for the memory panel
  const memoryEvents = events.filter(e => e.event_type === 'WORKING_MEMORY_UPDATED')
  const latestMemory = memoryEvents.length > 0 ? memoryEvents[memoryEvents.length - 1] : null
  const memoryFields = (latestMemory?.payload?.fields || {}) as Record<string, { synthesis: string; confidence: number; evidence_count: number; last_updated: number }>

  // Budget tracking
  const budgetEvents = events.filter(e => e.event_type === 'GROUNDING_QUERIES_COUNTED')
  const lastBudget = budgetEvents.length > 0 ? budgetEvents[budgetEvents.length - 1] : null
  const searchUsed = (lastBudget?.payload?.total_used as number) || 0
  const searchTotal = (lastBudget?.payload?.budget as number) || 25
  const ragEvents = events.filter(e => e.event_type === 'RAG_QUERY_EXECUTED')

  // Filter events
  const filters = ['all', 'loops', 'memory', 'evidence', 'budget']
  const filtered = events.filter(e => {
    if (filter === 'all') return true
    if (filter === 'loops') return e.event_type.includes('LOOP') || e.event_type.includes('MID_GAP')
    if (filter === 'memory') return e.event_type === 'WORKING_MEMORY_UPDATED'
    if (filter === 'evidence') return e.event_type.includes('GROUNDING') || e.event_type.includes('RAG') || e.event_type === 'EVIDENCE_PROMOTED'
    if (filter === 'budget') return e.event_type.includes('BUDGET') || e.event_type.includes('EXHAUSTED') || e.event_type.includes('QUERIES_COUNTED')
    return true
  })

  return (
    <div className="min-h-screen bg-canvas">
      <header className="h-11 bg-canvas-raised border-b border-edge-subtle flex items-center px-5 shrink-0 sticky top-0 z-20">
        <Link href={`/run/${runId}`} className="text-2xs text-ink-tertiary hover:text-ink transition-colors font-mono">&larr; Analysis</Link>
        <div className="w-px h-4 bg-edge mx-4" />
        <span className="text-2xs font-mono text-ink-tertiary uppercase tracking-[0.15em]">Trace</span>
        <div className="flex-1" />
        <Link href={`/run/${runId}/report`} className="text-2xs text-mint hover:text-mint-bright transition-colors font-mono">Report &rarr;</Link>
      </header>

      <div className="flex">
        {/* Left: Working Memory Panel */}
        <aside className="w-72 bg-canvas-raised border-r border-edge-subtle shrink-0 sticky top-11 h-[calc(100vh-44px)] overflow-y-auto hidden lg:block">
          <div className="p-4">
            <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium mb-4">Working Memory</p>
            {Object.keys(memoryFields).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(memoryFields).map(([field, data]) => (
                  <div key={field} className="border border-edge-subtle rounded p-3">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-2xs text-ink-secondary uppercase tracking-wider font-medium">{field.replace(/_/g, ' ')}</span>
                      <span className="text-2xs font-mono text-mint tabular">{(data.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-2xs text-ink leading-relaxed">{data.synthesis}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-2xs text-ink-tertiary font-mono">{data.evidence_count} sources</span>
                      <span className="text-2xs text-ink-tertiary font-mono">loop {data.last_updated}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-2xs text-ink-tertiary">No memory snapshots yet. Run reasoning to see field synthesis evolve.</p>
            )}

            {/* Budget summary */}
            <div className="mt-6 border-t border-edge-subtle pt-4">
              <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium mb-3">Budget</p>
              <div className="space-y-2">
                <ScoreBar label="Search" value={1 - (searchUsed / Math.max(searchTotal, 1))}
                  color={searchUsed >= searchTotal ? 'rose' : 'mint'} />
                <ScoreBar label="RAG" value={1 - (ragEvents.length / 15)}
                  color={ragEvents.length >= 15 ? 'rose' : 'mint'} />
              </div>
              <div className="flex justify-between mt-2">
                <span className="text-2xs text-ink-tertiary font-mono">{searchUsed}/{searchTotal} searches</span>
                <span className="text-2xs text-ink-tertiary font-mono">{ragEvents.length}/15 RAG</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Right: Event Timeline */}
        <main className="flex-1 min-w-0 p-6">
          <div className="max-w-4xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-xl font-semibold text-ink">Reasoning Trace</h1>
                <p className="text-sm text-ink-secondary mt-1">{events.length} events · {run.company_intake?.company_name}</p>
              </div>
              <button onClick={load} className="text-2xs text-ink-tertiary hover:text-mint transition-colors font-mono">Refresh</button>
            </div>

            {/* Filters */}
            <div className="flex gap-2 mb-6">
              {filters.map(f => (
                <button key={f} onClick={() => setFilter(f)}
                  className={`text-2xs font-mono px-3 py-1.5 rounded transition-colors ${filter === f ? 'bg-canvas-overlay text-ink border border-edge' : 'text-ink-tertiary hover:text-ink-secondary'}`}>
                  {f.toUpperCase()}
                </button>
              ))}
            </div>

            {/* Timeline */}
            <div className="space-y-1">
              {filtered.map((ev, i) => {
                const label = EVENT_LABELS[ev.event_type] || ev.event_type
                const p = (ev.payload || {}) as Record<string, string | number | boolean | null>
                const phase = (p.phase as string) || ''
                const phaseColor = PHASE_COLORS[phase] || 'text-ink-tertiary'
                const isLoop = ev.event_type.includes('LOOP_STARTED')
                const isMemory = ev.event_type === 'WORKING_MEMORY_UPDATED'
                const isAlert = ev.event_type.includes('ESCALATION') || ev.event_type.includes('EXHAUSTED') || ev.event_type.includes('STAGNATION')
                const isExpanded = expandedId === ev.event_id

                return (
                  <div key={ev.event_id || i}
                    className={`border-l-2 pl-4 py-2 cursor-pointer hover:bg-canvas-raised/50 transition-colors ${
                      isLoop ? 'border-l-mint' : isMemory ? 'border-l-indigo' : isAlert ? 'border-l-amber' : 'border-l-edge-subtle'
                    }`}
                    onClick={() => setExpandedId(isExpanded ? null : ev.event_id)}>
                    <div className="flex items-center gap-3">
                      <span className="text-2xs font-mono text-ink-tertiary w-16 shrink-0 tabular">
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : ''}
                      </span>
                      <span className={`text-2xs font-medium ${isAlert ? 'text-amber' : isMemory ? 'text-indigo' : 'text-ink-secondary'}`}>
                        {label}
                      </span>
                      {phase && <span className={`text-2xs font-mono ${phaseColor}`}>{phase}</span>}
                      {p.loop !== undefined && <span className="text-2xs font-mono text-ink-tertiary">L{p.loop as number}</span>}
                      {p.action_taken && <Badge variant="muted">{String(p.action_taken)}</Badge>}
                      {p.new_evidence_count !== undefined && (p.new_evidence_count as number) > 0 && (
                        <span className="text-2xs font-mono text-mint">+{p.new_evidence_count as number} ev</span>
                      )}
                      {p.react_action && <Badge>{String(p.react_action)}</Badge>}
                      {p.results_returned !== undefined && <span className="text-2xs font-mono text-ink-tertiary">{p.results_returned as number} results</span>}
                    </div>

                    {/* Thinking preview */}
                    {p.react_thinking && !isExpanded && (
                      <p className="text-2xs text-ink-tertiary mt-1 ml-[76px] truncate max-w-2xl">{(p.react_thinking as string).slice(0, 120)}...</p>
                    )}

                    {/* Expanded payload */}
                    {isExpanded && (
                      <div className="mt-2 ml-[76px] bg-canvas-inset border border-edge-subtle rounded p-3">
                        <pre className="text-2xs text-ink-secondary font-mono whitespace-pre-wrap break-words leading-relaxed">
                          {JSON.stringify(p, null, 2).slice(0, 1500)}
                        </pre>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
