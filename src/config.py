"""
Централна конфигурация
=======================
Настройки, които преди бяха пръснати hardcoded на различни места
(различен default period в различни backend routes, seq_length=60
повторен на 10 места и т.н.). Overridable през .env файл — виж
.env.example в root-а на проекта.

Не заменя ВСЕКИ hardcoded default в проекта (напр. portfolio.py,
sector_analysis.py не са пипани — несвързани с тази задача), само
новия news/market/fundamentals код и най-очевидните CLI defaults.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv вече е в requirements.txt, но ако липсва в
    # конкретната среда, просто ползваме os.environ директно —
    # .env файл просто няма да се зареди автоматично.
    pass


def _env_int(name, default):
    v = os.getenv(name)
    try:
        return int(v) if v else default
    except ValueError:
        return default


def _env_float(name, default):
    v = os.getenv(name)
    try:
        return float(v) if v else default
    except ValueError:
        return default


def _env_list(name, default_csv):
    v = os.getenv(name, default_csv)
    return tuple(x.strip() for x in v.split(',') if x.strip())


# --- Основни ---
DEFAULT_TICKER = os.getenv('DEFAULT_TICKER', 'AAPL')
DEFAULT_TIMEFRAME = os.getenv('DEFAULT_TIMEFRAME', '1d')
DEFAULT_PERIOD = os.getenv('DEFAULT_PERIOD', '2y')

# --- Модел / prediction ---
PREDICTION_HORIZON_DAYS = _env_int('PREDICTION_HORIZON_DAYS', 1)
SEQUENCE_LENGTH = _env_int('SEQUENCE_LENGTH', 60)
TRAIN_SIZE = _env_float('TRAIN_SIZE', 0.8)

# --- Walk-forward валидация ---
WALKFORWARD_TRAIN_WINDOW = _env_int('WALKFORWARD_TRAIN_WINDOW', 252)
WALKFORWARD_TEST_WINDOW = _env_int('WALKFORWARD_TEST_WINDOW', 63)
WALKFORWARD_STEP_SIZE = _env_int('WALKFORWARD_STEP_SIZE', 21)

# --- News ---
NEWS_WINDOW_HOURS = _env_int('NEWS_WINDOW_HOURS', 24)
NEWS_PROVIDER = os.getenv('NEWS_PROVIDER', 'google_rss')
NEWS_API_KEY = os.getenv('NEWS_API_KEY') or None  # незадължителен, за бъдещ платен provider

# --- Market data ---
MARKET_DATA_API_KEY = os.getenv('MARKET_DATA_API_KEY') or None  # незадължителен, текущата
                                                                  # имплементация ползва yfinance, без ключ

# --- Feature групи, включени по подразбиране ---
# 'price'/'technical' винаги достъпни без нов dependency/ключ.
# 'market'/'news'/'fundamental' изискват мрежа при първо изтегляне,
# после се кешират локално (data/market/, data/news/raw/).
DEFAULT_FEATURE_GROUPS = _env_list('DEFAULT_FEATURE_GROUPS', 'price,technical')
