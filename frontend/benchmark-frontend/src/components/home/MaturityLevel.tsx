import { Circle } from "lucide-react";
import logoNetwork from "../../assets/logos/logo-network.svg";

export function MaturityLevel() {
  const score = 72;
  const industryAverage = 62;

  return (
    <section className="relative rounded-xl border border-gray-700 px-5 py-8 sm:px-8 md:px-10 md:py-10 shadow-xl">
      <div className="grid w-full grid-cols-1 items-center gap-10 md:grid-cols-[25%_1fr] md:gap-16">
        
        {/* Contenedor izquierdo*/}
        <div>
          <div className="flex items-start gap-4">
            <img
              src={logoNetwork}
              alt="Logo Data Center Intelligence"
              className="h-16 w-16 shrink-0"
            />

            <div>
              <h2 className="text-lg font-bold uppercase leading-tight sm:text-xl">
                Tu nivel de madurez operativa
              </h2>

              <p className="mt-4 text-base leading-relaxed text-slate-400 sm:mt-5 sm:text-lg">
                Compara tu desempeño con el promedio
                de la industria en una escala de 0 a 100.
              </p>
            </div>
          </div>

          <div className="mt-8 flex flex-wrap items-center gap-x-3 gap-y-2 md:mt-10 md:gap-8">

            <div className="flex items-center gap-2 text-sm sm:text-base">
              <span className="h-0.75 w-7 rounded-full bg-cyan-400 sm:w-8" />
              <span>Tu resultado</span>
            </div>

            <div className="flex items-center gap-2 text-sm sm:text-base">
              <Circle className="h-4 w-4 text-emerald-400 stroke-2 sm:h-5 sm:w-5" />
              <span>Promedio de la industria</span>
            </div>
          </div>
        </div>

        {/* Separador */}
        <div className="absolute bottom-10 left-[calc(26%+2rem)] top-10 hidden w-px bg-gray-700 md:block" />

        {/* Grafico de la madurez */}
        <div className="w-full">
          <div className="relative">

            <div
              className="absolute -top-16 -translate-x-1/2 sm:-top-20"
              style={{ left: `${industryAverage}%` }}
            >
              <div className="flex flex-col items-center whitespace-nowrap">
                <span className="text-xs uppercase text-emerald-400 sm:text-sm md:text-base">
                  Promedio de la industria
                </span>

                <span className="text-2xl font-bold text-emerald-400 sm:text-3xl">
                  {industryAverage}
                </span>

                <div className="h-0 w-0 border-x-[5px] border-t-[7px] border-x-transparent border-t-emerald-400" />
              </div>
            </div>

            {/* Línea */}
            <div className="mt-20 h-3 w-full rounded-full bg-linear-to-r from-blue-900 via-cyan-500 to-emerald-400 sm:mt-20" />

            {/* Indicador */}
            <div
              className="absolute top-1/2 -translate-y-12.5"
              style={{ left: `${score}%` }}
            >
              <div
                className="h-6 w-6 -translate-x-1/2 rounded-full border-4 border-[#020D1B] ring-3 ring-emerald-500 sm:h-7 sm:w-7"
                style={{
                  backgroundColor:
                    score < 25
                      ? "#1e3a8a"
                      : score < 50
                        ? "#06b6d4"
                        : score < 75
                          ? "#2dd4bf"
                          : "#34d399",
                }}
              />
            </div>

            {/* Escala */}
            <div className="mt-4 flex justify-between">

              <span className="flex flex-col">
                <span className="text-base font-bold text-white sm:text-lg">
                  0
                </span>
                <span className="text-xs text-slate-500 sm:text-sm md:text-base">
                  Inicial
                </span>
              </span>

              <span className="flex flex-col items-center">
                <span className="text-base font-bold text-white sm:text-lg">
                  25
                </span>
                <span className="text-xs text-slate-500 sm:text-sm md:text-base">
                  En desarrollo
                </span>
              </span>

              <span className="flex flex-col items-center">
                <span className="text-base font-bold text-white sm:text-lg">
                  50
                </span>
                <span className="text-xs text-slate-500 sm:text-sm md:text-base">
                  Consolidado
                </span>
              </span>

              <span className="flex flex-col items-center">
                <span className="text-base font-bold text-white sm:text-lg">
                  75
                </span>
                <span className="text-xs text-slate-500 sm:text-sm md:text-base">
                  Avanzado
                </span>
              </span>

              <span className="flex flex-col items-end">
                <span className="text-base font-bold text-white sm:text-lg">
                  100
                </span>
                <span className="text-xs text-slate-500 sm:text-sm md:text-base">
                  Líder
                </span>
              </span>

            </div>
          </div>
        </div>
      </div>
    </section>
  );
}