"""
Проверки на pooled (cross-sectional) dataset-а.

Смесването на много акции в един dataset отваря два нови начина за
изтичане на данни, каквито при един тикър няма:

  1. Ако всеки тикер се реже на своите собствени 80%, тестовият период на
     едната акция съвпада по време с тренировъчния на другата — моделът е
     виждал пазара точно тогава. Затова разделянето е по глобална дата.
  2. Ако последователностите се строят върху слепения масив, един прозорец
     може да хване последните дни на AAPL и първите на MSFT — вход, който
     не съществува в реалността.

Тестовете тук проверяват точно тези две неща, плюс purge зоната и това, че
скалерът не е видял нищо от теста.

Стартиране:
    python tests/test_pooled.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pooled_dataset import pool_frames, split_train_val, apply_min_move

SEQ = 10
DAYS_AHEAD = 1


def make_frame(ticker_id, n=200, start='2020-01-01', seed=0):
    """
    Синтетична таблица във формата, който build_raw_frame връща.

    'marker' е константа, различна за всеки тикер — по нея се вижда дали
    някой прозорец е прескочил от една акция в друга.
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, periods=n, freq='B')
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    future = pd.Series(close).shift(-DAYS_AHEAD)

    return pd.DataFrame({
        'Date': dates,
        'Close': close,
        'Future_Price': future,
        'Price_Direction': np.where(future.isna(), np.nan,
                                    (future > close).astype(float)),
        'marker': np.full(n, float(ticker_id)),
        'noise': rng.normal(0, 1, n),
    })


def make_frames(k=3, n=200):
    return {f'T{i}': make_frame(i, n=n, seed=i) for i in range(k)}


def test_split_is_by_global_date():
    """Нито един тренировъчен етикет не се решава след split датата."""
    ds = pool_frames(make_frames(), seq_length=SEQ, days_ahead=DAYS_AHEAD)
    split = ds['split_date']

    late = ds['meta_train'][ds['meta_train']['label_date'] > split]
    assert late.empty, (
        f"{len(late)} тренировъчни примера имат етикет след split датата "
        f"{split.date()} — това е бъдеща информация в тренировката"
    )

    early = ds['meta_test'][ds['meta_test']['end_date'] <= split]
    assert early.empty, (
        f"{len(early)} тестови примера свършват преди split датата — "
        f"тестът застъпва тренировъчния период"
    )
    return (f"train до {ds['meta_train']['label_date'].max().date()}, "
            f"test от {ds['meta_test']['end_date'].min().date()}")


def test_every_ticker_is_split_at_the_same_date():
    """
    Всеки тикер се реже на една и съща дата.

    Точно това е разликата от наивното слепване на 25 отделни 80/20
    split-а: там границата е различна за всяка акция.
    """
    ds = pool_frames(make_frames(k=4), seq_length=SEQ, days_ahead=DAYS_AHEAD)

    boundaries = {}
    for ticker, grp in ds['meta_train'].groupby('ticker'):
        boundaries[ticker] = grp['end_date'].max()
    test_starts = {t: g['end_date'].min() for t, g in ds['meta_test'].groupby('ticker')}

    assert len(ds['meta_test']['ticker'].unique()) == 4, "не всички тикери са в теста"
    spread = (max(boundaries.values()) - min(boundaries.values())).days
    assert spread <= 7, (
        f"краят на тренировката се различава с {spread} дни между тикерите — "
        f"значи разделянето не е по обща дата"
    )
    return f"4 тикера, разлика в границата {spread} дни, тестове почват {min(test_starts.values()).date()}"


def test_sequences_never_span_two_tickers():
    """Един вход съдържа дни само от една акция."""
    frames = make_frames(k=3, n=120)
    ds = pool_frames(frames, seq_length=SEQ, days_ahead=DAYS_AHEAD)

    names = ds['feature_names']
    assert 'marker' in names, "marker колоната трябва да е сред features"
    m = names.index('marker')

    for X, meta, label in ((ds['X_train'], ds['meta_train'], 'train'),
                           (ds['X_test'], ds['meta_test'], 'test')):
        markers = X[:, :, m]
        varying = np.where(markers.std(axis=1) > 1e-9)[0]
        assert len(varying) == 0, (
            f"{len(varying)} последователности в {label} смесват два тикера "
            f"(първата е № {varying[0] if len(varying) else '-'})"
        )
    return f"{len(ds['X_train']) + len(ds['X_test'])} прозореца, всеки в рамките на един тикер"


def test_scaler_never_sees_test_rows():
    """
    Скалерът е научен само от редове до split датата.

    Проверката е пряка: пресмятаме средното на една колона ръчно от
    редовете преди split-а и го сравняваме с това на скалера.
    """
    frames = make_frames(k=3, n=200)
    ds = pool_frames(frames, seq_length=SEQ, days_ahead=DAYS_AHEAD)
    split = ds['split_date']
    col = ds['feature_names'].index('noise')

    manual = []
    for df in frames.values():
        d = df.sort_values('Date')
        labelled = d['Price_Direction'].notna()
        end = int(np.flatnonzero(labelled.to_numpy())[-1]) + 1
        d = d.iloc[:end]
        manual.append(d.loc[d['Date'] <= split, 'noise'].to_numpy())
    manual = np.concatenate(manual)

    got = ds['scaler'].mean_[col]
    assert abs(got - manual.mean()) < 1e-9, (
        f"средното на скалера ({got:.6f}) не съвпада с това само на "
        f"тренировъчните редове ({manual.mean():.6f}) — видял е и тестови данни"
    )
    return f"скалерът е учил от {len(manual)} реда до {split.date()}"


