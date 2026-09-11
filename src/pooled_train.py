"""
Pooled Training
===============
Тренира ЕДИН модел върху общия dataset от много акции (pooled_dataset.py)
и го оценява честно срещу базовата честота.

Какво значи "честно" тук: точност от 54% звучи добре, но ако през тестовия
период 54% от дните така или иначе са били нагоре, моделът не е научил
нищо — същото се постига с "винаги казвай нагоре". Затова навсякъде се
показва edge = точност - базова честота. Той е истинският резултат.

Архитектурата нарочно остава същата като при модела за един тикер. Целта
на тази стъпка е да се измери ефектът САМО от повечето данни; ако едновременно
с това се смени и мрежата, не се знае кое какво е донесло.
"""

import os
import json
from datetime import datetime

import numpy as np
import torch

import config as cfg
import pooled_dataset
from model import StockPredictionModel

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
RESULTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'pooled_results.json')

# Всяко пускане се добавя тук, а не презаписва предишното. Иначе сравнението
# между вариантите (точка 5) се прави по число, което някой си спомня, а
# спомнените числа винаги излизат по-добри, отколкото са били.
EXPERIMENTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiments.jsonl')

# Прагове на увереност. Моделът не е длъжен да търгува всеки ден — ако
# познава по-добре тогава, когато е по-уверен, това се вижда тук.
CONFIDENCE_THRESHOLDS = (0.50, 0.55, 0.60)


def evaluate_pooled(probs, y_true, meta, thresholds=CONFIDENCE_THRESHOLDS):
    """
    Оценка на тестовите предсказания.

    Връща речник с обща точност, базова честота, edge, и същото по
    прагове на увереност и по тикер.
    """
    probs = np.asarray(probs).ravel()
    y_true = np.asarray(y_true).ravel()

    base_rate = max(y_true.mean(), 1 - y_true.mean())
    preds = (probs >= 0.5).astype(float)
    accuracy = float((preds == y_true).mean())

    by_threshold = []
    for thr in thresholds:
        # Търгуваме само когато моделът е уверен в някоя от двете посоки.
        confident = (probs >= thr) | (probs <= 1 - thr)
        n = int(confident.sum())
        if n == 0:
            by_threshold.append({'threshold': thr, 'n': 0, 'accuracy': None,
                                 'base_rate': None, 'edge': None, 'coverage': 0.0})
            continue
        sub_y = y_true[confident]
        sub_acc = float((preds[confident] == sub_y).mean())
        sub_base = float(max(sub_y.mean(), 1 - sub_y.mean()))
        by_threshold.append({
            'threshold': thr, 'n': n,
            'accuracy': sub_acc, 'base_rate': sub_base,
            'edge': sub_acc - sub_base,
            'coverage': n / len(y_true),
        })

    by_ticker = []
    for ticker, grp in meta.groupby('ticker'):
        idx = grp.index.to_numpy()
        sub_y = y_true[idx]
        sub_acc = float((preds[idx] == sub_y).mean())
        sub_base = float(max(sub_y.mean(), 1 - sub_y.mean()))
        by_ticker.append({'ticker': ticker, 'n': len(idx), 'accuracy': sub_acc,
                          'base_rate': sub_base, 'edge': sub_acc - sub_base})
    by_ticker.sort(key=lambda r: r['edge'], reverse=True)

    return {
        'n_test': int(len(y_true)),
        'accuracy': accuracy,
        'base_rate': float(base_rate),
        'edge': accuracy - float(base_rate),
        'mean_prob': float(probs.mean()),
        'prob_std': float(probs.std()),
        'by_threshold': by_threshold,
        'by_ticker': by_ticker,
    }


