import { useState, useEffect, useMemo } from 'react'
import { useTheme } from '../ThemeContext'

interface StockChartProps {
  ticker: string
}

interface ChartData {
  Date: string
  Open: number
  High: number
  Low: number
  Close: number
  Volume: number
  SMA_20: number
  SMA_50: number
  BB_Upper: number
  BB_Lower: number
  RSI: number
  MACD: number
  MACD_Signal: number
}

// Custom Candlestick Component
function Candlestick({ x, y, width, height, open, close, isPositive, wickHeight, wickY }: any) {
  const color = isPositive ? '#00C853' : '#FF1744'
  return (
    <g>
      {/* Wick (high-low line) */}
      <line
        x1={x + width / 2}
        y1={wickY}
        x2={x + width / 2}
        y2={wickY + wickHeight}
        stroke={color}
        strokeWidth={1}
      />
      {/* Body (open-close) */}
      <rect
        x={x}
        y={y}
        width={width}
        height={Math.max(height, 1)}
        fill={isPositive ? color : color}
        stroke={color}
        strokeWidth={0.5}
      />
    </g>
  )
}

export default function StockChart({ ticker }: StockChartProps) {
  const [data, setData] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('1y')
  const [chartType, setChartType] = useState<'candle' | 'area'>('candle')
  const [showIndicators, setShowIndicators] = useState({ sma: true, bb: false, volume: true })
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  useEffect(() => {
    fetchHistory()
  }, [ticker, period])

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/stocks/${ticker}/history?period=${period}`)
      const json = await res.json()
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

  // Calculate chart dimensions
  const chartData = useMemo(() => {
    if (!data.length) return { candles: [], yMin: 0, yMax: 100, volumeMax: 100 }
    const prices = data.flatMap(d => [d.High, d.Low])
    const yMin = Math.min(...prices) * 0.99
    const yMax = Math.max(...prices) * 1.01
    const volumeMax = Math.max(...data.map(d => d.Volume))
    return { candles: data, yMin, yMax, volumeMax }
  }, [data])

  const periods = ['1mo', '3mo', '6mo', '1y', '2y', '5y']

  if (loading) {
    return (
      <div className={`rounded-xl border p-6 h-96 flex items-center justify-center ${
        isDark ? 'bg-dark-card border-dark-border' : 'bg-white border-gray-200'
      }`}>
        <div className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Loading chart...</div>
      </div>
    )
  }

  const chartWidth = 900
  const chartHeight = 400
  const padding = { top: 20, right: 60, bottom: 30, left: 10 }
  const innerWidth = chartWidth - padding.left - padding.right
  const innerHeight = chartHeight - padding.top - padding.bottom

  const { yMin, yMax, volumeMax } = chartData
  const candleWidth = Math.max(2, (innerWidth / data.length) - 1)

  const scaleY = (price: number) => {
    return padding.top + innerHeight - ((price - yMin) / (yMax - yMin)) * innerHeight
  }

  const scaleX = (index: number) => {
    return padding.left + (index / data.length) * innerWidth
  }

  return (
    <div className={`rounded-xl border p-6 ${
      isDark ? 'bg-dark-card border-dark-border' : 'bg-white border-gray-200'
    }`}>
      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {periods.map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                period === p
                  ? 'bg-stock-blue text-white'
                  : isDark ? 'bg-dark-bg text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          {/* Chart Type Toggle */}
          <div className={`flex rounded-lg overflow-hidden border ${isDark ? 'border-dark-border' : 'border-gray-200'}`}>
            <button
              onClick={() => setChartType('candle')}
              className={`px-3 py-1 text-xs font-medium transition-colors ${
                chartType === 'candle'
                  ? 'bg-stock-blue text-white'
                  : isDark ? 'bg-dark-bg text-gray-400' : 'bg-gray-100 text-gray-600'
              }`}
            >
              🕯️ Candle
            </button>
            <button
              onClick={() => setChartType('area')}
              className={`px-3 py-1 text-xs font-medium transition-colors ${
                chartType === 'area'
                  ? 'bg-stock-blue text-white'
                  : isDark ? 'bg-dark-bg text-gray-400' : 'bg-gray-100 text-gray-600'
              }`}
            >
              📈 Area
            </button>
          </div>
          {/* Indicator Toggles */}
          <label className="flex items-center gap-1 cursor-pointer">
            <input type="checkbox" checked={showIndicators.sma}
              onChange={(e) => setShowIndicators({...showIndicators, sma: e.target.checked})}
              className="rounded" />
            <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>SMA</span>
          </label>
          <label className="flex items-center gap-1 cursor-pointer">
            <input type="checkbox" checked={showIndicators.bb}
              onChange={(e) => setShowIndicators({...showIndicators, bb: e.target.checked})}
              className="rounded" />
            <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>BB</span>
          </label>
        </div>
      </div>

      {/* Main Chart */}
      <div className="overflow-x-auto">
        <svg width={chartWidth} height={chartHeight} className="select-none">
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2979FF" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#2979FF" stopOpacity={0} />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const y = padding.top + innerHeight * (1 - pct)
            const price = yMin + (yMax - yMin) * pct
            return (
              <g key={i}>
                <line x1={padding.left} y1={y} x2={chartWidth - padding.right} y2={y}
                  stroke={isDark ? '#1e1e2e' : '#e5e7eb'} strokeWidth={0.5} />
                <text x={chartWidth - padding.right + 5} y={y + 4}
                  fill={isDark ? '#666' : '#999'} fontSize={10}>
                  ${price.toFixed(2)}
                </text>
              </g>
            )
          })}

          {/* SMA Lines */}
          {showIndicators.sma && data.length > 0 && (
            <>
              <polyline
                points={data.map((d, i) => `${scaleX(i) + candleWidth/2},${scaleY(d.SMA_20)}`).join(' ')}
                fill="none" stroke="#FFC107" strokeWidth={1} opacity={0.7}
              />
              <polyline
                points={data.map((d, i) => `${scaleX(i) + candleWidth/2},${scaleY(d.SMA_50)}`).join(' ')}
                fill="none" stroke="#FF9800" strokeWidth={1} opacity={0.7}
              />
            </>
          )}

          {/* Bollinger Bands */}
          {showIndicators.bb && data.length > 0 && (
            <>
              <polyline
                points={data.map((d, i) => `${scaleX(i) + candleWidth/2},${scaleY(d.BB_Upper)}`).join(' ')}
                fill="none" stroke="#9C27B0" strokeWidth={1} strokeDasharray="4 2" opacity={0.6}
              />
              <polyline
                points={data.map((d, i) => `${scaleX(i) + candleWidth/2},${scaleY(d.BB_Lower)}`).join(' ')}
                fill="none" stroke="#9C27B0" strokeWidth={1} strokeDasharray="4 2" opacity={0.6}
              />
            </>
          )}

          {/* Candles or Area */}
          {chartType === 'candle' ? (
            data.map((d, i) => {
              const x = scaleX(i)
              const isPositive = d.Close >= d.Open
              const bodyTop = scaleY(Math.max(d.Open, d.Close))
              const bodyBottom = scaleY(Math.min(d.Open, d.Close))
              const bodyHeight = Math.max(bodyBottom - bodyTop, 1)
              const wickTop = scaleY(d.High)
              const wickBottom = scaleY(d.Low)

              return (
                <Candlestick
                  key={i}
                  x={x}
                  y={bodyTop}
                  width={candleWidth}
                  height={bodyHeight}
                  open={d.Open}
                  close={d.Close}
                  isPositive={isPositive}
                  wickHeight={wickBottom - wickTop}
                  wickY={wickTop}
                />
              )
            })
          ) : (
            <>
              <polygon
                points={[
                  ...data.map((d, i) => `${scaleX(i) + candleWidth/2},${scaleY(d.Close)}`),
                  `${scaleX(data.length - 1) + candleWidth/2},${padding.top + innerHeight}`,
                  `${scaleX(0) + candleWidth/2},${padding.top + innerHeight}`
                ].join(' ')}
                fill="url(#areaGradient)"
              />
              <polyline
                points={data.map((d, i) => `${scaleX(i) + candleWidth/2},${scaleY(d.Close)}`).join(' ')}
                fill="none" stroke="#2979FF" strokeWidth={2}
              />
            </>
          )}

          {/* Volume bars at bottom */}
          {showIndicators.volume && (
            <g opacity={0.3}>
              {data.map((d, i) => {
                const x = scaleX(i)
                const volHeight = (d.Volume / volumeMax) * (innerHeight * 0.15)
                const isPositive = d.Close >= d.Open
                return (
                  <rect key={`vol-${i}`}
                    x={x} y={padding.top + innerHeight - volHeight}
                    width={candleWidth} height={volHeight}
                    fill={isPositive ? '#00C853' : '#FF1744'}
                  />
                )
              })}
            </g>
          )}
        </svg>
      </div>

      {/* RSI Chart */}
      <div className="mt-4">
        <p className={`text-xs mb-1 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>RSI (14)</p>
        <svg width={chartWidth} height={80}>
          {/* RSI grid */}
          {[30, 50, 70].map(level => {
            const y = 10 + (1 - (level / 100)) * 60
            return (
              <g key={level}>
                <line x1={padding.left} y1={y} x2={chartWidth - padding.right} y2={y}
                  stroke={isDark ? '#1e1e2e' : '#e5e7eb'} strokeWidth={0.5} strokeDasharray="3 3" />
                <text x={chartWidth - padding.right + 5} y={y + 3}
                  fill={isDark ? '#666' : '#999'} fontSize={9}>
                  {level}
                </text>
              </g>
            )
          })}

          {/* RSI line */}
          <polyline
            points={data.map((d, i) => {
              const x = scaleX(i) + candleWidth / 2
              const y = 10 + (1 - ((d.RSI || 50) / 100)) * 60
              return `${x},${y}`
            }).join(' ')}
            fill="none" stroke="#E91E63" strokeWidth={1.5}
          />

          {/* Overbought/Oversold zones */}
          <rect x={padding.left} y={10} width={innerWidth} height={18}
            fill="#FF1744" opacity={0.05} />
          <rect x={padding.left} y={52} width={innerWidth} height={18}
            fill="#00C853" opacity={0.05} />
        </svg>
      </div>
    </div>
  )
}
