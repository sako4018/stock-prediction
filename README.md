# Stock Prediction System

Full-stack stock prediction dashboard with LSTM Neural Network (PyTorch), real-time data, and interactive React frontend.

## Features

- **Real-time data** from Yahoo Finance (yfinance)
- **LSTM Neural Network** with Attention mechanism (PyTorch, GPU support)
- **Point-in-time feature pipeline** — price/technical + market indices +
  news sentiment + fundamentals, all joined so the model only ever sees
  information that was actually public at each moment (no leakage)
- **5-Voter Signal System** — ML, RSI, MACD, Price Trend, Sentiment vote UP/DOWN
- **Interactive Dashboard** — dark/light theme, live prices, charts, market overview
- **Technical Indicators** — RSI, MACD, Bollinger Bands, Stochastic, Williams %R
- **News Sentiment** — keyword-based analysis from Google News RSS, with
  deduplication and a real per-article timestamp
- **Market Context** — S&P 500, NASDAQ, VIX, Dow, 10Y Treasury yield
- **Point-in-time Fundamentals** — EPS/earnings surprise/P/E as they were
  actually known on each historical date, not today's snapshot applied backward
- **Feature Importance** — permutation importance (model-agnostic)
- **Ablation Comparison** — Buy&Hold vs ML vs ML+Market vs ML+News vs
  ML+Fundamentals vs ML+All, real computed backtest numbers
- **Walk-Forward Validation** — rolling train/test folds with a purge gap,
  not a single lucky split
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

### Windows (PowerShell)

Same commands work in PowerShell as-is. If you hit `UnicodeEncodeError`
in the console, set UTF-8 output first:

```powershell
$env:PYTHONIOENCODING = "utf-8"
pip install -r requirements.txt
```

### Environment variables (optional)

The project works with **zero configuration** — market data comes from
`yfinance` (no key) and news from the free Google News RSS feed (no key).
Copy `.env.example` to `.env` only if you want to override defaults or
plug in a paid provider later:

```powershell
copy .env.example .env
```

```
NEWS_API_KEY=            # optional — for a future paid news provider
MARKET_DATA_API_KEY=     # optional — for a future paid market data provider
DEFAULT_TICKER=AAPL
DEFAULT_PERIOD=2y
NEWS_WINDOW_HOURS=24
DEFAULT_FEATURE_GROUPS=price,technical
```

See `src/config.py` for the full list of overridable settings.

## Usage

### Start both servers

**Terminal 1 — Backend:**
```bash
cd stock-prediction
PYTHONIOENCODING=utf-8 python backend/app.py
```
PowerShell equivalent:
```powershell
cd stock-prediction
$env:PYTHONIOENCODING = "utf-8"
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
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

# Backtest (single train/test split)
python main.py --ticker AAPL --backtest

# Walk-forward validation (rolling folds, more reliable than --backtest)
python main.py --ticker AAPL --walkforward
```

### Data pipeline (market / news / fundamentals)

