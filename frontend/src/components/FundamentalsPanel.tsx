import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

interface FundamentalsPanelProps {
  ticker: string
}

export default function FundamentalsPanel({ ticker }: FundamentalsPanelProps) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => { fetchData() }, [ticker])

  const fetchData = async () => {
    setLoading(true)
    try {
      const json = await cachedFetch(`/api/stocks/${ticker}/fundamentals`)
      setData(json)
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const Row = ({ label, value, color }: { label: string; value: any; color?: string }) => (
    <div className="flex items-center justify-between py-1 border-b border-line/50 last:border-0">
      <span className="text-xxs text-txt-dim">{label}</span>
      <span className={`text-xs font-medium tabular-nums ${color || 'text-txt'}`}>{value ?? '—'}</span>
    </div>
  )

  const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div className="mb-3">
      <p className="text-xxs text-txt-dim uppercase tracking-wider mb-1.5">{title}</p>
      <div className="bg-surface-elevated rounded p-2.5">{children}</div>
    </div>
  )

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="section-header" style={{ border: 'none', paddingBottom: 0, marginBottom: 0 }}>Fundamentals</span>
        <button onClick={fetchData} disabled={loading} className="text-xxs text-accent hover:text-accent-hover disabled:text-txt-dim">
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {loading ? (
        <div className="text-txt-dim text-xs text-center py-12">Loading fundamentals...</div>
      ) : data && !data.error ? (
        <div>
          {/* Score */}
          <div className="text-center mb-3 py-2 bg-surface-elevated rounded">
            <p className="text-xxs text-txt-dim uppercase">Fundamentals Score</p>
            <p className={`text-xl font-bold ${
              data.fundamentals_score?.score >= 60 ? 'text-up' :
              data.fundamentals_score?.score >= 40 ? 'text-warn' : 'text-down'
            }`}>{data.fundamentals_score?.score}/100</p>
            <p className="text-xxs text-txt-muted">{data.fundamentals_score?.rating}</p>
          </div>

          <Section title="Valuation">
            <Row label="P/E Ratio" value={data.valuation?.pe_ratio?.toFixed(1)} />
            <Row label="PEG Ratio" value={data.valuation?.peg_ratio?.toFixed(2)} />
            <Row label="Price/Book" value={data.valuation?.price_to_book?.toFixed(1)} />
            <Row label="EV/EBITDA" value={data.valuation?.ev_to_ebitda?.toFixed(1)} />
          </Section>

          <Section title="Profitability">
            <Row label="Profit Margin" value={data.profitability?.profit_margin ? `${data.profitability.profit_margin}%` : null}
              color={data.profitability?.profit_margin > 20 ? 'text-up' : data.profitability?.profit_margin > 0 ? 'text-txt' : 'text-down'} />
            <Row label="ROE" value={data.profitability?.roe ? `${data.profitability.roe}%` : null}
              color={data.profitability?.roe > 20 ? 'text-up' : 'text-txt'} />
            <Row label="Revenue Growth" value={data.profitability?.revenue_growth ? `${data.profitability.revenue_growth}%` : null}
              color={data.profitability?.revenue_growth > 0 ? 'text-up' : 'text-down'} />
            <Row label="Earnings Growth" value={data.profitability?.earnings_growth ? `${data.profitability.earnings_growth}%` : null} />
          </Section>

          <Section title="Financial Health">
            <Row label="Debt/Equity" value={data.financial_health?.debt_to_equity?.toFixed(1)} />
            <Row label="Current Ratio" value={data.financial_health?.current_ratio?.toFixed(2)} />
            <Row label="Free Cash Flow" value={data.financial_health?.free_cash_flow ? `$${(data.financial_health.free_cash_flow / 1e9).toFixed(1)}B` : null} />
          </Section>

          <Section title="Analysts">
            <Row label="Target Mean" value={data.analysts?.target_mean_price ? `$${data.analysts.target_mean_price}` : null} />
            <Row label="Recommendation" value={data.analysts?.recommendation}
              color={data.analysts?.recommendation === 'buy' ? 'text-up' : data.analysts?.recommendation === 'sell' ? 'text-down' : 'text-txt'} />
            <Row label="Analysts" value={data.analysts?.number_of_analysts} />
          </Section>
        </div>
      ) : (
        <div className="text-txt-dim text-xs text-center py-12">{data?.error || 'No data'}</div>
      )}
    </div>
  )
}
