import { type BenchmarkQuestion } from '@/types/benchmark'

import QuestionOption from './QuestionOption'

const SCALE_LABELS = ['Nunca', 'Casi nunca', 'A veces', 'Casi siempre', 'Siempre']

interface QuestionCardProps {
  question: BenchmarkQuestion
  value?: number
  onChange: (value: number) => void
}

export default function QuestionCard({ question, value, onChange }: QuestionCardProps) {
  return (
    <div className="rounded-xl border-2 border-[#1E4458] shadow-sm my-10">
      <div className="mb-4 flex flex-col justify-between gap-3 p-4">
        <span className="rounded-md border-2 border-[#1E4458] p-4 py-1 text-md font-medium text-white w-fit">
          {question.order}
        </span>
        <div>
          <h2 className="mb-6 text-xl font-medium text-white text-center">{question.text}</h2>
          <div className="flex flex-col justify-between gap-4">
            {SCALE_LABELS.map((label, index) => {
              const optionValue = index + 1
              return (
                <label key={label} className="flex cursor-pointer flex-col items-center gap-2">
                  <QuestionOption
                    value={label}
                    selected={value === optionValue}
                    onSelect={() => onChange(optionValue)}
                  />
                </label>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}