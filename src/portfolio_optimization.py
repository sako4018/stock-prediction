"""
Portfolio Optimization Module
==============================
Modern Portfolio Theory (MPT) - Markowitz Model

Функции:
- calculate_efficient_frontier(): Изчислява efficient frontier
- optimize_portfolio(): Намира оптималното портфолио
- optimize_for_risk(): Оптимизира за конкретен risk level
- get_diversification_metrics(): Метрики за диверсификация
"""

import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, List, Tuple
from scipy.optimize import minimize


def fetch_price_data(tickers: List[str], period: str = '2y') -> pd.DataFrame:
    """Изтегля adjusted close цените за списък от акции."""
    data = yf.download(tickers, period=period, interval='1d', progress=False)['Close']
    if isinstance(data, pd.Series):
        data = data.to_frame()
    return data.dropna()


def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Изчислява daily returns."""
    return prices.pct_change().dropna()


def portfolio_stats(weights: np.ndarray, mean_returns: np.ndarray,
                    cov_matrix: np.ndarray, risk_free_rate: float = 0.02) -> Tuple:
    """Изчислява return, volatility, Sharpe ratio за портфолио."""
    port_return = np.sum(mean_returns * weights) * 252
    port_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
    sharpe_ratio = (port_return - risk_free_rate) / port_volatility if port_volatility > 0 else 0
    return port_return, port_volatility, sharpe_ratio


def optimize_portfolio(prices: pd.DataFrame, risk_free_rate: float = 0.02,
                       target_return: float = None) -> Dict:
    """
    Намира оптималното портфолио по Maximum Sharpe Ratio.

    Връща:
    -------
    Dict
        weights, return, volatility, sharpe_ratio
    """
    returns = calculate_returns(prices)
    mean_returns = returns.mean().values
    cov_matrix = returns.cov().values
    n = len(prices.columns)
    tickers = list(prices.columns)

    # Ограничения
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    if target_return is not None:
        constraints.append({
            'type': 'eq',
            'fun': lambda w: np.sum(mean_returns * w) * 252 - target_return
        })

    bounds = tuple((0, 1) for _ in range(n))
    initial = np.array([1.0 / n] * n)

    # Negative Sharpe (minimize)
    def neg_sharpe(w):
        _, _, sharpe = portfolio_stats(w, mean_returns, cov_matrix, risk_free_rate)
        return -sharpe

    result = minimize(neg_sharpe, initial, method='SLSQP', bounds=bounds, constraints=constraints)

    if result.success:
        weights = result.x
        port_return, port_volatility, sharpe_ratio = portfolio_stats(
            weights, mean_returns, cov_matrix, risk_free_rate
        )

        allocation = {tickers[i]: round(float(weights[i]), 4) for i in range(n) if weights[i] > 0.01}

        return {
            'allocation': allocation,
            'expected_return': round(float(port_return) * 100, 2),
            'expected_volatility': round(float(port_volatility) * 100, 2),
            'sharpe_ratio': round(float(sharpe_ratio), 3),
            'risk_free_rate': risk_free_rate * 100,
            'num_positions': len(allocation)
        }

    return {'error': 'Optimization failed'}


def optimize_min_volatility(prices: pd.DataFrame) -> Dict:
    """Намира портфолиото с минимална волатилност."""
    returns = calculate_returns(prices)
    mean_returns = returns.mean().values
    cov_matrix = returns.cov().values
    n = len(prices.columns)
    tickers = list(prices.columns)

    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = tuple((0, 1) for _ in range(n))
    initial = np.array([1.0 / n] * n)

    def volatility(w):
        return np.sqrt(np.dot(w.T, np.dot(cov_matrix * 252, w)))

    result = minimize(volatility, initial, method='SLSQP', bounds=bounds, constraints=constraints)

    if result.success:
        weights = result.x
        port_return, port_volatility, sharpe_ratio = portfolio_stats(
            weights, mean_returns, cov_matrix
        )
        allocation = {tickers[i]: round(float(weights[i]), 4) for i in range(n) if weights[i] > 0.01}

        return {
            'strategy': 'Minimum Volatility',
            'allocation': allocation,
            'expected_return': round(float(port_return) * 100, 2),
            'expected_volatility': round(float(port_volatility) * 100, 2),
            'sharpe_ratio': round(float(sharpe_ratio), 3),
            'num_positions': len(allocation)
        }

    return {'error': 'Optimization failed'}


def calculate_efficient_frontier(prices: pd.DataFrame, n_points: int = 20) -> List[Dict]:
    """
    Изчислява efficient frontier.

    Връща:
    -------
    List[Dict]
        Точки от efficient frontier
    """
    returns = calculate_returns(prices)
    mean_returns = returns.mean().values
    cov_matrix = returns.cov().values
    n = len(prices.columns)
    tickers = list(prices.columns)

    # Минимална и максимална възвръщаемост
    min_ret = mean_returns.min() * 252
    max_ret = mean_returns.max() * 252

    target_returns = np.linspace(min_ret * 0.5, max_ret * 1.2, n_points)
    frontier = []

    for target in target_returns:
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
            {'type': 'eq', 'fun': lambda w, t=target: np.sum(mean_returns * w) * 252 - t}
        ]
        bounds = tuple((0, 1) for _ in range(n))
        initial = np.array([1.0 / n] * n)

        def volatility(w):
            return np.sqrt(np.dot(w.T, np.dot(cov_matrix * 252, w)))

        result = minimize(volatility, initial, method='SLSQP', bounds=bounds, constraints=constraints)

        if result.success:
            port_return, port_volatility, sharpe = portfolio_stats(
                result.x, mean_returns, cov_matrix
            )
            frontier.append({
                'return': round(float(port_return) * 100, 2),
                'volatility': round(float(port_volatility) * 100, 2),
                'sharpe': round(float(sharpe), 3)
            })

    return sorted(frontier, key=lambda x: x['volatility'])


def get_diversification_metrics(tickers: List[str], weights: Dict[str, float] = None,
                                 period: str = '2y') -> Dict:
    """
    Метрики за диверсификация на портфолио.
    """
    prices = fetch_price_data(tickers, period)
    returns = calculate_returns(prices)

    if weights is None:
        weights = {t: 1.0 / len(tickers) for t in tickers}

    # Correlation matrix
    corr = returns.corr()

    # Average correlation
    pairs = []
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            if tickers[i] in corr.index and tickers[j] in corr.columns:
                pairs.append(corr.loc[tickers[i], tickers[j]])

    avg_corr = np.mean(pairs) if pairs else 0

    # Portfolio variance
    w = np.array([weights.get(t, 0) for t in tickers])
    cov = returns.cov().values
    port_var = np.dot(w.T, np.dot(cov * 252, w))

    # Individual variances
    individual_vars = [returns[t].var() * 252 for t in tickers if t in returns.columns]
    weighted_var = sum(weights.get(t, 0) ** 2 * returns[t].var() * 252
                       for t in tickers if t in returns.columns)

    # Diversification ratio
    div_ratio = port_var / weighted_var if weighted_var > 0 else 1

    return {
        'num_assets': len(tickers),
        'average_correlation': round(float(avg_corr), 3),
        'diversification_ratio': round(float(div_ratio), 3),
        'diversification_benefit': round((1 - float(div_ratio)) * 100, 1),
        'correlation_matrix': corr.round(3).to_dict(),
        'assessment': 'Well diversified' if avg_corr < 0.3 else 'Moderately correlated' if avg_corr < 0.6 else 'Highly correlated'
    }
