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
  const [depth, setDepth] = useState(5)
  const [threshold, setThreshold] = useState(0.7)

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem('recent_runs') || '[]')
      setRecents(stored.slice(0, 8))
    } catch { /* ignore */ }
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
      saveRecent(run.run_id, data.company_name, data.industry)
      router.push(`/run/${run.run_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create run')
      setLoading(false)
    }
  }

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
        <div className="w-px h-4 bg-edge mx-4" />
        <span className="text-2xs text-ink-tertiary font-mono">v1.0</span>
        <div className="flex-1" />
        <span className="text-2xs text-ink-tertiary font-mono tabular">
          {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        </span>
        <div className="w-px h-4 bg-edge mx-4" />
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-mint animate-pulse-slow" />
          <span className="text-2xs text-ink-tertiary font-mono">READY</span>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* ── Left Rail ── */}
        <nav className="w-48 bg-canvas-raised border-r border-edge-subtle shrink-0 flex flex-col py-4 hidden lg:flex">
          <div className="px-4 mb-5">
            <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium mb-3">Workspace</p>
            <div className="space-y-0.5">
              {[
                { label: 'New Analysis', active: true },
                { label: 'Recent Runs', active: false },
              ].map(item => (
                <button key={item.label}
                  className={`w-full text-left px-2.5 py-1.5 text-sm rounded transition-colors ${
                    item.active
                      ? 'bg-canvas-overlay text-ink border-l-2 border-mint -ml-px pl-2'
                      : 'text-ink-tertiary hover:text-ink-secondary hover:bg-canvas-overlay/50'
                  }`}>
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          <div className="px-4 mb-5">
            <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium mb-3">Pipeline</p>
            <div className="space-y-0.5">
              {['Assumptions', 'Evidence', 'Opportunities', 'Reports'].map(label => (
                <button key={label}
                  className="w-full text-left px-2.5 py-1.5 text-sm text-ink-tertiary rounded transition-colors hover:text-ink-secondary hover:bg-canvas-overlay/50 cursor-default opacity-40">
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Recent runs in rail */}
          {recents.length > 0 && (
            <div className="px-4 mt-auto">
              <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium mb-2">History</p>
              <div className="space-y-0.5">
                {recents.slice(0, 5).map(r => (
                  <a key={r.id} href={`/run/${r.id}`}
                    className="block px-2.5 py-1.5 text-2xs text-ink-tertiary hover:text-mint transition-colors truncate rounded hover:bg-canvas-overlay/50">
                    {r.company} <span className="text-ink-tertiary/50 font-mono">· {r.industry}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </nav>

        {/* ── Main Workspace ── */}
        <main className="flex-1 min-w-0 overflow-y-auto">
          <div className="max-w-6xl mx-auto p-6 lg:p-8">
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 mb-6">
              <span className="text-2xs text-ink-tertiary font-mono uppercase tracking-wider">Workspace</span>
              <span className="text-2xs text-ink-tertiary">/</span>
              <span className="text-2xs text-mint font-mono uppercase tracking-wider">New Analysis</span>
            </div>

            {/* Page Title */}
            <div className="mb-8">
              <h1 className="text-xl font-semibold text-ink mb-1">New Analysis Run</h1>
              <p className="text-sm text-ink-secondary">Configure target company and reasoning parameters to begin evidence-backed opportunity discovery.</p>
            </div>

            {error && (
              <div className="bg-rose/8 border border-rose/20 rounded p-3 mb-6">
                <p className="text-sm text-rose font-mono">{error}</p>
              </div>
            )}

            {/* Two-column workspace */}
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

              {/* Right: Context Panel */}
              <div className="space-y-4">
                {/* Run Configuration Summary */}
                <div className="border border-edge-subtle rounded bg-canvas-raised">
                  <div className="px-4 py-2.5 border-b border-edge-subtle">
                    <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium">Run Configuration</p>
                  </div>
                  <div className="p-4 space-y-3">
                    <ConfigRow label="Reasoning Depth" value={`${depth} / 10`} />
                    <ConfigRow label="Stop Threshold" value={`≥${(threshold * 100).toFixed(0)}%`} />
                    <ConfigRow label="RAG Budget" value="15 queries" />
                    <ConfigRow label="Search Budget" value="10 queries" />
                    <ConfigRow label="Model" value="Gemini 2.5" />
                  </div>
                </div>

                {/* Execution Estimate */}
                <div className="border border-edge-subtle rounded bg-canvas-raised">
                  <div className="px-4 py-2.5 border-b border-edge-subtle">
                    <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium">Execution Estimate</p>
                  </div>
                  <div className="p-4 space-y-3">
                    <ConfigRow label="Pipeline" value="5 stages" />
                    <ConfigRow label="Reasoning Loops" value={`up to ${depth}`} />
                    <ConfigRow label="Evidence Sources" value="KB + Web" />
                    <ConfigRow label="Output" value="3-tier report" />
                  </div>
                </div>

                {/* System Status */}
                <div className="border border-edge-subtle rounded bg-canvas-raised">
                  <div className="px-4 py-2.5 border-b border-edge-subtle">
                    <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium">System Status</p>
                  </div>
                  <div className="p-4 space-y-2.5">
                    <StatusRow label="Grounder" status="online" />
                    <StatusRow label="RAG Store" status="online" />
                    <StatusRow label="Reasoning Engine" status="standby" />
                    <StatusRow label="Pitch Synthesis" status="standby" />
                  </div>
                </div>

                {/* Recent Analyses (mobile/tablet fallback) */}
                {recents.length > 0 && (
                  <div className="border border-edge-subtle rounded bg-canvas-raised lg:hidden">
                    <div className="px-4 py-2.5 border-b border-edge-subtle">
                      <p className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium">Recent Analyses</p>
                    </div>
                    <div className="divide-y divide-edge-subtle">
                      {recents.map(r => (
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

      {/* ── Bottom Status Bar ── */}
      <footer className="h-7 bg-canvas-raised border-t border-edge-subtle flex items-center px-5 shrink-0">
        <span className="text-2xs text-ink-tertiary font-mono">AI Opportunity Mapper</span>
        <div className="flex-1" />
        <div className="flex items-center gap-4">
          <span className="text-2xs text-ink-tertiary font-mono">RAG: 15 avail</span>
          <span className="text-2xs text-ink-tertiary font-mono">SEARCH: 10 avail</span>
          <span className="text-2xs text-ink-tertiary font-mono">DEPTH: {depth}</span>
        </div>
      </footer>
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

function StatusRow({ label, status }: { label: string; status: 'online' | 'standby' | 'offline' }) {
  const color = status === 'online' ? 'bg-mint' : status === 'standby' ? 'bg-amber' : 'bg-rose'
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
