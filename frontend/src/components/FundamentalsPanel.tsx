import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

function Row({ label, value, color }: { label: string; value: any; color?: string }) {
  return (
    <div className="flex items-center justify-between text-xs py-0.5">
      <span style={{ color: 'var(--dim)' }}>{label}</span>
      <span style={{ color: color || 'var(--text)' }}>{value ?? '--'}</span>
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
    <div className="panel">
      <div className="panel-title">FUNDAMENTALS</div>
      {data && !data.error ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
          {/* Score */}
          <div className="mb-2">
            <div className="text-xs" style={{ color: 'var(--dim)' }}>SCORE</div>
            <span className="text-lg font-bold" style={{
              color: data.fundamentals_score?.score >= 60 ? 'var(--green)' : data.fundamentals_score?.score >= 40 ? 'var(--amber)' : 'var(--red)',
            }}>{data.fundamentals_score?.score}/100</span>
            <span className="ml-2 text-xs" style={{ color: 'var(--dim)' }}>{data.fundamentals_score?.rating}</span>
          </div>

          {/* Valuation */}
          <div>
            <div className="text-xs font-bold mb-1" style={{ color: 'var(--cyan)' }}>VALUATION</div>
            <Row label="P/E" value={data.valuation?.pe_ratio?.toFixed(1)} />
            <Row label="PEG" value={data.valuation?.peg_ratio?.toFixed(2)} />
            <Row label="P/B" value={data.valuation?.price_to_book?.toFixed(1)} />
            <Row label="EV/EBITDA" value={data.valuation?.ev_to_ebitda?.toFixed(1)} />
          </div>

          {/* Profitability */}
          <div>
            <div className="text-xs font-bold mb-1" style={{ color: 'var(--cyan)' }}>PROFITABILITY</div>
            <Row label="Margin" value={data.profitability?.profit_margin ? `${data.profitability.profit_margin}%` : null}
              color={data.profitability?.profit_margin > 20 ? 'var(--green)' : data.profitability?.profit_margin > 0 ? 'var(--text)' : 'var(--red)'} />
            <Row label="ROE" value={data.profitability?.roe ? `${data.profitability.roe}%` : null}
              color={data.profitability?.roe > 20 ? 'var(--green)' : 'var(--text)'} />
            <Row label="Rev Growth" value={data.profitability?.revenue_growth ? `${data.profitability.revenue_growth}%` : null}
              color={data.profitability?.revenue_growth > 0 ? 'var(--green)' : 'var(--red)'} />
          </div>

          {/* Health */}
          <div>
            <div className="text-xs font-bold mb-1" style={{ color: 'var(--cyan)' }}>HEALTH</div>
            <Row label="D/E" value={data.financial_health?.debt_to_equity?.toFixed(1)} />
            <Row label="Current" value={data.financial_health?.current_ratio?.toFixed(2)} />
            <Row label="FCF" value={data.financial_health?.free_cash_flow ? `$${(data.financial_health.free_cash_flow / 1e9).toFixed(1)}B` : null} />
          </div>
        </div>
      ) : (
        <div style={{ color: 'var(--dim)' }}>{data?.error || 'Loading...'}</div>
      )}
    </div>
  )
}
