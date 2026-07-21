import { useState } from 'react'
import { useTheme } from '../ThemeContext'
import CompanySelector from './CompanySelector'
import Watchlist from './Watchlist'

interface SidebarProps {
  onSelect: (ticker: string) => void
  currentTicker: string
  activeView: string
  onViewChange: (view: string) => void
}

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Overview', icon: '◫' },
  { id: 'predict', label: 'Predict', icon: '◉' },
  { id: 'backtest', label: 'Backtest', icon: '⊞' },
  { id: 'signals', label: 'Signals', icon: '◎' },
  { id: 'portfolio', label: 'Portfolio', icon: '▤' },
]

export default function Sidebar({ onSelect, currentTicker, activeView, onViewChange }: SidebarProps) {
  return (
    <aside className="w-56 h-screen bg-surface-1 border-r border-border flex flex-col shrink-0">
      {/* Brand */}
      <div className="h-12 border-b border-border flex items-center px-4 gap-2.5 shrink-0">
        <div className="w-6 h-6 rounded bg-accent flex items-center justify-center">
          <span className="text-white text-xs font-bold">S</span>
        </div>
        <div>
          <span className="text-sm font-semibold text-text-primary tracking-tight">StockPredict</span>
        </div>
      </div>

      {/* Company Selector */}
      <div className="p-3 border-b border-border">
        <CompanySelector onSelect={onSelect} currentTicker={currentTicker} />
      </div>

      {/* Navigation */}
      <nav className="p-2 space-y-0.5">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            onClick={() => onViewChange(item.id)}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded text-sm transition-colors ${
              activeView === item.id
                ? 'bg-accent/10 text-accent font-medium'
                : 'text-text-secondary hover:text-text-primary hover:bg-surface-3'
            }`}
          >
            <span className="text-xs w-4 text-center opacity-60">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Watchlist */}
      <div className="flex-1 overflow-y-auto p-3 border-t border-border">
        <Watchlist onSelect={onSelect} currentTicker={currentTicker} />
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-border">
        <div className="flex items-center gap-1.5 text-xxs text-text-muted">
          <span className="w-1.5 h-1.5 rounded-full bg-up animate-pulse-dot" />
          Connected
        </div>
      </div>
    </aside>
  )
}
