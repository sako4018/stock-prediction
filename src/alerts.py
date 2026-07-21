"""
Alert System Module
===================
Проследяване на персонални алерти за акции.

Типове алерти:
- Price Above/Below: цената премине определено ниво
- Price Change %: промяна в цената над определен %
- RSI Above/Below: RSI премине ниво
- Crosses MA: цената премине moving average

Съхранение: JSON файл в data/alerts.json
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import yfinance as yf


class AlertManager:
    """
    Мениджър за персонални алерти.
    """

    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.data_dir = data_dir
        self.alerts_file = os.path.join(data_dir, 'alerts.json')
        self.alerts = self._load()

    def _load(self) -> List[Dict]:
        """Зарежда алертите от файл."""
        if os.path.exists(self.alerts_file):
            with open(self.alerts_file, 'r') as f:
                return json.load(f)
        return []

    def _save(self):
        """Записва алертите в файл."""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.alerts_file, 'w') as f:
            json.dump(self.alerts, f, indent=2)

    def add_alert(self, ticker: str, alert_type: str, condition: str, value: float, note: str = '') -> Dict:
        """
        Добавя нов алерт.

        Параметри:
        ----------
        ticker : str
            Тикер на акцията
        alert_type : str
            Тип: 'price_above', 'price_below', 'price_change_pct', 'rsi_above', 'rsi_below'
        condition : str
            Описание на условието
        value : float
            Стойност за сравнение
        note : str
            Бележка

        Връща:
        -------
        Dict
            Създаденият алерт
        """
        alert = {
            'id': str(uuid.uuid4())[:8],
            'ticker': ticker.upper(),
            'alert_type': alert_type,
            'condition': condition,
            'value': value,
            'note': note,
            'active': True,
            'triggered': False,
            'triggered_at': None,
            'triggered_value': None,
            'created_at': datetime.now().isoformat()
        }

        self.alerts.append(alert)
        self._save()
        return alert

    def remove_alert(self, alert_id: str) -> bool:
        """Премахва алерт по ID."""
        for i, alert in enumerate(self.alerts):
            if alert['id'] == alert_id:
                self.alerts.pop(i)
                self._save()
                return True
        return False

    def get_alerts(self, ticker: str = None, active_only: bool = True) -> List[Dict]:
        """Връща алерти, филтрирани по ticker и/или статус."""
        result = self.alerts
        if ticker:
            result = [a for a in result if a['ticker'] == ticker.upper()]
        if active_only:
            result = [a for a in result if a['active'] and not a['triggered']]
        return result

    def check_alerts(self) -> List[Dict]:
        """
        Проверява всички активни алерти и връща trigger-натите.

        Връща:
        -------
        List[Dict]
            Списък с trigger-нати алерти
        """
        triggered = []

        # Групираме по ticker за по-малко API заявки
        active_tickers = set(a['ticker'] for a in self.alerts if a['active'] and not a['triggered'])

        for ticker in active_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))

                if not current_price:
                    continue

                # RSI за RSI алерти
                rsi = None
                has_rsi_alerts = any(
                    a['ticker'] == ticker and a['active'] and not a['triggered'] and 'rsi' in a['alert_type']
                    for a in self.alerts
                )

                if has_rsi_alerts:
                    hist = stock.history(period='1mo', interval='1d')
                    if len(hist) >= 14:
                        delta = hist['Close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        rsi = float((100 - (100 / (1 + rs))).iloc[-1])

                for alert in self.alerts:
                    if alert['ticker'] != ticker or not alert['active'] or alert['triggered']:
                        continue

                    triggered_now = False
                    triggered_value = None

                    if alert['alert_type'] == 'price_above' and current_price > alert['value']:
                        triggered_now = True
                        triggered_value = current_price

                    elif alert['alert_type'] == 'price_below' and current_price < alert['value']:
                        triggered_now = True
                        triggered_value = current_price

                    elif alert['alert_type'] == 'rsi_above' and rsi is not None and rsi > alert['value']:
                        triggered_now = True
                        triggered_value = rsi

                    elif alert['alert_type'] == 'rsi_below' and rsi is not None and rsi < alert['value']:
                        triggered_now = True
                        triggered_value = rsi

                    if triggered_now:
                        alert['triggered'] = True
                        alert['triggered_at'] = datetime.now().isoformat()
                        alert['triggered_value'] = triggered_value
                        triggered.append(alert)

            except Exception as e:
                print(f"Warning: Could not check alerts for {ticker}: {e}")

        if triggered:
            self._save()

        return triggered

    def get_all_alerts(self) -> List[Dict]:
        """Връща всички алерти."""
        return self.alerts

    def get_stats(self) -> Dict:
        """Статистики за алертите."""
        total = len(self.alerts)
        active = sum(1 for a in self.alerts if a['active'] and not a['triggered'])
        triggered = sum(1 for a in self.alerts if a['triggered'])
        return {
            'total': total,
            'active': active,
            'triggered': triggered,
            'by_ticker': {}
        }
