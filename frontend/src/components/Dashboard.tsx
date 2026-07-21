import { useState } from 'react'
import { useTheme } from '../ThemeContext'
import StockChart from './StockChart'
import PredictionPanel from './PredictionPanel'
import SignalsPanel from './SignalsPanel'
import CompanyInfo from './CompanyInfo'
import BacktestPanel from './BacktestPanel'

interface DashboardProps {
  ticker: string
}

export default function Dashboard({ ticker }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<'chart' | 'backtest'>('chart')
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="space-y-6">
      {/* Top Row: Price + Prediction + Signals */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <CompanyInfo ticker={ticker} />
        <PredictionPanel ticker={ticker} />
        <SignalsPanel ticker={ticker} />
      </div>

      {/* Tab Navigation */}
      <div className={`flex gap-4 border-b ${isDark ? 'border-dark-border' : 'border-gray-200'}`}>
        <button
          onClick={() => setActiveTab('chart')}
          className={`pb-3 px-4 font-medium transition-colors ${
            activeTab === 'chart'
              ? 'text-stock-blue border-b-2 border-stock-blue'
              : isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          📊 Chart & History
        </button>
        <button
          onClick={() => setActiveTab('backtest')}
          className={`pb-3 px-4 font-medium transition-colors ${
            activeTab === 'backtest'
              ? 'text-stock-blue border-b-2 border-stock-blue'
              : isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          💰 Backtest
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'chart' && <StockChart ticker={ticker} />}
      {activeTab === 'backtest' && <BacktestPanel ticker={ticker} />}
    </div>
  )
}
