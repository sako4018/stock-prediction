"""
Pooled (Cross-Sectional) Dataset
=================================
Един dataset от много акции наведнъж, вместо отделен модел за всеки тикер.

Защо: при един тикър и 2 години данни остават ~400 тренировъчни примера за
модел с хиляди параметри. Това е основната причина резултатите да скачат от
пускане на пускане — моделът запаметява шума на конкретната акция, а не общ
pattern. С 25 тикера по 5 години примерите стават десетки хиляди.

Защо изобщо е позволено да се смесват различни акции в един dataset:
features-ите вече са стационарни съотношения и разлики (Close_vs_SMA20,
Price_Change, RSI...), а не абсолютни цени. "+2% дневна промяна" значи
едно и също за AAPL и за KO. Ако бяхме останали при суровите цени
(AAPL на $180, KO на $60), смесването щеше да е безсмислено.

Разликата от batch_train.py: там се тренира по един отделен модел на тикер
и всеки пак вижда само своите ~400 примера. Тук е ЕДИН модел върху всички.
"""

import os
import io
import time
import contextlib
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from sklearn.preprocessing import StandardScaler

import config as cfg
import feature_pipeline
from data_collection import StockDataCollector
from preprocessing import TARGET_COLUMN, TARGET_COLUMNS, NON_STATIONARY_COLUMNS

# Ликвидни large-cap акции от различни сектори. Разнообразието е нарочно:
# ако всички бяха технологични, "общият pattern" щеше да е просто патернът
# на технологичния сектор.
DEFAULT_TICKERS = (
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'INTC', 'CSCO',
    'JPM', 'BAC', 'V', 'MA',
    'JNJ', 'UNH', 'PFE',
    'XOM', 'CVX',
    'WMT', 'HD', 'PG', 'KO',
    'DIS', 'NFLX', 'VZ',
)

PRICE_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'prices')
CACHE_MAX_AGE_HOURS = 12


def load_price_data(ticker, period, max_age_hours=CACHE_MAX_AGE_HOURS, verbose=False):
    """
    Сваля OHLCV данни с локален файлов кеш.

    При 25 тикера сваляното е най-бавната част и се повтаря при всяко
    пускане на експеримента. Кешът е на диск (CSV), защото проектът няма
    база данни, а форматът е същият, който StockDataCollector връща.
    """
    os.makedirs(PRICE_CACHE_DIR, exist_ok=True)
    path = os.path.join(PRICE_CACHE_DIR, f'{ticker.upper()}_{period}_1d.csv')

    if os.path.exists(path):
        age_hours = (time.time() - os.path.getmtime(path)) / 3600.0
        if age_hours < max_age_hours:
            try:
                df = pd.read_csv(path, parse_dates=['Date'])
                if not df.empty:
                    if verbose:
                        print(f"[CACHE] {ticker}: {len(df)} реда от кеша "
                              f"({age_hours:.1f}ч)")
                    return df
            except Exception as e:
                print(f"[CACHE][WARN] Повреден кеш за {ticker} ({e}) — пресвалям")

    collector = StockDataCollector(ticker=ticker, period=period, interval='1d')
    df = collector.fetch_stock_data(save_to_csv=False)
    if df is None or df.empty:
        return None

    try:
        df.to_csv(path, index=False)
    except Exception as e:
        print(f"[CACHE][WARN] Не можах да запиша кеша за {ticker}: {e}")
    return df


def _canonical_feature_columns(frames):
    """
    Имената на features, общи за всички тикери, в стабилен ред.

    Редът трябва да е един и същ за всеки тикер — колона 7 във входа на
    модела трябва да значи едно и също нещо независимо от акцията. Затова
    редът се взима от първия тикер, а не от set() (чийто ред е случаен).
    """
    excluded = set(['Date'] + list(TARGET_COLUMNS) + list(NON_STATIONARY_COLUMNS))
    frames_list = list(frames.values())
    first = [c for c in frames_list[0].columns if c not in excluded]

    common = set(first)
    for df in frames_list[1:]:
        common &= set(df.columns)

    ordered = [c for c in first if c in common]
    missing = [c for c in first if c not in common]
    if missing:
        print(f"[POOL][WARN] {len(missing)} колони липсват при част от "
              f"тикерите и отпадат: {missing[:6]}")
    return ordered


