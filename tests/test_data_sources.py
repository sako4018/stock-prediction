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


# ---------------------------------------------------------------- fundamentals.py (as-of)

def test_fundamentals_respects_publish_time():
    """
    ТОЧНИЯТ сценарий от заданието: стойност публикувана на
    2026-08-01 21:00 UTC не бива да се вижда преди този момент, и
    остава валидна до следващия отчет (не изчезва на другия ден).
    """
    from fundamentals import merge_fundamentals_asof

    timeline = pd.DataFrame({
        'available_at': [
            datetime(2026, 5, 1, 21, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 1, 21, 0, tzinfo=timezone.utc),
        ],
        'eps_actual': [1.50, 1.80],
        'eps_estimate': [1.45, 1.75],
        'surprise_pct': [3.4, 2.9],
        'revenue': [1e11, 1.1e11],
        'net_income': [3e10, 3.1e10],
        'trailing_eps_ttm': [6.0, 6.3],
        'pe_ratio_at_report': [30.0, 31.0],
    })

    price_df = pd.DataFrame({
        'Date': [
            datetime(2026, 8, 1, 20, 0, tzinfo=timezone.utc),   # 1 час ПРЕДИ отчета
            datetime(2026, 8, 1, 22, 0, tzinfo=timezone.utc),   # 1 час СЛЕД отчета
            datetime(2026, 8, 15, tzinfo=timezone.utc),         # между двата отчета
            datetime(2026, 10, 1, tzinfo=timezone.utc),         # все още преди следващия
        ]
    })

    merged = merge_fundamentals_asof(price_df, timeline)

    before = merged.iloc[0]
    after = merged.iloc[1]
    between = merged.iloc[2]
    later = merged.iloc[3]

    assert pd.isna(before['eps_actual']) or before['eps_actual'] == 1.50, \
        "часът преди отчета не бива да вижда НОВИЯ отчет"
    assert before['eps_actual'] != 1.80, "видяна е бъдеща стойност (leakage)"
    assert after['eps_actual'] == 1.80, "стойността не се появи веднага след публикуване"
    assert between['eps_actual'] == 1.80, "стойността изчезна преди следващия отчет"
    assert later['eps_actual'] == 1.80, "стойността не остава валидна до следващ отчет"
    return "публикувана стойност: невидима преди, видима веднага след, валидна до следващ отчет"


def test_fundamentals_no_report_yet_gives_nan_not_zero():
    """Преди първия отчет — NaN (липсваща информация), не 0 (невярна информация)."""
    from fundamentals import merge_fundamentals_asof

    timeline = pd.DataFrame({
        'available_at': [datetime(2026, 6, 1, tzinfo=timezone.utc)],
        'eps_actual': [1.5], 'eps_estimate': [1.4], 'surprise_pct': [7.1],
        'revenue': [1e11], 'net_income': [3e10], 'trailing_eps_ttm': [6.0],
        'pe_ratio_at_report': [30.0],
    })
    price_df = pd.DataFrame({'Date': [datetime(2026, 1, 1, tzinfo=timezone.utc)]})
    merged = merge_fundamentals_asof(price_df, timeline)
    assert pd.isna(merged.iloc[0]['eps_actual']), \
        f"очаквах NaN преди първия отчет, получих {merged.iloc[0]['eps_actual']}"
    return "ред преди първия отчет: NaN, не 0"


def test_fundamentals_timeline_empty_does_not_crash():
    """Тикер без earnings история (или API грешка) не бива да чупи merge-а."""
    from fundamentals import merge_fundamentals_asof, FUNDAMENTAL_TIMELINE_COLUMNS
    empty = pd.DataFrame(columns=FUNDAMENTAL_TIMELINE_COLUMNS)
    price_df = pd.DataFrame({'Date': [datetime(2026, 1, 1, tzinfo=timezone.utc)]})
    merged = merge_fundamentals_asof(price_df, empty)
    assert len(merged) == 1
    assert pd.isna(merged.iloc[0]['eps_actual'])
    return "празна timeline не чупи merge-а, дава NaN колони"


TESTS = [
    test_market_features_no_duplicate_dates,
    test_market_features_have_expected_columns,
    test_market_features_no_future_leak,
    test_treasury_yield_sane_scale,
    test_market_asof_join_never_pulls_future_row,
    test_fundamentals_respects_publish_time,
    test_fundamentals_no_report_yet_gives_nan_not_zero,
    test_fundamentals_timeline_empty_does_not_crash,
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
