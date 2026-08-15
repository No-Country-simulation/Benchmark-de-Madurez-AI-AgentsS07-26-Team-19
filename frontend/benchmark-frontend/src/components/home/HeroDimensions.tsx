import type * as React from "react";
import { Eye, Waves, Clock3, Layers3, TriangleAlert } from "lucide-react";

export function HeroDimensions() {
  return (
    <div className="relative h-130 w-full max-w-200 sm:h-140">

      {/* Líneas de conexión */}
      <svg
        className="pointer-events-none absolute inset-0 z-10 h-full w-full"
        viewBox="0 0 800 560"
        preserveAspectRatio="none"
        fill="none"
      >
        {/* Visibilidad */}
        <path
          d="M185 105 H285 L365 175"
          stroke="#38bdf8"
          strokeWidth="2"
        />
        <circle cx="365" cy="175" r="5" fill="#38bdf8" />

        {/* Fricción */}
        <path
          d="M160 280 H275 L345 280"
          stroke="#4ade80"
          strokeWidth="2"
        />
        <circle cx="345" cy="280" r="5" fill="#4ade80" />

        {/* Latencia */}
        <path
          d="M175 455 H290 L370 380"
          stroke="#38bdf8"
          strokeWidth="2"
        />
        <circle cx="370" cy="380" r="5" fill="#38bdf8" />

        {/* Capacidad */}
        <path
          d="M615 170 H545 L475 220"
          stroke="#4ade80"
          strokeWidth="2"
        />
        <circle cx="475" cy="220" r="5" fill="#4ade80" />

        {/* Bloqueantes */}
        <path
          d="M625 400 H545 L480 350"
          stroke="#38bdf8"
          strokeWidth="2"
        />
        <circle cx="480" cy="350" r="5" fill="#38bdf8" />
      </svg>

      {/* Imagen del Data Center */}
      <div
        className="
          absolute left-1/2 top-1/2 z-10
          -translate-x-1/2 -translate-y-1/2
        "
      >
        <img
          src="https://placehold.co/300x300"
          alt="Placeholder"
          className="
            h-52 w-52 rounded-lg border border-slate-700/80
            shadow-xl
            sm:h-60 sm:w-60
            md:h-75 md:w-75
          "
        />
      </div>

      {/* VISIBILIDAD */}
      <DimensionCard
        className="
          left-0 top-5
          sm:top-8
          md:left-0 md:top-13.75
        "
        title="VISIBILIDAD"
        value="72"
        icon={<Eye className="h-6 w-6" />}
        color="cyan"
      />

      {/* FRICCIÓN */}
      <DimensionCard
        className="
          left-0 top-37.5
          sm:top-45
          md:-left-5 md:top-57.5
        "
        title="FRICCIÓN"
        value="58"
        icon={<Waves className="h-6 w-6" />}
        color="green"
      />

      {/* LATENCIA */}
      <DimensionCard
        className="
          left-0 bottom-5
          sm:bottom-8
          md:bottom-auto md:left-0 md:top-100
        "
        title="LATENCIA"
        value="63"
        icon={<Clock3 className="h-6 w-6" />}
        color="cyan"
      />

      {/* CAPACIDAD */}
      <DimensionCard
        className="
          right-0 top-25
          sm:top-30
          md:right-0 md:top-30
        "
        title="CAPACIDAD"
        value="76"
        icon={<Layers3 className="h-6 w-6" />}
        color="green"
      />

      {/* BLOQUEANTES */}
      <DimensionCard
        className="
          right-0 top-80
          sm:top-87.5
          md:-right-2.5 md:top-87.5
        "
        title="BLOQUEANTES"
        value="41"
        icon={<TriangleAlert className="h-6 w-6" />}
        color="cyan"
      />
    </div>
  )
}

type DimensionCardProps = {
  className?: string
  title: string
  value: string
  icon: React.ReactNode
  color: "cyan" | "green"
}

function DimensionCard({
  className,
  title,
  value,
  icon,
  color,
}: DimensionCardProps) {
  const isGreen = color === "green"

  return (
    <div
      className={`
        absolute z-20
        w-36 rounded-xl
        border border-slate-700/80
        bg-[#06101d]/95
        px-3 py-3
        shadow-xl
        backdrop-blur-sm

        sm:w-40 sm:px-4 sm:py-3

        md:w-47.5 md:px-5 md:py-4

        ${className}
      `}
    >
      <div className="flex items-center gap-2 sm:gap-3 md:gap-4">

        <div
          className={`
            text-2xl
            sm:text-2xl
            md:text-3xl
            ${isGreen ? "text-green-400" : "text-cyan-400"}
          `}
        >
          {icon}
        </div>

        <div>
          <p className="text-[10px] font-medium tracking-wide text-slate-300 sm:text-xs">
            {title}
          </p>

          <div className="flex items-baseline gap-1">
            <span
              className={`
                text-2xl font-semibold
                sm:text-2xl
                md:text-3xl
                ${isGreen ? "text-green-400" : "text-cyan-400"}
              `}
            >
              {value}
            </span>

            <span className="text-xs text-slate-500 sm:text-sm">
              /100
            </span>
          </div>
        </div>

      </div>
    </div>
  )
}