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


def test_price_levels_are_not_features():
    """Абсолютните нива остават за графики, но не влизат в модела."""
    p = build(make_random_walk())
    cols = set(p.get_feature_columns())

    for bad in ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_20', 'SMA_50',
                'EMA_12', 'MACD', 'BB_Upper', 'BB_Lower', 'ATR', 'OBV', 'VWAP']:
        assert bad not in cols, f"{bad} е абсолютно ниво, а е във features"
        assert bad in p.data.columns, f"{bad} трябва да остане в self.data"

    for good in ['Close_vs_SMA20', 'SMA20_vs_SMA50', 'MACD_Norm', 'BB_Position',
                 'Volume_Ratio', 'OBV_Norm', 'Close_vs_VWAP', 'Gap_Pct',
                 'HL_Range_Pct', 'Is_Quarter_Month', 'Day_Of_Week']:
        assert good in cols, f"липсва стационарният заместител {good}"
    return f"{len(cols)} стационарни features, нивата са изключени"


def test_features_are_stationary():
    """
    Върху силно растяща серия нито един feature не бива да следва тренда.
    Ако следва, стойностите му в теста са извън диапазона от тренировката.
    """
    df = make_random_walk(n=800, seed=11, drift=0.0012)
    p = build(df)
    cols = p.get_feature_columns()

    # Ненормализирани стойности — тестваме самите features, не скалера
    feats = p.data[cols].values.astype(float)
    t = np.arange(len(feats), dtype=float)

    worst, worst_col = 0.0, None
    for j, c in enumerate(cols):
        v = feats[:, j]
        if np.std(v) < 1e-12 or not np.isfinite(v).all():
            continue
        r = abs(np.corrcoef(t, v)[0, 1])
        if r > worst:
            worst, worst_col = r, c

    price_corr = abs(np.corrcoef(t, p.data['Close'].values)[0, 1])
    assert price_corr > 0.8, "тестовата серия не е достатъчно трендова"
    assert worst < 0.8, \
        f"'{worst_col}' следва тренда (corr={worst:.2f}) — не е стационарен"
    return (f"най-трендов feature: {worst_col} (corr={worst:.2f}), "
            f"докато цената е {price_corr:.2f}")


def test_no_infinities_in_features():
    p = build(make_random_walk(n=400, seed=5))
    feats = p.data[p.get_feature_columns()].values.astype(float)
    assert np.isfinite(feats).all(), "има inf или NaN във features"
    return "няма inf/NaN"


def test_no_backfill_at_series_start():
    """
    Началните редове нямат история за дългите прозорци. Преди се запълваха
    с bfill, тоест със стойности от бъдещето. Сега трябва да са изхвърлени,
    а първият оцелял ред да носи истински изчислен индикатор.
    """
    df = make_random_walk(n=300, seed=31)
    p = StockDataPreprocessor(df)
    with contextlib.redirect_stdout(io.StringIO()):
        out = p.calculate_technical_indicators()

    assert len(out) < len(df), "нищо не е отрязано — warmup-ът още се запълва"
    assert not out.isna().any().any(), "остават NaN след обработката"

    # Първият оцелял ред, намерен обратно в оригиналните данни
    first_date = out['Date'].iloc[0]
    pos = int(np.flatnonzero(df['Date'].values == first_date)[0])

    # SMA_50 там трябва да е истинската средна на последните 50 дни,
    # а не първата налична стойност, дръпната назад
    expected = df['Close'].iloc[pos - 49:pos + 1].mean()
    actual = out['SMA_50'].iloc[0]
    assert abs(actual - expected) < 1e-6, \
        f"SMA_50 на първия ред е {actual:.4f}, а истинската е {expected:.4f}"

    return f"изхвърлени {len(df)-len(out)} реда warmup, индикаторите са истински"


