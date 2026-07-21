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
        """
        print("📈 Изчисляване на технически индикатори...")

        df = self.data.copy()

        # 1. Simple Moving Averages (SMA)
        # SMA показва средната цена за последните N дни
        df['SMA_20'] = df['Close'].rolling(window=20).mean()  # 20-дневна средна
        df['SMA_50'] = df['Close'].rolling(window=50).mean()  # 50-дневна средна

        # 2. Exponential Moving Averages (EMA)
        # EMA дава повече тежест на по-новите цени
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()

        # 3. RSI (Relative Strength Index)
        # RSI измерва "свръхкупеност" или "свръхпродаденост"
        # Стойности: 0-100
        # > 70 = свръхкупена (може да падне)
        # < 30 = свръхпродадена (може да се качи)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 4. MACD (Moving Average Convergence Divergence)
        # MACD показва промени в тренда
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        # 5. Bollinger Bands
        # Bollinger Bands показват волатилността
        # Когато цената е близо до горната лента = скъпо
        # Когато цената е близо до долната лента = евтино
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
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
