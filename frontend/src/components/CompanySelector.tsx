import { useState, useRef, useEffect } from 'react'
import { POPULAR_STOCKS, SECTORS, searchCompanies, Company } from '../data/companies'

interface CompanySelectorProps {
  onSelect: (ticker: string) => void
  currentTicker: string
}

export default function CompanySelector({ onSelect, currentTicker }: CompanySelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeSector, setActiveSector] = useState('All')
  const dropdownRef = useRef<HTMLDivElement>(null)

  const filtered = query
    ? searchCompanies(query)
    : activeSector === 'All'
      ? POPULAR_STOCKS
      : POPULAR_STOCKS.filter(c => c.sector === activeSector)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const currentCompany = POPULAR_STOCKS.find(c => c.ticker === currentTicker)

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2.5 px-3 py-2 rounded bg-surface-3 border border-border hover:border-border-light transition-colors text-left"
      >
        <div className="w-7 h-7 rounded bg-accent/15 flex items-center justify-center shrink-0">
          <span className="text-xxs font-semibold text-accent">{currentTicker.slice(0, 2)}</span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-text-primary">{currentTicker}</p>
          <p className="text-xxs text-text-muted truncate">{currentCompany?.name || 'Custom'}</p>
        </div>
        <svg className={`w-3.5 h-3.5 text-text-muted shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-80 bg-surface-2 border border-border rounded-lg shadow-xl z-50 overflow-hidden animate-fade-in">
          {/* Search */}
          <div className="p-2 border-b border-border">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search..."
              className="w-full px-2.5 py-1.5 bg-surface-3 border border-border rounded text-xs text-text-primary placeholder-text-muted focus:outline-none focus:border-accent"
              autoFocus
            />
          </div>

          {/* Sectors */}
          <div className="flex gap-1 px-2 py-1.5 border-b border-border overflow-x-auto">
            {SECTORS.map(sector => (
              <button
                key={sector}
                onClick={() => { setActiveSector(sector); setQuery(''); }}
                className={`px-2 py-0.5 rounded text-xxs font-medium whitespace-nowrap transition-colors ${
                  activeSector === sector
                    ? 'bg-accent text-white'
                    : 'bg-surface-3 text-text-muted hover:text-text-secondary'
                }`}
              >
                {sector}
              </button>
            ))}
          </div>

          {/* List */}
          <div className="max-h-64 overflow-y-auto">
            {filtered.map(company => (
              <button
                key={company.ticker}
                onClick={() => { onSelect(company.ticker); setIsOpen(false); setQuery(''); }}
                className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-colors ${
                  company.ticker === currentTicker
                    ? 'bg-accent/10'
                    : 'hover:bg-surface-3'
                }`}
              >
                <div className={`w-7 h-7 rounded flex items-center justify-center text-xxs font-semibold shrink-0 ${
                  company.ticker === currentTicker ? 'bg-accent text-white' : 'bg-surface-4 text-text-muted'
                }`}>
                  {company.ticker.slice(0, 2)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-semibold text-text-primary">{company.ticker}</span>
                    <span className="text-xxs text-text-muted">{company.sector}</span>
                  </div>
                  <p className="text-xxs text-text-muted truncate">{company.name}</p>
                </div>
                {company.marketCap && (
                  <span className="text-xxs text-text-muted shrink-0">{company.marketCap}</span>
                )}
              </button>
            ))}
            {filtered.length === 0 && (
              <div className="px-3 py-6 text-center text-xxs text-text-muted">No results</div>
            )}
          </div>

          {/* Custom ticker */}
          {query && !POPULAR_STOCKS.find(c => c.ticker.toLowerCase() === query.toLowerCase()) && (
            <div className="p-2 border-t border-border">
              <button
                onClick={() => { onSelect(query.toUpperCase()); setIsOpen(false); setQuery(''); }}
                className="w-full px-3 py-1.5 bg-accent text-white rounded text-xs font-medium hover:bg-accent-hover transition-colors"
              >
                Search "{query.toUpperCase()}" →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
