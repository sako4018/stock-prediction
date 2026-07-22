"""
Data Collection Module
======================
Този модул свалят real-time данни за акции от Yahoo Finance.

Функции:
- fetch_stock_data(): Изтегля исторически данни
- get_real_time_price(): Взима текуща цена
- update_data(): Обновява данните автоматично
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

class StockDataCollector:
    """
    Клас за събиране на данни за акции.

    Параметри:
    ----------
    ticker : str
        Символ на акцията (напр. 'AAPL', 'TSLA', 'GOOGL')
    period : str
        Период на данните ('1mo', '3mo', '6mo', '1y', '2y', '5y')
    interval : str
        Интервал на данните ('1m', '5m', '15m', '1h', '1d')
    """

    def __init__(self, ticker='AAPL', period='1y', interval='1d'):
        self.ticker = ticker.upper()
        self.period = period
        self.interval = interval
        self.data = None
        self.stock = yf.Ticker(self.ticker)

    def fetch_stock_data(self, save_to_csv=True):
        """
        Изтегля исторически данни за акцията.

        Връща:
        -------
        pandas.DataFrame
            DataFrame с колони: Open, High, Low, Close, Volume
        """
        try:
            print(f"📊 Изтегляне на данни за {self.ticker}...")

            # Опитваме с първоначалния interval
            self.data = self.stock.history(period=self.period, interval=self.interval)

            # Ако няма данни, опитваме с '1d' interval
            if self.data is None or self.data.empty:
                print(f"⚠️ Няма данни с interval={self.interval}, опитваме с 1d...")
                self.data = self.stock.history(period=self.period, interval='1d')

            # Ако пак няма данни, опитваме с по-дълъг период
            if self.data is None or self.data.empty:
                fallback_periods = {'1mo': '3mo', '3mo': '6mo', '6mo': '1y'}
                fallback = fallback_periods.get(self.period)
                if fallback:
                    print(f"⚠️ Опитваме с period={fallback}...")
                    self.data = self.stock.history(period=fallback, interval='1d')

            if self.data is None or self.data.empty:
                print(f"❌ Няма данни за {self.ticker}")
                return None

            # Почистване на данните
            self.data = self.data[['Open', 'High', 'Low', 'Close', 'Volume']]
            self.data.reset_index(inplace=True)

            print(f"✅ Свалени {len(self.data)} реда данни")
            print(f"📅 От {self.data['Date'].min()} до {self.data['Date'].max()}")

            # Запазване в CSV файл
            if save_to_csv:
                data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
                os.makedirs(data_dir, exist_ok=True)

                filename = f"{self.ticker}_{self.period}_{self.interval}.csv"
                filepath = os.path.join(data_dir, filename)

                self.data.to_csv(filepath, index=False)
                print(f"💾 Данните са запазени в: {filepath}")

            return self.data

        except Exception as e:
            print(f"❌ Грешка при изтегляне на данни: {e}")
            return None

    def get_real_time_price(self):
        """
        Взима текущата цена на акцията в реално време.

        Връща:
        -------
        dict
            Речник с информация за текущата цена
        """
        try:
            # Взимане на real-time информация
            info = self.stock.info

            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            previous_close = info.get('previousClose', 0)

            # Изчисляване на промяната
            if previous_close > 0:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
            else:
                change = 0
                change_percent = 0

            result = {
                'ticker': self.ticker,
                'current_price': current_price,
                'previous_close': previous_close,
                'change': change,
                'change_percent': change_percent,
                'timestamp': datetime.now(),
                'currency': info.get('currency', 'USD')
            }

            return result

        except Exception as e:
            print(f"❌ Грешка при взимане на real-time цена: {e}")
            return None

    def get_company_info(self):
        """
        Взима информация за компанията.

        Връща:
        -------
        dict
            Информация за компанията (име, сектор, описание и др.)
        """
        try:
            info = self.stock.info

            company_info = {
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'country': info.get('country', 'N/A'),
                'website': info.get('website', 'N/A'),
                'description': info.get('longBusinessSummary', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'employees': info.get('fullTimeEmployees', 0)
            }

            return company_info

        except Exception as e:
            print(f"❌ Грешка при взимане на информация: {e}")
            return None

    def load_saved_data(self, filename=None):
        """
        Зарежда запазени данни от CSV файл.

        Параметри:
        ----------
        filename : str, optional
            Име на файла. Ако не е зададено, използва стандартното име.

        Връща:
        -------
        pandas.DataFrame
            Заредените данни
        """
        try:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')

            if filename is None:
                filename = f"{self.ticker}_{self.period}_{self.interval}.csv"

            filepath = os.path.join(data_dir, filename)

            if not os.path.exists(filepath):
                print(f"❌ Файлът {filepath} не съществува")
                return None

            self.data = pd.read_csv(filepath, parse_dates=['Date'])
            print(f"✅ Заредени {len(self.data)} реда от {filepath}")

            return self.data

        except Exception as e:
            print(f"❌ Грешка при зареждане на данни: {e}")
            return None


# Тестване на модула
if __name__ == "__main__":
    print("🚀 Тестване на Data Collection Module\n")

    # Създаване на collector за Apple акции
    collector = StockDataCollector(ticker='AAPL', period='6mo', interval='1d')

    # Изтегляне на исторически данни
    data = collector.fetch_stock_data()

    if data is not None:
        print("\n📊 Първите 5 реда:")
        print(data.head())

        print("\n📊 Последните 5 реда:")
        print(data.tail())

    # Взимане на real-time цена
    print("\n💹 Real-time информация:")
    price_info = collector.get_real_time_price()

    if price_info:
        print(f"Акция: {price_info['ticker']}")
        print(f"Текуща цена: ${price_info['current_price']:.2f}")
        print(f"Промяна: {price_info['change']:+.2f} ({price_info['change_percent']:+.2f}%)")

    # Информация за компанията
    print("\n🏢 Информация за компанията:")
    company = collector.get_company_info()

    if company:
        print(f"Име: {company['name']}")
        print(f"Сектор: {company['sector']}")
        print(f"Индустрия: {company['industry']}")
