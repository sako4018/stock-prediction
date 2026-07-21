import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface BacktestPanelProps {
  ticker: string
}

interface BacktestResults {
  ticker: string
  initial_capital: number
  results: {
    accuracy: number
    precision: number
    recall: number
    f1_score: number
    initial_capital: number
    final_capital: number
    total_return: number
    total_trades: number
    profitable_trades: number
    losing_trades: number
    win_rate: number
    buy_and_hold_return: number
    outperformance: number
  }
}

export default function BacktestPanel({ ticker }: BacktestPanelProps) {
  const [data, setData] = useState<BacktestResults | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    runBacktest()
  }, [ticker])

  const runBacktest = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/stocks/${ticker}/backtest?period=2y&initial_capital=10000`)
      const json = await res.json()
      setData(json)
    } catch (err) {
      console.error('Backtest failed:', err)
    }
    setLoading(false)
  }

  const chartData = data ? [
    { name: 'Strategy', value: data.results.total_return, color: data.results.total_return >= 0 ? '#00C853' : '#FF1744' },
    { name: 'Buy & Hold', value: data.results.buy_and_hold_return, color: '#2979FF' },
  ] : []

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">💰 Backtest Results</h3>
        <button
          onClick={runBacktest}
          disabled={loading}
          className="text-xs bg-dark-bg px-3 py-1 rounded hover:bg-dark-border transition-colors"
        >
          {loading ? 'Running...' : 'Run Again'}
        </button>
      </div>

      {loading ? (
        <div className="text-gray-500 text-center py-12">Running backtest simulation...</div>
      ) : data ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Metrics */}
          <div className="space-y-4">
            {/* Performance Metrics */}
            <div className="bg-dark-bg rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Performance Metrics</h4>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-gray-500">Accuracy</p>
                  <p className="text-lg font-bold">{data.results.accuracy?.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Precision</p>
                  <p className="text-lg font-bold">{data.results.precision?.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Recall</p>
                  <p className="text-lg font-bold">{data.results.recall?.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">F1-Score</p>
                  <p className="text-lg font-bold">{data.results.f1_score?.toFixed(1)}%</p>
                </div>
              </div>
            </div>

            {/* Trading Metrics */}
            <div className="bg-dark-bg rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Trading Results</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-400">Total Return</span>
                  <span className={`font-bold ${data.results.total_return >= 0 ? 'text-stock-green' : 'text-stock-red'}`}>
                    {data.results.total_return >= 0 ? '+' : ''}{data.results.total_return?.toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-400">Win Rate</span>
                  <span className="font-bold">{data.results.win_rate?.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-400">Total Trades</span>
                  <span className="font-bold">{data.results.total_trades}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-400">Profitable</span>
                  <span className="text-stock-green font-bold">{data.results.profitable_trades}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-400">Losing</span>
                  <span className="text-stock-red font-bold">{data.results.losing_trades}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Chart & Comparison */}
          <div className="space-y-4">
            {/* Return Comparison */}
            <div className="bg-dark-bg rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Strategy vs Buy & Hold</h4>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
                    <XAxis type="number" stroke="#666" tick={{ fontSize: 12 }} />
                    <YAxis type="category" dataKey="name" stroke="#666" tick={{ fontSize: 12 }} width={80} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#12121a',
                        border: '1px solid #1e1e2e',
                        borderRadius: '8px'
                      }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Outperformance */}
            <div className={`text-center p-4 rounded-lg ${
              data.results.outperformance >= 0 ? 'bg-green-500/10' : 'bg-red-500/10'
            }`}>
              <p className="text-sm text-gray-400">Outperformance vs Buy & Hold</p>
              <p className={`text-2xl font-bold ${
                data.results.outperformance >= 0 ? 'text-stock-green' : 'text-stock-red'
              }`}>
                {data.results.outperformance >= 0 ? '+' : ''}{data.results.outperformance?.toFixed(2)}%
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-gray-500 text-center py-12">No backtest data available</div>
      )}
    </div>
  )
}