def test_purge_zone_is_dropped():
    """
    Примерите между тренировката и теста отпадат.

    Пример, чийто прозорец свършва точно на split датата, има етикет, който
    се решава ден по-късно — тоест вече в тестовия период. Той не бива да
    се ползва нито за тренировка, нито за тест.
    """
    ds = pool_frames(make_frames(k=3), seq_length=SEQ, days_ahead=DAYS_AHEAD)
    assert ds['n_purged'] > 0, "очаквах поне един изхвърлен пример в purge зоната"

    total_kept = len(ds['meta_train']) + len(ds['meta_test'])
    overlap = set(zip(ds['meta_train']['ticker'], ds['meta_train']['end_date'])) & \
              set(zip(ds['meta_test']['ticker'], ds['meta_test']['end_date']))
    assert not overlap, f"{len(overlap)} примера са едновременно в train и test"
    return f"{ds['n_purged']} изхвърлени, {total_kept} запазени, 0 застъпващи се"


def test_longer_horizon_widens_the_purge_gap():
    """При 5-дневен хоризонт замърсената зона е по-широка, не по-тясна."""
    frames = make_frames(k=3, n=250)
    for df in frames.values():
        future = df['Close'].shift(-5)
        df['Future_Price'] = future
        df['Price_Direction'] = np.where(future.isna(), np.nan,
                                         (future > df['Close']).astype(float))

    d1 = pool_frames(make_frames(k=3, n=250), seq_length=SEQ, days_ahead=1)
    d5 = pool_frames(frames, seq_length=SEQ, days_ahead=5)

    assert d5['n_purged'] > d1['n_purged'], (
        f"5-дневният хоризонт изхвърли {d5['n_purged']} примера, а "
        f"1-дневният {d1['n_purged']} — при по-дълъг етикет зоната трябва да расте"
    )
    gap = (d5['meta_test']['end_date'].min() - d5['meta_train']['label_date'].max()).days
    assert gap >= 0, f"train етикетите застъпват теста ({gap} дни)"
    return f"purge: 1 ден -> {d1['n_purged']}, 5 дни -> {d5['n_purged']}"


def test_meta_rows_line_up_with_x_rows():
    """
    meta[i] описва X[i] — ред по ред.

    Регресия: meta беше сортирана по дата, докато X е слепен по тикери.
    Така предсказание за едната акция се отчиташе като предсказание за
    друга, без нищо да гръмне — точно тихата грешка, която прави
    резултатите безсмислени.
    """
    ds = pool_frames(make_frames(k=4, n=150), seq_length=SEQ, days_ahead=DAYS_AHEAD)
    m = ds['feature_names'].index('marker')

    for X, meta, label in ((ds['X_train'], ds['meta_train'], 'train'),
                           (ds['X_test'], ds['meta_test'], 'test')):
        # marker е ID-то на тикера, но минато през скалера — достатъчно е,
        # че е константа за тикера, затова сравняваме групирано.
        seen = {}
        for i, ticker in enumerate(meta['ticker'].to_numpy()):
            value = float(X[i, -1, m])
            if ticker in seen:
                assert abs(seen[ticker] - value) < 1e-6, (
                    f"{label}: ред {i} е означен като {ticker}, но marker "
                    f"стойността му ({value:.4f}) не съвпада с останалите "
                    f"редове на същия тикер ({seen[ticker]:.4f})"
                )
            else:
                seen[ticker] = value
        assert len(seen) == 4, f"{label}: очаквах 4 тикера, намерих {len(seen)}"
    return "X и meta са подравнени и в train, и в test"


def test_validation_split_is_chronological():
    """Всички валидационни примери са по-късни от всички тренировъчни."""
    ds = pool_frames(make_frames(k=3, n=300), seq_length=SEQ, days_ahead=DAYS_AHEAD)
    X_tr, y_tr, X_val, y_val = split_train_val(ds, val_fraction=0.2)

    assert len(X_tr) + len(X_val) == len(ds['X_train']), "примери се загубиха при разделянето"
    assert len(X_val) > 0 and len(X_tr) > 0, "празен train или val"

    dates = ds['meta_train']['end_date'].to_numpy()
    ordered = np.sort(dates)
    cut = min(max(1, int(len(ordered) * 0.8)), len(ordered) - 1)
    boundary = ordered[cut]
    is_val = dates >= boundary

    assert dates[~is_val].max() < dates[is_val].min(), (
        "тренировъчен пример е по-късен от валидационен — разделянето не е по време"
    )
    return f"train {len(X_tr)} (до {pd.Timestamp(dates[~is_val].max()).date()}), val {len(X_val)}"


