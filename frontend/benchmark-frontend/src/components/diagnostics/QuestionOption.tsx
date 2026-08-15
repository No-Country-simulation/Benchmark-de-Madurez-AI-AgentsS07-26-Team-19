import {CheckIcon} from "lucide-react"

interface QuestionOptionProps {
  value: string
  selected: boolean
  onSelect: () => void
}

export default function QuestionOption({ value, selected, onSelect }: QuestionOptionProps) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onSelect}
      className={cnOption(selected)}
    >
      <span>{value}</span>
      {selected && <CheckIcon className="h-4 w-4 shrink-0 text-green-500"/>}
    </button>
  )
}

function cnOption(selected: boolean): string {
  return [
    'flex h-11 w-full items-center justify-center border-2 text-sm text-white font-semibold transition-colors',
    selected
      ? 'border-blue-600 bg-blue-600 shadow-sm'
      : 'border-[#1E4458] text-gray-700 hover:border-blue-400 hover:text-blue-600',
  ].join(' ')
}