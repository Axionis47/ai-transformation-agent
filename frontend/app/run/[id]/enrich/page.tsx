'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { getRun, getHypotheses, enrichRun } from '@/lib/api'
import EnrichForm from '@/components/EnrichForm'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'
import type { Run, Hypothesis, EnrichmentInput, EnrichResponse } from '@/lib/types'

export default function EnrichPage() {
  const params = useParams()
  const runId = params.id as string
  const [run, setRun] = useState<Run | null>(null)
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<EnrichResponse | null>(null)

  const load = useCallback(async () => {
    try {
      const [r, h] = await Promise.all([getRun(runId), getHypotheses(runId).catch(() => [])])
      setRun(r); setHypotheses(h)
    } catch (err) { setError(err instanceof Error ? err.message : 'Failed to load run') }
  }, [runId])

  useEffect(() => { load() }, [load])

  async function handleSubmit(inputs: EnrichmentInput[]) {
    setLoading(true); setError(null)
    try {
      const res = await enrichRun(runId, inputs)
      setResult(res)
      await load() // refresh run state
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Enrichment failed')
    } finally { setLoading(false) }
  }

  if (!run) return (
    <div className="min-h-screen bg-canvas flex items-center justify-center">
      {error ? <p className="text-rose text-sm">{error}</p> : <Spinner size={24} />}
    </div>
  )

  return (
    <div className="min-h-screen bg-canvas">
      <header className="h-11 bg-canvas-raised border-b border-edge-subtle flex items-center px-5 sticky top-0 z-20">
        <Link href={`/run/${runId}/report`} className="text-2xs text-ink-tertiary hover:text-ink transition-colors font-mono">&larr; Back to Report</Link>
        <div className="w-px h-4 bg-edge mx-4" />
        <span className="text-2xs font-mono text-ink-tertiary uppercase tracking-[0.15em]">Enrich Analysis</span>
        {run.company_intake && (
          <>
            <div className="w-px h-4 bg-edge mx-4" />
            <span className="text-sm text-ink font-medium">{run.company_intake.company_name}</span>
          </>
        )}
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-xl font-semibold text-ink mb-1">Enrich with Ground Truth</h1>
          <p className="text-sm text-ink-secondary">Add what you learned from surveys, interviews, and stakeholder conversations. The system will re-evaluate affected hypotheses and update the report.</p>
        </div>

        {error && (
          <div className="bg-rose/10 border border-rose/20 rounded-md p-3 mb-6">
            <p className="text-sm text-rose font-mono">{error}</p>
          </div>
        )}

        {/* Result diff panel */}
        {result && (
          <div className="bg-mint/5 border border-mint/20 rounded-md p-5 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <Badge variant="mint">Enrichment Applied</Badge>
              <span className="text-sm text-ink-secondary">{result.evidence_added} evidence added, {result.hypotheses_affected} hypotheses re-evaluated</span>
            </div>

            {result.deltas.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium">Impact</p>
                {result.deltas.map(d => {
                  const delta = d.confidence_after - d.confidence_before
                  const up = delta > 0
                  const changed = Math.abs(delta) > 0.01
                  const statusChanged = d.status_before !== d.status_after
                  return (
                    <div key={d.hypothesis_id} className="bg-canvas-raised border border-edge-subtle rounded-md p-3">
                      <p className="text-sm text-ink font-medium line-clamp-1">{d.statement}</p>
                      <div className="flex items-center gap-4 mt-1.5 text-2xs font-mono">
                        <span className="text-ink-tertiary">{Math.round(d.confidence_before * 100)}%</span>
                        <span className={changed ? (up ? 'text-mint' : 'text-rose') : 'text-ink-tertiary'}>
                          {changed ? (up ? '↑' : '↓') : '→'} {Math.round(d.confidence_after * 100)}%
                        </span>
                        {statusChanged && (
                          <Badge variant={d.status_after === 'validated' ? 'mint' : d.status_after === 'rejected' ? 'rose' : 'amber'}>
                            {d.status_before} → {d.status_after}
                          </Badge>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            <div className="mt-4">
              <Link href={`/run/${runId}/report`}
                className="inline-flex items-center gap-2 bg-mint text-ink-inverse px-5 py-2.5 text-sm font-semibold rounded-md hover:bg-mint-bright transition-colors">
                View Updated Report
              </Link>
            </div>
          </div>
        )}

        {/* Enrich form */}
        <EnrichForm hypotheses={hypotheses} onSubmit={handleSubmit} loading={loading} />
      </main>
    </div>
  )
}
