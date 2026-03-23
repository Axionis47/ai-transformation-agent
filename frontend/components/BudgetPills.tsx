'use client'

import type { BudgetView } from '@/lib/types'

interface BudgetPillsProps {
  budget: BudgetView
  ragTotal?: number
  searchTotal?: number
}

function pillColor(remaining: number, total: number): string {
  if (remaining === 0) return 'text-tier-hard'
  if (remaining / total < 0.5) return 'text-tier-medium'
  return 'text-tier-easy'
}

export default function BudgetPills({
  budget,
  ragTotal = 8,
  searchTotal = 5,
}: BudgetPillsProps) {
  const ragColor = pillColor(budget.rag_queries_remaining, ragTotal)
  const searchColor = pillColor(
    budget.external_search_queries_remaining,
    searchTotal,
  )

  return (
    <div className="fixed top-3 right-4 z-10 flex gap-2">
      <span
        className={`font-mono px-2 py-0.5 bg-surface border border-border rounded-sm ${ragColor}`}
        style={{ fontSize: '11px' }}
      >
        RAG {budget.rag_queries_remaining}/{ragTotal}
      </span>
      <span
        className={`font-mono px-2 py-0.5 bg-surface border border-border rounded-sm ${searchColor}`}
        style={{ fontSize: '11px' }}
      >
        SEARCH {budget.external_search_queries_remaining}/{searchTotal}
      </span>
    </div>
  )
}
