import { useState, useEffect } from 'react'
import FadeIn from './FadeIn'

interface PredictionPanelProps {
  ticker: string
}

interface Voter {
  vote: 'UP' | 'DOWN' | 'NEUTRAL'
  label: string
}

interface CombinedSignal {
  direction: 'UP' | 'DOWN' | 'UNCERTAIN'
  confidence: number
  voters: Record<string, Voter>
  up_votes: number
  down_votes: number
  neutral_votes: number
  summary: string
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
      const raw = json.combined

      // Normalize: old backend returns {final_signal, breakdown}, new returns {direction, voters}
      if (raw.direction) {
        // New format — already correct
        setData(raw)
      } else if (raw.final_signal) {
        // Old format — convert to new format
        const sig = raw.final_signal.toUpperCase()
        const direction = sig.includes('BUY') ? 'UP' : sig.includes('SELL') ? 'DOWN' : 'UNCERTAIN'
        const confidence = raw.final_confidence || 0
        const voters: Record<string, Voter> = {}
        if (raw.breakdown) {
          if (raw.breakdown.ml) voters.ml = { vote: raw.breakdown.ml.signal?.includes('BUY') ? 'UP' : raw.breakdown.ml.signal?.includes('SELL') ? 'DOWN' : 'NEUTRAL', label: 'ML Model' }
          if (raw.breakdown.technical) voters.technical = { vote: raw.breakdown.technical.signal?.includes('BUY') ? 'UP' : raw.breakdown.technical.signal?.includes('SELL') ? 'DOWN' : 'NEUTRAL', label: 'Technical' }
          if (raw.breakdown.sentiment) voters.sentiment = { vote: raw.breakdown.sentiment.score > 0 ? 'UP' : raw.breakdown.sentiment.score < 0 ? 'DOWN' : 'NEUTRAL', label: 'Sentiment' }
        }
        const upVotes = Object.values(voters).filter(v => v.vote === 'UP').length
        const downVotes = Object.values(voters).filter(v => v.vote === 'DOWN').length
        const neutralVotes = Object.values(voters).filter(v => v.vote === 'NEUTRAL').length
        setData({
          direction,
          confidence,
          voters,
          up_votes: upVotes,
          down_votes: downVotes,
          neutral_votes: neutralVotes,
          summary: raw.agreement === 'all_agree' ? 'All indicators agree.' : 'Mixed signals — indicators disagree.',
        })
      } else {
        setData(null)
      }
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const getDirectionColor = (dir: string) => {
    if (dir === 'UP') return 'text-up'
    if (dir === 'DOWN') return 'text-down'
    return 'text-txt-muted'
  }

  const getDirectionBg = (dir: string) => {
    if (dir === 'UP') return 'border-up/20'
    if (dir === 'DOWN') return 'border-down/20'
    return 'bg-surface-overlay border-line'
  }

  const getDirectionBgStyle = (dir: string) => {
    if (dir === 'UP') return { background: 'rgb(var(--color-up) / 0.06)' }
    if (dir === 'DOWN') return { background: 'rgb(var(--color-down) / 0.06)' }
    return {}
  }

  const getVoteIcon = (vote: string) => {
    if (vote === 'UP') return { icon: '↑', color: 'text-up' }
    if (vote === 'DOWN') return { icon: '↓', color: 'text-down' }
    return { icon: '—', color: 'text-txt-muted' }
  }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="section-header" style={{ border: 'none', paddingBottom: 0, marginBottom: 0 }}>
          Price Prediction
        </span>
        <button onClick={fetchCombined} disabled={loading}
          className="text-xxs text-accent hover:text-accent-hover disabled:text-txt-muted">
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          <div className="h-20 skeleton" />
          <div className="h-4 skeleton" />
          <div className="h-4 skeleton" />
        </div>
      ) : data ? (
        <FadeIn>
          <div className="space-y-4">

            {/* Big Direction Display */}
            <div className={`text-center py-5 rounded-lg border ${getDirectionBg(data.direction)}`}
              style={getDirectionBgStyle(data.direction)}>
              <div className={`text-5xl font-bold mb-2 ${getDirectionColor(data.direction)}`}
                style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                {data.direction === 'UP' ? '↑' : data.direction === 'DOWN' ? '↓' : '?'}
              </div>
              <p className={`text-xl font-bold ${getDirectionColor(data.direction)}`}
                style={{ fontFamily: '"Space Grotesk", system-ui, sans-serif' }}>
                {data.direction === 'UP' ? 'Will Go Up' :
                 data.direction === 'DOWN' ? 'Will Go Down' :
                 'Uncertain'}
              </p>
              {data.direction !== 'UNCERTAIN' && (
                <p className="text-sm mt-1" style={{ color: 'rgb(var(--color-txt-sec))' }}>
                  Confidence: <span className="font-bold" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                    {data.confidence}%
                  </span>
                </p>
              )}
            </div>

            {/* Summary */}
            <p className="text-xs text-center" style={{ color: 'rgb(var(--color-txt-dim))' }}>
              {data.summary}
            </p>

            {/* Voter Breakdown */}
            <div>
              <p className="text-xxs uppercase tracking-wider mb-2" style={{
                fontFamily: '"Space Grotesk", system-ui, sans-serif',
                letterSpacing: '0.1em',
                color: 'rgb(var(--color-txt-muted))',
              }}>Indicator Votes</p>
              <div className="space-y-1.5">
                {Object.entries(data.voters).map(([key, voter]) => {
                  const v = getVoteIcon(voter.vote)
                  return (
                    <div key={key} className="flex items-center justify-between py-1.5 px-3 rounded"
                      style={{ background: 'rgb(var(--color-surface))' }}>
                      <span className="text-xs" style={{ color: 'rgb(var(--color-txt-sec))' }}>
                        {voter.label}
                      </span>
                      <span className={`text-sm font-bold ${v.color}`}
                        style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                        {v.icon}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Vote Count */}
            <div className="flex items-center justify-center gap-4 text-xxs" style={{
              color: 'rgb(var(--color-txt-muted))',
              fontFamily: '"JetBrains Mono", monospace',
            }}>
              <span className="text-up">{data.up_votes} UP</span>
              <span>·</span>
              <span className="text-down">{data.down_votes} DOWN</span>
              <span>·</span>
              <span>{data.neutral_votes} NEUTRAL</span>
            </div>

          </div>
        </FadeIn>
      ) : (
        <div className="text-txt-muted text-xs text-center py-12">No data</div>
      )}
    </div>
  )
}
