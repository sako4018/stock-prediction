import { useState, useEffect } from 'react'
import { ThemeProvider, useTheme } from './ThemeContext'
import Dashboard from './components/Dashboard'
import PredictionPanel from './components/PredictionPanel'
import SignalsPanel from './components/SignalsPanel'
import BacktestPanel from './components/BacktestPanel'
import StockChart from './components/StockChart'
import FundamentalsPanel from './components/FundamentalsPanel'
import MultiTimeframePanel from './components/MultiTimeframePanel'
import AlertsPanel from './components/AlertsPanel'
import PortfolioOptimizer from './components/PortfolioOptimizer'
import BatchTrainPanel from './components/BatchTrainPanel'
import HeroPrice from './components/HeroPrice'
import ErrorBoundary from './components/ErrorBoundary'

const VIEWS = [
  { id: 'dashboard', key: '1', label: 'OVERVIEW' },
  { id: 'predict', key: '2', label: 'PREDICT' },
  { id: 'backtest', key: '3', label: 'BACKTEST' },
  { id: 'signals', key: '4', label: 'SIGNALS' },
  { id: 'fundamentals', key: '5', label: 'FUNDAMENTALS' },
  { id: 'portfolio', key: '6', label: 'PORTFOLIO' },
]

function AppContent() {
  const [ticker, setTicker] = useState('AAPL')
  const [activeView, setActiveView] = useState('dashboard')
  const [inputTicker, setInputTicker] = useState('')
  const [time, setTime] = useState(new Date())
  const { theme, toggleTheme } = useTheme()

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === 'INPUT') return
      const v = VIEWS.find(v => v.key === e.key)
      if (v) { e.preventDefault(); setActiveView(v.id) }
      if (e.key === 't') { e.preventDefault(); toggleTheme() }
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [toggleTheme])

  const handleTickerSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputTicker.trim()) {
      setTicker(inputTicker.trim().toUpperCase())
      setInputTicker('')
    }
  }

  const renderView = () => {
    switch (activeView) {
      case 'dashboard': return <Dashboard ticker={ticker} />
      case 'predict':
        return (
          <div className="space-y-2">
            <StockChart ticker={ticker} />
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-2">
              <div className="xl:col-span-2"><PredictionPanel ticker={ticker} /></div>
              <div><BatchTrainPanel /></div>
            </div>
          </div>
        )
      case 'backtest': return <BacktestPanel ticker={ticker} />
      case 'signals':
        return (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-2">
            <div className="xl:col-span-2"><StockChart ticker={ticker} /></div>
            <div className="space-y-2">
              <SignalsPanel ticker={ticker} />
              <AlertsPanel ticker={ticker} />
            </div>
          </div>
        )
      case 'portfolio': return <PortfolioOptimizer />
      case 'fundamentals':
        return (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-2">
            <FundamentalsPanel ticker={ticker} />
            <MultiTimeframePanel ticker={ticker} />
          </div>
        )
      default: return <Dashboard ticker={ticker} />
    }
  }

  const timeStr = time.toLocaleTimeString('en-US', { hour12: false })
  const dateStr = time.toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' })

  return (
    <div className="min-h-screen pb-6" style={{ background: 'var(--bg)' }}>
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-4">
          <span className="font-bold text-sm" style={{ color: 'var(--cyan)' }}>STOCKTERM</span>
          <span style={{ color: 'var(--dim)' }}>v1.0</span>
          <span className="cursor-blink" style={{ color: 'var(--green)' }}>●</span>
          <span style={{ color: 'var(--dim)' }}>CONNECTED</span>
        </div>
        <div className="flex items-center gap-4">
          <span style={{ color: 'var(--dim)' }}>{dateStr}</span>
          <span className="font-bold" style={{ color: 'var(--amber)' }}>{timeStr}</span>
          <button onClick={toggleTheme} className="px-2 py-0.5 text-xs">
            {theme === 'dark' ? 'LIGHT' : 'DARK'}
          </button>
        </div>
      </div>

      {/* Nav bar */}
      <div className="flex items-center gap-0 px-4 py-1 border-b" style={{ borderColor: 'var(--border)' }}>
        {VIEWS.map(v => (
          <button
            key={v.id}
            onClick={() => setActiveView(v.id)}
            className="px-3 py-1 text-xs font-bold transition-colors"
            style={{
              background: activeView === v.id ? 'var(--cyan)' : 'transparent',
              color: activeView === v.id ? 'var(--bg)' : 'var(--dim)',
              border: 'none',
            }}
          >
            {v.key}:{v.label}
          </button>
        ))}
        <div className="flex-1" />
        <form onSubmit={handleTickerSubmit} className="flex items-center gap-1">
          <span style={{ color: 'var(--dim)' }}>TICKER&gt;</span>
          <input
            value={inputTicker}
            onChange={e => setInputTicker(e.target.value)}
            placeholder={ticker}
            className="w-20 text-xs bg-transparent border-none px-1 py-0"
            style={{ color: 'var(--bright)', outline: 'none' }}
          />
        </form>
      </div>

      {/* Main content */}
      <div className="flex">
        <div className="flex-1 p-3 mr-0 lg:mr-[200px]">
          {/* Ticker + Price header */}
          <div className="flex items-baseline gap-3 mb-3">
            <span className="text-2xl font-bold" style={{ color: 'var(--bright)' }}>{ticker}</span>
            <HeroPrice ticker={ticker} />
          </div>
          {renderView()}
        </div>

        {/* Right sidebar — watchlist */}
        <div className="hidden lg:block ticker-sidebar">
          <div className="p-2 border-b text-xs font-bold" style={{ borderColor: 'var(--border)', color: 'var(--cyan)' }}>
            WATCHLIST
          </div>
          <TickerSidebar ticker={ticker} onSelect={setTicker} />
        </div>
      </div>

      {/* Status bar */}
      <div className="status-bar">
        <span>{activeView.toUpperCase()}</span>
        <span>|</span>
        <span>{ticker}</span>
        <span>|</span>
        <span>LIVE</span>
        <div className="flex-1" />
        <span>PRESS 1-6 TO SWITCH VIEW</span>
        <span>|</span>
        <span>T: TOGGLE THEME</span>
      </div>
    </div>
  )
}

