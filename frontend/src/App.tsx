import { useState, useEffect } from 'react'
import { ThemeProvider, useTheme } from './ThemeContext'
import Dashboard from './components/Dashboard'
import PredictionPanel from './components/PredictionPanel'
import SignalsPanel from './components/SignalsPanel'
import BacktestPanel from './components/BacktestPanel'
import StockChart from './components/StockChart'
import FundamentalsPanel from './components/FundamentalsPanel'
import MultiTimeframePanel from './components/MultiTimeframePanel'
import KeyStats from './components/KeyStats'
import NewsPanel from './components/NewsPanel'
import MarketPanel from './components/MarketPanel'
import AlertsPanel from './components/AlertsPanel'
import PortfolioOptimizer from './components/PortfolioOptimizer'
import BatchTrainPanel from './components/BatchTrainPanel'
import HeroPrice from './components/HeroPrice'
import ErrorBoundary from './components/ErrorBoundary'
import SplitFlap from './components/SplitFlap'
import StockSearch from './components/StockSearch'
import PlatformNav, { VIEWS } from './components/PlatformNav'

function AppContent() {
  const [ticker, setTicker] = useState('AAPL')
  const [activeView, setActiveView] = useState('dashboard')
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === 'INPUT') return
      const view = VIEWS.find(v => v.key === e.key)
      if (view) { e.preventDefault(); setActiveView(view.id) }
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
          <div className="space-y-4">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              <FundamentalsPanel ticker={ticker} />
              <KeyStats ticker={ticker} />
              <MultiTimeframePanel ticker={ticker} />
              <MarketPanel />
            </div>
            <NewsPanel ticker={ticker} />
          </div>
        )
      default: return <Dashboard ticker={ticker} />
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-app)' }}>
      <header className="flex flex-wrap items-center justify-between gap-3 px-4 lg:px-8 py-3 shrink-0" style={{
        background: 'var(--bg-header)',
        borderBottom: '1px solid rgb(var(--color-line))',
      }}>
        <div className="flex items-center gap-3 lg:gap-6 min-w-0">
          <h1 className="text-xl lg:text-3xl leading-none"><SplitFlap text={ticker} /></h1>
          <div className="hidden sm:block"><HeroPrice ticker={ticker} /></div>
        </div>

        <div className="flex items-center gap-2 lg:gap-3">
          <StockSearch onSelect={setTicker} />
          <button
            onClick={toggleTheme}
            aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all"
            style={{
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
            <span className="hidden sm:inline">{isDark ? 'Light' : 'Dark'}</span>
          </button>
        </div>
      </header>

      <PlatformNav active={activeView} onChange={setActiveView} />

      <main className="flex-1 p-4 lg:p-8" style={{ background: 'var(--bg-app)' }}>
        {renderView()}
      </main>
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
