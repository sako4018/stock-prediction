import { useState, useEffect } from 'react'
import FadeIn from './FadeIn'

interface PredictionPanelProps {
  ticker: string
}

interface CombinedSignal {
  final_signal: string
  final_score: number
  final_confidence: number
  agreement: string
  breakdown: {
    ml: {
      signal: string
      score: number
      confidence: number
      weight: number
      raw_prediction: number
    }
    technical: {
      signal: string
      score: number
      confidence: number
      weight: number
    }
    sentiment: {
      signal: string
      score: number
      confidence: number
      weight: number
      article_count: number
      bullish: number
      bearish: number
      neutral: number
    }
  }
}

export default function PredictionPanel({ ticker }: PredictionPanelProps) {
  const [data, setData] = useState<CombinedSignal | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => { fetchCombined() }, [ticker])

  const fetchCombined = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/stocks/${ticker}/combined`)
      const json = await res.json()
      setData(json.combined)
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const getSignalColor = (signal: string) => {
    const s = signal.toUpperCase()
    if (s.includes('BUY') || s.includes('BULLISH')) return 'text-up'
    if (s.includes('SELL') || s.includes('BEARISH')) return 'text-down'
    return 'text-txt-muted'
  }

  const getSignalBg = (signal: string) => {
    const s = signal.toUpperCase()
    if (s.includes('BUY') || s.includes('BULLISH')) return 'bg-up/10 border-up/20'
    if (s.includes('SELL') || s.includes('BEARISH')) return 'bg-down/10 border-down/20'
    return 'bg-surface-overlay border-line'
  }

  const getScoreBar = (score: number) => {
    const pct = ((score + 1) / 2) * 100
    const color = score > 0.1 ? '#22C55E' : score < -0.1 ? '#EF4444' : '#6B7280'
    return (
      <div className="h-1.5 bg-surface-overlay rounded-full overflow-hidden relative">
        <div className="absolute inset-0 flex">
          <div className="w-1/2" />
          <div className="w-px bg-frame h-full" />
        </div>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${Math.abs(pct - 50)}%`,
            marginLeft: pct >= 50 ? '50%' : `${pct}%`,
            backgroundColor: color
          }}
        />
      </div>
    )
  }

  return (
    <div className="bg-surface-alt border border-line rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xxs font-medium text-txt-muted uppercase tracking-wider">Combined Signal</span>
        <button onClick={fetchCombined} disabled={loading}
          className="text-xxs text-accent hover:text-accent-hover disabled:text-txt-muted">
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          <div className="h-8 skeleton" />
          <div className="h-12 skeleton" />
          <div className="h-4 skeleton" />
          <div className="h-4 skeleton" />
        </div>
      ) : data ? (
        <FadeIn>
        <div className="space-y-4">

          {/* === FINAL SIGNAL === */}
          <div className={`text-center py-3 rounded border ${getSignalBg(data.final_signal)}`}>
            <p className="text-xxs text-txt-muted uppercase tracking-wider mb-1">Final Verdict</p>
            <p className={`text-lg font-bold ${getSignalColor(data.final_signal)}`}>
              {data.final_signal}
            </p>
            <div className="flex items-center justify-center gap-3 mt-1.5">
              <span className="text-xxs text-txt-muted">
                Confidence: <span className="text-txt-dim font-medium">{data.final_confidence.toFixed(0)}%</span>
              </span>
              {data.agreement === 'all_agree' && (
                <span className="text-xxs px-1.5 py-0.5 rounded bg-accent/10 text-accent">All Agree</span>
              )}
            </div>
          </div>

          {/* === BREAKDOWN === */}
          <div className="space-y-3">

            {/* ML Signal */}
            <div className="bg-surface-elevated rounded p-3">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                  <span className="text-xs font-medium text-txt">ML Model</span>
                  <span className="text-xxs text-txt-muted">(40% weight)</span>
                </div>
                <span className={`text-xs font-semibold ${getSignalColor(data.breakdown.ml.signal)}`}>
                  {data.breakdown.ml.signal}
                </span>
              </div>
              {getScoreBar(data.breakdown.ml.score)}
              <div className="flex items-center justify-between mt-1.5">
                <span className="text-xxs text-txt-muted">
                  Output: {data.breakdown.ml.raw_prediction.toFixed(4)}
                </span>
                <span className="text-xxs text-txt-muted">
                  Confidence: {data.breakdown.ml.confidence.toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Technical Signal */}
            <div className="bg-surface-elevated rounded p-3">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-up" />
                  <span className="text-xs font-medium text-txt">Technical Indicators</span>
                  <span className="text-xxs text-txt-muted">(35% weight)</span>
                </div>
                <span className={`text-xs font-semibold ${getSignalColor(data.breakdown.technical.signal)}`}>
                  {data.breakdown.technical.signal}
                </span>
              </div>
              {getScoreBar(data.breakdown.technical.score)}
              <div className="flex items-center justify-between mt-1.5">
                <span className="text-xxs text-txt-muted">RSI + MACD + BB + Stoch + Williams</span>
                <span className="text-xxs text-txt-muted">
                  Confidence: {data.breakdown.technical.confidence.toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Sentiment Signal */}
            <div className="bg-surface-elevated rounded p-3">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]" />
                  <span className="text-xs font-medium text-txt">News Sentiment</span>
                  <span className="text-xxs text-txt-muted">(25% weight)</span>
                </div>
                <span className={`text-xs font-semibold ${getSignalColor(data.breakdown.sentiment.signal)}`}>
                  {data.breakdown.sentiment.signal}
                </span>
              </div>
              {getScoreBar(data.breakdown.sentiment.score)}
              <div className="flex items-center justify-between mt-1.5">
                <span className="text-xxs text-txt-muted">
                  {data.breakdown.sentiment.article_count} articles
                  {data.breakdown.sentiment.article_count > 0 && (
                    <> — <span className="text-up">{data.breakdown.sentiment.bullish}↑</span> <span className="text-down">{data.breakdown.sentiment.bearish}↓</span> <span className="text-txt-muted">{data.breakdown.sentiment.neutral}—</span></>
                  )}
                </span>
                <span className="text-xxs text-txt-muted">
                  Confidence: {data.breakdown.sentiment.confidence.toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

        </div>
        </FadeIn>
      ) : (
        <div className="text-txt-muted text-xs text-center py-12">No data</div>
      )}
    </div>
  )
}
