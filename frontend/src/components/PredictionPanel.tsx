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
        if (raw.breakdown?.ml) voters.ml = { vote: raw.breakdown.ml.signal?.includes('BUY') ? 'UP' : raw.breakdown.ml.signal?.includes('SELL') ? 'DOWN' : 'NEUTRAL', label: 'ML' }
        if (raw.breakdown?.technical) voters.technical = { vote: raw.breakdown.technical.signal?.includes('BUY') ? 'UP' : raw.breakdown.technical.signal?.includes('SELL') ? 'DOWN' : 'NEUTRAL', label: 'TECH' }
        if (raw.breakdown?.sentiment) voters.sentiment = { vote: raw.breakdown.sentiment.score > 0 ? 'UP' : raw.breakdown.sentiment.score < 0 ? 'DOWN' : 'NEUTRAL', label: 'SENT' }
        const up = Object.values(voters).filter(v => v.vote === 'UP').length
        const down = Object.values(voters).filter(v => v.vote === 'DOWN').length
        const neut = Object.values(voters).filter(v => v.vote === 'NEUTRAL').length
        setData({ direction: dir, confidence: raw.final_confidence || 0, voters, up_votes: up, down_votes: down, neutral_votes: neut, summary: raw.agreement === 'all_agree' ? 'ALL AGREE' : 'MIXED' })
      }
    } catch {}
    setLoading(false)
  }

  const voteChar = (v: string) => v === 'UP' ? { t: '▲', c: 'var(--green)' } : v === 'DOWN' ? { t: '▼', c: 'var(--red)' } : { t: '—', c: 'var(--dim)' }

  return (
    <div className="panel">
      <div className="panel-title">SIGNAL ANALYSIS</div>
      {loading ? (
        <div style={{ color: 'var(--dim)' }}>Loading...</div>
      ) : data ? (
        <div>
          {/* Big signal */}
          <div className="text-center py-3 mb-2" style={{
            borderTop: '1px solid var(--border)',
            borderBottom: '1px solid var(--border)',
          }}>
            <div className="text-3xl font-bold mb-1" style={{
              color: data.direction === 'UP' ? 'var(--green)' : data.direction === 'DOWN' ? 'var(--red)' : 'var(--dim)',
            }}>
              {data.direction === 'UP' ? '▲' : data.direction === 'DOWN' ? '▼' : '?'}
            </div>
            <div className="text-sm font-bold" style={{
              color: data.direction === 'UP' ? 'var(--green)' : data.direction === 'DOWN' ? 'var(--red)' : 'var(--dim)',
            }}>
              {data.direction === 'UP' ? 'BULLISH' : data.direction === 'DOWN' ? 'BEARISH' : 'UNCERTAIN'}
            </div>
            {data.direction !== 'UNCERTAIN' && (
              <div className="text-xs mt-1" style={{ color: 'var(--amber)' }}>
                CONFIDENCE: {data.confidence}%
              </div>
            )}
          </div>

          {/* Voters */}
          <div className="space-y-0.5">
            {Object.entries(data.voters).map(([k, v]) => {
              const vc = voteChar(v.vote)
              return (
                <div key={k} className="flex items-center justify-between text-xs py-0.5">
                  <span style={{ color: 'var(--dim)' }}>{v.label}</span>
                  <span style={{ color: vc.c }}>{vc.t}</span>
                </div>
              )
            })}
          </div>

          {/* Vote count */}
          <div className="flex items-center justify-center gap-3 text-xs mt-2 pt-2" style={{ borderTop: '1px solid var(--border)' }}>
            <span style={{ color: 'var(--green)' }}>{data.up_votes}↑</span>
            <span style={{ color: 'var(--dim)' }}>|</span>
            <span style={{ color: 'var(--red)' }}>{data.down_votes}↓</span>
            <span style={{ color: 'var(--dim)' }}>|</span>
            <span>{data.neutral_votes}—</span>
          </div>
        </div>
      ) : (
        <div style={{ color: 'var(--dim)' }}>NO DATA</div>
      )}
    </div>
  )
}
