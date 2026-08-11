import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

import { DIMENSION_LABELS } from '@/types/benchmark'
import type { DimensionScore } from '@/types/diagnostic'

interface RadarChartProps {
  dimensionScores: DimensionScore[]
}

export default function RadarChart({ dimensionScores }: RadarChartProps) {
  const data = dimensionScores.map(({ dimension, score }) => ({
    dimension: DIMENSION_LABELS[dimension],
    score,
  }))

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart data={data} outerRadius="70%">
          <PolarGrid />
          <PolarAngleAxis dataKey="dimension" />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
          <Radar name="Tu score" dataKey="score" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.4} />
          <Legend />
          <Tooltip />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  )
}