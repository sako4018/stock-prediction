import { useState } from 'react'
import Dashboard from './components/Dashboard'
import SearchBar from './components/SearchBar'

function App() {
  const [ticker, setTicker] = useState<string>('AAPL')

  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Header */}
      <header className="border-b border-dark-border bg-dark-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-stock-blue rounded-lg flex items-center justify-center">
              <span className="text-xl">📈</span>
            </div>
            <div>
              <h1 className="text-xl font-bold">Stock Predictor</h1>
              <p className="text-xs text-gray-500">ML-Powered Predictions</p>
            </div>
          </div>

          <SearchBar onSearch={setTicker} />

          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="w-2 h-2 bg-stock-green rounded-full pulse-live"></span>
            Live
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Dashboard ticker={ticker} />
      </main>
    </div>
  )
}

export default App
