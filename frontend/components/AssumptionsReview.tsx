'use client'

import { useState } from 'react'
import type { AssumptionsDraft, Assumption } from '@/lib/types'

interface AssumptionsReviewProps {
  assumptions: AssumptionsDraft
  onConfirm: (edited: AssumptionsDraft) => void
  loading: boolean
}

const cls = 'bg-surface border border-border text-text-primary p-1 text-sm font-mono rounded-sm focus:border-accent focus:outline-none w-48'

export default function AssumptionsReview({ assumptions, onConfirm, loading }: AssumptionsReviewProps) {
  const [items, setItems] = useState<Assumption[]>(assumptions.assumptions)

  function updateValue(idx: number, val: string) {
    setItems((prev) => prev.map((a, i) => i === idx ? { ...a, value: val } : a))
  }

  function handleConfirm() {
    onConfirm({ assumptions: items, open_questions: assumptions.open_questions })
  }

  return (
    <div className="space-y-2">
      {items.map((assumption, idx) => (
        <div key={assumption.field} className="flex justify-between items-center border-b border-border py-1.5">
          <div>
            <span className="text-text-muted uppercase tracking-widest" style={{ fontSize: '12px', fontWeight: 500 }}>
              {assumption.field.replace(/_/g, ' ')}
            </span>
            <span className="font-mono text-border ml-2" style={{ fontSize: '10px' }}>
              [{assumption.source}] {assumption.confidence.toFixed(2)}
            </span>
          </div>
          <input type="text" className={cls} value={items[idx].value} onChange={(e) => updateValue(idx, e.target.value)} />
        </div>
      ))}
      {assumptions.open_questions.length > 0 && (
        <div className="pt-2">
          <p className="text-text-muted uppercase tracking-widest mb-1" style={{ fontSize: '12px' }}>Open Questions</p>
          {assumptions.open_questions.map((q, i) => (
            <p key={i} className="text-text-muted font-mono" style={{ fontSize: '13px' }}>{q}</p>
          ))}
        </div>
      )}
      <div className="pt-3">
        <button onClick={handleConfirm} disabled={loading} className="bg-accent text-white px-4 py-2 text-sm font-medium rounded-sm disabled:opacity-50">
          {loading ? 'Confirming...' : 'Confirm Assumptions'}
        </button>
      </div>
    </div>
  )
}
