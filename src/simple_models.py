"""
Прости модели върху същите pooled данни
========================================
Логистична регресия и gradient boosting срещу LSTM-а, на абсолютно същия
dataset, същото разделяне по дата и същия скалер.

Защо това е най-важният тест от плана: LSTM-ът излезе с edge 0.00 и на 5, и
на 10 години. Това има точно два възможни отговора и те искат различни
следващи стъпки:

  - Ако и простите модели дадат 0 — в цена+технически индикатори няма сигнал
    за посоката на следващия ден. Тогава смяната на мрежата е губене на време
    и трябва да се сменя целта или данните.
  - Ако gradient boosting намери нещо — сигналът съществува, а LSTM-ът просто
    не го изважда. Тогава се работи по модела.

Входът за таблични модели е ПОСЛЕДНИЯТ ден от всеки прозорец, не целият
прозорец. Технически индикаторите (RSI, SMA съотношения, ROC) вече носят
историята в себе си — разстилането на 60 дни × 37 колони би дало 2220
features срещу 20 000 примера, което е сигурен път към преучване.
"""

import os
import json
from datetime import datetime

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier

import pooled_dataset
import pooled_train


def last_day_features(X):
    """Последният ден от всеки прозорец: (n, seq, feat) -> (n, feat)."""
    return X[:, -1, :]


def lagged_features(X, lags=(0, 1, 4, 9, 19)):
    """
    Последният ден плюс няколко по-ранни дни от прозореца.

    Компромис между "само днес" и целия прозорец: дава на модела известна
    история, без да го залива с 2220 колони.
    """
    idx = [X.shape[1] - 1 - lag for lag in lags if lag < X.shape[1]]
    return np.concatenate([X[:, i, :] for i in idx], axis=1)


def build_models(seed=42):
    """
    Моделите за сравнение.

    DummyClassifier не е излишен: той е "винаги предсказвай мнозинството" в
    код. Ако някой друг модел не го бие, това се вижда веднага, вместо да се
    смята наум от базовата честота.
    """
    return {
        'dummy_majority': DummyClassifier(strategy='most_frequent'),
        'logistic': LogisticRegression(max_iter=2000, C=0.1, random_state=seed),
        'gradient_boosting': HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.05, max_depth=4,
            l2_regularization=1.0, early_stopping=True,
            validation_fraction=0.15, random_state=seed,
        ),
    }


def run(tickers=None, period='5y', feature_groups=None, seq_length=None,
        days_ahead=None, train_size=0.8, use_lags=False, seed=42,
        label_prefix='', verbose=False):
    """
    Строи pooled dataset-а веднъж и пуска всички прости модели върху него.

    Dataset-ът се строи един път нарочно — ако всеки модел си го строеше сам,
    най-малката разлика в split-а прави числата несравними.
    """
    ds = pooled_dataset.build_pooled_dataset(
        tickers=tickers, period=period, feature_groups=feature_groups,
        seq_length=seq_length, days_ahead=days_ahead, train_size=train_size,
        verbose=verbose,
    )

    shape_fn = lagged_features if use_lags else last_day_features
    X_train = shape_fn(ds['X_train'])
    X_test = shape_fn(ds['X_test'])
    y_train, y_test = ds['y_train'], ds['y_test']

    print(f"\n[SIMPLE] Вход за табличните модели: {X_train.shape[1]} колони "
          f"({'последен ден + лагове' if use_lags else 'само последния ден'})")

    results = {}
    for name, model in build_models(seed).items():
        print(f"\n[SIMPLE] Тренировка: {name}...")
        model.fit(X_train, y_train)

        if hasattr(model, 'predict_proba'):
            probs = model.predict_proba(X_test)[:, 1]
        else:
            probs = model.predict(X_test).astype(float)

        evaluation = pooled_train.evaluate_pooled(probs, y_test, ds['meta_test'])
        result = {
            'created_at': datetime.now().isoformat(timespec='seconds'),
            'model_name': name,
            'model_type': name,
            'tickers': ds['tickers'],
            'period': period,
            'feature_groups': list(ds['feature_groups']),
            'n_features': X_train.shape[1],
            'seq_length': ds['seq_length'],
            'days_ahead': ds['days_ahead'],
            'n_train': int(len(X_train)),
            'n_val': 0,
            'n_purged': ds['n_purged'],
            'n_parameters': None,
            'split_date': str(ds['split_date'].date()),
            'test_from': str(ds['meta_test']['end_date'].min().date()),
            'test_to': str(ds['meta_test']['end_date'].max().date()),
            'evaluation': evaluation,
        }
        results[name] = result

        suffix = '+lags' if use_lags else ''
        pooled_train.log_experiment(
            result, label=f"{label_prefix}{name}{suffix} {period}")

        print(f"[SIMPLE] {name}: точност {evaluation['accuracy']*100:.2f}% | "
              f"база {evaluation['base_rate']*100:.2f}% | "
              f"edge {evaluation['edge']*100:+.2f} пункта")

    print_verdict(results)
    return results


def print_verdict(results):
    """Отговорът на въпроса, заради който съществува този файл."""
    print("\n" + "=" * 62)
    print("ИМА ЛИ ИЗОБЩО СИГНАЛ В ТЕЗИ FEATURES?")
    print("=" * 62)
    for name, r in results.items():
        ev = r['evaluation']
        print(f"{name:<20} точност {ev['accuracy']*100:6.2f}%  "
              f"edge {ev['edge']*100:+6.2f} пункта")

    best = max(
        (r for n, r in results.items() if n != 'dummy_majority'),
        key=lambda r: r['evaluation']['edge'],
    )
    best_edge = best['evaluation']['edge']
    n_test = best['evaluation']['n_test']
    # Груба граница на шума: стандартната грешка на дял при n теста.
    noise = 1.96 * np.sqrt(0.25 / n_test)

    print(f"\nГраница на шума при {n_test} теста: ±{noise*100:.2f} пункта")
    print("-" * 62)
    if best_edge > noise:
        print(f"ИМА сигнал: {best['model_name']} дава {best_edge*100:+.2f} пункта,")
        print("което е над шума. Значи проблемът е бил в модела, не в данните —")
        print("следващата работа е по модела.")
    else:
        print(f"НЯМА откриваем сигнал: най-доброто е {best_edge*100:+.2f} пункта,")
        print(f"в рамките на шума (±{noise*100:.2f}). Нито линеен, нито дървесен")
        print("модел намира повече от LSTM-а. Значи не мрежата е проблемът —")
        print("посоката на следващия ден просто не се чете от тези features.")
        print("Следващата стъпка е да се смени ЦЕЛТА, не моделът.")
    print("=" * 62)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description='Прости модели върху pooled данните')
    p.add_argument('--period', default='5y')
    p.add_argument('--days-ahead', type=int, default=None)
    p.add_argument('--seq-length', type=int, default=None)
    p.add_argument('--groups', default=None)
    p.add_argument('--lags', action='store_true', help='добави и по-ранни дни от прозореца')
    p.add_argument('--label-prefix', default='')
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args()

    run(period=args.period, days_ahead=args.days_ahead, seq_length=args.seq_length,
        feature_groups=args.groups.split(',') if args.groups else None,
        use_lags=args.lags, label_prefix=args.label_prefix, verbose=args.verbose)
