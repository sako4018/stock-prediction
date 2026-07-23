"""
Export Module
=============
Експортиране на данни и резултати в различни формати.

Функции:
- export_to_csv(): Експорт в CSV
- export_to_json(): Експорт в JSON
- generate_report(): Генериране на PDF отчет
"""

import pandas as pd
import json
import os
from datetime import datetime


def export_to_csv(data, filename, directory=None):
    """
    Експортира данни в CSV файл.

    Параметри:
    ----------
    data : dict или pandas.DataFrame
        Данни за експортиране
    filename : str
        Име на файла (без разширение)
    directory : str, optional
        Директория за запазване

    Връща:
    -------
    str
        Път до записания файл
    """
    if directory is None:
        directory = os.path.join(os.path.dirname(__file__), '..', 'exports')
    os.makedirs(directory, exist_ok=True)

    if isinstance(data, dict):
        df = pd.DataFrame(data)
    else:
        df = data

    filepath = os.path.join(directory, f'{filename}.csv')
    df.to_csv(filepath, index=False)
    print(f"📄 CSV записан: {filepath}")
    return filepath


def export_to_json(data, filename, directory=None):
    """
    Експортира данни в JSON файл.
    """
    if directory is None:
        directory = os.path.join(os.path.dirname(__file__), '..', 'exports')
    os.makedirs(directory, exist_ok=True)

    filepath = os.path.join(directory, f'{filename}.json')

    # Конвертиране на не-serializable данни
    def default_serializer(obj):
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        if hasattr(obj, 'item'):
            return obj.item()
        return str(obj)

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=default_serializer)

    print(f"📄 JSON записан: {filepath}")
    return filepath


def generate_report(ticker, predictions, signals, backtest_results, export_dir=None):
    """
    Генериране на обобщен отчет.
    """
    if export_dir is None:
        export_dir = os.path.join(os.path.dirname(__file__), '..', 'exports')
    os.makedirs(export_dir, exist_ok=True)

    report = {
        'ticker': ticker,
        'generated_at': datetime.now().isoformat(),
        'prediction': predictions,
        'signals': signals,
        'backtest': {
            'total_return': backtest_results.get('total_return'),
            'win_rate': backtest_results.get('win_rate'),
            'sharpe_ratio': backtest_results.get('sharpe_ratio'),
            'max_drawdown': backtest_results.get('max_drawdown'),
            'total_trades': backtest_results.get('total_trades')
        }
    }

    filepath = export_to_json(report, f'{ticker}_report', export_dir)
    return filepath


def export_signals_history(ticker, signals_data, directory=None):
    """
    Експортира история от сигнали в CSV.
    """
    if directory is None:
        directory = os.path.join(os.path.dirname(__file__), '..', 'exports')
    os.makedirs(directory, exist_ok=True)

    filepath = os.path.join(directory, f'{ticker}_signals.csv')

    if isinstance(signals_data, list):
        df = pd.DataFrame(signals_data)
    else:
        df = pd.DataFrame([signals_data])

    df.to_csv(filepath, index=False)
    print(f"[INFO] Signals CSV записан: {filepath}")
    return filepath
