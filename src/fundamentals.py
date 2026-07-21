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
