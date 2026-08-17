import {
  BarChart3,
  ClipboardCheck,
  Search,
  Check,
} from 'lucide-react'

type ProcessingStage = 1 | 2 | 3 | 4

interface ResultsProcessingProps {
  currentStage: ProcessingStage
}

const stages = [
  {
    title: 'Validando respuestas',
    icon: ClipboardCheck,
  },
  {
    title: 'Calculando puntuación',
    icon: BarChart3,
  },
  {
    title: 'Comparando con la industria',
    icon: Search,
  },
]

export default function ResultsProcessing({
  currentStage,
}: ResultsProcessingProps) {
  return (
    <div className="flex min-h-screen flex-col bg-[#020D1B] text-white">
      <main className="flex flex-1 flex-col items-center justify-center px-4 py-10 sm:px-6 sm:py-12">

        <div className="relative mb-8 h-36 w-36 sm:mb-10 sm:h-44 sm:w-44 md:h-56 md:w-56">
          <div className="absolute inset-0 rounded-full border border-cyan-400/40" />

          <div className="absolute inset-2 rounded-full border border-cyan-400/30 sm:inset-3" />

          <div className="absolute inset-5 animate-spin rounded-full border-4 border-transparent border-r-cyan-300 border-t-cyan-400 sm:inset-6" />

          <div className="absolute inset-8 rounded-full border border-cyan-400/20 sm:inset-10" />
        </div>

        <div className="mb-14 max-w-4xl px-2 text-center sm:mb-16 md:mb-20">
          <h1 className="text-2xl font-bold leading-snug sm:text-3xl md:text-4xl">
            ¡Gracias! Estamos calculando tus resultados
            <br className="hidden sm:block" />
            <span className="sm:hidden"> </span>
            y comparándote con el resto de la industria...
          </h1>
        </div>

        <div className="w-full max-w-5xl">
          <div className="flex w-full items-start">
            {stages.map((stage, index) => {
              const stageNumber = index + 1

              const completed = currentStage > stageNumber
              const active = currentStage === stageNumber

              const Icon = stage.icon

              return (
                <div
                  key={stage.title}
                  className="flex min-w-0 flex-1 items-start"
                >
                    
                  <div className="flex min-w-0 w-auto flex-col items-center">
                    <div
                      className={`
                        relative flex items-center justify-center
                        rounded-full border-2
                        transition-all duration-500
                        h-16 w-16
                        sm:h-20 sm:w-20
                        md:h-24 md:w-24
                        ${
                          completed
                            ? 'border-lime-400 text-lime-400'
                            : active
                              ? 'border-cyan-400 text-cyan-400 shadow-[0_0_20px_rgba(37,185,232,0.5)]'
                              : 'border-slate-600 text-slate-500'
                        }
                      `}
                    >
                      <Icon
                        className="h-7 w-7 sm:h-8 sm:w-8 md:h-10 md:w-10"
                        strokeWidth={1.8}
                      />

                      {completed && (
                        <span className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-lime-400 text-[#020D1B] sm:h-7 sm:w-7 md:h-8 md:w-8">
                          <Check
                            className="h-3.5 w-3.5 sm:h-4 sm:w-4 md:h-4.5 md:w-4.5"
                            strokeWidth={3}
                          />
                        </span>
                      )}
                    </div>

                    <span
                      className={`
                        mt-3 max-w-22.5 text-center text-xs leading-tight
                        transition-colors
                        sm:mt-4 sm:max-w-30 sm:text-sm
                        md:mt-5 md:max-w-none
                        ${
                          completed || active
                            ? 'text-white'
                            : 'text-slate-400'
                        }
                      `}
                    >
                      {stage.title}
                    </span>
                  </div>

                  {index < stages.length - 1 && (
                    <div className="relative mt-8 h-0.5 min-w-3 flex-1 sm:mt-10 md:mt-12">
                      
                      <div className="absolute inset-0 bg-slate-700" />

                      <div
                        className={`
                          absolute inset-y-0 left-0
                          transition-all duration-700
                          ${
                            completed
                              ? 'w-full bg-cyan-400'
                              : 'w-0'
                          }
                        `}
                      />

                      <div
                        className={`
                          absolute right-0 top-1/2
                          h-2 w-2 -translate-y-1/2
                          rounded-full
                          transition-colors duration-500
                          ${
                            completed
                              ? 'bg-cyan-400'
                              : 'bg-slate-600'
                          }
                        `}
                      />
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </main>
    </div>
  )
}