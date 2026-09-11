"""
Проверки на дневника с реалните прогнози.

Тук грешките са особено коварни, защото не гърмят: ако проверката вземе
цената на грешния ден, дневникът пак ще показва някакъв процент познати и
никой няма да забележи, че е измислен.

Трите неща, които се пазят:
  1. Прогноза, чийто срок още не е минал, остава непроверена — не се гадае.
  2. Проверката взема цената точно N търговски дни след прогнозата, а не
     последната налична.
  3. "Познал" се смята спрямо цената при прогнозата, не спрямо предишния ден.

Стартиране:
    python tests/test_prediction_log.py
"""

import os
import sys
import json
import tempfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pooled_dataset
import prediction_log


def fake_prices(closes, start='2026-01-05'):
    """Търговски дни с зададени цени на затваряне."""
    return pd.DataFrame({
        'Date': pd.date_range(start, periods=len(closes), freq='B', tz='UTC'),
        'Close': closes,
    })


class TempLog:
    """Временен дневник + подменено сваляне на цени."""

    def __init__(self, rows, prices):
        self.rows = rows
        self.prices = prices

    def __enter__(self):
        self.dir = tempfile.mkdtemp()
        self.old_path = prediction_log.LOG_PATH
        self.old_loader = pooled_dataset.load_price_data

        prediction_log.LOG_PATH = os.path.join(self.dir, 'predictions.jsonl')
        with open(prediction_log.LOG_PATH, 'w', encoding='utf-8') as f:
            for r in self.rows:
                f.write(json.dumps(r) + '\n')

        prices = self.prices
        pooled_dataset.load_price_data = lambda ticker, *a, **kw: prices.get(ticker)
        return self

    def __exit__(self, *exc):
        prediction_log.LOG_PATH = self.old_path
        pooled_dataset.load_price_data = self.old_loader


def make_row(ticker='AAPL', as_of='2026-01-06', close=100.0, direction='up',
             prob=0.6, days_ahead=1):
    return {
        'ticker': ticker, 'as_of': as_of, 'recorded_at': '2026-01-06T21:00:00+00:00',
        'model': 'test', 'days_ahead': days_ahead,
        'close_at_prediction': close, 'probability_up': prob,
        'predicted_direction': direction,
        'actual_close': None, 'actual_direction': None,
        'correct': None, 'resolved_at': None,
    }


def test_unresolved_when_future_has_not_arrived():
    """Последният наличен ден не може да се провери — бъдещето още го няма."""
    prices = {'AAPL': fake_prices([100.0, 101.0, 102.0])}
    last_day = str(prices['AAPL']['Date'].iloc[-1].date())
    rows = [make_row(as_of=last_day, close=102.0)]

    with TempLog(rows, prices):
        n = prediction_log.resolve_predictions()
        after = prediction_log._load_rows()

    assert n == 0, f"проверени {n} прогнози, а бъдещето още не е настъпило"
    assert after[0]['correct'] is None, "прогнозата е маркирана без реални данни"
    return "прогноза за последния ден остава непроверена"


def test_resolve_uses_the_day_n_steps_ahead_not_the_latest():
    """
    Цената се взема точно N дни напред.

    Ако се вземеше последната налична, всяка стара прогноза щеше да се
    сравнява с днешната цена и при качващ се пазар всичко щеше да излиза
    "познато".
    """
    # ден 0=100, ден 1=99 (надолу), ..., последен ден=200 (силно нагоре)
    prices = {'AAPL': fake_prices([100.0, 99.0, 98.0, 150.0, 200.0])}
    day0 = str(prices['AAPL']['Date'].iloc[0].date())
    rows = [make_row(as_of=day0, close=100.0, direction='up', days_ahead=1)]

    with TempLog(rows, prices):
        prediction_log.resolve_predictions()
        after = prediction_log._load_rows()

    assert after[0]['actual_close'] == 99.0, (
        f"взета е цена {after[0]['actual_close']}, а на следващия ден е 99.0 "
        f"(вероятно е взета последната налична — 200.0)"
    )
    assert after[0]['actual_direction'] == 'down'
    assert after[0]['correct'] is False, "прогноза 'up' при спад е отчетена като позната"
    return "взе цената на ден+1 (99.0), не последната (200.0)"


