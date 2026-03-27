'use client'

import { useState } from 'react'
import type { Hypothesis, HypothesisStatus } from '@/lib/types'
import Badge from '@/components/ui/Badge'
import ScoreBar from '@/components/ui/ScoreBar'

interface HypothesisCardProps {
  hypothesis: Hypothesis
}

const STATUS_BADGE: Record<HypothesisStatus, { variant: 'indigo' | 'amber' | 'mint' | 'rose' | 'muted'; label: string }> = {
  forming:          { variant: 'indigo', label: 'Forming' },
  testing:          { variant: 'amber',  label: 'Testing' },
  validated:        { variant: 'mint',   label: 'Validated' },
  rejected:         { variant: 'rose',   label: 'Rejected' },
  needs_user_input: { variant: 'muted',  label: 'Needs Input' },
}

const STATUS_BORDER: Record<HypothesisStatus, string> = {
  forming: 'border-l-indigo', testing: 'border-l-amber',
  validated: 'border-l-mint', rejected: 'border-l-rose',
  needs_user_input: 'border-l-edge',
}

function confidenceColor(c: number): 'mint' | 'amber' | 'rose' {
  if (c >= 0.7) return 'mint'
  if (c >= 0.4) return 'amber'
  return 'rose'
}

export default function HypothesisCard({ hypothesis }: HypothesisCardProps) {
  const [expanded, setExpanded] = useState(false)
  const { status, confidence, evidence_for, evidence_against } = hypothesis
  const badge = STATUS_BADGE[status]
  const isRejected = status === 'rejected'
  const isForming = status === 'forming'

  return (
    <div className={`bg-canvas-raised border border-edge-subtle border-l-[3px] ${STATUS_BORDER[status]} rounded-md overflow-hidden ${isRejected ? 'opacity-60' : ''}`}>
      <div className="px-5 py-4 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-start justify-between gap-4">
          <h3 className={`text-base font-semibold text-ink leading-snug ${isRejected ? 'line-through' : ''}`}>
            {hypothesis.statement}
          </h3>
          <div className="flex items-center gap-2 shrink-0">
            {isForming && <span className="w-2 h-2 rounded-full bg-indigo animate-pulse" />}
            <Badge variant={badge.variant}>{badge.label}</Badge>
          </div>
        </div>

        <div className="mt-3">
          <ScoreBar label="Conf." value={confidence} color={confidenceColor(confidence)} />
        </div>

        <div className="flex items-center gap-4 mt-3 text-2xs font-mono">
          <span className="text-mint">{evidence_for.length} for</span>
          <span className="text-rose">{evidence_against.length} against</span>
          <span className="text-ink-tertiary ml-auto">{hypothesis.category}</span>
        </div>
      </div>

      <div className={`grid transition-all duration-300 ${expanded ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}>
        <div className="overflow-hidden">
          <div className="px-5 pb-5 border-t border-edge-subtle pt-4 space-y-3">
            {hypothesis.reasoning_chain.length > 0 && (<div>
              <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-2 font-medium">Reasoning</p>
              <ul className="space-y-1">{hypothesis.reasoning_chain.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-ink-secondary">
                  <span className="mt-1 w-1.5 h-1.5 rounded-full bg-indigo/50 shrink-0" />{s.description}
                </li>))}
              </ul></div>)}
            {hypothesis.test_results.length > 0 && (<div>
              <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-2 font-medium">Test Results</p>
              <ul className="space-y-1">{hypothesis.test_results.map((t, i) => (
                <li key={i} className="text-sm text-ink-secondary">
                  <span className="font-mono text-2xs text-amber mr-2">{t.test_type}</span>{t.finding}
                </li>))}
              </ul></div>)}
            {hypothesis.risks.length > 0 && (<div>
              <p className="text-2xs text-rose uppercase tracking-wider mb-2 font-medium">Risks</p>
              <ul className="space-y-1">{hypothesis.risks.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-ink-secondary">
                  <span className="mt-1 w-1.5 h-1.5 rounded-full bg-rose/50 shrink-0" />{r}
                </li>))}
              </ul></div>)}
          </div>
        </div>
      </div>
    </div>
  )
}
