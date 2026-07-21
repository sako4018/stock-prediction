import { useState, useRef, useEffect } from 'react'
import { POPULAR_STOCKS, SECTORS, searchCompanies, Company } from '../data/companies'
import { useTheme } from '../ThemeContext'

interface CompanySelectorProps {
  onSelect: (ticker: string) => void
  currentTicker: string
}

export default function CompanySelector({ onSelect, currentTicker }: CompanySelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeSector, setActiveSector] = useState('All')
  const { theme } = useTheme()
  const isDark = theme === 'dark'
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
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-3 px-4 py-2 rounded-lg border transition-all ${
          isDark
            ? 'bg-dark-bg border-dark-border hover:border-stock-blue'
            : 'bg-white border-gray-200 hover:border-blue-400'
        }`}
      >
        <div className="w-8 h-8 bg-stock-blue/20 rounded-lg flex items-center justify-center">
          <span className="text-sm font-bold text-stock-blue">{currentTicker.slice(0, 2)}</span>
        </div>
        <div className="text-left">
          <p className="font-semibold text-sm">{currentTicker}</p>
          <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
            {currentCompany?.name || 'Custom ticker'}
          </p>
        </div>
        <svg className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''} ${isDark ? 'text-gray-400' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className={`absolute top-full left-0 mt-2 w-96 rounded-xl border shadow-2xl z-50 overflow-hidden ${
          isDark ? 'bg-dark-card border-dark-border' : 'bg-white border-gray-200'
        }`}>
          {/* Search */}
          <div className={`p-3 border-b ${isDark ? 'border-dark-border' : 'border-gray-200'}`}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search company or ticker..."
              className={`w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-stock-blue ${
                isDark ? 'bg-dark-bg text-white' : 'bg-gray-100 text-gray-900'
              }`}
              autoFocus
            />
          </div>

          {/* Sector Tabs */}
          <div className={`flex gap-1 px-3 py-2 border-b overflow-x-auto ${isDark ? 'border-dark-border' : 'border-gray-200'}`}>
            {SECTORS.map(sector => (
              <button
                key={sector}
                onClick={() => { setActiveSector(sector); setQuery(''); }}
                className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                  activeSector === sector
                    ? 'bg-stock-blue text-white'
                    : isDark ? 'bg-dark-bg text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-900'
                }`}
              >
                {sector}
              </button>
            ))}
          </div>

          {/* Company List */}
          <div className="max-h-80 overflow-y-auto">
            {filtered.map(company => (
              <button
                key={company.ticker}
                onClick={() => {
                  onSelect(company.ticker)
                  setIsOpen(false)
                  setQuery('')
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                  company.ticker === currentTicker
                    ? isDark ? 'bg-stock-blue/20' : 'bg-blue-50'
                    : isDark ? 'hover:bg-dark-bg' : 'hover:bg-gray-50'
                }`}
              >
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-sm ${
                  company.ticker === currentTicker ? 'bg-stock-blue text-white' : 'bg-dark-bg text-stock-blue'
                }`}>
                  {company.ticker.slice(0, 2)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">{company.ticker}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      isDark ? 'bg-dark-bg text-gray-400' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {company.sector}
                    </span>
                  </div>
                  <p className={`text-xs truncate ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                    {company.name} {company.country}
                  </p>
                </div>
                {company.marketCap && (
                  <span className={`text-xs font-medium ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                    {company.marketCap}
                  </span>
                )}
              </button>
            ))}
            {filtered.length === 0 && (
              <div className={`px-4 py-8 text-center text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                No companies found. Try a different search.
              </div>
            )}
          </div>

          {/* Custom Ticker */}
          {query && !POPULAR_STOCKS.find(c => c.ticker.toLowerCase() === query.toLowerCase()) && (
            <div className={`p-3 border-t ${isDark ? 'border-dark-border' : 'border-gray-200'}`}>
              <button
                onClick={() => {
                  onSelect(query.toUpperCase())
                  setIsOpen(false)
                  setQuery('')
                }}
                className="w-full px-4 py-2 bg-stock-blue text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
              >
                Search for "{query.toUpperCase()}" →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
