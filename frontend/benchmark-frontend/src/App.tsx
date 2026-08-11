import { lazy, Suspense } from 'react'
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'

import Layout from '@/components/layout/Layout'

const Home = lazy(() => import('@/pages/Home/Home'))
const Diagnostic = lazy(() => import('@/pages/Diagnostic/Diagnostic'))
const Result = lazy(() => import('@/pages/Results/Result'))

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoading />}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/diagnostic" element={<Diagnostic />} />
            <Route path="/results/:id" element={<Result />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

function PageLoading() {
  return <p className="py-16 text-center text-gray-500">Cargando…</p>
}

function NotFound() {
  return (
    <div className="py-24 text-center">
      <p className="text-5xl font-bold text-gray-300">404</p>
      <h1 className="mt-2 text-2xl font-semibold text-gray-900">Página no encontrada</h1>
      <Link
        to="/"
        className="mt-4 inline-block text-sm font-medium text-blue-600 hover:text-blue-700"
      >
        Volver al inicio
      </Link>
    </div>
  )
}