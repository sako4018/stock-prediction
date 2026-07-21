"""
Sector Correlation Analysis Module
==================================
Анализира корелацията между акции в един сектор.
Помага за разбиране на пазарните движения и диверсификация.

Функции:
- calculate_correlation(): Корелация между две акции
- sector_correlation_matrix(): Матрица на корелация в сектор
- get_sector_stocks(): Връща акциите в даден сектор
- find_uncorrelated_pairs(): Намира акции с ниска корелация (за диверсификация)
"""

import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, List, Tuple
from dataclasses import dataclass


# Секторни групи
SECTOR_STOCKS = {
    'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'CRM', 'ADBE', 'AMD', 'INTC', 'ORCL', 'NFLX', 'AVGO', 'QCOM'],
    'Finance': ['JPM', 'V', 'MA', 'BAC', 'GS', 'MS', 'AXP', 'PYPL', 'SQ'],
    'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'LLY', 'MRK', 'TMO', 'ABT'],
    'Consumer': ['WMT', 'PG', 'KO', 'PEP', 'COST', 'MCD', 'NKE', 'SBUX'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG'],
    'Industrial': ['CAT', 'BA', 'HON', 'UPS', 'GE'],
}


@dataclass
class CorrelationResult:
    ticker1: str
    ticker2: str
    correlation: float
    p_value: float
    period: str


def get_sector_stocks(sector: str) -> List[str]:
    """Връща акциите в даден сектор."""
    return SECTOR_STOCKS.get(sector, [])


def get_all_sectors() -> List[str]:
    """Връща всички налични сектори."""
    return list(SECTOR_STOCKS.keys())


def fetch_returns(tickers: List[str], period: str = '1y') -> pd.DataFrame:
    """
    Изтегля дневни returns за списък от акции.

    Връща:
    -------
    pd.DataFrame
        Дневни % промени за всяка акция
    """
    if not tickers:
        return pd.DataFrame()

    # Изтегляне на данни за всички акции
    data = yf.download(tickers, period=period, interval='1d', progress=False)

    if data.empty:
        return pd.DataFrame()

    # Взимаме Close цените
    if len(tickers) == 1:
        prices = data[['Close']].copy()
        prices.columns = tickers
    else:
        prices = data['Close'].copy()

    # Изчисляване на daily returns
    returns = prices.pct_change().dropna()

    return returns


def calculate_correlation(ticker1: str, ticker2: str, period: str = '1y') -> CorrelationResult:
    """
    Изчислява корелацията между две акции.

    Параметри:
    ----------
    ticker1, ticker2 : str
        Тикерите на двете акции
    period : str
        Период за данни

    Връща:
    -------
    CorrelationResult
        Корелация, p-value, период
    """
    returns = fetch_returns([ticker1, ticker2], period)

    if returns.empty or len(returns.columns) < 2:
        return CorrelationResult(ticker1, ticker2, 0.0, 1.0, period)

    corr = returns[ticker1].corr(returns[ticker2])

    # Pearson correlation p-value approximation
    n = len(returns)
    if n > 2 and abs(corr) < 1:
        t_stat = corr * np.sqrt((n - 2) / (1 - corr**2))
        p_value = 2 * (1 - abs(t_stat) / np.sqrt(n))  # Rough approximation
    else:
        p_value = 0.0

    return CorrelationResult(
        ticker1=ticker1,
        ticker2=ticker2,
        correlation=round(corr, 4),
        p_value=round(max(0, min(1, p_value)), 4),
        period=period
    )


def sector_correlation_matrix(sector: str, period: str = '1y') -> Dict:
    """
    Матрица на корелация за акции в един сектор.

    Връща:
    -------
    Dict
        correlation_matrix, average_correlation, most/least correlated pairs
    """
    tickers = get_sector_stocks(sector)
    if not tickers:
        return {'error': f'Sector "{sector}" not found'}

    returns = fetch_returns(tickers, period)

    if returns.empty:
        return {'error': 'Could not fetch data'}

    # Корелационна матрица
    corr_matrix = returns.corr()

    # Намиране на most/least correlated pairs
    pairs = []
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            t1, t2 = tickers[i], tickers[j]
            if t1 in corr_matrix.index and t2 in corr_matrix.columns:
                corr_val = corr_matrix.loc[t1, t2]
                pairs.append({
                    'ticker1': t1,
                    'ticker2': t2,
                    'correlation': round(corr_val, 4)
                })

    pairs.sort(key=lambda x: x['correlation'], reverse=True)

    avg_correlation = np.mean([p['correlation'] for p in pairs]) if pairs else 0

    return {
        'sector': sector,
        'tickers': tickers,
        'period': period,
        'average_correlation': round(avg_correlation, 4),
        'most_correlated': pairs[:3] if pairs else [],
        'least_correlated': pairs[-3:] if pairs else [],
        'diversification_score': round((1 - abs(avg_correlation)) * 100, 1),
        'data_points': len(returns),
        'matrix': corr_matrix.round(4).to_dict()
    }


def find_uncorrelated_pairs(sector: str = None, period: str = '1y', max_correlation: float = 0.3) -> List[Dict]:
    """
    Намира акции с ниска корелация (добри за диверсификация).

    Параметри:
    ----------
    sector : str, optional
        Ограничава търсенето до конкретен сектор
    period : str
        Период за данни
    max_correlation : float
        Максимална корелация за pairs (по подразбиране 0.3)

    Връща:
    -------
    List[Dict]
        Списък с pairs с ниска корелация
    """
    if sector:
        tickers = get_sector_stocks(sector)
    else:
        # Вземаме от всички сектори
        tickers = []
        for stocks in SECTOR_STOCKS.values():
            tickers.extend(stocks[:3])  # Top 3 от всеки сектор
        tickers = list(set(tickers))

    returns = fetch_returns(tickers, period)

    if returns.empty:
        return []

    corr_matrix = returns.corr()
    low_corr_pairs = []

    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            t1, t2 = tickers[i], tickers[j]
            if t1 in corr_matrix.index and t2 in corr_matrix.columns:
                corr_val = corr_matrix.loc[t1, t2]
                if abs(corr_val) <= max_correlation:
                    low_corr_pairs.append({
                        'ticker1': t1,
                        'ticker2': t2,
                        'correlation': round(corr_val, 4),
                        'diversification': 'excellent' if abs(corr_val) < 0.1 else 'good'
                    })

    low_corr_pairs.sort(key=lambda x: abs(x['correlation']))
    return low_corr_pairs[:10]


def get_sector_summary(period: str = '1y') -> List[Dict]:
    """
    Обобщение по всички сектори - средна корелация и диверсификация.
    """
    summaries = []
    for sector in SECTOR_STOCKS:
        returns = fetch_returns(SECTOR_STOCKS[sector][:5], period)
        if not returns.empty and len(returns.columns) > 1:
            corr_matrix = returns.corr()
            pairs = []
            for i in range(len(returns.columns)):
                for j in range(i + 1, len(returns.columns)):
                    pairs.append(corr_matrix.iloc[i, j])
            avg_corr = np.mean(pairs) if pairs else 0
        else:
            avg_corr = 0

        summaries.append({
            'sector': sector,
            'avg_correlation': round(avg_corr, 3),
            'diversification_score': round((1 - abs(avg_corr)) * 100, 1),
            'stock_count': len(SECTOR_STOCKS[sector])
        })

    return summaries
