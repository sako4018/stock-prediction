import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

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
    total_return: number
    win_rate: number
    total_trades: number
    profitable_trades: number
    losing_trades: number
    buy_and_hold_return: number
    outperformance: number
    sharpe_ratio: number
    sortino_ratio: number
    max_drawdown: number
    volatility: number
    calmar_ratio: number
  }
}

export default function BacktestPanel({ ticker }: BacktestPanelProps) {
  const [data, setData] = useState<BacktestResults | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => { runBacktest() }, [ticker])

  const runBacktest = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/stocks/${ticker}/backtest?period=2y&initial_capital=10000`)
      const json = await res.json()
      setData(json)
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const chartData = data ? [
    { name: 'Strategy', value: data.results.total_return, color: data.results.total_return >= 0 ? '#22C55E' : '#EF4444' },
    { name: 'Buy & Hold', value: data.results.buy_and_hold_return, color: '#3B82F6' },
  ] : []

  const MetricCard = ({ label, value, color = 'text-txt', sub }: { label: string; value: string; color?: string; sub?: string }) => (
    <div className="bg-elevated rounded p-3">
      <p className="text-xxs text-txt-muted uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-lg font-semibold tabular-nums ${color}`}>{value}</p>
      {sub && <p className="text-xxs text-txt-muted mt-0.5">{sub}</p>}
    </div>
  )

  return (
    <div className="bg-alt border border-line rounded-lg p-5">
      <div className="flex items-center justify-between mb-5">
        <span className="text-xxs font-medium text-txt-muted uppercase tracking-wider">Backtest Results</span>
        <button onClick={runBacktest} disabled={loading}
          className="text-xxs text-accent hover:text-accent-hover disabled:text-txt-muted">
          {loading ? 'Running...' : 'Run Again'}
        </button>
      </div>

      {loading ? (
        <div className="text-txt-muted text-xs text-center py-16">Running simulation...</div>
      ) : data ? (
        <div className="space-y-5">
          {/* Performance Metrics */}
          <div>
            <p className="text-xxs text-txt-muted uppercase tracking-wider mb-2">Accuracy Metrics</p>
            <div className="grid grid-cols-4 gap-2">
              <MetricCard label="Accuracy" value={`${data.results.accuracy?.toFixed(1)}%`} />
              <MetricCard label="Precision" value={`${data.results.precision?.toFixed(1)}%`} />
              <MetricCard label="Recall" value={`${data.results.recall?.toFixed(1)}%`} />
              <MetricCard label="F1-Score" value={`${data.results.f1_score?.toFixed(1)}%`} />
            </div>
          </div>

          {/* Trading Results */}
          <div>
            <p className="text-xxs text-txt-muted uppercase tracking-wider mb-2">Trading Performance</p>
            <div className="grid grid-cols-4 gap-2">
              <MetricCard label="Total Return" value={`${data.results.total_return >= 0 ? '+' : ''}${data.results.total_return?.toFixed(2)}%`}
                color={data.results.total_return >= 0 ? 'text-up' : 'text-down'} />
              <MetricCard label="Win Rate" value={`${data.results.win_rate?.toFixed(1)}%`} />
              <MetricCard label="Total Trades" value={`${data.results.total_trades}`} />
              <MetricCard label="Outperformance" value={`${data.results.outperformance >= 0 ? '+' : ''}${data.results.outperformance?.toFixed(2)}%`}
                color={data.results.outperformance >= 0 ? 'text-up' : 'text-down'} sub="vs Buy & Hold" />
            </div>
          </div>

          {/* Risk Metrics */}
          <div>
            <p className="text-xxs text-txt-muted uppercase tracking-wider mb-2">Risk Metrics</p>
            <div className="grid grid-cols-5 gap-2">
              <MetricCard label="Sharpe" value={data.results.sharpe_ratio?.toFixed(2)}
                color={data.results.sharpe_ratio > 1 ? 'text-up' : data.results.sharpe_ratio > 0 ? 'text-txt-dim' : 'text-down'} />
              <MetricCard label="Sortino" value={data.results.sortino_ratio?.toFixed(2)}
                color={data.results.sortino_ratio > 1 ? 'text-up' : 'text-txt-dim'} />
              <MetricCard label="Max Drawdown" value={`${data.results.max_drawdown?.toFixed(2)}%`}
                color={data.results.max_drawdown > -20 ? 'text-up' : 'text-down'} />
              <MetricCard label="Volatility" value={`${data.results.volatility?.toFixed(2)}%`} />
              <MetricCard label="Calmar" value={data.results.calmar_ratio?.toFixed(2)} />
            </div>
          </div>

          {/* Chart */}
          <div>
            <p className="text-xxs text-txt-muted uppercase tracking-wider mb-2">Strategy Comparison</p>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical">
                  <XAxis type="number" stroke="#6B7280" tick={{ fontSize: 10, fill: '#6B7280' }} />
                  <YAxis type="category" dataKey="name" stroke="#6B7280" tick={{ fontSize: 10, fill: '#9CA3AF' }} width={70} />
                  <Tooltip contentStyle={{ backgroundColor: '#171A20', border: '1px solid #2A2D35', borderRadius: 6, fontSize: 12 }} />
                  <Bar dataKey="value" radius={[0, 3, 3, 0]} barSize={16}>
                    {chartData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-txt-muted text-xs text-center py-16">No data</div>
      )}
    </div>
  )
}
