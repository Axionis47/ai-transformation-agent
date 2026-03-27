'use client'

import { useState } from 'react'
import type { ReportFeedback } from '@/lib/types'

interface FeedbackButtonProps {
  targetSection: string
  onSubmit: (feedback: ReportFeedback) => void
}

export default function FeedbackButton({ targetSection, onSubmit }: FeedbackButtonProps) {
  const [open, setOpen] = useState(false)
  const [instruction, setInstruction] = useState('')

  function handleSubmit() {
    if (!instruction.trim()) return
    onSubmit({
      feedback_type: 'edit',
      target_section: targetSection,
      instruction: instruction.trim(),
    })
    setInstruction('')
    setOpen(false)
  }

  function handleCancel() {
    setInstruction('')
    setOpen(false)
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="opacity-0 group-hover:opacity-100 transition-opacity text-ink-tertiary hover:text-mint text-2xs font-mono flex items-center gap-1 px-1.5 py-0.5 rounded print:hidden"
        title="Edit this section"
      >
        <span className="text-xs leading-none">&#9998;</span>
        Edit
      </button>
    )
  }

  return (
    <div className="bg-canvas-overlay border border-edge rounded-md p-3 mt-3 print:hidden">
      <p className="text-2xs text-ink-secondary font-medium mb-2">
        What should change in this section?
      </p>
      <textarea
        value={instruction}
        onChange={(e) => setInstruction(e.target.value)}
        placeholder="e.g. Focus on cost savings, not technology..."
        rows={2}
        className="w-full bg-canvas-inset border border-edge text-ink text-sm p-2.5 rounded focus:border-mint focus:outline-none resize-none placeholder:text-ink-tertiary"
        autoFocus
      />
      <div className="flex items-center justify-end gap-2 mt-2">
        <button
          onClick={handleCancel}
          className="text-ink-tertiary text-xs px-3 py-1.5 hover:text-ink-secondary transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={!instruction.trim()}
          className="bg-mint text-ink-inverse text-xs font-semibold px-3 py-1.5 rounded disabled:opacity-40 hover:bg-mint-bright transition-colors"
        >
          Apply Change
        </button>
      </div>
    </div>
  )
}
