import MethodologyCard from '@/components/methodology/MethodologyCard'
import {
    Eye,
    Waves,
    Clock3,
    Layers3,
    TriangleAlert,
    ArrowRight
} from "lucide-react";
import { Link } from 'react-router-dom'

export default function Methodology() {
    return (
        <div className="min-h-screen overflow-hidden bg-[#020D1B] text-white">
            <section className="flex flex-col items-center justify-center px-5 py-8 text-center sm:px-8 sm:py-10 lg:px-16 lg:py-12">
                <h1 className="mt-8 max-w-5xl pb-4 text-3xl font-bold leading-tight sm:mt-10 sm:text-4xl lg:mt-15 lg:text-6xl">
                    Este test evalúa 5 áreas de tu Data Center
                </h1>

                <h3 className="max-w-3xl text-base font-medium text-slate-400 sm:text-xl lg:text-2xl">
                    No te pediremos correos ni nombres. Tus datos están seguros.
                </h3>
            </section>
            <section className="flex justify-center pb-10 sm:px-8 lg:px-16">
                <div className="w-full max-w-7xl">
                    <div className="grid grid-cols-1 justify-items-center gap-5 sm:grid-cols-2 lg:grid-cols-5 lg:justify-items-stretch lg:gap-6">
                        <MethodologyCard
                            number={1}
                            title="Visibilidad"
                            description="Qué tan completo y actualizado es tu conocimiento del entorno."
                            image={
                                <Eye
                                    className="h-16 w-20 text-sky-400 sm:h-20 sm:w-24"
                                    strokeWidth={1.0}
                                />
                            }
                        />
                        <MethodologyCard
                            number={2}
                            title="Fricción"
                            description="Cuánta resistencia y complejidad enfrentas para avanzar en iniciativas."
                            image={
                                <Waves
                                    className="h-16 w-20 text-sky-400 sm:h-20 sm:w-24"
                                    strokeWidth={1.0}
                                />
                            }
                        />
                        <MethodologyCard
                            number={3}
                            title="Latencia"
                            description="Qué tan rápido obtienes la información y tomas decisiones."
                            image={
                                <Clock3
                                    className="h-16 w-20 text-sky-400 sm:h-20 sm:w-24"
                                    strokeWidth={1.0}
                                />
                            }
                        />
                        <MethodologyCard
                            number={4}
                            title="Capacidad"
                            description="Qué tan preparada está tu infraestructura y tu equipo para escalar."
                            image={
                                <Layers3
                                    className="h-16 w-20 text-sky-400 sm:h-20 sm:w-24"
                                    strokeWidth={1.0}
                                />
                            }
                        />
                        <MethodologyCard
                            number={5}
                            title="Bloqueantes"
                            description="Qué factores críticos te impiden avanzar con mayor velocidad."
                            image={
                                <TriangleAlert
                                    className="h-16 w-20 text-sky-400 sm:h-20 sm:w-24"
                                    strokeWidth={1.0}
                                />
                            }
                        />
                    </div>
                    <div className="mx-auto mt-8 flex w-full max-w-7xl items-center rounded-lg border-2 border-slate-700 py-4 sm:mt-10 sm:px-6">
                        <Clock3
                            className="mr-3 h-9 w-9 shrink-0 text-sky-400 sm:mr-4 sm:h-12 sm:w-12"
                            strokeWidth={1.0}
                        />

                        <p className="text-sm text-slate-400 sm:text-base">
                            Duración estimada:
                        </p>

                        <p className="ml-2 text-sm font-bold text-white sm:text-base">
                            5 minutos
                        </p>
                    </div>
                    <Link
                        className="mx-auto mt-6 flex w-fit items-center justify-center rounded-lg border border-[#25B9E8] bg-[#00284B] px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-[#00365F] sm:mt-8 sm:px-8 sm:py-4 sm:text-base"
                        to="/diagnostic"
                    >
                        <span>Entendido, ir a las preguntas</span>
                        <ArrowRight className="ml-2 h-5 w-5 sm:h-6 sm:w-6" />
                    </Link>
                </div>
            </section>
        </div>
    )
}