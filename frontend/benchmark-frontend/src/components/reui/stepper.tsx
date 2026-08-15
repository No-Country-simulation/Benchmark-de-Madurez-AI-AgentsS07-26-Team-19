import type { HTMLAttributes, ReactElement } from "react"
import {
  Children,
  createContext,
  isValidElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react"
import { useRender } from "@base-ui/react/use-render"

import { cn } from "@/lib/utils"

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------

type StepperOrientation = "horizontal" | "vertical"

type StepState = "active" | "completed" | "inactive" | "loading"

type StepIndicators = {
  active?: React.ReactNode
  completed?: React.ReactNode
  inactive?: React.ReactNode
  loading?: React.ReactNode
}

// -----------------------------------------------------------------------------
// Context
// -----------------------------------------------------------------------------

interface StepperContextValue {
  activeStep: number
  setActiveStep: (step: number) => void
  stepsCount: number
  orientation: StepperOrientation

  registerTrigger: (node: HTMLButtonElement) => void
  unregisterTrigger: (node: HTMLButtonElement) => void

  triggerNodes: HTMLButtonElement[]

  focusNext: (currentIdx: number) => void
  focusPrev: (currentIdx: number) => void
  focusFirst: () => void
  focusLast: () => void

  indicators: StepIndicators
}

interface StepItemContextValue {
  step: number
  state: StepState
  isDisabled: boolean
  isLoading: boolean
}

const StepperContext = createContext<StepperContextValue | undefined>(
  undefined
)

const StepItemContext = createContext<StepItemContextValue | undefined>(
  undefined
)

// -----------------------------------------------------------------------------
// Hooks
// -----------------------------------------------------------------------------

function useStepper() {
  const ctx = useContext(StepperContext)

  if (!ctx) {
    throw new Error("useStepper must be used within a Stepper")
  }

  return ctx
}

function useStepItem() {
  const ctx = useContext(StepItemContext)

  if (!ctx) {
    throw new Error("useStepItem must be used within a StepperItem")
  }

  return ctx
}

// -----------------------------------------------------------------------------
// Stepper
// -----------------------------------------------------------------------------

interface StepperProps extends HTMLAttributes<HTMLDivElement> {
  defaultValue?: number
  value?: number
  onValueChange?: (value: number) => void
  orientation?: StepperOrientation
  indicators?: StepIndicators
}

function Stepper({
  defaultValue = 1,
  value,
  onValueChange,
  orientation = "horizontal",
  className,
  children,
  indicators = {},
  ...props
}: StepperProps) {
  const [activeStep, setActiveStep] = useState(defaultValue)
  const [triggerNodes, setTriggerNodes] = useState<HTMLButtonElement[]>([])

  const registerTrigger = useCallback((node: HTMLButtonElement) => {
    setTriggerNodes((prev) => {
      if (prev.includes(node)) {
        return prev
      }

      return [...prev, node]
    })
  }, [])

  const unregisterTrigger = useCallback((node: HTMLButtonElement) => {
    setTriggerNodes((prev) => prev.filter((item) => item !== node))
  }, [])

  const handleSetActiveStep = useCallback(
    (step: number) => {
      if (value === undefined) {
        setActiveStep(step)
      }

      onValueChange?.(step)
    },
    [value, onValueChange]
  )

  const currentStep = value ?? activeStep

  // ---------------------------------------------------------------------------
  // Keyboard navigation
  // ---------------------------------------------------------------------------

  const focusTrigger = useCallback(
    (index: number) => {
      const trigger = triggerNodes[index]

      if (trigger) {
        trigger.focus()
      }
    },
    [triggerNodes]
  )

  const focusNext = useCallback(
    (currentIdx: number) => {
      if (triggerNodes.length === 0) return

      const nextIndex = (currentIdx + 1) % triggerNodes.length

      focusTrigger(nextIndex)
    },
    [triggerNodes.length, focusTrigger]
  )

  const focusPrev = useCallback(
    (currentIdx: number) => {
      if (triggerNodes.length === 0) return

      const prevIndex =
        (currentIdx - 1 + triggerNodes.length) % triggerNodes.length

      focusTrigger(prevIndex)
    },
    [triggerNodes.length, focusTrigger]
  )

  const focusFirst = useCallback(() => {
    focusTrigger(0)
  }, [focusTrigger])

  const focusLast = useCallback(() => {
    focusTrigger(triggerNodes.length - 1)
  }, [triggerNodes.length, focusTrigger])

  // ---------------------------------------------------------------------------
  // Context
  // ---------------------------------------------------------------------------

  const stepsCount = Children.toArray(children).filter(
    (child): child is ReactElement =>
      isValidElement(child) &&
      (child.type as { displayName?: string }).displayName === "StepperItem"
  ).length

  const contextValue = useMemo<StepperContextValue>(
    () => ({
      activeStep: currentStep,
      setActiveStep: handleSetActiveStep,
      stepsCount,
      orientation,

      registerTrigger,
      unregisterTrigger,

      triggerNodes,

      focusNext,
      focusPrev,
      focusFirst,
      focusLast,

      indicators,
    }),
    [
      currentStep,
      handleSetActiveStep,
      stepsCount,
      orientation,
      registerTrigger,
      unregisterTrigger,
      triggerNodes,
      focusNext,
      focusPrev,
      focusFirst,
      focusLast,
      indicators,
    ]
  )

  return (
    <StepperContext.Provider value={contextValue}>
      <div
        role="tablist"
        aria-orientation={orientation}
        data-slot="stepper"
        data-orientation={orientation}
        className={cn("w-full", className)}
        {...props}
      >
        {children}
      </div>
    </StepperContext.Provider>
  )
}

// -----------------------------------------------------------------------------
// StepperItem
// -----------------------------------------------------------------------------

interface StepperItemProps extends React.HTMLAttributes<HTMLDivElement> {
  step: number
  completed?: boolean
  disabled?: boolean
  loading?: boolean
}

function StepperItem({
  step,
  completed = false,
  disabled = false,
  loading = false,
  className,
  children,
  ...props
}: StepperItemProps) {
  const { activeStep } = useStepper()

  const state: StepState =
    completed || step < activeStep
      ? "completed"
      : activeStep === step
        ? "active"
        : "inactive"

  const isLoading = loading && step === activeStep

  return (
    <StepItemContext.Provider
      value={{
        step,
        state,
        isDisabled: disabled,
        isLoading,
      }}
    >
      <div
        data-slot="stepper-item"
        data-state={state}
        data-loading={isLoading || undefined}
        className={cn(
          "group/step flex items-center justify-center not-last:flex-1",
          "group-data-[orientation=horizontal]/stepper-nav:flex-row",
          "group-data-[orientation=vertical]/stepper-nav:flex-col",
          className
        )}
        {...props}
      >
        {children}
      </div>
    </StepItemContext.Provider>
  )
}

StepperItem.displayName = "StepperItem"

// -----------------------------------------------------------------------------
// StepperTrigger
// -----------------------------------------------------------------------------

type StepperTriggerProps = ReturnType<
  typeof useRender
> extends never
  ? never
  : React.ComponentProps<"button"> & {
    render?: React.ReactElement
  }

function StepperTrigger({
  className,
  children,
  tabIndex,
  ...props
}: StepperTriggerProps) {
  const { state, isLoading } = useStepItem()

  const {
    setActiveStep,
    activeStep,
    registerTrigger,
    unregisterTrigger,
    triggerNodes,
    focusNext,
    focusPrev,
    focusFirst,
    focusLast,
  } = useStepper()

  const { step, isDisabled } = useStepItem()

  const isSelected = activeStep === step

  const id = `stepper-tab-${step}`
  const panelId = `stepper-panel-${step}`

  const btnRef = useRef<HTMLButtonElement>(null)

  // Register / unregister trigger
  useEffect(() => {
    const node = btnRef.current

    if (!node) return

    registerTrigger(node)

    return () => {
      unregisterTrigger(node)
    }
  }, [registerTrigger, unregisterTrigger])


  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLButtonElement>
  ) => {
    const myIdx = triggerNodes.findIndex(
      (node) => node === btnRef.current
    )
    switch (event.key) {
      case "ArrowRight":
      case "ArrowDown":
        event.preventDefault()

        if (myIdx !== -1) {
          focusNext(myIdx)
        }

        break

      case "ArrowLeft":
      case "ArrowUp":
        event.preventDefault()

        if (myIdx !== -1) {
          focusPrev(myIdx)
        }

        break

      case "Home":
        event.preventDefault()
        focusFirst()
        break

      case "End":
        event.preventDefault()
        focusLast()
        break

      case "Enter":
      case " ":
        event.preventDefault()
        setActiveStep(step)
        break
    }
  }

  const defaultProps = {
    role: "tab",
    id,
    "aria-selected": isSelected,
    "aria-controls": panelId,
    tabIndex:
      typeof tabIndex === "number"
        ? tabIndex
        : isSelected
          ? 0
          : -1,
    "data-slot": "stepper-trigger",
    "data-state": state,
    "data-loading": isLoading || undefined,
    className: cn(
      "focus-visible:border-ring focus-visible:ring-ring/50",
      "inline-flex cursor-pointer items-center outline-none",
      "focus-visible:z-10 focus-visible:ring-3",
      "disabled:pointer-events-none disabled:opacity-60",
      "gap-2.5 rounded-full",
      className
    ),
    onClick: () => setActiveStep(step),
    onKeyDown: handleKeyDown,
    disabled: isDisabled,
    children,
  }

  return (
  <button
    ref={btnRef}
    {...props}
    {...defaultProps}
  >
    {children}
  </button>
)
}

