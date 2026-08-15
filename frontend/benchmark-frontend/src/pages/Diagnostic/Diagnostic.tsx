import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import ProgressBar from '@/components/diagnostics/ProgressBar'
import QuestionCard from '@/components/diagnostics/QuestionCard'
import StepNavigation from '@/components/diagnostics/StepNavigation'
import { useBenchmarkQuestions } from '@/hooks/use-benchmark'
import { ANSWER_VALUE_SCHEMA } from '@/schemas/diagnostic.schema'
import { submitDiagnostic } from '@/services/diagnostic.service'
import { useBenchmarkStore } from '@/store/benchmark.store'
import type { DiagnosticAnswer } from '@/types/diagnostic'

const orderBy = (a: { order: number; id: number }, b: { order: number; id: number }) =>
  a.order - b.order || a.id - b.id

export default function Diagnostic() {
  const navigate = useNavigate()
  const [currentIndex, setCurrentIndex] = useState(0)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const storeAnswers = useBenchmarkStore((state) => state.answers)
  const storeSessionId = useBenchmarkStore((state) => state.sessionId)
  const setAnswer = useBenchmarkStore((state) => state.setAnswer)
  const clearStore = useBenchmarkStore((state) => state.clear)
  const setLastResult = useBenchmarkStore((state) => state.setLastResult)

  const { data: questions, isError, isPending } = useBenchmarkQuestions()
  const sortedQuestions = useMemo(() => {
    if (isPending || isError) return []
    return [...(questions ?? [])].sort(orderBy)
  }, [questions, isPending, isError])

  const safeIndex = Math.min(currentIndex, Math.max(sortedQuestions.length - 1, 0))
  const currentQuestion = sortedQuestions[safeIndex] ?? null
  const answeredCount = sortedQuestions.filter((q) => storeAnswers[q.id] != null).length
  const isComplete = sortedQuestions.every((q) => storeAnswers[q.id] != null)
  const canGoNext = currentQuestion != null && storeAnswers[currentQuestion.id] != null

  if (isPending) {
    return <p className="py-16 text-center text-white bg-[#020D1B] min-h-screen">Cargando preguntas…</p>
  }

  if (isError || sortedQuestions.length === 0) {
    return (
      <p className="py-16 text-center text-red-600 bg-[#020D1B] min-h-screen">
        No se pudieron cargar las preguntas. Verificá que la API esté disponible.
      </p>
    )
  }

  function handleAnswerChange(value: number) {
    setAnswer(currentQuestion!.id, value)
  }

  function goToNext() {
    setSubmitError(null)
    setCurrentIndex((index) => Math.min(index + 1, sortedQuestions.length - 1))
  }

  function goToPrevious() {
    setSubmitError(null)
    setCurrentIndex((index) => Math.max(index - 1, 0))
  }

  async function handleSubmit() {
    if (!isComplete) {
      setSubmitError('Respondé todas las preguntas antes de ver los resultados.')
      return
    }

    setSubmitError(null)
    setIsSubmitting(true)

    const payload: DiagnosticAnswer[] = sortedQuestions.map((question) => ({
      question_id: question.id,
      value: ANSWER_VALUE_SCHEMA.parse(storeAnswers[question.id]) as DiagnosticAnswer['value'],
    }))

    try {
      const response = await submitDiagnostic(payload, storeSessionId)
      setLastResult(response)
      clearStore()
      navigate(`/results/${response.diagnostic.id}`)
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : 'Ocurrió un error al enviar el diagnóstico.',
      )
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#020D1B] text-white">
      <div className="mx-auto w-full px-6 pt-8 lg:px-16">
        <ProgressBar
          answered={answeredCount}
          total={sortedQuestions.length}
        />
      </div>
      <main className="flex w-full justify-center px-6 py-12">
        {currentQuestion != null ? (
          <div className="w-full max-w-5xl">
            {submitError != null ? (
              <p className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {submitError}
              </p>
            ) : null}

            <QuestionCard
              key={currentQuestion.id}
              question={currentQuestion}
              value={storeAnswers[currentQuestion.id]}
              onChange={handleAnswerChange}
            />
          </div>
        ) : null}
      </main>
      <div className="mx-auto w-auto px-6 pb-8 lg:px-16">
        <StepNavigation
          currentIndex={safeIndex}
          isLast={safeIndex === sortedQuestions.length - 1}
          canGoNext={canGoNext}
          isSubmitting={isSubmitting}
          onPrevious={goToPrevious}
          onNext={goToNext}
          onSubmit={() => void handleSubmit()}
        />
      </div>
    </div>
  )
}