'use client'

import Link from 'next/link'
import Badge from '@/components/ui/Badge'

interface HeaderProps {
  companyName?: string
  industry?: string
  sizeBand?: string
  confidence?: number
  ragRemaining?: number
  ragTotal?: number
  searchRemaining?: number
  searchTotal?: number
}

export default function Header({
  companyName, industry, sizeBand,
  confidence, ragRemaining, ragTotal, searchRemaining, searchTotal,
}: HeaderProps) {
  return (
    <header className="h-14 bg-canvas-raised border-b border-edge-subtle sticky top-0 z-30 flex items-center px-6 gap-4">
      <Link href="/" className="text-ink-tertiary hover:text-ink transition-colors text-sm">
        &larr; Home
      </Link>
      <div className="w-px h-5 bg-edge-subtle" />
      {companyName && (
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <h1 className="text-xl font-semibold text-ink truncate">{companyName}</h1>
          {industry && <Badge>{industry}</Badge>}
          {sizeBand && <Badge variant="muted">{sizeBand}</Badge>}
        </div>
      )}
      <div className="flex items-center gap-3 shrink-0">
        {confidence != null && (
          <div className="flex items-center gap-1.5">
            <span className="text-2xs text-ink-tertiary uppercase tracking-wider">Understanding</span>
            <span className="font-mono text-sm text-mint tabular">{(confidence * 100).toFixed(0)}%</span>
          </div>
        )}
        {ragTotal != null && (
          <div className={`font-mono text-2xs px-2 py-1 rounded ${ragRemaining === 0 ? 'bg-rose/15 text-rose' : 'bg-canvas-overlay text-ink-secondary'}`}>
            RAG {ragRemaining}/{ragTotal}
          </div>
        )}
        {searchTotal != null && (
          <div className={`font-mono text-2xs px-2 py-1 rounded ${searchRemaining === 0 ? 'bg-rose/15 text-rose' : 'bg-canvas-overlay text-ink-secondary'}`}>
            SEARCH {searchRemaining}/{searchTotal}
          </div>
        )}
      </div>
    </header>
  )
}
