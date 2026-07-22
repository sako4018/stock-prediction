"""
Combined Signal Module (v2 — Majority Vote)
============================================
5 гласоподаватели решават: UP или DOWN?

1. ML Model    — предсказана цена vs текуща
2. RSI         — oversold (<40) → UP, overbought (>60) → DOWN
3. MACD        — MACD > signal → UP,反之 → DOWN
4. Price Trend — цена > 20 SMA → UP,反之 → DOWN
5. Sentiment   — bullish → UP, bearish → DOWN

Решение: мнозинството печели. Ако няма ясен победител → UNCERTAIN.
"""

from typing import Dict, Optional


def _ml_voter(ml_prediction: float, current_price: float) -> str:
    """
    ML моделът предсказва нормализирана цена (0-1).
    Ако предсказаната стойност > 0.5 → цената ще се качи.
    """
    if ml_prediction > 0.55:
        return 'UP'
    elif ml_prediction < 0.45:
        return 'DOWN'
    return 'NEUTRAL'


def _rsi_voter(rsi_value: float) -> str:
    """
    RSI логика:
    - < 35 → премалък (oversold) → ще се качи
    - > 65 → премного (overbought) → ще спадне
    - Между 35-65 → неутрален
    """
    if rsi_value < 35:
        return 'UP'
    elif rsi_value > 65:
        return 'DOWN'
    return 'NEUTRAL'


def _macd_voter(macd: float, macd_signal: float) -> str:
    """
    MACD логика:
    - MACD > signal line → bullish momentum → UP
    - MACD < signal line → bearish momentum → DOWN
    """
    if macd > macd_signal:
        return 'UP'
    elif macd < macd_signal:
        return 'DOWN'
    return 'NEUTRAL'


def _trend_voter(current_price: float, sma_20: float) -> str:
    """
    Price trend логика:
    - Цена > 20-дневна SMA → uptrend → UP
    - Цена < 20-дневна SMA → downtrend → DOWN
    """
    if sma_20 == 0:
        return 'NEUTRAL'
    pct_diff = (current_price - sma_20) / sma_20
    if pct_diff > 0.01:  # >1% над SMA
        return 'UP'
    elif pct_diff < -0.01:  # >1% под SMA
        return 'DOWN'
    return 'NEUTRAL'


def _sentiment_voter(sentiment_data: Dict) -> str:
    """
    Sentiment логика:
    - bullish score > 0.15 → UP
    - bearish score < -0.15 → DOWN
    - иначе → NEUTRAL
    """
    score = sentiment_data.get('score', 0)
    if score > 0.15:
        return 'UP'
    elif score < -0.15:
        return 'DOWN'
    return 'NEUTRAL'


def combine_signals(
    ml_prediction: float,
    current_price: float,
    indicators: Dict,
    sentiment_data: Dict,
    model_metrics: Dict = None
) -> Dict:
    """
    5 гласоподаватели решават посоката.

    Връща:
    -------
    Dict
        direction: 'UP' | 'DOWN' | 'UNCERTAIN'
        confidence: 0-100
        voters: { ml, rsi, macd, trend, sentiment }
        summary: кратко описание
    """

    # 1. ML глас
    ml_vote = _ml_voter(ml_prediction, current_price)

    # 2. RSI глас
    rsi_val = indicators.get('rsi', 50)
    rsi_vote = _rsi_voter(rsi_val)

    # 3. MACD глас
    macd_val = indicators.get('macd', 0)
    macd_signal = indicators.get('macd_signal', 0)
    macd_vote = _macd_voter(macd_val, macd_signal)

    # 4. Trend глас
    sma_20 = indicators.get('sma_20', current_price)
    trend_vote = _trend_voter(current_price, sma_20)

    # 5. Sentiment глас
    sent_vote = _sentiment_voter(sentiment_data)

    # Събиране на гласовете
    voters = {
        'ml': {'vote': ml_vote, 'label': 'ML Model'},
        'rsi': {'vote': rsi_vote, 'label': 'RSI'},
        'macd': {'vote': macd_vote, 'label': 'MACD'},
        'trend': {'vote': trend_vote, 'label': 'Price Trend'},
        'sentiment': {'vote': sent_vote, 'label': 'Sentiment'},
    }

    # Броене
    up_votes = sum(1 for v in voters.values() if v['vote'] == 'UP')
    down_votes = sum(1 for v in voters.values() if v['vote'] == 'DOWN')
    neutral_votes = sum(1 for v in voters.values() if v['vote'] == 'NEUTRAL')
    total_active = up_votes + down_votes

    # Решение
    if total_active == 0 or up_votes == down_votes:
        direction = 'UNCERTAIN'
        confidence = 0
        summary = 'Няма ясен сигнал — индикаторите не са единодушни.'
    elif up_votes > down_votes:
        direction = 'UP'
        confidence = round((up_votes / total_active) * 100)
        if up_votes >= 4:
            summary = 'Силен сигнал за покачване — почти всички индикатори са bullish.'
        elif up_votes >= 3:
            summary = 'Покачване е по-вероятно — мнозинството от индикаторите са bullish.'
        else:
            summary = 'Слабо покачване — само 2 от 5 индикатора са bullish.'
    else:
        direction = 'DOWN'
        confidence = round((down_votes / total_active) * 100)
        if down_votes >= 4:
            summary = 'Силен сигнал за спад — почти всички индикатори са bearish.'
        elif down_votes >= 3:
            summary = 'Спад е по-вероятен — мнозинството от индикаторите са bearish.'
        else:
            summary = 'Слаб спад — само 2 от 5 индикатора са bearish.'

    return {
        'direction': direction,
        'confidence': confidence,
        'voters': voters,
        'up_votes': up_votes,
        'down_votes': down_votes,
        'neutral_votes': neutral_votes,
        'summary': summary,
    }
