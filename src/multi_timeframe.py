"""
Multi-Timeframe Analysis Module
===============================
Комбинира сигнали от различни времеви периоди (daily + weekly + monthly)
за по-надежни предсказания.

Логика: Ако daily и weekly сигнализират BUY, confidence-а е по-висок.
Ако си противоречат, confidence-а намалява.
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from data_collection import StockDataCollector
from preprocessing import StockDataPreprocessor


def calculate_timeframe_signals(data: pd.DataFrame) -> Dict:
    """
    Изчислява сигнали за един timeframe.

    Връща:
    -------
    Dict
        signal, confidence, indicators
    """
    if data is None or len(data) < 30:
        return {'signal': 'NEUTRAL', 'confidence': 0, 'indicators': {}}

    preprocessor = StockDataPreprocessor(data)
    df = preprocessor.calculate_technical_indicators()

    buy_score = 0
    sell_score = 0
    indicators = {}

    # RSI
    rsi = df['RSI'].iloc[-1]
    indicators['rsi'] = float(rsi)
    if rsi < 30: buy_score += 2
    elif rsi < 40: buy_score += 1
    elif rsi > 70: sell_score += 2
    elif rsi > 60: sell_score += 1

    # MACD
    macd = df['MACD'].iloc[-1]
    macd_signal = df['MACD_Signal'].iloc[-1]
    indicators['macd'] = float(macd)
    if macd > macd_signal: buy_score += 1
    else: sell_score += 1

    # Stochastic
    stoch_k = df['Stoch_K'].iloc[-1]
    indicators['stoch_k'] = float(stoch_k)
    if stoch_k < 20: buy_score += 2
    elif stoch_k < 30: buy_score += 1
    elif stoch_k > 80: sell_score += 2
    elif stoch_k > 70: sell_score += 1

    # ADX (trend strength)
    if 'ADX' in df.columns:
        adx = df['ADX'].iloc[-1]
        indicators['adx'] = float(adx)
    else:
        indicators['adx'] = 0

    # Price vs MAs
    close = df['Close'].iloc[-1]
    sma20 = df['SMA_20'].iloc[-1]
    sma50 = df['SMA_50'].iloc[-1]
    indicators['price_vs_sma20'] = float((close / sma20 - 1) * 100)
    indicators['price_vs_sma50'] = float((close / sma50 - 1) * 100)

    if close > sma20 > sma50: buy_score += 2  # Uptrend
    elif close < sma20 < sma50: sell_score += 2  # Downtrend
    elif close > sma20: buy_score += 1
    elif close < sma20: sell_score += 1

    # Bollinger Band position
    bb_upper = df['BB_Upper'].iloc[-1]
    bb_lower = df['BB_Lower'].iloc[-1]
    bb_position = (close - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
    indicators['bb_position'] = float(bb_position)

    # Determine signal
    total = buy_score + sell_score
    if total == 0:
        return {'signal': 'NEUTRAL', 'confidence': 0, 'indicators': indicators}

    if buy_score > sell_score:
        signal = 'BUY'
        confidence = (buy_score / total) * 100
    elif sell_score > buy_score:
        signal = 'SELL'
        confidence = (sell_score / total) * 100
    else:
        signal = 'NEUTRAL'
        confidence = 0

    indicators['buy_score'] = buy_score
    indicators['sell_score'] = sell_score

    return {
        'signal': signal,
        'confidence': round(confidence, 1),
        'indicators': indicators
    }


def multi_timeframe_analysis(ticker: str) -> Dict:
    """
    Комбинира daily, weekly и monthly сигнали.

    Логика:
    - Daily: краткосрочен тренд (най-висок приоритет за timing)
    - Weekly: средносрочен тренд (потвърждение)
    - Monthly: дългосрочен тренд (контекст)

    Връща:
    -------
    Dict
        Combined signal с breakdown по timeframes
    """
    results = {}

    # Daily
    try:
        collector = StockDataCollector(ticker=ticker, period='6mo', interval='1d')
        daily_data = collector.fetch_stock_data(save_to_csv=False)
        results['daily'] = calculate_timeframe_signals(daily_data)
        results['daily']['period'] = '6 months'
    except Exception as e:
        results['daily'] = {'signal': 'NEUTRAL', 'confidence': 0, 'indicators': {}, 'error': str(e)}

    # Weekly
    try:
        collector_w = StockDataCollector(ticker=ticker, period='2y', interval='1wk')
        weekly_data = collector_w.fetch_stock_data(save_to_csv=False)
        results['weekly'] = calculate_timeframe_signals(weekly_data)
        results['weekly']['period'] = '2 years'
    except Exception as e:
        results['weekly'] = {'signal': 'NEUTRAL', 'confidence': 0, 'indicators': {}, 'error': str(e)}

    # Monthly
    try:
        collector_m = StockDataCollector(ticker=ticker, period='5y', interval='1mo')
        monthly_data = collector_m.fetch_stock_data(save_to_csv=False)
        results['monthly'] = calculate_timeframe_signals(monthly_data)
        results['monthly']['period'] = '5 years'
    except Exception as e:
        results['monthly'] = {'signal': 'NEUTRAL', 'confidence': 0, 'indicators': {}, 'error': str(e)}

    # Combine signals
    signals = [results['daily']['signal'], results['weekly']['signal'], results['monthly']['signal']]
    confidences = [results['daily']['confidence'], results['weekly']['confidence'], results['monthly']['confidence']]

    # Weight: daily=40%, weekly=35%, monthly=25%
    weights = [0.40, 0.35, 0.25]

    signal_scores = {'BUY': 1, 'SELL': -1, 'NEUTRAL': 0}
    weighted_score = sum(signal_scores.get(s, 0) * w for s, w in zip(signals, weights))

    # Count agreements
    buy_count = signals.count('BUY')
    sell_count = signals.count('SELL')

    if weighted_score > 0.2:
        if buy_count == 3:
            combined = 'STRONG BUY'
        else:
            combined = 'BUY'
    elif weighted_score < -0.2:
        if sell_count == 3:
            combined = 'STRONG SELL'
        else:
            combined = 'SELL'
    else:
        combined = 'HOLD'

    # Confidence from agreement
    agreement = max(buy_count, sell_count) / 3 * 100

    return {
        'ticker': ticker,
        'combined_signal': combined,
        'combined_confidence': round(agreement, 1),
        'timeframes': results,
        'agreement': f'{buy_count}B/{sell_count}S/{3-buy_count-sell_count}N'
    }
