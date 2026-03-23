'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import IntakeForm from '@/components/IntakeForm'
import { createRun, submitIntake } from '@/lib/api'
import type { CompanyIntake } from '@/lib/types'

export default function HomePage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(data: CompanyIntake) {
    setLoading(true)
    setError(null)
    try {
      const run = await createRun(data.company_name, data.industry)
      await submitIntake(run.run_id, data)
      router.push(`/run/${run.run_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create run')
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-lg">
        <div className="mb-8">
          <p className="text-text-muted uppercase tracking-widest mb-1" style={{ fontSize: '12px' }}>
            AI OPPORTUNITY MAPPER
          </p>
          <h1 className="text-text-primary" style={{ fontSize: '18px', fontWeight: 600 }}>
            New Analysis
          </h1>
        </div>

        {error && (
          <div className="border border-tier-hard bg-surface p-3 mb-4 rounded-sm">
            <p className="font-mono text-tier-hard" style={{ fontSize: '13px' }}>{error}</p>
          </div>
        )}

        <IntakeForm onSubmit={handleSubmit} loading={loading} />
      </div>
    </main>
  )
}
