import { HeroDimensions } from "@/components/home/HeroDimensions";
import { MaturityLevel } from "@/components/home/MaturityLevel";
import { ShieldCheck, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="min-h-screen overflow-hidden bg-[#020D1B] text-white">

      <section className="px-5 py-8 sm:px-8 sm:py-10 lg:px-16 lg:py-12">
        <div className="flex w-full flex-col items-center gap-12 pt-4 sm:gap-16 sm:pt-8 lg:flex-row lg:items-center lg:gap-0">

          {/* Hero izquierdo*/}
          <div className="w-full shrink-0 lg:w-3/5">
            <div className="flex flex-col gap-5 sm:gap-6">

              <span className="flex w-fit items-center gap-2 rounded-lg border border-cyan-400/50 px-3 py-2.5 text-[10px] font-medium uppercase tracking-[0.15em] text-cyan-400 sm:px-3 sm:py-3 sm:text-[12px] sm:tracking-[0.2em]">
                <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-cyan-400" />
                Diagnóstico anónimo - 5 min
              </span>

              <h1 className="text-4xl font-bold leading-[1.05] sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl">
                Descubre tu nivel
                <br />
                en la industria
              </h1>

              <p className="max-w-2xl text-base leading-relaxed text-slate-400 sm:text-lg md:text-xl lg:text-2xl">
                Evalúa la madurez operativa de tu Data Center y compárate
                con el promedio de la industria.
              </p>

              <div className="flex flex-col gap-4">

                <Link
                  to="/methodology"
                  className="flex w-full max-w-sm items-center justify-between gap-6 rounded-md bg-[#25B9E8] px-6 py-3.5 text-lg font-medium text-[#020D1B] transition hover:bg-[#20A9D5] sm:w-fit sm:px-8 sm:py-4 sm:text-xl lg:text-2xl"
                >
                  <span>Comenzar</span>

                  <ArrowRight
                    className="h-5 w-5 translate-y-px sm:h-6 sm:w-6"
                    strokeWidth={2}
                  />
                </Link>

                <div className="flex items-center gap-3 text-sm text-slate-300 sm:text-base">
                  <ShieldCheck className="h-8 w-6 shrink-0 text-emerald-400 sm:h-10 sm:w-7" />

                  <span>
                    No solicitamos correos ni nombres
                  </span>
                </div>

              </div>
            </div>
          </div>

          {/* Dimensiones */}
          <div className="flex w-full shrink-0 justify-center lg:w-2/5">
            <HeroDimensions />
          </div>

        </div>
      </section>

      {/* Nivel de madurez */}
      <section className="px-5 pb-10 sm:px-8 sm:pb-12 lg:px-10 lg:pb-15">
        <MaturityLevel />
      </section>

    </div>
  );
}