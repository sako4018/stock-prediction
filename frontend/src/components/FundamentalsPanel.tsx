import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

function Row({ label, value, color }: { label: string; value: any; color?: string }) {
  return (
    <div className="flex items-center justify-between py-1" style={{ borderBottom: '1px solid rgb(var(--color-line) / 0.3)' }}>
      <span className="text-xxs" style={{ color: 'rgb(var(--color-txt-dim))' }}>{label}</span>
      <span className={`text-xs font-medium tabular-nums ${color || 'text-txt'}`}>{value ?? '—'}</span>
    </div>
  )
}

export default function FundamentalsPanel({ ticker }: { ticker: string }) {
  const [data, setData] = useState<any>(null)

  useEffect(() => { fetchData() }, [ticker])

  const fetchData = async () => {
    try { setData(await cachedFetch(`/api/stocks/${ticker}/fundamentals`)) } catch {}
  }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="section-header" style={{ border: 'none', paddingBottom: 0, marginBottom: 0 }}>Fundamentals</span>
        <button onClick={fetchData} disabled={!data} className="text-xxs" style={{ color: 'rgb(var(--color-accent))' }}>
          {data ? 'Refresh' : '...'}
        </button>
      </div>
      {data && !data.error ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
          <div>
            <p className="text-xxs font-bold mb-1" style={{ fontFamily: '"Space Grotesk", system-ui, sans-serif', color: 'rgb(var(--color-accent))' }}>VALUATION</p>
            <Row label="P/E Ratio" value={data.valuation?.pe_ratio?.toFixed(1)} />
            <Row label="PEG Ratio" value={data.valuation?.peg_ratio?.toFixed(2)} />
            <Row label="Price/Book" value={data.valuation?.price_to_book?.toFixed(1)} />
            <Row label="EV/EBITDA" value={data.valuation?.ev_to_ebitda?.toFixed(1)} />
          </div>
          <div>
            <p className="text-xxs font-bold mb-1" style={{ fontFamily: '"Space Grotesk", system-ui, sans-serif', color: 'rgb(var(--color-accent))' }}>PROFITABILITY</p>
            <Row label="Margin" value={data.profitability?.profit_margin ? `${data.profitability.profit_margin}%` : null}
              color={data.profitability?.profit_margin > 20 ? 'text-up' : data.profitability?.profit_margin > 0 ? 'text-txt' : 'text-down'} />
            <Row label="ROE" value={data.profitability?.roe ? `${data.profitability.roe}%` : null}
              color={data.profitability?.roe > 20 ? 'text-up' : 'text-txt'} />
            <Row label="Rev Growth" value={data.profitability?.revenue_growth ? `${data.profitability.revenue_growth}%` : null}
              color={data.profitability?.revenue_growth > 0 ? 'text-up' : 'text-down'} />
          </div>
          <div>
            <p className="text-xxs font-bold mb-1" style={{ fontFamily: '"Space Grotesk", system-ui, sans-serif', color: 'rgb(var(--color-accent))' }}>HEALTH</p>
            <Row label="Debt/Equity" value={data.financial_health?.debt_to_equity?.toFixed(1)} />
            <Row label="Current Ratio" value={data.financial_health?.current_ratio?.toFixed(2)} />
            <Row label="Free Cash Flow" value={data.financial_health?.free_cash_flow ? `$${(data.financial_health.free_cash_flow / 1e9).toFixed(1)}B` : null} />
          </div>
          <div>
            <p className="text-xxs font-bold mb-1" style={{ fontFamily: '"Space Grotesk", system-ui, sans-serif', color: 'rgb(var(--color-accent))' }}>ANALYSTS</p>
            <Row label="Target Mean" value={data.analysts?.target_mean_price ? `$${data.analysts.target_mean_price}` : null} />
            <Row label="Rating" value={data.analysts?.recommendation}
              color={data.analysts?.recommendation === 'buy' ? 'text-up' : data.analysts?.recommendation === 'sell' ? 'text-down' : 'text-txt'} />
          </div>
        </div>
      ) : (
        <div className="text-xs text-center py-8" style={{ color: 'rgb(var(--color-txt-dim))' }}>{data?.error || 'Loading...'}</div>
      )}
    </div>
  )
}
