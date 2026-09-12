import { useState, useRef, useEffect } from 'react'
import { searchCompanies } from '../data/companies'

export default function StockSearch({ onSelect }: { onSelect: (ticker: string) => void }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const boxRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const results = query.trim() ? searchCompanies(query.trim()).slice(0, 6) : []

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const pick = (ticker: string) => {
    onSelect(ticker.toUpperCase())
    setQuery('')
    setOpen(false)
    inputRef.current?.blur()
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive(a => Math.min(a + 1, results.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(a => Math.max(a - 1, 0)) }
    else if (e.key === 'Enter') {
      const hit = results[active]
      if (hit) pick(hit.ticker)
      else if (query.trim()) pick(query.trim())
    }
    else if (e.key === 'Escape') { setOpen(false); inputRef.current?.blur() }
  }

  return (
    <div ref={boxRef} className="search">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
      <input
        ref={inputRef}
        value={query}
        onChange={e => { setQuery(e.target.value); setActive(0); setOpen(true) }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
        placeholder="Search"
        aria-label="Search stocks"
        autoComplete="off"
        spellCheck={false}
      />
      {open && results.length > 0 && (
        <ul className="search-results" role="listbox">
          {results.map((c, i) => (
            <li key={c.ticker}>
              <button
                onMouseDown={e => e.preventDefault()}
                onClick={() => pick(c.ticker)}
                onMouseEnter={() => setActive(i)}
                className={i === active ? 'is-active' : ''}
              >
                <span className="search-ticker">{c.ticker}</span>
                <span className="search-name">{c.name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
