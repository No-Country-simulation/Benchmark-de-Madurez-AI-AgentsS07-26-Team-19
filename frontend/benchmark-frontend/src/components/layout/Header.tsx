import { Link, NavLink } from 'react-router-dom'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
  }`

export default function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-4">
        <Link to="/" className="text-lg font-semibold text-gray-900">
          NLR <span className="text-blue-600">Benchmark</span>
        </Link>
        <nav className="flex items-center gap-1">
          <NavLink to="/" end className={navLinkClass}>
            Inicio
          </NavLink>
          <NavLink to="/diagnostic" className={navLinkClass}>
            Diagnóstico
          </NavLink>
        </nav>
      </div>
    </header>
  )
}