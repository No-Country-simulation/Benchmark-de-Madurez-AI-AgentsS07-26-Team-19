import { DIMENSION_LABELS, type BenchmarkStats } from '@/types/benchmark'
import type { DimensionScore } from '@/types/diagnostic'

interface BenchmarkComparisionProps {
  dimensionScores: DimensionScore[]
  stats: BenchmarkStats[] | undefined
}

export default function BenchmarkComparision({ dimensionScores, stats }: BenchmarkComparisionProps) {
  if (!stats || stats.length === 0) return null

  const statsByDimension = new Map(stats.map((stat) => [stat.dimension, stat]))

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <ul className="divide-y divide-gray-100">
        {dimensionScores.map(({ dimension, score }) => {
          const stat = statsByDimension.get(dimension)
          const mean = stat?.mean ?? 0
          const stdDev = stat?.std_dev
          const sampleSize = stat?.sample_size

          return (
            <li key={dimension} className="px-4 py-3">
              <div className="mb-2 flex items-baseline justify-between gap-2">
                <p className="text-sm font-medium text-gray-800">
                  {DIMENSION_LABELS[dimension]}
                </p>
                {sampleSize != null && (
                  <p className="text-xs tabular-nums text-gray-400">n={sampleSize}</p>
                )}
              </div>
              <ComparisonRow label="Tu score" value={score} barClass="bg-blue-500" />
              <ComparisonRow
                label="Promedio"
                value={mean}
                barClass="bg-gray-400"
                caption={stdDev != null ? `σ ±${stdDev.toFixed(1)}` : undefined}
              />
            </li>
          )
        })}
      </ul>
    </div>
  )
}

interface ComparisonRowProps {
  label: string
  value: number
  barClass: string
  caption?: string
}

function ComparisonRow({ label, value, barClass, caption }: ComparisonRowProps) {
  const clamped = Math.max(0, Math.min(100, value))
  return (
    <div className="flex items-center gap-3">
      <span className="w-16 shrink-0 text-xs text-gray-500">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-100">
        <div className={`h-full ${barClass}`} style={{ width: `${clamped}%` }} />
      </div>
      <span className="flex w-24 shrink-0 items-baseline justify-end gap-2 text-xs tabular-nums text-gray-600">
        {value.toFixed(0)}
        {caption != null ? <span className="text-gray-400">{caption}</span> : null}
      </span>
    </div>
  )
}