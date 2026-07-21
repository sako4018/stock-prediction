# 🚀 Бързо Стартиране (Quick Start)

Следвай тези стъпки за да стартираш проекта за първи път.

## Стъпка 1: Инсталиране на Python библиотеките

Отвори Command Prompt или PowerShell в папката на проекта и напиши:

```bash
pip install -r requirements.txt
```

Ако имаш NVIDIA GPU (RTX 2050), инсталирай и GPU support:

```bash
pip install tensorflow[and-cuda]
```

## Стъпка 2: Провери дали GPU работи

```bash
python -c "import tensorflow as tf; print('GPU:', tf.config.list_physical_devices('GPU'))"
```

Ако виждаш твоята видео карта в резултата - отлично! ✅

## Стъпка 3: Тествай със симулирани данни (бързо)

Първо можеш да тестваш системата с малък брой епохи (само 5-10 минути):

```bash
python main.py --ticker AAPL --train --epochs 10
```

## Стъпка 4: Направи предсказване

След като модела е тренирован:

```bash
python main.py --ticker AAPL --predict
```

Ще видиш:
- Текущата цена на Apple акциите
- Дали модела предсказва покачване или спад
- BUY или SELL сигнал
- Колко уверен е модела (в %)

## Стъпка 5: Тествай trading стратегията (Backtest)

```bash
python main.py --ticker AAPL --backtest
```

Ще видиш:
- Симулирана печалба/загуба
- Процент на успешните сделки
- Сравнение с просто "купи и дръж" стратегия
- Графики със сделките

## Препоръчан работен процес

### За първи път:
1. Започни с малък модел за тест (10 епохи)
2. Провери дали всичко работи
3. След това направи истинско обучение (100-200 епохи)

### Команди:

```bash
# ТЕСТ (бързо - 5 min)
python main.py --ticker AAPL --full --epochs 10

# ИСТИНСКО (бавно - 30-60 min, но по-точно)
python main.py --ticker AAPL --full --epochs 100
```

## Популярни акции за тестване

```bash
# Технологични компании
python main.py --ticker AAPL --predict   # Apple
python main.py --ticker TSLA --predict   # Tesla
python main.py --ticker GOOGL --predict  # Google
python main.py --ticker MSFT --predict   # Microsoft

# Crypto-related
python main.py --ticker COIN --predict   # Coinbase
```

## Помощ

Ако нещо не работи:
1. Провери дали си инсталирал всички библиотеки
2. Прочети README.md за детайли
3. Виж секцията "Често срещани проблеми"

## Следващи стъпки

След като разбереш как работи:
- Експериментирай с различни акции
- Промени параметрите (epochs, batch_size)
- Погледни в кода и разбери как работи всеки модул
- Опитай да добавиш нови функции

---

**Enjoy coding! 🎉**
