"""
Batch Training Module
=====================
Тренира модели за множество акции едновременно.

Функции:
- train_batch(): Тренира модели за списък от акции
- train_sector(): Тренира модели за всички акции в сектор
- get_training_status(): Статус на тренировката
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from data_collection import StockDataCollector
from preprocessing import StockDataPreprocessor
from model import StockPredictionModel


class BatchTrainer:
    """
    Batch тренировка на модели за множество акции.
    """

    def __init__(self):
        self.models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        self.status_file = os.path.join(self.models_dir, 'training_status.json')
        os.makedirs(self.models_dir, exist_ok=True)

    def get_training_status(self) -> Dict:
        """Връща статуса на тренировката."""
        if os.path.exists(self.status_file):
            with open(self.status_file, 'r') as f:
                return json.load(f)
        return {'running': False, 'progress': {}, 'last_run': None}

    def _save_status(self, status: Dict):
        """Записва статуса."""
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)

    def train_single(self, ticker: str, period: str = '2y', epochs: int = 50) -> Dict:
        """
        Тренира модел за една акция.

        Връща:
        -------
        Dict
            Резултат от тренировката
        """
        try:
            # Събиране на данни
            collector = StockDataCollector(ticker=ticker, period=period, interval='1d')
            data = collector.fetch_stock_data(save_to_csv=False)

            if data is None or len(data) < 100:
                return {'ticker': ticker, 'status': 'error', 'message': 'Insufficient data'}

            # Обработка
            preprocessor = StockDataPreprocessor(data)
            preprocessor.calculate_technical_indicators()
            preprocessor.create_target_variable(days_ahead=1)
            preprocessor.normalize_data()

            scaled_data = preprocessor.scaled_data
            feature_cols = [col for col in scaled_data.columns if col not in ['Date']]
            model_data = scaled_data[feature_cols].values

            if len(model_data) < 80:
                return {'ticker': ticker, 'status': 'error', 'message': 'Not enough data after preprocessing'}

            # Подготовка на последователности
            X, y = preprocessor.create_sequences(model_data, seq_length=60)

            if len(X) < 20:
                return {'ticker': ticker, 'status': 'error', 'message': 'Not enough sequences'}

            split_idx = int(len(X) * 0.9)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            # Трениране
            model = StockPredictionModel(
                sequence_length=X.shape[1],
                n_features=X.shape[2]
            )
            model.build_lstm_model(lstm_units=[128, 64, 32], dropout_rate=0.2)

            history = model.train_model(
                X_train, y_train, X_val, y_val,
                epochs=epochs, batch_size=32
            )

            # Оценка
            metrics = model.evaluate(X_val, y_val)

            # Запазване
            model_name = f'{ticker}_stock_model'
            model.save_model(model_name)

            return {
                'ticker': ticker,
                'status': 'success',
                'features': len(feature_cols),
                'data_points': len(data),
                'train_samples': len(X_train),
                'val_samples': len(X_val),
                'val_accuracy': metrics.get('Direction_Accuracy', 0),
                'train_loss': history['train_loss'][-1] if history['train_loss'] else 0,
                'val_loss': history['val_loss'][-1] if history['val_loss'] else 0,
                'model_saved': model_name
            }

        except Exception as e:
            return {'ticker': ticker, 'status': 'error', 'message': str(e)}

    def train_batch(self, tickers: List[str], period: str = '2y', epochs: int = 50) -> Dict:
        """
        Тренира модели за списък от акции.

        Параметри:
        ----------
        tickers : List[str]
            Списък с тикери
        period : str
            Период на данните
        epochs : int
            Брой епохи

        Връща:
        -------
        Dict
            Резултати от batch тренировката
        """
        status = {
            'running': True,
            'started_at': datetime.now().isoformat(),
            'total': len(tickers),
            'completed': 0,
            'successful': 0,
            'failed': 0,
            'progress': {}
        }
        self._save_status(status)

        results = []

        for i, ticker in enumerate(tickers):
            print(f"[{i+1}/{len(tickers)}] Training {ticker}...")

            status['progress'][ticker] = 'training'
            self._save_status(status)

            result = self.train_single(ticker, period, epochs)
            results.append(result)

            if result['status'] == 'success':
                status['successful'] += 1
                status['progress'][ticker] = f"done ({result['val_accuracy']:.1f}%)"
            else:
                status['failed'] += 1
                status['progress'][ticker] = f"error: {result.get('message', 'unknown')}"

            status['completed'] = i + 1
            self._save_status(status)

        status['running'] = False
        status['finished_at'] = datetime.now().isoformat()
        self._save_status(status)

        return {
            'total': len(tickers),
            'successful': status['successful'],
            'failed': status['failed'],
            'results': results
        }

    def train_sector(self, sector: str, period: str = '2y', epochs: int = 50) -> Dict:
        """
        Тренира модели за всички акции в сектор.
        """
        from sector_analysis import get_sector_stocks
        tickers = get_sector_stocks(sector)
        if not tickers:
            return {'error': f'Sector "{sector}" not found'}
        return self.train_batch(tickers, period, epochs)

    def get_trained_models(self) -> List[Dict]:
        """Връща списък с тренирани модели."""
        models = []
        for f in os.listdir(self.models_dir):
            if f.endswith('_config.json'):
                ticker = f.replace('_stock_model_config.json', '').replace('_config.json', '')
                config_path = os.path.join(self.models_dir, f)
                with open(config_path, 'r') as fh:
                    config = json.load(fh)

                # Check if model file exists
                model_path = os.path.join(self.models_dir, f'{ticker}_stock_model.pt')
                exists = os.path.exists(model_path)

                models.append({
                    'ticker': ticker,
                    'has_model': exists,
                    'architecture': config.get('architecture', 'lstm_attention_v2'),
                    'n_features': config.get('n_features', 0),
                    'sequence_length': config.get('sequence_length', 60)
                })

        return models
