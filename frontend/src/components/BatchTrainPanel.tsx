import { useState, useEffect } from 'react'
import FadeIn from './FadeIn'

export default function BatchTrainPanel() {
  const [tickers, setTickers] = useState('AAPL,MSFT,GOOGL')
  const [epochs, setEpochs] = useState(50)
  const [training, setTraining] = useState(false)
  const [status, setStatus] = useState<any>(null)
  const [models, setModels] = useState<any[]>([])

  useEffect(() => { fetchModels(); fetchStatus() }, [])

  const fetchModels = async () => {
    try {
      const res = await fetch('/api/train/models')
      const data = await res.json()
      setModels(data.models || [])
    } catch (err) { console.error(err) }
  }

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/train/status')
      const data = await res.json()
      setStatus(data)
      if (data.running) setTraining(true)
    } catch (err) { console.error(err) }
  }

  const startTraining = async () => {
    setTraining(true)
    setStatus({ running: true, progress: {} })
    try {
      const tickerList = tickers.split(',').map(t => t.trim().toUpperCase()).filter(Boolean)
      const res = await fetch('/api/train/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tickers: tickerList, epochs })
      })
      const data = await res.json()
      setStatus({ running: false, ...data })
      await fetchModels()
    } catch (err) { console.error(err) }
    setTraining(false)
  }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="section-header" style={{ border: 'none', paddingBottom: 0, marginBottom: 0 }}>Batch Training</span>
        <span className="text-xxs text-txt-dim">{models.length} models trained</span>
      </div>

      {/* Input */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <input type="text" value={tickers} onChange={e => setTickers(e.target.value)}
          placeholder="AAPL, MSFT, GOOGL..."
          className="col-span-2 bg-surface-elevated border border-line rounded px-3 py-2 text-xs text-txt placeholder-txt-dim focus:outline-none focus:border-accent" />
        <div className="flex items-center gap-2">
          <input type="number" value={epochs} onChange={e => setEpochs(parseInt(e.target.value) || 50)}
            className="w-16 bg-surface-elevated border border-line rounded px-2 py-2 text-xs text-txt text-center" />
          <span className="text-xxs text-txt-dim">epochs</span>
        </div>
      </div>

      <button onClick={startTraining} disabled={training}
        className="w-full py-2 bg-accent text-white rounded text-xs font-medium hover:bg-accent-hover disabled:opacity-50 mb-4">
        {training ? 'Training...' : 'Start Batch Training'}
      </button>

      {/* Training Progress */}
      {status?.progress && Object.keys(status.progress).length > 0 && (
        <div className="space-y-1 mb-4 max-h-40 overflow-y-auto">
          {Object.entries(status.progress).map(([ticker, info]: [string, any]) => (
            <div key={ticker} className="flex items-center justify-between py-1 px-2 rounded bg-surface-elevated text-xs">
              <span className="text-txt font-medium">{ticker}</span>
              <span className={info.includes('done') ? 'text-up' : info.includes('error') ? 'text-down' : 'text-txt-dim'}>
                {info}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Trained Models */}
      {models.length > 0 && (
        <FadeIn>
          <div>
            <p className="text-xxs text-txt-dim uppercase tracking-wider mb-2">Trained Models</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-1.5 max-h-48 overflow-y-auto">
              {models.map((m, i) => (
                <div key={i} className="bg-surface-elevated rounded px-2.5 py-1.5 flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${m.has_model ? 'bg-up' : 'bg-down'}`} />
                  <span className="text-xxs text-txt font-medium">{m.ticker}</span>
                </div>
              ))}
            </div>
          </div>
        </FadeIn>
      )}
    </div>
  )
}
