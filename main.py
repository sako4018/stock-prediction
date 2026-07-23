"""
Main Application
================
Главен скрипт който обединява всички модули и предоставя лесен интерфейс.

Използване:
    python main.py --ticker AAPL --train      # Тренира нов модел
    python main.py --ticker AAPL --predict    # Прави предсказания
    python main.py --ticker AAPL --backtest   # Backtest на модела
    python main.py --web                      # Стартира web dashboard
"""

import argparse
import sys
import os
import numpy as np
from datetime import datetime

# Добавяне на src директорията в path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_collection import StockDataCollector
from preprocessing import StockDataPreprocessor
from model import StockPredictionModel
from backtest import StockBacktester

class StockPredictionPipeline:
    """
    Главен pipeline който управлява целия процес.
    """

    def __init__(self, ticker='AAPL', period='2y', interval='1d'):
        self.ticker = ticker
        self.period = period
        self.interval = interval
        self.collector = None
        self.preprocessor = None
        self.model = None
        self.data = None

    def collect_data(self):
        """
        Стъпка 1: Събиране на данни
        """
        print("\n" + "="*60)
        print("[STEP 1] СЪБИРАНЕ НА ДАННИ")
        print("="*60 + "\n")

        self.collector = StockDataCollector(
            ticker=self.ticker,
            period=self.period,
            interval=self.interval
        )

        self.data = self.collector.fetch_stock_data()

        if self.data is None or len(self.data) == 0:
            raise ValueError(f"[ERROR] Няма данни за {self.ticker}")

        # Показване на real-time информация
        price_info = self.collector.get_real_time_price()
        if price_info:
            print(f"\n[INFO] Текуща информация за {self.ticker}:")
            print(f"   Цена: ${price_info['current_price']:.2f}")
            print(f"   Промяна: {price_info['change']:+.2f} ({price_info['change_percent']:+.2f}%)")

        return self.data

    def preprocess_data(self, days_ahead=1):
        """
        Стъпка 2: Обработка на данни
        """
        print("\n" + "="*60)
        print("[STEP 2] ОБРАБОТКА НА ДАННИ")
        print("="*60 + "\n")

        if self.data is None:
            raise ValueError("[ERROR] Първо събери данни с collect_data()")

        self.preprocessor = StockDataPreprocessor(self.data)

        # Изчисляване на технически индикатори
        self.preprocessor.calculate_technical_indicators()

        # Създаване на target variable
        self.preprocessor.create_target_variable(days_ahead=days_ahead)

        # Нормализиране
        self.preprocessor.normalize_data()

        print("\n[OK] Данните са готови за модела!")

        return self.preprocessor

    def prepare_sequences(self, seq_length=60, train_size=0.8):
        """
        Стъпка 3: Подготовка на последователности за LSTM
        """
        print("\n" + "="*60)
        print("[STEP 3] ПОДГОТОВКА НА ПОСЛЕДОВАТЕЛНОСТИ")
        print("="*60 + "\n")

        if self.preprocessor is None:
            raise ValueError("[ERROR] Първо обработи данни с preprocess_data()")

        # Взимане на нормализираните данни
        data = self.preprocessor.scaled_data

        # Премахване на не-числови колони
        feature_cols = [col for col in data.columns if col not in ['Date']]
        model_data = data[feature_cols].values

        # Създаване на последователности
        X, y = self.preprocessor.create_sequences(model_data, seq_length=seq_length)

        # Разделяне на train/test
        X_train, X_test, y_train, y_test = self.preprocessor.split_data(
            X, y, train_size=train_size
        )

        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test

        return X_train, X_test, y_train, y_test

    def train_model(self, epochs=100, batch_size=32):
        """
        Стъпка 4: Тренировка на модела
        """
        print("\n" + "="*60)
        print("[STEP 4] ТРЕНИРОВКА НА МОДЕЛА")
        print("="*60 + "\n")

        if not hasattr(self, 'X_train'):
            raise ValueError("[ERROR] Първо подготви последователностите с prepare_sequences()")

        # Създаване на модела
        sequence_length = self.X_train.shape[1]
        n_features = self.X_train.shape[2]

        self.model = StockPredictionModel(
            sequence_length=sequence_length,
            n_features=n_features
        )

        # Build архитектурата
        self.model.build_lstm_model(
            lstm_units=[128, 64, 32],
            dropout_rate=0.2
        )

        # Split train data за validation
        split_idx = int(len(self.X_train) * 0.9)
        X_train_split = self.X_train[:split_idx]
        X_val_split = self.X_train[split_idx:]
        y_train_split = self.y_train[:split_idx]
        y_val_split = self.y_train[split_idx:]

        # Тренировка
        self.model.train_model(
            X_train_split, y_train_split,
            X_val_split, y_val_split,
            epochs=epochs,
            batch_size=batch_size
        )

        # Запазване на модела
        model_name = f'{self.ticker}_stock_model'
        self.model.save_model(model_name)

        print(f"\n[OK] Модел тренирован и запазен като '{model_name}'")

        return self.model

    def evaluate_model(self):
        """
        Стъпка 5: Оценка на модела
        """
        print("\n" + "="*60)
        print("[STEP 5] ОЦЕНКА НА МОДЕЛА")
        print("="*60 + "\n")

        if self.model is None:
            raise ValueError("[ERROR] Първо тренирай модела с train_model()")

        # Оценка
        metrics = self.model.evaluate(self.X_test, self.y_test)

        return metrics

    def run_backtest(self):
        """
        Стъпка 6: Backtesting
        """
        print("\n" + "="*60)
        print("[STEP 6] BACKTESTING")
        print("="*60 + "\n")

        if self.model is None:
            raise ValueError("[ERROR] Първо тренирай модела с train_model()")

        # Предсказания върху test данните
        predictions = self.model.predict(self.X_test)

        # Взимане на реалните цени за test периода
        # Изчисляваме от колко ред започват test данните
        seq_length = self.X_train.shape[1]
        train_size = 0.8
        total_sequences = len(self.X_train) + len(self.X_test)
        train_sequences = len(self.X_train)

        # Реалните цени започват от seq_length
        all_prices = self.preprocessor.data['Close'].values[seq_length:]
        test_prices = all_prices[train_sequences:]

        # Backtesting
        backtester = StockBacktester(
            predictions=predictions,
            actual_values=self.y_test,
            prices=test_prices,
            initial_capital=10000
        )

        # Метрики за точност
        backtester.calculate_accuracy_metrics()

        # Trading сигнали
        backtester.generate_trading_signals(threshold=0.52)

        # Симулация
        results = backtester.simulate_trading(transaction_cost=0.001)

        # Визуализация
        plot_path = f'{self.ticker}_backtest_results.png'
        backtester.plot_results(save_path=plot_path)

        return results

    def predict_future(self, model_name=None):
        """
        Прави предсказание за следващия период
        """
        print("\n" + "="*60)
        print("[PREDICT] ПРЕДСКАЗВАНЕ НА БЪДЕЩЕТО")
        print("="*60 + "\n")

        # Зареждане на модела ако не е зареден
        if self.model is None:
            if model_name is None:
                model_name = f'{self.ticker}_stock_model'

            self.model = StockPredictionModel()
            self.model.load_model(model_name)

        # Подготовка на най-новите данни
        if self.preprocessor is None:
            self.collect_data()
            self.preprocess_data()

        # Взимане на последните 60 дни
        data = self.preprocessor.scaled_data
        feature_cols = [col for col in data.columns if col not in ['Date']]
        latest_data = data[feature_cols].values[-60:]

        # Reshape за модела
        latest_data = latest_data.reshape(1, 60, -1)

        # Предсказание
        prediction = self.model.predict(latest_data)

        # Денормализиране на предсказанието
        # (за простота показваме нормализираната стойност и посоката)
        predicted_value = prediction[0][0]

        current_price = self.data['Close'].values[-1]

        print(f"\n[INFO] Предсказание за {self.ticker}:")
        print(f"   Текуща цена: ${current_price:.2f}")
        print(f"   Предсказана стойност (нормализирана): {predicted_value:.4f}")

        if predicted_value > 0.5:
            signal = "BUY - Очаква се покачване"
            confidence = (predicted_value - 0.5) * 200  # Конвертиране в %
        else:
            signal = "SELL - Очаква се спад"
            confidence = (0.5 - predicted_value) * 200

        print(f"   Сигнал: {signal}")
        print(f"   Увереност: {confidence:.1f}%")

        return {
            'ticker': self.ticker,
            'current_price': current_price,
            'prediction': predicted_value,
            'signal': 'BUY' if predicted_value > 0.5 else 'SELL',
            'confidence': confidence
        }


