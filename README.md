# 📈 Stock Prediction System

Интелигентна система за предсказване на цени на акции с Machine Learning (LSTM Neural Network) и real-time данни.

## 🎯 Възможности

- ✅ **Real-time данни** от Yahoo Finance
- 🤖 **LSTM Neural Network** с GPU поддръжка (TensorFlow)
- 📊 **Технически индикатори** (RSI, MACD, Moving Averages, Bollinger Bands)
- 💰 **Trading симулация** с BUY/SELL сигнали
- 📈 **Backtesting** на стратегии
- 🎨 **Визуализации** на резултатите
- 🔮 **Предсказания** за следващите дни

## 🚀 Инсталация

### 1. Изисквания

- Python 3.8 или по-нова версия
- NVIDIA GPU (препоръчително за по-бързо обучение)
- pip package manager

### 2. Клониране на проекта

```bash
cd Desktop/VS code/stock-prediction
```

### 3. Инсталиране на зависимости

```bash
pip install -r requirements.txt
```

**Важно за Windows с GPU:**
```bash
# За да използваш NVIDIA GPU с TensorFlow
pip install tensorflow[and-cuda]
```

### 4. Проверка на GPU

```bash
python -c "import tensorflow as tf; print('GPU:', tf.config.list_physical_devices('GPU'))"
```

Ако виждаш твоята RTX 2050, значи GPU е разпознато! ✅

## 📖 Използване

### Бързо начало

#### 1️⃣ Тренировка на модел за Apple (AAPL)

```bash
python main.py --ticker AAPL --train --epochs 50
```

Това ще:
- Свали 2 години данни за AAPL
- Изчисли технически индикатори
- Тренира LSTM модел (50 епохи)
- Запази модела в `models/AAPL_stock_model.keras`

#### 2️⃣ Backtest на модела

```bash
python main.py --ticker AAPL --backtest
```

Това ще:
- Зареди обучения модел
- Симулира trading стратегия
- Покаже печалби/загуби
- Създаде визуализация `AAPL_backtest_results.png`

#### 3️⃣ Предсказване на бъдещето

```bash
python main.py --ticker AAPL --predict
```

Това ще покаже:
- Текуща цена
- Предсказана посока (нагоре/надолу)
- BUY/SELL сигнал
- Увереност на модела

#### 4️⃣ Пълен pipeline (всичко наведнъж)

```bash
python main.py --ticker TSLA --full --epochs 100
```

### Примери с различни акции

```bash
# Tesla
python main.py --ticker TSLA --train --epochs 100

# Google
python main.py --ticker GOOGL --predict

# Microsoft
python main.py --ticker MSFT --backtest

# Amazon
python main.py --ticker AMZN --full
```

## 🏗️ Структура на проекта

```
stock-prediction/
│
├── data/                          # Запазени данни (CSV файлове)
│   └── AAPL_2y_1d.csv
│
├── models/                        # Обучени модели
│   ├── AAPL_stock_model.keras
│   ├── AAPL_stock_model_config.json
│   └── AAPL_stock_model_history.json
│
├── src/                           # Изходен код
│   ├── data_collection.py         # Събиране на данни
│   ├── preprocessing.py           # Обработка и индикатори
│   ├── model.py                   # LSTM модел
│   └── backtest.py                # Backtesting система
│
├── notebooks/                     # Jupyter notebooks (за експерименти)
├── tests/                         # Unit tests
├── static/                        # Web dashboard static files (future)
├── templates/                     # Web dashboard HTML templates (future)
│
├── main.py                        # Главен скрипт
├── requirements.txt               # Python зависимости
└── README.md                      # Тази документация
```

## 🧠 Как работи?

### 1. Събиране на данни
Модулът `data_collection.py` използва `yfinance` за да свали:
- Open, High, Low, Close цени
- Volume (обем на търговията)
- Real-time информация

### 2. Обработка на данни
Модулът `preprocessing.py` създава технически индикатори:

- **SMA** (Simple Moving Average) - 20 и 50 дни
- **EMA** (Exponential Moving Average) - 12 и 26 дни
- **RSI** (Relative Strength Index) - свръхкупеност/свръхпродаденост
- **MACD** (Moving Average Convergence Divergence) - трендове
- **Bollinger Bands** - волатилност
- **Volume Change** - промяна в обема
- **Price Change** - дневна промяна

### 3. LSTM Neural Network
Модулът `model.py` създава LSTM (Long Short-Term Memory) мрежа:

```
Архитектура:
├── LSTM Layer (128 units) → Dropout → Batch Normalization
├── LSTM Layer (64 units)  → Dropout → Batch Normalization
├── LSTM Layer (32 units)  → Dropout → Batch Normalization
├── Dense Layer (25 units)
└── Output Layer (1 unit) → Предсказание
```

**Защо LSTM?**
- Научава се от последователности (времеви серии)
- "Помни" дългосрочни зависимости в данните
- Най-добър избор за stock prediction

### 4. Backtesting
Модулът `backtest.py` симулира реални търговски операции:

- Генерира BUY/SELL/HOLD сигнали
- Симулира портфолио с начален капитал $10,000
- Изчислява печалби/загуби
- Сравнява с "Buy & Hold" стратегията
- Изчислява Win Rate (процент печеливши сделки)

## 📊 Метрики за оценка

Системата изчислява:

