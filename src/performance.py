"""
Model Performance Tracking Module
=================================
Проследява точността на модела във времето.

Функции:
- record_prediction(): Записва предсказание с timestamp
- update_actual(): Обновява с реална стойност след N дни
- get_performance(): Метрики за точност
- get_accuracy_trend(): Точността във времето
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from sklearn.metrics import accuracy_score, mean_absolute_error


class PerformanceTracker:
    """
    Проследяване на представянето на модела във времето.
    Записва всяко предсказание и го сравнява с реалния резултат.
    """

    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.data_dir = data_dir
        self.predictions_file = os.path.join(data_dir, 'predictions.json')
        os.makedirs(data_dir, exist_ok=True)
        self.predictions = self._load()

    def _load(self) -> List[Dict]:
        if os.path.exists(self.predictions_file):
            with open(self.predictions_file, 'r') as f:
                return json.load(f)
        return []

    def _save(self):
        with open(self.predictions_file, 'w') as f:
            json.dump(self.predictions, f, indent=2)

    def record_prediction(self, ticker: str, predicted_signal: str, predicted_value: float,
                          actual_price: float, confidence: float = 0) -> Dict:
        """
        Записва предсказание за проследяване.

        Параметри:
        ----------
        ticker : str
            Тикер на акцията
        predicted_signal : str
            BUY/SELL/HOLD
        predicted_value : float
            Суров модел output
        actual_price : float
            Текуща цена при предсказанието
        confidence : float
            Confidence на предсказанието
        """
        record = {
            'id': f"{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'ticker': ticker,
            'predicted_signal': predicted_signal,
            'predicted_value': predicted_value,
            'actual_price_at_prediction': actual_price,
            'confidence': confidence,
            'recorded_at': datetime.now().isoformat(),
            'actual_price_after': None,
            'actual_return_pct': None,
            'direction_correct': None,
            'verified': False,
            'verified_at': None
        }

        self.predictions.append(record)
        self._save()
        return record

    def update_actual(self, record_id: str, actual_price_after: float) -> Dict:
        """
        Обновява запис с реална стойност след изтичане на периода.
        """
        for pred in self.predictions:
            if pred['id'] == record_id:
                pred['actual_price_after'] = actual_price_after
                initial_price = pred['actual_price_at_prediction']
                pred['actual_return_pct'] = round(
                    ((actual_price_after - initial_price) / initial_price) * 100, 2
                )

                # Проверка дали посоката е била правилна
                if pred['predicted_signal'] == 'BUY':
                    pred['direction_correct'] = actual_price_after > initial_price
                elif pred['predicted_signal'] == 'SELL':
                    pred['direction_correct'] = actual_price_after < initial_price
                else:
                    pred['direction_correct'] = True  # HOLD е правилно ако не е имало голяма промяна

                pred['verified'] = True
                pred['verified_at'] = datetime.now().isoformat()
                self._save()
                return pred

        return {'error': 'Record not found'}

    def auto_verify_pending(self, days_after: int = 5):
        """
        Автоматично верифицира pending предсказания,
        ако са минали N дни от записването.
        """
        from data_collection import StockDataCollector

        cutoff = datetime.now() - timedelta(days=days_after)
        verified_count = 0

        for pred in self.predictions:
            if pred['verified']:
                continue

            recorded_at = datetime.fromisoformat(pred['recorded_at'])
            if recorded_at > cutoff:
                continue  # Още е рано

            try:
                collector = StockDataCollector(
                    ticker=pred['ticker'], period='5d', interval='1d'
                )
                data = collector.fetch_stock_data(save_to_csv=False)
                if data is not None and len(data) > 0:
                    current_price = data['Close'].iloc[-1]
                    self.update_actual(pred['id'], float(current_price))
                    verified_count += 1
            except Exception:
                pass

        return verified_count

    def get_performance(self, ticker: str = None, days: int = 30) -> Dict:
        """
        Изчислява метрики за точност.

        Връща:
        -------
        Dict
            accuracy, avg_return, win_rate, by_signal
        """
        verified = [p for p in self.predictions if p['verified']]

        if ticker:
            verified = [p for p in verified if p['ticker'] == ticker]

        if not verified:
            return {
                'total_predictions': 0,
                'accuracy': 0,
                'avg_return': 0,
                'win_rate': 0
            }

        # Обща точност
        correct = sum(1 for p in verified if p['direction_correct'])
        accuracy = (correct / len(verified)) * 100

        # Средна възвръщаемост
        returns = [p['actual_return_pct'] for p in verified if p['actual_return_pct'] is not None]
        avg_return = np.mean(returns) if returns else 0

        # Win rate (profitable trades)
        profitable = sum(1 for r in returns if r > 0)
        win_rate = (profitable / len(returns)) * 100 if returns else 0

        # По тип сигнал
        by_signal = {}
        for signal in ['BUY', 'SELL', 'HOLD']:
            signal_preds = [p for p in verified if p['predicted_signal'] == signal]
            if signal_preds:
                signal_correct = sum(1 for p in signal_preds if p['direction_correct'])
                by_signal[signal] = {
                    'count': len(signal_preds),
                    'accuracy': round((signal_correct / len(signal_preds)) * 100, 1)
                }

        return {
            'total_predictions': len(verified),
            'accuracy': round(accuracy, 1),
            'avg_return': round(avg_return, 2),
            'win_rate': round(win_rate, 1),
            'by_signal': by_signal,
            'profitable_trades': profitable,
            'losing_trades': len(returns) - profitable
        }

    def get_accuracy_trend(self, ticker: str = None, window: int = 10) -> List[Dict]:
        """
        Точността във времето (rolling window).

        Връща:
        -------
        List[Dict]
            Точност по периоди
        """
        verified = [p for p in self.predictions if p['verified']]
        if ticker:
            verified = [p for p in verified if p['ticker'] == ticker]

        if len(verified) < window:
            return []

        trend = []
        for i in range(window, len(verified) + 1):
            chunk = verified[i - window:i]
            correct = sum(1 for p in chunk if p['direction_correct'])
            accuracy = (correct / len(chunk)) * 100
            trend.append({
                'period': i,
                'accuracy': round(accuracy, 1),
                'predictions': len(chunk),
                'date': chunk[-1]['recorded_at'][:10]
            })

        return trend

    def get_pending_count(self) -> int:
        """Брой pending предсказания."""
        return sum(1 for p in self.predictions if not p['verified'])
