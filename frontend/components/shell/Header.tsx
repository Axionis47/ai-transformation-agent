'use client'

import Link from 'next/link'
import Badge from '@/components/ui/Badge'
import type { Run } from '@/lib/types'

interface HeaderProps {
  run: Run
}

const STATUS_VARIANT: Record<string, 'mint' | 'amber' | 'rose' | 'indigo' | 'muted'> = {
  INTAKE: 'muted',
  GROUNDING: 'indigo',
  DEEP_RESEARCH: 'indigo',
  HYPOTHESIS_FORMATION: 'amber',
  HYPOTHESIS_TESTING: 'amber',
  SYNTHESIS: 'mint',
  REVIEW: 'mint',
  PUBLISHED: 'mint',
  FAILED: 'rose',
  // Legacy statuses
  created: 'muted',
  intake: 'muted',
  assumptions_draft: 'indigo',
  assumptions_confirmed: 'indigo',
  reasoning: 'amber',
  synthesis: 'amber',
  report: 'mint',
  published: 'mint',
}

function statusLabel(status: string): string {
  return status.replace(/_/g, ' ').toUpperCase()
}

function ConfidenceGauge({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  // Circumference for r=14: 2 * PI * 14 ≈ 87.96
  const radius = 14
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (value * circumference)

  return (
    <div className="flex items-center gap-2">
      <svg width="36" height="36" viewBox="0 0 36 36" className="-rotate-90">
        <circle
          cx="18" cy="18" r={radius}
          fill="none"
          stroke="#1E1E2A"
          strokeWidth="3"
        />
        <circle
          cx="18" cy="18" r={radius}
          fill="none"
          stroke="#34D399"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.6s cubic-bezier(0.16, 1, 0.3, 1)' }}
        />
      </svg>
      <span className="font-mono text-sm text-mint tabular">{pct}%</span>
    </div>
  )
}

export default function Header({ run }: HeaderProps) {
  const { company_intake: intake, status, reasoning_state: reasoning, evidence, budget_state } = run

  const toolCalls = budget_state.external_search_queries_used + budget_state.rag_queries_used
  const evidenceCount = evidence.length
  // Count unique agent types from config or use a reasonable estimate from budget usage
  const agentCount = run.config_snapshot?.orchestration_mode === 'multi_agent'
    ? (run as Record<string, unknown>).agent_count as number | undefined
    : undefined

  return (
    <header className="h-16 bg-canvas-raised border-b border-edge-subtle sticky top-0 z-30 flex items-center px-6 gap-6">
      {/* Left: back + company info */}
      <Link
        href="/"
        className="text-ink-tertiary hover:text-ink transition-colors text-sm shrink-0"
      >
        &larr; Back
      </Link>

      <div className="w-px h-6 bg-edge-subtle shrink-0" />

      {intake && (
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold text-ink truncate">
              {intake.company_name}
            </h1>
            {intake.industry && (
              <Badge>{intake.industry}</Badge>
            )}
          </div>
          {intake.employee_count_band && (
            <p className="text-2xs text-ink-secondary mt-0.5">
              {intake.employee_count_band}
            </p>
          )}
        </div>
      )}

      {/* Center: status badge */}
      <Badge variant={STATUS_VARIANT[status] || 'muted'}>
        {statusLabel(status)}
      </Badge>

      {/* Right: confidence + metrics */}
      <div className="flex items-center gap-4 shrink-0">
        {reasoning?.overall_confidence != null && (
          <ConfidenceGauge value={reasoning.overall_confidence} />
        )}

        <div className="flex items-center gap-1.5 text-2xs font-mono text-ink-tertiary">
          <span className="tabular">{toolCalls} tool calls</span>
          <span>&middot;</span>
          <span className="tabular">{evidenceCount} evidence</span>
          {agentCount != null && (
            <>
              <span>&middot;</span>
              <span className="tabular">{agentCount} agents</span>
            </>
          )}
          <span>&middot;</span>
          <a
            href={`/run/${run.run_id}/trace`}
            className="text-2xs font-mono text-ink-tertiary hover:text-ink transition-colors"
          >
            Trace
          </a>
        </div>
      </div>
    </header>
  )
}