def test_correct_flag_for_both_directions():
    """И двете посоки се отчитат спрямо цената при прогнозата."""
    prices = {
        'UP': fake_prices([100.0, 105.0, 105.0]),
        'DOWN': fake_prices([100.0, 95.0, 95.0]),
    }
    day0 = str(prices['UP']['Date'].iloc[0].date())
    rows = [
        make_row(ticker='UP', as_of=day0, close=100.0, direction='up'),
        make_row(ticker='DOWN', as_of=day0, close=100.0, direction='up'),
        make_row(ticker='DOWN', as_of=day0, close=100.0, direction='down'),
    ]
    # третият ред е дубликат по (ticker, as_of) — тук нарочно, за да се види
    # че проверката работи по ред, а не по тикер
    with TempLog(rows, prices):
        prediction_log.resolve_predictions()
        after = prediction_log._load_rows()

    assert after[0]['correct'] is True, "качване, предсказано 'up' — трябва да е познато"
    assert after[1]['correct'] is False, "спад, предсказано 'up' — трябва да е сгрешено"
    assert after[2]['correct'] is True, "спад, предсказано 'down' — трябва да е познато"
    return "up/up познато, up/down сгрешено, down/down познато"


def test_longer_horizon_skips_intermediate_days():
    """При 5-дневен хоризонт се гледа петият ден, не първият."""
    prices = {'AAPL': fake_prices([100.0, 90.0, 90.0, 90.0, 90.0, 130.0, 130.0])}
    day0 = str(prices['AAPL']['Date'].iloc[0].date())
    rows = [make_row(as_of=day0, close=100.0, direction='up', days_ahead=5)]

    with TempLog(rows, prices):
        prediction_log.resolve_predictions()
        after = prediction_log._load_rows()

    assert after[0]['actual_close'] == 130.0, (
        f"взета е цена {after[0]['actual_close']}, а на ден+5 е 130.0"
    )
    assert after[0]['correct'] is True
    return "ден+5 = 130.0, междинните спадове са пропуснати правилно"


def test_scoreboard_compares_against_base_rate():
    """
    Резултатът се мери срещу базовата честота, не сам по себе си.

    Сценарий: всички 10 дни са били нагоре и моделът винаги е казвал 'up'.
    100% познати изглежда перфектно, но базовата честота също е 100% —
    edge-ът е нула. Точно това число трябва да се показва.
    """
    rows = []
    for i in range(10):
        r = make_row(as_of=f'2026-02-{i+2:02d}', close=100.0, direction='up')
        r.update({'actual_close': 105.0, 'actual_direction': 'up', 'correct': True,
                  'resolved_at': '2026-03-01T00:00:00+00:00'})
        rows.append(r)

    with TempLog(rows, {}):
        s = prediction_log.scoreboard()

    assert s['accuracy'] == 1.0, "10 от 10 познати трябва да е 100%"
    assert s['base_rate'] == 1.0, "всички дни са нагоре — базовата честота е 100%"
    assert abs(s['edge']) < 1e-9, (
        f"edge {s['edge']:.4f} при 100% точност и 100% база — трябва да е 0"
    )
    return "100% точност, 100% база, edge 0.00 — показва се честно"


def test_resolved_predictions_are_not_rechecked():
    """Веднъж проверена прогноза не се пипа повторно."""
    prices = {'AAPL': fake_prices([100.0, 105.0, 105.0])}
    day0 = str(prices['AAPL']['Date'].iloc[0].date())
    row = make_row(as_of=day0, close=100.0, direction='up')
    row.update({'actual_close': 999.0, 'actual_direction': 'up', 'correct': True,
                'resolved_at': '2026-01-07T00:00:00+00:00'})

    with TempLog([row], prices):
        n = prediction_log.resolve_predictions()
        after = prediction_log._load_rows()

    assert n == 0, "вече проверена прогноза е пипната отново"
    assert after[0]['actual_close'] == 999.0, "записаната стойност е презаписана"
    return "готовите записи остават непокътнати"


TESTS = [
    test_unresolved_when_future_has_not_arrived,
    test_resolve_uses_the_day_n_steps_ahead_not_the_latest,
    test_correct_flag_for_both_directions,
    test_longer_horizon_skips_intermediate_days,
    test_scoreboard_compares_against_base_rate,
    test_resolved_predictions_are_not_rechecked,
]


def main():
    import io
    import contextlib

    print("=" * 62)
    print("ПРОВЕРКА НА ДНЕВНИКА С ПРОГНОЗИТЕ")
    print("=" * 62)
    failed = 0
    for t in TESTS:
        try:
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
