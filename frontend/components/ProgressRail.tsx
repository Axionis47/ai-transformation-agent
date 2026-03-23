'use client'

interface ProgressItem {
  stage: string
  status: string
}

interface ProgressRailProps {
  progress: ProgressItem[]
}

const STAGE_LABELS: Record<string, string> = {
  created: 'CREATE',
  intake: 'INTAKE',
  assumptions_draft: 'ASSUME',
  assumptions_confirmed: 'CONFMD',
  reasoning: 'REASON',
  synthesis: 'SYNTH',
  report: 'REPORT',
  published: 'PUBLD',
}

export default function ProgressRail({ progress }: ProgressRailProps) {
  return (
    <div className="w-12 flex flex-col items-center py-6 relative">
      {progress.map((item, idx) => (
        <div key={item.stage} className="flex flex-col items-center relative">
          {idx > 0 && (
            <div
              className={`w-px h-4 ${
                item.status === 'completed' || item.status === 'active'
                  ? 'bg-accent'
                  : 'bg-border'
              }`}
            />
          )}
          <div
            className={`w-2 h-2 rounded-full border ${
              item.status === 'completed'
                ? 'bg-accent border-accent'
                : item.status === 'active'
                ? 'bg-transparent border-accent'
                : 'bg-transparent border-border'
            }`}
          />
          <span className="text-text-muted font-mono mt-1 mb-1 leading-none"
                style={{ fontSize: '9px', letterSpacing: '0.05em' }}>
            {STAGE_LABELS[item.stage] ?? item.stage.slice(0, 6).toUpperCase()}
          </span>
        </div>
      ))}
    </div>
  )
}
