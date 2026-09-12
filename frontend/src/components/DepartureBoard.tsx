import { useEffect, useState } from 'react'
import { cachedFetch } from '../cache'
import SplitFlap from './SplitFlap'

type Tone = 'up' | 'down' | 'muted' | ''
interface Price { current_price: number; change_percent?: number }
interface Call { dir: 'UP' | 'DOWN' | 'UNCERTAIN' }

function readCall(raw: any): Call | null {
  if (!raw) return null
  if (raw.direction) return { dir: raw.direction }
  if (raw.final_signal) {
    const s = String(raw.final_signal).toUpperCase()
    const dir = s.includes('BUY') ? 'UP' : s.includes('SELL') ? 'DOWN' : 'UNCERTAIN'
    return { dir }
  }
  return null
}

function useClock() {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const i = setInterval(() => setNow(new Date()), 10000)
    return () => clearInterval(i)
  }, [])
  return now
}

function Cell({ label, text, length, tone = '', align }: {
  label: string; text: string; length: number; tone?: Tone; align?: 'left' | 'right'
}) {
  return (
    <div className={`min-w-0 ${tone ? `tone-${tone}` : ''}`}>
      <div className="board-label">{label}</div>
      <SplitFlap text={text} length={length} align={align} className="text-2xl lg:text-3xl" />
    </div>
  )
}

export default function DepartureBoard({ ticker }: { ticker: string }) {
  const [price, setPrice] = useState<Price | null>(null)
  const [call, setCall] = useState<Call | null>(null)
  const now = useClock()

  useEffect(() => {
    let alive = true
    setPrice(null)
    setCall(null)
    cachedFetch(`/api/stocks/${ticker}`)
      .then((j: any) => { if (alive && j?.price?.current_price != null) setPrice(j.price) })
      .catch(() => {})
    cachedFetch(`/api/stocks/${ticker}/combined`)
      .then((j: any) => { if (alive) setCall(readCall(j?.combined)) })
      .catch(() => {})
    return () => { alive = false }
  }, [ticker])

  const pct = price?.change_percent ?? 0
  const dirTone: Tone = call?.dir === 'UP' ? 'up' : call?.dir === 'DOWN' ? 'down' : 'muted'
  const direction = !call ? '' : call.dir === 'UP' ? '↑ UP' : call.dir === 'DOWN' ? '↓ DOWN' : '- HOLD'
  const clock = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`

  return (
    <section className="board" aria-label="Prediction board">
      <span className="board-bolt" style={{ top: 8, left: 8 }} />
      <span className="board-bolt" style={{ top: 8, right: 8 }} />
      <span className="board-bolt" style={{ bottom: 8, left: 8 }} />
      <span className="board-bolt" style={{ bottom: 8, right: 8 }} />

      <div className="board-strip">
        <span className="text-sm lg:text-base font-semibold">Next move · Departures</span>
        <SplitFlap text={clock} className="text-base lg:text-lg" stagger={60} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-5">
        <Cell label="Ticker" text={ticker} length={5} />
        <Cell label="Price" text={price ? price.current_price.toFixed(2) : ''} length={7} align="right" />
        <Cell label="Today" text={price ? `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%` : ''} length={7} align="right"
          tone={price ? (pct >= 0 ? 'up' : 'down') : ''} />
        <Cell label="Model leans" text={direction} length={6} tone={call ? dirTone : ''} />
      </div>

      <p className="board-note">A model guess, not advice. In testing it has not yet beaten chance.</p>
    </section>
  )
}
