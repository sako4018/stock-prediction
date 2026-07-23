import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

function fmt(n: number | undefined, decimals = 2): string {
  if (n === undefined || n === null) return '--'
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
  if (Math.abs(n) >= 1e6) return `${(n / 1e6).toFixed(1)}M`
  return n.toFixed(decimals)
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 text-xs" style={{ borderBottom: '1px solid rgb(var(--color-line) / 0.2)' }}>
      <span style={{ color: 'rgb(var(--color-txt-dim))' }}>{label}</span>
      <span className="font-medium tabular-nums" style={{ color: 'rgb(var(--color-txt))', fontFamily: '"JetBrains Mono", monospace' }}>{value}</span>
    </div>
  )
}

export default function KeyStats({ ticker }: { ticker: string }) {
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    cachedFetch(`/api/stocks/${ticker}`)
      .then(json => setData(json))
      .catch(() => {})
  }, [ticker])

  if (!data) return <div className="card p-4"><div className="h-40 skeleton" /></div>

  const p = data.price || {}
  const c = data.company || {}
  const open = p.current_price && p.change ? (p.current_price - p.change) : null

  return (
    <div className="card p-4">
      <p className="section-header">Key Statistics</p>
      {p.previous_close && <StatRow label="Previous Close" value={`$${p.previous_close.toFixed(2)}`} />}
      {open && <StatRow label="Open" value={`$${open.toFixed(2)}`} />}
      {p.change != null && <StatRow label="Change" value={`${p.change >= 0 ? '+' : ''}$${p.change?.toFixed(2)} (${p.change_percent >= 0 ? '+' : ''}${p.change_percent?.toFixed(2)}%)`} />}
      {c.market_cap && <StatRow label="Market Cap" value={fmt(c.market_cap, 0)} />}
      {c.sector && <StatRow label="Sector" value={c.sector} />}
      {c.industry && <StatRow label="Industry" value={c.industry} />}
      {c.employees && <StatRow label="Employees" value={c.employees.toLocaleString()} />}
    </div>
  )
}
