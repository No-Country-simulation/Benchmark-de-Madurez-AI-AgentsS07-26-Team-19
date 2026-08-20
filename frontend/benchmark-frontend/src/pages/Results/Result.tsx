import { useState } from 'react'
import {
  ArrowUpRight,
  Download,
  Printer,
  RefreshCcw,
  Target,
  TrendingUp,
} from 'lucide-react'
import ReactMarkdown, { type Components } from 'react-markdown'
import { Link, useParams } from 'react-router-dom'

import BenchmarkComparision from '@/components/results/BenchmarkComparision'
import RadarChart from '@/components/results/RadarChart'

import {
  useBenchmarkStats,
  useDiagnosticResult,
} from '@/hooks/use-benchmark'

import { ApiError } from '@/lib/api'

import {
  downloadReportPdf,
  generateReportPdf,
} from '@/services/report.service'

import { useBenchmarkStore } from '@/store/benchmark.store'

import type { DiagnosticResponseV2 } from '@/types/diagnostic'

type PdfState = 'idle' | 'loading' | 'error'

const markdownComponents: Components = {
  h1: (props) => (
    <h1
      className="mb-3 mt-5 text-lg font-bold text-white"
      {...props}
    />
  ),

  h2: (props) => (
    <h2
      className="mb-3 mt-5 text-base font-semibold text-white"
      {...props}
    />
  ),

  h3: (props) => (
    <h3
      className="mb-2 mt-4 text-sm font-semibold text-cyan-400"
      {...props}
    />
  ),

  p: (props) => (
    <p
      className="mb-3 leading-7 text-slate-300"
      {...props}
    />
  ),

  ul: (props) => (
    <ul
      className="mb-3 list-disc space-y-1.5 pl-5 text-slate-300"
      {...props}
    />
  ),

  ol: (props) => (
    <ol
      className="mb-3 list-decimal space-y-1.5 pl-5 text-slate-300"
      {...props}
    />
  ),

  li: (props) => (
    <li
      className="leading-6"
      {...props}
    />
  ),

  strong: (props) => (
    <strong
      className="font-semibold text-white"
      {...props}
    />
  ),

  em: (props) => (
    <em
      className="italic text-slate-200"
      {...props}
    />
  ),

  blockquote: (props) => (
    <blockquote
      className="mb-4 border-l-2 border-cyan-400 pl-4 text-slate-400"
      {...props}
    />
  ),

  a: (props) => (
    <a
      className="text-cyan-400 underline decoration-cyan-400/40 underline-offset-2 hover:text-cyan-300"
      {...props}
    />
  ),

  code: (props) => (
    <code
      className="rounded bg-slate-800 px-1.5 py-0.5 text-xs text-cyan-300"
      {...props}
    />
  ),
}

const dimensionLabels: Record<string, string> = {
  visibilidad: 'Visibilidad',
  friccion: 'Fricción',
  latencia: 'Latencia',
  capacidad: 'Capacidad',
  bloqueantes: 'Bloqueantes',
}

function getDimensionLabel(dimension: string) {
  const normalized = dimension
    .toLowerCase()
    .replace(/_/g, '')

  return (
    dimensionLabels[normalized] ??
    dimension
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase())
  )
}

function getScoreStatus(score: number) {
  if (score >= 80) {
    return {
      label: 'Excelente',
      text: 'text-emerald-400',
      bar: 'bg-emerald-400',
    }
  }

  if (score >= 60) {
    return {
      label: 'Buen nivel',
      text: 'text-cyan-400',
      bar: 'bg-cyan-400',
    }
  }

  if (score >= 40) {
    return {
      label: 'En desarrollo',
      text: 'text-amber-400',
      bar: 'bg-amber-400',
    }
  }

  return {
    label: 'A mejorar',
    text: 'text-red-400',
    bar: 'bg-red-400',
  }
}

