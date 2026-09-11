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
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Колони, които са target-и, а не features. Никога не влизат в X —
# Price_Direction[t] е точно отговорът, който моделът трябва да предскаже.
TARGET_COLUMNS = ['Future_Price', 'Price_Direction']

# Колоната, която моделът предсказва: 1 = утре нагоре, 0 = утре надолу.
TARGET_COLUMN = 'Price_Direction'

# Стандартните периоди на индикаторите. Фиксирани са нарочно: ако размерът
# зависи от това колко данни са свалени, "RSI" при 1 година значи друго от
# "RSI" при 2 години. Модел, трениран на едното, получава на входа си колона
# със същото име, но различен смисъл.
W_SMA_SHORT, W_SMA_LONG = 20, 50
W_EMA_SHORT, W_EMA_LONG, W_MACD_SIGNAL = 12, 26, 9
W_RSI, W_BB, W_ATR = 14, 20, 14
W_STOCH, W_STOCH_D = 14, 3
W_MFI, W_CCI, W_ADX = 14, 20, 14
W_VWAP, W_EWMA_VOL, W_VOLUME = 20, 20, 20
ROC_PERIODS = [5, 10, 20]

# Най-дългият прозорец определя колко реда в началото нямат пълна история.
# ADX смила два пъти по W_ADX, затова му трябват 2*W_ADX-1 реда.
WARMUP_ROWS = max(W_SMA_LONG, W_EMA_LONG, W_BB, W_CCI,
                  2 * W_ADX - 1, max(ROC_PERIODS)) + 1

