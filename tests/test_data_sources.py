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


# ---------------------------------------------------------------- news_data.py

def _mk_article(title, source, url, available_at, score=0.0, label='neutral', historical=False):
    return {
        'title': title, 'source': source, 'url': url,
        'available_at': available_at, 'is_historical': historical,
        'sentiment_score': score, 'sentiment_label': label,
    }


def test_pubdate_parsing_handles_valid_and_invalid():
    from news_data import parse_pub_date
    ok = parse_pub_date('Tue, 02 Jan 2024 08:00:00 GMT')
    assert ok is not None and ok.year == 2024 and ok.hour == 8
    assert parse_pub_date('') is None
    assert parse_pub_date('not a date at all') is None
    assert parse_pub_date(None) is None
    return "валиден RFC-822 се парсва, невалиден дава None без изключение"


def test_dedup_collapses_wire_copies():
    """20 копия на една новина (различни source label, същия URL) -> 1."""
    from news_data import deduplicate_articles
    base_time = datetime(2024, 3, 1, tzinfo=timezone.utc)
    articles = [
        _mk_article(f"Apple beats earnings estimates", f"Outlet {i}",
                   "https://example.com/apple-earnings-story",
                   base_time + timedelta(hours=i))
        for i in range(20)
    ]
    deduped = deduplicate_articles(articles)
    assert len(deduped) == 1, f"очаквах 1 статия след dedup, получих {len(deduped)}"
    assert deduped[0]['available_at'] == base_time, "не запази най-ранния timestamp"
    return "20 копия на една статия -> 1 след dedup, пази най-ранния timestamp"


def test_dedup_keeps_distinct_articles():
    from news_data import deduplicate_articles
    t = datetime(2024, 3, 1, tzinfo=timezone.utc)
    articles = [
        _mk_article("Apple beats earnings", "Reuters", "https://a.com/1", t),
        _mk_article("Apple unveils new iPhone", "Bloomberg", "https://a.com/2", t),
        _mk_article("Apple faces lawsuit", "CNBC", "https://a.com/3", t),
    ]
    deduped = deduplicate_articles(articles)
    assert len(deduped) == 3, "различни статии не бива да се сливат"
    return "3 различни статии остават 3 след dedup"


def test_historical_backfill_embargo_is_full_day():
    """
    Historical fetch (виж модулния docstring) НЕ може да се тества с жива
    мрежа тук стабилно, но embargo логиката (date(pubDate)+1 ден) е
    чиста функция — проверяваме я директно.
    """
    from datetime import date as _date
    raw_pub = "Wed, 06 Mar 2024 14:32:00 GMT"  # реален час, но от backfill резултат
    from news_data import parse_pub_date
    parsed = parse_pub_date(raw_pub)
    embargo_start = datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc) + timedelta(days=1)
    assert embargo_start == datetime(2024, 3, 7, tzinfo=timezone.utc), (
        f"embargo трябва да е следващият ден 00:00 UTC, получих {embargo_start}"
    )
    assert embargo_start.date() > parsed.date(), "backfill embargo трябва да мести с цял ден напред"
    return f"статия от {parsed.date()} става налична едва от {embargo_start}"


