import CompanyInfo from './CompanyInfo'
import PredictionPanel from './PredictionPanel'
import SignalsPanel from './SignalsPanel'
import StockChart from './StockChart'

interface DashboardProps {
  ticker: string
}

export default function Dashboard({ ticker }: DashboardProps) {
  return (
    <div className="space-y-6">
      {/* Top Row: Company + Prediction + Signals */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <CompanyInfo ticker={ticker} />
        <PredictionPanel ticker={ticker} />
        <SignalsPanel ticker={ticker} />
      </div>

      {/* Full Width Chart */}
      <StockChart ticker={ticker} />
    </div>
  )
}
