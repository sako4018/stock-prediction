import StockChart from './StockChart'
import DepartureBoard from './DepartureBoard'

export default function Dashboard({ ticker }: { ticker: string }) {
  return (
    <div className="space-y-6" key={ticker}>
      <DepartureBoard ticker={ticker} />
      <StockChart ticker={ticker} />
    </div>
  )
}
