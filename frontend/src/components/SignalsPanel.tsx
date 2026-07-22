import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

function Bar({ value, min, max, label }: { value: number; min: number; max: number; label: string }) {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100))
  const filled = Math.round(pct / 5)
  const empty = 20 - filled
  const color = value < 30 ? 'var(--green)' : value > 70 ? 'var(--red)' : 'var(--amber)'
  return (
    <div className="flex items-center gap-2 text-xs py-0.5">
      <span className="w-24 shrink-0" style={{ color: 'var(--dim)' }}>{label}</span>
      <span style={{ color }}>{'█'.repeat(filled)}{'░'.repeat(empty)}</span>
      <span className="w-10 text-right font-bold" style={{ color }}>{value.toFixed(1)}</span>
    </div>
  )
}

export default function SignalsPanel({ ticker }: { ticker: string }) {
  const [data, setData] = useState<any>(null)

  useEffect(() => { fetchData() }, [ticker])

  const fetchData = async () => {
    try {
      setData(await cachedFetch(`/api/stocks/${ticker}/signals`))
    } catch {}
  }

  const signalColor = (s: string) => {
    if (s?.includes('BUY') || s?.includes('OVERSOLD') || s?.includes('BULLISH')) return 'var(--green)'
    if (s?.includes('SELL') || s?.includes('OVERBOUGHT') || s?.includes('BEARISH')) return 'var(--red)'
    return 'var(--dim)'
  }

  return (
    <div className="panel">
      <div className="panel-title">TECHNICAL SIGNALS</div>
      {data ? (
        <div className="space-y-1">
          {/* Recommendation */}
          <div className="text-center py-2 mb-2" style={{ borderBottom: '1px solid var(--border)' }}>
            <span className="text-sm font-bold" style={{ color: signalColor(data.recommendation) }}>
              {data.recommendation}
            </span>
          </div>

          {/* Oscillators as bars */}
          <Bar value={data.indicators.rsi.value} min={0} max={100} label="RSI" />
          <Bar value={data.indicators.stochastic.k} min={0} max={100} label="STOCH %K" />
          <Bar value={Math.abs(data.indicators.williams_r.value)} min={0} max={100} label="W%R" />

          {/* Signal summary */}
          <div className="pt-2 mt-1" style={{ borderTop: '1px solid var(--border)' }}>
            {['macd', 'bollinger', 'atr'].map(k => {
              const s = data.indicators[k]
              const label = k.toUpperCase()
              return (
                <div key={k} className="flex items-center justify-between text-xs py-0.5">
                  <span style={{ color: 'var(--dim)' }}>{label}</span>
                  <span style={{ color: signalColor(s.signal) }}>{s.signal?.split(' ')[0]}</span>
                </div>
              )
            })}
          </div>
        </div>
      ) : (
        <div style={{ color: 'var(--dim)' }}>Loading...</div>
      )}
    </div>
  )
}
