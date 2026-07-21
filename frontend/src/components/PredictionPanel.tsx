import { useState, useEffect } from 'react'

interface PredictionPanelProps {
  ticker: string
}

interface Prediction {
  ticker: string
  current_price: number
  prediction: number
  signal: string
  confidence: number
  timestamp: string
}

export default function PredictionPanel({ ticker }: PredictionPanelProps) {
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => { fetchPrediction() }, [ticker])

  const fetchPrediction = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/stocks/${ticker}/predict`, { method: 'POST' })
      const data = await res.json()
      setPrediction(data)
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const trainModel = async () => {
    setLoading(true)
    try {
      await fetch(`/api/stocks/${ticker}/train`, { method: 'POST' })
      await fetchPrediction()
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const isBuy = prediction?.signal === 'BUY'

  return (
    <div className="bg-surface-1 border border-frame rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xxs font-medium text-label-muted uppercase tracking-wider">ML Prediction</span>
        <button onClick={fetchPrediction} disabled={loading}
          className="text-xxs text-accent hover:text-accent-hover disabled:text-label-muted">
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {prediction ? (
        <div className="space-y-4">
          {/* Signal */}
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded ${
            isBuy ? 'bg-up/10 text-up' : 'bg-down/10 text-down'
          }`}>
            <span className="w-2 h-2 rounded-full bg-current" />
            <span className="text-sm font-semibold">{prediction.signal}</span>
          </div>

          {/* Price */}
          <div>
            <p className="text-xxs text-label-muted mb-0.5">Current Price</p>
            <p className="text-xl font-bold tabular-nums text-label">${prediction.current_price.toFixed(2)}</p>
          </div>

          {/* Confidence */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <p className="text-xxs text-label-muted">Confidence</p>
              <p className="text-xxs tabular-nums text-label-dim">{prediction.confidence.toFixed(1)}%</p>
            </div>
            <div className="h-1 bg-surface-3 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${isBuy ? 'bg-up' : 'bg-down'}`}
                style={{ width: `${Math.min(prediction.confidence, 100)}%` }}
              />
            </div>
          </div>

          {/* Model Output */}
          <div className="bg-surface-2 rounded p-2.5">
            <p className="text-xxs text-label-muted mb-0.5">Model Output</p>
            <p className="text-xs font-mono text-label-dim tabular-nums">{prediction.prediction.toFixed(4)}</p>
          </div>
        </div>
      ) : (
        <div className="text-label-muted text-xs text-center py-8">
          {loading ? 'Analyzing...' : 'No prediction'}
        </div>
      )}

      <button onClick={trainModel} disabled={loading}
        className="w-full mt-4 py-2 bg-surface-3 hover:bg-surface-4 border border-frame rounded text-xs font-medium text-label-dim hover:text-label transition-colors disabled:opacity-50">
        {loading ? 'Training...' : 'Retrain Model'}
      </button>
    </div>
  )
}
