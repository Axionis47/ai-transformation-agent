'use client'

import { useState } from 'react'
import Spinner from '@/components/ui/Spinner'
import type { CompanyIntake, ReasoningConfig } from '@/lib/types'

interface IntakeFormProps {
  onSubmit: (data: CompanyIntake, config: ReasoningConfig) => void
  loading: boolean
}

const SIZE_OPTIONS = ['50-100', '100-200', '200-500', '500-2000', '2000+']
const input = 'w-full bg-canvas-inset border border-edge text-ink text-sm font-sans p-2.5 rounded-md focus:border-mint focus:outline-none transition-colors'
const label = 'block text-2xs text-ink-tertiary uppercase tracking-wider mb-1.5 font-medium'

export default function IntakeForm({ onSubmit, loading }: IntakeFormProps) {
  const [companyName, setCompanyName] = useState('')
  const [industry, setIndustry] = useState('')
  const [employeeBand, setEmployeeBand] = useState('')
  const [notes, setNotes] = useState('')
  const [depth, setDepth] = useState(5)
  const [threshold, setThreshold] = useState(0.7)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit(
      { company_name: companyName, industry, employee_count_band: employeeBand || undefined, notes: notes || undefined, constraints: [] },
      { reasoning_depth: depth, confidence_threshold: threshold },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2 sm:col-span-1">
          <label className={label}>Company Name</label>
          <input type="text" className={input} value={companyName} onChange={(e) => setCompanyName(e.target.value)} required placeholder="Ramp" />
        </div>
        <div className="col-span-2 sm:col-span-1">
          <label className={label}>Industry</label>
          <input type="text" className={input} value={industry} onChange={(e) => setIndustry(e.target.value)} required placeholder="fintech" />
        </div>
      </div>
      <div>
        <label className={label}>Company Size</label>
        <select className={input} value={employeeBand} onChange={(e) => setEmployeeBand(e.target.value)}>
          <option value="">Select size band</option>
          {SIZE_OPTIONS.map(opt => <option key={opt} value={opt}>{opt} employees</option>)}
        </select>
      </div>
      <div>
        <label className={label}>Additional Notes</label>
        <textarea className={`${input} resize-none`} rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Focus areas, constraints, context..." />
      </div>

      <div className="border-t border-edge-subtle pt-5 space-y-4">
        <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium">Reasoning</p>
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className={label}>Analysis Depth</label>
            <span className="font-mono text-sm text-mint tabular">{depth}</span>
          </div>
          <input type="range" min={1} max={10} step={1} value={depth} onChange={(e) => setDepth(Number(e.target.value))}
            className="w-full h-1.5 bg-edge-subtle rounded-full appearance-none cursor-pointer accent-mint" />
          <div className="flex justify-between mt-1">
            <span className="text-2xs text-ink-tertiary">Quick</span>
            <span className="text-2xs text-ink-tertiary">Deep</span>
          </div>
        </div>
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className={label}>Confidence Target</label>
            <span className="font-mono text-sm text-mint tabular">{(threshold * 100).toFixed(0)}%</span>
          </div>
          <input type="range" min={0.3} max={1.0} step={0.05} value={threshold} onChange={(e) => setThreshold(Number(e.target.value))}
            className="w-full h-1.5 bg-edge-subtle rounded-full appearance-none cursor-pointer accent-mint" />
          <div className="flex justify-between mt-1">
            <span className="text-2xs text-ink-tertiary">Exploratory</span>
            <span className="text-2xs text-ink-tertiary">High-confidence</span>
          </div>
        </div>
      </div>

      <button type="submit" disabled={loading}
        className="w-full bg-mint text-ink-inverse py-3 text-sm font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors flex items-center justify-center gap-2">
        {loading ? <><Spinner size={14} />Creating run...</> : 'Start Analysis'}
      </button>
    </form>
  )
}
