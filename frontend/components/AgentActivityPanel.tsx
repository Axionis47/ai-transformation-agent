'use client'

import type { AgentState } from '@/lib/types'
import Badge from '@/components/ui/Badge'

interface AgentActivityPanelProps {
  agents: AgentState[]
}

const TYPE_VARIANT: Record<string, 'indigo' | 'amber' | 'mint' | 'rose' | 'muted'> = {
  research: 'indigo', hypothesis: 'amber', testing: 'mint', synthesis: 'rose',
}

function statusIndicator(status: string) {
  if (status === 'running') return 'bg-mint animate-pulse'
  if (status === 'completed') return 'bg-indigo'
  if (status === 'failed') return 'bg-rose'
  return 'bg-edge-subtle'
}

export default function AgentActivityPanel({ agents }: AgentActivityPanelProps) {
  const running = agents.filter(a => a.status === 'running')
  const done = agents.filter(a => a.status !== 'running')

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold text-ink uppercase tracking-wider">Agents</h3>
        {running.length > 0 && (
          <Badge variant="mint">{running.length} active</Badge>
        )}
      </div>

      {agents.length === 0 ? (
        <p className="text-sm text-ink-tertiary py-4 text-center">No agents spawned yet.</p>
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-2">
          {[...running, ...done].map(agent => {
            const isRunning = agent.status === 'running'
            const progress = agent.tool_calls_budget > 0
              ? Math.round((agent.tool_calls_made / agent.tool_calls_budget) * 100)
              : 0
            return (
              <div key={agent.agent_id}
                className={`shrink-0 w-56 bg-canvas-raised border border-edge-subtle rounded-md p-4 ${isRunning ? '' : 'opacity-75'}`}>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${statusIndicator(agent.status)}`} />
                  <Badge variant={TYPE_VARIANT[agent.agent_type] ?? 'muted'}>{agent.agent_type}</Badge>
                </div>
                {isRunning && agent.tool_calls_budget > 0 && (
                  <div className="h-1 rounded-full bg-edge-subtle overflow-hidden mb-2">
                    <div className="h-full rounded-full bg-mint transition-all duration-500"
                      style={{ width: `${progress}%` }} />
                  </div>
                )}
                <div className="flex items-center gap-3 text-2xs font-mono text-ink-tertiary">
                  <span>{agent.tool_calls_made} calls</span>
                  <span>{agent.evidence_produced.length} evidence</span>
                </div>
                {!isRunning && agent.summary && (
                  <p className="mt-2 text-2xs text-ink-secondary leading-relaxed line-clamp-2">
                    {agent.summary}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
