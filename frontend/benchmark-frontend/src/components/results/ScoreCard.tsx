import { DIMENSION_LABELS } from '@/types/benchmark'
import type { DimensionScore } from '@/types/diagnostic'

interface ScoreCardProps {
  dimensionScore: DimensionScore
}

export default function ScoreCard({ dimensionScore }: ScoreCardProps) {
  const { dimension, score, percentile } = dimensionScore

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">{DIMENSION_LABELS[dimension]}</h3>
        <span className="text-sm font-medium text-gray-600">{score.toFixed(0)}/100</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all"
          style={{ width: `${score}%` }}
        />
      </div>
      {percentile != null && (
        <p className="mt-2 text-xs text-gray-500">Percentil {percentile.toFixed(0)}</p>
      )}
    </div>
  )
}