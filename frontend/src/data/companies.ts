export interface Company {
  ticker: string
  name: string
  sector: string
  country: string
  marketCap: string
}

export const POPULAR_STOCKS: Company[] = [
  // Mega Cap Tech
  { ticker: 'AAPL', name: 'Apple Inc.', sector: 'Technology', country: 'USA', marketCap: '$3T' },
  { ticker: 'MSFT', name: 'Microsoft Corp.', sector: 'Technology', country: 'USA', marketCap: '$2.8T' },
  { ticker: 'GOOGL', name: 'Alphabet Inc.', sector: 'Technology', country: 'USA', marketCap: '$1.7T' },
  { ticker: 'AMZN', name: 'Amazon.com Inc.', sector: 'Technology', country: 'USA', marketCap: '$1.5T' },
  { ticker: 'NVDA', name: 'NVIDIA Corp.', sector: 'Technology', country: 'USA', marketCap: '$1.2T' },
  { ticker: 'META', name: 'Meta Platforms', sector: 'Technology', country: 'USA', marketCap: '$800B' },
  { ticker: 'TSLA', name: 'Tesla Inc.', sector: 'Automotive', country: 'USA', marketCap: '$800B' },

  // Software & Cloud
  { ticker: 'CRM', name: 'Salesforce', sector: 'Technology', country: 'USA', marketCap: '$250B' },
  { ticker: 'ADBE', name: 'Adobe Inc.', sector: 'Technology', country: 'USA', marketCap: '$200B' },
  { ticker: 'SNOW', name: 'Snowflake', sector: 'Technology', country: 'USA', marketCap: '$60B' },
  { ticker: 'PLTR', name: 'Palantir', sector: 'Technology', country: 'USA', marketCap: '$60B' },
  { ticker: 'AMD', name: 'AMD', sector: 'Technology', country: 'USA', marketCap: '$250B' },
  { ticker: 'INTC', name: 'Intel Corp.', sector: 'Technology', country: 'USA', marketCap: '$120B' },
  { ticker: 'ORCL', name: 'Oracle Corp.', sector: 'Technology', country: 'USA', marketCap: '$350B' },
  { ticker: 'NFLX', name: 'Netflix Inc.', sector: 'Technology', country: 'USA', marketCap: '$250B' },
  { ticker: 'DIS', name: 'Walt Disney', sector: 'Technology', country: 'USA', marketCap: '$200B' },

  // Finance
  { ticker: 'JPM', name: 'JPMorgan Chase', sector: 'Finance', country: 'USA', marketCap: '$500B' },
  { ticker: 'V', name: 'Visa Inc.', sector: 'Finance', country: 'USA', marketCap: '$500B' },
  { ticker: 'MA', name: 'Mastercard', sector: 'Finance', country: 'USA', marketCap: '$400B' },
  { ticker: 'BAC', name: 'Bank of America', sector: 'Finance', country: 'USA', marketCap: '$300B' },
  { ticker: 'GS', name: 'Goldman Sachs', sector: 'Finance', country: 'USA', marketCap: '$150B' },
  { ticker: 'MS', name: 'Morgan Stanley', sector: 'Finance', country: 'USA', marketCap: '$150B' },
  { ticker: 'BRK.B', name: 'Berkshire Hathaway', sector: 'Finance', country: 'USA', marketCap: '$800B' },
  { ticker: 'AXP', name: 'American Express', sector: 'Finance', country: 'USA', marketCap: '$150B' },

  // Healthcare
  { ticker: 'JNJ', name: 'Johnson & Johnson', sector: 'Healthcare', country: 'USA', marketCap: '$400B' },
  { ticker: 'UNH', name: 'UnitedHealth', sector: 'Healthcare', country: 'USA', marketCap: '$500B' },
  { ticker: 'PFE', name: 'Pfizer Inc.', sector: 'Healthcare', country: 'USA', marketCap: '$150B' },
  { ticker: 'ABBV', name: 'AbbVie Inc.', sector: 'Healthcare', country: 'USA', marketCap: '$300B' },
  { ticker: 'LLY', name: 'Eli Lilly', sector: 'Healthcare', country: 'USA', marketCap: '$700B' },
  { ticker: 'MRK', name: 'Merck & Co.', sector: 'Healthcare', country: 'USA', marketCap: '$300B' },
  { ticker: 'TMO', name: 'Thermo Fisher', sector: 'Healthcare', country: 'USA', marketCap: '$200B' },
  { ticker: 'ABT', name: 'Abbott Labs', sector: 'Healthcare', country: 'USA', marketCap: '$200B' },

  // Consumer
  { ticker: 'WMT', name: 'Walmart Inc.', sector: 'Consumer', country: 'USA', marketCap: '$400B' },
  { ticker: 'PG', name: 'Procter & Gamble', sector: 'Consumer', country: 'USA', marketCap: '$350B' },
  { ticker: 'KO', name: 'Coca-Cola Co.', sector: 'Consumer', country: 'USA', marketCap: '$250B' },
  { ticker: 'PEP', name: 'PepsiCo Inc.', sector: 'Consumer', country: 'USA', marketCap: '$230B' },
  { ticker: 'COST', name: 'Costco', sector: 'Consumer', country: 'USA', marketCap: '$350B' },
  { ticker: 'MCD', name: "McDonald's", sector: 'Consumer', country: 'USA', marketCap: '$200B' },
  { ticker: 'NKE', name: 'Nike Inc.', sector: 'Consumer', country: 'USA', marketCap: '$150B' },
  { ticker: 'SBUX', name: 'Starbucks', sector: 'Consumer', country: 'USA', marketCap: '$100B' },
  { ticker: 'TGT', name: 'Target Corp.', sector: 'Consumer', country: 'USA', marketCap: '$60B' },

  // Energy
  { ticker: 'XOM', name: 'Exxon Mobil', sector: 'Energy', country: 'USA', marketCap: '$450B' },
  { ticker: 'CVX', name: 'Chevron Corp.', sector: 'Energy', country: 'USA', marketCap: '$300B' },
  { ticker: 'COP', name: 'ConocoPhillips', sector: 'Energy', country: 'USA', marketCap: '$140B' },
  { ticker: 'SLB', name: 'Schlumberger', sector: 'Energy', country: 'USA', marketCap: '$80B' },
  { ticker: 'EOG', name: 'EOG Resources', sector: 'Energy', country: 'USA', marketCap: '$70B' },

  // Industrial
  { ticker: 'CAT', name: 'Caterpillar', sector: 'Industrial', country: 'USA', marketCap: '$170B' },
  { ticker: 'BA', name: 'Boeing Co.', sector: 'Industrial', country: 'USA', marketCap: '$130B' },
  { ticker: 'HON', name: 'Honeywell', sector: 'Industrial', country: 'USA', marketCap: '$130B' },
  { ticker: 'UPS', name: 'UPS Inc.', sector: 'Industrial', country: 'USA', marketCap: '$110B' },
  { ticker: 'GE', name: 'GE Aerospace', sector: 'Industrial', country: 'USA', marketCap: '$180B' },

  // Semiconductor
  { ticker: 'AVGO', name: 'Broadcom', sector: 'Technology', country: 'USA', marketCap: '$700B' },
  { ticker: 'QCOM', name: 'Qualcomm', sector: 'Technology', country: 'USA', marketCap: '$200B' },
  { ticker: 'TXN', name: 'Texas Instruments', sector: 'Technology', country: 'USA', marketCap: '$170B' },
  { ticker: 'MU', name: 'Micron Tech', sector: 'Technology', country: 'USA', marketCap: '$120B' },

  // International
  { ticker: 'TSM', name: 'Taiwan Semi', sector: 'Technology', country: 'Taiwan', marketCap: '$500B' },
  { ticker: 'ASML', name: 'ASML Holding', sector: 'Technology', country: 'Netherlands', marketCap: '$300B' },
  { ticker: 'SAP', name: 'SAP SE', sector: 'Technology', country: 'Germany', marketCap: '$200B' },
  { ticker: 'NVO', name: 'Novo Nordisk', sector: 'Healthcare', country: 'Denmark', marketCap: '$400B' },
  { ticker: 'SONY', name: 'Sony Group', sector: 'Technology', country: 'Japan', marketCap: '$100B' },
  { ticker: 'BABA', name: 'Alibaba', sector: 'Technology', country: 'China', marketCap: '$200B' },
  { ticker: 'JD', name: 'JD.com', sector: 'Technology', country: 'China', marketCap: '$50B' },
  { ticker: 'PYPL', name: 'PayPal', sector: 'Finance', country: 'USA', marketCap: '$70B' },
  { ticker: 'UBER', name: 'Uber Technologies', sector: 'Technology', country: 'USA', marketCap: '$150B' },
  { ticker: 'ABNB', name: 'Airbnb Inc.', sector: 'Technology', country: 'USA', marketCap: '$80B' },
  { ticker: 'SQ', name: 'Block Inc.', sector: 'Finance', country: 'USA', marketCap: '$40B' },
  { ticker: 'SHOP', name: 'Shopify', sector: 'Technology', country: 'Canada', marketCap: '$100B' },
  { ticker: 'SE', name: 'Sea Limited', sector: 'Technology', country: 'Singapore', marketCap: '$40B' },

  // Crypto ETFs
  { ticker: 'IBIT', name: 'iShares Bitcoin Trust', sector: 'Crypto ETF', country: 'USA', marketCap: '$50B' },
  { ticker: 'BITO', name: 'ProShares Bitcoin Strategy', sector: 'Crypto ETF', country: 'USA', marketCap: '$2B' },
  { ticker: 'COIN', name: 'Coinbase Global', sector: 'Crypto ETF', country: 'USA', marketCap: '$50B' },
  { ticker: 'MSTR', name: 'MicroStrategy', sector: 'Crypto ETF', country: 'USA', marketCap: '$30B' },
  { ticker: 'MARA', name: 'Marathon Digital', sector: 'Crypto ETF', country: 'USA', marketCap: '$5B' },
  { ticker: 'RIOT', name: 'Riot Platforms', sector: 'Crypto ETF', country: 'USA', marketCap: '$3B' },

  // REITs
  { ticker: 'PLD', name: 'Prologis', sector: 'REITs', country: 'USA', marketCap: '$120B' },
  { ticker: 'AMT', name: 'American Tower', sector: 'REITs', country: 'USA', marketCap: '$100B' },
  { ticker: 'EQIX', name: 'Equinix', sector: 'REITs', country: 'USA', marketCap: '$80B' },
  { ticker: 'SPG', name: 'Simon Property', sector: 'REITs', country: 'USA', marketCap: '$50B' },

  // Defense
  { ticker: 'LMT', name: 'Lockheed Martin', sector: 'Defense', country: 'USA', marketCap: '$120B' },
  { ticker: 'RTX', name: 'RTX Corp.', sector: 'Defense', country: 'USA', marketCap: '$140B' },
  { ticker: 'NOC', name: 'Northrop Grumman', sector: 'Defense', country: 'USA', marketCap: '$80B' },
  { ticker: 'GD', name: 'General Dynamics', sector: 'Defense', country: 'USA', marketCap: '$75B' },
  { ticker: 'LHX', name: 'L3Harris Tech', sector: 'Defense', country: 'USA', marketCap: '$45B' },

  // More Healthcare
  { ticker: 'AMGN', name: 'Amgen Inc.', sector: 'Healthcare', country: 'USA', marketCap: '$150B' },
  { ticker: 'GILD', name: 'Gilead Sciences', sector: 'Healthcare', country: 'USA', marketCap: '$100B' },
  { ticker: 'ISRG', name: 'Intuitive Surgical', sector: 'Healthcare', country: 'USA', marketCap: '$150B' },
  { ticker: 'REGN', name: 'Regeneron', sector: 'Healthcare', country: 'USA', marketCap: '$100B' },
]

export const SECTORS = ['All', 'Technology', 'Finance', 'Healthcare', 'Consumer', 'Energy', 'Industrial', 'Automotive', 'Crypto ETF', 'REITs', 'Defense']

export function searchCompanies(query: string): Company[] {
  const q = query.toLowerCase()
  const results = POPULAR_STOCKS.filter(
    c => c.ticker.toLowerCase().includes(q) ||
         c.name.toLowerCase().includes(q) ||
         c.sector.toLowerCase().includes(q)
  )

  // If query looks like a valid ticker (1-5 uppercase letters) and not found in list, offer it
  if (results.length === 0 && /^[A-Za-z]{1,5}$/.test(query.trim())) {
    results.push({
      ticker: query.toUpperCase(),
      name: 'Search on Yahoo Finance',
      sector: 'Custom',
      country: 'Global',
      marketCap: ''
    })
  }

  return results
}
