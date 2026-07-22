import PredictionPanel from './PredictionPanel'
import SignalsPanel from './SignalsPanel'
import StockChart from './StockChart'
import FundamentalsPanel from './FundamentalsPanel'
import FadeIn from './FadeIn'

interface DashboardProps {
  ticker: string
}

export default function Dashboard({ ticker }: DashboardProps) {
  return (
    <div className="space-y-4" key={ticker}>
      {/* Asymmetric: chart 62% / signals 38% */}
      <FadeIn delay={0}>
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
          <div className="xl:col-span-3"><StockChart ticker={ticker} /></div>
          <div className="xl:col-span-2"><SignalsPanel ticker={ticker} /></div>
        </div>
      </FadeIn>

      {/* Prediction — full width */}
      <FadeIn delay={100}>
        <PredictionPanel ticker={ticker} />
      </FadeIn>

      {/* Bottom: Fundamentals 60% / Backtest summary 40% */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        <FadeIn delay={200}>
          <div className="xl:col-span-3"><FundamentalsPanel ticker={ticker} /></div>
        </FadeIn>
        <FadeIn delay={300}>
          <div className="xl:col-span-2">
            <div className="card p-5">
              <h3 className="section-header">Quick Stats</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'Volatility', value: '—', color: '' },
                  { label: 'Momentum', value: '—', color: '' },
                  { label: 'Trend', value: '—', color: '' },
                  { label: 'Sentiment', value: '—', color: '' },
                ].map((stat, i) => (
                  <div key={i} className="p-3 rounded" style={{
                    background: 'rgb(var(--color-surface))',
                    border: '1px solid rgb(var(--color-line))',
                  }}>
                    <p className="text-xxs uppercase tracking-wider mb-1" style={{
                      fontFamily: '"Space Grotesk", system-ui, sans-serif',
                      letterSpacing: '0.1em',
                      color: 'rgb(var(--color-txt-muted))',
                    }}>{stat.label}</p>
                    <p className="text-lg font-bold tabular-nums" style={{
                      fontFamily: '"JetBrains Mono", monospace',
                      color: 'rgb(var(--color-txt))',
                    }}>{stat.value}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </FadeIn>
      </div>
    </div>
  )
}
