import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Menu, X } from "lucide-react";
import logoMain from "../../assets/logos/logo-main.svg";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg border px-3 py-2 text-sm font-medium text-white transition-colors ${
    isActive
      ? "border-cyan-300/40"
      : "border-transparent hover:border-cyan-300/20"
  }`;

export default function Header() {
  const [isOpen, setIsOpen] = useState(false);

  const closeMenu = () => setIsOpen(false);

  return (
    <header className="border-b border-[#183047] bg-[#020D1B]">
      <div className="mx-auto flex w-full items-center justify-between px-5 py-3 sm:px-8 sm:py-4 lg:px-20">

        {/* Logo */}
        <Link
          to="/"
          className="flex items-center gap-2"
          onClick={closeMenu}
        >
          <img
            src={logoMain}
            alt="DC Benchmark logo"
            className="h-9 w-9 shrink-0 sm:h-10 sm:w-10 lg:h-12.5 lg:w-12.5"
          />

          <div className="flex flex-col text-base font-semibold leading-tight text-white sm:text-lg">
            DC BENCHMARK

            <span className="text-[8px] font-medium sm:text-[10px]">
              BY DATA CENTER INTELLIGENCE
            </span>
          </div>
        </Link>

        {/* Botón hamburguesa - Mobile */}
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="rounded-lg border border-slate-700 p-2 text-white transition hover:border-cyan-300/40 lg:hidden"
          aria-label={isOpen ? "Cerrar menú" : "Abrir menú"}
          aria-expanded={isOpen}
        >
          {isOpen ? (
            <X className="h-6 w-6" />
          ) : (
            <Menu className="h-6 w-6" />
          )}
        </button>

        {/* Navegación Desktop */}
        <nav className="hidden items-center gap-1 lg:flex">
          <NavLink to="/" end className={navLinkClass}>
            Cómo funciona
          </NavLink>

          <NavLink to="/diagnostic" className={navLinkClass}>
            Las 5 áreas
          </NavLink>

          <NavLink to="/diagnostic" className={navLinkClass}>
            Privacidad
          </NavLink>

          <NavLink to="/methodology" className={navLinkClass}>
            Ver metodología
          </NavLink>
        </nav>
      </div>

      {/* Menú Mobile */}
      {isOpen && (
        <nav className="border-t border-[#183047] px-5 py-4 lg:hidden">
          <div className="flex flex-col gap-2">

            <NavLink
              to="/"
              end
              className={navLinkClass}
              onClick={closeMenu}
            >
              Como funciona
            </NavLink>

            <NavLink
              to="/diagnostic"
              className={navLinkClass}
              onClick={closeMenu}
            >
              Las 5 áreas
            </NavLink>

            <NavLink
              to="/diagnostic"
              className={navLinkClass}
              onClick={closeMenu}
            >
              Privacidad
            </NavLink>

            <NavLink
              to="/methodology"
              className={navLinkClass}
              onClick={closeMenu}
            >
              Ver metodología
            </NavLink>

          </div>
        </nav>
      )}
    </header>
  );
}