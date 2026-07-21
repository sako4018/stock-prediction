import PredictionPanel from './PredictionPanel'
import SignalsPanel from './SignalsPanel'
import StockChart from './StockChart'
import FundamentalsPanel from './FundamentalsPanel'
import FadeIn from './FadeIn'

interface DashboardProps {
  ticker: string
}

export default function Dashboard({ ticker }: DashboardProps) {
  return (
    <div className="space-y-4" key={ticker}>
      {/* Hero: Full-width chart */}
      <FadeIn delay={0}>
        <StockChart ticker={ticker} />
      </FadeIn>

      {/* Prediction: Full-width horizontal breakdown */}
      <FadeIn delay={100}>
        <PredictionPanel ticker={ticker} />
      </FadeIn>

      {/* Bottom: Signals + Fundamentals side by side */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <FadeIn delay={200}>
          <SignalsPanel ticker={ticker} />
        </FadeIn>
        <FadeIn delay={300}>
          <FundamentalsPanel ticker={ticker} />
        </FadeIn>
      </div>
    </div>
  )
}