export default function Result() {
  const params = useParams<{ id: string }>()

  const numericId = Number(params.id)

  const diagnosticId =
    Number.isInteger(numericId) && numericId > 0
      ? numericId
      : undefined

  const [pdfState, setPdfState] =
    useState<PdfState>('idle')

  const lastResult = useBenchmarkStore(
    (state) => state.lastResult,
  )

  const enriched: DiagnosticResponseV2 | null =
    lastResult != null &&
    lastResult.diagnostic.id === diagnosticId
      ? lastResult
      : null

  const diagnosticQuery =
    useDiagnosticResult(diagnosticId)

  const statsQuery = useBenchmarkStats()

  const result =
    enriched?.diagnostic ??
    diagnosticQuery.data

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
      return (
        <div className="min-h-[60vh] bg-[#020D1B] px-6 py-16 text-center">
          <div className="mx-auto max-w-md">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-cyan-400/20 bg-cyan-400/5">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-700 border-t-cyan-400" />
            </div>

            <p className="mt-5 text-lg font-semibold text-white">
              Cargando resultados
            </p>

            <p className="mt-2 text-sm text-slate-500">
              Estamos preparando tu diagnóstico.
            </p>
          </div>
        </div>
      )
    }

    const isNotFound =
      diagnosticQuery.error instanceof ApiError &&
      (diagnosticQuery.error.status === 404 ||
        diagnosticQuery.error.status === 422)

    return (
      <NotFound
        message={
          isNotFound
            ? 'Diagnóstico no encontrado'
            : 'No se pudieron cargar los resultados'
        }
        action="Verificá el enlace y volvé a intentar."
      />
    )
  }

  const currentResult = result

  const aiAnalysis =
    diagnosticQuery.data?.ai_analysis?.trim() ||
    currentResult.ai_analysis?.trim() ||
    ''

  const isAiPending =
    aiAnalysis.length === 0

  async function handleDownloadPdf() {
    setPdfState('loading')

    try {
      const report = await generateReportPdf(
        currentResult.id,
      )

      if (report.pdf_base64 != null) {
        downloadReportPdf(
          report.pdf_base64,
          report.filename,
        )

        setPdfState('idle')
      } else {
        setPdfState('error')
      }
    } catch {
      setPdfState('error')
    }
  }

  const overallStatus = getScoreStatus(
    currentResult.overall_score,
  )

  return (
    <div className="min-h-screen bg-[#020D1B] text-white">
      <div className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6 lg:px-8 lg:py-10">

        {/* =====================================================
            RESULTADO PRINCIPAL
        ===================================================== */}

        <section className="relative overflow-hidden rounded-3xl border border-cyan-400/10 bg-[#061525]">

          <div className="pointer-events-none absolute -right-32 -top-32 h-80 w-80 rounded-full bg-cyan-400/10 blur-3xl" />

          <div className="relative grid items-center gap-8 p-6 sm:p-8 lg:grid-cols-[0.9fr_1.1fr] lg:p-10">

            <div>

              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">
                Resultado
              </p>

              <h1 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Tu nivel de madurez
              </h1>

              <div className="mt-4 flex items-end gap-2">
                <span className="text-6xl font-bold tracking-tight text-white sm:text-7xl">
                  {currentResult.overall_score.toFixed(1)}
                </span>

                <span className="mb-2 text-lg text-slate-500">
                  /100
                </span>
              </div>

              <div className="mt-4">
                <span
                  className={`inline-flex items-center gap-2 rounded-full border border-white/5 bg-white/3 px-3 py-1.5 text-xs font-semibold ${overallStatus.text}`}
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${overallStatus.bar}`}
                  />

                  {overallStatus.label}
                </span>
              </div>

              {enriched?.cuartil_superior === true ? (
                <p className="mt-4 text-sm text-slate-400">
                  Tu resultado se encuentra dentro del
                  cuartil superior.
                </p>
              ) : null}

              <p className="mt-4 max-w-md text-sm leading-6 text-slate-500">
                Este resultado resume el nivel de madurez
                de tu organización en las principales
                dimensiones evaluadas.
              </p>

              <div className="mt-7 flex flex-wrap gap-3 print:hidden">

                <button
                  type="button"
                  onClick={() =>
                    void handleDownloadPdf()
                  }
                  disabled={
                    pdfState === 'loading'
                  }
                  className="inline-flex items-center gap-2 rounded-xl bg-[#25B9E8] px-5 py-2.5 text-sm font-semibold text-[#020D1B] transition-colors hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Download className="h-4 w-4" />

                  {pdfState === 'loading'
                    ? 'Generando…'
                    : 'Descargar informe'}
                </button>

                <button
                  type="button"
                  onClick={() =>
                    window.print()
                  }
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900/40 px-5 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-800"
                >
                  <Printer className="h-4 w-4" />

                  Imprimir
                </button>

              </div>

              {pdfState === 'error' ? (
                <p className="mt-3 text-xs text-amber-400">
                  No pudimos generar el PDF. Podés
                  utilizar la opción Imprimir.
                </p>
              ) : null}

            </div>

            {/* Radar único */}

            <div className="flex min-h-80 items-center justify-center rounded-2xl border border-white/5 bg-[#020D1B]/50 p-4">
              <div className="w-full max-w-110">
                <RadarChart
                  dimensionScores={
                    currentResult.dimensions
                  }
                />
              </div>
            </div>

          </div>
        </section>

        {/* =====================================================
            DIMENSIONES
        ===================================================== */}

        <section>

          <div className="mb-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">
              Evaluación
            </p>

            <h2 className="mt-1 text-2xl font-bold text-white">
              Tus dimensiones
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              El resultado de cada área evaluada.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">

            {currentResult.dimensions.map(
              (dimensionScore) => {
                const status =
                  getScoreStatus(
                    dimensionScore.score,
                  )

                return (
                  <div
                    key={
                      dimensionScore.dimension
                    }
                    className="rounded-2xl border border-white/5 bg-[#061525] p-5 transition-colors hover:border-cyan-400/20"
                  >

                    <div className="flex items-center justify-between gap-3">

                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                        {getDimensionLabel(
                          dimensionScore.dimension,
                        )}
                      </p>

                      <Target className="h-4 w-4 text-slate-700" />

                    </div>

                    <div className="mt-5 flex items-baseline gap-1">

                      <span className="text-3xl font-bold text-white">
                        {dimensionScore.score.toFixed(
                          1,
                        )}
                      </span>

                      <span className="text-xs text-slate-600">
                        /100
                      </span>

                    </div>

                    <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-800">
                      <div
                        className={`h-full rounded-full ${status.bar}`}
                        style={{
                          width: `${Math.min(
                            Math.max(
                              dimensionScore.score,
                              0,
                            ),
                            100,
                          )}%`,
                        }}
                      />
                    </div>

                    <p
                      className={`mt-3 text-xs font-medium ${status.text}`}
                    >
                      {status.label}
                    </p>

                  </div>
                )
              },
            )}

          </div>
        </section>

        {/* =====================================================
            COMPARACIÓN
        ===================================================== */}

        <section>

          <div className="mb-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">
              Benchmark
            </p>

            <h2 className="mt-1 text-2xl font-bold text-white">
              Comparación con la industria
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Una referencia para entender dónde estás
              parado.
            </p>
          </div>

          <div className="rounded-2xl border border-white/5 bg-[#061525] p-5 sm:p-6">

            <div className="mb-6 flex items-center gap-3">

              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-400/10">
                <TrendingUp className="h-4 w-4 text-cyan-400" />
              </div>

              <div>
                <h3 className="font-semibold text-white">
                  Tu posición
                </h3>

                <p className="text-xs text-slate-500">
                  Comparación por dimensión
                </p>
              </div>

            </div>

            <BenchmarkComparision
              dimensionScores={
                currentResult.dimensions
              }
              stats={statsQuery.data}
            />

          </div>
        </section>

        {/* =====================================================
            RESUMEN
        ===================================================== */}

        <section className="rounded-2xl border border-white/5 bg-[#061525]">

          <div className="border-b border-white/5 px-6 py-5 sm:px-7">

            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">
              Resumen
            </p>

            <h2 className="mt-1 text-xl font-bold text-white">
              Qué significa tu resultado
            </h2>

          </div>

          <div className="px-6 py-6 sm:px-7">

            {isAiPending ? (
              <div>

                <div
                  className="animate-pulse space-y-3"
                  aria-hidden
                >
                  <div className="h-3 w-full rounded bg-slate-800" />
                  <div className="h-3 w-11/12 rounded bg-slate-800" />
                  <div className="h-3 w-4/5 rounded bg-slate-800" />
                </div>

                <p className="mt-4 text-sm text-slate-500">
                  Estamos preparando tu resumen.
                </p>

                <button
                  type="button"
                  onClick={() =>
                    void diagnosticQuery.refetch()
                  }
                  disabled={
                    diagnosticQuery.isFetching
                  }
                  className="mt-4 inline-flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-xs font-medium text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-800 disabled:opacity-50"
                >
                  <RefreshCcw className="h-3.5 w-3.5" />

                  {diagnosticQuery.isFetching
                    ? 'Actualizando…'
                    : 'Actualizar'}
                </button>

              </div>
            ) : (
              <div className="max-w-4xl text-sm">
                <ReactMarkdown
                  components={
                    markdownComponents
                  }
                >
                  {aiAnalysis}
                </ReactMarkdown>
              </div>
            )}

          </div>
        </section>

        {/* =====================================================
            ÁREA DE OPORTUNIDAD
        ===================================================== */}

        {enriched != null ? (
          <section className="rounded-2xl border border-amber-400/10 bg-[#061525] p-6 sm:p-7">

            <div className="flex items-start gap-4">

              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-400/10">
                <ArrowUpRight className="h-5 w-5 text-amber-400" />
              </div>

              <div>

                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-400">
                  Área de oportunidad
                </p>

                <h2 className="mt-1 text-xl font-bold text-white">
                  {getDimensionLabel(
                    enriched.perfil_friccion
                      .dominant_dimension,
                  )}
                </h2>

                <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">
                  {
                    enriched.perfil_friccion
                      .interpretation
                  }
                </p>

              </div>

            </div>

          </section>
        ) : null}

        {/* =====================================================
            ACCIÓN FINAL
        ===================================================== */}

        <section className="flex flex-col items-center justify-center border-t border-white/5 pt-8 print:hidden">

          <p className="text-sm text-slate-500">
            ¿Querés volver a evaluar tu nivel?
          </p>

          <Link
            to="/diagnostic"
            className="mt-3 inline-flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/5 px-5 py-2.5 text-sm font-semibold text-cyan-400 transition-colors hover:border-cyan-400/40 hover:bg-cyan-400/10"
          >
            <RefreshCcw className="h-4 w-4" />

            Realizar otro diagnóstico
          </Link>

        </section>

        {/* =====================================================
            REPORTE PARA IMPRESIÓN
        ===================================================== */}

        <section className="hidden print:block rounded-xl border border-gray-200 bg-white p-6 text-gray-900">

          <h2 className="text-lg font-semibold">
            Reporte de madurez
          </h2>

          <p className="mt-2 text-sm text-gray-600">
            <strong>Score general:</strong>{' '}
            {currentResult.overall_score.toFixed(1)}
            /100
          </p>

          <h3 className="mb-2 mt-5 text-sm font-semibold">
            Scores por dimensión
          </h3>

          <ul className="list-disc pl-5 text-sm text-gray-600">

            {currentResult.dimensions.map(
              ({
                dimension,
                score,
              }) => (
                <li key={dimension}>
                  {getDimensionLabel(
                    dimension,
                  )}
                  : {score.toFixed(1)}
                  /100
                </li>
              ),
            )}

          </ul>

          {enriched != null ? (
            <div className="mt-5">

              <h3 className="text-sm font-semibold">
                Área de oportunidad
              </h3>

              <p className="mt-1 text-sm text-gray-600">
                {getDimensionLabel(
                  enriched.perfil_friccion
                    .dominant_dimension,
                )}
                {' — '}
                {
                  enriched.perfil_friccion
                    .interpretation
                }
              </p>

            </div>
          ) : null}

          {aiAnalysis.length > 0 ? (
            <div className="mt-5">

              <h3 className="text-sm font-semibold">
                Resumen
              </h3>

              <div className="mt-2 text-sm leading-relaxed text-gray-700">
                <ReactMarkdown
                  components={{
                    p: (props) => (
                      <p
                        className="mb-2"
                        {...props}
                      />
                    ),
                    strong: (props) => (
                      <strong
                        className="font-semibold"
                        {...props}
                      />
                    ),
                    ul: (props) => (
                      <ul
                        className="mb-2 list-disc pl-5"
                        {...props}
                      />
                    ),
                    li: (props) => (
                      <li {...props} />
                    ),
                  }}
                >
                  {aiAnalysis}
                </ReactMarkdown>
              </div>

            </div>
          ) : null}

        </section>

      </div>
    </div>
  )
}

function NotFound({
  message,
  action,
}: {
  message: string
  action: string
}) {
  return (
    <div className="min-h-[70vh] bg-[#020D1B] px-6 py-16 text-center">

      <div className="mx-auto max-w-md">

        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-cyan-400/10 bg-cyan-400/5">
          <Target className="h-6 w-6 text-cyan-400" />
        </div>

        <p className="mt-5 text-2xl font-bold text-white">
          {message}
        </p>

        <p className="mt-2 text-sm leading-6 text-slate-500">
          {action}
        </p>

        <Link
          to="/"
          className="mt-6 inline-flex rounded-xl bg-[#25B9E8] px-5 py-2.5 text-sm font-semibold text-[#020D1B] transition-colors hover:bg-cyan-300"
        >
          Volver al inicio
        </Link>

      </div>

    </div>
  )
}