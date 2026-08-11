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
        className={cnButton(currentIndex > 0, 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50')}
      >
        Anterior
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
          className={cnButton(canGoNext, 'bg-blue-600 text-white hover:bg-blue-700')}
        >
          Siguiente
        </button>
      )}
    </div>
  )
}

function cnButton(enabled: boolean, activeStyle: string): string {
  const base = 'rounded-lg px-5 py-2.5 text-sm font-medium transition-colors disabled:cursor-not-allowed'
  return `${base} ${enabled ? activeStyle : 'border border-gray-200 bg-gray-100 text-gray-400'}`
}