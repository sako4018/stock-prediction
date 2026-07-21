export interface Company {
  ticker: string
  name: string
  sector: string
  country: string
  marketCap: string
}

export const POPULAR_STOCKS: Company[] = [
  // Tech Giants
  { ticker: 'AAPL', name: 'Apple Inc.', sector: 'Technology', country: '🇺🇸 USA', marketCap: '$3T' },
  { ticker: 'MSFT', name: 'Microsoft Corp.', sector: 'Technology', country: '🇺🇸 USA', marketCap: '$2.8T' },
  { ticker: 'GOOGL', name: 'Alphabet Inc.', sector: 'Technology', country: '🇺🇸 USA', marketCap: '$1.7T' },
  { ticker: 'AMZN', name: 'Amazon.com Inc.', sector: 'Technology', country: '🇺🇸 USA', marketCap: '$1.5T' },
  { ticker: 'NVDA', name: 'NVIDIA Corp.', sector: 'Technology', country: '🇺🇸 USA', marketCap: '$1.2T' },
  { ticker: 'META', name: 'Meta Platforms', sector: 'Technology', country: '🇺🇸 USA', marketCap: '$800B' },
  { ticker: 'TSLA', name: 'Tesla Inc.', sector: 'Automotive', country: '🇺🇸 USA', marketCap: '$800B' },

  // Finance
  { ticker: 'JPM', name: 'JPMorgan Chase', sector: 'Finance', country: '🇺🇸 USA', marketCap: '$500B' },
  { ticker: 'V', name: 'Visa Inc.', sector: 'Finance', country: '🇺🇸 USA', marketCap: '$500B' },
  { ticker: 'MA', name: 'Mastercard', sector: 'Finance', country: '🇺🇸 USA', marketCap: '$400B' },
  { ticker: 'BAC', name: 'Bank of America', sector: 'Finance', country: '🇺🇸 USA', marketCap: '$300B' },

  // Healthcare
  { ticker: 'JNJ', name: 'Johnson & Johnson', sector: 'Healthcare', country: '🇺🇸 USA', marketCap: '$400B' },
  { ticker: 'UNH', name: 'UnitedHealth', sector: 'Healthcare', country: '🇺🇸 USA', marketCap: '$500B' },
  { ticker: 'PFE', name: 'Pfizer Inc.', sector: 'Healthcare', country: '🇺🇸 USA', marketCap: '$150B' },

  // Consumer
  { ticker: 'WMT', name: 'Walmart Inc.', sector: 'Consumer', country: '🇺🇸 USA', marketCap: '$400B' },
  { ticker: 'PG', name: 'Procter & Gamble', sector: 'Consumer', country: '🇺🇸 USA', marketCap: '$350B' },
  { ticker: 'KO', name: 'Coca-Cola Co.', sector: 'Consumer', country: '🇺🇸 USA', marketCap: '$250B' },
  { ticker: 'PEP', name: 'PepsiCo Inc.', sector: 'Consumer', country: '🇺🇸 USA', marketCap: '$230B' },

  // Energy
  { ticker: 'XOM', name: 'Exxon Mobil', sector: 'Energy', country: '🇺🇸 USA', marketCap: '$450B' },
  { ticker: 'CVX', name: 'Chevron Corp.', sector: 'Energy', country: '🇺🇸 USA', marketCap: '$300B' },

  // International
  { ticker: 'TSM', name: 'Taiwan Semi', sector: 'Technology', country: '🇹🇼 Taiwan', marketCap: '$500B' },
  { ticker: 'ASML', name: 'ASML Holding', sector: 'Technology', country: '🇳🇱 Netherlands', marketCap: '$300B' },
  { ticker: 'SAP', name: 'SAP SE', sector: 'Technology', country: '🇩🇪 Germany', marketCap: '$200B' },
  { ticker: 'NVO', name: 'Novo Nordisk', sector: 'Healthcare', country: '🇩🇰 Denmark', marketCap: '$400B' },
  { ticker: 'SONY', name: 'Sony Group', sector: 'Technology', country: '🇯🇵 Japan', marketCap: '$100B' },

  // Bulgarian/Regional
  { ticker: 'BIOB', name: 'Biovet', sector: 'Healthcare', country: '🇧🇬 Bulgaria', marketCap: '' },
]

export const SECTORS = ['All', 'Technology', 'Finance', 'Healthcare', 'Consumer', 'Energy', 'Automotive']

export function searchCompanies(query: string): Company[] {
  const q = query.toLowerCase()
  return POPULAR_STOCKS.filter(
    c => c.ticker.toLowerCase().includes(q) ||
         c.name.toLowerCase().includes(q) ||
         c.sector.toLowerCase().includes(q)
  )
}
