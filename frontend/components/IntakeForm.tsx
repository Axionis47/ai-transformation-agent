'use client'

import { useState } from 'react'
import type { CompanyIntake, ReasoningConfig } from '@/lib/types'

interface IntakeFormProps {
  onSubmit: (data: CompanyIntake, reasoningConfig: ReasoningConfig) => void
  loading: boolean
}

const SIZE_OPTIONS = ['50-100', '100-200', '200-500', '500-2000', '2000+']
const cls = 'w-full bg-surface border border-border text-text-primary p-2 text-sm font-mono rounded-sm focus:border-accent focus:outline-none'
const lbl = 'block text-text-muted uppercase tracking-widest mb-1'

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
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className={lbl} style={{ fontSize: '12px' }}>Company Name</label>
        <input type="text" className={cls} value={companyName} onChange={(e) => setCompanyName(e.target.value)} required placeholder="Acme Corp" />
      </div>
      <div>
        <label className={lbl} style={{ fontSize: '12px' }}>Industry</label>
        <input type="text" className={cls} value={industry} onChange={(e) => setIndustry(e.target.value)} required placeholder="logistics" />
      </div>
      <div>
        <label className={lbl} style={{ fontSize: '12px' }}>Company Size</label>
        <select className={cls} value={employeeBand} onChange={(e) => setEmployeeBand(e.target.value)}>
          <option value="">Select size</option>
          {SIZE_OPTIONS.map((opt) => <option key={opt} value={opt}>{opt} employees</option>)}
        </select>
      </div>
      <div>
        <label className={lbl} style={{ fontSize: '12px' }}>Additional Notes</label>
        <textarea className={`${cls} resize-none`} rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional context..." />
      </div>

      <div className="border-t border-border pt-4 mt-4">
        <p className="text-text-muted uppercase tracking-widest mb-3" style={{ fontSize: '11px' }}>
          Reasoning Controls
        </p>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className={lbl} style={{ fontSize: '12px' }}>Reasoning Depth</label>
              <span className="text-accent font-mono text-sm">{depth} loops</span>
            </div>
            <input
              type="range"
              min={1}
              max={10}
              step={1}
              value={depth}
              onChange={(e) => setDepth(Number(e.target.value))}
              className="w-full accent-accent"
            />
            <div className="flex justify-between text-text-muted font-mono" style={{ fontSize: '10px' }}>
              <span>Quick (1)</span>
              <span>Deep (10)</span>
            </div>
          </div>
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className={lbl} style={{ fontSize: '12px' }}>Confidence Threshold</label>
              <span className="text-accent font-mono text-sm">{(threshold * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min={0.3}
              max={1.0}
              step={0.05}
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              className="w-full accent-accent"
            />
            <div className="flex justify-between text-text-muted font-mono" style={{ fontSize: '10px' }}>
              <span>Exploratory (30%)</span>
              <span>High-confidence (100%)</span>
            </div>
          </div>
        </div>
      </div>

      <button type="submit" disabled={loading} className="bg-accent text-white px-4 py-2 text-sm font-medium rounded-sm disabled:opacity-50 w-full mt-2">
        {loading ? 'Creating run...' : 'Start Analysis'}
      </button>
    </form>
  )
}
