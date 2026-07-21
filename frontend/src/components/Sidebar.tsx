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
  return (
    <aside className="w-56 h-screen bg-surface-alt border-r border-line flex flex-col shrink-0 overflow-visible">
      {/* Brand */}
      <div className="h-12 border-b border-line flex items-center px-4 gap-2.5 shrink-0">
        <svg width="22" height="22" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <line x1="4.5" y1="2" x2="4.5" y2="5" stroke="#3B82F6" strokeWidth="1.2" strokeLinecap="round" />
          <rect x="3" y="5" width="3" height="8" rx="0.5" fill="#3B82F6" />
          <line x1="4.5" y1="13" x2="4.5" y2="16" stroke="#3B82F6" strokeWidth="1.2" strokeLinecap="round" />
          <line x1="9.5" y1="0.5" x2="9.5" y2="3" stroke="#2962FF" strokeWidth="1.2" strokeLinecap="round" />
          <rect x="8" y="3" width="3" height="12" rx="0.5" fill="#2962FF" />
          <line x1="9.5" y1="15" x2="9.5" y2="18" stroke="#2962FF" strokeWidth="1.2" strokeLinecap="round" />
          <line x1="14.5" y1="3.5" x2="14.5" y2="6" stroke="#3B82F6" strokeWidth="1.2" strokeLinecap="round" />
          <rect x="13" y="6" width="3" height="7" rx="0.5" fill="#3B82F6" />
          <line x1="14.5" y1="13" x2="14.5" y2="15.5" stroke="#3B82F6" strokeWidth="1.2" strokeLinecap="round" />
        </svg>
        <span className="text-sm font-semibold text-txt tracking-tight">StockPredict</span>
      </div>

      {/* Company Selector */}
      <div className="p-3 border-b border-line relative z-[100]">
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
                : 'text-txt-dim hover:text-txt hover:bg-surface-overlay'
            }`}
          >
            <span className="text-xs w-4 text-center opacity-60">{item.icon}</span>
            {item.label}
            <span className="ml-auto text-xxs text-txt-dim opacity-0 group-hover:opacity-100 transition-opacity">{item.key}</span>
          </button>
        ))}
      </nav>

      {/* Watchlist */}
      <div className="flex-1 overflow-y-auto p-3 border-t border-line">
        <Watchlist onSelect={onSelect} currentTicker={currentTicker} />
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-line">
        <div className="flex items-center gap-1.5 text-xxs text-txt-muted">
          <span className="w-1.5 h-1.5 rounded-full bg-up animate-pulse-dot" />
          Connected
        </div>
      </div>
    </aside>
  )
}
