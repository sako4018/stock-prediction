"""
Feature Pipeline Orchestrator
==============================
Единственото място, където групите features (price / technical / market /
news / fundamental) се комбинират в един dataset за модела. Целта: да се
вижда ясно кои features реално участват в prediction-а, вместо имената им
да са пръснати hardcoded на много места.

Не пипа съществуващия StockDataPreprocessor — само го оркестрира и му
добавя нови колони чрез as-of присъединяване, преди normalize_data().
"""

import pandas as pd

from data_collection import StockDataCollector
from preprocessing import StockDataPreprocessor
import market_data
import fundamentals as fundamentals_module
import news_data
import config as cfg

ALL_FEATURE_GROUPS = ('price', 'technical', 'market', 'news', 'fundamental')

# 'price'/'technical' идват директно от StockDataPreprocessor и не се
# делят изкуствено на две отделни изчислителни стъпки (RSI и Close_vs_SMA20
# минават през еднакъв код) — тук просто показваме кои от новите features
# по смисъл са "сурово ниво на цената" срещу "производен индикатор", за
# прозрачност, не защото pipeline-ът реално ги смята различно.
_PRICE_LIKE_KEYWORDS = ('Close_vs_', 'SMA', 'EMA', 'BB_', 'HL_Range', 'OC_Range',
                        'Gap_Pct', 'Volume_Ratio', 'OBV_Norm', 'Volatility_Ratio',
                        'Price_Change', 'Volume_Change', 'ROC_', 'Higher_', 'Lower_',
                        'Day_Of_Week', 'Is_Quarter', 'Is_Month')


def _split_price_technical(columns):
    price, technical = [], []
    for c in columns:
        (price if any(k in c for k in _PRICE_LIKE_KEYWORDS) else technical).append(c)
    return price, technical


def _merge_market(preprocessor, period):
    """Добавя market-index features чрез merge_asof (backward-only)."""
    print("[MARKET] Зареждане на пазарни индекси...")
    collector = market_data.MarketIndexCollector(period=period)
    idx_data = collector.load_cached()

    # Кешът може да е от по-къс период (напр. от предишен --predict с 6mo),
    # докато сега ни трябват данни чак до началото на цената на акцията.
    # Празен/твърде плитък кеш -> пресвалим, вместо тихо да留 половината
    # редове без market покритие по-долу.
    needed_start = pd.to_datetime(preprocessor.data['Date'], utc=True).min()
    stale = True
    if idx_data:
        earliest_cached = min(
            pd.to_datetime(df['Date'], utc=True).min() for df in idx_data.values()
        )
        stale = earliest_cached > needed_start
    if not idx_data or stale:
        idx_data = collector.fetch_all()
    if not idx_data:
        print("[FEATURES][WARN] Няма пазарни данни — market групата остава празна")
        return []

    feats = market_data.compute_market_features(idx_data)
    if feats.empty:
        return []

    left = preprocessor.data.copy()
    # .astype('datetime64[ns, UTC]') нормализира прецизността — merge_asof
    # отказва да съедини ключове от различна резолюция (s срещу us срещу ns),
    # а различните pandas операции по веригата могат да върнат различна.
    left['Date'] = pd.to_datetime(left['Date'], utc=True).astype('datetime64[ns, UTC]')
    feats = feats.copy()
    feats['Date'] = pd.to_datetime(feats['Date'], utc=True).astype('datetime64[ns, UTC]')
    feats = feats.sort_values('Date')

    merged = pd.merge_asof(left.sort_values('Date'), feats, on='Date', direction='backward')
    preprocessor.data = merged
    new_cols = [c for c in feats.columns if c != 'Date']
    print(f"[MARKET] Добавени {len(new_cols)} market features")
    return new_cols


