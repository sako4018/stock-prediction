import { useState, useEffect } from 'react'
import { ThemeProvider, useTheme } from './ThemeContext'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import PredictionPanel from './components/PredictionPanel'
import SignalsPanel from './components/SignalsPanel'
import BacktestPanel from './components/BacktestPanel'
import StockChart from './components/StockChart'
import FundamentalsPanel from './components/FundamentalsPanel'
import MultiTimeframePanel from './components/MultiTimeframePanel'
import AlertsPanel from './components/AlertsPanel'
import TickerTape from './components/TickerTape'
import PortfolioOptimizer from './components/PortfolioOptimizer'
import BatchTrainPanel from './components/BatchTrainPanel'
import HeroPrice from './components/HeroPrice'
import ErrorBoundary from './components/ErrorBoundary'

const VIEW_KEYS: Record<string, string> = { '1': 'dashboard', '2': 'predict', '3': 'backtest', '4': 'signals', '5': 'fundamentals', '6': 'portfolio' }

function AppContent() {
  const [ticker, setTicker] = useState('AAPL')
  const [activeView, setActiveView] = useState('dashboard')
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === 'INPUT') return
      if (VIEW_KEYS[e.key]) { e.preventDefault(); setActiveView(VIEW_KEYS[e.key]) }
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [])

  const renderView = () => {
    switch (activeView) {
      case 'dashboard': return <Dashboard ticker={ticker} />
      case 'predict':
        return (
          <div className="space-y-4">
            <StockChart ticker={ticker} />
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
              <div className="xl:col-span-2"><PredictionPanel ticker={ticker} /></div>
              <div><BatchTrainPanel /></div>
            </div>
          </div>
        )
      case 'backtest': return <BacktestPanel ticker={ticker} />
      case 'signals':
        return (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
            <div className="xl:col-span-2"><StockChart ticker={ticker} /></div>
            <div className="space-y-4">
              <SignalsPanel ticker={ticker} />
              <AlertsPanel ticker={ticker} />
            </div>
          </div>
        )
      case 'portfolio': return <PortfolioOptimizer />
      case 'fundamentals':
        return (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <FundamentalsPanel ticker={ticker} />
            <MultiTimeframePanel ticker={ticker} />
          </div>
        )
      default: return <Dashboard ticker={ticker} />
    }
  }

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg-app)' }}>
      <Sidebar
        onSelect={setTicker}
        currentTicker={ticker}
        activeView={activeView}
        onViewChange={setActiveView}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="h-14 lg:h-16 flex items-center justify-between px-4 lg:px-8 shrink-0" style={{
          background: 'var(--bg-header)',
          borderBottom: '1px solid rgb(var(--color-line))',
        }}>
          <div className="flex items-center gap-3 lg:gap-6">
            {/* Mobile hamburger */}
            <button onClick={() => {}} className="lg:hidden w-8 h-8 flex items-center justify-center rounded"
              style={{ color: 'rgb(var(--color-txt))' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 12h18M3 6h18M3 18h18" />
              </svg>
            </button>
            <h1 className="text-2xl lg:text-4xl font-bold tracking-tight" style={{
              fontFamily: '"Space Grotesk", system-ui, sans-serif',
              color: 'rgb(var(--color-txt))',
              letterSpacing: '-0.02em',
            }}>{ticker}</h1>
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded" style={{
              background: 'rgb(var(--color-up) / 0.08)',
              border: '1px solid rgb(var(--color-up) / 0.15)',
            }}>
              <span className="w-1.5 h-1.5 rounded-full animate-pulse-dot" style={{ background: 'rgb(var(--color-up))' }} />
              <span className="text-xxs font-medium" style={{ color: 'rgb(var(--color-up))', fontFamily: '"JetBrains Mono", monospace' }}>LIVE</span>
            </div>
            <div className="hidden sm:block w-px h-8" style={{ background: 'rgb(var(--color-line))' }} />
            <div className="hidden sm:block"><HeroPrice ticker={ticker} /></div>
          </div>

          <div className="flex items-center gap-2 lg:gap-3">
            {/* Theme toggle button */}
            <button
              onClick={toggleTheme}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
              style={{
                fontFamily: '"Space Grotesk", system-ui, sans-serif',
                background: isDark ? 'rgb(var(--color-accent) / 0.1)' : 'rgb(var(--color-surface-elevated))',
                color: isDark ? 'rgb(var(--color-accent))' : 'rgb(var(--color-txt-sec))',
                border: `1px solid ${isDark ? 'rgb(var(--color-accent) / 0.2)' : 'rgb(var(--color-line))'}`,
              }}
            >
              {isDark ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="4" /><path d="M12 2v2" /><path d="M12 20v2" /><path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" /><path d="M2 12h2" /><path d="M20 12h2" /><path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" />
                </svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
                </svg>
              )}
              {isDark ? 'Light' : 'Dark'}
            </button>
          </div>
        </div>

        <TickerTape />
        <main className="flex-1 p-4 lg:p-8 overflow-y-auto" style={{ background: 'var(--bg-app)' }}>
          {renderView()}
        </main>
      </div>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <ErrorBoundary>
        <AppContent />
      </ErrorBoundary>
    </ThemeProvider>
  )
}

export default App
