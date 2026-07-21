import { useState, useEffect } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend
} from 'recharts'

interface StockChartProps {
  ticker: string
}

interface ChartData {
  Date: string
  Close: number
  SMA_20: number
  SMA_50: number
  RSI: number
  MACD: number
  MACD_Signal: number
}

export default function StockChart({ ticker }: StockChartProps) {
  const [data, setData] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('1y')
  const [showIndicators, setShowIndicators] = useState({ sma: true, bb: false })

  useEffect(() => {
    fetchHistory()
  }, [ticker, period])

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/stocks/${ticker}/history?period=${period}`)
      const json = await res.json()
      // Format dates for display
      const formatted = json.data.map((d: any) => ({
        ...d,
        Date: d.Date.split('T')[0]
      }))
      setData(formatted)
    } catch (err) {
      console.error('Failed to fetch history:', err)
    }
    setLoading(false)
  }

  const periods = ['1mo', '3mo', '6mo', '1y', '2y', '5y']

  if (loading) {
    return (
      <div className="bg-dark-card border border-dark-border rounded-xl p-6 h-96 flex items-center justify-center">
        <div className="text-gray-500">Loading chart data...</div>
      </div>
    )
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6">
      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          {periods.map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                period === p
                  ? 'bg-stock-blue text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
        <div className="flex gap-4 text-sm">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showIndicators.sma}
              onChange={(e) => setShowIndicators({...showIndicators, sma: e.target.checked})}
              className="rounded"
            />
            <span className="text-gray-400">SMA</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showIndicators.bb}
              onChange={(e) => setShowIndicators({...showIndicators, bb: e.target.checked})}
              className="rounded"
            />
            <span className="text-gray-400">Bollinger</span>
          </label>
        </div>
      </div>

      {/* Price Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2979FF" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#2979FF" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
            <XAxis
              dataKey="Date"
              stroke="#666"
              tick={{ fontSize: 12 }}
              tickFormatter={(val) => val.slice(5)} // Show MM-DD
            />
            <YAxis
              stroke="#666"
              tick={{ fontSize: 12 }}
              domain={['auto', 'auto']}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#12121a',
                border: '1px solid #1e1e2e',
                borderRadius: '8px'
              }}
            />
            <Area
              type="monotone"
              dataKey="Close"
              stroke="#2979FF"
              fillOpacity={1}
              fill="url(#colorClose)"
              strokeWidth={2}
            />
            {showIndicators.sma && (
              <>
                <Line type="monotone" dataKey="SMA_20" stroke="#FFC107" dot={false} strokeWidth={1} />
                <Line type="monotone" dataKey="SMA_50" stroke="#FF9800" dot={false} strokeWidth={1} />
              </>
            )}
            {showIndicators.bb && (
              <>
                <Line type="monotone" dataKey="BB_Upper" stroke="#9C27B0" dot={false} strokeWidth={1} strokeDasharray="5 5" />
                <Line type="monotone" dataKey="BB_Lower" stroke="#9C27B0" dot={false} strokeWidth={1} strokeDasharray="5 5" />
              </>
            )}
            <Legend />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* RSI Chart */}
      <div className="h-32 mt-4">
        <p className="text-xs text-gray-500 mb-1">RSI (14)</p>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
            <XAxis dataKey="Date" stroke="#666" tick={{ fontSize: 10 }} tickFormatter={(val) => val.slice(5)} />
            <YAxis stroke="#666" tick={{ fontSize: 10 }} domain={[0, 100]} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#12121a',
                border: '1px solid #1e1e2e',
                borderRadius: '8px'
              }}
            />
            <Line type="monotone" dataKey="RSI" stroke="#E91E63" dot={false} strokeWidth={1.5} />
            {/* Overbought/Oversold lines */}
            <Line type="monotone" dataKey={() => 70} stroke="#FF5252" dot={false} strokeWidth={1} strokeDasharray="3 3" />
            <Line type="monotone" dataKey={() => 30} stroke="#4CAF50" dot={false} strokeWidth={1} strokeDasharray="3 3" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
