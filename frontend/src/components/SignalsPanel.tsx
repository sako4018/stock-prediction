import { useState, useEffect } from 'react'

interface SignalsPanelProps {
  ticker: string
}

interface Signals {
  ticker: string
  current_price: number
  indicators: {
    rsi: { value: number; signal: string }
    macd: { value: number; signal: string }
    bollinger: { upper: number; lower: number; signal: string }
  }
  recommendation: string
}

export default function SignalsPanel({ ticker }: SignalsPanelProps) {
  const [signals, setSignals] = useState<Signals | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSignals()
  }, [ticker])

  const fetchSignals = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/stocks/${ticker}/signals`)
      const data = await res.json()
      setSignals(data)
    } catch (err) {
      console.error('Failed to fetch signals:', err)
    }
    setLoading(false)
  }

  const getSignalColor = (signal: string) => {
    if (signal.includes('BUY') || signal.includes('OVERSOLD')) return 'text-stock-green'
    if (signal.includes('SELL') || signal.includes('OVERBOUGHT')) return 'text-stock-red'
    return 'text-gray-400'
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6 card-hover">
      <h3 className="text-lg font-semibold mb-4">📡 Technical Signals</h3>

      {loading ? (
        <div className="text-gray-500 text-center py-8">Loading signals...</div>
      ) : signals ? (
        <div className="space-y-4">
          {/* Overall Recommendation */}
          <div className={`text-center py-3 rounded-lg ${
            signals.recommendation === 'BUY' ? 'bg-green-500/20' :
            signals.recommendation === 'SELL' ? 'bg-red-500/20' :
            'bg-gray-500/20'
          }`}>
            <p className="text-sm text-gray-400">Overall</p>
            <p className={`text-xl font-bold ${
              signals.recommendation === 'BUY' ? 'text-stock-green' :
              signals.recommendation === 'SELL' ? 'text-stock-red' :
              'text-gray-400'
            }`}>
              {signals.recommendation}
            </p>
          </div>

          {/* RSI */}
          <div className="bg-dark-bg rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">RSI (14)</span>
              <span className={`text-sm font-medium ${getSignalColor(signals.indicators.rsi.signal)}`}>
                {signals.indicators.rsi.value.toFixed(1)}
              </span>
            </div>
            <p className={`text-xs mt-1 ${getSignalColor(signals.indicators.rsi.signal)}`}>
              {signals.indicators.rsi.signal}
            </p>
          </div>

          {/* MACD */}
          <div className="bg-dark-bg rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">MACD</span>
              <span className={`text-sm font-medium ${getSignalColor(signals.indicators.macd.signal)}`}>
                {signals.indicators.macd.value.toFixed(4)}
              </span>
            </div>
            <p className={`text-xs mt-1 ${getSignalColor(signals.indicators.macd.signal)}`}>
              {signals.indicators.macd.signal}
            </p>
          </div>

          {/* Bollinger Bands */}
          <div className="bg-dark-bg rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Bollinger</span>
              <span className={`text-sm font-medium ${getSignalColor(signals.indicators.bollinger.signal)}`}>
                {signals.indicators.bollinger.signal}
              </span>
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>L: ${signals.indicators.bollinger.lower.toFixed(2)}</span>
              <span>U: ${signals.indicators.bollinger.upper.toFixed(2)}</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-gray-500 text-center py-8">No signals available</div>
      )}
    </div>
  )
}
