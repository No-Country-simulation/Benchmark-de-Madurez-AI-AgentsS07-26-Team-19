import { ArrowRight, Cpu, Server } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { useAiHealth, useApiHealth } from '@/hooks/use-benchmark'
import { DIMENSION_LABELS, DIMENSIONS } from '@/types/benchmark'

const DIMENSION_DESCRIPTIONS: Record<(typeof DIMENSIONS)[number], string> = {
  visibility: 'Vista unificada de energía, cooling y workloads.',
  friction: 'Identificación de la interfaz donde se pierde capacidad.',
  latency: 'Velocidad de ajuste ante cambios de workload.',
  quantification: 'Conocimiento de la stranded capacity propia.',
  blockers: 'Obstáculos organizacionales o técnicos.',
}

export default function Home() {
  const apiHealthQuery = useApiHealth()
  const aiHealthQuery = useAiHealth()

  return (
    <div className="space-y-12">
      <section className="rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm sm:p-12">
        <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
          ¿Qué tan maduro es tu data center?
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-gray-600">
          Evaluá la madurez de liderazgo de tu operación en 5 dimensiones. Respondé un breve
          diagnóstico y compará tu resultado contra el benchmark de la población.
        </p>
        <Link
          to="/diagnostic"
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          Comenzar diagnóstico
          <ArrowRight className="h-4 w-4" />
        </Link>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Estado del sistema</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <HealthCard
            icon={<Server className="h-5 w-5" />}
            title="API"
            ok={apiHealthQuery.data?.status === 'ok'}
            loading={apiHealthQuery.isPending}
            extra={apiHealthQuery.data?.environment}
          />
          <HealthCard
            icon={<Cpu className="h-5 w-5" />}
            title="Modelo IA"
            ok={aiHealthQuery.data?.status === 'ok'}
            loading={aiHealthQuery.isPending}
          />
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Las 5 dimensiones</h2>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {DIMENSIONS.map((dimension) => (
            <li
              key={dimension}
              className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"
            >
              <h3 className="flex items-center gap-2 font-semibold text-gray-900">
                <span className="h-2.5 w-2.5 rounded-full bg-blue-500" />
                {DIMENSION_LABELS[dimension]}
              </h3>
              <p className="mt-2 text-sm text-gray-600">{DIMENSION_DESCRIPTIONS[dimension]}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

interface HealthCardProps {
  icon: ReactNode
  title: string
  ok: boolean
  loading: boolean
  extra?: string
}

function HealthCard({ icon, title, ok, loading, extra }: HealthCardProps) {
  const isOk = ok && !loading
  return (
    <div className="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <span
        className={`flex h-10 w-10 items-center justify-center rounded-lg ${
          isOk ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'
        }`}
      >
        {icon}
      </span>
      <div className="flex-1">
        <p className="text-sm font-semibold text-gray-900">{title}</p>
        <p className="text-xs text-gray-500">
          {loading
            ? 'Verificando…'
            : isOk
              ? 'Disponible'
              : 'No disponible'}
          {isOk && extra != null ? ` · ${extra}` : ''}
        </p>
      </div>
      <span
        className={`h-2.5 w-2.5 rounded-full ${
          loading ? 'animate-pulse bg-gray-300' : isOk ? 'bg-emerald-500' : 'bg-red-500'
        }`}
      />
    </div>
  )
}