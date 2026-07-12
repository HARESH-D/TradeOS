import { Activity, BadgeIndianRupee, CalendarDays, RefreshCw, Scale, Target, TrendingUp, Upload, WalletCards } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { MetricCard } from '../components/MetricCard'
import { PnLCalendar } from '../components/PnLCalendar'
import { api } from '../lib/api'
import { compactCurrency, currency, formatDateTime } from '../lib/format'
import type { DashboardData } from '../types'

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      setData(await api<DashboardData>('/dashboard'))
      setError('')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load dashboard')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  async function sync() {
    setSyncing(true)
    try {
      await api('/broker/sync', { method: 'POST' })
      await load()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  if (loading) return <div className="loading-state"><RefreshCw className="spin" />Loading dashboard</div>
  if (!data) return <div className="empty-state">{error || 'Dashboard data is unavailable'}</div>
  const { metrics } = data
  const netTrend = metrics.net_pnl >= 0 ? 'positive' : 'negative'

  return (
    <div className="dashboard-page">
      <div className="workspace-toolbar">
        <div className="sync-summary"><span className={`status-dot ${data.broker.status}`} /> <strong>{data.broker.name ?? 'No broker'}</strong><span>Last sync {formatDateTime(data.broker.last_synced_at)}</span></div>
        <div className="toolbar-actions"><button className="select-button"><CalendarDays size={16} />All history</button>{data.broker.mode === 'statement' ? <Link className="primary-button" to="/broker"><Upload size={16} />Upload statement</Link> : <button className="primary-button" onClick={sync} disabled={syncing}><RefreshCw size={16} className={syncing ? 'spin' : ''} />{syncing ? 'Syncing...' : 'Sync broker'}</button>}</div>
      </div>
      {error && <div className="page-alert">{error}</div>}

      <section className="metrics-grid">
        <MetricCard label="Account balance" value={currency.format(metrics.account_balance)} helper={`${currency.format(metrics.net_pnl)} net P&L`} trend={netTrend} icon={WalletCards} />
        <MetricCard label="Win rate" value={`${metrics.win_rate.toFixed(1)}%`} helper={`${metrics.winner_count} wins / ${metrics.loser_count} losses`} trend={metrics.win_rate >= 50 ? 'positive' : 'negative'} icon={Target} />
        <MetricCard label="Profit factor" value={metrics.profit_factor.toFixed(2)} helper={metrics.profit_factor >= 1 ? 'Profitable edge' : 'Below breakeven'} trend={metrics.profit_factor >= 1 ? 'positive' : 'negative'} icon={Scale} />
        <MetricCard label="Avg win / loss" value={`${compactCurrency.format(metrics.avg_win)} / ${compactCurrency.format(metrics.avg_loss)}`} helper={`${metrics.trade_count} closed trades`} icon={TrendingUp} />
        <MetricCard label="Trade expectancy" value={currency.format(metrics.expectancy)} helper="Average per closed trade" trend={metrics.expectancy >= 0 ? 'positive' : 'negative'} icon={BadgeIndianRupee} />
      </section>

      <section className="dashboard-grid dashboard-grid-top">
        <div className="panel chart-panel wide-panel">
          <div className="panel-header"><div><h2>Equity curve</h2><p>Daily net cumulative P&amp;L</p></div><span className={`panel-stat ${netTrend}`}>{currency.format(metrics.net_pnl)}</span></div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.series} margin={{ top: 14, right: 8, left: 0, bottom: 0 }}>
                <defs><linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#6d5bd0" stopOpacity={0.28} /><stop offset="100%" stopColor="#6d5bd0" stopOpacity={0.02} /></linearGradient></defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8e9ef" />
                <XAxis dataKey="date" tickFormatter={(value) => new Date(`${value}T12:00:00`).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })} tick={{ fontSize: 11, fill: '#77798a' }} axisLine={false} tickLine={false} minTickGap={38} />
                <YAxis tickFormatter={(value) => compactCurrency.format(value)} tick={{ fontSize: 11, fill: '#77798a' }} axisLine={false} tickLine={false} width={62} />
                <Tooltip formatter={(value: number) => currency.format(value)} labelFormatter={(value) => new Date(`${value}T12:00:00`).toLocaleDateString('en-IN', { dateStyle: 'medium' })} />
                <Area type="monotone" dataKey="cumulative" stroke="#6d5bd0" strokeWidth={2} fill="url(#equityFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="panel evaluation-panel">
          <div className="panel-header"><div><h2>Performance</h2><p>Current synced account</p></div><Activity size={18} /></div>
          <dl className="evaluation-list">
            <div><dt>Total trades</dt><dd>{metrics.trade_count}</dd></div>
            <div><dt>Net return</dt><dd className={netTrend}>{currency.format(metrics.net_pnl)}</dd></div>
            <div><dt>Best average</dt><dd className="positive">{currency.format(metrics.avg_win)}</dd></div>
            <div><dt>Average loss</dt><dd className="negative">-{currency.format(metrics.avg_loss)}</dd></div>
            <div><dt>Max drawdown</dt><dd className="negative">{currency.format(metrics.max_drawdown)}</dd></div>
          </dl>
          <div className="win-loss-track"><span style={{ width: `${metrics.win_rate}%` }} /><div><small>Wins {metrics.winner_count}</small><small>Losses {metrics.loser_count}</small></div></div>
        </div>
      </section>

      <PnLCalendar rows={data.calendar} />

      <section className="dashboard-grid dashboard-grid-bottom">
        <div className="panel chart-panel">
          <div className="panel-header"><div><h2>Daily net P&amp;L</h2><p>Realized performance by close date</p></div></div>
          <div className="chart-wrap compact-chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.series} margin={{ top: 12, right: 6, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8e9ef" />
                <XAxis dataKey="date" hide />
                <YAxis tickFormatter={(value) => compactCurrency.format(value)} tick={{ fontSize: 11, fill: '#77798a' }} axisLine={false} tickLine={false} width={62} />
                <Tooltip formatter={(value: number) => currency.format(value)} />
                <Bar dataKey="daily" radius={[2, 2, 0, 0]}>{data.series.map((entry) => <Cell key={entry.date} fill={entry.daily >= 0 ? '#24a47a' : '#ec5b61'} />)}</Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="panel recent-panel">
          <div className="panel-header"><div><h2>Recent trades</h2><p>Latest closed positions</p></div></div>
          <div className="table-scroll"><table className="data-table"><thead><tr><th>Symbol</th><th>Date</th><th>Return</th><th>Net P&amp;L</th></tr></thead><tbody>{data.recent_trades.map((trade) => <tr key={trade.id}><td><strong>{trade.symbol}</strong><small>{trade.product}</small></td><td>{new Date(`${trade.trade_date}T12:00:00`).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}</td><td className={trade.return_percent >= 0 ? 'positive' : 'negative'}>{trade.return_percent.toFixed(2)}%</td><td className={trade.net_pnl >= 0 ? 'positive' : 'negative'}>{currency.format(trade.net_pnl)}</td></tr>)}</tbody></table></div>
        </div>
      </section>
    </div>
  )
}