def pool_frames(frames, seq_length=60, days_ahead=1, train_size=0.8,
                split_date=None, feature_cols=None):
    """
    Слепва вече изградените (сурови) DataFrame-и на много тикери в един
    train/test dataset.

    Чиста функция без мрежа — цялата логика срещу leakage е тук, затова
    тестовете я викат директно със синтетични данни.

    Двете правила, които пазят от leakage:

    1. Разделянето е по ДАТА, глобално за всички тикери, не по индекс за
       всеки поотделно. Ако всеки тикер се режеше на своите 80%, тестът на
       AAPL щеше да съвпада по време с тренировката на MSFT — и моделът
       щеше да е виждал как се е държал пазарът точно в тестовия период.

    2. Всяка последователност е изцяло вътре в един тикер. Прозорците се
       строят поотделно за всеки DataFrame, така че никой вход да не
       смесва последните дни на едната акция с първите на другата.

    Purging: тренировъчен пример се брои за тренировъчен само ако и
    ЕТИКЕТЪТ му (цената след days_ahead дни) е известен до split_date.
    Примерите, чийто прозорец свършва преди split_date, но етикетът им
    пада след нея, не влизат никъде — те са "замърсената" зона.

    Параметри:
    ----------
    frames : dict[str, pandas.DataFrame]
        Тикер -> сурова таблица с Date, Close, Price_Direction + features
    seq_length, days_ahead, train_size : виж config.py
    split_date : pandas.Timestamp, optional
        Ако липсва, се избира така, че ~train_size от примерите да са преди нея
    feature_cols : list[str], optional

    Връща:
    -------
    dict: X_train, y_train, X_test, y_test, meta_train, meta_test,
          scaler, feature_names, split_date, ...
    """
    if not frames:
        raise ValueError("[POOL] Няма нито един тикер с данни")

    feature_cols = feature_cols or _canonical_feature_columns(frames)
    if not feature_cols:
        raise ValueError("[POOL] Няма общи feature колони между тикерите")

    # --- 1. Изрязваме неетикетираните редове и записваме позициите ---
    usable = {}
    for ticker, df in frames.items():
        df = df.sort_values('Date').reset_index(drop=True)
        target = df[TARGET_COLUMN].values.astype(float)
        labelled = np.flatnonzero(~np.isnan(target))
        if len(labelled) == 0:
            print(f"[POOL][WARN] {ticker}: няма нито един етикет — пропускам")
            continue

        end = labelled[-1] + 1
        if end < seq_length + days_ahead:
            print(f"[POOL][WARN] {ticker}: само {end} използваеми реда, "
                  f"трябват поне {seq_length + days_ahead} — пропускам")
            continue

        feats = df[feature_cols].to_numpy(dtype=np.float64, copy=True)
        feats[~np.isfinite(feats)] = np.nan
        bad = np.isnan(feats[:end]).any(axis=1).sum()
        if bad:
            print(f"[POOL][WARN] {ticker}: {bad} реда с липсващи стойности "
                  f"във features — пропускам тикера")
            continue

        dates = pd.to_datetime(df['Date'], utc=True).dt.tz_localize(None)
        usable[ticker] = {
            'features': feats[:end],
            'target': target[:end].astype(np.float32),
            'close': df['Close'].to_numpy(dtype=np.float64)[:end],
            'dates': dates.to_numpy()[:end],
            # Етикетът на ред i се решава от цената на ред i+days_ahead.
            # Пазим датата, защото точно тя определя кога информацията
            # реално е станала известна.
            'label_dates': dates.to_numpy()[days_ahead:end + days_ahead],
        }

    if not usable:
        raise ValueError("[POOL] Нито един тикер не остана след проверките")

    # --- 2. Глобална дата на разделяне ---
    if split_date is None:
        all_end_dates = np.concatenate([
            d['dates'][seq_length - 1:] for d in usable.values()
        ])
        all_end_dates = np.sort(all_end_dates)
        idx = min(int(len(all_end_dates) * train_size), len(all_end_dates) - 1)
        split_date = pd.Timestamp(all_end_dates[idx])
    split_date = pd.Timestamp(split_date)
    if split_date.tz is not None:
        split_date = split_date.tz_localize(None)
    split_np = np.datetime64(split_date)

    # --- 3. Скалер, научен САМО от редовете до split_date, от всички тикери ---
    train_rows = [d['features'][d['dates'] <= split_np] for d in usable.values()]
    train_rows = np.concatenate([r for r in train_rows if len(r)])
    if len(train_rows) == 0:
        raise ValueError("[POOL] Няма тренировъчни редове преди split_date")

    scaler = StandardScaler()
    scaler.fit(train_rows)

    # --- 4. Последователности, поотделно за всеки тикер ---
    Xtr, ytr, Xte, yte = [], [], [], []
    meta_tr, meta_te = [], []
    purged = 0

    for ticker, d in usable.items():
        scaled = scaler.transform(d['features']).astype(np.float32)

        # sliding_window_view връща изглед, не копие — копираме едва след
        # като изберем кои прозорци ни трябват. При 25 тикера разликата е
        # стотици мегабайта.
        windows = sliding_window_view(scaled, seq_length, axis=0).transpose(0, 2, 1)

        starts = np.arange(len(windows))
        ends = starts + seq_length - 1
        end_dates = d['dates'][ends]
        label_dates = d['label_dates'][ends]
        y = d['target'][ends]

        is_train = label_dates <= split_np
        is_test = end_dates > split_np
        purged += int((~is_train & ~is_test).sum())

        for mask, Xs, ys, metas, split_name in (
            (is_train, Xtr, ytr, meta_tr, 'train'),
            (is_test, Xte, yte, meta_te, 'test'),
        ):
            if not mask.any():
                continue
            Xs.append(np.ascontiguousarray(windows[mask]))
            ys.append(y[mask])
            metas.append(pd.DataFrame({
                'ticker': ticker,
                'end_date': end_dates[mask],
                'label_date': label_dates[mask],
                'close': d['close'][ends][mask],
                'y': y[mask],
                'split': split_name,
            }))

    if not Xtr or not Xte:
        raise ValueError("[POOL] Разделянето остави празен train или test — "
                         "пробвай по-дълъг период или друга split_date")

    X_train = np.concatenate(Xtr)
    y_train = np.concatenate(ytr)
    X_test = np.concatenate(Xte)
    y_test = np.concatenate(yte)
    # Редът на meta трябва да съвпада ред по ред с X — meta[i] описва X[i].
    # Затова НЕ се сортира по дата: X се слепва по тикери, и сортиране само
    # на meta щеше тихо да разбърка съответствието (предсказание за AAPL
    # щеше да се отчете като предсказание за KO).
    meta_train = pd.concat(meta_tr, ignore_index=True)
    meta_test = pd.concat(meta_te, ignore_index=True)

    mb = (X_train.nbytes + X_test.nbytes) / 1024 ** 2
    print(f"\n[POOL] Тикери: {len(usable)} | features: {len(feature_cols)} | "
          f"seq_length: {seq_length}")
    print(f"[POOL] Split дата: {split_date.date()}")
    print(f"[POOL] Train: {len(X_train)} примера "
          f"({meta_train['end_date'].min().date()} -> {meta_train['end_date'].max().date()})")
    print(f"[POOL] Test:  {len(X_test)} примера "
          f"({meta_test['end_date'].min().date()} -> {meta_test['end_date'].max().date()})")
    print(f"[POOL] Изхвърлени в purge зоната: {purged}")
    print(f"[POOL] Базова честота нагоре — train {y_train.mean()*100:.1f}%, "
          f"test {y_test.mean()*100:.1f}%")
    print(f"[POOL] Памет за X: {mb:.0f} MB")

    return {
        'X_train': X_train, 'y_train': y_train,
        'X_test': X_test, 'y_test': y_test,
        'meta_train': meta_train, 'meta_test': meta_test,
        'scaler': scaler,
        'feature_names': feature_cols,
        'split_date': split_date,
        'seq_length': seq_length,
        'days_ahead': days_ahead,
        'tickers': sorted(usable.keys()),
        'n_purged': purged,
    }


