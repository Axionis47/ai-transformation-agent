'use client'

import { useState, useMemo } from 'react'
import type { Hypothesis, HypothesisStatus } from '@/lib/types'
import HypothesisCard from '@/components/cards/HypothesisCard'
import Badge from '@/components/ui/Badge'

interface HypothesisListProps {
  hypotheses: Hypothesis[]
}

type Filter = 'all' | HypothesisStatus

const TABS: { key: Filter; label: string; variant: 'default' | 'indigo' | 'amber' | 'mint' | 'rose' | 'muted' }[] = [
  { key: 'all',       label: 'All',       variant: 'default' },
  { key: 'forming',   label: 'Forming',   variant: 'indigo' },
  { key: 'testing',   label: 'Testing',   variant: 'amber' },
  { key: 'validated', label: 'Validated', variant: 'mint' },
  { key: 'rejected',  label: 'Rejected',  variant: 'rose' },
]

export default function HypothesisList({ hypotheses }: HypothesisListProps) {
  const [filter, setFilter] = useState<Filter>('all')

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: hypotheses.length }
    for (const h of hypotheses) c[h.status] = (c[h.status] || 0) + 1
    return c
  }, [hypotheses])

  const filtered = useMemo(() => {
    const list = filter === 'all' ? hypotheses : hypotheses.filter(h => h.status === filter)
    return [...list].sort((a, b) => b.confidence - a.confidence)
  }, [hypotheses, filter])

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 flex-wrap">
        {TABS.map(tab => {
          const active = filter === tab.key
          const count = counts[tab.key] || 0
          return (
            <button key={tab.key} onClick={() => setFilter(tab.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                active ? 'bg-canvas-raised text-ink border border-edge-subtle' : 'text-ink-tertiary hover:text-ink-secondary'
              }`}>
              {tab.label}
              <Badge variant={active ? tab.variant : 'muted'}>{count}</Badge>
            </button>
          )
        })}
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-ink-tertiary py-8 text-center">No hypotheses in this state yet.</p>
      ) : (
        <div className="space-y-3">
          {filtered.map(h => <HypothesisCard key={h.hypothesis_id} hypothesis={h} />)}
        </div>
      )}
    </div>
  )
}
