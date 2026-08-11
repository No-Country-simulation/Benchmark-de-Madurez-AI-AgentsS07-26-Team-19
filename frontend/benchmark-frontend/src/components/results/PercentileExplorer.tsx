import { Calculator } from 'lucide-react'
import { useState } from 'react'

import { usePercentileLookup } from '@/hooks/use-benchmark'
import { DIMENSION_LABELS, DIMENSIONS, type Dimension } from '@/types/benchmark'

interface PercentileExplorerProps {
  initialScores?: Partial<Record<Dimension, number>>
}

export default function PercentileExplorer({ initialScores }: PercentileExplorerProps) {
  const [dimension, setDimension] = useState<Dimension>(DIMENSIONS[0])
  const [score, setScore] = useState<number>(initialScores?.[DIMENSIONS[0]] ?? 50)
  const lookup = usePercentileLookup()

  function handleDimensionChange(next: Dimension) {
    setDimension(next)
    setScore(initialScores?.[next] ?? 50)
  }

  function handleLookup() {
    lookup.mutate({ dimension, score })
  }

  const disabled = lookup.isPending

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-gray-700">Dimensión</span>
          <select
            value={dimension}
            onChange={(event) => handleDimensionChange(event.target.value as Dimension)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none"
          >
            {(Object.keys(DIMENSION_LABELS) as Dimension[]).map((name) => (
              <option key={name} value={name}>
                {DIMENSION_LABELS[name]}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="mb-1 block text-sm font-medium text-gray-700">
            Score (0–100): {score}
          </span>
          <input
            type="range"
            min={0}
            max={100}
            step={1}
            value={score}
            onChange={(event) => setScore(Number(event.target.value))}
            className="w-full accent-blue-600"
          />
        </label>
      </div>

      <button
        type="button"
        onClick={handleLookup}
        disabled={disabled}
        className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Calculator className="h-4 w-4" />
        {disabled ? 'Calculando…' : 'Calcular percentil'}
      </button>

      {lookup.isPending ? (
        <p className="animate-pulse text-sm text-gray-500">Consultando el percentil…</p>
      ) : null}

      {lookup.isError ? (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          No se pudo calcular el percentil.
        </p>
      ) : null}

      {lookup.data != null ? (
        <p className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-sm text-blue-800">
          Un score de <strong>{lookup.data.score.toFixed(0)}</strong> en{' '}
          {DIMENSION_LABELS[lookup.data.dimension]} se ubica en el percentil{' '}
          <strong>{lookup.data.percentile.toFixed(0)}</strong>.
        </p>
      ) : null}
    </div>
  )
}