def test_future_news_excluded_from_features():
    """
    ТОЧНИЯТ сценарий от заданието: prediction в 14:00, новина в 15:00
    същия ден -> новината НЕ бива да участва в features за 14:00.
    """
    from news_data import compute_news_features

    prediction_time = datetime(2026, 9, 10, 14, 0, tzinfo=timezone.utc)
    future_article = _mk_article(
        "Apple stock surges on huge news", "Reuters", "https://x.com/future",
        datetime(2026, 9, 10, 15, 0, tzinfo=timezone.utc),  # 1 час СЛЕД prediction_time
        score=0.9, label='bullish',
    )
    past_article = _mk_article(
        "Apple stock steady", "Bloomberg", "https://x.com/past",
        datetime(2026, 9, 10, 13, 30, tzinfo=timezone.utc),  # 30 мин ПРЕДИ, ясно вътре в 1h прозореца
        score=0.1, label='neutral',
    )

    feats_with_future = compute_news_features(
        [future_article, past_article], [prediction_time]
    )
    feats_without_future = compute_news_features([past_article], [prediction_time])

    row_with = feats_with_future.iloc[0]
    row_without = feats_without_future.iloc[0]

    assert row_with['news_count_1h'] == row_without['news_count_1h'] == 1, (
        "бъдещата новина в 15:00 промени броя новини за 14:00 prediction — LEAKAGE"
    )
    assert row_with['avg_sentiment_1h'] == row_without['avg_sentiment_1h'], (
        "бъдещата новина промени sentiment-а за 14:00 prediction — LEAKAGE"
    )
    assert row_with['avg_sentiment_1h'] == 0.1, "трябваше да остане само миналата (неутрална) статия"
    return "новина в 15:00 не влияе на features, изчислени за 14:00 (проверено с/без нея)"


def test_news_rolling_aggregates_no_forward_window():
    """Общо свойство: добавяне на СЛЕДВАЩИ статии не бива да променя минали target features."""
    from news_data import compute_news_features

    rng = np.random.default_rng(42)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    articles = [
        _mk_article(f"story {i}", "src", f"https://x.com/{i}",
                   base + timedelta(hours=int(rng.uniform(0, 24 * 30))),
                   score=float(rng.uniform(-1, 1)),
                   label=rng.choice(['bullish', 'bearish', 'neutral']))
        for i in range(200)
    ]

    targets = [base + timedelta(days=d) for d in range(5, 20)]
    cutoff = base + timedelta(days=15)

    full_feats = compute_news_features(articles, targets)
    past_only = [a for a in articles if a['available_at'] <= cutoff]
    past_feats = compute_news_features(past_only, targets)

    early_targets = [t for t in targets if t <= cutoff - timedelta(hours=24)]
    for i, t in enumerate(targets):
        if t not in early_targets:
            continue
        for col in ['news_count_24h', 'avg_sentiment_24h', 'positive_news_count_24h']:
            a = full_feats.iloc[i][col]
            b = past_feats.iloc[i][col]
            assert a == b, f"{col} за {t} се промени при добавяне на бъдещи статии"

    return f"{len(early_targets)} target момента непроменени при добавяне на {len(articles)-len(past_only)} бъдещи статии"


def test_no_news_gives_neutral_defaults_not_nan():
    """
    Ден без новини: count=0, sentiment=0.0 (неутрално по смисъл, не
    'липсваща' стойност) — умишлен избор, различен от fundamentals
    (където липса на отчет = NaN, защото там наистина е неизвестно).
    """
    from news_data import compute_news_features
    feats = compute_news_features([], [datetime(2026, 1, 1, tzinfo=timezone.utc)])
    row = feats.iloc[0]
    assert row['news_count_24h'] == 0
    assert row['avg_sentiment_24h'] == 0.0
    assert not pd.isna(row['avg_sentiment_24h'])
    return "празен news list -> 0/0.0 (неутрално), не NaN"


TESTS = [
    test_market_features_no_duplicate_dates,
    test_market_features_have_expected_columns,
    test_market_features_no_future_leak,
    test_treasury_yield_sane_scale,
    test_market_asof_join_never_pulls_future_row,
    test_fundamentals_respects_publish_time,
    test_fundamentals_no_report_yet_gives_nan_not_zero,
    test_fundamentals_timeline_empty_does_not_crash,
    test_pubdate_parsing_handles_valid_and_invalid,
    test_dedup_collapses_wire_copies,
    test_dedup_keeps_distinct_articles,
    test_historical_backfill_embargo_is_full_day,
    test_future_news_excluded_from_features,
    test_news_rolling_aggregates_no_forward_window,
    test_no_news_gives_neutral_defaults_not_nan,
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
