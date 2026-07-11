import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useMemo, useState } from 'react'

import { compactCurrency, currency } from '../lib/format'

type CalendarRow = { date: string; pnl: number; trades: number }

export function PnLCalendar({ rows }: { rows: CalendarRow[] }) {
  const initial = rows.length ? new Date(`${rows[rows.length - 1].date}T12:00:00`) : new Date()
  const [visibleMonth, setVisibleMonth] = useState(new Date(initial.getFullYear(), initial.getMonth(), 1))
  const valueMap = useMemo(() => new Map(rows.map((row) => [row.date, row])), [rows])
  const year = visibleMonth.getFullYear()
  const month = visibleMonth.getMonth()
  const dayCount = new Date(year, month + 1, 0).getDate()
  const startDay = new Date(year, month, 1).getDay()
  const cells = Array.from({ length: 42 }, (_, index) => {
    const day = index - startDay + 1
    if (day < 1 || day > dayCount) return null
    const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    return { day, value: valueMap.get(key) }
  })
  const monthRows = rows.filter((row) => {
    const date = new Date(`${row.date}T12:00:00`)
    return date.getFullYear() === year && date.getMonth() === month
  })
  const monthlyPnl = monthRows.reduce((sum, row) => sum + row.pnl, 0)

  return (
    <section className="panel calendar-panel">
      <div className="panel-header calendar-header">
        <div>
          <h2>Profit calendar</h2>
          <p>{monthRows.length} active trading days</p>
        </div>
        <div className="month-controls">
          <button className="icon-button" onClick={() => setVisibleMonth(new Date(year, month - 1, 1))} title="Previous month"><ChevronLeft size={18} /></button>
          <strong>{visibleMonth.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}</strong>
          <button className="icon-button" onClick={() => setVisibleMonth(new Date(year, month + 1, 1))} title="Next month"><ChevronRight size={18} /></button>
        </div>
        <div className={`month-total ${monthlyPnl >= 0 ? 'positive' : 'negative'}`}>
          <span>Monthly P&amp;L</span>
          <strong>{currency.format(monthlyPnl)}</strong>
        </div>
      </div>
      <div className="calendar-weekdays">{['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => <span key={day}>{day}</span>)}</div>
      <div className="calendar-grid">
        {cells.map((cell, index) => (
          <div key={index} className={`calendar-cell ${cell?.value ? (cell.value.pnl >= 0 ? 'gain' : 'loss') : ''} ${!cell ? 'empty' : ''}`}>
            {cell && <span className="calendar-day">{cell.day}</span>}
            {cell?.value && <><strong>{compactCurrency.format(cell.value.pnl)}</strong><small>{cell.value.trades} {cell.value.trades === 1 ? 'trade' : 'trades'}</small></>}
          </div>
        ))}
      </div>
    </section>
  )
}

