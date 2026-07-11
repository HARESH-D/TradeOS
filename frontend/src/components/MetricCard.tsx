import { ArrowDownRight, ArrowUpRight, Info } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

type MetricCardProps = {
  label: string
  value: string
  helper?: string
  trend?: 'positive' | 'negative' | 'neutral'
  icon: LucideIcon
}

export function MetricCard({ label, value, helper, trend = 'neutral', icon: Icon }: MetricCardProps) {
  const TrendIcon = trend === 'positive' ? ArrowUpRight : ArrowDownRight
  return (
    <article className="metric-card">
      <div className="metric-label"><span>{label}</span><Info size={14} /></div>
      <div className="metric-value-row">
        <strong>{value}</strong>
        <span className={`metric-icon ${trend}`}><Icon size={18} /></span>
      </div>
      {helper && (
        <div className={`metric-helper ${trend}`}>
          {trend !== 'neutral' && <TrendIcon size={14} />}{helper}
        </div>
      )}
    </article>
  )
}

