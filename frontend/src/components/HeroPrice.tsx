import { useState, useEffect, useRef } from 'react'
import { cachedFetch } from '../cache'

interface HeroPriceProps {
  ticker: string
}

interface PriceData {
  current_price: number
  previous_close: number
  change: number
  change_percent: number
  currency: string
}

function AnimatedPrice({ value, decimals = 2, prefix = '$' }: { value: number; decimals?: number; prefix?: string }) {
  const [display, setDisplay] = useState(value)
  const prevRef = useRef(value)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    const from = prevRef.current
    const to = value
    const startTime = performance.now()
    const duration = 800

    const animate = (now: number) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(from + (to - from) * eased)
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate)
      } else {
        prevRef.current = to
      }
    }

    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [value])

  return (
    <span className="tabular-nums" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
      {prefix}{display.toFixed(decimals)}
    </span>
  )
}

export default function HeroPrice({ ticker }: HeroPriceProps) {
  const [data, setData] = useState<PriceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [pulse, setPulse] = useState(false)

  useEffect(() => {
    setData(null)
    setLoading(true)
    fetchPrice()
    const interval = setInterval(fetchPrice, 10000)
    return () => clearInterval(interval)
  }, [ticker])

  const fetchPrice = async () => {
    try {
      const json = await cachedFetch(`/api/stocks/${ticker}`)
      if (json.price) {
        setData(json.price)
        setPulse(true)
        setTimeout(() => setPulse(false), 300)
      }
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  if (loading || !data) {
    return (
      <div className="flex items-center gap-3">
        <div className="h-7 w-28 rounded animate-pulse" style={{ background: 'var(--price-loading)' }} />
      </div>
    )
  }

  const isPositive = data.change >= 0

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-baseline gap-3">
        <span className={`text-3xl font-bold tabular-nums tracking-tight transition-colors duration-300 ${
          pulse ? (isPositive ? 'text-up' : 'text-down') : 'text-txt'
        }`} style={{ fontFamily: '"JetBrains Mono", monospace', letterSpacing: '-0.02em' }}>
          <AnimatedPrice value={data.current_price} decimals={2} />
        </span>
        <span className={`text-sm font-medium tabular-nums ${isPositive ? 'text-up' : 'text-down'}`}>
          {isPositive ? '+' : ''}<AnimatedPrice value={data.change} decimals={2} />
        </span>
        <span className={`text-xxs font-semibold px-2 py-0.5 rounded ${
          isPositive ? 'bg-up/10 text-up' : 'bg-down/10 text-down'
        }`} style={{ fontFamily: '"JetBrains Mono", monospace' }}>
          {isPositive ? '▲' : '▼'} {Math.abs(data.change_percent).toFixed(2)}%
        </span>
      </div>
    </div>
  )
}
