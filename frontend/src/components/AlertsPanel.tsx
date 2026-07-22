import { useState, useEffect } from 'react'

interface Props { ticker: string }

export default function AlertsPanel({ ticker }: Props) {
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [newType, setNewType] = useState('price_above')
  const [newValue, setNewValue] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => { fetchAlerts() }, [ticker])

  const fetchAlerts = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/alerts?ticker=${ticker}`)
      const json = await res.json()
      setAlerts(json.alerts || [])
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const createAlert = async () => {
    if (!newValue) return
    setCreating(true)
    try {
      await fetch(`/api/alerts/${ticker}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_type: newType, value: parseFloat(newValue), note: '' })
      })
      setNewValue('')
      await fetchAlerts()
    } catch (err) { console.error(err) }
    setCreating(false)
  }

  const deleteAlert = async (id: string) => {
    try {
      await fetch(`/api/alerts/${id}`, { method: 'DELETE' })
      await fetchAlerts()
    } catch (err) { console.error(err) }
  }

  const typeLabels: Record<string, string> = {
    price_above: 'Price Above',
    price_below: 'Price Below',
    rsi_above: 'RSI Above',
    rsi_below: 'RSI Below',
  }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="section-header" style={{ border: 'none', paddingBottom: 0, marginBottom: 0 }}>Price Alerts</span>
        <button onClick={fetchAlerts} disabled={loading} className="text-xxs text-accent hover:text-accent-hover disabled:text-txt-dim">
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {/* Create Alert */}
      <div className="flex gap-2 mb-3">
        <select value={newType} onChange={e => setNewType(e.target.value)}
          className="bg-surface-elevated border border-line rounded px-2 py-1 text-xs text-txt flex-shrink-0">
          {Object.entries(typeLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <input type="number" value={newValue} onChange={e => setNewValue(e.target.value)}
          placeholder="Value" className="bg-surface-elevated border border-line rounded px-2 py-1 text-xs text-txt w-20" />
        <button onClick={createAlert} disabled={creating || !newValue}
          className="px-3 py-1 bg-accent text-white rounded text-xs font-medium hover:bg-accent-hover disabled:opacity-50">
          {creating ? '...' : '+'}
        </button>
      </div>

      {/* Alert List */}
      <div className="space-y-1">
        {alerts.length === 0 && !loading && (
          <p className="text-xxs text-txt-dim text-center py-4">No alerts for {ticker}</p>
        )}
        {alerts.map(alert => (
          <div key={alert.id} className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-surface-overlay group">
            <div className="flex items-center gap-2">
              <span className={`w-1.5 h-1.5 rounded-full ${alert.triggered ? 'bg-warn' : 'bg-up'}`} />
              <span className="text-xs text-txt">{typeLabels[alert.alert_type] || alert.alert_type}</span>
              <span className="text-xs text-txt-sec font-medium tabular-nums">
                {alert.alert_type.includes('price') ? `$${alert.value}` : alert.value}
              </span>
            </div>
            <button onClick={() => deleteAlert(alert.id)}
              className="opacity-0 group-hover:opacity-100 text-txt-dim hover:text-down text-xxs transition-opacity">
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