def main():
    """
    Главна функция с command-line interface
    """
    parser = argparse.ArgumentParser(
        description='Stock Prediction ML System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примери:
  python main.py --ticker AAPL --train              # Тренира модел за Apple
  python main.py --ticker TSLA --predict            # Прави предсказание за Tesla
  python main.py --ticker GOOGL --backtest          # Backtest за Google
  python main.py --ticker MSFT --full               # Пълен pipeline (train + backtest)
  python main.py --web                              # Стартира web dashboard
        """
    )

    parser.add_argument('--ticker', type=str, default='AAPL',
                       help='Stock ticker symbol (default: AAPL)')
    parser.add_argument('--period', type=str, default='2y',
                       help='Data period (default: 2y)')
    parser.add_argument('--train', action='store_true',
                       help='Train a new model')
    parser.add_argument('--predict', action='store_true',
                       help='Make predictions')
    parser.add_argument('--backtest', action='store_true',
                       help='Run backtesting')
    parser.add_argument('--full', action='store_true',
                       help='Run full pipeline (train + backtest)')
    parser.add_argument('--web', action='store_true',
                       help='Start web dashboard')
    parser.add_argument('--epochs', type=int, default=100,
                       help='Training epochs (default: 100)')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Batch size (default: 32)')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("STOCK PREDICTION SYSTEM")
    print("="*60)
    print(f"\n[TIME] Време: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[INFO] Акция: {args.ticker}")
    print(f"[INFO] Период: {args.period}\n")

    # Web Dashboard
    if args.web:
        print("[INFO] Стартиране на web dashboard...")
        print("[INFO] Ще видиш командата за стартиране в следваща версия")
        return

    # Създаване на pipeline
    pipeline = StockPredictionPipeline(
        ticker=args.ticker,
        period=args.period,
        interval='1d'
    )

    try:
        # Full Pipeline
        if args.full:
            pipeline.collect_data()
            pipeline.preprocess_data(days_ahead=1)
            pipeline.prepare_sequences(seq_length=60, train_size=0.8)
            pipeline.train_model(epochs=args.epochs, batch_size=args.batch_size)
            pipeline.evaluate_model()
            pipeline.run_backtest()

        # Train
        elif args.train:
            pipeline.collect_data()
            pipeline.preprocess_data(days_ahead=1)
            pipeline.prepare_sequences(seq_length=60, train_size=0.8)
            pipeline.train_model(epochs=args.epochs, batch_size=args.batch_size)
            pipeline.evaluate_model()

        # Predict
        elif args.predict:
            pipeline.collect_data()
            pipeline.preprocess_data(days_ahead=1)
            result = pipeline.predict_future()

        # Backtest
        elif args.backtest:
            pipeline.collect_data()
            pipeline.preprocess_data(days_ahead=1)
            pipeline.prepare_sequences(seq_length=60, train_size=0.8)

            # Опит да заредим съществуващ модел
            model_name = f'{args.ticker}_stock_model'
            try:
                pipeline.model = StockPredictionModel()
                pipeline.model.load_model(model_name)
                print(f"[OK] Зареден модел: {model_name}")
            except:
                print(f"[WARN] Модел {model_name} не е намерен. Тренираме нов...")
                pipeline.train_model(epochs=args.epochs, batch_size=args.batch_size)

            pipeline.run_backtest()

        else:
            print("[ERROR] Моля посочи --train, --predict, --backtest, --full или --web")
            parser.print_help()
            return

        print("\n" + "="*60)
        print("[OK] ЗАВЪРШЕНО УСПЕШНО!")
        print("="*60 + "\n")

    except KeyboardInterrupt:
        print("\n\n[WARN] Прекъснато от потребителя")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] ГРЕШКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