# Колони в абсолютни нива (долари, брой акции). Растат с годините, затова
# стойностите от теста са извън диапазона, който моделът е виждал в
# тренировката — и той няма как да ги разпознае. Остават в self.data за
# графики и backtest, но никога не влизат в модела. За всяка от тях има
# стационарен заместител: съотношение или процентна промяна.
NON_STATIONARY_COLUMNS = [
    'Open', 'High', 'Low', 'Close', 'Volume',
    'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26',
    'MACD', 'MACD_Signal', 'MACD_Histogram',
    'BB_Middle', 'BB_Upper', 'BB_Lower',
    'ATR', 'HL_Range', 'OC_Range', 'OBV', 'VWAP',
]


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
        self.scaler = None
        self.scaled_data = None
        self._scaled_columns = None
        self._fit_rows = None

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
        print("[UP] Изчисляване на технически индикатори...")

        df = self.data.copy()
        n = len(df)

        if n <= WARMUP_ROWS:
            raise ValueError(
                f"[FAIL] Само {n} реда данни. Индикаторите имат фиксирани "
                f"периоди (най-дългият е {W_SMA_LONG} дни), затова първите "
                f"{WARMUP_ROWS} реда отпадат и не остава нищо. Свали по-дълъг "
                f"период."
            )

        # Фиксирани периоди — виж коментара при константите
        sma20_w = W_SMA_SHORT
        sma50_w = W_SMA_LONG

        # 1. Simple Moving Averages (SMA)
        df['SMA_20'] = df['Close'].rolling(window=sma20_w).mean()
        df['SMA_50'] = df['Close'].rolling(window=sma50_w).mean()

        # 2. Exponential Moving Averages (EMA)
        ema12_w = W_EMA_SHORT
        ema26_w = W_EMA_LONG
        df['EMA_12'] = df['Close'].ewm(span=ema12_w, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=ema26_w, adjust=False).mean()

        # 3. RSI
        rsi_w = W_RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_w).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_w).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 4. MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=W_MACD_SIGNAL, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        # 5. Bollinger Bands
        bb_w = W_BB
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
        atr_w = W_ATR
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = true_range.rolling(window=atr_w).mean()

        # 11. Stochastic Oscillator
        stoch_w = W_STOCH
        low_14 = df['Low'].rolling(window=stoch_w).min()
        high_14 = df['High'].rolling(window=stoch_w).max()
        df['Stoch_K'] = ((df['Close'] - low_14) / (high_14 - low_14)) * 100
        df['Stoch_D'] = df['Stoch_K'].rolling(window=W_STOCH_D).mean()

        # 12. Williams %R
        df['Williams_R'] = ((high_14 - df['Close']) / (high_14 - low_14)) * -100

        # 13. OBV (On-Balance Volume)
        # Натрупване на обем base на посоката на цената
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

        # 14. VWAP (Volume Weighted Average Price) — пълзящ прозорец.
        # Кумулативен VWAP от началото на серията зависи от това откога сме
        # свалили данните, което го прави безсмислен като сигнал.
        vwap_w = W_VWAP
        typical = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = ((typical * df['Volume']).rolling(vwap_w).sum()
                      / df['Volume'].rolling(vwap_w).sum())

        # 15. MFI (Money Flow Index) - RSI с обем
        mfi_w = W_MFI
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        money_flow = typical_price * df['Volume']
        positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(mfi_w).sum()
        negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(mfi_w).sum()
        mfi_ratio = positive_flow / negative_flow
        df['MFI'] = 100 - (100 / (1 + mfi_ratio))

        # 16. CCI
        cci_w = W_CCI
        tp_sma = typical_price.rolling(cci_w).mean()
        tp_mad = typical_price.rolling(cci_w).apply(lambda x: np.abs(x - x.mean()).mean())
        df['CCI'] = (typical_price - tp_sma) / (0.015 * tp_mad)

        # 17. ADX
        adx_w = W_ADX
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

        # 21. Rate of Change (ROC) — адаптивни периоди за кратък data frame
        roc_periods = ROC_PERIODS
        for period in roc_periods:
            df[f'ROC_{period}'] = df['Close'].pct_change(period) * 100

        # 22. Exponential weighted moving stats
        ewma_span = W_EWMA_VOL
        df['EWMA_Volatility'] = df['Price_Change'].ewm(span=ewma_span).std() * np.sqrt(252)

        # === 23. СТАЦИОНАРНИ ЗАМЕСТИТЕЛИ НА НИВАТА ===
        # Всяко абсолютно ниво се превръща в съотношение или процент, за да
        # значи едно и също при цена $50 и при цена $500.
        close = df['Close']

        df['Close_vs_SMA20'] = close / df['SMA_20'] - 1
        df['Close_vs_SMA50'] = close / df['SMA_50'] - 1
        df['SMA20_vs_SMA50'] = df['SMA_20'] / df['SMA_50'] - 1
        df['Close_vs_EMA12'] = close / df['EMA_12'] - 1
        df['EMA12_vs_EMA26'] = df['EMA_12'] / df['EMA_26'] - 1

        df['MACD_Norm'] = df['MACD'] / close
        df['MACD_Hist_Norm'] = df['MACD_Histogram'] / close

        # Къде е цената в Bollinger канала: 0 = долната лента, 1 = горната
        df['BB_Position'] = ((close - df['BB_Lower'])
                             / (df['BB_Upper'] - df['BB_Lower']))

        df['HL_Range_Pct'] = (df['High'] - df['Low']) / close * 100
        df['OC_Range_Pct'] = (close - df['Open']) / close * 100
        df['Gap_Pct'] = (df['Open'] / close.shift(1) - 1) * 100

        vol_avg = df['Volume'].rolling(window=W_VOLUME).mean()
        df['Volume_Ratio'] = df['Volume'] / vol_avg
        df['OBV_Norm'] = df['OBV'].diff() / vol_avg
        df['Close_vs_VWAP'] = close / df['VWAP'] - 1

        # === 24. КАЛЕНДАРНИ ===
        # Отчетите на компаниите се струпват около края на тримесечията,
        # а част от обема е свързан с края на месеца.
        # utc=True, защото CSV от различни сесии може да смесва часови зони
        # (yfinance връща tz-aware дати) и pandas отказва да ги обедини.
        raw_dates = df['Date'] if 'Date' in df.columns else df.index
        dates = pd.DatetimeIndex(pd.to_datetime(raw_dates, utc=True))

        df['Day_Of_Week'] = dates.dayofweek
        df['Is_Quarter_Month'] = (dates.month % 3 == 0).astype(int)
        df['Is_Month_End'] = dates.is_month_end.astype(int)

        # Деления като pct_change и Close/SMA могат да дадат inf при нула.
        # Ако inf стигне до скалера, цялата колона става безполезна.
        df = df.replace([np.inf, -np.inf], np.nan)

        # ffill запълва редки дупки ВЪТРЕ в серията (например липсващ обем
        # за един ден) — това ползва само минали стойности и е позволено.
        df = df.ffill()

        # Началните редове нямат достатъчно история за дългите прозорци.
        # Тук преди стоеше bfill(), който ги запълваше с БЪДЕЩИ стойности:
        # SMA_50 на ден 0 получаваше средната от дни 0..49, тоест моделът
        # виждаше напред. Такива редове се изхвърлят, а не се измислят.
        rows_before = len(df)
        df = df.dropna().reset_index(drop=True)
        dropped = rows_before - len(df)

        if len(df) < 2:
            raise ValueError(
                f"[FAIL] След изхвърляне на warmup-а не остана нищо "
                f"({rows_before} реда вход). Трябват поне ~{rows_before} + 60 "
                f"дни данни за тези индикатори."
            )

        self.data = df

        print(f"[OK] Създадени {len(df.columns)} колони с индикатори")
        print(f"[INFO] Изхвърлени {dropped} реда warmup (без пълна история)")
        print(f"[INFO] Налични данни: {len(df)} реда")

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
        print(f"[TARGET] Създаване на target variable за {days_ahead} ден напред...")

        self.days_ahead = days_ahead

        # Цената след N дни
        future = self.data['Close'].shift(-days_ahead)
        self.data['Future_Price'] = future

        # Посока на промяната (1 = нагоре, 0 = надолу).
        # Последните N реда остават NaN — за тях бъдещето още не е настъпило.
        # НЕ ги режем: последният ред е днешният ден и от него се прави
        # предсказанието за утре. Тренировката сама ги пропуска.
        self.data['Price_Direction'] = np.where(
            future.isna(), np.nan, (future > self.data['Close']).astype(float)
        )

        up = int(np.nansum(self.data['Price_Direction']))
        labelled = int(self.data['Price_Direction'].notna().sum())

        print(f"[OK] Target variable създаден")
        print(f"[UP] Дни нагоре: {up}")
        print(f"[DOWN] Дни надолу: {labelled - up}")
        print(f"[INFO] {days_ahead} ред(а) без етикет (най-новите) — за предсказване")

        return self.data

    def _train_row_boundary(self, seq_length, train_size):
        """
        Първият ред, който попада в тестова последователност.

        Скалерът няма право да вижда нищо от този ред нататък — иначе
        средното и дисперсията носят информация от теста.
        """
        if TARGET_COLUMN not in self.data.columns:
            return len(self.data)

        target = self.data[TARGET_COLUMN].values.astype(float)
        labelled = np.flatnonzero(~np.isnan(target))
        if len(labelled) == 0:
            return len(self.data)

        end = labelled[-1] + 1
        n_seq = end - seq_length + 1
        if n_seq < 2:
            return end
        return max(10, int(n_seq * train_size))

    def _transform_all(self):
        """Прилага текущия скалер върху всички редове."""
        cols = self._scaled_columns
        non_scaled = [c for c in self.data.columns if c not in cols]
        scaled = pd.DataFrame(
            self.scaler.transform(self.data[cols]),
            columns=cols,
            index=self.data.index,
        )
        self.scaled_data = pd.concat([self.data[non_scaled], scaled], axis=1)
        return self.scaled_data

    def normalize_data(self, columns_to_scale=None, train_size=0.8, seq_length=60):
        """
        Стандартизира features за ML обучение.

        Два избора тук имат значение:

        1. Скалерът се учи САМО от тренировъчните редове. Ако се учи от
           всичко, средното и дисперсията носят информация от бъдещето и
           резултатите излизат по-добри, отколкото са в действителност.

        2. StandardScaler, не MinMax. Стационарните features имат дебели
           опашки, а MinMax мащабира по крайните стойности — един скок от
           10% свива всички нормални дни в няколко процента от диапазона.
           Точно най-информативните колони (Price_Change, Gap_Pct) така
           стават по-тихи от ограничените осцилатори и мрежата ги игнорира.

        Параметри:
        ----------
        columns_to_scale : list, optional
            Колони за скалиране. По подразбиране всички числови без target-ите.
        train_size : float
            Каква част от последователностите са тренировъчни
        seq_length : int
            Дължина на последователността (определя къде почва тестът)

        Връща:
        -------
        pandas.DataFrame
            Данни със стандартизирани features
        """
        print("[NUM] Нормализиране на данни...")

        if columns_to_scale is None:
            # Всички числови колони освен Date и target-ите.
            # Target колоните не са features и не бива да се скалират.
            columns_to_scale = self.data.select_dtypes(include=[np.number]).columns.tolist()
            columns_to_scale = [col for col in columns_to_scale
                                if col not in TARGET_COLUMNS]

        fit_rows = self._train_row_boundary(seq_length, train_size)

        self.scaler = StandardScaler()
        self.scaler.fit(self.data[columns_to_scale].iloc[:fit_rows])
        self._scaled_columns = list(columns_to_scale)
        self._fit_rows = fit_rows

        self._transform_all()

        print(f"[OK] {len(columns_to_scale)} колони стандартизирани")
        print(f"[INFO] Скалерът е трениран само от първите {fit_rows} "
              f"от {len(self.data)} реда")

        return self.scaled_data

    def apply_scaler(self, scaler, columns):
        """
        Пренормализира с вече трениран скалер.

        Ползва се при предсказване със записан модел: входовете трябва да
        са в същата скала, в която моделът е учил. Ако всеки път се тренира
        нов скалер от новосвалените данни, моделът получава числа, които
        не отговарят на нищо от тренировката.
        """
        missing = [c for c in columns if c not in self.data.columns]
        if missing:
            raise ValueError(
                f"[FAIL] Записаният скалер иска колони, които ги няма: {missing[:5]}"
            )

        self.scaler = scaler
        self._scaled_columns = list(columns)
        self._fit_rows = None  # външен скалер — не го пипаме
        return self._transform_all()

    @property
    def scaled_columns(self):
        """Колоните, върху които скалерът е трениран, в реда на трениране."""
        return list(self._scaled_columns or [])

    def get_feature_columns(self):
        """
        Имената на колоните, които влизат в модела като features.

        Изключва Date (не е число), target колоните — ако Price_Direction
        остане във features, моделът чете отговора направо от входа — и
        абсолютните нива, които не са сравними между различни периоди.
        """
        source = self.scaled_data if self.scaled_data is not None else self.data
        excluded = set(['Date'] + TARGET_COLUMNS + NON_STATIONARY_COLUMNS)
        return [c for c in source.columns if c not in excluded]

    def create_sequences(self, features, target, seq_length=60):
        """
        Създава последователности за LSTM модела.

        Подравняване (без надничане в бъдещето):
            X[k] = features[k : k+seq_length]   -> дни k .. k+seq_length-1
            y[k] = target[k+seq_length-1]       -> посоката за последния ден

        Последният ден в прозореца е "днес". Всичко в X е известно при
        затваряне на днешния ден, а y казва дали утре затваря по-високо.

        Параметри:
        ----------
        features : numpy.array или pandas.DataFrame
            Само feature колони (без target-ите)
        target : numpy.array или pandas.Series
            Target стойност за всеки ред (Price_Direction: 0/1)
        seq_length : int
            Дължина на последователността (по подразбиране 60 дни)

        Връща:
        -------
        tuple
            (X, y, end_idx) - последователности, target-и и индексът на
            последния ден от всеки прозорец (за подравняване на цени/дати)
        """
        print(f"[RUN] Създаване на последователности с дължина {seq_length}...")

        if isinstance(features, pd.DataFrame):
            features = features.values
        if isinstance(target, (pd.Series, pd.DataFrame)):
            target = target.values

        features = np.asarray(features, dtype=np.float32)
        target = np.asarray(target).ravel()

        if len(features) != len(target):
            raise ValueError(
                f"[FAIL] features ({len(features)}) и target ({len(target)}) "
                f"имат различна дължина"
            )
        if len(features) < seq_length:
            raise ValueError(
                f"[FAIL] Само {len(features)} реда, а трябват поне {seq_length}"
            )

        end_idx = np.arange(seq_length - 1, len(features))
        X = np.stack([features[i - seq_length + 1: i + 1] for i in end_idx])
        y = target[end_idx].astype(np.float32)

        print(f"[OK] Създадени {len(X)} последователности")
        print(f"[INFO] Форма на X: {X.shape}")
        print(f"[INFO] Форма на y: {y.shape}")
        print(f"[INFO] Баланс на target: {y.mean()*100:.1f}% нагоре, "
              f"{(1-y.mean())*100:.1f}% надолу")

        return X, y, end_idx

    def prepare_model_data(self, seq_length=60, train_size=0.8):
        """
        Единствената правилна входна точка за модела.

        Сама избира feature колоните, target-а и подравнените реални цени,
        така че никой извикващ да не reconstruct-ва това ръчно (и да сбърка).

        Връща:
        -------
        tuple
            (X, y, prices)
            X      : (n, seq_length, n_features) — нормализирани features
            y      : (n,) — 1 ако утре затваря по-високо, иначе 0
            prices : (n,) — реалната Close цена на последния ден от прозореца
        """
        if self.scaled_data is None:
            raise ValueError("[FAIL] Първо извикай normalize_data()")
        if TARGET_COLUMN not in self.data.columns:
            raise ValueError("[FAIL] Първо извикай create_target_variable()")

        # Ако скалерът е трениран за друг split, преучи го — иначе щеше да
        # е видял редове, които сега попадат в теста.
        required = self._train_row_boundary(seq_length, train_size)
        if self._fit_rows is not None and self._fit_rows != required:
            self.normalize_data(train_size=train_size, seq_length=seq_length)

        feature_cols = self.get_feature_columns()
        target = self.data[TARGET_COLUMN].values.astype(float)

        # Най-новите редове нямат етикет (бъдещето още не е настъпило) —
        # те се ползват само за предсказване, не за тренировка.
        labelled = np.flatnonzero(~np.isnan(target))
        if len(labelled) == 0:
            raise ValueError("[FAIL] Няма нито един ред с етикет")
        end = labelled[-1] + 1

        features = self.scaled_data[feature_cols].values[:end]
        target = target[:end]

        X, y, end_idx = self.create_sequences(features, target, seq_length)
        prices = self.data['Close'].values[:end][end_idx]

        return X, y, prices

    def get_latest_sequence(self, seq_length=60):
        """
        Последният прозорец от features — включително днешния ден.

        Това е входът за реално предсказание: моделът гледа последните
        seq_length дни (последният е днес) и казва дали утре затваря по-високо.

        Връща:
        -------
        numpy.array
            (1, seq_length, n_features), готов за model.predict()
        """
        if self.scaled_data is None:
            raise ValueError("[FAIL] Първо извикай normalize_data()")

        feature_cols = self.get_feature_columns()
        features = self.scaled_data[feature_cols].values

        if len(features) < seq_length:
            raise ValueError(
                f"[FAIL] Само {len(features)} реда, а трябват поне {seq_length}"
            )

        window = features[-seq_length:]
        return window.reshape(1, seq_length, -1).astype(np.float32)

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

        print(f"[INFO] Разделяне на данни:")
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
    print("[START] Тестване на Preprocessing Module\n")

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
        print("\n[INFO] Колони след индикаторите:")
        print(data_with_indicators.columns.tolist())

        # Създаване на target variable
        preprocessor.create_target_variable(days_ahead=1)

        # Нормализиране
        normalized_data = preprocessor.normalize_data()

        print("\n[INFO] Първите 3 реда от обработените данни:")
        print(normalized_data.head(3))

        # Създаване на последователности
        # Подготовка за LSTM модела
        X, y, prices = preprocessor.prepare_model_data(seq_length=60)

        # Разделяне на train/test
        X_train, X_test, y_train, y_test = preprocessor.split_data(X, y, train_size=0.8)

        print("\n[OK] Данните са готови за модела!")