def build_pooled_dataset(tickers=None, period='5y', feature_groups=None,
                         seq_length=None, days_ahead=None, train_size=0.8,
                         split_date=None, verbose=False):
    """
    Сваля данните за всички тикери, построява суровите таблици и ги слепва.

    Тикер, който гръмне (няма данни, твърде къса история, мрежова грешка),
    се пропуска с предупреждение — един проблемен символ не бива да убива
    целия експеримент.
    """
    tickers = tuple(tickers or DEFAULT_TICKERS)
    seq_length = seq_length or cfg.SEQUENCE_LENGTH
    days_ahead = days_ahead or cfg.PREDICTION_HORIZON_DAYS
    feature_groups = tuple(feature_groups or cfg.DEFAULT_FEATURE_GROUPS)

    print(f"[POOL] Изграждане на общ dataset от {len(tickers)} тикера "
          f"(период {period}, групи {feature_groups})")

    frames = {}
    failed = []
    for i, ticker in enumerate(tickers, 1):
        try:
            price = load_price_data(ticker, period, verbose=verbose)
            if price is None or price.empty:
                failed.append((ticker, 'няма данни'))
                continue

            # build_raw_frame печата десетки реда на тикер — при 25 тикера
            # това затрупва конзолата, а полезното е само обобщението.
            sink = io.StringIO()
            ctx = contextlib.nullcontext() if verbose else contextlib.redirect_stdout(sink)
            with ctx:
                preprocessor, _ = feature_pipeline.build_raw_frame(
                    ticker, period=period, feature_groups=feature_groups,
                    days_ahead=days_ahead, price_data=price,
                )
            frames[ticker] = preprocessor.data
            print(f"[POOL] [{i}/{len(tickers)}] {ticker}: {len(preprocessor.data)} реда")
        except Exception as e:
            failed.append((ticker, str(e)[:80]))
            print(f"[POOL][WARN] [{i}/{len(tickers)}] {ticker} пропуснат: {e}")

    if failed:
        print(f"[POOL][WARN] {len(failed)} тикера пропуснати: "
              f"{', '.join(t for t, _ in failed)}")
    if not frames:
        raise ValueError("[POOL] Нито един тикер не се свали успешно")

    result = pool_frames(frames, seq_length=seq_length, days_ahead=days_ahead,
                         train_size=train_size, split_date=split_date)
    result['failed'] = failed
    result['period'] = period
    result['feature_groups'] = feature_groups
    return result


