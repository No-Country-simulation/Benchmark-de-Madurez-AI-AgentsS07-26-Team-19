import { useBenchmarkPercentiles } from '@/hooks/use-benchmark'
import { DIMENSION_LABELS, type Dimension } from '@/types/benchmark'

interface PercentilesTableProps {
  userScores?: Partial<Record<Dimension, number>>
}

export default function PercentilesTable({ userScores }: PercentilesTableProps) {
  const { data: percentiles, isPending, isError } = useBenchmarkPercentiles()

  if (isPending) {
    return <p className="animate-pulse text-sm text-gray-500">Cargando percentiles…</p>
  }

  if (isError || percentiles == null) {
    return (
      <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
        No se pudieron cargar los percentiles de referencia.
      </p>
    )
  }

  const dimensions = Object.keys(percentiles) as Dimension[]
  const percentileKeys = dimensions.length > 0 ? Object.keys(percentiles[dimensions[0]]) : []

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-gray-500">
            <th className="px-3 py-2 text-left font-medium">Dimensión</th>
            {percentileKeys.map((percentile) => (
              <th key={percentile} className="px-3 py-2 text-right font-medium">
                P{Number(percentile).toFixed(0)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dimensions.map((dimension) => {
            const thresholds = percentiles[dimension]
            const userScore = userScores?.[dimension]
            const highlighted = percentileKeys
              .filter((percentile) => Number(percentile) <= (userScore ?? Number.NEGATIVE_INFINITY))
              .pop()

            return (
              <tr key={dimension} className="border-b border-gray-100">
                <td className="px-3 py-2 font-medium text-gray-800">
                  {DIMENSION_LABELS[dimension]}
                </td>
                {percentileKeys.map((percentile) => {
                  const isHighlighted = percentile === highlighted
                  const value = thresholds?.[percentile] ?? 0

                  return (
                    <td
                      key={percentile}
                      className={`px-3 py-2 text-right ${
                        isHighlighted
                          ? 'bg-blue-50 font-semibold text-blue-700'
                          : 'text-gray-600'
                      }`}
                    >
                      {value.toFixed(0)}
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}