def log_experiment(result, label):
    """Добавя един ред към дневника на експериментите."""
    ev = result['evaluation']
    row = {
        'label': label,
        'created_at': result['created_at'],
        'model': result.get('model_type', 'lstm'),
        'period': result['period'],
        'n_tickers': len(result['tickers']),
        'feature_groups': result['feature_groups'],
        'seq_length': result['seq_length'],
        'days_ahead': result['days_ahead'],
        'n_train': result['n_train'],
        'n_test': ev['n_test'],
        'test_from': result['test_from'],
        'test_to': result['test_to'],
        'accuracy': round(ev['accuracy'], 4),
        'base_rate': round(ev['base_rate'], 4),
        'edge': round(ev['edge'], 4),
        'prob_std': round(ev['prob_std'], 4),
        'tickers_with_positive_edge': sum(1 for r in ev['by_ticker'] if r['edge'] > 0),
    }
    os.makedirs(os.path.dirname(EXPERIMENTS_PATH), exist_ok=True)
    with open(EXPERIMENTS_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')


def load_experiments():
    """Чете дневника. Връща празен списък, ако още няма пуснат експеримент."""
    if not os.path.exists(EXPERIMENTS_PATH):
        return []
    rows = []
    with open(EXPERIMENTS_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def print_experiments():
    """Всички пускания досега, едно на ред, сортирани по edge."""
    rows = load_experiments()
    if not rows:
        print("[EXP] Още няма записани експерименти")
        return

    print("\n" + "=" * 96)
    print("ДНЕВНИК НА ЕКСПЕРИМЕНТИТЕ (реални числа, не оценки)")
    print("=" * 96)
    print(f"{'вариант':<26} {'модел':<10} {'период':<7} {'цел':>4} "
          f"{'train':>7} {'test':>6} {'точност':>8} {'база':>7} {'EDGE':>8}")
    print("-" * 96)
    for r in sorted(rows, key=lambda x: x['edge'], reverse=True):
        print(f"{r['label'][:25]:<26} {r.get('model','lstm')[:9]:<10} "
              f"{r['period']:<7} {r['days_ahead']:>3}д "
              f"{r['n_train']:>7} {r['n_test']:>6} "
              f"{r['accuracy']*100:>7.2f}% {r['base_rate']*100:>6.2f}% "
              f"{r['edge']*100:>+7.2f}")
    print("=" * 96)


def print_report(result):
    """Чете се отгоре надолу: колко данни, какво излезе, струва ли си."""
    ev = result['evaluation']
    print("\n" + "=" * 62)
    print("РЕЗУЛТАТ ОТ POOLED МОДЕЛА")
    print("=" * 62)
    print(f"Тикери:          {len(result['tickers'])}")
    print(f"Тренировка:      {result['n_train']} примера")
    print(f"Валидация:       {result['n_val']} примера")
    print(f"Тест:            {ev['n_test']} примера ({result['test_from']} -> {result['test_to']})")
    print(f"Параметри:       {result['n_parameters']}")
    print()
    print(f"Точност:         {ev['accuracy']*100:.2f}%")
    print(f"Базова честота:  {ev['base_rate']*100:.2f}%  (винаги предсказвай мнозинството)")
    print(f"EDGE:            {ev['edge']*100:+.2f} процентни пункта")
    print()
    print("По увереност:")
    for row in ev['by_threshold']:
        if row['n'] == 0:
            print(f"  праг {row['threshold']:.2f}: няма достатъчно уверени предсказания")
            continue
        print(f"  праг {row['threshold']:.2f}: {row['n']:5d} предсказания "
              f"({row['coverage']*100:4.1f}% от дните) | точност {row['accuracy']*100:5.2f}% | "
              f"edge {row['edge']*100:+5.2f} пункта")

    best = ev['by_ticker'][:3]
    worst = ev['by_ticker'][-3:]
    print("\nНай-добри тикери: " + ", ".join(f"{r['ticker']} {r['edge']*100:+.1f}" for r in best))
    print("Най-лоши тикери:  " + ", ".join(f"{r['ticker']} {r['edge']*100:+.1f}" for r in worst))

    positive = sum(1 for r in ev['by_ticker'] if r['edge'] > 0)
    print(f"\nТикери с положителен edge: {positive} от {len(ev['by_ticker'])}")
    print("=" * 62)

    if ev['edge'] <= 0:
        print("ИЗВОД: моделът не бие базовата честота. Повече данни сами по себе")
        print("си не стигат — следващите стъпки (по-дълга история, прост модел,")
        print("по-лесна цел) трябва да покажат дали изобщо има сигнал.")
    elif ev['edge'] < 0.01:
        print("ИЗВОД: edge под 1 пункт е в границите на шума при този брой")
        print("тестови примери. Не го приемай за реално предимство още.")
    else:
        print(f"ИЗВОД: edge от {ev['edge']*100:.2f} пункта върху {ev['n_test']} теста.")
        print("Точка 6 (дневен дневник на прогнозите) ще покаже дали се държи и напред.")
    print("=" * 62)


def train_pooled(tickers=None, period='5y', feature_groups=None, seq_length=None,
                 days_ahead=None, epochs=40, batch_size=128, train_size=0.8,
                 lstm_units=(32, 16, 8), dropout_rate=0.2, seed=42,
                 save_as='pooled_model', label=None, verbose=False):
    """
    Пълният цикъл: данни -> тренировка -> честна оценка -> запис.

    batch_size е 128, а не 32 както при единичния тикер: при 20 000+ примера
    по-големите batch-ове са и по-бързи, и по-стабилни в градиента.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    ds = pooled_dataset.build_pooled_dataset(
        tickers=tickers, period=period, feature_groups=feature_groups,
        seq_length=seq_length, days_ahead=days_ahead, train_size=train_size,
        verbose=verbose,
    )

    X_tr, y_tr, X_val, y_val = pooled_dataset.split_train_val(ds)
    print(f"[POOL] Тренировка {len(X_tr)} / валидация {len(X_val)} (по дата)")

    model = StockPredictionModel(sequence_length=ds['seq_length'],
                                 n_features=len(ds['feature_names']))
    model.build_lstm_model(lstm_units=list(lstm_units), dropout_rate=dropout_rate)
    n_params = sum(p.numel() for p in model.model.parameters())

    model.train_model(X_tr, y_tr, X_val, y_val, epochs=epochs, batch_size=batch_size)

    probs = model.predict(ds['X_test'])
    evaluation = evaluate_pooled(probs, ds['y_test'], ds['meta_test'])

    model.save_model(save_as, scaler=ds['scaler'], feature_columns=ds['feature_names'])

    result = {
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'model_name': save_as,
        'tickers': ds['tickers'],
        'period': period,
        'feature_groups': list(ds['feature_groups']),
        'n_features': len(ds['feature_names']),
        'seq_length': ds['seq_length'],
        'days_ahead': ds['days_ahead'],
        'n_train': int(len(X_tr)),
        'n_val': int(len(X_val)),
        'n_purged': ds['n_purged'],
        'n_parameters': int(n_params),
        'split_date': str(ds['split_date'].date()),
        'test_from': str(ds['meta_test']['end_date'].min().date()),
        'test_to': str(ds['meta_test']['end_date'].max().date()),
        'evaluation': evaluation,
    }

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    log_experiment(result, label=label or save_as)
    print(f"[SAVE] Резултатите са записани в {RESULTS_PATH}")

    print_report(result)
    return result


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description='Тренира един модел върху много акции')
    p.add_argument('--tickers', default=None,
                   help='Списък, разделен със запетая (по подразбиране 25-те от pooled_dataset)')
    p.add_argument('--period', default='5y')
    p.add_argument('--epochs', type=int, default=40)
    p.add_argument('--batch-size', type=int, default=128)
    p.add_argument('--seq-length', type=int, default=None)
    p.add_argument('--days-ahead', type=int, default=None)
    p.add_argument('--groups', default=None, help='напр. price,technical,market')
    p.add_argument('--name', default='pooled_model')
    p.add_argument('--label', default=None, help='име на реда в дневника на експериментите')
    p.add_argument('--show-log', action='store_true', help='само покажи дневника и излез')
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args()

    if args.show_log:
        print_experiments()
        raise SystemExit(0)

    train_pooled(
        tickers=args.tickers.split(',') if args.tickers else None,
        period=args.period,
        feature_groups=args.groups.split(',') if args.groups else None,
        seq_length=args.seq_length,
        days_ahead=args.days_ahead,
        epochs=args.epochs,
        batch_size=args.batch_size,
        save_as=args.name,
        label=args.label,
        verbose=args.verbose,
    )
