import { useState, useEffect, useMemo } from 'react'
import { useTheme } from '../ThemeContext'
import { cachedFetch } from '../cache'

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

export default function StockChart({ ticker }: StockChartProps) {
  const { theme } = useTheme()
  const [data, setData] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('1y')
  const [chartType, setChartType] = useState<'candle' | 'area'>('candle')
  const [showIndicators, setShowIndicators] = useState({ sma: true, bb: false, volume: true })
  const [hoverData, setHoverData] = useState<any>(null)

  // Read chart colors from CSS variables
  const c = useMemo(() => {
    const s = getComputedStyle(document.documentElement)
    return {
      grid: s.getPropertyValue('--chart-grid').trim(),
      label: s.getPropertyValue('--chart-label').trim(),
      sma20: s.getPropertyValue('--chart-sma20').trim(),
      sma50: s.getPropertyValue('--chart-sma50').trim(),
      bb: s.getPropertyValue('--chart-bb').trim(),
      up: s.getPropertyValue('--chart-up').trim(),
      down: s.getPropertyValue('--chart-down').trim(),
      areaStart: s.getPropertyValue('--chart-area-start').trim(),
      areaEnd: s.getPropertyValue('--chart-area-end').trim(),
    }
  }, [theme])

  useEffect(() => { fetchHistory() }, [ticker, period])

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const json = await cachedFetch(`/api/stocks/${ticker}/history?period=${period}`)
      setData(json.data.map((d: any) => ({ ...d, Date: d.Date.split('T')[0] })))
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const chartMetrics = useMemo(() => {
    if (!data.length) return { yMin: 0, yMax: 100, volumeMax: 100 }
    const prices = data.flatMap(d => [d.High, d.Low])
    return {
      yMin: Math.min(...prices) * 0.99,
      yMax: Math.max(...prices) * 1.01,
      volumeMax: Math.max(...data.map(d => d.Volume))
    }
  }, [data])

  const periods = ['1mo', '3mo', '6mo', '1y', '2y', '5y']

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left
    const idx = Math.floor(((x - pad.l) / iW) * data.length)
    if (idx >= 0 && idx < data.length) {
      setHoverData(data[idx])
    }
  }

  if (loading) {
    return <div className="h-80 animate-pulse rounded" style={{
      background: 'rgb(var(--color-surface-elevated))',
      border: '1px solid rgb(var(--color-line))',
    }} />
  }

  const W = 900, H = 380
  const pad = { t: 16, r: 56, b: 24, l: 8 }
  const iW = W - pad.l - pad.r, iH = H - pad.t - pad.b
  const { yMin, yMax, volumeMax } = chartMetrics
  const cW = Math.max(2, (iW / data.length) - 1)
  const scaleY = (p: number) => pad.t + iH - ((p - yMin) / (yMax - yMin)) * iH
  const scaleX = (i: number) => pad.l + (i / data.length) * iW

  return (
    <div className="panel">
      {/* OHLC Tooltip */}
      {hoverData && (
        <div className="flex items-center gap-4 mb-3 text-xs tabular-nums animate-fade-in" style={{
          fontFamily: '"JetBrains Mono", monospace',
          color: 'rgb(var(--color-txt-sec))',
        }}>
          <span className="text-txt-dim">{hoverData.Date}</span>
          <span>O <span className="text-txt">{hoverData.Open?.toFixed(2)}</span></span>
          <span>H <span className="text-up">{hoverData.High?.toFixed(2)}</span></span>
          <span>L <span className="text-down">{hoverData.Low?.toFixed(2)}</span></span>
          <span>C <span className="text-txt font-medium">{hoverData.Close?.toFixed(2)}</span></span>
          <span>Vol <span className="text-txt-dim">{(hoverData.Volume / 1e6).toFixed(1)}M</span></span>
          {hoverData.SMA_20 && <span>SMA20 <span className="text-accent">{hoverData.SMA_20?.toFixed(2)}</span></span>}
        </div>
      )}
      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-0.5" style={{
          background: 'rgb(var(--color-surface))',
          border: '1px solid rgb(var(--color-line))',
          borderRadius: '4px',
          padding: '2px',
        }}>
          {periods.map(p => (
            <button key={p} onClick={() => setPeriod(p)}
              className="px-2.5 py-1 rounded text-xxs font-medium transition-colors"
              style={{
                fontFamily: '"Space Grotesk", system-ui, sans-serif',
                background: period === p ? 'rgb(var(--color-accent))' : 'transparent',
                color: period === p ? '#0C0A09' : 'rgb(var(--color-txt-muted))',
              }}>{p}</button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded overflow-hidden" style={{
            border: '1px solid rgb(var(--color-line))',
          }}>
            {(['candle', 'area'] as const).map(t => (
              <button key={t} onClick={() => setChartType(t)}
                className="px-2.5 py-1 text-xxs font-medium transition-colors"
                style={{
                  fontFamily: '"Space Grotesk", system-ui, sans-serif',
                  background: chartType === t ? 'rgb(var(--color-accent))' : 'rgb(var(--color-surface))',
                  color: chartType === t ? '#0C0A09' : 'rgb(var(--color-txt-muted))',
                }}>{t === 'candle' ? 'Candle' : 'Area'}</button>
            ))}
          </div>
          {[
            { key: 'sma', label: 'SMA' },
            { key: 'bb', label: 'BB' },
            { key: 'volume', label: 'Vol' },
          ].map(({ key, label }) => (
            <label key={key} className="flex items-center gap-1 cursor-pointer">
              <input type="checkbox"
                checked={(showIndicators as any)[key]}
                onChange={(e) => setShowIndicators({ ...showIndicators, [key]: e.target.checked })}
                className="w-3 h-3 rounded accent-accent" style={{ borderColor: 'rgb(var(--color-line))' }} />
              <span className="text-xxs text-txt-muted" style={{ fontFamily: '"Space Grotesk", system-ui, sans-serif' }}>{label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="overflow-x-auto">
        <svg width={W} height={H} className="select-none cursor-crosshair"
          onMouseMove={handleMouseMove} onMouseLeave={() => setHoverData(null)}>
          <defs>
            <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={c.sma20} stopOpacity={0.15} />
              <stop offset="100%" stopColor={c.sma20} stopOpacity={0} />
            </linearGradient>
            <linearGradient id="agPink" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={c.sma20} stopOpacity={0.12} />
              <stop offset="50%" stopColor={c.sma50} stopOpacity={0.08} />
              <stop offset="100%" stopColor={c.bb} stopOpacity={0} />
            </linearGradient>
          </defs>

          {/* Grid */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const y = pad.t + iH * (1 - pct)
            const price = yMin + (yMax - yMin) * pct
            return (
              <g key={i}>
                <line x1={pad.l} y1={y} x2={W - pad.r} y2={y} stroke={c.grid} strokeWidth={0.5} />
                <text x={W - pad.r + 4} y={y + 3} fill={c.label} fontSize={9} fontFamily="JetBrains Mono, monospace">
                  ${price.toFixed(2)}
                </text>
              </g>
            )
          })}

          {/* SMA */}
          {showIndicators.sma && (
            <>
              <polyline points={data.map((d, i) => `${scaleX(i) + cW / 2},${scaleY(d.SMA_20)}`).join(' ')}
                fill="none" stroke={c.sma20} strokeWidth={0.8} opacity={0.5} />
              <polyline points={data.map((d, i) => `${scaleX(i) + cW / 2},${scaleY(d.SMA_50)}`).join(' ')}
                fill="none" stroke={c.sma50} strokeWidth={0.8} opacity={0.5} />
            </>
          )}

          {/* Bollinger */}
          {showIndicators.bb && (
            <>
              <polyline points={data.map((d, i) => `${scaleX(i) + cW / 2},${scaleY(d.BB_Upper)}`).join(' ')}
                fill="none" stroke={c.bb} strokeWidth={0.8} strokeDasharray="3 2" opacity={0.5} />
              <polyline points={data.map((d, i) => `${scaleX(i) + cW / 2},${scaleY(d.BB_Lower)}`).join(' ')}
                fill="none" stroke={c.bb} strokeWidth={0.8} strokeDasharray="3 2" opacity={0.5} />
            </>
          )}

          {/* Volume */}
          {showIndicators.volume && (
            <g opacity={0.2}>
              {data.map((d, i) => {
                const vh = (d.Volume / volumeMax) * (iH * 0.12)
                return <rect key={`v${i}`} x={scaleX(i)} y={pad.t + iH - vh} width={cW} height={vh}
                  fill={d.Close >= d.Open ? c.up : c.down} />
              })}
            </g>
          )}

          {/* Candles / Area */}
          {chartType === 'candle' ? (
            data.map((d, i) => {
              const x = scaleX(i)
              const up = d.Close >= d.Open
              const col = up ? c.up : c.down
              const bTop = scaleY(Math.max(d.Open, d.Close))
              const bBot = scaleY(Math.min(d.Open, d.Close))
              return (
                <g key={i}>
                  <line x1={x + cW / 2} y1={scaleY(d.High)} x2={x + cW / 2} y2={scaleY(d.Low)}
                    stroke={col} strokeWidth={0.8} />
                  <rect x={x} y={bTop} width={cW} height={Math.max(bBot - bTop, 0.8)} fill={up ? col : col} />
                </g>
              )
            })
          ) : (
            <>
              <polygon
                points={[...data.map((d, i) => `${scaleX(i) + cW / 2},${scaleY(d.Close)}`),
                  `${scaleX(data.length - 1) + cW / 2},${pad.t + iH}`, `${scaleX(0) + cW / 2},${pad.t + iH}`].join(' ')}
                fill="url(#agPink)" />
              <polyline points={data.map((d, i) => `${scaleX(i) + cW / 2},${scaleY(d.Close)}`).join(' ')}
                fill="none" stroke={c.sma20} strokeWidth={1.5} />
            </>
          )}
        </svg>
      </div>

      {/* RSI */}
      <div className="mt-3 pt-3" style={{ borderTop: '1px solid rgb(var(--color-line))' }}>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xxs text-txt-muted" style={{
            fontFamily: '"Space Grotesk", system-ui, sans-serif',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}>RSI</span>
        </div>
        <svg width={W} height={60}>
          {[30, 50, 70].map(lvl => {
            const y = 6 + (1 - lvl / 100) * 48
            return (
              <g key={lvl}>
                <line x1={pad.l} y1={y} x2={W - pad.r} y2={y} stroke={c.grid} strokeWidth={0.5} strokeDasharray="2 2" />
                <text x={W - pad.r + 4} y={y + 3} fill={c.label} fontSize={8} fontFamily="JetBrains Mono, monospace">{lvl}</text>
              </g>
            )
          })}
          <rect x={pad.l} y={6} width={iW} height={14} fill={c.sma50} opacity={0.04} />
          <rect x={pad.l} y={40} width={iW} height={14} fill={c.sma20} opacity={0.04} />
          <polyline
            points={data.map((d, i) => `${scaleX(i) + cW / 2},${6 + (1 - ((d.RSI || 50) / 100)) * 48}`).join(' ')}
            fill="none" stroke={c.sma50} strokeWidth={1} />
        </svg>
      </div>
    </div>
  )
}
