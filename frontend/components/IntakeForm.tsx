'use client'

import { useState } from 'react'
import type { CompanyIntake } from '@/lib/types'

interface IntakeFormProps {
  onSubmit: (data: CompanyIntake) => void
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

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit({ company_name: companyName, industry, employee_count_band: employeeBand || undefined, notes: notes || undefined, constraints: [] })
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
      <button type="submit" disabled={loading} className="bg-accent text-white px-4 py-2 text-sm font-medium rounded-sm disabled:opacity-50">
        {loading ? 'Creating run...' : 'Start Analysis'}
      </button>
    </form>
  )
}
