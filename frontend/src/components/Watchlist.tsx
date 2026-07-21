import { useState, useEffect } from 'react'

interface WatchlistProps {
  onSelect: (ticker: string) => void
  currentTicker: string
}

interface WatchlistItem {
  ticker: string
  price: number | null
  change: number | null
  changePercent: number | null
}

export default function Watchlist({ onSelect, currentTicker }: WatchlistProps) {
  const [watchlist, setWatchlist] = useState<string[]>(() => {
    const saved = localStorage.getItem('watchlist')
    return saved ? JSON.parse(saved) : ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
  })
  const [prices, setPrices] = useState<Record<string, WatchlistItem>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    localStorage.setItem('watchlist', JSON.stringify(watchlist))
    fetchPrices()
  }, [watchlist])

  const fetchPrices = async () => {
    setLoading(true)
    const newPrices: Record<string, WatchlistItem> = {}
    for (const ticker of watchlist) {
      try {
        const res = await fetch(`/api/stocks/${ticker}`)
        const data = await res.json()
        if (data.price) {
          newPrices[ticker] = {
            ticker,
            price: data.price.current_price,
            change: data.price.change,
            changePercent: data.price.change_percent
          }
        }
      } catch {
        newPrices[ticker] = { ticker, price: null, change: null, changePercent: null }
      }
    }
    setPrices(newPrices)
    setLoading(false)
  }

  const addSymbol = () => {
    const input = prompt('Ticker symbol:')
    if (input && !watchlist.includes(input.toUpperCase())) {
      setWatchlist([...watchlist, input.toUpperCase()])
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xxs font-medium text-txt-muted uppercase tracking-wider">Watchlist</span>
        <button onClick={addSymbol} className="text-xxs text-accent hover:text-accent-hover">+ Add</button>
      </div>
      <div className="space-y-px">
        {watchlist.map(ticker => {
          const item = prices[ticker]
          const isActive = ticker === currentTicker
          const isPositive = (item?.changePercent ?? 0) >= 0
          return (
            <button
              key={ticker}
              onClick={() => onSelect(ticker)}
              className={`w-full flex items-center justify-between px-2 py-1.5 rounded text-left transition-colors group ${
                isActive ? 'bg-accent/10' : 'hover:bg-surface-overlay'
              }`}
            >
              <span className={`text-xs font-medium ${isActive ? 'text-accent' : 'text-txt'}`}>{ticker}</span>
              {item?.price ? (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-txt-dim tabular-nums">${item.price.toFixed(2)}</span>
                  <span className={`text-xxs tabular-nums ${isPositive ? 'text-up' : 'text-down'}`}>
                    {isPositive ? '+' : ''}{item.changePercent?.toFixed(2)}%
                  </span>
                </div>
              ) : (
                <span className="text-xxs text-txt-muted">{loading ? '—' : '—'}</span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
