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
    atr: { value: number; percent: number; signal: string }
    stochastic: { k: number; d: number; signal: string }
    williams_r: { value: number; signal: string }
  }
  recommendation: string
}

export default function SignalsPanel({ ticker }: SignalsPanelProps) {
  const [signals, setSignals] = useState<Signals | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { fetchSignals() }, [ticker])

  const fetchSignals = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/stocks/${ticker}/signals`)
      const data = await res.json()
      setSignals(data)
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const getSignalColor = (signal: string) => {
    if (signal.includes('BUY') || signal.includes('OVERSOLD') || signal.includes('BULLISH')) return 'text-up'
    if (signal.includes('SELL') || signal.includes('OVERBOUGHT') || signal.includes('BEARISH')) return 'text-down'
    return 'text-text-muted'
  }

  const getSignalBg = (signal: string) => {
    if (signal.includes('BUY') || signal.includes('OVERSOLD') || signal.includes('BULLISH')) return 'bg-up/10'
    if (signal.includes('SELL') || signal.includes('OVERBOUGHT') || signal.includes('BEARISH')) return 'bg-down/10'
    return 'bg-surface-3'
  }

  return (
    <div className="bg-surface-1 border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xxs font-medium text-text-muted uppercase tracking-wider">Technical Signals</span>
        <button onClick={fetchSignals} disabled={loading}
          className="text-xxs text-accent hover:text-accent-hover disabled:text-text-muted">
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {loading ? (
        <div className="text-text-muted text-xs text-center py-8">Loading...</div>
      ) : signals ? (
        <div className="space-y-3">
          {/* Recommendation */}
          <div className={`text-center py-2.5 rounded ${getSignalBg(signals.recommendation)}`}>
            <p className={`text-sm font-semibold ${getSignalColor(signals.recommendation)}`}>
              {signals.recommendation}
            </p>
          </div>

          {/* Indicators */}
          {[
            { name: 'RSI (14)', value: signals.indicators.rsi.value.toFixed(1), signal: signals.indicators.rsi.signal },
            { name: 'MACD', value: signals.indicators.macd.value.toFixed(4), signal: signals.indicators.macd.signal },
            { name: 'Stochastic', value: `%K ${signals.indicators.stochastic.k.toFixed(0)} / %D ${signals.indicators.stochastic.d.toFixed(0)}`, signal: signals.indicators.stochastic.signal },
            { name: 'Williams %R', value: signals.indicators.williams_r.value.toFixed(1), signal: signals.indicators.williams_r.signal },
            { name: 'ATR', value: `${signals.indicators.atr.percent.toFixed(1)}%`, signal: signals.indicators.atr.signal },
            { name: 'Bollinger', value: signals.indicators.bollinger.signal, signal: signals.indicators.bollinger.signal },
          ].map((ind, i) => (
            <div key={i} className="flex items-center justify-between py-1.5 border-b border-border last:border-0">
              <span className="text-xs text-text-muted">{ind.name}</span>
              <div className="text-right">
                <span className="text-xs text-text-secondary tabular-nums mr-2">{ind.value}</span>
                <span className={`text-xxs font-medium ${getSignalColor(ind.signal)}`}>
                  {ind.signal.split(' ')[0]}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-text-muted text-xs text-center py-8">No data</div>
      )}
    </div>
  )
}
