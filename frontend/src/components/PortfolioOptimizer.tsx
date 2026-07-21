import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import FadeIn from './FadeIn'

export default function PortfolioOptimizer() {
  const [tickers, setTickers] = useState('AAPL,MSFT,GOOGL,NVDA,AMZN')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'max-sharpe' | 'min-volatility'>('max-sharpe')

  const optimize = async () => {
    setLoading(true)
    try {
      const tickerList = tickers.split(',').map(t => t.trim().toUpperCase()).filter(Boolean)
      const endpoint = activeTab === 'max-sharpe' ? '/api/optimize/max-sharpe' : '/api/optimize/min-volatility'
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tickers: tickerList, period: '2y' })
      })
      const data = await res.json()
      setResult(data)
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const chartData = result?.allocation
    ? Object.entries(result.allocation).map(([ticker, weight]) => ({
        name: ticker,
        value: Math.round((weight as number) * 100)
      })).sort((a, b) => b.value - a.value)
    : []

  const COLORS = ['#7c4dff', '#00b8d4', '#69f0ae', '#ff6e40', '#ffd740', '#e040fb', '#40c4ff', '#b388ff']

  return (
    <div className="bg-surface-alt border border-line rounded-lg p-5 card-smooth">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xxs font-medium text-txt-dim uppercase tracking-wider">Portfolio Optimizer</span>
      </div>

      {/* Input */}
      <div className="flex gap-2 mb-4">
        <input
          type="text" value={tickers} onChange={e => setTickers(e.target.value)}
          placeholder="AAPL, MSFT, GOOGL, NVDA..."
          className="flex-1 bg-surface-elevated border border-line rounded px-3 py-2 text-xs text-txt placeholder-txt-dim focus:outline-none focus:border-accent"
        />
        <button onClick={optimize} disabled={loading}
          className="px-4 py-2 bg-accent text-white rounded text-xs font-medium hover:bg-accent-hover disabled:opacity-50">
          {loading ? '...' : 'Optimize'}
        </button>
      </div>

      {/* Strategy tabs */}
      <div className="flex gap-2 mb-4">
        {(['max-sharpe', 'min-volatility'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 rounded text-xxs font-medium transition-colors ${
              activeTab === tab ? 'bg-accent text-white' : 'bg-surface-elevated text-txt-dim hover:text-txt'
            }`}>
            {tab === 'max-sharpe' ? 'Max Sharpe' : 'Min Volatility'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1,2,3].map(i => <div key={i} className="h-8 skeleton" />)}
        </div>
      ) : result && !result.error ? (
        <FadeIn>
          <div className="space-y-4">
            {/* Stats */}
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: 'Expected Return', value: `${result.expected_return}%`, color: 'text-up' },
                { label: 'Volatility', value: `${result.expected_volatility}%`, color: 'text-txt' },
                { label: 'Sharpe Ratio', value: result.sharpe_ratio?.toFixed(2), color: 'text-accent' },
              ].map((s, i) => (
                <div key={i} className="bg-surface-elevated rounded p-3 text-center">
                  <p className="text-xxs text-txt-dim">{s.label}</p>
                  <p className={`text-lg font-bold tabular-nums ${s.color}`}>{s.value}</p>
                </div>
              ))}
            </div>

            {/* Allocation chart */}
            <div className="bg-surface-elevated rounded p-4">
              <p className="text-xxs text-txt-dim uppercase tracking-wider mb-2">Allocation</p>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical">
                    <XAxis type="number" stroke="#6b6b80" tick={{ fontSize: 10, fill: '#6b6b80' }} unit="%" />
                    <YAxis type="category" dataKey="name" stroke="#6b6b80" tick={{ fontSize: 11, fill: '#e8e8e8' }} width={50} />
                    <Tooltip contentStyle={{ background: '#13131a', border: '1px solid #222233', borderRadius: 6, fontSize: 12 }} />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={18}>
                      {chartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </FadeIn>
      ) : result?.error ? (
        <p className="text-down text-xs text-center py-4">{result.error}</p>
      ) : null}
    </div>
  )
}
