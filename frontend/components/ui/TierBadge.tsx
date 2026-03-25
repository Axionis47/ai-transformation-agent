const TIER_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  easy: { label: 'EASY', bg: 'bg-mint/15', text: 'text-mint' },
  medium: { label: 'MEDIUM', bg: 'bg-amber/15', text: 'text-amber' },
  hard: { label: 'HARD', bg: 'bg-rose/15', text: 'text-rose' },
}

export default function TierBadge({ tier }: { tier: string }) {
  const cfg = TIER_CONFIG[tier.toLowerCase()] ?? TIER_CONFIG.hard
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded font-mono text-2xs font-semibold tracking-wider ${cfg.bg} ${cfg.text}`}>
      {cfg.label}
    </span>
  )
}
