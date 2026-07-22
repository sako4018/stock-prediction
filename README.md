# Stock Prediction System

Full-stack stock prediction dashboard with LSTM Neural Network (PyTorch), real-time data, and interactive React frontend.

## Features

- **Real-time data** from Yahoo Finance (yfinance)
- **LSTM Neural Network** with Attention mechanism (PyTorch, GPU support)
- **5-Voter Signal System** — ML, RSI, MACD, Price Trend, Sentiment vote UP/DOWN
- **Interactive Dashboard** — dark/light theme, live prices, charts
- **Technical Indicators** — RSI, MACD, Bollinger Bands, Stochastic, Williams %R
- **News Sentiment** — keyword-based analysis from Google News RSS
- **Backtesting** — simulated trading with Sharpe/Sortino/Max Drawdown metrics
- **Portfolio Optimization** — efficient frontier, diversification metrics
- **Batch Training** — train models for multiple tickers at once
- **Price Alerts** — set price/RSI thresholds
- **Multi-Timeframe Analysis** — daily/weekly/monthly signals

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| Backend | Python, FastAPI, Uvicorn |
| ML | PyTorch (LSTM + Attention), scikit-learn |
| Data | yfinance, Google News RSS |
| Fonts | Space Grotesk, JetBrains Mono, DM Sans |

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- NVIDIA GPU (optional, for faster training)

### Backend

```bash
cd stock-prediction
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Usage

### Start both servers

**Terminal 1 — Backend:**
```bash
cd stock-prediction
PYTHONIOENCODING=utf-8 python backend/app.py
```

**Terminal 2 — Frontend:**
```bash
cd stock-prediction/frontend
npm run dev
```

Open http://localhost:5173

### CLI (alternative)

```bash
# Train a model
python main.py --ticker AAPL --train --epochs 50

# Predict
python main.py --ticker AAPL --predict

# Backtest
python main.py --ticker AAPL --backtest
```

## Project Structure

```
stock-prediction/
├── backend/
│   ├── app.py                    # FastAPI server (all API endpoints)
│   └── export.py                 # Report generation
├── frontend/
│   ├── src/
│   │   ├── App.tsx               # Main app layout
│   │   ├── ThemeContext.tsx       # Dark/light theme
│   │   ├── index.css             # CSS variables + theme colors
│   │   ├── components/
│   │   │   ├── Sidebar.tsx       # Navigation sidebar
│   │   │   ├── Dashboard.tsx     # Main dashboard view
│   │   │   ├── StockChart.tsx    # Candlestick/area chart (SVG)
│   │   │   ├── PredictionPanel.tsx  # UP/DOWN signal display
│   │   │   ├── SignalsPanel.tsx  # Technical indicator gauges
│   │   │   ├── FundamentalsPanel.tsx
│   │   │   ├── BacktestPanel.tsx
│   │   │   ├── PortfolioOptimizer.tsx
│   │   │   ├── HeroPrice.tsx     # Live price display
│   │   │   ├── TickerTape.tsx    # Scrolling price ticker
│   │   │   ├── Watchlist.tsx
│   │   │   ├── AlertsPanel.tsx
│   │   │   ├── BatchTrainPanel.tsx
│   │   │   └── CompanySelector.tsx
│   │   └── data/
│   │       └── companies.ts      # Stock catalog
│   ├── tailwind.config.js
│   └── package.json
├── src/
│   ├── model.py                  # LSTM Neural Network (PyTorch)
│   ├── data_collection.py        # Yahoo Finance data fetcher
│   ├── preprocessing.py          # Technical indicators + normalization
│   ├── combined_signal.py        # 5-voter majority vote system
│   ├── sentiment.py              # News sentiment analysis
│   ├── backtest.py               # Backtesting + walk-forward validation
│   ├── fundamentals.py           # Company fundamentals (P/E, ROE, etc.)
│   ├── portfolio.py              # Portfolio tracking
│   ├── portfolio_optimization.py # Efficient frontier optimization
│   ├── multi_timeframe.py        # Daily/weekly/monthly analysis
│   ├── sector_analysis.py        # Sector correlation analysis
│   ├── alerts.py                 # Price/RSI alert system
│   ├── batch_train.py            # Multi-ticker training
│   ├── performance.py            # Performance tracking
│   └── ensemble.py               # Ensemble methods
├── models/                       # Saved PyTorch models (.pt)
├── main.py                       # CLI entry point
├── requirements.txt
├── Dockerfile.backend
├── Dockerfile.frontend
└── docker-compose.yml
```

## Signal System

The prediction uses a **5-voter majority vote**:

| Voter | Logic |
|-------|-------|
| ML Model | Predicted price > 0.55 → UP, < 0.45 → DOWN |
| RSI | < 35 → UP (oversold), > 65 → DOWN (overbought) |
| MACD | MACD > signal line → UP, else DOWN |
| Price Trend | Price > SMA20 → UP, below → DOWN |
| Sentiment | Bullish score > 0.15 → UP, bearish < -0.15 → DOWN |

**Decision:** Majority wins. If no clear majority → "Uncertain" (no signal).

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/stocks/{ticker}` | Real-time price + company info |
| `GET /api/stocks/{ticker}/history` | Historical OHLCV data |
| `GET /api/stocks/{ticker}/combined` | 5-voter signal prediction |
| `GET /api/stocks/{ticker}/signals` | Technical indicator values |
| `GET /api/stocks/{ticker}/fundamentals` | P/E, ROE, revenue growth |
| `GET /api/stocks/{ticker}/backtest` | Backtest results |
| `GET /api/stocks/{ticker}/multi-timeframe` | Daily/weekly/monthly analysis |
| `GET /api/alerts?ticker=X` | List price alerts |
| `POST /api/alerts/{ticker}` | Create alert |
| `GET /api/portfolio` | Portfolio overview |
| `POST /api/optimize/max-sharpe` | Portfolio optimization |
| `POST /api/train/batch` | Batch train multiple tickers |

## Warning

**This is an educational project!**

Do NOT invest real money based solely on this model. Past results do not guarantee future performance. The stock market is risky and you can lose money.

Always consult a financial advisor before investing.

---

Made on Earth by Sercho
