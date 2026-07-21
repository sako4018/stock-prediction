import { useState } from 'react'
import { ThemeProvider, useTheme } from './ThemeContext'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import PredictionPanel from './components/PredictionPanel'
import SignalsPanel from './components/SignalsPanel'
import BacktestPanel from './components/BacktestPanel'
import StockChart from './components/StockChart'
import CompanyInfo from './components/CompanyInfo'
import FundamentalsPanel from './components/FundamentalsPanel'
import MultiTimeframePanel from './components/MultiTimeframePanel'
import AlertsPanel from './components/AlertsPanel'
import TickerTape from './components/TickerTape'

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
            <div className="space-y-4">
              <SignalsPanel ticker={ticker} />
              <AlertsPanel ticker={ticker} />
            </div>
          </div>
        )
      case 'portfolio':
        return <PortfolioView />
      case 'fundamentals':
        return (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <FundamentalsPanel ticker={ticker} />
            <MultiTimeframePanel ticker={ticker} />
          </div>
        )
      default:
        return <Dashboard ticker={ticker} />
    }
  }

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar
        onSelect={setTicker}
        currentTicker={ticker}
        activeView={activeView}
        onViewChange={setActiveView}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <TickerTape />
        <header className="h-12 border-b border-line flex items-center justify-between px-4 bg-surface-alt shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-txt">{ticker}</h2>
            <CompanyInfo ticker={ticker} compact />
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-up animate-pulse-dot" />
              <span className="text-xxs text-txt-dim">Live • 30s</span>
            </div>
            <button
              onClick={toggleTheme}
              className="p-1.5 rounded hover:bg-surface-overlay text-txt-muted hover:text-txt-dim transition-colors"
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
      <div className="bg-surface-alt border border-line rounded-lg p-5">
        <h3 className="text-xs font-semibold text-txt-muted uppercase tracking-wider mb-4">Portfolio Overview</h3>
        {portfolio ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Total Value', value: `$${portfolio.total_portfolio_value?.toLocaleString()}`, color: 'text-txt' },
              { label: 'Cash', value: `$${portfolio.current_cash?.toLocaleString()}`, color: 'text-txt' },
              { label: 'Invested', value: `$${portfolio.total_invested?.toLocaleString()}`, color: 'text-txt-dim' },
              { label: 'Return', value: `${portfolio.total_return >= 0 ? '+' : ''}${portfolio.total_return?.toFixed(2)}%`, color: portfolio.total_return >= 0 ? 'text-up' : 'text-down' },
            ].map((item, i) => (
              <div key={i} className="bg-surface-elevated rounded-lg p-3">
                <p className="text-xxs text-txt-muted uppercase tracking-wider mb-1">{item.label}</p>
                <p className={`text-lg font-semibold tabular-nums ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-txt-muted py-6 text-center">Loading portfolio...</p>
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
