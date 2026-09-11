"""
Дневник на прогнозите
=====================
Записва какво моделът е предсказал днес и след N дни проверява познал ли е.

Защо това е по-силна проверка от всеки backtest: тук няма как да се
надникне в бъдещето, защото бъдещето още не е настъпило. Всяка грешка в
pipeline-а, всяко тихо изтичане на данни, всяко пренастройване към
историята — всичко това се вижда веднага, щом реалните дни почнат да
идват.

Как работи:
  1. record_predictions() — веднъж на ден, след затваряне на борсата.
     Записва по един ред на тикер в data/predictions.jsonl: дата, цена,
     вероятност, посока. Етикетът остава празен.
  2. resolve_predictions() — сваля реалните цени и попълва етикета на
     всички прогнози, чийто срок вече е минал.
  3. print_scoreboard() — натрупаният резултат, пак срещу базовата честота.

Заради pooled модела на ден излизат ~25 прогнози, не една. За месец това са
~500 реални проверки — достатъчно, за да се различи 50% от 55%. С един
тикер щяха да са 20 и нямаше да значат нищо.
"""

import os
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config as cfg
import pooled_dataset
import feature_pipeline
from model import StockPredictionModel

LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'predictions.jsonl')


def _load_rows():
    if not os.path.exists(LOG_PATH):
        return []
    rows = []
    with open(LOG_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_rows(rows):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    tmp = LOG_PATH + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    os.replace(tmp, LOG_PATH)


def record_predictions(model_name='pooled_model', tickers=None, period='1y',
                       feature_groups=None, verbose=False):
    """
    Прогноза за всеки тикер от последния наличен ден и запис в дневника.

    Скалерът се взима от записания модел, не се тренира наново — иначе
    входовете щяха да са в друга скала от тази, в която моделът е учил, и
    прогнозата нямаше да значи нищо.
    """
    model = StockPredictionModel()
    model.load_model(model_name)
    scaler = model.scaler
    feature_cols = list(model.scaler_columns)
    seq_length = model.sequence_length

    tickers = tuple(tickers or pooled_dataset.DEFAULT_TICKERS)
    feature_groups = tuple(feature_groups or cfg.DEFAULT_FEATURE_GROUPS)

    existing = _load_rows()
    seen = {(r['ticker'], r['as_of']) for r in existing}

    new_rows = []
    skipped = []
    for ticker in tickers:
        try:
            price = pooled_dataset.load_price_data(ticker, period, verbose=verbose)
            if price is None or price.empty:
                skipped.append((ticker, 'няма данни'))
                continue

            import io
            import contextlib
            sink = io.StringIO()
            ctx = contextlib.nullcontext() if verbose else contextlib.redirect_stdout(sink)
            with ctx:
                preprocessor, _ = feature_pipeline.build_raw_frame(
                    ticker, period=period, feature_groups=feature_groups,
                    days_ahead=cfg.PREDICTION_HORIZON_DAYS, price_data=price,
                )
            df = preprocessor.data

            missing = [c for c in feature_cols if c not in df.columns]
            if missing:
                skipped.append((ticker, f'липсват колони: {missing[:3]}'))
                continue
            if len(df) < seq_length:
                skipped.append((ticker, f'само {len(df)} реда'))
                continue

            # Последният ред е днес. Той няма етикет (утре още не е било) —
            # точно от него се прави прогнозата.
            window = df[feature_cols].to_numpy(dtype=np.float64)[-seq_length:]
            if not np.isfinite(window).all():
                skipped.append((ticker, 'липсващи стойности в последните дни'))
                continue

            X = scaler.transform(window).astype(np.float32)[None, :, :]
            prob = float(model.predict(X).ravel()[0])

            as_of = pd.Timestamp(df['Date'].iloc[-1]).tz_localize(None).date().isoformat()
            if (ticker, as_of) in seen:
                skipped.append((ticker, f'вече записан за {as_of}'))
                continue

            new_rows.append({
                'ticker': ticker,
                'as_of': as_of,
                'recorded_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'model': model_name,
                'days_ahead': cfg.PREDICTION_HORIZON_DAYS,
                'close_at_prediction': float(df['Close'].iloc[-1]),
                'probability_up': prob,
                'predicted_direction': 'up' if prob >= 0.5 else 'down',
                # Попълва се по-късно от resolve_predictions()
                'actual_close': None,
                'actual_direction': None,
                'correct': None,
                'resolved_at': None,
            })
        except Exception as e:
            skipped.append((ticker, str(e)[:60]))

    if new_rows:
        _write_rows(existing + new_rows)

    print(f"[LOG] Записани {len(new_rows)} нови прогнози")
    for r in sorted(new_rows, key=lambda x: -x['probability_up'])[:5]:
        print(f"   {r['ticker']:<6} {r['predicted_direction']:<5} "
              f"{r['probability_up']*100:5.1f}%  (от {r['as_of']}, "
              f"цена {r['close_at_prediction']:.2f})")
    if skipped:
        print(f"[LOG] Пропуснати {len(skipped)}: "
              f"{', '.join(f'{t} ({why})' for t, why in skipped[:4])}"
              f"{' ...' if len(skipped) > 4 else ''}")
    return new_rows


def resolve_predictions(period='6mo', verbose=False):
    """
    Попълва реалния изход на прогнозите, чийто срок е минал.

    Търси се цената на първия търговски ден, който е поне days_ahead
    търговски дни след прогнозата. Ако борсата още не е стигнала дотам,
    прогнозата просто остава неразрешена — не се гадае.
    """
    rows = _load_rows()
    pending = [r for r in rows if r.get('correct') is None]
    if not pending:
        print("[LOG] Няма неразрешени прогнози")
        return 0

    by_ticker = {}
    for r in pending:
        by_ticker.setdefault(r['ticker'], []).append(r)

    resolved = 0
    for ticker, items in by_ticker.items():
        price = pooled_dataset.load_price_data(ticker, period, max_age_hours=1,
                                               verbose=verbose)
        if price is None or price.empty:
            print(f"[LOG][WARN] {ticker}: няма данни за проверка")
            continue

        dates = pd.to_datetime(price['Date'], utc=True).dt.tz_localize(None)
        dates = dates.dt.normalize().to_numpy()
        closes = price['Close'].to_numpy(dtype=float)

        for r in items:
            as_of = np.datetime64(pd.Timestamp(r['as_of']))
            pos = np.flatnonzero(dates == as_of)
            if len(pos) == 0:
                continue
            target = int(pos[0]) + int(r['days_ahead'])
            if target >= len(closes):
                continue  # бъдещето още не е настъпило

            actual = float(closes[target])
            went_up = actual > r['close_at_prediction']
            r['actual_close'] = actual
            r['actual_direction'] = 'up' if went_up else 'down'
            r['correct'] = bool(r['predicted_direction'] == r['actual_direction'])
            r['resolved_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
            resolved += 1

    if resolved:
        _write_rows(rows)
    print(f"[LOG] Проверени {resolved} прогнози "
          f"({len(pending) - resolved} още чакат бъдещето)")
    return resolved


def scoreboard():
    """Числата от дневника, без разкрасяване."""
    rows = [r for r in _load_rows() if r.get('correct') is not None]
    if not rows:
        return None

    df = pd.DataFrame(rows)
    up_rate = (df['actual_direction'] == 'up').mean()
    base_rate = max(up_rate, 1 - up_rate)
    accuracy = df['correct'].mean()
    n = len(df)
    noise = 1.96 * np.sqrt(0.25 / n)

    by_ticker = (df.groupby('ticker')
                 .agg(n=('correct', 'size'), accuracy=('correct', 'mean'))
                 .sort_values('accuracy', ascending=False)
                 .reset_index())

    confident = df[(df['probability_up'] >= 0.55) | (df['probability_up'] <= 0.45)]

    return {
        'n': int(n),
        'accuracy': float(accuracy),
        'base_rate': float(base_rate),
        'edge': float(accuracy - base_rate),
        'noise_margin': float(noise),
        'first_date': str(df['as_of'].min()),
        'last_date': str(df['as_of'].max()),
        'pending': int(sum(1 for r in _load_rows() if r.get('correct') is None)),
        'by_ticker': by_ticker.to_dict('records'),
        'confident_n': int(len(confident)),
        'confident_accuracy': float(confident['correct'].mean()) if len(confident) else None,
    }


def print_scoreboard():
    s = scoreboard()
    if s is None:
        pending = sum(1 for r in _load_rows() if r.get('correct') is None)
        print(f"[LOG] Още няма проверена прогноза ({pending} чакат). "
              f"Пусни отново след няколко търговски дни.")
        return

    print("\n" + "=" * 62)
    print("РЕЗУЛТАТ ОТ РЕАЛНИТЕ ПРОГНОЗИ")
    print("=" * 62)
    print(f"Период:          {s['first_date']} -> {s['last_date']}")
    print(f"Проверени:       {s['n']} прогнози ({s['pending']} още чакат)")
    print(f"Познати:         {s['accuracy']*100:.2f}%")
    print(f"Базова честота:  {s['base_rate']*100:.2f}%")
    print(f"EDGE:            {s['edge']*100:+.2f} пункта")
    print(f"Граница на шума: ±{s['noise_margin']*100:.2f} пункта при {s['n']} проверки")

    if s['confident_accuracy'] is not None:
        print(f"\nСамо уверените (над 55% или под 45%): {s['confident_n']} прогнози, "
              f"{s['confident_accuracy']*100:.2f}% познати")

    print("-" * 62)
    if s['n'] < 100:
        need = 100 - s['n']
        print(f"Още рано за извод. Трябват поне ~100 проверки (още {need}),")
        print("иначе границата на шума е по-голяма от всичко, което ще видиш.")
    elif s['edge'] > s['noise_margin']:
        print(f"Моделът бие базовата честота с {s['edge']*100:.2f} пункта,")
        print(f"над границата на шума. Това е реален резултат на живи данни.")
    else:
        print(f"Edge {s['edge']*100:+.2f} при граница на шума ±{s['noise_margin']*100:.2f}")
        print("— в рамките на случайното. Моделът още не показва предимство.")
    print("=" * 62)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description='Дневник на реалните прогнози')
    p.add_argument('--record', action='store_true', help='запиши днешните прогнози')
    p.add_argument('--resolve', action='store_true', help='провери миналите прогнози')
    p.add_argument('--scoreboard', action='store_true', help='покажи резултата')
    p.add_argument('--daily', action='store_true',
                   help='всичко наведнъж: провери, запиши, покажи (за ежедневно пускане)')
    p.add_argument('--model', default='pooled_model')
    p.add_argument('--tickers', default=None)
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args()

    tickers = args.tickers.split(',') if args.tickers else None

    if args.daily or args.resolve:
        resolve_predictions(verbose=args.verbose)
    if args.daily or args.record:
        record_predictions(model_name=args.model, tickers=tickers, verbose=args.verbose)
    if args.daily or args.scoreboard or not any(
            [args.record, args.resolve, args.scoreboard]):
        print_scoreboard()
