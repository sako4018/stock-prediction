import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

function BarGauge({ value, min, max, label }: { value: number; min: number; max: number; label: string }) {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100))
  const color = value < 30 ? 'rgb(var(--color-up))' : value > 70 ? 'rgb(var(--color-down))' : 'rgb(var(--color-accent))'
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xxs" style={{ color: 'rgb(var(--color-txt-dim))' }}>{label}</span>
        <span className="text-xxs font-bold tabular-nums" style={{ color: 'rgb(var(--color-txt))' }}>{value.toFixed(1)}</span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgb(var(--color-surface-overlay))' }}>
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  )
}

export default function SignalsPanel({ ticker }: { ticker: string }) {
  const [data, setData] = useState<any>(null)

  useEffect(() => { fetchData() }, [ticker])

  const fetchData = async () => {
    try { setData(await cachedFetch(`/api/stocks/${ticker}/signals`)) } catch {}
  }

  const signalColor = (s: string) => {
    if (s?.includes('BUY') || s?.includes('OVERSOLD') || s?.includes('BULLISH')) return 'text-up'
    if (s?.includes('SELL') || s?.includes('OVERBOUGHT') || s?.includes('BEARISH')) return 'text-down'
    return 'text-txt-dim'
  }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="section-header" style={{ border: 'none', paddingBottom: 0, marginBottom: 0 }}>Technical Signals</span>
        <button onClick={fetchData} disabled={!data} className="text-xxs" style={{ color: 'rgb(var(--color-accent))' }}>
          {data ? 'Refresh' : '...'}
        </button>
      </div>
      {data ? (
        <div className="space-y-3 animate-fade-in">
          <div className="text-center py-2 rounded-lg" style={{
            background: 'rgb(var(--color-surface))',
            border: '1px solid rgb(var(--color-line))',
          }}>
            <span className={`text-sm font-bold ${signalColor(data.recommendation)}`}>{data.recommendation}</span>
          </div>
          <BarGauge value={data.indicators.rsi.value} min={0} max={100} label="RSI (14)" />
          <BarGauge value={data.indicators.stochastic.k} min={0} max={100} label="Stochastic %K" />
          {['macd', 'bollinger', 'atr'].map(k => (
            <div key={k} className="flex items-center justify-between text-xxs py-1" style={{ borderTop: '1px solid rgb(var(--color-line) / 0.3)' }}>
              <span style={{ color: 'rgb(var(--color-txt-dim))' }}>{k.toUpperCase()}</span>
              <span className={`font-medium ${signalColor(data.indicators[k]?.signal)}`}>{data.indicators[k]?.signal?.split(' ')[0]}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="h-12 skeleton" />)}</div>
      )}
    </div>
  )
}
