import { useEffect, useRef, useState } from 'react'

const GLYPHS = ' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$.,+-%↑↓:'
const STEP_MS = 70
const MAX_STEPS = 8

const reducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

function Half({ char, className }: { char: string; className: string }) {
  return (
    <span className={`flap-half ${className}`}>
      <span>{char === ' ' ? '\u00a0' : char}</span>
    </span>
  )
}

function Flap({ target, delay }: { target: string; delay: number }) {
  const [shown, setShown] = useState(' ')
  const [prev, setPrev] = useState(' ')
  const [tick, setTick] = useState(0)
  const shownRef = useRef(' ')

  useEffect(() => {
    if (shownRef.current === target) return
    if (reducedMotion() || !GLYPHS.includes(target)) {
      shownRef.current = target
      setPrev(target)
      setShown(target)
      return
    }
    // Real boards spin through every glyph; cap the spin so a change settles in ~half a second.
    const n = GLYPHS.length
    const from = Math.max(GLYPHS.indexOf(shownRef.current), 0)
    const to = GLYPHS.indexOf(target)
    if ((to - from + n) % n > MAX_STEPS) shownRef.current = GLYPHS[(to - MAX_STEPS + n) % n]

    let timer = 0
    const step = () => {
      const cur = shownRef.current
      if (cur === target) return
      const next = GLYPHS[(GLYPHS.indexOf(cur) + 1) % n]
      shownRef.current = next
      setPrev(cur)
      setShown(next)
      setTick(t => t + 1)
      timer = window.setTimeout(step, STEP_MS)
    }
    timer = window.setTimeout(step, delay)
    return () => clearTimeout(timer)
  }, [target, delay])

  return (
    <span className="flap" aria-hidden="true">
      <Half char={shown} className="flap-top" />
      <Half char={shown} className="flap-bottom" />
      {tick > 0 && <Half key={tick} char={prev} className="flap-top flap-fall" />}
    </span>
  )
}

interface SplitFlapProps {
  text: string
  length?: number
  align?: 'left' | 'right'
  stagger?: number
  className?: string
}

export default function SplitFlap({ text, length, align = 'left', stagger = 40, className = '' }: SplitFlapProps) {
  const upper = text.toUpperCase()
  const size = length ?? upper.length
  const padded = (align === 'right' ? upper.padStart(size) : upper.padEnd(size)).slice(0, size)

  return (
    <span className={`flap-row ${className}`}>
      <span className="sr-only">{text}</span>
      {padded.split('').map((c, i) => (
        <Flap key={i} target={c} delay={i * stagger} />
      ))}
    </span>
  )
}
