import { useState, useEffect } from 'react'
import { useTheme } from '../ThemeContext'

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
  const { theme } = useTheme()
  const isDark = theme === 'dark'

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

  const addToWatchlist = () => {
    const input = prompt('Enter ticker symbol:')
    if (input && !watchlist.includes(input.toUpperCase())) {
      setWatchlist([...watchlist, input.toUpperCase()])
    }
  }

  const removeFromWatchlist = (ticker: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setWatchlist(watchlist.filter(t => t !== ticker))
  }

  return (
    <div className={`rounded-xl border p-4 ${
      isDark ? 'bg-dark-card border-dark-border' : 'bg-white border-gray-200'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm">📋 Watchlist</h3>
        <button
          onClick={addToWatchlist}
          className="text-stock-blue text-xs hover:underline"
        >
          + Add
        </button>
      </div>

      <div className="space-y-1">
        {watchlist.map(ticker => {
          const item = prices[ticker]
          const isActive = ticker === currentTicker
          const isPositive = (item?.changePercent ?? 0) >= 0

          return (
            <button
              key={ticker}
              onClick={() => onSelect(ticker)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors group ${
                isActive
                  ? isDark ? 'bg-stock-blue/20' : 'bg-blue-50'
                  : isDark ? 'hover:bg-dark-bg' : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className={`font-semibold ${isActive ? 'text-stock-blue' : ''}`}>{ticker}</span>
              </div>
              <div className="flex items-center gap-2">
                {item?.price ? (
                  <>
                    <span className={`font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      ${item.price.toFixed(2)}
                    </span>
                    <span className={`text-xs ${isPositive ? 'text-stock-green' : 'text-stock-red'}`}>
                      {isPositive ? '+' : ''}{item.changePercent?.toFixed(2)}%
                    </span>
                  </>
                ) : (
                  <span className={`text-xs ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                    {loading ? '...' : '—'}
                  </span>
                )}
                <button
                  onClick={(e) => removeFromWatchlist(ticker, e)}
                  className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-stock-red text-xs transition-opacity"
                >
                  ✕
                </button>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
