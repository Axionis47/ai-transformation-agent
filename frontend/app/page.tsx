'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import IntakeForm from '@/components/IntakeForm'
import { createRun, submitIntake } from '@/lib/api'
import type { CompanyIntake, ReasoningConfig } from '@/lib/types'

interface RecentRun {
  id: string
  company: string
  industry: string
  time: string
}

export default function HomePage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [recents, setRecents] = useState<RecentRun[]>([])

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem('recent_runs') || '[]')
      setRecents(stored.slice(0, 5))
    } catch { /* ignore */ }
  }, [])

  function saveRecent(id: string, company: string, industry: string) {
    const entry: RecentRun = { id, company, industry, time: new Date().toLocaleTimeString() }
    const updated = [entry, ...recents.filter(r => r.id !== id)].slice(0, 5)
    localStorage.setItem('recent_runs', JSON.stringify(updated))
    setRecents(updated)
  }

  async function handleSubmit(data: CompanyIntake, config: ReasoningConfig) {
    setLoading(true); setError(null)
    try {
      const run = await createRun(data.company_name, data.industry, config)
      await submitIntake(run.run_id, data)
      saveRecent(run.run_id, data.company_name, data.industry)
      router.push(`/run/${run.run_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create run')
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-xl">
        <div className="mb-10 text-center">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full bg-mint" />
            <p className="text-ink-tertiary uppercase tracking-[0.2em] text-2xs font-medium">
              AI Opportunity Mapper
            </p>
          </div>
          <h1 className="text-2xl font-bold text-ink">New Analysis</h1>
          <p className="text-sm text-ink-secondary mt-2">Evidence-backed AI transformation recommendations</p>
        </div>

        {error && (
          <div className="bg-rose/10 border border-rose/30 rounded-md p-4 mb-6">
            <p className="text-sm text-rose">{error}</p>
          </div>
        )}

        <div className="bg-canvas-raised border border-edge-subtle rounded-lg p-6">
          <IntakeForm onSubmit={handleSubmit} loading={loading} />
        </div>

        {recents.length > 0 && (
          <div className="mt-8">
            <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-3 font-medium">Recent Analyses</p>
            <div className="space-y-1">
              {recents.map(r => (
                <a key={r.id} href={`/run/${r.id}`}
                   className="flex items-center justify-between py-2.5 px-3 rounded-md hover:bg-canvas-raised transition-colors group">
                  <div className="flex items-center gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-mint/50" />
                    <span className="text-sm text-ink group-hover:text-mint transition-colors">{r.company}</span>
                    <span className="text-2xs text-ink-tertiary font-mono">{r.industry}</span>
                  </div>
                  <span className="text-2xs text-ink-tertiary">{r.time}</span>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
