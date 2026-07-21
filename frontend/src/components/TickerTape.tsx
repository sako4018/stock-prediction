import { useState, useEffect } from 'react'

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
    const interval = setInterval(fetchPrices, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchPrices = async () => {
    const watchlist = JSON.parse(localStorage.getItem('watchlist') || '["AAPL","MSFT","GOOGL","TSLA","NVDA","META","AMZN","JPM","V"]')
    const results: TickerItem[] = []

    for (const ticker of watchlist) {
      try {
        const res = await fetch(`/api/stocks/${ticker}`)
        const data = await res.json()
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

  // Duplicate items for seamless scroll
  const doubled = [...items, ...items]

  return (
    <div className="h-8 bg-surface-elevated border-b border-line overflow-hidden flex items-center relative">
      <div className="flex items-center gap-6 animate-ticker whitespace-nowrap">
        {doubled.map((item, i) => {
          const isPositive = (item.changePercent ?? 0) >= 0
          return (
            <span key={`${item.ticker}-${i}`} className="flex items-center gap-2 text-xs">
              <span className="font-semibold text-txt">{item.ticker}</span>
              {item.price ? (
                <>
                  <span className="text-txt-sec tabular-nums">${item.price.toFixed(2)}</span>
                  <span className={`tabular-nums font-medium ${isPositive ? 'text-up' : 'text-down'}`}>
                    {isPositive ? '▲' : '▼'}{Math.abs(item.changePercent ?? 0).toFixed(2)}%
                  </span>
                </>
              ) : (
                <span className="text-txt-dim">—</span>
              )}
            </span>
          )
        })}
      </div>
    </div>
  )
}
