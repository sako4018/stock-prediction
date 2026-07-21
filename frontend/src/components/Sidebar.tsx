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
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'predict', label: 'Predict', icon: '🤖' },
  { id: 'backtest', label: 'Backtest', icon: '📈' },
  { id: 'portfolio', label: 'Portfolio', icon: '💼' },
  { id: 'signals', label: 'Signals', icon: '📡' },
]

export default function Sidebar({ onSelect, currentTicker, activeView, onViewChange }: SidebarProps) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <aside className={`w-64 min-h-screen border-r flex flex-col ${
      isDark ? 'bg-dark-card border-dark-border' : 'bg-white border-gray-200'
    }`}>
      {/* Logo */}
      <div className={`p-4 border-b ${isDark ? 'border-dark-border' : 'border-gray-200'}`}>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-stock-blue rounded-lg flex items-center justify-center">
            <span className="text-lg">📈</span>
          </div>
          <div>
            <h1 className="font-bold text-sm">StockPredict</h1>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>ML Trading Platform</p>
          </div>
        </div>
      </div>

      {/* Company Selector */}
      <div className="p-3">
        <CompanySelector onSelect={onSelect} currentTicker={currentTicker} />
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2">
        <p className={`text-xs font-medium mb-2 px-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>NAVIGATION</p>
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            onClick={() => onViewChange(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors mb-1 ${
              activeView === item.id
                ? 'bg-stock-blue/20 text-stock-blue'
                : isDark ? 'text-gray-400 hover:text-white hover:bg-dark-bg' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Watchlist */}
      <div className="p-3">
        <Watchlist onSelect={onSelect} currentTicker={currentTicker} />
      </div>

      {/* Status */}
      <div className={`p-4 border-t ${isDark ? 'border-dark-border' : 'border-gray-200'}`}>
        <div className="flex items-center gap-2 text-xs">
          <span className="w-2 h-2 bg-stock-green rounded-full pulse-live"></span>
          <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>Market Open</span>
        </div>
      </div>
    </aside>
  )
}
