"""
Preprocessing Module
====================
Този модул обработва суровите данни и създава технически индикатори.

Функции:
- calculate_technical_indicators(): Изчислява Moving Averages, RSI, MACD и др.
- prepare_data_for_model(): Подготвя данните за ML модела
- normalize_data(): Нормализира данните за по-добро обучение
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

class StockDataPreprocessor:
    """
    Клас за обработка на данни за акции и създаване на features.

    Параметри:
    ----------
    data : pandas.DataFrame
        Сурови данни за акции с колони: Date, Open, High, Low, Close, Volume
    """

    def __init__(self, data):
        self.data = data.copy()
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.scaled_data = None

    def calculate_technical_indicators(self):
        """
        Изчислява технически индикатори за техническа анализа.

        Създава:
        - SMA (Simple Moving Average) - 20, 50 дни
        - EMA (Exponential Moving Average) - 12, 26 дни
        - RSI (Relative Strength Index)
        - MACD (Moving Average Convergence Divergence)
        - Bollinger Bands
        - Volume Change
        - ATR (Average True Range)
        - Stochastic Oscillator
        - Williams %R
        """
        print("📈 Изчисляване на технически индикатори...")

        df = self.data.copy()
        n = len(df)

        # Adaptive windows based on available data
        sma20_w = min(20, max(5, n // 3))
        sma50_w = min(50, max(10, n // 2))

        # 1. Simple Moving Averages (SMA)
        df['SMA_20'] = df['Close'].rolling(window=sma20_w).mean()
        df['SMA_50'] = df['Close'].rolling(window=sma50_w).mean()

        # 2. Exponential Moving Averages (EMA)
        ema12_w = min(12, max(3, n // 4))
        ema26_w = min(26, max(5, n // 2))
        df['EMA_12'] = df['Close'].ewm(span=ema12_w, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=ema26_w, adjust=False).mean()

        # 3. RSI
        rsi_w = min(14, max(3, n // 4))
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_w).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_w).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 4. MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=min(9, max(2, n // 5)), adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        # 5. Bollinger Bands
        bb_w = min(20, max(5, n // 3))
        df['BB_Middle'] = df['Close'].rolling(window=bb_w).mean()
        bb_std = df['Close'].rolling(window=bb_w).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)

        # 6. Volume Change
        # Промяна в обема на търговията (важно за потвърждение на трендове)
        df['Volume_Change'] = df['Volume'].pct_change() * 100

        # 7. Price Change
        # Дневна промяна в цената (в проценти)
        df['Price_Change'] = df['Close'].pct_change() * 100

        # 8. High-Low Range
        # Разликата между най-високата и най-ниската цена за деня
        df['HL_Range'] = df['High'] - df['Low']

        # 9. Open-Close Range
        # Разликата между цената при отваряне и затваряне
        df['OC_Range'] = df['Close'] - df['Open']

        # 10. ATR
        atr_w = min(14, max(3, n // 4))
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = true_range.rolling(window=atr_w).mean()

        # 11. Stochastic Oscillator
        stoch_w = min(14, max(3, n // 4))
        low_14 = df['Low'].rolling(window=stoch_w).min()
        high_14 = df['High'].rolling(window=stoch_w).max()
        df['Stoch_K'] = ((df['Close'] - low_14) / (high_14 - low_14)) * 100
        df['Stoch_D'] = df['Stoch_K'].rolling(window=min(3, max(1, n // 8))).mean()

        # 12. Williams %R
        df['Williams_R'] = ((high_14 - df['Close']) / (high_14 - low_14)) * -100

        # 13. OBV (On-Balance Volume)
        # Натрупване на обем base на посоката на цената
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

        # 14. VWAP (Volume Weighted Average Price) - approximation
        df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()

        # 15. MFI (Money Flow Index) - RSI с обем
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        money_flow = typical_price * df['Volume']
        positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(14).sum()
        negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(14).sum()
        mfi_ratio = positive_flow / negative_flow
        df['MFI'] = 100 - (100 / (1 + mfi_ratio))

        # 16. CCI
        cci_w = min(20, max(5, n // 3))
        tp_sma = typical_price.rolling(cci_w).mean()
        tp_mad = typical_price.rolling(cci_w).apply(lambda x: np.abs(x - x.mean()).mean())
        df['CCI'] = (typical_price - tp_sma) / (0.015 * tp_mad)

        # 17. ADX
        adx_w = min(14, max(3, n // 4))
        plus_dm = df['High'].diff()
        minus_dm = -df['Low'].diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        atr_adx = true_range.rolling(adx_w).mean()
        plus_di = 100 * (plus_dm.rolling(adx_w).mean() / atr_adx)
        minus_di = 100 * (minus_dm.rolling(adx_w).mean() / atr_adx)
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
        df['ADX'] = dx.rolling(adx_w).mean()

        # 18. Price Patterns
        # Higher High / Lower Low
        df['Higher_High'] = (df['High'] > df['High'].shift(1)).astype(int)
        df['Lower_Low'] = (df['Low'] < df['Low'].shift(1)).astype(int)
        df['Higher_Low'] = (df['Low'] > df['Low'].shift(1)).astype(int)
        df['Lower_High'] = (df['High'] < df['High'].shift(1)).astype(int)

        # 19. Volatility Ratios
        df['Volatility_Ratio'] = df['ATR'] / df['Close'] * 100
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']

        # 20. Momentum Divergence
        # RSI divergence from price
        df['RSI_Divergence'] = df['Close'].pct_change(5) - df['RSI'].pct_change(5)

        # 21. Rate of Change (ROC)
        for period in [5, 10, 20]:
            df[f'ROC_{period}'] = df['Close'].pct_change(period) * 100

        # 22. Exponential weighted moving stats
        df['EWMA_Volatility'] = df['Price_Change'].ewm(span=20).std() * np.sqrt(252)

        # Премахване на редове с NaN стойности (от изчисленията)
        df = df.dropna()

        self.data = df

        print(f"✅ Създадени {len(df.columns)} колони с индикатори")
        print(f"📊 Налични данни: {len(df)} реда")

        return df

    def create_target_variable(self, days_ahead=1):
        """
        Създава target variable за предсказване.

        Параметри:
        ----------
        days_ahead : int
            След колко дни искаме да предскажем цената (по подразбиране 1 ден)

        Създава:
        - Future_Price: Цената след N дни
        - Price_Direction: 1 (нагоре) или 0 (надолу)
        """
        print(f"🎯 Създаване на target variable за {days_ahead} ден напред...")

        # Цената след N дни
        self.data['Future_Price'] = self.data['Close'].shift(-days_ahead)

        # Посока на промяната (1 = нагоре, 0 = надолу)
        self.data['Price_Direction'] = (
            self.data['Future_Price'] > self.data['Close']
        ).astype(int)

        # Премахване на последните N реда (нямаме бъдещи данни за тях)
        self.data = self.data[:-days_ahead]

        print(f"✅ Target variable създаден")
        print(f"📈 Дни нагоре: {self.data['Price_Direction'].sum()}")
        print(f"📉 Дни надолу: {len(self.data) - self.data['Price_Direction'].sum()}")

        return self.data

    def normalize_data(self, columns_to_scale=None):
        """
        Нормализира данните между 0 и 1 за по-добро ML обучение.

        Параметри:
        ----------
        columns_to_scale : list, optional
            Списък с колони за нормализация. Ако не е зададено, използва всички числови.

        Връща:
        -------
        pandas.DataFrame
            Нормализирани данни
        """
        print("🔢 Нормализиране на данни...")

        if columns_to_scale is None:
            # Вземаме всички числови колони освен Date и Price_Direction
            columns_to_scale = self.data.select_dtypes(include=[np.number]).columns.tolist()
            columns_to_scale = [col for col in columns_to_scale if col not in ['Price_Direction']]

        # Запазване на не-нормализираните колони
        non_scaled_cols = [col for col in self.data.columns if col not in columns_to_scale]
        non_scaled_data = self.data[non_scaled_cols].copy()

        # Нормализиране
        scaled_array = self.scaler.fit_transform(self.data[columns_to_scale])
        scaled_df = pd.DataFrame(scaled_array, columns=columns_to_scale, index=self.data.index)

        # Обединяване на нормализираните и не-нормализираните данни
        self.scaled_data = pd.concat([non_scaled_data, scaled_df], axis=1)

        print(f"✅ {len(columns_to_scale)} колони нормализирани")

        return self.scaled_data

    def create_sequences(self, data, seq_length=60):
        """
        Създава последователности за LSTM модела.

        LSTM модела се учи от последователности от данни.
        Например: взима последните 60 дни за да предскаже следващия ден.

        Параметри:
        ----------
        data : pandas.DataFrame или numpy.array
            Подготвени данни
        seq_length : int
            Дължина на последователността (по подразбиране 60 дни)

        Връща:
        -------
        tuple
            (X, y) - входни последователности и изходни стойности
        """
        print(f"🔄 Създаване на последователности с дължина {seq_length}...")

        if isinstance(data, pd.DataFrame):
            data = data.values

        X, y = [], []

        for i in range(seq_length, len(data)):
            # X: последните 60 дни данни
            X.append(data[i-seq_length:i])
            # y: таргет стойността (Future_Price или Price_Direction)
            y.append(data[i, -1])  # Последната колона е target

        X, y = np.array(X), np.array(y)

        print(f"✅ Създадени {len(X)} последователности")
        print(f"📊 Форма на X: {X.shape}")
        print(f"📊 Форма на y: {y.shape}")

        return X, y

    def split_data(self, X, y, train_size=0.8):
        """
        Разделя данните на тренировъчни и тестови.

        Параметри:
        ----------
        X : numpy.array
            Входни данни
        y : numpy.array
            Target данни
        train_size : float
            Процент от данните за обучение (по подразбиране 80%)

        Връща:
        -------
        tuple
            (X_train, X_test, y_train, y_test)
        """
        split_index = int(len(X) * train_size)

        X_train = X[:split_index]
        X_test = X[split_index:]
        y_train = y[:split_index]
        y_test = y[split_index:]

        print(f"📊 Разделяне на данни:")
        print(f"   Тренировъчни: {len(X_train)} примера ({train_size*100:.0f}%)")
        print(f"   Тестови: {len(X_test)} примера ({(1-train_size)*100:.0f}%)")

        return X_train, X_test, y_train, y_test

    def get_feature_names(self):
        """
        Връща имената на всички създадени features.
        """
        return self.data.columns.tolist()


# Тестване на модула
if __name__ == "__main__":
    print("🚀 Тестване на Preprocessing Module\n")

    # Импортиране на data collector
    import sys
    sys.path.append('..')
    from src.data_collection import StockDataCollector

    # Свалане на данни
    collector = StockDataCollector(ticker='AAPL', period='1y', interval='1d')
    data = collector.fetch_stock_data(save_to_csv=False)

    if data is not None:
        # Създаване на preprocessor
        preprocessor = StockDataPreprocessor(data)

        # Изчисляване на индикатори
        data_with_indicators = preprocessor.calculate_technical_indicators()
        print("\n📊 Колони след индикаторите:")
        print(data_with_indicators.columns.tolist())

        # Създаване на target variable
        preprocessor.create_target_variable(days_ahead=1)

        # Нормализиране
        normalized_data = preprocessor.normalize_data()

        print("\n📊 Първите 3 реда от обработените данни:")
        print(normalized_data.head(3))

        # Създаване на последователности
        # Подготовка за LSTM модела
        feature_cols = [col for col in normalized_data.columns if col not in ['Date']]
        model_data = normalized_data[feature_cols].values

        X, y = preprocessor.create_sequences(model_data, seq_length=60)

        # Разделяне на train/test
        X_train, X_test, y_train, y_test = preprocessor.split_data(X, y, train_size=0.8)

        print("\n✅ Данните са готови за модела!")
