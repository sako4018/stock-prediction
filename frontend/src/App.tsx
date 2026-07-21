import { useState } from 'react'
import { ThemeProvider, useTheme } from './ThemeContext'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import PredictionPanel from './components/PredictionPanel'
import SignalsPanel from './components/SignalsPanel'
import BacktestPanel from './components/BacktestPanel'
import StockChart from './components/StockChart'
import CompanyInfo from './components/CompanyInfo'

function AppContent() {
  const [ticker, setTicker] = useState<string>('AAPL')
  const [activeView, setActiveView] = useState<string>('dashboard')
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard ticker={ticker} />
      case 'predict':
        return (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
            <div className="xl:col-span-2">
              <StockChart ticker={ticker} />
            </div>
            <div>
              <PredictionPanel ticker={ticker} />
            </div>
          </div>
        )
      case 'backtest':
        return <BacktestPanel ticker={ticker} />
      case 'signals':
        return (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
            <div className="xl:col-span-2">
              <StockChart ticker={ticker} />
            </div>
            <div>
              <SignalsPanel ticker={ticker} />
            </div>
          </div>
        )
      case 'portfolio':
        return <PortfolioView />
      default:
        return <Dashboard ticker={ticker} />
    }
  }

  return (
    <div className="flex min-h-screen bg-surface-0">
      <Sidebar
        onSelect={setTicker}
        currentTicker={ticker}
        activeView={activeView}
        onViewChange={setActiveView}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-12 border-b border-frame flex items-center justify-between px-4 bg-surface-1 shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-label">{ticker}</h2>
            <CompanyInfo ticker={ticker} compact />
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-up animate-pulse-dot" />
              <span className="text-xxs text-label-muted">Market Data</span>
            </div>
            <button
              onClick={toggleTheme}
              className="p-1.5 rounded hover:bg-surface-3 text-label-muted hover:text-label-dim transition-colors"
            >
              {isDark ? '☀' : '☾'}
            </button>
          </div>
        </header>
        <main className="flex-1 p-4 overflow-y-auto">
          {renderView()}
        </main>
      </div>
    </div>
  )
}

function PortfolioView() {
  const [portfolio, setPortfolio] = useState<any>(null)

  useState(() => {
    fetch('/api/portfolio')
      .then(r => r.json())
      .then(setPortfolio)
      .catch(console.error)
  })

  return (
    <div className="space-y-4">
      <div className="bg-surface-1 border border-frame rounded-lg p-5">
        <h3 className="text-xs font-semibold text-label-muted uppercase tracking-wider mb-4">Portfolio Overview</h3>
        {portfolio ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Total Value', value: `$${portfolio.total_portfolio_value?.toLocaleString()}`, color: 'text-label' },
              { label: 'Cash', value: `$${portfolio.current_cash?.toLocaleString()}`, color: 'text-label' },
              { label: 'Invested', value: `$${portfolio.total_invested?.toLocaleString()}`, color: 'text-label-dim' },
              { label: 'Return', value: `${portfolio.total_return >= 0 ? '+' : ''}${portfolio.total_return?.toFixed(2)}%`, color: portfolio.total_return >= 0 ? 'text-up' : 'text-down' },
            ].map((item, i) => (
              <div key={i} className="bg-surface-2 rounded-lg p-3">
                <p className="text-xxs text-label-muted uppercase tracking-wider mb-1">{item.label}</p>
                <p className={`text-lg font-semibold tabular-nums ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-label-muted py-6 text-center">Loading portfolio...</p>
        )}
      </div>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  )
}

export default App
