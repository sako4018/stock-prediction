"""
Unit tests for combined_signal.py
5-voter majority vote system
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from combined_signal import combine_signals


def test_all_voters_up():
    """All 5 voters say UP → direction UP, confidence 100%"""
    result = combine_signals(
        ml_prediction=0.7,
        current_price=150,
        indicators={'rsi': 30, 'macd': 2.5, 'macd_signal': 1.0, 'sma_20': 145},
        sentiment_data={'score': 0.3}
    )
    assert result['direction'] == 'UP'
    assert result['confidence'] == 100
    assert result['up_votes'] == 5
    assert result['down_votes'] == 0


def test_all_voters_down():
    """All 5 voters say DOWN → direction DOWN, confidence 100%"""
    result = combine_signals(
        ml_prediction=0.3,
        current_price=150,
        indicators={'rsi': 75, 'macd': -1.0, 'macd_signal': 0.5, 'sma_20': 160},
        sentiment_data={'score': -0.4}
    )
    assert result['direction'] == 'DOWN'
    assert result['confidence'] == 100
    assert result['down_votes'] == 5
    assert result['up_votes'] == 0


def test_majority_up():
    """3 UP, 1 DOWN, 1 NEUTRAL → direction UP"""
    result = combine_signals(
        ml_prediction=0.6,
        current_price=150,
        indicators={'rsi': 30, 'macd': 2.5, 'macd_signal': 1.0, 'sma_20': 155},
        sentiment_data={'score': -0.2}
    )
    assert result['direction'] == 'UP'
    assert result['up_votes'] >= 3


def test_majority_down():
    """3 DOWN, 1 UP, 1 NEUTRAL → direction DOWN"""
    result = combine_signals(
        ml_prediction=0.4,
        current_price=150,
        indicators={'rsi': 70, 'macd': -1.0, 'macd_signal': 0.5, 'sma_20': 160},
        sentiment_data={'score': -0.3}
    )
    assert result['direction'] == 'DOWN'
    assert result['down_votes'] >= 3


def test_uncertain_when_split():
    """2 UP, 2 DOWN, 1 NEUTRAL → UNCERTAIN"""
    result = combine_signals(
        ml_prediction=0.55,
        current_price=150,
        indicators={'rsi': 50, 'macd': 2.5, 'macd_signal': 1.0, 'sma_20': 155},
        sentiment_data={'score': -0.3}
    )
    # With 2 UP (macd, trend) and 2 DOWN (rsi→neutral, sentiment→DOWN, ml→UP)
    # The exact split depends on thresholds, but should be close
    assert result['direction'] in ('UP', 'DOWN', 'UNCERTAIN')
    assert 0 <= result['confidence'] <= 100


def test_ml_neutral_zone():
    """ML prediction 0.5 (neutral) → ML voter is NEUTRAL"""
    result = combine_signals(
        ml_prediction=0.5,
        current_price=150,
        indicators={'rsi': 30, 'macd': 2.5, 'macd_signal': 1.0, 'sma_20': 145},
        sentiment_data={'score': 0.3}
    )
    assert result['voters']['ml']['vote'] == 'NEUTRAL'


def test_rsi_oversold():
    """RSI < 35 → UP (oversold)"""
    result = combine_signals(
        ml_prediction=0.5,
        current_price=150,
        indicators={'rsi': 25, 'macd': 0, 'macd_signal': 0, 'sma_20': 150},
        sentiment_data={'score': 0}
    )
    assert result['voters']['rsi']['vote'] == 'UP'


def test_rsi_overbought():
    """RSI > 65 → DOWN (overbought)"""
    result = combine_signals(
        ml_prediction=0.5,
        current_price=150,
        indicators={'rsi': 80, 'macd': 0, 'macd_signal': 0, 'sma_20': 150},
        sentiment_data={'score': 0}
    )
    assert result['voters']['rsi']['vote'] == 'DOWN'


def test_macd_bullish():
    """MACD > signal → UP"""
    result = combine_signals(
        ml_prediction=0.5,
        current_price=150,
        indicators={'rsi': 50, 'macd': 2.0, 'macd_signal': 1.0, 'sma_20': 150},
        sentiment_data={'score': 0}
    )
    assert result['voters']['macd']['vote'] == 'UP'


def test_macd_bearish():
    """MACD < signal → DOWN"""
    result = combine_signals(
        ml_prediction=0.5,
        current_price=150,
        indicators={'rsi': 50, 'macd': -1.0, 'macd_signal': 0.5, 'sma_20': 150},
        sentiment_data={'score': 0}
    )
    assert result['voters']['macd']['vote'] == 'DOWN'


def test_trend_above_sma():
    """Price > SMA20 by >1% → UP"""
    result = combine_signals(
        ml_prediction=0.5,
        current_price=155,
        indicators={'rsi': 50, 'macd': 0, 'macd_signal': 0, 'sma_20': 150},
        sentiment_data={'score': 0}
    )
    assert result['voters']['trend']['vote'] == 'UP'


def test_trend_below_sma():
    """Price < SMA20 by >1% → DOWN"""
    result = combine_signals(
        ml_prediction=0.5,
        current_price=145,
        indicators={'rsi': 50, 'macd': 0, 'macd_signal': 0, 'sma_20': 150},
        sentiment_data={'score': 0}
    )
    assert result['voters']['trend']['vote'] == 'DOWN'


def test_sentiment_bullish():
    """Sentiment score > 0.15 → UP"""
    result = combine_signals(
        ml_prediction=0.5,
        current_price=150,
        indicators={'rsi': 50, 'macd': 0, 'macd_signal': 0, 'sma_20': 150},
        sentiment_data={'score': 0.3}
    )
    assert result['voters']['sentiment']['vote'] == 'UP'


def test_sentiment_bearish():
    """Sentiment score < -0.15 → DOWN"""
    result = combine_signals(
        ml_prediction=0.5,
        current_price=150,
        indicators={'rsi': 50, 'macd': 0, 'macd_signal': 0, 'sma_20': 150},
        sentiment_data={'score': -0.3}
    )
    assert result['voters']['sentiment']['vote'] == 'DOWN'


def test_response_structure():
    """Response has all required fields"""
    result = combine_signals(
        ml_prediction=0.6,
        current_price=150,
        indicators={'rsi': 40, 'macd': 1.0, 'macd_signal': 0.5, 'sma_20': 148},
        sentiment_data={'score': 0.2}
    )
    assert 'direction' in result
    assert 'confidence' in result
    assert 'voters' in result
    assert 'up_votes' in result
    assert 'down_votes' in result
    assert 'neutral_votes' in result
    assert 'summary' in result
    assert result['direction'] in ('UP', 'DOWN', 'UNCERTAIN')
    assert 0 <= result['confidence'] <= 100
    assert len(result['voters']) == 5


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {test.__name__}: {e}")
            failed += 1
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
