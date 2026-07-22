import { useState } from 'react'
import CompanySelector from './CompanySelector'
import Watchlist from './Watchlist'

interface SidebarProps {
  onSelect: (ticker: string) => void
  currentTicker: string
  activeView: string
  onViewChange: (view: string) => void
}

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Overview', icon: '◫', key: '1' },
  { id: 'predict', label: 'Predict', icon: '◉', key: '2' },
  { id: 'backtest', label: 'Backtest', icon: '⊞', key: '3' },
  { id: 'signals', label: 'Signals', icon: '◎', key: '4' },
  { id: 'fundamentals', label: 'Analysis', icon: '◈', key: '5' },
  { id: 'portfolio', label: 'Portfolio', icon: '▤', key: '6' },
]

export default function Sidebar({ onSelect, currentTicker, activeView, onViewChange }: SidebarProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <aside
      className="h-screen flex flex-col shrink-0 overflow-visible transition-all duration-300 ease-out"
      style={{
        width: expanded ? '240px' : '56px',
        background: 'rgb(var(--color-surface-alt))',
        borderRight: '1px solid rgb(var(--color-line))',
      }}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      {/* Brand */}
      <div className="h-16 border-b flex items-center px-4 gap-2.5 shrink-0" style={{
        borderColor: 'rgb(var(--color-line))',
        background: 'linear-gradient(135deg, rgb(var(--color-accent) / 0.04), rgb(var(--color-accent-alt) / 0.02))',
      }}>
        <div className="w-7 h-7 rounded flex items-center justify-center shrink-0" style={{
          background: 'linear-gradient(135deg, rgb(var(--color-accent)), rgb(var(--color-accent-alt)))',
        }}>
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
            <rect x="3" y="5" width="3" height="8" rx="0.5" fill="white" opacity="0.9" />
            <rect x="8" y="3" width="3" height="12" rx="0.5" fill="white" opacity="0.9" />
            <rect x="13" y="6" width="3" height="7" rx="0.5" fill="white" opacity="0.9" />
          </svg>
        </div>
        {expanded && (
          <span className="text-sm font-bold gradient-text tracking-tight whitespace-nowrap" style={{
            fontFamily: '"Space Grotesk", system-ui, sans-serif',
          }}>StockPredict</span>
        )}
      </div>

      {/* Company Selector */}
      <div className="p-2 border-b relative z-[100]" style={{ borderColor: 'rgb(var(--color-line))' }}>
        <CompanySelector onSelect={onSelect} currentTicker={currentTicker} expanded={expanded} />
      </div>

      {/* Navigation */}
      <nav className="p-2 space-y-0.5">
        {NAV_ITEMS.map(item => {
          const isActive = activeView === item.id
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className="w-full flex items-center gap-2.5 rounded transition-all duration-200 relative"
              style={{
                padding: expanded ? '0.5rem 0.75rem' : '0.5rem 0',
                justifyContent: expanded ? 'flex-start' : 'center',
                background: isActive ? 'rgb(var(--color-accent) / 0.08)' : 'transparent',
                color: isActive ? 'rgb(var(--color-accent))' : 'rgb(var(--color-txt-dim))',
                fontFamily: '"Space Grotesk", system-ui, sans-serif',
                fontSize: '0.8125rem',
                fontWeight: isActive ? 600 : 400,
              }}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 rounded-r" style={{
                  background: 'rgb(var(--color-accent))',
                }} />
              )}
              <span className="text-sm w-5 text-center shrink-0">{item.icon}</span>
              {expanded && <span className="whitespace-nowrap">{item.label}</span>}
              {expanded && (
                <span className="ml-auto text-xxs opacity-40" style={{ fontFamily: '"JetBrains Mono", monospace' }}>{item.key}</span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Watchlist */}
      <div className="flex-1 overflow-y-auto p-2 border-t" style={{ borderColor: 'rgb(var(--color-line))' }}>
        <Watchlist onSelect={onSelect} currentTicker={currentTicker} expanded={expanded} />
      </div>

      {/* Footer */}
      <div className="p-3 border-t" style={{ borderColor: 'rgb(var(--color-line))' }}>
        <div className="flex items-center gap-1.5 text-xxs" style={{
          color: 'rgb(var(--color-txt-muted))',
          justifyContent: expanded ? 'flex-start' : 'center',
        }}>
          <span className="w-1.5 h-1.5 rounded-full bg-up animate-pulse-dot shrink-0" />
          {expanded && <span>Connected</span>}
        </div>
      </div>
    </aside>
  )
}
