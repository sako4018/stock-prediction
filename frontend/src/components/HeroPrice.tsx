import { useState, useEffect, useRef } from 'react'
import { cachedFetch } from '../cache'

function AnimatedPrice({ value, decimals = 2, prefix = '$' }: { value: number; decimals?: number; prefix?: string }) {
  const [display, setDisplay] = useState(value)
  const prevRef = useRef(value)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    const from = prevRef.current
    const to = value
    const start = performance.now()
    const animate = (now: number) => {
      const p = Math.min((now - start) / 600, 1)
      const e = 1 - Math.pow(1 - p, 3)
      setDisplay(from + (to - from) * e)
      if (p < 1) rafRef.current = requestAnimationFrame(animate)
      else prevRef.current = to
    }
    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [value])

  return <span style={{ fontFamily: '"JetBrains Mono", monospace' }}>{prefix}{display.toFixed(decimals)}</span>
}

export default function HeroPrice({ ticker }: { ticker: string }) {
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    setData(null)
    const load = async () => {
      try {
        const json = await cachedFetch(`/api/stocks/${ticker}`)
        if (json.price) setData(json.price)
      } catch {}
    }
    load()
    const i = setInterval(load, 15000)
    return () => clearInterval(i)
  }, [ticker])

  if (!data || data.current_price == null) return <span style={{ color: 'rgb(var(--color-txt-muted))' }}>Loading...</span>

  const up = (data.change || 0) >= 0
  const change = data.change || 0
  const changePercent = data.change_percent || 0

  return (
    <div className="flex items-baseline gap-3">
      <span className="text-3xl font-bold tabular-nums" style={{
        fontFamily: '"JetBrains Mono", monospace',
        color: 'rgb(var(--color-txt))',
        letterSpacing: '-0.02em',
      }}>
        <AnimatedPrice value={data.current_price} />
      </span>
      <span className="text-sm font-medium tabular-nums" style={{ color: up ? 'rgb(var(--color-up))' : 'rgb(var(--color-down))' }}>
        {up ? '+' : ''}<AnimatedPrice value={change} decimals={2} />
      </span>
      <span className="text-xxs font-semibold px-2 py-0.5 rounded" style={{
        fontFamily: '"JetBrains Mono", monospace',
        background: up ? 'rgb(var(--color-up) / 0.08)' : 'rgb(var(--color-down) / 0.08)',
        color: up ? 'rgb(var(--color-up))' : 'rgb(var(--color-down))',
      }}>
        {up ? '▲' : '▼'} {Math.abs(changePercent).toFixed(2)}%
      </span>
    </div>
  )
}
