import CompanyInfo from './CompanyInfo'
import PredictionPanel from './PredictionPanel'
import SignalsPanel from './SignalsPanel'
import StockChart from './StockChart'

interface DashboardProps {
  ticker: string
}

export default function Dashboard({ ticker }: DashboardProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <CompanyInfo ticker={ticker} />
        <PredictionPanel ticker={ticker} />
        <SignalsPanel ticker={ticker} />
      </div>
      <StockChart ticker={ticker} />
    </div>
  )
}