def _merge_fundamentals(preprocessor, ticker):
    """Добавя point-in-time fundamentals чрез merge_asof (backward-only)."""
    print(f"[FUNDAMENTALS] Изграждане на as-of timeline за {ticker}...")
    price_hist = preprocessor.data[['Date', 'Close']]
    timeline = fundamentals_module.get_fundamentals_timeline(ticker, price_history=price_hist)

    if timeline.empty:
        print(f"[FEATURES][WARN] Няма earnings история за {ticker} — fundamental групата остава празна")
        return []

    # revenue/net_income идват от quarterly_financials, която yfinance
    # (безплатен tier) връща само за последните ~5 тримесечия (~15 месеца)
    # — много по-плитко от eps_estimate/eps_actual (от earnings_dates,
    # ~24 тримесечия/6 години назад). Производни от тях (YoY growth,
    # margin) биха били NaN за по-голямата част от 2-годишния тренировъчен
    # прозорец — или ги пропускаме, или изхвърляме ~90% от редовете при
    # dropna. Затова НЕ влизат в trainable features тук; остават в
    # get_fundamentals_timeline()'s суров изход за друга употреба.
    merged = fundamentals_module.merge_fundamentals_asof(preprocessor.data, timeline)
    preprocessor.data = merged

    new_cols = ['eps_estimate', 'eps_actual', 'surprise_pct',
               'trailing_eps_ttm', 'pe_ratio_at_report']
    print(f"[FUNDAMENTALS] Добавени {len(new_cols)} fundamental features "
         f"({len(timeline)} earnings събития; revenue/net_income изключени — "
         f"покритие само ~5 тримесечия в безплатния yfinance tier)")
    return new_cols


def _merge_news(preprocessor, ticker):
    """Добавя агрегирани news features от локалния кеш (виж news_data.py)."""
    print(f"[NEWS] Зареждане на кеширани новини за {ticker}...")
    articles = news_data.load_cached_articles(ticker)
    if not articles:
        print(f"[FEATURES][WARN] Няма кеширани новини за {ticker} — "
             f"новинарските features ще са 0/неутрални за целия период. "
             f"Пусни news_data.fetch_historical_news() + save_articles() първо.")

    target_dates = preprocessor.data['Date']
    feats = news_data.compute_news_features(articles, target_dates)
    feats = feats.rename(columns={'timestamp': 'Date'})
    feats['Date'] = pd.to_datetime(feats['Date'], utc=True).astype('datetime64[ns, UTC]')

    left = preprocessor.data.copy()
    left['Date'] = pd.to_datetime(left['Date'], utc=True).astype('datetime64[ns, UTC]')
    merged = left.merge(feats, on='Date', how='left')

    new_cols = list(news_data.NEWS_FEATURE_COLUMNS)
    for c in new_cols:
        merged[c] = merged[c].fillna(0.0)  # ден без покритие в кеша = без новини, не непознато

    preprocessor.data = merged
    print(f"[NEWS] Добавени {len(new_cols)} news features от {len(articles)} статии")
    return new_cols


