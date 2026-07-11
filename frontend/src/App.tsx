import { lazy, Suspense, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from './components/AppShell'
import { LoginPage } from './pages/LoginPage'
import type { User } from './types'

const AnalysisPage = lazy(() => import('./pages/AnalysisPage').then((module) => ({ default: module.AnalysisPage })))
const BrokerPage = lazy(() => import('./pages/BrokerPage').then((module) => ({ default: module.BrokerPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((module) => ({ default: module.DashboardPage })))

function readUser(): User | null {
  try { return JSON.parse(localStorage.getItem('tradeos_user') ?? 'null') as User | null } catch { return null }
}

export default function App() {
  const [user, setUser] = useState<User | null>(readUser)

  function login(token: string, nextUser: User) {
    localStorage.setItem('tradeos_token', token)
    localStorage.setItem('tradeos_user', JSON.stringify(nextUser))
    setUser(nextUser)
  }

  function logout() {
    localStorage.removeItem('tradeos_token')
    localStorage.removeItem('tradeos_user')
    setUser(null)
  }

  if (!user) return <LoginPage onLogin={login} />

  return (
    <BrowserRouter>
      <AppShell user={user} onLogout={logout}>
        <Suspense fallback={<div className="loading-state">Loading workspace</div>}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/broker" element={<BrokerPage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </AppShell>
    </BrowserRouter>
  )
}