def split_train_val(dataset, val_fraction=0.15):
    """
    Реже последната част от тренировъчните примери за валидация.

    Разделянето пак е по дата, не случайно: валидацията трябва да е
    "по-късна" от тренировката, иначе early stopping-ът се настройва по
    период, който моделът вече е виждал, и спира твърде късно.
    """
    meta = dataset['meta_train']
    # meta е подредена по тикер (за да съвпада с X), не по дата — затова
    # границата се взима от сортирано копие, а маската се прилага върху
    # оригиналния ред.
    ordered = np.sort(meta['end_date'].to_numpy())
    cut = min(max(1, int(len(ordered) * (1 - val_fraction))), len(ordered) - 1)
    val_start_date = ordered[cut]

    is_val = (meta['end_date'].to_numpy() >= val_start_date)
    X, y = dataset['X_train'], dataset['y_train']
    return X[~is_val], y[~is_val], X[is_val], y[is_val]


if __name__ == "__main__":
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    period = sys.argv[2] if len(sys.argv) > 2 else '2y'

    ds = build_pooled_dataset(tickers=DEFAULT_TICKERS[:n], period=period)
    print(f"\nX_train: {ds['X_train'].shape}  X_test: {ds['X_test'].shape}")
    print(f"Тикери: {ds['tickers']}")
