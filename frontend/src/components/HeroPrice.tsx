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

  return <span>{prefix}{display.toFixed(decimals)}</span>
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

  if (!data) return <span style={{ color: 'var(--dim)' }}>--</span>

  const up = data.change >= 0
  const color = up ? 'var(--green)' : 'var(--red)'
  const arrow = up ? '▲' : '▼'

  return (
    <span className="text-sm">
      <span className="font-bold" style={{ color: 'var(--bright)' }}>
        <AnimatedPrice value={data.current_price} />
      </span>
      <span className="ml-2" style={{ color }}>
        {arrow} {up ? '+' : ''}{data.change.toFixed(2)} ({up ? '+' : ''}{data.change_percent.toFixed(2)}%)
      </span>
    </span>
  )
}
