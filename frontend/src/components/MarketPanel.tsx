import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

function IndexRow({ label, data }: { label: string; data: any }) {
  if (!data) return null
  const up = data.change >= 0
  const color = up ? 'rgb(var(--color-up))' : 'rgb(var(--color-down))'
  return (
    <div className="flex items-center justify-between py-1.5" style={{ borderBottom: '1px solid rgb(var(--color-line) / 0.3)' }}>
      <span className="text-xs" style={{ color: 'rgb(var(--color-txt-dim))' }}>{label}</span>
      <div className="text-right">
        <div className="text-xs font-medium tabular-nums" style={{ color: 'rgb(var(--color-txt))' }}>{data.value}</div>
        <div className="text-xxs tabular-nums" style={{ color }}>
          {up ? '+' : ''}{data.change} ({up ? '+' : ''}{data.change_percent}%)
        </div>
      </div>
    </div>
  )
}

export default function MarketPanel() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    cachedFetch('/api/market/overview', 60000)
      .then(json => setData(json?.indices || null))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="card p-4">
      <p className="section-header">Market</p>
      {loading ? (
        <div className="space-y-2">{[1, 2, 3, 4, 5].map(i => <div key={i} className="h-8 skeleton" />)}</div>
      ) : data ? (
        <div>
          <IndexRow label="S&P 500" data={data.sp500} />
          <IndexRow label="NASDAQ" data={data.nasdaq} />
          <IndexRow label="Dow Jones" data={data.dow} />
          <IndexRow label="VIX" data={data.vix} />
          <IndexRow label="10Y Yield" data={data.treasury_10y} />
        </div>
      ) : (
        <p className="text-xs" style={{ color: 'rgb(var(--color-txt-muted))' }}>Market data unavailable</p>
      )}
    </div>
  )
}