// -----------------------------------------------------------------------------
// StepperIndicator
// -----------------------------------------------------------------------------

function StepperIndicator({
  children,
  className,
}: React.ComponentProps<"div">) {
  const { state, isLoading } = useStepItem()
  const { indicators } = useStepper()

  const indicator =
    (isLoading && indicators.loading) ||
    (state === "completed" && indicators.completed) ||
    (state === "active" && indicators.active) ||
    (state === "inactive" && indicators.inactive) ||
    children

  return (
    <div
      data-slot="stepper-indicator"
      data-state={state}
      className={cn(
        "border-background bg-accent text-accent-foreground",
        "data-[state=completed]:bg-primary",
        "data-[state=completed]:text-primary-foreground",
        "data-[state=active]:bg-primary",
        "data-[state=active]:text-primary-foreground",
        "relative flex size-6 shrink-0 items-center justify-center",
        "overflow-hidden rounded-full text-xs",
        className
      )}
    >
      <div className="absolute">
        {indicator}
      </div>
    </div>
  )
}

// -----------------------------------------------------------------------------
// StepperSeparator
// -----------------------------------------------------------------------------

function StepperSeparator({
  className,
}: React.ComponentProps<"div">) {
  const { state } = useStepItem()

  return (
    <div
      data-slot="stepper-separator"
      data-state={state}
      className={cn(
        "bg-muted m-0.5 rounded-sm",
        "group-data-[orientation=horizontal]/stepper-nav:h-0.5",
        "group-data-[orientation=horizontal]/stepper-nav:flex-1",
        "group-data-[orientation=vertical]/stepper-nav:h-12",
        "group-data-[orientation=vertical]/stepper-nav:w-0.5",
        className
      )}
    />
  )
}

