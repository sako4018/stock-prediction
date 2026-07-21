"""
Portfolio Tracker Module
========================
Проследяване на портфолио от акции.

Функции:
- add_position(): Добавя позиция
- remove_position(): Премахва позиция
- get_portfolio_value(): Изчислява стойността
- get_portfolio_summary(): Обобщение
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import yfinance as yf


class PortfolioTracker:
    """
    Проследяване на портфолио от акции.

    Параметри:
    ----------
    initial_capital : float
        Начален капитал (по подразбиране $100,000)
    """

    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, dict] = {}
        self.history: List[dict] = []
        self.data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'portfolio.json')
        self.load_portfolio()

    def load_portfolio(self):
        """Зарежда портфолиото от файл."""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.cash = data.get('cash', self.initial_capital)
                self.positions = data.get('positions', {})
                self.history = data.get('history', [])
            print(f"📂 Портфолио заредено: {len(self.positions)} позиции")

    def save_portfolio(self):
        """Записва портфолиото в файл."""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        data = {
            'cash': self.cash,
            'positions': self.positions,
            'history': self.history,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_position(self, ticker: str, shares: float, price: float) -> dict:
        """
        Добавя позиция в портфолиото.

        Параметри:
        ----------
        ticker : str
            Тикер на акцията
        shares : float
            Брой акции
        price : float
            Цена на акция

        Връща:
        -------
        dict
            Информация за позицията
        """
        ticker = ticker.upper()
        cost = shares * price

        if cost > self.cash:
            return {'error': f'Недостатъчно пари. Нужни: ${cost:.2f}, Налични: ${self.cash:.2f}'}

        # Ако вече имаме позиция, добавяме
        if ticker in self.positions:
            old = self.positions[ticker]
            total_shares = old['shares'] + shares
            avg_price = (old['shares'] * old['avg_price'] + cost) / total_shares
            self.positions[ticker] = {
                'shares': total_shares,
                'avg_price': avg_price,
                'added_date': old['added_date']
            }
        else:
            self.positions[ticker] = {
                'shares': shares,
                'avg_price': price,
                'added_date': datetime.now().isoformat()
            }

        self.cash -= cost

        # Добавяне в историята
        self.history.append({
            'action': 'BUY',
            'ticker': ticker,
            'shares': shares,
            'price': price,
            'total': cost,
            'timestamp': datetime.now().isoformat()
        })

        self.save_portfolio()

        return {
            'action': 'BUY',
            'ticker': ticker,
            'shares': shares,
            'price': price,
            'total': cost,
            'remaining_cash': self.cash
        }

    def remove_position(self, ticker: str, shares: Optional[float] = None, price: float = 0) -> dict:
        """
        Премахва позиция (или част от нея).

        Параметри:
        ----------
        ticker : str
            Тикер на акцията
        shares : float, optional
            Брой акции за продаване (None = всички)
        price : float
            Цена на продажба
        """
        ticker = ticker.upper()

        if ticker not in self.positions:
            return {'error': f'Няма позиция за {ticker}'}

        pos = self.positions[ticker]

        if shares is None:
            shares = pos['shares']

        if shares > pos['shares']:
            return {'error': f'Няма достатъчно акции. Имаш: {pos["shares"]}'}

        revenue = shares * price
        profit = (price - pos['avg_price']) * shares

        # Обновяване на позицията
        pos['shares'] -= shares
        if pos['shares'] <= 0:
            del self.positions[ticker]
        else:
            self.positions[ticker] = pos

        self.cash += revenue

        # Добавяне в историята
        self.history.append({
            'action': 'SELL',
            'ticker': ticker,
            'shares': shares,
            'price': price,
            'total': revenue,
            'profit': profit,
            'timestamp': datetime.now().isoformat()
        })

        self.save_portfolio()

        return {
            'action': 'SELL',
            'ticker': ticker,
            'shares': shares,
            'price': price,
            'revenue': revenue,
            'profit': profit,
            'remaining_cash': self.cash
        }

    def get_current_prices(self) -> Dict[str, float]:
        """Взима текущите цени на всички акции в портфолиото."""
        prices = {}
        for ticker in self.positions:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                prices[ticker] = info.get('currentPrice', info.get('regularMarketPrice', 0))
            except:
                prices[ticker] = 0
        return prices

    def get_portfolio_summary(self) -> dict:
        """
        Връща обобщение на портфолиото.
        """
        current_prices = self.get_current_prices()

        total_invested = 0
        total_current_value = 0
        positions_summary = []

        for ticker, pos in self.positions.items():
            current_price = current_prices.get(ticker, pos['avg_price'])
            invested = pos['shares'] * pos['avg_price']
            current_value = pos['shares'] * current_price
            profit_loss = current_value - invested
            profit_pct = (profit_loss / invested * 100) if invested > 0 else 0

            total_invested += invested
            total_current_value += current_value

            positions_summary.append({
                'ticker': ticker,
                'shares': pos['shares'],
                'avg_price': pos['avg_price'],
                'current_price': current_price,
                'invested': invested,
                'current_value': current_value,
                'profit_loss': profit_loss,
                'profit_pct': profit_pct
            })

        total_value = self.cash + total_current_value
        total_return = ((total_value - self.initial_capital) / self.initial_capital) * 100

        return {
            'initial_capital': self.initial_capital,
            'current_cash': self.cash,
            'total_invested': total_invested,
            'total_positions_value': total_current_value,
            'total_portfolio_value': total_value,
            'total_return': total_return,
            'num_positions': len(self.positions),
            'positions': positions_summary
        }

    def get_history(self, limit: int = 50) -> List[dict]:
        """Връща историята на транзакциите."""
        return self.history[-limit:]