```bash
# Market indices — no setup needed, fetched from yfinance on first use
python src/market_data.py

# News backfill for a date range (needed once before news features are usable
# for training; live prediction fetches news fresh automatically)
python -c "
import sys; sys.path.insert(0, 'src')
from datetime import datetime, timezone, timedelta
from news_data import fetch_historical_news, enrich_with_sentiment, deduplicate_articles, save_articles
end = datetime.now(timezone.utc)
start = end - timedelta(days=180)
arts = fetch_historical_news('AAPL', 'Apple', start, end)
arts = enrich_with_sentiment(arts)
arts = deduplicate_articles(arts)
save_articles('AAPL', arts)
"

# Full feature pipeline (price + technical + market + news + fundamentals)
python -c "
import sys; sys.path.insert(0, 'src')
from feature_pipeline import build_dataset
r = build_dataset('AAPL', period='2y', feature_groups=('price','technical','market','news','fundamental'))
print(r['X'].shape, r['feature_groups'])
"

# Ablation comparison (Buy&Hold / ML / ML+Market / ML+News / ML+Fundamentals / ML+All)
python src/ablation.py
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
│   ├── sentiment.py              # Live news sentiment (UI, keyword heuristic)
│   ├── news_data.py              # Point-in-time news: fetch, dedup, embargo,
│   │                              #   rolling sentiment aggregates (training)
│   ├── market_data.py            # S&P500/NASDAQ/VIX/Dow/10Y — index features
│   ├── backtest.py               # Backtesting + walk-forward validation
│   ├── fundamentals.py           # Live fundamentals (UI) + point-in-time
│   │                              #   earnings timeline (training)
│   ├── feature_pipeline.py       # Orchestrator — combines price/technical/
│   │                              #   market/news/fundamental into one dataset
│   ├── feature_importance.py     # Permutation feature importance
│   ├── ablation.py               # Buy&Hold vs ML vs ML+X comparison
│   ├── config.py                 # Central settings, .env-overridable
│   ├── portfolio.py              # Portfolio tracking
│   ├── portfolio_optimization.py # Efficient frontier optimization
│   ├── multi_timeframe.py        # Daily/weekly/monthly analysis
│   ├── sector_analysis.py        # Sector correlation analysis
│   ├── alerts.py                 # Price/RSI alert system
│   ├── batch_train.py            # Multi-ticker training
│   ├── performance.py            # Performance tracking
│   └── ensemble.py               # Ensemble methods
├── models/                       # Saved PyTorch models (.pt + scaler + config)
├── data/
│   ├── market/                   # Cached raw index prices (gitignored)
│   └── news/raw/                 # Cached raw news articles, JSONL (gitignored)
├── tests/
│   ├── test_pipeline.py          # ML pipeline: leakage, alignment, walk-forward
│   ├── test_combined_signal.py   # 5-voter signal logic
│   └── test_data_sources.py      # Market/news/fundamentals: as-of joins,
│                                  #   dedup, embargo, the future-news leakage test
├── main.py                       # CLI entry point
├── requirements.txt
├── .env.example                  # Copy to .env — everything works without one
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

## Data Pipeline & Point-in-Time Correctness

Adding market/news/fundamental data to a training pipeline is easy to get
wrong: if a feature for date T can see information that only became public
after T, the model looks smarter in backtests than it will ever be live.
This project's rule: **every new feature carries a real `available_at`
timestamp, and is joined with `pandas.merge_asof(direction='backward')`**,
which by construction can never pick a future row.

- **Market** (`src/market_data.py`): daily index closes, `available_at` =
  the trading day itself.
- **Fundamentals** (`src/fundamentals.py`, `get_fundamentals_timeline()`):
  `available_at` = the real earnings-announcement timestamp (with time of
  day, from `yfinance`'s `earnings_dates`) — not the fiscal period end.
  A value stays valid until the *next* report, then is superseded.
- **News** (`src/news_data.py`): live articles keep their real timestamp
  (hour-precision). **Historical backfill is different and disclosed
  openly**: Google News RSS's date-range search only returns the
  *calendar day* of publication, not a trustworthy hour, so backfilled
  articles get a full one-day embargo (`available_at` = next day, 00:00
  UTC) rather than a fabricated precise time.

Other leakage guards already in place (see `tests/`):
- `StandardScaler` is fit **only on training rows**, per walk-forward fold.
- No `bfill()` anywhere — warmup rows without full history are dropped,
  never filled from the future.
- `tests/test_data_sources.py::test_future_news_excluded_from_features`
  constructs a news article timestamped *after* a prediction moment and
  asserts it has zero effect on that moment's features — the exact
  scenario this needs to prevent.
- `tests/test_pipeline.py::test_random_data_gives_no_edge` trains on pure
  noise and asserts accuracy stays near 50% — a leak would show up as
  suspiciously high accuracy on data that has no real signal.

Train/test splits are always chronological (`WalkForwardValidator` rolls
forward in time with a purge gap; nothing is ever shuffled).

### Known data-provider limitations

- **News backfill has only day-level precision** (see above) — live
  predictions get real hour precision, historical training data doesn't.
- **Revenue / net income only go back ~5 quarters** (yfinance's free
  `quarterly_financials`), far short of a multi-year training window.
  `revenue_yoy_growth` / `net_income_margin` are therefore *not* used as
  trainable features (they'd be NaN for ~90% of a 2-year window) — only
  EPS/surprise/P/E, which come from `earnings_dates` and go back ~6 years.
- **Analyst targets, recommendations, margins, debt/equity in the live
  `/fundamentals` panel have no historical endpoint in yfinance** — they
  reflect *today* only and are never used as training features for past
  dates (only the live UI panel).
- **Google News RSS is free but unofficial** — no SLA, and it showed
  occasional timeouts under rapid repeated requests during testing; the
  backfill function retries with backoff, but a large multi-year backfill
  will take real wall-clock time (minutes, not seconds).
- Google News RSS and yfinance require **no API key**. `NEWS_API_KEY` /
  `MARKET_DATA_API_KEY` in `.env.example` are unused placeholders for a
  future paid provider swap-in if either free source ever becomes
  unreliable — `src/news_data.py` is structured so a new provider class
  can be dropped in without touching the rest of the pipeline.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/stocks/{ticker}` | Real-time price + company info |
| `GET /api/stocks/{ticker}/history` | Historical OHLCV data |
| `GET /api/stocks/{ticker}/combined` | 5-voter signal prediction |
| `GET /api/stocks/{ticker}/signals` | Technical indicator values |
| `GET /api/stocks/{ticker}/fundamentals` | P/E, ROE, revenue growth (live) |
| `GET /api/stocks/{ticker}/backtest` | Backtest results (single split) |
| `GET /api/stocks/{ticker}/multi-timeframe` | Daily/weekly/monthly analysis |
| `GET /api/market/overview` | S&P500/NASDAQ/VIX/Dow/10Y — live snapshot |
| `GET /api/news/{ticker}` | Deduplicated live news + sentiment |
| `GET /api/stocks/{ticker}/feature-importance` | Permutation importance (cached; `?recompute=true` to refresh) |
| `GET /api/stocks/{ticker}/comparison` | Buy&Hold vs ML vs ML+X ablation table (cached; `?recompute=true` to refresh) |
| `GET /api/alerts?ticker=X` | List price alerts |
| `POST /api/alerts/{ticker}` | Create alert |
| `GET /api/portfolio` | Portfolio overview |
| `POST /api/optimize/max-sharpe` | Portfolio optimization |
| `POST /api/train/batch` | Batch train multiple tickers |

## Tests

```bash
python tests/test_pipeline.py        # ML pipeline: leakage, alignment, walk-forward (19 tests)
python tests/test_combined_signal.py # 5-voter signal logic (15 tests)
python tests/test_data_sources.py    # market/news/fundamentals as-of joins, dedup, embargo (20 tests)
```

No pytest dependency — each file is a standalone runner, exits non-zero
on failure.

## Warning

**This is an educational project!**

Do NOT invest real money based solely on this model. Past results do not guarantee future performance. The stock market is risky and you can lose money.

Always consult a financial advisor before investing.

---

Made on Earth by Sercho
