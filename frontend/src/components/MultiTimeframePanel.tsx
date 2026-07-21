import { useState, useEffect } from 'react'

interface Props { ticker: string }

export default function MultiTimeframePanel({ ticker }: Props) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => { fetchData() }, [ticker])

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/stocks/${ticker}/multi-timeframe`)
      const json = await res.json()
      setData(json)
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const getSignalColor = (s: string) => {
    if (s?.includes('BUY')) return 'text-up'
    if (s?.includes('SELL')) return 'text-down'
    return 'text-txt-dim'
  }

  const getSignalBg = (s: string) => {
    if (s?.includes('BUY')) return 'bg-up/10 border-up/20'
    if (s?.includes('SELL')) return 'bg-down/10 border-down/20'
    return 'bg-elevated border-line'
  }

  const TimeframeCard = ({ label, data, weight }: { label: string; data: any; weight: string }) => (
    <div className="bg-elevated rounded p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-txt">{label}</span>
          <span className="text-xxs text-txt-dim">({weight})</span>
        </div>
        <span className={`text-xs font-semibold ${getSignalColor(data?.signal)}`}>
          {data?.signal || '—'}
        </span>
      </div>
      {data?.indicators && (
        <div className="grid grid-cols-2 gap-1 text-xxs">
          <span className="text-txt-dim">RSI: <span className="text-txt-sec">{data.indicators.rsi?.toFixed(0)}</span></span>
          <span className="text-txt-dim">ADX: <span className="text-txt-sec">{data.indicators.adx?.toFixed(0)}</span></span>
          <span className="text-txt-dim">Stoch: <span className="text-txt-sec">{data.indicators.stoch_k?.toFixed(0)}</span></span>
          <span className="text-txt-dim">MACD: <span className={`text-txt-sec`}>{data.indicators.macd > 0 ? '+' : ''}{data.indicators.macd?.toFixed(2)}</span></span>
        </div>
      )}
      {data?.period && <p className="text-xxs text-txt-dim mt-1">Period: {data.period}</p>}
    </div>
  )

  return (
    <div className="bg-alt border border-line rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xxs font-medium text-txt-dim uppercase tracking-wider">Multi-Timeframe Analysis</span>
        <button onClick={fetchData} disabled={loading} className="text-xxs text-accent hover:text-accent-hover disabled:text-txt-dim">
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {loading ? (
        <div className="text-txt-dim text-xs text-center py-8">Analyzing 3 timeframes...</div>
      ) : data ? (
        <div className="space-y-3">
          {/* Combined */}
          <div className={`text-center py-2.5 rounded border ${getSignalBg(data.combined_signal)}`}>
            <p className="text-xxs text-txt-dim uppercase tracking-wider mb-0.5">Combined</p>
            <p className={`text-base font-bold ${getSignalColor(data.combined_signal)}`}>{data.combined_signal}</p>
            <p className="text-xxs text-txt-dim">Agreement: {data.agreement}</p>
          </div>

          {/* Timeframes */}
          <TimeframeCard label="Daily" data={data.timeframes?.daily} weight="40%" />
          <TimeframeCard label="Weekly" data={data.timeframes?.weekly} weight="35%" />
          <TimeframeCard label="Monthly" data={data.timeframes?.monthly} weight="25%" />
        </div>
      ) : (
        <div className="text-txt-dim text-xs text-center py-8">No data</div>
      )}
    </div>
  )
}
