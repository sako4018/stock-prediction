"""
Инициализация на src пакета
"""

__version__ = '1.0.0'
__author__ = 'Stock Prediction Team'

# Import основни класове за по-лесна употреба
from .data_collection import StockDataCollector
from .preprocessing import StockDataPreprocessor
from .model import StockPredictionModel
from .backtest import StockBacktester

__all__ = [
    'StockDataCollector',
    'StockDataPreprocessor',
    'StockPredictionModel',
    'StockBacktester'
]
