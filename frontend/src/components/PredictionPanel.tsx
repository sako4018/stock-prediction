import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

interface Voter { vote: 'UP' | 'DOWN' | 'NEUTRAL'; label: string }
interface Signal { direction: string; confidence: number; voters: Record<string, Voter>; up_votes: number; down_votes: number; neutral_votes: number; summary: string }

export default function PredictionPanel({ ticker }: { ticker: string }) {
  const [data, setData] = useState<Signal | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => { fetchCombined() }, [ticker])

  const fetchCombined = async () => {
    setLoading(true)
    try {
      const json = await cachedFetch(`/api/stocks/${ticker}/combined`)
      const raw = json.combined
      if (raw.direction) { setData(raw) }
      else if (raw.final_signal) {
        const sig = raw.final_signal.toUpperCase()
        const dir = sig.includes('BUY') ? 'UP' : sig.includes('SELL') ? 'DOWN' : 'UNCERTAIN'
        const voters: Record<string, Voter> = {}
        if (raw.breakdown?.ml) voters.ml = { vote: raw.breakdown.ml.signal?.includes('BUY') ? 'UP' : raw.breakdown.ml.signal?.includes('SELL') ? 'DOWN' : 'NEUTRAL', label: 'ML Model' }
        if (raw.breakdown?.technical) voters.technical = { vote: raw.breakdown.technical.signal?.includes('BUY') ? 'UP' : raw.breakdown.technical.signal?.includes('SELL') ? 'DOWN' : 'NEUTRAL', label: 'Technical' }
        if (raw.breakdown?.sentiment) voters.sentiment = { vote: raw.breakdown.sentiment.score > 0 ? 'UP' : raw.breakdown.sentiment.score < 0 ? 'DOWN' : 'NEUTRAL', label: 'Sentiment' }
        const up = Object.values(voters).filter(v => v.vote === 'UP').length
        const down = Object.values(voters).filter(v => v.vote === 'DOWN').length
        const neut = Object.values(voters).filter(v => v.vote === 'NEUTRAL').length
        setData({ direction: dir, confidence: raw.final_confidence || 0, voters, up_votes: up, down_votes: down, neutral_votes: neut, summary: raw.agreement === 'all_agree' ? 'All indicators agree.' : 'Mixed signals.' })
      }
    } catch {}
    setLoading(false)
  }

  const dirColor = (d: string) => d === 'UP' ? 'rgb(var(--color-up))' : d === 'DOWN' ? 'rgb(var(--color-down))' : 'rgb(var(--color-txt-muted))'
  const voteIcon = (v: string) => v === 'UP' ? { t: '↑', c: 'rgb(var(--color-up))' } : v === 'DOWN' ? { t: '↓', c: 'rgb(var(--color-down))' } : { t: '—', c: 'rgb(var(--color-txt-muted))' }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="section-header" style={{ border: 'none', paddingBottom: 0, marginBottom: 0 }}>Price Prediction</span>
        <button onClick={fetchCombined} disabled={loading} className="text-xxs" style={{ color: 'rgb(var(--color-accent))' }}>
          {loading ? '...' : 'Refresh'}
        </button>
      </div>
      {loading ? (
        <div className="space-y-3"><div className="h-20 skeleton" /><div className="h-4 skeleton" /></div>
      ) : data ? (
        <div className="space-y-4 animate-fade-in">
          {/* Direction */}
          <div className="text-center py-5 rounded-lg" style={{
            background: `rgb(${data.direction === 'UP' ? 'var(--color-up)' : data.direction === 'DOWN' ? 'var(--color-down)' : 'var(--color-surface-overlay)'} / 0.06)`,
            border: `1px solid rgb(${data.direction === 'UP' ? 'var(--color-up)' : data.direction === 'DOWN' ? 'var(--color-down)' : 'var(--color-line)'} / 0.15)`,
          }}>
            <div className="text-5xl font-bold mb-2" style={{ color: dirColor(data.direction), fontFamily: '"JetBrains Mono", monospace' }}>
              {data.direction === 'UP' ? '↑' : data.direction === 'DOWN' ? '↓' : '?'}
            </div>
            <p className="text-xl font-bold" style={{ color: dirColor(data.direction), fontFamily: '"Space Grotesk", system-ui, sans-serif' }}>
              {data.direction === 'UP' ? 'Will Go Up' : data.direction === 'DOWN' ? 'Will Go Down' : 'Uncertain'}
            </p>
            {data.direction !== 'UNCERTAIN' && (
              <p className="text-sm mt-1" style={{ color: 'rgb(var(--color-txt-sec))' }}>
                Confidence: <span className="font-bold" style={{ fontFamily: '"JetBrains Mono", monospace' }}>{data.confidence}%</span>
              </p>
            )}
          </div>
          <p className="text-xs text-center" style={{ color: 'rgb(var(--color-txt-dim))' }}>{data.summary}</p>
          {/* Voters */}
          <div>
            <p className="section-header">Indicator Votes</p>
            <div className="space-y-1">
              {Object.entries(data.voters).map(([k, v]) => {
                const vc = voteIcon(v.vote)
                return (
                  <div key={k} className="flex items-center justify-between py-1.5 px-3 rounded" style={{ background: 'rgb(var(--color-surface))' }}>
                    <span className="text-xs" style={{ color: 'rgb(var(--color-txt-sec))' }}>{v.label}</span>
                    <span className="text-sm font-bold" style={{ color: vc.c, fontFamily: '"JetBrains Mono", monospace' }}>{vc.t}</span>
                  </div>
                )
              })}
            </div>
          </div>
          <div className="flex items-center justify-center gap-4 text-xxs" style={{ color: 'rgb(var(--color-txt-muted))', fontFamily: '"JetBrains Mono", monospace' }}>
            <span style={{ color: 'rgb(var(--color-up))' }}>{data.up_votes} UP</span>
            <span>·</span>
            <span style={{ color: 'rgb(var(--color-down))' }}>{data.down_votes} DOWN</span>
            <span>·</span>
            <span>{data.neutral_votes} NEUTRAL</span>
          </div>
        </div>
      ) : (
        <div className="text-xs text-center py-12" style={{ color: 'rgb(var(--color-txt-muted))' }}>No data</div>
      )}
    </div>
  )
}
