import { useState, useEffect } from 'react'

interface CompanyInfoProps {
  ticker: string
  compact?: boolean
}

interface CompanyData {
  price: {
    ticker: string
    current_price: number
    previous_close: number
    change: number
    change_percent: number
  }
  company: {
    name: string
    sector: string
    industry: string
    market_cap: number
  }
}

export default function CompanyInfo({ ticker, compact }: CompanyInfoProps) {
  const [data, setData] = useState<CompanyData | null>(null)

  useEffect(() => {
    fetchInfo()
  }, [ticker])

  const fetchInfo = async () => {
    try {
      const res = await fetch(`/api/stocks/${ticker}`)
      const json = await res.json()
      setData(json)
    } catch (err) {
      console.error('Failed to fetch info:', err)
    }
  }

  if (!data) return compact ? null : <div className="bg-surface-alt border border-line rounded-lg p-4 h-24 animate-pulse" />

  if (compact) {
    return (
      <div className="flex items-center gap-3 text-xs">
        <span className="text-txt-muted">{data.company.sector}</span>
        <span className="text-txt-muted">•</span>
        <span className={`tabular-nums font-medium ${data.price.change >= 0 ? 'text-up' : 'text-down'}`}>
          ${data.price.current_price.toFixed(2)}
          <span className="ml-1.5 text-xxs">
            {data.price.change >= 0 ? '+' : ''}{data.price.change_percent.toFixed(2)}%
          </span>
        </span>
      </div>
    )
  }

  const formatCap = (cap: number) => {
    if (cap >= 1e12) return `$${(cap / 1e12).toFixed(2)}T`
    if (cap >= 1e9) return `$${(cap / 1e9).toFixed(2)}B`
    return `$${(cap / 1e6).toFixed(0)}M`
  }

  return (
    <div className="bg-surface-alt border border-line rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-txt">{data.price.ticker}</span>
            <span className="text-xxs px-1.5 py-0.5 rounded bg-surface-overlay text-txt-muted">{data.company.sector}</span>
          </div>
          <p className="text-xs text-txt-muted mt-0.5">{data.company.name}</p>
        </div>
      </div>
      <div className="mb-3">
        <p className="text-2xl font-bold tabular-nums text-txt">${data.price.current_price.toFixed(2)}</p>
        <p className={`text-sm tabular-nums font-medium ${data.price.change >= 0 ? 'text-up' : 'text-down'}`}>
          {data.price.change >= 0 ? '+' : ''}{data.price.change.toFixed(2)} ({data.price.change_percent.toFixed(2)}%)
        </p>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {[
          { label: 'Mkt Cap', value: formatCap(data.company.market_cap) },
          { label: 'Prev Close', value: `$${data.price.previous_close.toFixed(2)}` },
          { label: 'Industry', value: data.company.industry || '—' },
        ].map((item, i) => (
          <div key={i} className="bg-surface-elevated rounded px-2.5 py-1.5">
            <p className="text-xxs text-txt-muted">{item.label}</p>
            <p className="text-xs font-medium text-txt-dim">{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
