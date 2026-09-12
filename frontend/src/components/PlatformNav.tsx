export const VIEWS = [
  { id: 'dashboard', label: 'Overview', key: '1' },
  { id: 'predict', label: 'Predict', key: '2' },
  { id: 'backtest', label: 'Backtest', key: '3' },
  { id: 'signals', label: 'Signals', key: '4' },
  { id: 'fundamentals', label: 'Analysis', key: '5' },
  { id: 'portfolio', label: 'Portfolio', key: '6' },
]

export default function PlatformNav({ active, onChange }: { active: string; onChange: (view: string) => void }) {
  return (
    <nav className="platforms" aria-label="Views">
      {VIEWS.map(v => {
        const on = v.id === active
        return (
          <button key={v.id} onClick={() => onChange(v.id)} className={`platform ${on ? 'is-active' : ''}`}
            aria-current={on ? 'page' : undefined}>
            <span className="platform-no">{v.key}</span>
            <span>{v.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
