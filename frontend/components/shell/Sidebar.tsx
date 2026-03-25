'use client'

import ScoreBar from '@/components/ui/ScoreBar'

interface StageItem {
  id: string
  label: string
  status: 'completed' | 'active' | 'pending'
}

interface SidebarProps {
  stages: StageItem[]
  fieldCoverage?: Record<string, number>
  ragRemaining?: number
  ragTotal?: number
  searchRemaining?: number
  searchTotal?: number
}

function Dot({ status }: { status: string }) {
  if (status === 'completed') return <div className="w-2.5 h-2.5 rounded-full bg-mint shrink-0" />
  if (status === 'active') return <div className="w-2.5 h-2.5 rounded-full border-2 border-mint shrink-0 animate-pulse-slow" />
  return <div className="w-2.5 h-2.5 rounded-full border border-edge shrink-0" />
}

export default function Sidebar({ stages, fieldCoverage, ragRemaining, ragTotal, searchRemaining, searchTotal }: SidebarProps) {
  return (
    <aside className="w-60 bg-canvas-raised border-r border-edge-subtle shrink-0 sticky top-14 h-[calc(100vh-56px)] overflow-y-auto hidden md:block">
      <nav className="p-4">
        <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-3 font-medium">Pipeline</p>
        <div className="space-y-1">
          {stages.map((stage) => (
            <a
              key={stage.id}
              href={`#stage-${stage.id}`}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                stage.status === 'active'
                  ? 'bg-canvas-overlay text-ink border-l-2 border-mint -ml-px'
                  : stage.status === 'completed'
                  ? 'text-ink-secondary hover:bg-canvas-overlay'
                  : 'text-ink-tertiary'
              }`}
            >
              <Dot status={stage.status} />
              <span className="font-medium">{stage.label}</span>
            </a>
          ))}
        </div>
      </nav>

      {fieldCoverage && Object.keys(fieldCoverage).length > 0 && (
        <div className="px-4 pb-4">
          <div className="border-t border-edge-subtle pt-4">
            <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-3 font-medium">Coverage</p>
            <div className="space-y-2">
              {Object.entries(fieldCoverage).map(([field, score]) => {
                const color = score > 0.6 ? 'mint' : score > 0.3 ? 'amber' : 'rose'
                return <ScoreBar key={field} label={field.replace(/_/g, ' ').slice(0, 8)} value={score} color={color} />
              })}
            </div>
          </div>
        </div>
      )}

      {ragTotal != null && (
        <div className="px-4 pb-4">
          <div className="border-t border-edge-subtle pt-4">
            <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-3 font-medium">Budget</p>
            <div className="space-y-2">
              <ScoreBar
                label="RAG"
                value={(ragRemaining ?? 0) / Math.max(ragTotal, 1)}
                color={(ragRemaining ?? 0) === 0 ? 'rose' : 'mint'}
                showValue={false}
              />
              <ScoreBar
                label="Search"
                value={(searchRemaining ?? 0) / Math.max(searchTotal ?? 1, 1)}
                color={(searchRemaining ?? 0) === 0 ? 'rose' : 'mint'}
                showValue={false}
              />
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}
