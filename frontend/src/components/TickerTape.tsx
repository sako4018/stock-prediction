import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

interface TickerItem {
  ticker: string
  price: number | null
  change: number | null
  changePercent: number | null
}

export default function TickerTape() {
  const [items, setItems] = useState<TickerItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPrices()
    const interval = setInterval(fetchPrices, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchPrices = async () => {
    const watchlist = JSON.parse(localStorage.getItem('watchlist') || '["AAPL","MSFT","GOOGL","TSLA","NVDA","META","AMZN","JPM","V"]')
    const results: TickerItem[] = []

    for (const ticker of watchlist) {
      try {
        const data = await cachedFetch(`/api/stocks/${ticker}`)
        if (data.price) {
          results.push({
            ticker,
            price: data.price.current_price,
            change: data.price.change,
            changePercent: data.price.change_percent
          })
        }
      } catch {
        results.push({ ticker, price: null, change: null, changePercent: null })
      }
    }

    setItems(results)
    setLoading(false)
  }

  if (loading && items.length === 0) return null

  const doubled = [...items, ...items]

  return (
    <div className="h-7 overflow-hidden flex items-center relative" style={{
      background: 'rgb(var(--color-surface-alt))',
      borderBottom: '1px solid rgb(var(--color-line))',
    }}>
      <div className="flex items-center gap-5 animate-ticker whitespace-nowrap" style={{
        fontFamily: '"JetBrains Mono", monospace',
        fontSize: '0.6875rem',
      }}>
        {doubled.map((item, i) => {
          const isPositive = (item.changePercent ?? 0) >= 0
          return (
            <span key={`${item.ticker}-${i}`} className="flex items-center gap-2">
              <span className="font-semibold" style={{ color: 'rgb(var(--color-txt))' }}>{item.ticker}</span>
              {item.price ? (
                <>
                  <span style={{ color: 'rgb(var(--color-txt-sec))' }}>${item.price.toFixed(2)}</span>
                  <span className={`tabular-nums font-medium ${isPositive ? 'text-up' : 'text-down'}`}>
                    {isPositive ? '▲' : '▼'}{Math.abs(item.changePercent ?? 0).toFixed(2)}%
                  </span>
                </>
              ) : (
                <span style={{ color: 'rgb(var(--color-txt-dim))' }}>—</span>
              )}
            </span>
          )
        })}
      </div>
    </div>
  )
}