def test_scaler_sees_only_training_rows():
    """Скалерът не бива да е видял нито един ред от тестовите прозорци."""
    p = build(make_random_walk(n=600, seed=13))
    X, y, _ = p.prepare_model_data(seq_length=SEQ, train_size=0.8)

    cols = p.scaled_columns
    raw = p.data[cols].values.astype(float)
    fit_rows = p._fit_rows

    split = int(len(X) * 0.8)
    assert fit_rows <= split, \
        f"скалерът е видял {fit_rows} реда, а тестът почва на ред {split}"

    assert np.allclose(p.scaler.mean_, raw[:fit_rows].mean(axis=0)), \
        "скалерът не е трениран точно от тренировъчните редове"
    assert not np.allclose(p.scaler.mean_, raw.mean(axis=0)), \
        "скалерът е видял целите данни"
    return f"скалер от първите {fit_rows} реда, тестът почва на {split}"


def test_standard_scaler_keeps_signal_wide():
    """
    MinMax свиваше дневните промени под 0.1 std, докато осцилаторите
    оставаха широки. След StandardScaler всички са сравними.
    """
    p = build(make_random_walk(n=600, seed=17))
    p.prepare_model_data(seq_length=SEQ, train_size=0.8)

    cols = p.get_feature_columns()
    scaled = p.scaled_data[cols].values.astype(float)
    stds = scaled.std(axis=0)

    for name in ['Price_Change', 'Gap_Pct', 'OC_Range_Pct']:
        s = stds[cols.index(name)]
        assert s > 0.5, f"{name} е смачкан до std={s:.3f}"

    ratio = stds.max() / max(stds.min(), 1e-9)
    assert ratio < 10, f"разликата между най-широкия и най-тесния е {ratio:.1f}x"
    return f"std между {stds.min():.2f} и {stds.max():.2f} ({ratio:.1f}x разлика)"


def test_scaler_travels_with_model():
    """Записаният модел носи скалера си и го налага върху новите данни."""
    import shutil
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    name = '__scaler_roundtrip'

    p = build(make_random_walk(n=300, seed=21))
    X, y, _ = p.prepare_model_data(seq_length=SEQ)
    m = train_quick(X[:200], y[:200], X[200:], y[200:], epochs=3)

    try:
        with contextlib.redirect_stdout(io.StringIO()):
            m.save_model(name, scaler=p.scaler, feature_columns=p.scaled_columns)
            m2 = StockPredictionModel()
            m2.load_model(name)

        assert m2.scaler is not None, "скалерът не е зареден"
        assert m2.scaler_columns == p.scaled_columns, "редът на колоните се разминава"
        assert np.allclose(m2.scaler.mean_, p.scaler.mean_)

        # По-дълга серия има свой различен скалер — моделът налага своя
        p2 = build(make_random_walk(n=450, seed=21))
        own = p2.get_latest_sequence(SEQ).copy()
        p2.apply_scaler(m2.scaler, m2.scaler_columns)
        imposed = p2.get_latest_sequence(SEQ)
        assert not np.allclose(own, imposed), \
            "apply_scaler не промени нищо — записаният скалер се игнорира"
    finally:
        for suffix in ['.pt', '_config.json', '_history.json', '_scaler.joblib']:
            path = os.path.join(models_dir, f'{name}{suffix}')
            if os.path.exists(path):
                os.remove(path)
    return "скалерът се записва, зарежда и се налага при предсказване"


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

    # Warmup-ът отпред се маха, но последният ден трябва да оцелее —
    # той е входът за предсказанието.
    assert p.data['Date'].iloc[-1] == df['Date'].iloc[-1], \
        "последният ден е отрязан — няма от какво да предсказваме"
    assert prices[-1] == df['Close'].values[-2], \
        "тренировката включва ден без етикет"
    assert np.allclose(latest[0, -1], feats[-1]), \
        "прозорецът за предсказване не завършва с днешния ден"
    assert not np.allclose(latest[0], X[-1]), \
        "предсказваме същия прозорец, на който тренирахме"
    assert not np.isnan(latest).any(), "NaN в прозореца за предсказване"
    assert not np.isnan(X).any(), "NaN в тренировъчните данни"
    return (f"{len(X)} тренировъчни прозореца, предсказването ползва "
            f"последния ден от данните")


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
    test_price_levels_are_not_features,
    test_features_are_stationary,
    test_no_infinities_in_features,
    test_no_backfill_at_series_start,
    test_scaler_sees_only_training_rows,
    test_standard_scaler_keeps_signal_wide,
    test_scaler_travels_with_model,
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
