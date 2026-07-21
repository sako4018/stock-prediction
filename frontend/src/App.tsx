import { useState } from 'react'
import { ThemeProvider, useTheme } from './ThemeContext'
import Dashboard from './components/Dashboard'
import SearchBar from './components/SearchBar'

function AppContent() {
  const [ticker, setTicker] = useState<string>('AAPL')
  const { theme, toggleTheme } = useTheme()

  const isDark = theme === 'dark'

  return (
    <div className={`min-h-screen transition-colors duration-300 ${isDark ? 'bg-dark-bg text-white' : 'bg-gray-50 text-gray-900'}`}>
      {/* Header */}
      <header className={`border-b backdrop-blur-sm sticky top-0 z-50 transition-colors duration-300 ${
        isDark ? 'border-dark-border bg-dark-card/80' : 'border-gray-200 bg-white/80'
      }`}>
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-stock-blue rounded-lg flex items-center justify-center">
              <span className="text-xl">📈</span>
            </div>
            <div>
              <h1 className="text-xl font-bold">Stock Predictor</h1>
              <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>ML-Powered Predictions</p>
            </div>
          </div>

          <SearchBar onSearch={setTicker} />

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <span className="w-2 h-2 bg-stock-green rounded-full pulse-live"></span>
              <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>Live</span>
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-lg transition-colors ${
                isDark ? 'bg-dark-bg hover:bg-dark-border' : 'bg-gray-200 hover:bg-gray-300'
              }`}
              title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDark ? '☀️' : '🌙'}
            </button>
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

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  )
}

export default App
