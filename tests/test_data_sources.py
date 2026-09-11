"""
Тестове за news / market / fundamentals интеграцията.

Най-важната гаранция във всички тези тестове: нищо, изчислено за момент T,
не бива да зависи от информация с timestamp > T. Проверяваме го буквално —
пресмятаме features с данни само до T, после с допълнителни бъдещи редове,
и очакваме идентичен резултат за T.

Стартиране:
    python tests/test_data_sources.py
"""

import os
import sys
import io
import contextlib
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ---------------------------------------------------------------- helpers

def make_index_series(n=200, seed=0, start='2024-01-01'):
    """Синтетична дневна серия за един индекс (random walk)."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start=start, periods=n, tz='UTC')
    close = 4000 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, n)))
    return pd.DataFrame({'Date': dates, 'Close': close})


# ---------------------------------------------------------------- market_data.py

def test_market_features_no_duplicate_dates():
    from market_data import compute_market_features
    idx = {
        '^GSPC': make_index_series(150, seed=1),
        '^VIX': make_index_series(150, seed=2),
        '^TNX': make_index_series(150, seed=3),
    }
    feats = compute_market_features(idx)
    dupes = feats['Date'].duplicated().sum()
    assert dupes == 0, f"{dupes} дублирани дати в market features"
    return f"{len(feats)} реда, без дублирани дати"


def test_market_features_have_expected_columns():
    from market_data import compute_market_features
    idx = {'^GSPC': make_index_series(150, seed=4), '^VIX': make_index_series(150, seed=5)}
    feats = compute_market_features(idx)
    expected = ['sp500_return_1d', 'sp500_return_5d', 'sp500_volatility_20d',
                'market_trend', 'vix_close', 'vix_change_1d', 'vix_change_5d']
    missing = [c for c in expected if c not in feats.columns]
    assert not missing, f"липсват колони: {missing}"
    return f"{len(feats.columns)-1} market features присъстват"


def test_market_features_no_future_leak():
    """
    КРИТИЧЕН: стойността на ред T не бива да се промени, ако добавим
    редове СЛЕД T към входа. Пресмятаме два пъти — веднъж с пълната
    серия, веднъж отрязана точно на T — и очакваме identical резултат
    за всички редове <= T.
    """
    from market_data import compute_market_features

    full = make_index_series(200, seed=6)
    cutoff = 120  # индекс в серията, не дата
    truncated = full.iloc[:cutoff].copy()

    idx_full = {'^GSPC': full}
    idx_trunc = {'^GSPC': truncated}

    feats_full = compute_market_features(idx_full)
    feats_trunc = compute_market_features(idx_trunc)

    common = feats_trunc['Date']
    merged = feats_full[feats_full['Date'].isin(common)].reset_index(drop=True)
    trunc_sorted = feats_trunc.sort_values('Date').reset_index(drop=True)

    numeric_cols = [c for c in merged.columns if c != 'Date']
    for col in numeric_cols:
        a = merged[col].values.astype(float)
        b = trunc_sorted[col].values.astype(float)
        assert np.allclose(a, b, equal_nan=True), (
            f"{col} се променя, когато добавим БЪДЕЩИ редове — има leakage"
        )
    return f"{len(numeric_cols)} market features непроменени при добавяне на бъдещи редове"


def test_treasury_yield_sane_scale():
    from market_data import compute_market_features
    tnx = make_index_series(100, seed=7, start='2024-01-01')
    tnx['Close'] = np.random.default_rng(8).uniform(3.5, 5.5, len(tnx))  # реалистичен % диапазон
    feats = compute_market_features({'^TNX': tnx})
    yields = feats['treasury_10y_yield'].dropna()
    assert yields.between(0, 20).all(), (
        f"treasury_10y_yield извън разумен диапазон: {yields.min()}-{yields.max()}"
    )
    return f"yield диапазон {yields.min():.2f}-{yields.max():.2f}% — разумна скала"


def test_market_asof_join_never_pulls_future_row():
    """
    Точният начин, по който market features ще се присъединяват към
    цената на акцията: merge_asof(direction='backward'). Проверяваме, че
    за всеки ден от акцията присъединеният market ред е ИЛИ същия ден,
    ИЛИ по-стар — никога по-нов.
    """
    from market_data import compute_market_features

    idx = make_index_series(60, seed=9)
    feats = compute_market_features({'^GSPC': idx}).sort_values('Date')

    stock_dates = pd.bdate_range('2024-01-10', periods=40, tz='UTC')
    stock_df = pd.DataFrame({'Date': stock_dates}).sort_values('Date')

    merged = pd.merge_asof(stock_df, feats, on='Date', direction='backward')

    # merge_asof гарантира backward-only по конструкция, но проверяваме
    # директно: избраната market стойност трябва да идва от ред с
    # Date <= датата на акцията, никога от по-нов ред.
    checked = 0
    for _, row in merged.dropna(subset=['sp500_return_1d']).iterrows():
        chosen = feats[feats['sp500_return_1d'] == row['sp500_return_1d']]
        assert (chosen['Date'] <= row['Date']).all(), (
            f"merge_asof избра market ред от бъдещето за {row['Date']}"
        )
        checked += 1
    assert checked > 0
    return f"проверени {checked} присъединявания, всички backward-only"


TESTS = [
    test_market_features_no_duplicate_dates,
    test_market_features_have_expected_columns,
    test_market_features_no_future_leak,
    test_treasury_yield_sane_scale,
    test_market_asof_join_never_pulls_future_row,
]


def main():
    print("=" * 62)
    print("ПРОВЕРКА НА NEWS / MARKET / FUNDAMENTALS МОДУЛИТЕ")
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
