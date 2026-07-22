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

const VIEW_KEYS: Record<string, string> = { '1': 'dashboard', '2': 'predict', '3': 'backtest', '4': 'signals', '5': 'fundamentals', '6': 'portfolio' }

function AppContent() {
  const [ticker, setTicker] = useState<string>('AAPL')
  const [activeView, setActiveView] = useState<string>('dashboard')
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === 'INPUT' || (e.target as HTMLElement).tagName === 'TEXTAREA') return
      if (VIEW_KEYS[e.key]) { e.preventDefault(); setActiveView(VIEW_KEYS[e.key]) }
      if (e.key === '/') { e.preventDefault(); document.querySelector<HTMLInputElement>('[placeholder*="Search"]')?.focus() }
      if (e.key === 't') { e.preventDefault(); toggleTheme() }
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [toggleTheme])

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard ticker={ticker} />
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
      case 'backtest':
        return <BacktestPanel ticker={ticker} />
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
    <div className="flex min-h-screen" style={{ background: 'var(--bg-app)' }}>
      <Sidebar
        onSelect={setTicker}
        currentTicker={ticker}
        activeView={activeView}
        onViewChange={setActiveView}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header — editorial: large ticker, minimal controls */}
        <div className="h-16 flex items-center justify-between px-8 shrink-0" style={{
          background: 'var(--bg-header)',
          borderBottom: '1px solid rgb(var(--color-line))',
        }}>
          <div className="flex items-center gap-6">
            <h1 className="text-4xl font-bold tracking-tight" style={{
              fontFamily: '"Space Grotesk", system-ui, sans-serif',
              color: 'rgb(var(--color-txt))',
              letterSpacing: '-0.02em',
            }}>{ticker}</h1>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded" style={{
              background: 'rgb(var(--color-up) / 0.08)',
              border: '1px solid rgb(var(--color-up) / 0.15)',
            }}>
              <span className="w-1.5 h-1.5 rounded-full bg-up animate-pulse-dot" />
              <span className="text-xxs font-medium text-up" style={{ fontFamily: '"JetBrains Mono", monospace' }}>LIVE</span>
            </div>
            <div className="w-px h-8" style={{ background: 'rgb(var(--color-line))' }} />
            <HeroPrice ticker={ticker} />
          </div>

          <div className="flex items-center gap-3">
            <div className="px-2.5 py-1 rounded text-xxs font-semibold" style={{
              fontFamily: '"Space Grotesk", system-ui, sans-serif',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              background: 'rgb(var(--color-accent) / 0.08)',
              color: 'rgb(var(--color-accent))',
              border: '1px solid rgb(var(--color-accent) / 0.15)',
            }}>
              {activeView}
            </div>
            <button
              onClick={toggleTheme}
              className="w-8 h-8 flex items-center justify-center rounded transition-all"
              style={{
                background: 'rgb(var(--color-surface-elevated))',
                color: 'rgb(var(--color-txt-sec))',
                border: '1px solid rgb(var(--color-line))',
              }}
              title={isDark ? 'Switch to light' : 'Switch to dark'}
            >
              {isDark ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="4" />
                  <path d="M12 2v2" /><path d="M12 20v2" /><path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" /><path d="M2 12h2" /><path d="M20 12h2" /><path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" />
                </svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
                </svg>
              )}
            </button>
          </div>
        </div>

        <TickerTape />
        <main className="flex-1 p-8 overflow-y-auto" style={{ background: 'var(--bg-app)' }}>
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
      <PortfolioOptimizer />
      <div className="card p-6">
        <h3 className="section-header">Portfolio Overview</h3>
        {portfolio ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Total Value', value: `$${portfolio.total_portfolio_value?.toLocaleString()}`, cls: '' },
              { label: 'Cash', value: `$${portfolio.current_cash?.toLocaleString()}`, cls: '' },
              { label: 'Invested', value: `$${portfolio.total_invested?.toLocaleString()}`, cls: 'txt-dim' },
              { label: 'Return', value: `${portfolio.total_return >= 0 ? '+' : ''}${portfolio.total_return?.toFixed(2)}%`, cls: portfolio.total_return >= 0 ? 'up' : 'down' },
            ].map((item, i) => (
              <div key={i} className="rounded p-4" style={{ background: 'rgb(var(--color-surface-elevated))', border: '1px solid rgb(var(--color-line))' }}>
                <p className="text-xxs uppercase tracking-wider mb-1.5" style={{ fontFamily: '"Space Grotesk", system-ui, sans-serif', color: 'rgb(var(--color-txt-muted))' }}>{item.label}</p>
                <p className={`text-xl font-bold tabular-nums ${item.cls ? `text-${item.cls}` : ''}`} style={{ fontFamily: '"JetBrains Mono", monospace', color: item.cls ? undefined : 'rgb(var(--color-txt))' }}>{item.value}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm py-6 text-center" style={{ color: 'rgb(var(--color-txt-dim))' }}>Loading portfolio...</p>
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
