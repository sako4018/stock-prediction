"""
Market Data Module
===================
Пазарни индекси (S&P 500, NASDAQ, VIX, Dow, 10-годишни treasury yields) —
контекст извън конкретната акция. Моделът не бива да гледа само цената на
една акция, а и какво прави пазарът като цяло same ден.

Data source: yfinance (същият, вече ползван от data_collection.py) —
без нов dependency, без API ключ. Проверено на живо, че ^GSPC/^IXIC/^VIX/
^DJI/^TNX работят директно.
"""

import os
import time
import pandas as pd
import numpy as np
import yfinance as yf

# Символ -> кратко име, ползвано в имената на features и кеш файловете
MARKET_INDICES = {
    '^GSPC': 'sp500',
    '^IXIC': 'nasdaq',
    '^VIX': 'vix',
    '^DJI': 'dow',
    '^TNX': 'treasury_10y',
}

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'market')


class MarketIndexCollector:
    """
    Сваля и кешира дневни цени на пазарни индекси.

    Параметри:
    ----------
    indices : list, optional
        Символи за сваляне (по подразбиране всички от MARKET_INDICES)
    period, interval : str
        Същите конвенции като StockDataCollector
    """

    def __init__(self, indices=None, period='2y', interval='1d'):
        self.indices = indices or list(MARKET_INDICES.keys())
        self.period = period
        self.interval = interval
        self.data = {}

    def fetch_all(self, save_to_csv=True, retries=2, delay=1.5):
        """
        Сваля всички индекси. Ако един индекс не успее, продължава с
        останалите — липсващ VIX не бива да съборя целия pipeline.
        """
        print(f"[MARKET] Изтегляне на {len(self.indices)} пазарни индекса...")
        self.data = {}

        for symbol in self.indices:
            name = MARKET_INDICES.get(symbol, symbol)
            df = None

            for attempt in range(retries + 1):
                try:
                    print(f"[MARKET] Изтегляне на {name} ({symbol})"
                          f"{f' (опит {attempt+1})' if attempt else ''}...")
                    raw = yf.Ticker(symbol).history(period=self.period, interval=self.interval)
                    if raw is not None and not raw.empty:
                        df = raw
                        break
                except Exception as e:
                    print(f"[MARKET][WARN] {symbol}: {e}")
                if attempt < retries:
                    time.sleep(delay)

            if df is None:
                print(f"[MARKET][WARN] Няма данни за {symbol} след {retries+1} опита, пропускам")
                continue

            df = df[['Close']].reset_index()
            df.columns = ['Date', 'Close']
            # normalize() маха часа — различните индекси (акции vs
            # облигации) имат леко различни intraday timestamp-и за
            # дневната си свещ, което иначе дублира "един и същи" ден
            # в две близки, но не еднакви UTC времена при merge-а по-долу.
            df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.normalize()
            self.data[symbol] = df

            if save_to_csv:
                os.makedirs(_DATA_DIR, exist_ok=True)
                df.to_csv(os.path.join(_DATA_DIR, f'{name}.csv'), index=False)

        print(f"[MARKET] Успешно свалени {len(self.data)}/{len(self.indices)} индекса")
        return self.data

    def load_cached(self):
        """Зарежда индекси от локалния CSV кеш, ако ги има."""
        loaded = {}
        for symbol, name in MARKET_INDICES.items():
            path = os.path.join(_DATA_DIR, f'{name}.csv')
            if os.path.exists(path):
                df = pd.read_csv(path)
                df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.normalize()
                loaded[symbol] = df
        self.data = loaded
        return loaded


def compute_market_features(index_data: dict) -> pd.DataFrame:
    """
    Изчислява market-level features от суровите индексни цени.

    Всяко изчисление ползва само минали/текущи стойности (pct_change,
    diff, rolling) — никакви center=True прозорци или бъдещи редове.
    Резултатът е "as-of" таблица: всеки ред е валиден от датата си
    нататък и трябва да се присъедини към цената на акцията с
    merge_asof(direction='backward'), не с обикновен merge по дата
    (различните борси понякога имат различни почивни дни).

    Връща:
    -------
    pandas.DataFrame
        Колона 'Date' + market features
    """
    frames = []

    sma20_sp500 = sma50_sp500 = None

    for symbol, df in index_data.items():
        name = MARKET_INDICES.get(symbol, symbol.strip('^').lower())
        d = df[['Date', 'Close']].copy().sort_values('Date').reset_index(drop=True)
        close = d['Close']
        out = pd.DataFrame({'Date': d['Date']})

        if name == 'vix':
            # VIX е ниво на волатилност само по себе си — гледаме нивото
            # и промяната му, не "разстояние от собствената му SMA".
            out['vix_close'] = close
            out['vix_change_1d'] = close.diff(1)
            out['vix_change_5d'] = close.diff(5)
        elif name == 'treasury_10y':
            # ^TNX от yfinance вече е в проценти (4.78 = 4.78%), не изисква мащабиране
            out['treasury_10y_yield'] = close
            out['treasury_10y_change_1d'] = close.diff(1)
        else:
            out[f'{name}_return_1d'] = close.pct_change(1) * 100
            out[f'{name}_return_5d'] = close.pct_change(5) * 100

            if name == 'sp500':
                # Пълният индикаторен набор (volatility, SMA distance,
                # общ market_trend) само на основния бенчмарк индекс —
                # не дублираме за всеки от петте индекса без причина.
                out['sp500_return_20d'] = close.pct_change(20) * 100
                out['sp500_volatility_20d'] = (
                    close.pct_change().rolling(20).std() * np.sqrt(252) * 100
                )
                sma20 = close.rolling(20).mean()
                sma50 = close.rolling(50).mean()
                out['sp500_dist_from_sma20'] = (close / sma20 - 1) * 100
                out['sp500_dist_from_sma50'] = (close / sma50 - 1) * 100
                # market_trend: +1 краткосрочната средна е над дългосрочната
                # (uptrend), -1 обратното. NaN (в началото, преди SMA50 да
                # има достатъчно история) остава NaN, не се познава на сляпо.
                out['market_trend'] = np.sign(sma20 - sma50)

        # Ако нормализирането на часа доведе до два реда със същата дата
        # (не би трябвало, но по-добре явно, отколкото случаен duplicate
        # ред при merge-а по-долу), пазим последната стойност за деня.
        out = out.drop_duplicates(subset='Date', keep='last')
        frames.append(out)

    if not frames:
        return pd.DataFrame(columns=['Date'])

    merged = frames[0]
    for f in frames[1:]:
        merged = merged.merge(f, on='Date', how='outer')
    merged = merged.sort_values('Date').reset_index(drop=True)

    # forward-fill само за запълване на редки дни, в които един индекс е
    # затворен, а друг — не (напр. облигационният пазар има различни
    # почивни дни от фондовия). Това НЕ гледа напред във времето — всеки
    # запълнен ред взима стойност от предходен, вече отминал ден.
    merged = merged.ffill()

    return merged


if __name__ == "__main__":
    print("[START] Тестване на Market Data Module\n")

    collector = MarketIndexCollector(period='6mo')
    data = collector.fetch_all()

    if data:
        features = compute_market_features(data)
        print("\n[INFO] Последни редове с market features:")
        print(features.tail())
