import {
  Stepper,
  StepperIndicator,
  StepperItem,
  StepperNav,
  StepperTitle,
  StepperTrigger,
} from "@/components/reui/stepper"

import { Check } from "lucide-react"

interface ProgressBarProps {
  answered: number
  total: number
}

const dimensions = [
  "Visibilidad",
  "Fricción",
  "Latencia",
  "Capacidad",
  "Bloqueantes",
]

export default function ProgressBar({
  answered,
  total,
}: ProgressBarProps) {
  const percent = total > 0
    ? (answered / total) * 100
    : 0

  const totalSteps = dimensions.length + 1

  const currentStep = Math.min(
    Math.floor((answered / total) * dimensions.length) + 1,
    totalSteps
  )

  return (
    <div className="w-full mt-5">

      <Stepper
        value={currentStep}
        className="w-full"
      >
        <div className="mb-5 w-full pl-[8%]">
          <p className="text-2xl font-medium text-white">
            Paso {currentStep - 1} de {totalSteps - 1}
          </p>
        </div>
        <StepperNav className="w-full">
          {Array.from({ length: totalSteps }).map((_, index) => {
            const step = index + 1

            const isStart = index === 0
            const isEnd = index === totalSteps - 1

            const completed =
              answered >=
              (index / dimensions.length) * total

            const isCurrent =
              step === currentStep

            const lineStart =
              (index / dimensions.length) * 100

            const lineEnd =
              ((index + 1) / dimensions.length) * 100

            const lineProgress =
              percent <= lineStart
                ? 0
                : percent >= lineEnd
                  ? 100
                  : ((percent - lineStart) /
                    (lineEnd - lineStart)) *
                  100

            return (
              <StepperItem
                key={step}
                step={step}
                completed={completed}
                className="relative flex-1 items-start"
              >
                <StepperTrigger className="flex flex-col items-center gap-3">
                  <StepperIndicator
                    className="
                            relative
                            z-10
                            size-6
                            rounded-full
                            border-3
                            bg-white
                            data-[state=active]:border-[#25B9E8]
                            data-[state=active]:bg-white
                            data-[state=completed]:border-[#25B9E8]
                            data-[state=completed]:bg-white
                            data-[state=completed]:text-[#25B9E8]
                            data-[state=inactive]:border-gray-300
                            data-[state=inactive]:bg-white
                          "
                  >
                    {completed && !isStart && (
                      <Check className="size-3" />
                    )}
                  </StepperIndicator>

                  {!isStart && !isEnd && (
                    <StepperTitle
                      className={`
                        whitespace-nowrap
                        text-xs
                        font-medium
                        ${completed || isCurrent
                          ? "text-[#25B9E8]"
                          : "text-gray-400"
                        }
                      `}
                    >
                      {dimensions[index - 1]}
                    </StepperTitle>
                  )}

                  {isStart && (
                    <StepperTitle
                      className="text-xs font-medium text-gray-400"
                    >
                    </StepperTitle>
                  )}

                  {isEnd && (
                    <StepperTitle
                    >
                    </StepperTitle>
                  )}
                </StepperTrigger>

                {!isEnd && (
                  <div
                    className="
                      absolute
                      left-1/2
                      top-2.5
                      z-0
                      h-1
                      w-full
                      bg-gray-600
                    "
                  >
                    <div
                      className="
                        h-full
                        bg-[#25B9E8]
                        transition-all
                        duration-500
                        ease-out
                      "
                      style={{
                        width: `${lineProgress}%`,
                      }}
                    />
                  </div>
                )}
              </StepperItem>
            )
          })}
        </StepperNav>
      </Stepper>
    </div>
  )
}