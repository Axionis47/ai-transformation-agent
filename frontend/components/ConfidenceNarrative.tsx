function confidenceLabel(c: number): { text: string; color: string; barColor: string } {
  if (c >= 0.8) return { text: 'Highly Confident', color: 'text-green-700', barColor: 'bg-green-500' }
  if (c >= 0.6) return { text: 'Moderately Confident', color: 'text-amber-700', barColor: 'bg-amber-500' }
  return { text: 'Low Confidence', color: 'text-red-700', barColor: 'bg-red-500' }
}

interface ConfidenceNarrativeProps {
  assessment: string
  confidence: number
}

export default function ConfidenceNarrative({ assessment, confidence }: ConfidenceNarrativeProps) {
  // When confidence is 0 and assessment is provided, show assessment text only (report-level)
  if (confidence === 0 && assessment) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Confidence Assessment</p>
        <p className="text-sm text-gray-700 leading-relaxed">{assessment}</p>
      </div>
    )
  }
  if (confidence === 0 && !assessment) return null

  const { text, color, barColor } = confidenceLabel(confidence)
  const pct = Math.round(confidence * 100)
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className={`text-xs font-semibold uppercase tracking-wider ${color}`}>{text}</span>
        <span className="text-xs text-gray-500 font-mono">{pct}%</span>
      </div>
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
      {assessment && <p className="text-sm text-gray-600 leading-relaxed mt-1">{assessment}</p>}
    </div>
  )
}
