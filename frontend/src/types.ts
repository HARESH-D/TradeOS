export type User = {
  id: number
  name: string
  email: string
}

export type Trade = {
  id: number
  broker_trade_id: string
  trade_date: string
  symbol: string
  exchange: string
  segment: string
  product: string
  direction: string
  quantity: number
  entry_price: number
  exit_price: number | null
  gross_pnl: number
  charges: number
  net_pnl: number
  return_percent: number
  status: string
  entry_time: string | null
  exit_time: string | null
  holding_minutes: number
}

export type DashboardData = {
  broker: {
    name: string | null
    mode: string | null
    status: string
    last_synced_at: string | null
    counts: Record<string, number>
  }
  metrics: {
    account_balance: number
    net_pnl: number
    win_rate: number
    profit_factor: number
    avg_win: number
    avg_loss: number
    expectancy: number
    max_drawdown: number
    trade_count: number
    winner_count: number
    loser_count: number
  }
  series: Array<{ date: string; daily: number; cumulative: number; drawdown: number }>
  calendar: Array<{ date: string; pnl: number; trades: number }>
  recent_trades: Trade[]
}

export type BrokerAccount = {
  id?: number
  broker_name?: string
  mode?: string
  status: string
  client_code?: string
  account_balance?: number
  last_synced_at?: string | null
  counts?: Record<string, number>
}

export type SyncRun = {
  id: number
  status: string
  started_at: string
  completed_at: string | null
  records_synced: number
  details: Record<string, number | string> | null
  error_message: string | null
}

export type TradebookImportResult = {
  status: string
  executions_received: number
  executions_added: number
  executions_existing: number
  total_executions: number
  closed_trades: number
  open_lots: number
  open_positions: number
  unmatched_sell_executions: number
  unmatched_sell_quantity: number
  period_start: string
  period_end: string
  charges_included: boolean
}

export type AgentRuntimeStatus = {
  providers: {
    gemini: { configured: boolean; model: string | null; modes: Array<'research' | 'trades' | 'portfolio'> }
    llama: { configured: boolean; model: string | null; modes: Array<'research' | 'trades' | 'portfolio'> }
  }
  modes: Record<'research' | 'trades' | 'portfolio', boolean>
}

export type AgentSource = {
  url: string
  title: string
  cited_text: string
}

export type AgentRun = {
  id: number
  mode: 'research' | 'trades' | 'portfolio'
  provider: 'gemini' | 'llama' | string
  model: string
  status: 'running' | 'completed' | 'failed'
  prompt: string
  answer: string | null
  sources: AgentSource[]
  search_queries: string[]
  error_message: string | null
  created_at: string
  completed_at: string | null
}
