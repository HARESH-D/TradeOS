import {
  BarChart3,
  Bot,
  CandlestickChart,
  ChevronLeft,
  LayoutDashboard,
  LogOut,
  Menu,
  RefreshCw,
  Settings,
  TableProperties,
  X,
} from 'lucide-react'
import { ReactNode, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'

import type { User } from '../types'

type AppShellProps = {
  children: ReactNode
  user: User
  onLogout: () => void
}

const navigation = [
  { label: 'Dashboard', icon: LayoutDashboard, to: '/' },
  { label: 'Broker Sync', icon: RefreshCw, to: '/broker' },
  { label: 'Analysis', icon: TableProperties, to: '/analysis' },
  { label: 'AI Agent', icon: Bot, to: '/agent' },
]

const titles: Record<string, string> = {
  '/': 'Dashboard',
  '/broker': 'Broker Sync',
  '/analysis': 'Trade Analysis',
  '/agent': 'AI Agent',
}

export function AppShell({ children, user, onLogout }: AppShellProps) {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  return (
    <div className={`app-shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
      {mobileOpen && <button className="sidebar-scrim" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}
      <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="brand-row">
          <div className="brand-mark"><CandlestickChart size={20} /></div>
          {!collapsed && <span className="brand-name">TradeOS</span>}
          <button className="icon-button sidebar-close" onClick={() => setMobileOpen(false)} title="Close navigation"><X size={18} /></button>
        </div>
        <nav className="primary-nav" aria-label="Main navigation">
          {navigation.map(({ label, icon: Icon, to }) => (
            <NavLink key={to} to={to} end={to === '/'} onClick={() => setMobileOpen(false)} title={collapsed ? label : undefined}>
              <Icon size={19} />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-spacer" />
        <button className="nav-button" title="Settings"><Settings size={19} />{!collapsed && <span>Settings</span>}</button>
        <button className="nav-button" onClick={onLogout} title="Sign out"><LogOut size={19} />{!collapsed && <span>Sign out</span>}</button>
        <button className="collapse-button" onClick={() => setCollapsed((value) => !value)} title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
          <ChevronLeft size={17} />
        </button>
      </aside>
      <div className="app-body">
        <header className="topbar">
          <div className="page-heading">
            <button className="icon-button mobile-menu" onClick={() => setMobileOpen(true)} title="Open navigation"><Menu size={19} /></button>
            <div>
              <h1>{titles[location.pathname] ?? 'TradeOS'}</h1>
              <p>Trading workspace</p>
            </div>
          </div>
          <div className="topbar-actions">
            <div className="market-status"><span /> Markets closed</div>
            <div className="user-avatar" title={user.email}>{user.name.slice(0, 2).toUpperCase()}</div>
          </div>
        </header>
        <main className="page-content">{children}</main>
      </div>
    </div>
  )
}
