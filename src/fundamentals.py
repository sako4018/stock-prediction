"""
Fundamental Data Integration Module
====================================
Интегрира фундаментални данни за компании от Yahoo Finance.

Данни:
- PE Ratio, PEG Ratio, Price-to-Book
- EPS, Revenue, Net Income
- Dividend Yield, Payout Ratio
- Debt/Equity, Current Ratio
- Market Cap, Enterprise Value
- Profit Margin, ROE, ROA
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional


def get_fundamentals(ticker: str) -> Dict:
    """
    Получава фундаментални данни за компания.

    Връща:
    -------
    Dict
        Фундаментални метрики
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info:
            return {'error': f'No data for {ticker}'}

        # Valuation
        valuation = {
            'pe_ratio': info.get('trailingPE') or info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
            'ev_to_ebitda': info.get('enterpriseToEbitda'),
        }

        # Profitability
        profitability = {
            'profit_margin': _pct(info.get('profitMargins')),
            'gross_margin': _pct(info.get('grossMargins')),
            'operating_margin': _pct(info.get('operatingMargins')),
            'roe': _pct(info.get('returnOnEquity')),
            'roa': _pct(info.get('returnOnAssets')),
            'revenue_growth': _pct(info.get('revenueGrowth')),
            'earnings_growth': _pct(info.get('earningsGrowth')),
        }

        # Financial Health
        health = {
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'quick_ratio': info.get('quickRatio'),
            'free_cash_flow': info.get('freeCashflow'),
            'total_cash': info.get('totalCash'),
            'total_debt': info.get('totalDebt'),
        }

        # Per Share
        per_share = {
            'eps_trailing': info.get('trailingEps'),
            'eps_forward': info.get('forwardEps'),
            'book_value': info.get('bookValue'),
            'dividend_per_share': info.get('dividendRate'),
        }

        # Size & Market
        size = {
            'market_cap': info.get('marketCap'),
            'enterprise_value': info.get('enterpriseValue'),
            'shares_outstanding': info.get('sharesOutstanding'),
            'float_shares': info.get('floatShares'),
        }

        # Dividends
        dividends = {
            'dividend_yield': _pct(info.get('dividendYield')),
            'payout_ratio': _pct(info.get('payoutRatio')),
            'ex_dividend_date': str(info.get('exDividendDate', '')),
        }

        # Analyst
        analysts = {
            'target_mean_price': info.get('targetMeanPrice'),
            'target_high_price': info.get('targetHighPrice'),
            'target_low_price': info.get('targetLowPrice'),
            'recommendation': info.get('recommendationKey'),
            'number_of_analysts': info.get('numberOfAnalystOpinions'),
        }

        # Fundamentals Score (0-100)
        score = _calculate_fundamentals_score(valuation, profitability, health)

        return {
            'ticker': ticker.upper(),
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'valuation': _clean_dict(valuation),
            'profitability': _clean_dict(profitability),
            'financial_health': _clean_dict(health),
            'per_share': _clean_dict(per_share),
            'size': _clean_dict(size),
            'dividends': _clean_dict(dividends),
            'analysts': _clean_dict(analysts),
            'fundamentals_score': score,
            'summary': _generate_summary(valuation, profitability, health, score)
        }

    except Exception as e:
        return {'ticker': ticker, 'error': str(e)}


