'use client'

import { useState } from 'react'
import type { ReasoningState } from '@/lib/types'
import ScoreBar from '@/components/ui/ScoreBar'
import Spinner from '@/components/ui/Spinner'

interface ReasoningStageProps {
  state: ReasoningState | null
  depthBudget: number
  onAnswer: (questionId: string, answer: string) => void
  loading: boolean
}

export default function ReasoningStage({ state, depthBudget, onAnswer, loading }: ReasoningStageProps) {
  const [answer, setAnswer] = useState('')

  if (!state) {
    return loading
      ? <div className="flex items-center gap-3 py-4"><Spinner /><span className="text-sm text-ink-secondary">Starting reasoning loop...</span></div>
      : null
  }

  const { current_loop, field_coverage, overall_confidence, pending_question, completed, stop_reason, coverage_gaps, escalation_reason, escalation_fields, contradictions } = state

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!pending_question || !answer.trim()) return
    onAnswer(pending_question.question_id, answer)
    setAnswer('')
  }

  const isEscalation = !!escalation_reason

  return (
    <div className="space-y-5">
      {/* Loop progress */}
      <div className="flex items-center gap-3">
        {Array.from({ length: depthBudget }).map((_, i) => (
          <div key={i} className="flex items-center gap-1.5">
            <div className={`w-8 h-1.5 rounded-full ${
              i < current_loop ? 'bg-mint' : i === current_loop && !completed ? 'bg-mint/40 animate-pulse-slow' : 'bg-edge-subtle'
            }`} />
            {i < depthBudget - 1 && <div className="w-1" />}
          </div>
        ))}
        <span className="text-sm text-ink-secondary font-mono ml-2">
          {completed ? `${current_loop} loops` : `loop ${current_loop + 1}/${depthBudget}`}
        </span>
      </div>

      {/* Understanding (renamed from Confidence) */}
      <div className="bg-canvas-raised border border-edge-subtle rounded-md p-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium">Understanding</span>
          <span className="font-mono text-lg text-ink tabular">{(overall_confidence * 100).toFixed(0)}%</span>
        </div>
        <p className="text-2xs text-ink-tertiary mb-3">How well the system understands this company across all required fields</p>
        <ScoreBar value={overall_confidence} color={overall_confidence > 0.6 ? 'mint' : overall_confidence > 0.3 ? 'amber' : 'rose'} showValue={false} />
      </div>

      {/* Field coverage */}
      {Object.keys(field_coverage).length > 0 && (
        <div className="bg-canvas-raised border border-edge-subtle rounded-md p-4">
          <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-3 font-medium">Field Coverage</p>
          <div className="space-y-2">
            {Object.entries(field_coverage).map(([field, score]) => (
              <ScoreBar key={field} label={field.replace(/_/g, ' ')} value={score}
                color={score > 0.6 ? 'mint' : score > 0.3 ? 'amber' : 'rose'} />
            ))}
          </div>
        </div>
      )}

      {/* Escalation panel (amber) — distinct from regular agent question (mint) */}
      {pending_question && !completed && isEscalation && (
        <div className="bg-canvas-overlay border border-amber/30 rounded-md p-5">
          <p className="text-2xs text-amber uppercase tracking-wider mb-2 font-medium">
            {escalation_reason?.replace(/_/g, ' ') || 'Input Required'}
          </p>
          {escalation_fields && escalation_fields.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {escalation_fields.map(f => (
                <span key={f} className="text-2xs font-mono bg-amber/10 text-amber px-2 py-0.5 rounded">{f.replace(/_/g, ' ')}</span>
              ))}
            </div>
          )}
          {contradictions && contradictions.length > 0 && (
            <div className="mb-3 text-sm text-ink-secondary border-l-2 border-amber/40 pl-3">
              <p className="text-2xs text-amber uppercase tracking-wider mb-1 font-medium">Conflicting Data</p>
              {contradictions.map((c, i) => (
                <p key={i}>{c.field}: {(c.values || []).join(' vs ')}</p>
              ))}
            </div>
          )}
          <p className="text-base text-ink leading-relaxed mb-3">{pending_question.question_text}</p>
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input type="text" value={answer} onChange={(e) => setAnswer(e.target.value)}
              placeholder="Your answer..."
              className="flex-1 bg-canvas-inset border border-edge text-ink text-sm font-sans p-2.5 rounded-md focus:border-amber focus:outline-none" />
            <button type="submit" disabled={loading || !answer.trim()}
              className="bg-amber text-ink-inverse px-4 py-2 text-sm font-semibold rounded-md disabled:opacity-40 hover:brightness-110 transition-colors">
              Submit
            </button>
          </form>
        </div>
      )}

      {/* Regular agent question (mint) */}
      {pending_question && !completed && !isEscalation && (
        <div className="bg-canvas-overlay border border-mint/30 rounded-md p-5">
          <p className="text-2xs text-mint uppercase tracking-wider mb-2 font-medium">Agent Question</p>
          <p className="text-base text-ink leading-relaxed mb-3">{pending_question.question_text}</p>
          {pending_question.context && (
            <p className="text-sm text-ink-secondary mb-3 border-l-2 border-edge pl-3 italic">{pending_question.context}</p>
          )}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input type="text" value={answer} onChange={(e) => setAnswer(e.target.value)}
              placeholder="Your answer..."
              className="flex-1 bg-canvas-inset border border-edge text-ink text-sm font-sans p-2.5 rounded-md focus:border-mint focus:outline-none" />
            <button type="submit" disabled={loading || !answer.trim()}
              className="bg-mint text-ink-inverse px-4 py-2 text-sm font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors">
              Submit
            </button>
          </form>
        </div>
      )}

      {/* Completed */}
      {completed && (
        <div className="bg-canvas-raised border border-edge-subtle rounded-md p-4 space-y-2">
          {stop_reason && (
            <div className="flex items-center gap-2">
              <span className="text-2xs text-ink-tertiary uppercase tracking-wider font-medium">Stopped</span>
              <span className="text-sm text-ink-secondary">{stop_reason.replace(/_/g, ' ')}</span>
            </div>
          )}
          {coverage_gaps.length > 0 && (
            <div>
              <p className="text-2xs text-amber uppercase tracking-wider mb-1 font-medium">Coverage Gaps</p>
              <div className="flex flex-wrap gap-1.5">
                {coverage_gaps.map(g => (
                  <span key={g} className="text-2xs font-mono bg-amber/10 text-amber px-2 py-0.5 rounded">{g.replace(/_/g, ' ')}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {loading && <div className="flex items-center gap-3"><Spinner /><span className="text-sm text-ink-secondary">Reasoning...</span></div>}
    </div>
  )
}
