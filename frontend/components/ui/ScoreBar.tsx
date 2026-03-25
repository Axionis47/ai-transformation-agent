interface ScoreBarProps {
  value: number
  label?: string
  color?: 'mint' | 'amber' | 'rose' | 'indigo'
  showValue?: boolean
}

const BAR_COLORS = {
  mint: 'bg-mint',
  amber: 'bg-amber',
  rose: 'bg-rose',
  indigo: 'bg-indigo',
}

const TRACK = 'bg-edge-subtle'

export default function ScoreBar({ value, label, color = 'mint', showValue = true }: ScoreBarProps) {
  const pct = Math.max(0, Math.min(100, value * 100))
  return (
    <div className="flex items-center gap-3">
      {label && <span className="text-ink-secondary text-2xs font-medium uppercase tracking-wider w-16 shrink-0">{label}</span>}
      <div className={`flex-1 h-1.5 rounded-full ${TRACK} overflow-hidden`}>
        <div className={`h-full rounded-full score-fill ${BAR_COLORS[color]}`} style={{ width: `${pct}%` }} />
      </div>
      {showValue && <span className="font-mono text-2xs text-ink tabular w-8 text-right">{value.toFixed(2)}</span>}
    </div>
  )
}
