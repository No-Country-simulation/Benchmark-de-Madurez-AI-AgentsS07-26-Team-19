import {ArrowLeft, ArrowRight} from 'lucide-react'

interface StepNavigationProps {
  currentIndex: number
  isLast: boolean
  canGoNext: boolean
  isSubmitting?: boolean
  onPrevious: () => void
  onNext: () => void
  onSubmit: () => void
}

export default function StepNavigation({
  currentIndex,
  isLast,
  canGoNext,
  isSubmitting = false,
  onPrevious,
  onNext,
  onSubmit,
}: StepNavigationProps) {
  return (
    <div className="flex items-center justify-between">
      <button
        type="button"
        onClick={onPrevious}
        disabled={currentIndex === 0}
        className={cnButton(currentIndex > 0, 'border border-[#25B9E8] text-white hover:border-blue-400 hover:text-white hover:bg-[#25B9E8]')}
      >
        <ArrowLeft className="size-4 translate-y-0.5 mr-2" />
        <span>Anterior</span>
      </button>

      {isLast ? (
        <button
          type="button"
          onClick={onSubmit}
          disabled={!canGoNext || isSubmitting}
          className={cnButton(canGoNext && !isSubmitting, 'bg-blue-600 text-white hover:bg-blue-700')}
        >
          {isSubmitting ? 'Enviando…' : 'Ver resultados'}
        </button>
      ) : (
        <button
          type="button"
          onClick={onNext}
          disabled={!canGoNext}
          className={cnButton(canGoNext, 'hover:bg-[#25B9E8] text-white bg-blue-700')}
        >
          Siguiente
          <ArrowRight className="size-4 translate-y-0.5 ml-2" />
        </button>
      )}
    </div>
  )
}

function cnButton(
  enabled: boolean,
  activeStyle: string
): string {
  const base =
    "inline-flex min-w-32 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors disabled:cursor-not-allowed sm:min-w-36 sm:px-5 lg:min-w-40"

  return `${base} ${
    enabled
      ? activeStyle
      : "border border-gray-200 bg-gray-100 text-gray-400"
  }`
}