def test_ticker_with_broken_data_is_skipped_not_fatal():
    """Един повреден тикер не бива да събори целия dataset."""
    frames = make_frames(k=3, n=200)
    frames['BROKEN'] = make_frame(99, n=200, seed=99)
    frames['BROKEN'].loc[50:60, 'noise'] = np.nan
    frames['TOO_SHORT'] = make_frame(98, n=SEQ - 2, seed=98)

    ds = pool_frames(frames, seq_length=SEQ, days_ahead=DAYS_AHEAD)
    assert 'BROKEN' not in ds['tickers'], "тикер с липсващи стойности влезе в dataset-а"
    assert 'TOO_SHORT' not in ds['tickers'], "твърде къс тикер влезе в dataset-а"
    assert len(ds['tickers']) == 3, f"очаквах 3 здрави тикера, останаха {ds['tickers']}"
    return f"запазени {ds['tickers']}, пропуснати BROKEN и TOO_SHORT"


def test_min_move_drops_flat_days_from_the_middle():
    """
    Дните с дребно движение отпадат като примери, но остават в историята.

    Важното е второто: ако редът се изтриеше от таблицата, прозорците на
    следващите дни щяха да прескочат ден и да съдържат вход, който в
    реалността не съществува.
    """
    frames = {}
    for i in range(3):
        df = make_frame(i, n=200, seed=i)
        frames[f'T{i}'] = apply_min_move(df, min_move=0.01)

    rows_before = len(make_frame(0, n=200, seed=0))
    assert len(frames['T0']) == rows_before, "min_move е изтрил редове вместо етикети"

    labelled = frames['T0']['Price_Direction'].notna().sum()
    assert labelled < rows_before, "min_move не махна нито един етикет"

    ds = pool_frames(frames, seq_length=SEQ, days_ahead=DAYS_AHEAD)
    y_all = np.concatenate([ds['y_train'], ds['y_test']])
    assert not np.isnan(y_all).any(), (
        f"{int(np.isnan(y_all).sum())} примера влязоха в модела без етикет"
    )
    assert set(np.unique(y_all)) <= {0.0, 1.0}, "етикетите не са само 0/1"
    return (f"{rows_before} реда запазени, етикети {labelled}, "
            f"примери в модела {len(y_all)}, нула NaN")


def test_min_move_makes_the_moves_bigger_not_the_rows_fewer():
    """Останалите примери наистина са дните с по-голямо движение."""
    df = make_frame(0, n=400, seed=7)
    filtered = apply_min_move(df, min_move=0.015)

    ret = (df['Future_Price'] / df['Close'] - 1.0).abs()
    kept = filtered['Price_Direction'].notna() & df['Future_Price'].notna()
    dropped = filtered['Price_Direction'].isna() & df['Future_Price'].notna()

    assert kept.sum() > 0 and dropped.sum() > 0, "филтърът не раздели данните"
    assert ret[kept].min() >= 0.015 - 1e-12, "останал е ден под прага"
    assert ret[dropped].max() < 0.015, "изхвърлен е ден над прага"
    return (f"запазени {int(kept.sum())} дни (мин. движение "
            f"{ret[kept].min()*100:.2f}%), изхвърлени {int(dropped.sum())}")


def test_pooling_actually_multiplies_the_examples():
    """
    Смисълът на цялото упражнение: повече примери.

    Сравнява един тикер срещу десет при еднакви настройки.
    """
    one = pool_frames(make_frames(k=1, n=200), seq_length=SEQ, days_ahead=DAYS_AHEAD)
    ten = pool_frames(make_frames(k=10, n=200), seq_length=SEQ, days_ahead=DAYS_AHEAD)

    ratio = len(ten['X_train']) / max(1, len(one['X_train']))
    assert ratio > 8, (
        f"10 тикера дадоха само {ratio:.1f}x повече примера от един — "
        f"очаквах близо 10x"
    )
    return f"1 тикер -> {len(one['X_train'])} примера, 10 тикера -> {len(ten['X_train'])} ({ratio:.1f}x)"


TESTS = [
    test_split_is_by_global_date,
    test_every_ticker_is_split_at_the_same_date,
    test_sequences_never_span_two_tickers,
    test_scaler_never_sees_test_rows,
    test_purge_zone_is_dropped,
    test_longer_horizon_widens_the_purge_gap,
    test_meta_rows_line_up_with_x_rows,
    test_validation_split_is_chronological,
    test_ticker_with_broken_data_is_skipped_not_fatal,
    test_min_move_drops_flat_days_from_the_middle,
    test_min_move_makes_the_moves_bigger_not_the_rows_fewer,
    test_pooling_actually_multiplies_the_examples,
]


def main():
    print("=" * 62)
    print("ПРОВЕРКА НА POOLED DATASET-А")
    print("=" * 62)
    failed = 0
    for t in TESTS:
        try:
            import io
            import contextlib
            sink = io.StringIO()
            with contextlib.redirect_stdout(sink):
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
