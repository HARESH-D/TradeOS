import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-quartz.css'

import type { ColDef, GridApi, GridReadyEvent, ValueFormatterParams } from 'ag-grid-community'
import { AgGridReact } from 'ag-grid-react'
import { CalendarRange, Download, Filter, RefreshCw, Search, SlidersHorizontal, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { api } from '../lib/api'
import { currency, holdingTime } from '../lib/format'
import type { Trade } from '../types'

const moneyFormatter = ({ value }: ValueFormatterParams) => value == null ? '-' : currency.format(value)
const dateTimeFormatter = ({ value }: ValueFormatterParams) => value == null
  ? '-'
  : new Date(value).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })

export function AnalysisPage() {
  const [rows, setRows] = useState<Trade[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [product, setProduct] = useState('ALL')
  const [outcome, setOutcome] = useState('')
  const [gridApi, setGridApi] = useState<GridApi | null>(null)
  const [displayedRows, setDisplayedRows] = useState(0)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({ limit: '500' })
    if (search) params.set('search', search)
    if (product !== 'ALL') params.set('product', product)
    if (outcome) params.set('outcome', outcome)
    try {
      const response = await api<{ total: number; items: Trade[] }>(`/analysis?${params}`)
      setRows(response.items); setTotal(response.total); setError('')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load trades')
    } finally { setLoading(false) }
  }, [outcome, product, search])

  useEffect(() => { const timeout = window.setTimeout(() => void load(), 220); return () => window.clearTimeout(timeout) }, [load])

  const columns = useMemo((): ColDef<Trade>[] => [
    { field: 'symbol', headerName: 'Symbol', pinned: 'left', minWidth: 135, cellClass: 'symbol-cell' },
    { field: 'trade_date', headerName: 'Trade date', minWidth: 140, sort: 'desc', filter: 'agDateColumnFilter', valueFormatter: ({ value }) => new Date(`${value}T12:00:00`).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) },
    { field: 'entry_time', headerName: 'Entry time', minWidth: 185, valueFormatter: dateTimeFormatter },
    { field: 'exit_time', headerName: 'Exit time', minWidth: 185, valueFormatter: dateTimeFormatter },
    { field: 'exchange', headerName: 'Exchange', minWidth: 105 },
    { field: 'product', headerName: 'Product', minWidth: 125 },
    { field: 'direction', headerName: 'Side', minWidth: 95, cellClassRules: { 'positive': ({ value }) => value === 'LONG', 'negative': ({ value }) => value === 'SELL' } },
    { field: 'quantity', headerName: 'Qty', minWidth: 88, filter: 'agNumberColumnFilter' },
    { field: 'entry_price', headerName: 'Entry price', minWidth: 125, filter: 'agNumberColumnFilter', valueFormatter: moneyFormatter },
    { field: 'exit_price', headerName: 'Exit price', minWidth: 125, filter: 'agNumberColumnFilter', valueFormatter: moneyFormatter },
    { field: 'gross_pnl', headerName: 'Gross P&L', minWidth: 130, filter: 'agNumberColumnFilter', valueFormatter: moneyFormatter, cellClassRules: { 'positive': ({ value }) => value > 0, 'negative': ({ value }) => value < 0 } },
    { field: 'charges', headerName: 'Charges', minWidth: 115, filter: 'agNumberColumnFilter', valueFormatter: moneyFormatter },
    { field: 'net_pnl', headerName: 'Net P&L', minWidth: 130, filter: 'agNumberColumnFilter', valueFormatter: moneyFormatter, cellClassRules: { 'pnl-positive': ({ value }) => value > 0, 'pnl-negative': ({ value }) => value < 0 } },
    { field: 'return_percent', headerName: 'Return %', minWidth: 120, filter: 'agNumberColumnFilter', valueFormatter: ({ value }) => `${Number(value).toFixed(2)}%`, cellClassRules: { 'positive': ({ value }) => value > 0, 'negative': ({ value }) => value < 0 } },
    { field: 'holding_minutes', headerName: 'Holding', minWidth: 105, filter: 'agNumberColumnFilter', valueFormatter: ({ value }) => holdingTime(Number(value)) },
    { field: 'status', headerName: 'Status', minWidth: 110 },
    { field: 'broker_trade_id', headerName: 'Trade ID', minWidth: 190 },
  ], [])

  const defaultColDef = useMemo<ColDef>(() => ({ sortable: true, resizable: true, filter: true, floatingFilter: true, suppressHeaderMenuButton: false }), [])
  function resetFilters() { setSearch(''); setProduct('ALL'); setOutcome(''); gridApi?.setFilterModel(null) }
  function onGridReady(event: GridReadyEvent) { setGridApi(event.api); setDisplayedRows(event.api.getDisplayedRowCount()) }

  return (
    <div className="analysis-page">
      <div className="analysis-summary-row">
        <div><span>Trade ledger</span><strong>{total} records</strong></div>
        <div><span>Net P&amp;L</span><strong className={rows.reduce((sum, row) => sum + row.net_pnl, 0) >= 0 ? 'positive' : 'negative'}>{currency.format(rows.reduce((sum, row) => sum + row.net_pnl, 0))}</strong></div>
        <div><span>Filtered rows</span><strong>{displayedRows || rows.length}</strong></div>
      </div>
      <div className="analysis-toolbar">
        <div className="search-field"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search symbol or trade ID" />{search && <button onClick={() => setSearch('')} title="Clear search"><X size={15} /></button>}</div>
        <label className="filter-select"><Filter size={16} /><select value={product} onChange={(event) => setProduct(event.target.value)}><option value="ALL">All products</option><option value="EQUITY">Equity</option><option value="DELIVERY">Delivery</option><option value="SWING">Swing</option></select></label>
        <label className="filter-select"><SlidersHorizontal size={16} /><select value={outcome} onChange={(event) => setOutcome(event.target.value)}><option value="">All outcomes</option><option value="win">Winners</option><option value="loss">Losers</option><option value="flat">Flat</option><option value="open">Open positions</option></select></label>
        <button className="select-button date-filter"><CalendarRange size={16} />All dates</button>
        <div className="analysis-toolbar-spacer" />
        <button className="icon-button" onClick={resetFilters} title="Reset filters"><RefreshCw size={17} /></button>
        <button className="secondary-button" onClick={() => gridApi?.exportDataAsCsv({ fileName: 'tradeos-analysis.csv' })}><Download size={16} />Export CSV</button>
      </div>
      {error && <div className="page-alert error">{error}</div>}
      <div className="grid-caption"><span><span className="live-dot" /> Tradebook-derived records</span><span>FIFO P&amp;L currently excludes broker charges</span></div>
      <div className="ag-theme-quartz trade-grid">
        <AgGridReact<Trade>
          rowData={rows}
          columnDefs={columns}
          defaultColDef={defaultColDef}
          onGridReady={onGridReady}
          onFilterChanged={(event) => setDisplayedRows(event.api.getDisplayedRowCount())}
          onModelUpdated={(event) => setDisplayedRows(event.api.getDisplayedRowCount())}
          loading={loading}
          rowHeight={48}
          headerHeight={42}
          floatingFiltersHeight={40}
          animateRows
          enableCellTextSelection
          ensureDomOrder
          pagination
          paginationPageSize={25}
          paginationPageSizeSelector={[25, 50, 100]}
        />
      </div>
    </div>
  )
}
