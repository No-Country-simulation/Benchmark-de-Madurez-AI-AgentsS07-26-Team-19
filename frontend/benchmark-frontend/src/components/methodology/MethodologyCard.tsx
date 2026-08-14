type MethodologyCardProps = {
    number: number
    title: string
    description: string
    image: React.ReactNode
}

export default function MethodologyCard({ number, title, description, image }: MethodologyCardProps) {
    return (
        <div className="relative flex min-h-85 w-full max-w-66.25 flex-col items-center overflow-hidden rounded-xl border-2 border-slate-700 bg-[#020D1B] px-6 py-5 mx-3 text-center shadow-lg">
            <div className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-emerald-400 text-2xl font-medium text-emerald-400">
                {number}
            </div>
            <div className="my-6 flex h-24 items-center justify-center">
                {image}
            </div>
            <h3 className="text-2xl font-bold text-white">
                {title}
            </h3>
            <p className="mt-3 text-lg leading-8 text-slate-400">
                {description}
            </p>
        </div>
    )
}