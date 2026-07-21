import CompanyInfo from './CompanyInfo'
import PredictionPanel from './PredictionPanel'
import SignalsPanel from './SignalsPanel'
import StockChart from './StockChart'
import FadeIn from './FadeIn'

interface DashboardProps {
  ticker: string
}

export default function Dashboard({ ticker }: DashboardProps) {
  return (
    <div className="space-y-4" key={ticker}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <FadeIn delay={0}><CompanyInfo ticker={ticker} /></FadeIn>
        <FadeIn delay={80}><PredictionPanel ticker={ticker} /></FadeIn>
        <FadeIn delay={160}><SignalsPanel ticker={ticker} /></FadeIn>
      </div>
      <FadeIn delay={240}><StockChart ticker={ticker} /></FadeIn>
    </div>
  )
}
