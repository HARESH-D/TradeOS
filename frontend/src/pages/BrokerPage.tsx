import { Check, Database, FileSpreadsheet, KeyRound, Link2, RefreshCw, ShieldCheck, Unplug, Upload, WalletCards } from 'lucide-react'
import { FormEvent, useCallback, useEffect, useRef, useState } from 'react'

import { api } from '../lib/api'
import { currency, formatDateTime } from '../lib/format'
import type { BrokerAccount, SyncRun, TradebookImportResult } from '../types'

export function BrokerPage() {
  const [account, setAccount] = useState<BrokerAccount | null>(null)
  const [history, setHistory] = useState<SyncRun[]>([])
  const [mode, setMode] = useState<'demo' | 'angel'>('demo')
  const [form, setForm] = useState({ api_key: '', client_code: '', pin: '', totp: '' })
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [tradebookFile, setTradebookFile] = useState<File | null>(null)
  const [importResult, setImportResult] = useState<TradebookImportResult | null>(null)
  const tradebookInput = useRef<HTMLInputElement>(null)
  const latestDetails = history[0]?.details
  const tradeCount = Number(account?.counts?.trades ?? 0)
    || Number(latestDetails?.trades ?? 0)
    || (Number(latestDetails?.closed_trades ?? 0) + Number(latestDetails?.open_positions ?? latestDetails?.open_lots ?? 0))

  const load = useCallback(async () => {
    const [broker, runs] = await Promise.all([api<BrokerAccount>('/broker'), api<SyncRun[]>('/broker/sync/history')])
    setAccount(broker)
    setHistory(runs)
  }, [])

  useEffect(() => { void load().catch((reason) => setError(reason.message)) }, [load])

  async function connect(event: FormEvent) {
    event.preventDefault()
    setBusy(true); setError(''); setMessage('')
    try {
      const payload = mode === 'demo' ? { mode } : { mode, ...form }
      await api('/broker/connect', { method: 'POST', body: JSON.stringify(payload) })
      setMessage(mode === 'demo' ? 'Demo broker connected and synced.' : 'Angel One connected successfully.')
      await load()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Connection failed')
    } finally { setBusy(false) }
  }

  async function sync() {
    setBusy(true); setError(''); setMessage('')
    try {
      const result = await api<{ records_synced: number }>('/broker/sync', { method: 'POST' })
      setMessage(`${result.records_synced} broker records synchronized.`)
      await load()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Sync failed')
    } finally { setBusy(false) }
  }

  async function importTradebook() {
    if (!tradebookFile) return
    setBusy(true); setError(''); setMessage(''); setImportResult(null)
    try {
      const body = new FormData()
      body.append('file', tradebookFile)
      const result = await api<TradebookImportResult>('/broker/tradebook/import', { method: 'POST', body })
      setImportResult(result)
      setMessage(`${result.executions_added} new executions imported; ${result.executions_existing} already existed.`)
      setTradebookFile(null)
      if (tradebookInput.current) tradebookInput.current.value = ''
      await load()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Tradebook import failed')
    } finally { setBusy(false) }
  }

  return (
    <div className="broker-page">
      <div className="workspace-toolbar">
        <div className="sync-summary"><span className={`status-dot ${account?.status}`} /><strong>{account?.broker_name ?? 'Broker disconnected'}</strong><span>{account?.client_code ?? 'No account selected'}</span></div>
        <button className="primary-button" onClick={sync} disabled={busy || !account?.id || ['statement', 'tradebook'].includes(account.mode ?? '')}><RefreshCw size={16} className={busy ? 'spin' : ''} />{['statement', 'tradebook'].includes(account?.mode ?? '') ? 'Tradebook account' : 'Sync now'}</button>
      </div>
      {(message || error) && <div className={`page-alert ${error ? 'error' : 'success'}`}>{error || message}</div>}

      <section className="broker-overview">
        <div className="broker-identity">
          <div className="broker-logo">A1</div>
          <div><span className="eyebrow">Connected broker</span><h2>{account?.broker_name ?? 'No broker connected'}</h2><p>Last synced {formatDateTime(account?.last_synced_at)}</p></div>
        </div>
        <div className="broker-balance"><span>Available account balance</span><strong>{currency.format(account?.account_balance ?? 0)}</strong></div>
        <div className="connection-badge"><Check size={15} />{account?.status ?? 'disconnected'}</div>
      </section>

      <section className="sync-count-grid">
        <div><WalletCards size={18} /><span>Holdings</span><strong>{account?.counts?.holdings ?? 0}</strong></div>
        <div><Database size={18} /><span>Trades</span><strong>{tradeCount}</strong></div>
        <div><Link2 size={18} /><span>Orders</span><strong>{account?.counts?.orders ?? 0}</strong></div>
        <div><Unplug size={18} /><span>Positions</span><strong>{account?.counts?.positions ?? 0}</strong></div>
      </section>

      <section className="broker-content-grid">
        <form className="panel connection-panel" onSubmit={connect}>
          <div className="panel-header"><div><h2>Broker connection</h2><p>Angel One SmartAPI</p></div><KeyRound size={18} /></div>
          <div className="segmented-control"><button type="button" className={mode === 'demo' ? 'active' : ''} onClick={() => setMode('demo')}>Demo data</button><button type="button" className={mode === 'angel' ? 'active' : ''} onClick={() => setMode('angel')}>Live account</button></div>
          {mode === 'angel' ? (
            <div className="form-grid">
              <label>API key<input value={form.api_key} onChange={(event) => setForm({ ...form, api_key: event.target.value })} required /></label>
              <label>Client code<input value={form.client_code} onChange={(event) => setForm({ ...form, client_code: event.target.value })} required /></label>
              <label>PIN<input type="password" value={form.pin} onChange={(event) => setForm({ ...form, pin: event.target.value })} required /></label>
              <label>Current TOTP<input inputMode="numeric" maxLength={6} value={form.totp} onChange={(event) => setForm({ ...form, totp: event.target.value })} required /></label>
            </div>
          ) : <div className="demo-connect-block"><div className="demo-broker-symbol"><Database size={22} /></div><div><strong>TradeOS demo portfolio</strong><p>Deterministic holdings, positions and trade history</p></div></div>}
          <div className="security-note"><ShieldCheck size={17} /><span>PIN and TOTP are used for login only and are never stored.</span></div>
          <button className="primary-button connect-button" disabled={busy}>{busy ? 'Connecting...' : mode === 'demo' ? 'Connect demo broker' : 'Connect Angel One'}</button>
        </form>

        <section className="panel history-panel">
          <div className="panel-header"><div><h2>Sync history</h2><p>Recent broker imports</p></div></div>
          <div className="sync-history-list">
            {history.length === 0 && <div className="empty-state small">No sync runs yet</div>}
            {history.map((run) => <div className="sync-history-row" key={run.id}><span className={`sync-run-icon ${run.status}`}>{['statement', 'tradebook'].includes(String(run.details?.source)) ? <FileSpreadsheet size={16} /> : <RefreshCw size={16} />}</span><div><strong>{run.details?.source === 'tradebook' ? 'Tradebook import' : run.details?.source === 'statement' ? 'Legacy P&L import' : 'Manual broker sync'}</strong><span>{formatDateTime(run.completed_at ?? run.started_at)}</span></div><div className="sync-result"><strong>{run.records_synced}</strong><span>{run.details?.source === 'tradebook' ? 'new executions' : 'records'}</span></div><span className={`status-pill ${run.status}`}>{run.status}</span></div>)}
          </div>
        </section>

        <section className="panel tradebook-panel">
          <div className="panel-header"><div><h2>Import equity tradebook</h2><p>Angel One execution history XLSX</p></div><FileSpreadsheet size={18} /></div>
          <div className="tradebook-import-body">
            <input ref={tradebookInput} className="visually-hidden" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={(event) => setTradebookFile(event.target.files?.[0] ?? null)} />
            <button type="button" className="tradebook-file-picker" onClick={() => tradebookInput.current?.click()}>
              <span><Upload size={20} /></span>
              <div><strong>{tradebookFile?.name ?? 'Choose Angel One tradebook'}</strong><small>{tradebookFile ? `${(tradebookFile.size / 1024).toFixed(1)} KB` : 'XLSX, up to 4 MB'}</small></div>
            </button>
            <button type="button" className="primary-button tradebook-import-button" onClick={importTradebook} disabled={busy || !tradebookFile}>{busy ? 'Importing...' : 'Import tradebook'}</button>
          </div>
          {importResult && <div className="tradebook-result"><div><span>Execution period</span><strong>{importResult.period_start} to {importResult.period_end}</strong></div><div><span>New</span><strong>{importResult.executions_added}</strong></div><div><span>Already stored</span><strong>{importResult.executions_existing}</strong></div><div><span>Closed trades</span><strong>{importResult.closed_trades}</strong></div><div><span>Open lots</span><strong>{importResult.open_lots}</strong></div></div>}
          <div className="tradebook-date-note"><ShieldCheck size={16} /><span>Trade IDs prevent repeat uploads. P&amp;L is FIFO-derived from executions and excludes broker charges.{importResult?.unmatched_sell_quantity ? ` ${importResult.unmatched_sell_quantity} sold units need earlier buy history.` : ''}</span></div>
        </section>
      </section>
    </div>
  )
}