function TickerSidebar({ ticker: current, onSelect }: { ticker: string; onSelect: (t: string) => void }) {
  const [prices, setPrices] = useState<Record<string, any>>({})
  const watchlist = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'META', 'AMZN', 'JPM', 'V']

  useEffect(() => {
    const fetchAll = async () => {
      const newPrices: Record<string, any> = {}
      for (const t of watchlist) {
        try {
          const res = await fetch(`/api/stocks/${t}`)
          const data = await res.json()
          if (data.price) newPrices[t] = data.price
        } catch {}
      }
      setPrices(newPrices)
    }
    fetchAll()
    const i = setInterval(fetchAll, 30000)
    return () => clearInterval(i)
  }, [])

  return (
    <div className="p-1">
      {watchlist.map(t => {
        const p = prices[t]
        const isActive = t === current
        const up = p && p.change >= 0
        return (
          <button
            key={t}
            onClick={() => onSelect(t)}
            className="w-full text-left px-2 py-1 text-xs flex items-center justify-between border-none"
            style={{
              background: isActive ? 'var(--bg-hover)' : 'transparent',
              color: isActive ? 'var(--bright)' : 'var(--text)',
            }}
          >
            <span className="font-bold">{t}</span>
            {p ? (
              <span style={{ color: up ? 'var(--green)' : 'var(--red)' }}>
                {up ? '▲' : '▼'}{Math.abs(p.change_percent).toFixed(2)}%
              </span>
            ) : (
              <span style={{ color: 'var(--dim)' }}>--</span>
            )}
          </button>
        )
      })}
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
