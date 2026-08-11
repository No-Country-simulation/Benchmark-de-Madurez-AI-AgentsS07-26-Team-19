import { useQueries, type UseQueryResult } from '@tanstack/react-query'
import { Brain, Download, Printer, RefreshCcw } from 'lucide-react'
import { useState } from 'react'
import ReactMarkdown, { type Components } from 'react-markdown'
import { Link, useParams } from 'react-router-dom'

import BenchmarkComparision from '@/components/results/BenchmarkComparision'
import PercentileExplorer from '@/components/results/PercentileExplorer'
import PercentilesTable from '@/components/results/PercentilesTable'
import RadarChart from '@/components/results/RadarChart'
import ScoreCard from '@/components/results/ScoreCard'
import {
  useAiHealth,
  useBenchmarkStats,
  useBenchmarkWeights,
  useDiagnosticResult,
} from '@/hooks/use-benchmark'
import { ApiError } from '@/lib/api'
import { lookupPercentile } from '@/services/benchmark.service'
import { downloadReportPdf, generateReportPdf } from '@/services/report.service'
import { useBenchmarkStore } from '@/store/benchmark.store'
import type { Dimension } from '@/types/benchmark'
import type { DiagnosticResponseV2 } from '@/types/diagnostic'

type PdfState = 'idle' | 'loading' | 'error'

const markdownComponents: Components = {
  h1: (props) => <h1 className="mb-3 mt-4 text-xl font-bold text-gray-900" {...props} />,
  h2: (props) => <h2 className="mb-2 mt-4 text-lg font-semibold text-gray-900" {...props} />,
  h3: (props) => <h3 className="mb-2 mt-3 text-base font-semibold text-gray-900" {...props} />,
  p: (props) => <p className="mb-3 leading-relaxed text-gray-700" {...props} />,
  ul: (props) => <ul className="mb-3 list-disc space-y-1 pl-5 text-gray-700" {...props} />,
  ol: (props) => <ol className="mb-3 list-decimal space-y-1 pl-5 text-gray-700" {...props} />,
  li: (props) => <li className="leading-relaxed" {...props} />,
  strong: (props) => <strong className="font-semibold text-gray-900" {...props} />,
  em: (props) => <em className="italic" {...props} />,
  blockquote: (props) => (
    <blockquote
      className="mb-3 border-l-2 border-blue-300 pl-4 text-gray-600"
      {...props}
    />
  ),
  a: (props) => (
    <a className="text-blue-600 underline hover:text-blue-700" {...props} />
  ),
  code: (props) => (
    <code className="rounded bg-gray-100 px-1 py-0.5 text-xs" {...props} />
  ),
}

