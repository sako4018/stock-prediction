import { useState, useRef, useEffect } from 'react'
import { POPULAR_STOCKS, SECTORS, searchCompanies } from '../data/companies'
import { createPortal } from 'react-dom'

interface CompanySelectorProps {
  onSelect: (ticker: string) => void
  currentTicker: string
}

export default function CompanySelector({ onSelect, currentTicker }: CompanySelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeSector, setActiveSector] = useState('All')
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0, width: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const filtered = query
    ? searchCompanies(query)
    : activeSector === 'All'
      ? POPULAR_STOCKS
      : POPULAR_STOCKS.filter(c => c.sector === activeSector)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        dropdownRef.current && !dropdownRef.current.contains(e.target as Node) &&
        buttonRef.current && !buttonRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false)
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setIsOpen(false)
    }
    function handleScroll(e: Event) {
      // Only close if scroll happens OUTSIDE the dropdown
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleKeyDown)
    window.addEventListener('scroll', handleScroll, true)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('scroll', handleScroll, true)
    }
  }, [])

  const openDropdown = () => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      setDropdownPos({
        top: rect.bottom + 4,
        left: rect.left,
        width: Math.max(rect.width, 320)
      })
    }
    setIsOpen(!isOpen)
  }

  const currentCompany = POPULAR_STOCKS.find(c => c.ticker === currentTicker)

  return (
    <>
      <button
        ref={buttonRef}
        onClick={openDropdown}
        className="w-full flex items-center gap-2.5 px-3 py-2 rounded bg-surface-overlay border border-line hover:border-line-light transition-colors text-left"
      >
        <div className="w-7 h-7 rounded bg-accent/15 flex items-center justify-center shrink-0">
          <span className="text-xxs font-semibold text-accent">{currentTicker.slice(0, 2)}</span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-txt">{currentTicker}</p>
          <p className="text-xxs text-txt-muted truncate">{currentCompany?.name || 'Custom'}</p>
        </div>
        <svg className={`w-3.5 h-3.5 text-txt-muted shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && createPortal(
        <div
          ref={dropdownRef}
          className="bg-surface-elevated border border-line rounded-lg shadow-2xl overflow-hidden animate-fade-in"
          style={{
            position: 'fixed',
            top: dropdownPos.top,
            left: dropdownPos.left,
            width: dropdownPos.width,
            zIndex: 9999
          }}
        >
          {/* Search */}
          <div className="p-2 border-b border-line">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search company or ticker..."
              className="w-full px-2.5 py-1.5 bg-surface-overlay border border-line rounded text-xs text-txt placeholder-txt-dim focus:outline-none focus:border-accent"
              autoFocus
            />
          </div>

          {/* Sectors */}
          <div className="flex gap-1 px-2 py-1.5 border-b border-line overflow-x-auto">
            {SECTORS.map(sector => (
              <button
                key={sector}
                onClick={() => { setActiveSector(sector); setQuery(''); }}
                className={`px-2 py-0.5 rounded text-xxs font-medium whitespace-nowrap transition-colors ${
                  activeSector === sector
                    ? 'bg-accent text-white'
                    : 'bg-surface-overlay text-txt-muted hover:text-txt-dim'
                }`}
              >
                {sector}
              </button>
            ))}
          </div>

          {/* Company List */}
          <div className="max-h-72 overflow-y-auto">
            {filtered.map(company => (
              <button
                key={company.ticker}
                onClick={() => { onSelect(company.ticker); setIsOpen(false); setQuery(''); }}
                className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-colors ${
                  company.ticker === currentTicker
                    ? 'bg-accent/10'
                    : 'hover:bg-surface-overlay'
                }`}
              >
                <div className={`w-7 h-7 rounded flex items-center justify-center text-xxs font-semibold shrink-0 ${
                  company.ticker === currentTicker ? 'bg-accent text-white' : 'bg-surface-hover text-txt-muted'
                }`}>
                  {company.ticker.slice(0, 2)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-semibold text-txt">{company.ticker}</span>
                    <span className="text-xxs text-txt-muted">{company.sector}</span>
                  </div>
                  <p className="text-xxs text-txt-muted truncate">{company.name}</p>
                </div>
                {company.marketCap && (
                  <span className="text-xxs text-txt-muted shrink-0">{company.marketCap}</span>
                )}
              </button>
            ))}
            {filtered.length === 0 && (
              <div className="px-3 py-6 text-center text-xxs text-txt-muted">No results</div>
            )}
          </div>

          {/* Custom ticker */}
          {query && !POPULAR_STOCKS.find(c => c.ticker.toLowerCase() === query.toLowerCase()) && (
            <div className="p-2 border-t border-line">
              <button
                onClick={() => { onSelect(query.toUpperCase()); setIsOpen(false); setQuery(''); }}
                className="w-full px-3 py-1.5 bg-accent text-white rounded text-xs font-medium hover:bg-accent-hover transition-colors"
              >
                Search "{query.toUpperCase()}" →
              </button>
            </div>
          )}
        </div>,
        document.body
      )}
    </>
  )
}
