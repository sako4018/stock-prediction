import { useState } from 'react'
import { ThemeProvider, useTheme } from './ThemeContext'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import PredictionPanel from './components/PredictionPanel'
import SignalsPanel from './components/SignalsPanel'
import BacktestPanel from './components/BacktestPanel'
import StockChart from './components/StockChart'

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
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PredictionPanel ticker={ticker} />
            <StockChart ticker={ticker} />
          </div>
        )
      case 'backtest':
        return <BacktestPanel ticker={ticker} />
      case 'signals':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SignalsPanel ticker={ticker} />
            <StockChart ticker={ticker} />
          </div>
        )
      case 'portfolio':
        return <PortfolioView />
      default:
        return <Dashboard ticker={ticker} />
    }
  }

  return (
    <div className={`flex min-h-screen transition-colors duration-300 ${
      isDark ? 'bg-dark-bg' : 'bg-gray-50'
    }`}>
      {/* Sidebar */}
      <Sidebar
        onSelect={setTicker}
        currentTicker={ticker}
        activeView={activeView}
        onViewChange={setActiveView}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <header className={`flex items-center justify-between px-6 py-3 border-b ${
          isDark ? 'bg-dark-card/80 border-dark-border' : 'bg-white/80 border-gray-200'
        }`}>
          <div>
            <h2 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {ticker}
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-lg transition-colors ${
                isDark ? 'bg-dark-bg hover:bg-dark-border' : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              {isDark ? '☀️' : '🌙'}
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-6 overflow-y-auto">
          {renderView()}
        </main>
      </div>
    </div>
  )
}

function PortfolioView() {
  const [portfolio, setPortfolio] = useState<any>(null)
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  useState(() => {
    fetch('/api/portfolio')
      .then(r => r.json())
      .then(setPortfolio)
      .catch(console.error)
  })

  return (
    <div className="space-y-6">
      <div className={`rounded-xl border p-6 ${isDark ? 'bg-dark-card border-dark-border' : 'bg-white border-gray-200'}`}>
        <h3 className="text-lg font-bold mb-4">💼 Portfolio Overview</h3>
        {portfolio ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className={`p-4 rounded-lg ${isDark ? 'bg-dark-bg' : 'bg-gray-50'}`}>
              <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Total Value</p>
              <p className="text-xl font-bold">${portfolio.total_portfolio_value?.toLocaleString()}</p>
            </div>
            <div className={`p-4 rounded-lg ${isDark ? 'bg-dark-bg' : 'bg-gray-50'}`}>
              <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Cash</p>
              <p className="text-xl font-bold">${portfolio.current_cash?.toLocaleString()}</p>
            </div>
            <div className={`p-4 rounded-lg ${isDark ? 'bg-dark-bg' : 'bg-gray-50'}`}>
              <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Invested</p>
              <p className="text-xl font-bold">${portfolio.total_invested?.toLocaleString()}</p>
            </div>
            <div className={`p-4 rounded-lg ${isDark ? 'bg-dark-bg' : 'bg-gray-50'}`}>
              <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Return</p>
              <p className={`text-xl font-bold ${portfolio.total_return >= 0 ? 'text-stock-green' : 'text-stock-red'}`}>
                {portfolio.total_return >= 0 ? '+' : ''}{portfolio.total_return?.toFixed(2)}%
              </p>
            </div>
          </div>
        ) : (
          <p className={`text-center py-8 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Loading portfolio...</p>
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