export default function Result() {
  const params = useParams<{ id: string }>()
  const numericId = Number(params.id)
  const diagnosticId = Number.isInteger(numericId) && numericId > 0 ? numericId : undefined

  const [pdfState, setPdfState] = useState<PdfState>('idle')

  const lastResult = useBenchmarkStore((state) => state.lastResult)
  const enriched: DiagnosticResponseV2 | null =
    lastResult != null && lastResult.diagnostic.id === diagnosticId ? lastResult : null

  const diagnosticQuery = useDiagnosticResult(diagnosticId)
  const statsQuery = useBenchmarkStats()
  const weightsQuery = useBenchmarkWeights()
  const aiHealthQuery = useAiHealth()

  const result = enriched?.diagnostic ?? diagnosticQuery.data

  const needLivePercentiles = enriched == null
  const dimensionScores = result?.dimensions ?? []

  const percentileQueries = useQueries({
    queries: dimensionScores.map(({ dimension, score }) => ({
      queryKey: ['benchmark', 'percentile-lookup', dimension, score],
      queryFn: () => lookupPercentile(dimension, score),
      enabled: needLivePercentiles,
      staleTime: 300_000,
    })),
  })

  const effectiveDimensions = dimensionScores.map((dimensionScore, index) => ({
    ...dimensionScore,
    percentile:
      (percentileQueries[index] as UseQueryResult<{ percentile: number } | undefined> | undefined)
        ?.data?.percentile ?? dimensionScore.percentile,
  }))

  if (diagnosticId === undefined) {
    return (
      <NotFound
        message="Diagnóstico no encontrado"
        action="El enlace es inválido. Volvé a realizar el diagnóstico para ver tus resultados."
      />
    )
  }

  if (result == null) {
    if (diagnosticQuery.isPending) {
      return <p className="py-16 text-center text-gray-500">Cargando resultados…</p>
    }
    const isNotFound =
      diagnosticQuery.error instanceof ApiError &&
      (diagnosticQuery.error.status === 404 || diagnosticQuery.error.status === 422)
    return (
      <NotFound
        message={isNotFound ? 'Diagnóstico no encontrado' : 'No se pudieron cargar los resultados'}
        action="Verificá el enlace y volvé a intentar."
      />
    )
  }

  const aiAnalysis = diagnosticQuery.data?.ai_analysis?.trim() || result.ai_analysis?.trim() || ''
  const isAiPending = aiAnalysis.length === 0
  const currentResult = result
  const userScores = Object.fromEntries(
    effectiveDimensions.map(({ dimension, score }) => [dimension, score]),
  ) as Partial<Record<Dimension, number>>

  const weights = enriched?.pesos ?? weightsQuery.data

  async function handleDownloadPdf() {
    setPdfState('loading')
    try {
      const report = await generateReportPdf(currentResult.id)
      if (report.pdf_base64 != null) {
        downloadReportPdf(report.pdf_base64, report.filename)
        setPdfState('idle')
      } else {
        setPdfState('error')
      }
    } catch {
      setPdfState('error')
    }
  }

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-gray-500">Score general</p>
            <p className="mt-1 text-4xl font-bold text-gray-900">
              {currentResult.overall_score.toFixed(1)}
              <span className="text-lg font-medium text-gray-400">/100</span>
            </p>
            <p className="mt-2 text-xs text-gray-500">
              Generado el {new Date(currentResult.created_at).toLocaleString()}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2 print:hidden">
            {enriched?.cuartil_superior === true ? (
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                Cuartil superior
              </span>
            ) : null}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => void handleDownloadPdf()}
                disabled={pdfState === 'loading'}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Download className="h-4 w-4" />
                {pdfState === 'loading' ? 'Generando…' : 'Descargar PDF'}
              </button>
              <button
                type="button"
                onClick={() => window.print()}
                className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
              >
                <Printer className="h-4 w-4" />
                Imprimir
              </button>
            </div>
          </div>
        </div>

        {pdfState === 'error' ? (
          <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            El servicio de PDF no está disponible. Usá “Imprimir” para exportar el reporte.
          </p>
        ) : null}
      </section>

      <section className="hidden print:block rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-gray-900">Reporte de madurez</h2>
        <p className="text-sm text-gray-600">
          <strong>Score general:</strong> {currentResult.overall_score.toFixed(1)}/100 · Generado el{' '}
          {new Date(currentResult.created_at).toLocaleString()} · ID {currentResult.id}
          {enriched?.cuartil_superior === true ? ' · Cuartil superior' : ''}
        </p>
        <h3 className="mb-2 mt-4 text-sm font-semibold text-gray-900">Scores por dimensión</h3>
        <ul className="list-disc pl-5 text-sm text-gray-600">
          {effectiveDimensions.map(({ dimension, score, percentile }) => (
            <li key={dimension}>
              <span className="capitalize">{dimension.replace('_', ' ')}</span>: {score.toFixed(1)}
              /100{percentile != null ? ` · Percentil ${percentile.toFixed(0)}` : ''}
            </li>
          ))}
        </ul>
        {enriched != null ? (
          <p className="mt-3 text-sm text-gray-600">
            <strong>Perfil de fricción:</strong>{' '}
            {enriched.perfil_friccion.dominant_dimension.replace('_', ' ')} —{' '}
            {enriched.perfil_friccion.interpretation}
          </p>
        ) : null}
        {aiAnalysis.length > 0 ? (
          <div className="mt-3">
            <h3 className="mb-2 text-sm font-semibold text-gray-900">Análisis IA</h3>
            <div className="text-sm leading-relaxed text-gray-700">
              <ReactMarkdown components={markdownComponents}>{aiAnalysis}</ReactMarkdown>
            </div>
          </div>
        ) : null}
      </section>

      <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
            <Brain className="h-5 w-5 text-purple-600" />
            Análisis IA
          </h2>
          <div className="flex items-center gap-3 print:hidden">
            <AiStatusBadge status={aiHealthQuery.data?.status} isError={aiHealthQuery.isError} />
            {isAiPending ? (
              <button
                type="button"
                onClick={() => void diagnosticQuery.refetch()}
                disabled={diagnosticQuery.isFetching}
                className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <RefreshCcw className="h-3.5 w-3.5" />
                {diagnosticQuery.isFetching ? 'Actualizando…' : 'Actualizar'}
              </button>
            ) : null}
          </div>
        </div>

        {isAiPending ? (
          <div>
            <div className="animate-pulse space-y-2" aria-hidden>
              <div className="h-3 w-full rounded bg-gray-200" />
              <div className="h-3 w-11/12 rounded bg-gray-200" />
              <div className="h-3 w-full rounded bg-gray-200" />
              <div className="h-3 w-3/4 rounded bg-gray-200" />
            </div>
            <p className="mt-3 text-sm text-gray-500">
              El modelo IA está generando el análisis del diagnóstico… Reintentamos
              automáticamente cada pocos segundos.
            </p>
          </div>
        ) : (
          <div className="text-sm leading-relaxed text-gray-700">
            <ReactMarkdown components={markdownComponents}>{aiAnalysis}</ReactMarkdown>
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Scores por dimensión</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {effectiveDimensions.map((dimensionScore) => (
            <ScoreCard key={dimensionScore.dimension} dimensionScore={dimensionScore} />
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Perfil</h2>
          <RadarChart dimensionScores={effectiveDimensions} />
        </div>
        <div>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Comparación con el promedio</h2>
          <BenchmarkComparision
            dimensionScores={effectiveDimensions}
            stats={statsQuery.data}
          />
        </div>
      </section>

      {enriched != null ? (
        <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-2 text-lg font-semibold text-gray-900">Perfil de fricción</h2>
          <p className="text-sm font-medium text-gray-800">
            Dimensión dominante:{' '}
            <span className="capitalize text-blue-700">
              {enriched.perfil_friccion.dominant_dimension.replace('_', ' ')}
            </span>
          </p>
          <p className="mt-2 text-sm leading-relaxed text-gray-600">
            {enriched.perfil_friccion.interpretation}
          </p>
        </section>
      ) : null}

      <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Percentiles de referencia</h2>
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="print:hidden">
            <h3 className="mb-3 text-sm font-semibold text-gray-800">
              Explorá tu posición
            </h3>
            <PercentileExplorer initialScores={userScores} />
          </div>
          <div>
            <h3 className="mb-3 text-sm font-semibold text-gray-800">
              Umbrales P10–P99 por dimensión
            </h3>
            <PercentilesTable userScores={userScores} />
          </div>
        </div>
        <p className="mt-4 text-xs text-gray-400">
          Percentiles calculados en vuelo sobre la población mezclada (público + reales).
        </p>
      </section>

      {weights != null ? (
        <section className="rounded-xl border border-gray-200 bg-white p-6 text-sm text-gray-600 shadow-sm">
          <h2 className="mb-2 text-lg font-semibold text-gray-900">Datos del benchmark</h2>
          <p>
            La comparación mezcla dataset público ({Math.round(weights.public_weight * 100)}%)
            con respuestas reales ({Math.round(weights.real_weight * 100)}%,
            {weights.real_count != null && weights.real_count > 0
              ? ` de ${weights.real_count} diagnósticos`
              : ' aún sin diagnósticos'}
            ).
          </p>
        </section>
      ) : null}

      <div className="flex justify-center print:hidden">
        <Link
          to="/diagnostic"
          className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-5 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
        >
          <RefreshCcw className="h-4 w-4" />
          Realizar otro diagnóstico
        </Link>
      </div>
    </div>
  )
}

interface AiStatusBadgeProps {
  status: 'ok' | 'unavailable' | undefined
  isError: boolean
}

function AiStatusBadge({ status, isError }: AiStatusBadgeProps) {
  const isOk = status === 'ok'
  const label = isError || status === undefined || !isOk ? 'IA no disponible' : 'IA activa'

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
        isOk
          ? 'bg-emerald-100 text-emerald-700'
          : 'bg-amber-100 text-amber-700'
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${isOk ? 'bg-emerald-500' : 'bg-amber-500'}`} />
      {label}
    </span>
  )
}

function NotFound({ message, action }: { message: string; action: string }) {
  return (
    <div className="py-16 text-center">
      <p className="text-2xl font-semibold text-gray-900">{message}</p>
      <p className="mt-2 text-sm text-gray-500">{action}</p>
      <Link
        to="/"
        className="mt-6 inline-block text-sm font-medium text-blue-600 hover:text-blue-700"
      >
        Volver al inicio
      </Link>
    </div>
  )
}