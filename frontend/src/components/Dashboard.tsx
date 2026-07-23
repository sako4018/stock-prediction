import PredictionPanel from './PredictionPanel'
import SignalsPanel from './SignalsPanel'
import StockChart from './StockChart'
import FundamentalsPanel from './FundamentalsPanel'
import KeyStats from './KeyStats'
import NewsPanel from './NewsPanel'

export default function Dashboard({ ticker }: { ticker: string }) {
  return (
    <div className="space-y-4" key={ticker}>
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        <div className="xl:col-span-3"><StockChart ticker={ticker} /></div>
        <div className="xl:col-span-2 space-y-4">
          <SignalsPanel ticker={ticker} />
          <KeyStats ticker={ticker} />
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        <div className="xl:col-span-3 space-y-4">
          <PredictionPanel ticker={ticker} />
          <NewsPanel ticker={ticker} />
        </div>
        <div className="xl:col-span-2"><FundamentalsPanel ticker={ticker} /></div>
      </div>
    </div>
  )
}
