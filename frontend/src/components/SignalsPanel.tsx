import { useState, useEffect } from 'react'
import FadeIn from './FadeIn'

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

// Semi-circle gauge component
function Gauge({ value, min, max, label, color }: { value: number; min: number; max: number; label: string; color: string }) {
  const pct = Math.max(0, Math.min(1, (value - min) / (max - min)))

  const size = 90
  const cx = size / 2
  const cy = size / 2 + 5
  const r = 35

  // Background arc (full semi-circle from left to right)
  const bgStart = { x: cx - r, y: cy }
  const bgEnd = { x: cx + r, y: cy }

  // Value arc
  const startAngle = Math.PI
  const endAngle = Math.PI * (1 - pct)
  const valStart = { x: cx + r * Math.cos(startAngle), y: cy + r * Math.sin(startAngle) }
  const valEnd = { x: cx + r * Math.cos(endAngle), y: cy + r * Math.sin(endAngle) }
  const largeArc = pct > 0.5 ? 1 : 0

  // Needle position
  const needleAngle = Math.PI * (1 - pct)
  const nx = cx + (r - 5) * Math.cos(needleAngle)
  const ny = cy + (r - 5) * Math.sin(needleAngle)

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size * 0.65} viewBox={`0 0 ${size} ${size * 0.65}`}>
        {/* Background arc */}
        <path
          d={`M ${bgStart.x} ${bgStart.y} A ${r} ${r} 0 0 1 ${bgEnd.x} ${bgEnd.y}`}
          fill="none" stroke="var(--gauge-bg)" strokeWidth="7" strokeLinecap="round"
        />
        {/* Value arc */}
        {pct > 0.005 && (
          <path
            d={`M ${valStart.x} ${valStart.y} A ${r} ${r} 0 ${largeArc} 1 ${valEnd.x} ${valEnd.y}`}
            fill="none" stroke={color} strokeWidth="7" strokeLinecap="round"
          />
        )}
        {/* Needle */}
        <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={color} strokeWidth="2" strokeLinecap="round" />
        <circle cx={cx} cy={cy} r="3" fill={color} />
        {/* Min/Max labels */}
        <text x={cx - r - 2} y={cy + 12} fill="var(--gauge-label)" fontSize="8" textAnchor="middle">{min}</text>
        <text x={cx + r + 2} y={cy + 12} fill="var(--gauge-label)" fontSize="8" textAnchor="middle">{max}</text>
      </svg>
      <span className="text-xxs text-txt-dim mt-1">{label}</span>
      <span className="text-sm font-bold tabular-nums text-txt">{value.toFixed(1)}</span>
    </div>
  )
}

// Horizontal bar gauge
function BarGauge({ value, min, max, label, zones }: {
  value: number; min: number; max: number; label: string;
  zones?: { from: number; to: number; color: string }[]
}) {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100))

  const defaultZones = zones || [
    { from: 0, to: 30, color: '#69f0ae' },
    { from: 30, to: 70, color: '#7c4dff' },
    { from: 70, to: 100, color: '#ff6e40' },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xxs text-txt-dim">{label}</span>
        <span className="text-xxs font-bold tabular-nums text-txt">{value.toFixed(1)}</span>
      </div>
      <div className="h-2 bg-surface-overlay rounded-full overflow-hidden relative">
        {defaultZones.map((z, i) => (
          <div key={i} className="absolute top-0 h-full opacity-20"
            style={{ left: `${z.from}%`, width: `${z.to - z.from}%`, background: z.color }} />
        ))}
        <div className="absolute top-0 h-full w-0.5 bg-txt rounded-full transition-all duration-500"
          style={{ left: `${pct}%` }} />
      </div>
    </div>
  )
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
    return 'text-txt-sec'
  }

  const getGaugeColor = (value: number, low: number, high: number) => {
    if (value < low) return '#69f0ae'
    if (value > high) return '#ff6e40'
    return '#7c4dff'
  }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="section-header" style={{ border: 'none', paddingBottom: 0, marginBottom: 0 }}>Technical Signals</span>
        <button onClick={fetchSignals} disabled={loading}
          className="text-xxs text-accent hover:text-accent-hover disabled:text-txt-dim">
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="h-12 skeleton" />)}
        </div>
      ) : signals ? (
        <FadeIn>
          <div className="space-y-4">
            {/* Recommendation */}
            <div className={`text-center py-3 rounded-lg border ${
              signals.recommendation.includes('BUY') ? 'border-up/30 bg-up/5' :
              signals.recommendation.includes('SELL') ? 'border-down/30 bg-down/5' :
              'border-line bg-surface-elevated'
            }`}>
              <p className={`text-base font-bold ${getSignalColor(signals.recommendation)}`}>
                {signals.recommendation}
              </p>
            </div>

            {/* Gauge Row: RSI + Stochastic + Williams %R */}
            <div className="bg-surface-elevated rounded-lg p-4">
              <p className="text-xxs text-txt-dim uppercase tracking-wider mb-3">Oscillators</p>
              <div className="flex justify-around">
                <Gauge
                  value={signals.indicators.rsi.value}
                  min={0} max={100}
                  label="RSI"
                  color={getGaugeColor(signals.indicators.rsi.value, 30, 70)}
                />
                <Gauge
                  value={signals.indicators.stochastic.k}
                  min={0} max={100}
                  label="Stoch %K"
                  color={getGaugeColor(signals.indicators.stochastic.k, 20, 80)}
                />
                <Gauge
                  value={Math.abs(signals.indicators.williams_r.value)}
                  min={0} max={100}
                  label="W%R"
                  color={getGaugeColor(Math.abs(signals.indicators.williams_r.value), 20, 80)}
                />
              </div>
            </div>

            {/* Bar Gauges */}
            <div className="bg-surface-elevated rounded-lg p-4 space-y-3">
              <p className="text-xxs text-txt-dim uppercase tracking-wider">Indicators</p>
              <BarGauge
                value={signals.indicators.rsi.value}
                min={0} max={100}
                label="RSI (14)"
              />
              <BarGauge
                value={signals.indicators.stochastic.k}
                min={0} max={100}
                label={`Stochastic %K: ${signals.indicators.stochastic.k.toFixed(0)} / %D: ${signals.indicators.stochastic.d.toFixed(0)}`}
              />
              <BarGauge
                value={signals.indicators.atr.percent}
                min={0} max={5}
                label={`ATR Volatility: ${signals.indicators.atr.percent.toFixed(1)}%`}
                zones={[
                  { from: 0, to: 20, color: '#69f0ae' },
                  { from: 20, to: 60, color: '#7c4dff' },
                  { from: 60, to: 100, color: '#ff6e40' },
                ]}
              />
            </div>

            {/* Quick Signal Summary */}
            <div className="grid grid-cols-3 gap-2">
              {[
                { name: 'MACD', signal: signals.indicators.macd.signal },
                { name: 'Bollinger', signal: signals.indicators.bollinger.signal },
                { name: 'ATR', signal: signals.indicators.atr.signal },
              ].map((item, i) => (
                <div key={i} className="text-center py-2 rounded bg-surface-elevated">
                  <p className="text-xxs text-txt-dim">{item.name}</p>
                  <p className={`text-xxs font-bold ${getSignalColor(item.signal)}`}>
                    {item.signal.split(' ')[0]}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </FadeIn>
      ) : (
        <div className="text-txt-dim text-xs text-center py-8">No data</div>
      )}
    </div>
  )
}
