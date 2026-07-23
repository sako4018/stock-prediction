import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

const PEERS: Record<string, string[]> = {
  AAPL: ['MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA'],
  MSFT: ['AAPL', 'GOOGL', 'AMZN', 'META', 'CRM'],
  GOOGL: ['AAPL', 'MSFT', 'AMZN', 'META', 'NFLX'],
  AMZN: ['AAPL', 'MSFT', 'GOOGL', 'META', 'TSLA'],
  TSLA: ['AAPL', 'NIO', 'RIVN', 'GM', 'F'],
  NVDA: ['AMD', 'INTC', 'QCOM', 'AVGO', 'MRVL'],
  META: ['AAPL', 'MSFT', 'GOOGL', 'SNAP', 'PINS'],
}

export default function PeerComparison({ ticker, onSelect }: { ticker: string; onSelect: (t: string) => void }) {
  const [peers, setPeers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const peerTickers = PEERS[ticker] || PEERS['AAPL']

  useEffect(() => {
    setLoading(true)
    const load = async () => {
      const results = []
      for (const t of peerTickers) {
        try {
          const data = await cachedFetch(`/api/stocks/${t}`)
          if (data?.price) {
            results.push({
              ticker: t,
              price: data.price.current_price,
              change: data.price.change_percent,
              name: data.company?.name || t,
            })
          }
        } catch {}
      }
      setPeers(results)
      setLoading(false)
    }
    load()
  }, [ticker])

  return (
    <div className="card p-4">
      <p className="section-header">Compare Peers</p>
      {loading ? (
        <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-6 skeleton" />)}</div>
      ) : (
        <div className="space-y-1">
          {peers.map(p => {
            const up = p.change >= 0
            return (
              <button key={p.ticker} onClick={() => onSelect(p.ticker)}
                className="w-full flex items-center justify-between py-1.5 px-2 rounded text-xs transition-colors"
                style={{
                  background: p.ticker === ticker ? 'rgb(var(--color-accent) / 0.06)' : 'transparent',
                  border: 'none',
                  textAlign: 'left',
                }}>
                <div>
                  <span className="font-bold" style={{ color: p.ticker === ticker ? 'rgb(var(--color-accent))' : 'rgb(var(--color-txt))' }}>{p.ticker}</span>
                  <span className="ml-2" style={{ color: 'rgb(var(--color-txt-muted))' }}>{p.name?.substring(0, 20)}</span>
                </div>
                <span className="tabular-nums" style={{ color: up ? 'rgb(var(--color-up))' : 'rgb(var(--color-down))' }}>
                  {up ? '+' : ''}{p.change?.toFixed(2)}%
                </span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