- **Accuracy** - Колко често посоката е правилна
- **Precision** - От всички BUY сигнали, колко са верни
- **Recall** - От всички покачвания, колко сме уловили
- **F1-Score** - Баланс между Precision и Recall
- **Total Return** - Обща печалба/загуба в %
- **Win Rate** - Процент печеливши сделки
- **MAPE** - Mean Absolute Percentage Error

## 🎓 За начинаещи

### Какво е Machine Learning?

ML моделът "учи" от исторически данни как се движат цените и прави предсказания за бъдещето.

**Аналогия:** Представи си, че гледаш как се движи топка 1000 пъти. След това можеш да предскажеш накъде ще отиде следващия път.

### Какво е LSTM?

LSTM е тип neural network който е много добър за "запомняне" на последователности от данни.

**Аналогия:** Като когато четеш история - трябва да помниш какво се е случило преди, за да разбереш настоящето.

### Какво е Backtesting?

Backtesting проверява дали твоят модел работи върху минали данни.

**Аналогия:** Като да играеш шах партия отново за да видиш дали новата стратегия е по-добра.

### Коментари в кода

Всеки модул има много коментари на български които обясняват какво прави всеки ред код. Не се притеснявай да ги четеш!

## ⚙️ Параметри

### Command-line опции

```bash
python main.py [опции]

Опции:
  --ticker SYMBOL      Символ на акцията (default: AAPL)
  --period PERIOD      Период на данните: 1mo, 3mo, 6mo, 1y, 2y, 5y (default: 2y)
  --train              Тренира нов модел
  --predict            Прави предсказание
  --backtest           Изпълнява backtesting
  --full               Пълен pipeline (train + backtest)
  --epochs N           Брой епохи за обучение (default: 100)
  --batch-size N       Batch size (default: 32)
```

### Примери

```bash
# Бързо обучение (10 епохи) за тестване
python main.py --ticker AAPL --train --epochs 10

# Дълго обучение (200 епохи) за по-добра точност
python main.py --ticker AAPL --train --epochs 200

# По-малък batch size за по-малка GPU памет
python main.py --ticker AAPL --train --batch-size 16

# Повече данни (5 години)
python main.py --ticker AAPL --period 5y --train
```

## 📈 Популярни акции

### Технологични компании
- `AAPL` - Apple
- `MSFT` - Microsoft
- `GOOGL` - Google (Alphabet)
- `AMZN` - Amazon
- `TSLA` - Tesla
- `NVDA` - NVIDIA
- `META` - Meta (Facebook)

### Финансови институции
- `JPM` - JPMorgan Chase
- `BAC` - Bank of America
- `GS` - Goldman Sachs

### Други
- `DIS` - Disney
- `NKE` - Nike
- `NFLX` - Netflix
- `AMD` - AMD

## 🐛 Често срещани проблеми

### GPU не се разпознава

**Проблем:** `GPU: []` (празен списък)

**Решение:**
1. Инсталирай CUDA Toolkit от NVIDIA
2. Инсталирай cuDNN
3. Инсталирай TensorFlow с GPU поддръжка:
   ```bash
   pip install tensorflow[and-cuda]
   ```

### yfinance не връща данни

**Проблем:** `Няма данни за TICKER`

**Решение:**
- Провери дали ticker символът е правилен
- Опитай с по-кратък период: `--period 1y`
- Някои акции може да не са налични

### Недостатъчна памет

**Проблем:** `ResourceExhaustedError` или `Out of Memory`

**Решение:**
- Намали batch size: `--batch-size 16`
- Намали броя епохи: `--epochs 50`
- Затвори други приложения

### Модел не се намира

**Проблем:** `Моделът не е намерен: models/TICKER_stock_model.keras`

**Решение:**
- Първо тренирай модел: `python main.py --ticker TICKER --train`
- После backtest: `python main.py --ticker TICKER --backtest`

## 🔮 Бъдещи функции

- [ ] Web Dashboard с Flask (real-time визуализация)
- [ ] Multi-stock портфолио анализ
- [ ] Sentiment analysis от новини
- [ ] Alert system за BUY/SELL сигнали
- [ ] Интеграция с реални trading API
- [ ] Mobile app
- [ ] Cloud deployment

## 📚 Допълнителни ресурси

### Учебни материали
- [TensorFlow Tutorial](https://www.tensorflow.org/tutorials)
- [LSTM Explained](https://colah.github.io/posts/2015-08-Understanding-LSTMs/)
- [Technical Analysis Indicators](https://www.investopedia.com/terms/t/technicalindicator.asp)

### Документация
- [yfinance Docs](https://pypi.org/project/yfinance/)
- [scikit-learn](https://scikit-learn.org/stable/)
- [Keras API](https://keras.io/api/)

## ⚠️ Предупреждение

**Това е образователен проект!**

❌ НЕ инвестирай реални пари базирайки се само на този модел
❌ Миналите резултати НЕ гарантират бъдещи печалби
❌ Фондовият пазар е рисков и може да загубиш пари

✅ Използвай го за обучение
✅ Експериментирай с различни модели
✅ Разбери как работи ML

**Винаги консултирай с финансов съветник преди да инвестираш!**

## 🤝 Принос

Имаш идеи за подобрения? Създай pull request или отвори issue!

## 📝 Лиценз

Този проект е със свободен лиценз за образователни цели.

---


## ❤️Made on earth by Sercho and not exactly human❤️
