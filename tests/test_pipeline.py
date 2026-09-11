"""
Проверки на ML pipeline-а.

Най-важният тест е test_random_data_gives_no_edge: върху чист random walk
няма какво да се научи, затова точността трябва да е около 50%. Ако някога
даде 90%, значи някъде е влязло изтичане на данни (leakage).

Стартиране:
    python tests/test_pipeline.py
"""

import os
import sys
import io
import contextlib

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from preprocessing import StockDataPreprocessor, TARGET_COLUMNS
from model import StockPredictionModel

SEQ = 30


def make_random_walk(n=500, seed=0, drift=0.0):
    """Синтетични OHLCV данни без предсказуем сигнал."""
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(drift, 0.015, n)))
    high = close * (1 + np.abs(rng.normal(0, 0.006, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.006, n)))
    return pd.DataFrame({
        'Date': pd.date_range('2022-01-03', periods=n, freq='B'),
        'Open': close * (1 + rng.normal(0, 0.004, n)),
        'High': np.maximum(high, close),
        'Low': np.minimum(low, close),
        'Close': close,
        'Volume': rng.integers(1_000_000, 5_000_000, n),
    })


def build(df):
    """Пуска пълния preprocessing, без шумните print-ове."""
    p = StockDataPreprocessor(df)
    with contextlib.redirect_stdout(io.StringIO()):
        p.calculate_technical_indicators()
        p.create_target_variable(days_ahead=1)
        p.normalize_data()
    return p


def train_quick(X_train, y_train, X_val, y_val, epochs=20):
    m = StockPredictionModel(sequence_length=X_train.shape[1],
                             n_features=X_train.shape[2])
    with contextlib.redirect_stdout(io.StringIO()):
        m.build_lstm_model(lstm_units=[32, 16, 16], dropout_rate=0.2)
        m.train_model(X_train, y_train, X_val, y_val,
                      epochs=epochs, batch_size=32)
    return m


# ---------------------------------------------------------------- тестове

def test_targets_not_in_features():
    p = build(make_random_walk())
    cols = p.get_feature_columns()
    for bad in TARGET_COLUMNS:
        assert bad not in cols, f"{bad} е във features — моделът чете отговора"
    assert 'Date' not in cols
    assert len(cols) > 20, f"очаквахме много индикатори, има само {len(cols)}"
    return f"{len(cols)} feature колони, без нито един target"


def test_alignment_has_no_lookahead():
    """y[k] трябва да е посоката на деня, с който свършва прозорецът."""
    p = build(make_random_walk())
    X, y, prices = p.prepare_model_data(seq_length=SEQ)

    close = p.data['Close'].values
    target = p.data['Price_Direction'].values.astype(float)

    # Прозорците свършват само на дни, които вече имат етикет
    n_labelled = np.flatnonzero(~np.isnan(target))[-1] + 1
    end_idx = np.arange(SEQ - 1, n_labelled)

    assert len(X) == len(end_idx), \
        f"грешен брой последователности: {len(X)} вместо {len(end_idx)}"

    # prices[k] е Close на последния ден от прозореца
    assert np.allclose(prices, close[end_idx]), "цените не са подравнени"

    # y[k] е посоката от този ден към следващия
    for k in range(0, len(y) - 1, 37):
        t = end_idx[k]
        expected = 1.0 if close[t + 1] > close[t] else 0.0
        assert y[k] == expected, (
            f"y[{k}]={y[k]} но Close[{t}]={close[t]:.2f} -> "
            f"Close[{t+1}]={close[t+1]:.2f}"
        )
    return f"{len(X)} прозореца, подравняването е вярно"


def test_target_is_binary():
    p = build(make_random_walk())
    X, y, _ = p.prepare_model_data(seq_length=SEQ)
    assert set(np.unique(y)).issubset({0.0, 1.0}), f"y не е 0/1: {np.unique(y)[:5]}"
    assert 0.3 < y.mean() < 0.7, f"подозрителен баланс: {y.mean():.2f}"
    return f"y е 0/1, {y.mean()*100:.1f}% нагоре"


def test_latest_sequence_ends_with_today():
    """
    Прозорецът за предсказване трябва да завършва с последния ден,
    докато тренировъчните прозорци спират един ден по-рано (последният
    ден още няма етикет). Иначе моделът "предсказва" вчерашния ход.
    """
    df = make_random_walk(n=300)
    p = build(df)
    X, y, prices = p.prepare_model_data(seq_length=SEQ)
    latest = p.get_latest_sequence(SEQ)

    feats = p.scaled_data[p.get_feature_columns()].values

    assert len(feats) == len(df), "редовете не бива да се режат"
    assert prices[-1] == df['Close'].values[-2], \
        "тренировката включва ден без етикет"
    assert np.allclose(latest[0, -1], feats[-1]), \
        "прозорецът за предсказване не завършва с днешния ден"
    assert not np.allclose(latest[0], X[-1]), \
        "предсказваме същия прозорец, на който тренирахме"
    assert not np.isnan(latest).any(), "NaN в прозореца за предсказване"
    assert not np.isnan(X).any(), "NaN в тренировъчните данни"
    return f"тренировка до ден {len(X)+SEQ-2}, предсказване от ден {len(df)-1}"


