import { DIMENSION_LABELS, type BenchmarkQuestion } from '@/types/benchmark'

import QuestionOption from './QuestionOption'

const SCALE_LABELS = ['Nunca', 'Casi nunca', 'A veces', 'Casi siempre', 'Siempre']

interface QuestionCardProps {
  question: BenchmarkQuestion
  value?: number
  onChange: (value: number) => void
}

export default function QuestionCard({ question, value, onChange }: QuestionCardProps) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
          {DIMENSION_LABELS[question.dimension]}
        </span>
        <span className="text-xs text-gray-400">{question.order}</span>
      </div>

      <h2 className="mb-6 text-lg font-medium text-gray-900">{question.text}</h2>

      <div className="flex flex-wrap items-start justify-between gap-4">
        {SCALE_LABELS.map((label, index) => {
          const optionValue = index + 1
          return (
            <label key={label} className="flex cursor-pointer flex-col items-center gap-2">
              <QuestionOption
                value={optionValue}
                selected={value === optionValue}
                onSelect={() => onChange(optionValue)}
              />
              <span className="text-center text-xs leading-tight text-gray-500">
                {optionValue} · {label}
              </span>
            </label>
          )
        })}
      </div>
    </div>
  )
}