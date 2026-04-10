import { AGENT_TYPE_LABELS } from "@/config/constants";
import Badge from "@/components/ui/Badge";
import type { AgentState } from "@/lib/types";

function BudgetMeter({ label, used, total }: { label: string; used: number; total: number }) {
  const pct = total > 0 ? Math.min(100, (used / total) * 100) : 0;
  const exhausted = used >= total;
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-2xs font-mono text-ink-tertiary uppercase">{label}</span>
        <span
          className={`text-2xs font-mono tabular ${exhausted ? "text-rose" : "text-ink-secondary"}`}
        >
          {Math.max(0, total - used)}/{total}
        </span>
      </div>
      <div className="h-1 bg-edge-subtle rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${exhausted ? "bg-rose" : pct > 70 ? "bg-amber" : "bg-mint"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

interface TraceSidebarProps {
  agents: AgentState[];
  searchUsed: number;
  searchTotal: number;
  ragUsed: number;
  ragTotal: number;
}

export default function TraceSidebar({
  agents,
  searchUsed,
  searchTotal,
  ragUsed,
  ragTotal,
}: TraceSidebarProps) {
  return (
    <aside className="w-72 bg-canvas-raised border-r border-edge-subtle shrink-0 sticky top-12 h-[calc(100vh-48px)] overflow-y-auto hidden lg:block">
      <div className="p-4">
        <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium mb-4">
          Agents
        </p>
        {agents.length > 0 ? (
          <div className="space-y-3">
            {agents.map((agent) => {
              const label = AGENT_TYPE_LABELS[agent.agent_type] || agent.agent_type;
              const isRunning = agent.status === "running";
              const isCompleted = agent.status === "completed";
              const isFailed = agent.status === "failed";
              return (
                <div key={agent.agent_id} className="border border-edge-subtle rounded-md p-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-2xs text-ink-secondary uppercase tracking-wider font-medium">
                      {label}
                    </span>
                    <Badge
                      variant={
                        isCompleted ? "mint" : isFailed ? "rose" : isRunning ? "amber" : "muted"
                      }
                    >
                      {agent.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 text-2xs font-mono text-ink-tertiary">
                    <span>{agent.tool_calls_made} calls</span>
                    <span>{agent.evidence_produced.length} evidence</span>
                  </div>
                  {agent.summary && (
                    <p className="text-2xs text-ink-secondary mt-1.5 line-clamp-2">
                      {agent.summary}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-2xs text-ink-tertiary">No agents spawned yet.</p>
        )}

        {/* Budget -- from run state */}
        <div className="mt-6 border-t border-edge-subtle pt-4">
          <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium mb-3">
            Budget
          </p>
          <div className="space-y-3">
            <BudgetMeter label="Search" used={searchUsed} total={searchTotal} />
            <BudgetMeter label="RAG" used={ragUsed} total={ragTotal} />
          </div>
        </div>
      </div>
    </aside>
  );
}