def test_predict_returns_probabilities():
    p = build(make_random_walk(n=300))
    X, y, _ = p.prepare_model_data(seq_length=SEQ)
    split = int(len(X) * 0.8)
    m = train_quick(X[:split], y[:split], X[split:], y[split:], epochs=5)
    probs = m.predict(X[split:]).flatten()
    assert probs.min() >= 0.0 and probs.max() <= 1.0, \
        f"извън [0,1]: {probs.min():.3f}..{probs.max():.3f}"
    logits = m.predict(X[split:], return_logits=True).flatten()
    assert not np.allclose(logits, probs), "logits и вероятности са еднакви"
    return f"вероятности в [{probs.min():.3f}, {probs.max():.3f}]"


def test_random_data_gives_no_edge():
    """КРИТИЧЕН: без сигнал в данните точността трябва да е около 50%."""
    p = build(make_random_walk(n=700, seed=7))
    X, y, _ = p.prepare_model_data(seq_length=SEQ)

    split = int(len(X) * 0.75)
    val = int(split * 0.85)
    m = train_quick(X[:val], y[:val], X[val:split], y[val:split], epochs=25)

    with contextlib.redirect_stdout(io.StringIO()):
        metrics = m.evaluate(X[split:], y[split:])

    acc = metrics['Accuracy']
    assert acc < 65.0, (
        f"{acc:.1f}% точност върху чист шум — това е изтичане на данни, "
        f"не умение"
    )
    return f"точност {acc:.1f}% (baseline {metrics['Baseline_Accuracy']:.1f}%), няма leakage"


def test_model_can_actually_learn():
    """Машинарията работи: моделът трябва да може да overfit-не малък набор."""
    rng = np.random.default_rng(3)
    n, feats = 120, 8
    X = rng.normal(0, 1, (n, SEQ, feats)).astype(np.float32)
    # Етикетът зависи детерминистично от последния ден
    y = (X[:, -1, 0] > 0).astype(np.float32)

    m = train_quick(X, y, X, y, epochs=60)
    acc = ((m.predict(X).flatten() > 0.5).astype(int) == y.astype(int)).mean() * 100
    assert acc > 75.0, f"моделът не може да научи дори тривиален сигнал: {acc:.1f}%"
    return f"научи тривиален сигнал до {acc:.1f}%"


def test_old_models_are_rejected():
    """Стар v2 регресионен модел не бива да се зареди мълчаливо."""
    import json
    import torch
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(models_dir, exist_ok=True)
    name = '__legacy_test_model'
    with open(os.path.join(models_dir, f'{name}_config.json'), 'w') as f:
        json.dump({'sequence_length': SEQ, 'n_features': 10,
                   'architecture': 'lstm_attention_v2'}, f)
    torch.save({}, os.path.join(models_dir, f'{name}.pt'))
    try:
        m = StockPredictionModel()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                m.load_model(name)
            raise AssertionError("стар модел се зареди — трябваше да откаже")
        except ValueError as e:
            assert 'lstm_attention_v2' in str(e)
    finally:
        for suffix in ['_config.json', '.pt']:
            path = os.path.join(models_dir, f'{name}{suffix}')
            if os.path.exists(path):
                os.remove(path)
    return "стари v2 модели се отхвърлят"


TESTS = [
    test_targets_not_in_features,
    test_alignment_has_no_lookahead,
    test_target_is_binary,
    test_latest_sequence_ends_with_today,
    test_old_models_are_rejected,
    test_predict_returns_probabilities,
    test_model_can_actually_learn,
    test_random_data_gives_no_edge,
]


def main():
    print("=" * 62)
    print("ПРОВЕРКА НА PIPELINE-А")
    print("=" * 62)
    failed = 0
    for t in TESTS:
        try:
            detail = t()
            print(f"[OK]   {t.__name__}\n         {detail}")
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {t.__name__}\n         {e}")
        except Exception as e:
            failed += 1
            print(f"[ERR]  {t.__name__}\n         {type(e).__name__}: {e}")
    print("=" * 62)
    if failed:
        print(f"{failed} от {len(TESTS)} теста паднаха")
        sys.exit(1)
    print(f"Всички {len(TESTS)} теста минаха")


if __name__ == "__main__":
    main()