// -----------------------------------------------------------------------------
// StepperTitle
// -----------------------------------------------------------------------------

function StepperTitle({
  children,
  className,
}: React.ComponentProps<"h3">) {
  const { state } = useStepItem()

  return (
    <h3
      data-slot="stepper-title"
      data-state={state}
      className={cn(
        "text-sm leading-none font-medium",
        className
      )}
    >
      {children}
    </h3>
  )
}

// -----------------------------------------------------------------------------
// StepperDescription
// -----------------------------------------------------------------------------

function StepperDescription({
  children,
  className,
}: React.ComponentProps<"div">) {
  const { state } = useStepItem()

  return (
    <div
      data-slot="stepper-description"
      data-state={state}
      className={cn(
        "text-muted-foreground text-sm",
        className
      )}
    >
      {children}
    </div>
  )
}

// -----------------------------------------------------------------------------
// StepperNav
// -----------------------------------------------------------------------------

function StepperNav({
  children,
  className,
}: React.ComponentProps<"nav">) {
  const { activeStep, orientation } = useStepper()

  return (
    <nav
      data-slot="stepper-nav"
      data-state={activeStep}
      data-orientation={orientation}
      className={cn(
        "group/stepper-nav inline-flex",
        "data-[orientation=horizontal]:w-full",
        "data-[orientation=horizontal]:flex-row",
        "data-[orientation=vertical]:flex-col",
        className
      )}
    >
      {children}
    </nav>
  )
}

// -----------------------------------------------------------------------------
// StepperPanel
// -----------------------------------------------------------------------------

function StepperPanel({
  children,
  className,
}: React.ComponentProps<"div">) {
  const { activeStep } = useStepper()

  return (
    <div
      data-slot="stepper-panel"
      data-state={activeStep}
      className={cn("w-full", className)}
    >
      {children}
    </div>
  )
}

// -----------------------------------------------------------------------------
// StepperContent
// -----------------------------------------------------------------------------

interface StepperContentProps
  extends React.ComponentProps<"div"> {
  value: number
  forceMount?: boolean
}

function StepperContent({
  value,
  forceMount,
  children,
  className,
}: StepperContentProps) {
  const { activeStep } = useStepper()

  const isActive = value === activeStep

  if (!forceMount && !isActive) {
    return null
  }

  return (
    <div
      data-slot="stepper-content"
      data-state={activeStep}
      className={cn(
        "w-full",
        className,
        !isActive && forceMount && "hidden"
      )}
      hidden={!isActive && forceMount}
    >
      {children}
    </div>
  )
}

// -----------------------------------------------------------------------------
// Exports
// -----------------------------------------------------------------------------

export {
  Stepper,
  StepperItem,
  StepperTrigger,
  StepperIndicator,
  StepperSeparator,
  StepperTitle,
  StepperDescription,
  StepperPanel,
  StepperContent,
  StepperNav,
}

export type {
  StepperProps,
  StepperItemProps,
  StepperTriggerProps,
  StepperContentProps,
}