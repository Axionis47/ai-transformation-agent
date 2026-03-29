'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import IntakeForm from '@/components/IntakeForm'
import { createRun, submitIntake, startRun, getDefaults, checkHealth } from '@/lib/api'
import type { SystemDefaults } from '@/lib/api'
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
  const [depth, setDepth] = useState(5)
  const [threshold, setThreshold] = useState(0.7)
  const [defaults, setDefaults] = useState<SystemDefaults | null>(null)
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem('recent_runs') || '[]')
      setRecents(stored.slice(0, 8))
    } catch { /* ignore */ }
    getDefaults().then(setDefaults).catch(() => {})
    checkHealth().then(setBackendOnline)
  }, [])

  function saveRecent(id: string, company: string, industry: string) {
    const entry: RecentRun = { id, company, industry, time: new Date().toLocaleTimeString() }
    const updated = [entry, ...recents.filter(r => r.id !== id)].slice(0, 8)
    localStorage.setItem('recent_runs', JSON.stringify(updated))
    setRecents(updated)
  }

  async function handleSubmit(data: CompanyIntake, config: ReasoningConfig) {
    setLoading(true); setError(null)
    try {
      const run = await createRun(data.company_name, data.industry, config)
      await submitIntake(run.run_id, data)
      startRun(run.run_id).catch(() => {}) // fire and forget — pipeline starts in background
      saveRecent(run.run_id, data.company_name, data.industry)
      router.push(`/run/${run.run_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create run')
      setLoading(false)
    }
  }

  const stages = defaults?.pipeline_stages ?? []

  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      {/* ── Top Bar ── */}
      <header className="h-11 bg-canvas-raised border-b border-edge-subtle flex items-center px-5 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-1.5 h-1.5 rounded-full bg-mint" />
          <span className="text-2xs font-mono text-ink-tertiary uppercase tracking-[0.15em]">
            AI Opportunity Mapper
          </span>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-1.5">
          <div className={`w-1.5 h-1.5 rounded-full ${backendOnline === true ? 'bg-mint animate-pulse-slow' : backendOnline === false ? 'bg-rose' : 'bg-amber'}`} />
          <span className="text-2xs text-ink-tertiary font-mono">
            {backendOnline === true ? 'ONLINE' : backendOnline === false ? 'OFFLINE' : 'CHECKING'}
          </span>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* ── Main Workspace ── */}
        <main className="flex-1 min-w-0 overflow-y-auto">
          <div className="max-w-6xl mx-auto p-6 lg:p-8">
            <div className="mb-8">
              <h1 className="text-xl font-semibold text-ink mb-1">New Analysis</h1>
              <p className="text-sm text-ink-secondary">Enter a company to begin multi-agent AI opportunity research.</p>
            </div>

            {error && (
              <div className="bg-rose/8 border border-rose/20 rounded p-3 mb-6">
                <p className="text-sm text-rose font-mono">{error}</p>
              </div>
            )}

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              {/* Left: Form (2 cols) */}
              <div className="xl:col-span-2">
                <IntakeForm
                  onSubmit={handleSubmit}
                  loading={loading}
                  depth={depth}
                  threshold={threshold}
                  onDepthChange={setDepth}
                  onThresholdChange={setThreshold}
                />
              </div>

              {/* Right: Context Panels */}
              <div className="space-y-4">
                {/* Run Configuration — live values */}
                <div className="border border-edge-subtle rounded bg-canvas-raised">
                  <div className="px-4 py-2.5 border-b border-edge-subtle">
                    <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium">Run Configuration</p>
                  </div>
                  <div className="p-4 space-y-3">
                    <ConfigRow label="Reasoning Depth" value={`${depth} / 10`} />
                    <ConfigRow label="Confidence Target" value={`${(threshold * 100).toFixed(0)}%`} />
                    {defaults && (
                      <>
                        <ConfigRow label="Search Budget" value={`${defaults.search_budget} queries`} />
                        <ConfigRow label="RAG Budget" value={`${defaults.rag_budget} queries`} />
                        <ConfigRow label="Research Model" value={defaults.reasoning_model} />
                        <ConfigRow label="Synthesis Model" value={defaults.synthesis_model} />
                      </>
                    )}
                  </div>
                </div>

                {/* Pipeline — from backend */}
                {stages.length > 0 && (
                  <div className="border border-edge-subtle rounded bg-canvas-raised">
                    <div className="px-4 py-2.5 border-b border-edge-subtle">
                      <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium">Pipeline ({stages.length} stages)</p>
                    </div>
                    <div className="p-4">
                      <div className="space-y-1.5">
                        {stages.map((stage, i) => (
                          <div key={stage} className="flex items-center gap-2.5">
                            <span className="text-2xs text-ink-tertiary font-mono w-4 text-right">{i + 1}</span>
                            <div className="w-1.5 h-1.5 rounded-full bg-edge" />
                            <span className="text-sm text-ink-secondary">{stage}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* System Status — real health check */}
                <div className="border border-edge-subtle rounded bg-canvas-raised">
                  <div className="px-4 py-2.5 border-b border-edge-subtle">
                    <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium">System</p>
                  </div>
                  <div className="p-4 space-y-2.5">
                    <StatusRow label="Backend API" status={backendOnline === true ? 'online' : backendOnline === false ? 'offline' : 'checking'} />
                    <StatusRow label="Orchestration" status={defaults ? 'ready' : 'loading'} />
                  </div>
                </div>

                {/* Recent runs */}
                {recents.length > 0 && (
                  <div className="border border-edge-subtle rounded bg-canvas-raised">
                    <div className="px-4 py-2.5 border-b border-edge-subtle">
                      <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium">Recent Analyses</p>
                    </div>
                    <div className="divide-y divide-edge-subtle">
                      {recents.slice(0, 5).map(r => (
                        <a key={r.id} href={`/run/${r.id}`}
                          className="flex items-center justify-between px-4 py-2.5 hover:bg-canvas-overlay transition-colors">
                          <div className="flex items-center gap-2.5">
                            <span className="text-sm text-ink">{r.company}</span>
                            <span className="text-2xs text-ink-tertiary font-mono">{r.industry}</span>
                          </div>
                          <span className="text-2xs text-ink-tertiary font-mono">{r.time}</span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

function ConfigRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-ink-secondary">{label}</span>
      <span className="text-sm text-ink font-mono tabular">{value}</span>
    </div>
  )
}

function StatusRow({ label, status }: { label: string; status: 'online' | 'ready' | 'offline' | 'loading' | 'checking' }) {
  const color = (status === 'online' || status === 'ready') ? 'bg-mint' : status === 'checking' || status === 'loading' ? 'bg-amber' : 'bg-rose'
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-ink-secondary">{label}</span>
      <div className="flex items-center gap-1.5">
        <div className={`w-1.5 h-1.5 rounded-full ${color}`} />
        <span className="text-2xs text-ink-secondary font-mono uppercase">{status}</span>
      </div>
    </div>
  )
}
