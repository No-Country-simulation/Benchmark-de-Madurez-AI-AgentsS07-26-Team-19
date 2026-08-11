interface ProgressBarProps {
  answered: number
  total: number
}

export default function ProgressBar({ answered, total }: ProgressBarProps) {
  const percent = total > 0 ? Math.round((answered / total) * 100) : 0

  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm text-gray-600">
        <span>
          {answered} de {total} respondidas
        </span>
        <span>{percent}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  )
}