'use client'
import { useState } from 'react'

function stepColor(text: string): string {
  const lower = text.toLowerCase()
  if (lower.includes('evidence') || lower.includes('found') || lower.includes('source')) return 'border-blue-300 bg-blue-50'
  if (lower.includes('hypothesis') || lower.includes('theory') || lower.includes('assume')) return 'border-purple-300 bg-purple-50'
  if (lower.includes('validated') || lower.includes('confirmed') || lower.includes('supports')) return 'border-green-300 bg-green-50'
  if (lower.includes('rejected') || lower.includes('contradicts') || lower.includes('disproved')) return 'border-red-300 bg-red-50'
  return 'border-gray-200 bg-gray-50'
}

function dotColor(text: string): string {
  const lower = text.toLowerCase()
  if (lower.includes('evidence') || lower.includes('found') || lower.includes('source')) return 'bg-blue-500'
  if (lower.includes('hypothesis') || lower.includes('theory') || lower.includes('assume')) return 'bg-purple-500'
  if (lower.includes('validated') || lower.includes('confirmed') || lower.includes('supports')) return 'bg-green-500'
  if (lower.includes('rejected') || lower.includes('contradicts') || lower.includes('disproved')) return 'bg-red-500'
  return 'bg-gray-400'
}

export default function ReasoningChain({ steps }: { steps: string[] }) {
  const [open, setOpen] = useState(false)
  if (steps.length === 0) return null
  return (
    <div>
      <button onClick={() => setOpen(!open)}
        className="text-sm font-medium text-gray-500 uppercase tracking-wider flex items-center gap-2 hover:text-gray-700 print:hidden">
        <span className={`transition-transform text-xs ${open ? 'rotate-90' : ''}`}>&#9654;</span>
        Reasoning Chain ({steps.length} steps)
      </button>
      {open && (
        <div className="mt-3 relative ml-4">
          <div className="absolute left-3 top-3 bottom-3 w-0.5 bg-gray-200" />
          <div className="space-y-3">
            {steps.map((step, i) => (
              <div key={i} className="flex items-start gap-3 relative">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 z-10 ${dotColor(step)}`}>
                  {i + 1}
                </div>
                <div className={`border rounded-md p-3 flex-1 ${stepColor(step)}`}>
                  <p className="text-sm text-gray-800 leading-relaxed">{step}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