def build_raw_frame(ticker, period=None, feature_groups=None, days_ahead=None,
                    price_data=None):
    """
    Суровата (нескалирана) част от pipeline-а: сваляне -> индикатори ->
    target -> по избор market/fundamental/news -> изхвърляне на редовете
    без пълно покритие.

    Изнесена отделно, защото pooled_dataset.py има нужда точно от този
    междинен резултат: там скалерът се учи от всички тикери наведнъж,
    затова нормализацията не може да стане тук, за всеки тикер поотделно.

    Параметри:
    ----------
    price_data : pandas.DataFrame, optional
        Вече свалени OHLCV данни (напр. от локален кеш). Ако липсва,
        се сваля наново.

    Връща:
    -------
    tuple: (preprocessor, used_groups)
    """
    period = period or cfg.DEFAULT_PERIOD
    feature_groups = tuple(feature_groups or cfg.DEFAULT_FEATURE_GROUPS)
    days_ahead = days_ahead or cfg.PREDICTION_HORIZON_DAYS

    unknown = set(feature_groups) - set(ALL_FEATURE_GROUPS)
    if unknown:
        raise ValueError(f"[FEATURES] Непознати feature групи: {unknown}. "
                         f"Позволени: {ALL_FEATURE_GROUPS}")

    print(f"[FEATURES] Групи: {feature_groups}")

    if price_data is None:
        collector = StockDataCollector(ticker=ticker, period=period, interval='1d')
        price_data = collector.fetch_stock_data(save_to_csv=False)
    if price_data is None or price_data.empty:
        raise ValueError(f"[FEATURES] Няма данни за {ticker}")

    preprocessor = StockDataPreprocessor(price_data)
    preprocessor.calculate_technical_indicators()
    preprocessor.create_target_variable(days_ahead=days_ahead)

    price_cols, technical_cols = _split_price_technical(preprocessor.get_feature_columns())
    used_groups = {'price': price_cols, 'technical': technical_cols,
                   'market': [], 'fundamental': [], 'news': []}

    if 'market' in feature_groups:
        used_groups['market'] = _merge_market(preprocessor, period)
    if 'fundamental' in feature_groups:
        used_groups['fundamental'] = _merge_fundamentals(preprocessor, ticker)
    if 'news' in feature_groups:
        used_groups['news'] = _merge_news(preprocessor, ticker)

    # Редове без пълно покритие на активните нови групи се изхвърлят —
    # същият принцип като warmup редовете в calculate_technical_indicators():
    # по-добре по-малко данни, отколкото fabricated/NaN стойности през скалера.
    new_numeric_cols = used_groups['market'] + used_groups['fundamental']
    if new_numeric_cols:
        before = len(preprocessor.data)
        preprocessor.data = preprocessor.data.dropna(
            subset=[c for c in new_numeric_cols if c in preprocessor.data.columns]
        ).reset_index(drop=True)
        dropped = before - len(preprocessor.data)
        if dropped:
            print(f"[FEATURES] Изхвърлени {dropped} реда без пълно покритие "
                 f"на market/fundamental данните")

    return preprocessor, used_groups


def build_dataset(ticker, period=None, feature_groups=None, seq_length=None,
                  train_size=None, days_ahead=None):
    """
    Оркестрира целия feature pipeline: price+technical (винаги) -> по
    избор market/fundamental/news -> изчистване на непълни редове ->
    normalize -> sequences.

    Параметри:
    ----------
    ticker : str
    period : str, optional
        По подразбиране config.DEFAULT_PERIOD
    feature_groups : tuple[str], optional
        Подмножество от ALL_FEATURE_GROUPS. По подразбиране
        config.DEFAULT_FEATURE_GROUPS ('price','technical' — работи
        винаги, без мрежа/кеш за market/news/fundamental).
    seq_length, train_size, days_ahead : optional
        По подразбиране от config.py

    Връща:
    -------
    dict: X, y, prices, feature_names, feature_groups (реално използвани
    имена по група — за UI/feature-importance/ablation), preprocessor
    """
    seq_length = seq_length or cfg.SEQUENCE_LENGTH
    train_size = train_size if train_size is not None else cfg.TRAIN_SIZE
    feature_groups = tuple(feature_groups or cfg.DEFAULT_FEATURE_GROUPS)

    preprocessor, used_groups = build_raw_frame(
        ticker, period=period, feature_groups=feature_groups, days_ahead=days_ahead
    )

    preprocessor.normalize_data(train_size=train_size, seq_length=seq_length)
    X, y, prices = preprocessor.prepare_model_data(seq_length=seq_length, train_size=train_size)

    all_features = preprocessor.get_feature_columns()
    summary = ', '.join(f"{g}={len(cols)}" for g, cols in used_groups.items() if cols or g in feature_groups)
    print(f"[FEATURES] Общо {len(all_features)} features ({summary})")
    print(f"[FEATURES] Финален dataset: {len(X)} последователности")

    return {
        'X': X, 'y': y, 'prices': prices,
        'feature_names': all_features,
        'feature_groups': used_groups,
        'preprocessor': preprocessor,
    }


if __name__ == "__main__":
    print("[START] Тестване на Feature Pipeline Orchestrator\n")

    result = build_dataset('AAPL', period='6mo', feature_groups=('price', 'technical', 'market'))
    print(f"\nX shape: {result['X'].shape}")
    print(f"feature групи: {[(g, len(c)) for g, c in result['feature_groups'].items()]}")
