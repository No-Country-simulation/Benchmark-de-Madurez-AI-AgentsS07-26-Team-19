interface QuestionOptionProps {
  value: number
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
      {value}
    </button>
  )
}

function cnOption(selected: boolean): string {
  return [
    'flex h-11 w-11 items-center justify-center rounded-full border text-sm font-semibold transition-colors',
    selected
      ? 'border-blue-600 bg-blue-600 text-white shadow-sm'
      : 'border-gray-300 bg-white text-gray-700 hover:border-blue-400 hover:text-blue-600',
  ].join(' ')
}