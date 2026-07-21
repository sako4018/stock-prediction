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
  const [training, setTraining] = useState(false)

  useEffect(() => {
    fetchPrediction()
  }, [ticker])

  const fetchPrediction = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/stocks/${ticker}/predict`, { method: 'POST' })
      const data = await res.json()
      setPrediction(data)
    } catch (err) {
      console.error('Failed to get prediction:', err)
    }
    setLoading(false)
  }

  const trainModel = async () => {
    setTraining(true)
    try {
      await fetch(`/api/stocks/${ticker}/train`, { method: 'POST' })
      await fetchPrediction()
    } catch (err) {
      console.error('Training failed:', err)
    }
    setTraining(false)
  }

  const isBuy = prediction?.signal === 'BUY'

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6 card-hover">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">🤖 ML Prediction</h3>
        <button
          onClick={fetchPrediction}
          disabled={loading}
          className="text-xs bg-dark-bg px-3 py-1 rounded hover:bg-dark-border transition-colors"
        >
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {prediction ? (
        <div className="space-y-4">
          {/* Signal Badge */}
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg ${
            isBuy ? 'bg-green-500/20 text-stock-green glow-green' : 'bg-red-500/20 text-stock-red glow-red'
          }`}>
            <span className="text-2xl">{isBuy ? '📈' : '📉'}</span>
            <span className="text-xl font-bold">{prediction.signal}</span>
          </div>

          {/* Price */}
          <div>
            <p className="text-gray-500 text-sm">Current Price</p>
            <p className="text-2xl font-bold">${prediction.current_price.toFixed(2)}</p>
          </div>

          {/* Confidence */}
          <div>
            <p className="text-gray-500 text-sm">Confidence</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-dark-bg rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${isBuy ? 'bg-stock-green' : 'bg-stock-red'}`}
                  style={{ width: `${Math.min(prediction.confidence, 100)}%` }}
                />
              </div>
              <span className="text-sm font-medium">{prediction.confidence.toFixed(1)}%</span>
            </div>
          </div>

          {/* Prediction Value */}
          <div>
            <p className="text-gray-500 text-sm">Model Output (normalized)</p>
            <p className="text-lg font-mono">{prediction.prediction.toFixed(4)}</p>
          </div>
        </div>
      ) : (
        <div className="text-gray-500 text-center py-8">
          {loading ? 'Analyzing market data...' : 'No prediction available'}
        </div>
      )}

      {/* Train Button */}
      <button
        onClick={trainModel}
        disabled={training}
        className="w-full mt-4 bg-stock-blue/20 hover:bg-stock-blue/30 text-stock-blue py-2 rounded-lg text-sm font-medium transition-colors"
      >
        {training ? '🔄 Training Model...' : '🧠 Retrain Model'}
      </button>
    </div>
  )
}