def get_valuation_comparison(tickers: list) -> Dict:
    """
    Сравнение на valuation между компании.
    """
    results = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            results[ticker] = {
                'pe_ratio': info.get('trailingPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'ev_to_ebitda': info.get('enterpriseToEbitda'),
                'profit_margin': _pct(info.get('profitMargins')),
                'roe': _pct(info.get('returnOnEquity')),
                'revenue_growth': _pct(info.get('revenueGrowth')),
            }
        except Exception:
            results[ticker] = {'error': 'Could not fetch'}

    return results


# ============================================================
# Point-in-time (as-of) fundamentals — за ТРЕНИРОВЪЧНИЯ pipeline
# ============================================================
#
# get_fundamentals() по-горе връща yfinance-ия ЖИВ snapshot — правилно за
# UI, но НЕВАЛИДНО за тренировъчни features: прилагането на "днешния" P/E
# към данни отпреди 2 години би било изтичане на бъдеща информация назад
# във времето.
#
# Тук вместо това строим "timeline" от реално публикувани отчети, всеки
# с истински timestamp на публикуване (available_at), взет от
# Ticker.earnings_dates — единственото поле в yfinance с точен час, не
# само дата. Revenue/Net Income идват от Ticker.quarterly_financials
# (индексирани по КРАЯ на периода, не по датата на публикуване), затова
# се присъединяват към следващия earnings_dates отчет СЛЕД края на
# периода — именно тогава числата реално стават публични.
#
# Analyst targets/recommendations/debt-to-equity/margins в get_fundamentals()
# НЯМАТ history endpoint в yfinance (само .info, само "сега") — затова
# НЕ участват в тази timeline и не бива да влизат в тренировъчни features
# за минали дати. Остават само за живия UI panel.

FUNDAMENTAL_TIMELINE_COLUMNS = [
    'available_at', 'eps_estimate', 'eps_actual', 'surprise_pct',
    'revenue', 'net_income', 'trailing_eps_ttm', 'pe_ratio_at_report',
]


def get_fundamentals_timeline(ticker: str, price_history: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Point-in-time история на fundamentals — един ред на всеки реален
    earnings отчет, с точния timestamp, на който е станал публичен.

    Параметри:
    ----------
    ticker : str
    price_history : pandas.DataFrame, optional
        Колони 'Date' (datetime) и 'Close'. Ползва се само за да се
        изчисли pe_ratio_at_report (историческата цена в деня на отчета
        / trailing 12-месечен EPS). Без него тази колона остава NaN —
        по-добре липсваща стойност, отколкото измислена.

    Връща:
    -------
    pandas.DataFrame
        Колони: available_at, eps_estimate, eps_actual, surprise_pct,
        revenue, net_income, trailing_eps_ttm, pe_ratio_at_report.
        Сортирано хронологично. Празен DataFrame (същите колони), ако
        yfinance не върне earnings история за тикера.
    """
    try:
        stock = yf.Ticker(ticker)
        earnings = stock.earnings_dates
    except Exception as e:
        print(f"[FUNDAMENTALS][WARN] Няма earnings_dates за {ticker}: {e}")
        earnings = None

    if earnings is None or earnings.empty:
        return pd.DataFrame(columns=FUNDAMENTAL_TIMELINE_COLUMNS)

    earnings = earnings.copy()
    earnings.index = pd.to_datetime(earnings.index, utc=True)
    earnings = earnings.sort_index()

    # Само реално отчетени тримесечия (бъдещи estimate-only редове имат
    # Reported EPS = NaN — не са "публикувана информация" за backfill)
    reported = earnings[earnings['Reported EPS'].notna()].copy()
    if reported.empty:
        return pd.DataFrame(columns=FUNDAMENTAL_TIMELINE_COLUMNS)

    # Trailing 12-месечен EPS: сума на последните 4 отчетени тримесечия,
    # хронологично, само с минали стойности (rolling, не central window)
    reported['trailing_eps_ttm'] = reported['Reported EPS'].rolling(4, min_periods=4).sum()

    try:
        qf = stock.quarterly_financials
    except Exception:
        qf = None

    revenue_map = {}
    net_income_map = {}
    if qf is not None and not qf.empty:
        # normalized period-end timestamp -> оригиналната колона в qf
        col_by_period = {
            (pd.Timestamp(c, tz='UTC') if pd.Timestamp(c).tzinfo is None else pd.Timestamp(c)): c
            for c in qf.columns
        }
        period_ends = sorted(col_by_period.keys())

        for report_date in reported.index:
            # Кой период приключи последен ПРЕДИ/НА датата на отчета?
            candidates = [p for p in period_ends if p <= report_date]
            if not candidates:
                continue
            col = col_by_period[max(candidates)]
            if 'Total Revenue' in qf.index:
                revenue_map[report_date] = qf.loc['Total Revenue', col]
            if 'Net Income' in qf.index:
                net_income_map[report_date] = qf.loc['Net Income', col]

    rows = []
    for report_date, row in reported.iterrows():
        rows.append({
            'available_at': report_date,
            'eps_estimate': row.get('EPS Estimate'),
            'eps_actual': row.get('Reported EPS'),
            'surprise_pct': row.get('Surprise(%)'),
            'revenue': revenue_map.get(report_date),
            'net_income': net_income_map.get(report_date),
            'trailing_eps_ttm': row.get('trailing_eps_ttm'),
        })

    timeline = pd.DataFrame(rows).sort_values('available_at').reset_index(drop=True)

    # Point-in-time P/E: историческата цена В ДЕНЯ на отчета, делена на
    # trailing EPS към този момент — истински "какъв е бил P/E-то тогава",
    # не днешния P/E приложен назад във времето.
    timeline['pe_ratio_at_report'] = np.nan
    if price_history is not None and not price_history.empty:
        ph = price_history[['Date', 'Close']].copy()
        # datetime64[ns, UTC] навсякъде — merge_asof отказва ключове с
        # различна прецизност (s/us/ns), а различните pandas пътища тук
        # могат да върнат различна.
        ph['Date'] = pd.to_datetime(ph['Date'], utc=True).astype('datetime64[ns, UTC]')
        ph = ph.sort_values('Date')

        avail_col = timeline[['available_at']].copy()
        avail_col['available_at'] = pd.to_datetime(
            avail_col['available_at'], utc=True
        ).astype('datetime64[ns, UTC]')

        priced = pd.merge_asof(
            avail_col.sort_values('available_at'),
            ph.rename(columns={'Date': 'available_at'}),
            on='available_at', direction='backward'
        )
        eps = timeline['trailing_eps_ttm'].values
        close = priced['Close'].values
        with np.errstate(divide='ignore', invalid='ignore'):
            pe = np.where(eps > 0, close / eps, np.nan)
        timeline['pe_ratio_at_report'] = pe

    return timeline[FUNDAMENTAL_TIMELINE_COLUMNS]


def merge_fundamentals_asof(price_df: pd.DataFrame, timeline_df: pd.DataFrame,
                             date_col: str = 'Date') -> pd.DataFrame:
    """
    Присъединява point-in-time fundamentals към ценовата времева ос.

    За всеки ред в price_df взима последния fundamentals ред с
    available_at <= Date — стойността остава "в сила" до следващия
    отчет, точно както потребителят я вижда в реалния свят. Ред без
    нито един минал отчет получава NaN (не 0 — липсваща информация,
    не "нулева").

    Параметри:
    ----------
    price_df : pandas.DataFrame
        Трябва да съдържа date_col (datetime), сортирана хронологично
        не е задължителна — сортира се вътрешно.
    timeline_df : pandas.DataFrame
        Изход от get_fundamentals_timeline().

    Връща:
    -------
    pandas.DataFrame
        price_df + fundamentals колоните (без available_at), подравнени.
    """
    left = price_df.copy()
    left[date_col] = pd.to_datetime(left[date_col], utc=True).astype('datetime64[ns, UTC]')
    left = left.sort_values(date_col).reset_index(drop=True)

    if timeline_df is None or timeline_df.empty:
        for col in FUNDAMENTAL_TIMELINE_COLUMNS:
            if col != 'available_at':
                left[col] = np.nan
        return left

    right = timeline_df.copy().sort_values('available_at')
    right['available_at'] = pd.to_datetime(right['available_at'], utc=True).astype('datetime64[ns, UTC]')

    merged = pd.merge_asof(
        left, right.rename(columns={'available_at': date_col}),
        on=date_col, direction='backward'
    )
    return merged


def _pct(value) -> Optional[float]:
    """Конвертира decimal в percentage."""
    if value is not None:
        return round(value * 100, 2)
    return None


def _clean_dict(d: Dict) -> Dict:
    """Премахва None стойности и round-ва floats."""
    return {k: round(v, 2) if isinstance(v, float) else v
            for k, v in d.items() if v is not None}


def _calculate_fundamentals_score(valuation, profitability, health) -> Dict:
    """
    Изчислява fundamentals score (0-100) базиран на метрики.
    """
    score = 50  # базов score
    factors = []

    # PE ratio оценка
    pe = valuation.get('pe_ratio')
    if pe is not None:
        if pe < 15: score += 10; factors.append('Low PE (+10)')
        elif pe < 25: score += 5; factors.append('Fair PE (+5)')
        elif pe > 40: score -= 10; factors.append('High PE (-10)')

    # Profit margin
    pm = profitability.get('profit_margin')
    if pm is not None:
        if pm > 20: score += 10; factors.append('High margin (+10)')
        elif pm > 10: score += 5; factors.append('Good margin (+5)')
        elif pm < 0: score -= 15; factors.append('Negative margin (-15)')

    # ROE
    roe = profitability.get('roe')
    if roe is not None:
        if roe > 20: score += 10; factors.append('High ROE (+10)')
        elif roe > 10: score += 5; factors.append('Good ROE (+5)')
        elif roe < 0: score -= 10; factors.append('Negative ROE (-10)')

    # Debt/Equity
    de = health.get('debt_to_equity')
    if de is not None:
        if de < 50: score += 5; factors.append('Low debt (+5)')
        elif de > 200: score -= 10; factors.append('High debt (-10)')

    # Revenue growth
    rg = profitability.get('revenue_growth')
    if rg is not None:
        if rg > 15: score += 10; factors.append('High growth (+10)')
        elif rg > 5: score += 5; factors.append('Moderate growth (+5)')
        elif rg < -5: score -= 10; factors.append('Declining revenue (-10)')

    score = max(0, min(100, score))

    return {
        'score': score,
        'rating': 'Strong Buy' if score >= 75 else 'Buy' if score >= 60 else 'Hold' if score >= 40 else 'Sell' if score >= 25 else 'Strong Sell',
        'factors': factors
    }


def _generate_summary(valuation, profitability, health, score) -> str:
    """Генерира текстово обобщение."""
    rating = score.get('rating', 'N/A')
    pe = valuation.get('pe_ratio')
    margin = profitability.get('profit_margin')
    roe = profitability.get('roe')

    parts = [f"Overall rating: {rating} (score: {score['score']}/100)"]

    if pe:
        parts.append(f"P/E {pe:.1f}")
    if margin:
        parts.append(f"Margin {margin:.1f}%")
    if roe:
        parts.append(f"ROE {roe:.1f}%")

    return ' | '.join(parts)
