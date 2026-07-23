import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

const PERIODS = ['1D', '5D', '1M', '3M', '6M', 'YTD', '1Y', '5Y']

export default function PeriodReturns({ ticker }: { ticker: string }) {
  const [returns, setReturns] = useState<Record<string, number | null>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    cachedFetch(`/api/stocks/${ticker}/returns`)
      .then(json => setReturns(json.returns || {}))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [ticker])

  if (loading) return <div className="h-8 skeleton" />

  return (
    <div className="flex items-center gap-0 overflow-x-auto">
      {PERIODS.map(p => {
        const val = returns[p]
        const isUp = (val ?? 0) >= 0
        const color = val === null ? 'rgb(var(--color-txt-muted))' : isUp ? 'rgb(var(--color-up))' : 'rgb(var(--color-down))'
        return (
          <div key={p} className="flex flex-col items-center px-3 py-1.5 min-w-[52px]" style={{ borderRight: '1px solid rgb(var(--color-line) / 0.3)' }}>
            <span className="text-xxs font-medium" style={{ color: 'rgb(var(--color-txt-muted))' }}>{p}</span>
            <span className="text-xs font-bold tabular-nums" style={{ color }}>
              {val != null ? `${isUp ? '+' : ''}${val.toFixed(2)}%` : '--'}
            </span>
          </div>
        )
      })}
    </div>
  )
}
