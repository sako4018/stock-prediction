import { useState, useEffect } from 'react'

interface CompanyInfoProps {
  ticker: string
}

interface CompanyData {
  price: {
    ticker: string
    current_price: number
    previous_close: number
    change: number
    change_percent: number
    currency: string
  }
  company: {
    name: string
    sector: string
    industry: string
    country: string
    market_cap: number
    employees: number
  }
}

export default function CompanyInfo({ ticker }: CompanyInfoProps) {
  const [data, setData] = useState<CompanyData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchInfo()
  }, [ticker])

  const fetchInfo = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/stocks/${ticker}`)
      const json = await res.json()
      setData(json)
    } catch (err) {
      console.error('Failed to fetch stock info:', err)
    }
    setLoading(false)
  }

  const formatMarketCap = (cap: number) => {
    if (cap >= 1e12) return `$${(cap / 1e12).toFixed(2)}T`
    if (cap >= 1e9) return `$${(cap / 1e9).toFixed(2)}B`
    if (cap >= 1e6) return `$${(cap / 1e6).toFixed(2)}M`
    return `$${cap.toLocaleString()}`
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6 card-hover">
      {loading ? (
        <div className="text-gray-500 text-center py-8">Loading...</div>
      ) : data ? (
        <div className="space-y-4">
          {/* Ticker & Name */}
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-bold">{data.price.ticker}</h2>
              <span className="px-2 py-0.5 bg-dark-bg rounded text-xs text-gray-400">
                {data.company.sector}
              </span>
            </div>
            <p className="text-sm text-gray-400 truncate">{data.company.name}</p>
          </div>

          {/* Price */}
          <div>
            <p className="text-3xl font-bold">${data.price.current_price.toFixed(2)}</p>
            <p className={`text-sm font-medium ${
              data.price.change >= 0 ? 'text-stock-green' : 'text-stock-red'
            }`}>
              {data.price.change >= 0 ? '+' : ''}{data.price.change.toFixed(2)} ({data.price.change_percent.toFixed(2)}%)
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="bg-dark-bg rounded-lg p-3">
              <p className="text-xs text-gray-500">Market Cap</p>
              <p className="text-sm font-medium">{formatMarketCap(data.company.market_cap)}</p>
            </div>
            <div className="bg-dark-bg rounded-lg p-3">
              <p className="text-xs text-gray-500">Prev Close</p>
              <p className="text-sm font-medium">${data.price.previous_close.toFixed(2)}</p>
            </div>
            <div className="bg-dark-bg rounded-lg p-3">
              <p className="text-xs text-gray-500">Industry</p>
              <p className="text-sm font-medium truncate">{data.company.industry}</p>
            </div>
            <div className="bg-dark-bg rounded-lg p-3">
              <p className="text-xs text-gray-500">Employees</p>
              <p className="text-sm font-medium">{data.company.employees?.toLocaleString() || 'N/A'}</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-gray-500 text-center py-8">No data available</div>
      )}
    </div>
  )
}
