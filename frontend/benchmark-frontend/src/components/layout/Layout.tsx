import { Outlet } from 'react-router-dom'

import Footer from './Footer'
import Header from './Header'

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <Header />
      <main>
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}