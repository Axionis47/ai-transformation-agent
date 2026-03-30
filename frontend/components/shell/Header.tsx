'use client'

import Link from 'next/link'
import Badge from '@/components/ui/Badge'
import type { Run, AgentState } from '@/lib/types'

interface HeaderProps {
  run: Run
  agents?: AgentState[]
}

const STATUS_VARIANT: Record<string, 'mint' | 'amber' | 'rose' | 'indigo' | 'muted'> = {
  intake: 'muted',
  created: 'muted',
  grounding: 'indigo',
  deep_research: 'indigo',
  hypothesis_formation: 'amber',
  hypothesis_testing: 'amber',
  synthesis: 'mint',
  report: 'mint',
  review: 'mint',
  published: 'mint',
  failed: 'rose',
}

function statusLabel(status: string): string {
  return status.replace(/_/g, ' ').toUpperCase()
}

export default function Header({ run, agents = [] }: HeaderProps) {
  const { company_intake: intake, status, evidence, budget_state } = run
  const s = status.toLowerCase()

  const toolCalls = (budget_state.external_search_queries_used || 0) + (budget_state.rag_queries_used || 0)
  const evidenceCount = evidence.length
  const agentCount = agents.length
  const runningAgents = agents.filter(a => a.status === 'running').length

  return (
    <header className="h-12 bg-canvas-raised border-b border-edge-subtle sticky top-0 z-30 flex items-center px-6 gap-5">
      <Link href="/" className="text-ink-tertiary hover:text-ink transition-colors text-sm shrink-0">
        &larr; Back
      </Link>

      <div className="w-px h-5 bg-edge-subtle shrink-0" />

      {intake && (
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5">
            <h1 className="text-base font-semibold text-ink truncate">{intake.company_name}</h1>
            {intake.industry && <Badge>{intake.industry}</Badge>}
            {intake.employee_count_band && (
              <span className="text-2xs text-ink-tertiary font-mono">{intake.employee_count_band}</span>
            )}
          </div>
        </div>
      )}

      <Badge variant={STATUS_VARIANT[s] || 'muted'}>
        {statusLabel(status)}
      </Badge>

      <div className="flex items-center gap-3 shrink-0 text-2xs font-mono text-ink-tertiary">
        <span className="tabular">{toolCalls} calls</span>
        <span className="text-edge">&middot;</span>
        <span className="tabular">{evidenceCount} evidence</span>
        {agentCount > 0 && (
          <>
            <span className="text-edge">&middot;</span>
            <span className="tabular">
              {agentCount} agent{agentCount !== 1 ? 's' : ''}
              {runningAgents > 0 && <span className="text-mint ml-1">({runningAgents} active)</span>}
            </span>
          </>
        )}
        <span className="text-edge">&middot;</span>
        <Link href={`/run/${run.run_id}/trace`} className="hover:text-ink transition-colors">
          Trace
        </Link>
      </div>
    </header>
  )
}
