import { useState, useEffect } from 'react'
import { cachedFetch } from '../cache'

export default function NewsPanel({ ticker }: { ticker: string }) {
  const [articles, setArticles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    cachedFetch(`/api/stocks/${ticker}/combined`, 120000)
      .then(json => {
        setArticles(json?.combined?.breakdown?.sentiment?.articles || [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [ticker])

  return (
    <div className="card p-4">
      <p className="section-header">Recent News</p>
      {loading ? (
        <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-8 skeleton" />)}</div>
      ) : articles.length > 0 ? (
        <div className="space-y-2">
          {articles.slice(0, 8).map((a: any, i: number) => {
            const sentColor = a.sentiment === 'bullish' ? 'rgb(var(--color-up))' : a.sentiment === 'bearish' ? 'rgb(var(--color-down))' : 'rgb(var(--color-txt-muted))'
            return (
              <a key={i} href={a.url} target="_blank" rel="noopener noreferrer"
                className="block py-1.5 text-xs hover:underline" style={{ borderBottom: '1px solid rgb(var(--color-line) / 0.15)' }}>
                <div className="flex items-start gap-2">
                  <span className="shrink-0 mt-0.5" style={{ color: sentColor, fontSize: '8px' }}>●</span>
                  <div className="min-w-0">
                    <p className="truncate" style={{ color: 'rgb(var(--color-txt))' }}>{a.title}</p>
                    <p className="text-xxs" style={{ color: 'rgb(var(--color-txt-muted))' }}>{a.source}</p>
                  </div>
                </div>
              </a>
            )
          })}
        </div>
      ) : (
        <p className="text-xs" style={{ color: 'rgb(var(--color-txt-muted))' }}>No recent news</p>
      )}
    </div>
  )
}
