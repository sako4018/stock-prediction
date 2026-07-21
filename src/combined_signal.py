"""
Combined Signal Module
======================
Комбинира ML предсказание, технически индикатори и news sentiment
в един финален сигнал.

Тегла:
- ML Model: 40%
- Technical Indicators: 35%
- News Sentiment: 25%
"""

from typing import Dict


# Тегла за комбиниране
WEIGHTS = {
    'ml': 0.40,
    'technical': 0.35,
    'sentiment': 0.25
}


def signal_to_score(signal: str) -> float:
    """
    Конвертира сигнал в числов score (-1 до 1).

    BUY / BULLISH / OVERSOLD → positive
    SELL / BEARISH / OVERBOUGHT → negative
    HOLD / NEUTRAL → 0
    """
    signal_upper = signal.upper()

    if 'STRONG BUY' in signal_upper:
        return 1.0
    elif 'BUY' in signal_upper or 'BULLISH' in signal_upper or 'OVERSOLD' in signal_upper:
        return 0.6
    elif 'STRONG SELL' in signal_upper:
        return -1.0
    elif 'SELL' in signal_upper or 'BEARISH' in signal_upper or 'OVERBOUGHT' in signal_upper:
        return -0.6
    else:
        return 0.0


def calculate_ml_confidence(prediction_value: float, model_metrics: Dict = None) -> float:
    """
    Изчислява confidence за ML модела.

    Подобрено: използва distance от 0.5 и model accuracy ако е налична.
    """
    # Distance from 0.5 (undecided point)
    distance = abs(prediction_value - 0.5)

    # Base confidence from prediction strength
    # prediction 0.5 = 0% confidence, prediction 0.0 or 1.0 = 100%
    base_confidence = distance * 2 * 100  # 0-100%

    # If we have model accuracy, boost confidence
    if model_metrics and 'accuracy' in model_metrics:
        model_accuracy = model_metrics['accuracy'] / 100
        base_confidence = base_confidence * 0.7 + (model_accuracy * 100) * 0.3

    return min(max(base_confidence, 5), 95)  # Clamp 5-95%


def combine_signals(
    ml_signal: str,
    ml_prediction: float,
    technical_signal: str,
    sentiment_data: Dict,
    model_metrics: Dict = None
) -> Dict:
    """
    Комбинира всички сигнали в един финален резултат.

    Параметри:
    ----------
    ml_signal : str
        Сигнал от ML модела (BUY/SELL/HOLD)
    ml_prediction : float
        Суров output от модела (0-1)
    technical_signal : str
        Сигнал от технически индикатори
    sentiment_data : Dict
        Данни от news sentiment analysis
    model_metrics : Dict, optional
        Метрики от модела (accuracy и т.н.)

    Връща:
    -------
    Dict
        Финален сигнал с breakdown
    """

    # 1. ML Score
    ml_score = signal_to_score(ml_signal)
    ml_confidence = calculate_ml_confidence(ml_prediction, model_metrics)

    # 2. Technical Score
    tech_score = signal_to_score(technical_signal)
    tech_confidence = 70  # Technical indicators обикновено са ~70% сигурни

    # 3. Sentiment Score
    sent_score = sentiment_data.get('score', 0)
    sent_confidence = sentiment_data.get('confidence', 0)
    sent_label = sentiment_data.get('overall', 'neutral')

    # Weighted combination
    combined_score = (
        ml_score * WEIGHTS['ml'] +
        tech_score * WEIGHTS['technical'] +
        sent_score * WEIGHTS['sentiment']
    )

    # Combined confidence (weighted average)
    combined_confidence = (
        ml_confidence * WEIGHTS['ml'] +
        tech_confidence * WEIGHTS['technical'] +
        sent_confidence * WEIGHTS['sentiment']
    )

    # Boost confidence if all signals agree
    signals = [ml_score, tech_score, sent_score]
    all_positive = all(s > 0 for s in signals if s != 0)
    all_negative = all(s < 0 for s in signals if s != 0)

    if all_positive or all_negative:
        combined_confidence = min(combined_confidence * 1.2, 95)

    # Determine final signal
    if combined_score > 0.15:
        if combined_score > 0.4:
            final_signal = 'STRONG BUY'
        else:
            final_signal = 'BUY'
    elif combined_score < -0.15:
        if combined_score < -0.4:
            final_signal = 'STRONG SELL'
        else:
            final_signal = 'SELL'
    else:
        final_signal = 'HOLD'

    return {
        'final_signal': final_signal,
        'final_score': round(combined_score, 3),
        'final_confidence': round(combined_confidence, 1),

        'breakdown': {
            'ml': {
                'signal': ml_signal,
                'score': round(ml_score, 3),
                'confidence': round(ml_confidence, 1),
                'weight': WEIGHTS['ml'],
                'raw_prediction': round(ml_prediction, 4)
            },
            'technical': {
                'signal': technical_signal,
                'score': round(tech_score, 3),
                'confidence': round(tech_confidence, 1),
                'weight': WEIGHTS['technical']
            },
            'sentiment': {
                'signal': sent_label.upper(),
                'score': round(sent_score, 3),
                'confidence': round(sent_confidence, 1),
                'weight': WEIGHTS['sentiment'],
                'article_count': sentiment_data.get('article_count', 0),
                'bullish': sentiment_data.get('bullish_count', 0),
                'bearish': sentiment_data.get('bearish_count', 0),
                'neutral': sentiment_data.get('neutral_count', 0)
            }
        },

        'agreement': 'all_agree' if (all_positive or all_negative) else 'mixed'
    }
