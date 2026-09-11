"""
Ablation / Backtest Comparison Module
=======================================
Сравнява Buy & Hold срещу ML модела с различни комбинации от feature
групи — целта е да се отговори честно: помагат ли новините/пазарните
данни/фундаменталите на модела, или само добавят шум?

Скоростен компромис (обяснен изрично на потребителя): за таблицата с 6
варианта ползваме ЕДИНИЧЕН train/test split (StockBacktester), не пълен
WalkForwardValidator за всеки вариант — 6 варианта x 4 fold-а x 30 епохи
би отнело многократно повече време. За по-надеждна финална оценка на
най-добрия вариант ('ML+All'), пускай main.py --walkforward отделно.
"""

import pandas as pd

from feature_pipeline import build_dataset
from model import StockPredictionModel
from backtest import StockBacktester

ABLATION_VARIANTS = [
    ('ML (price+technical)', ('price', 'technical')),
    ('ML+Market', ('price', 'technical', 'market')),
    ('ML+News', ('price', 'technical', 'news')),
    ('ML+Fundamentals', ('price', 'technical', 'fundamental')),
    ('ML+All', ('price', 'technical', 'market', 'news', 'fundamental')),
]


def _train_and_backtest(ticker, period, feature_groups, epochs, initial_capital):
    result = build_dataset(ticker, period=period, feature_groups=feature_groups)
    X, y, prices = result['X'], result['y'], result['prices']

    if len(X) < 40:
        raise ValueError(
            f"[ABLATION] Само {len(X)} последователности за {feature_groups} — "
            f"твърде малко за смислен train/test split"
        )

    split = int(len(X) * 0.8)
    val = max(1, int(split * 0.9))

    model = StockPredictionModel(sequence_length=X.shape[1], n_features=X.shape[2])
    model.build_lstm_model()
    model.train_model(X[:val], y[:val], X[val:split], y[val:split],
                      epochs=epochs, batch_size=32)

    X_test, y_test, prices_test = X[split:], y[split:], prices[split:]
    metrics = model.evaluate(X_test, y_test)

    backtester = StockBacktester(model.predict(X_test), y_test, prices_test, initial_capital)
    backtester.calculate_accuracy_metrics()
    backtester.generate_trading_signals(threshold=0.52)
    bt_results = backtester.simulate_trading(transaction_cost=0.001)

    return metrics, bt_results, model, X_test, y_test, result['feature_names']


def run_comparison(ticker: str, period=None, epochs: int = 30,
                   initial_capital: float = 10000) -> pd.DataFrame:
    """
    Тренира и тества всеки вариант от ABLATION_VARIANTS, връща таблица с
    реални (не измислени) числа. Ако даден вариант няма достатъчно данни
    (напр. news кешът е празен), редът му показва грешката вместо да
    съборя цялото сравнение.

    Връща:
    -------
    pandas.DataFrame: strategy, total_return, accuracy, edge,
    sharpe_ratio, n_features, buy_and_hold_return_same_period.

    ВАЖНО за четенето на таблицата: различните feature групи имат
    различен warmup (market се нуждае от SMA50 история, fundamentals
    отпада преди първия earnings отчет в прозореца) — затова test
    периодът им НЕ е точно същите календарни дни. total_return на всеки
    ред е коректно сравним само със СОБСТВЕНАТА си
    buy_and_hold_return_same_period колона (същия ред), не между
    редовете — затова не показваме един общ "Buy & Hold" ред, а по един
    за всеки вариант.
    """
    rows = []
    last_model_info = None

    for name, groups in ABLATION_VARIANTS:
        print(f"\n{'='*60}\n[ABLATION] {name}  (групи: {groups})\n{'='*60}")
        try:
            metrics, bt_results, model, X_test, y_test, feat_names = _train_and_backtest(
                ticker, period, groups, epochs, initial_capital
            )
        except Exception as e:
            print(f"[ABLATION][WARN] {name} неуспешен: {e}")
            rows.append({'strategy': name, 'total_return': None, 'accuracy': None,
                        'edge': None, 'sharpe_ratio': None, 'n_features': None,
                        'buy_and_hold_return_same_period': None, 'error': str(e)})
            continue

        rows.append({
            'strategy': name,
            'total_return': bt_results['total_return'],
            'accuracy': metrics['Accuracy'],
            'edge': metrics['Edge'],
            'sharpe_ratio': bt_results.get('sharpe_ratio'),
            'n_features': X_test.shape[2],
            'buy_and_hold_return_same_period': bt_results['buy_and_hold_return'],
            'error': None,
        })

        if name == 'ML+All':
            last_model_info = (model, X_test, y_test, feat_names)

    df = pd.DataFrame(rows)

    print(f"\n{'='*60}\n[ABLATION] РЕЗУЛТАТИ")
    print("(всеки ред срещу СВОЯ Buy&Hold — test периодите се различават "
         "леко по warmup, виж buy_and_hold_return_same_period)")
    print('=' * 60)
    for _, r in df.iterrows():
        if r['error']:
            print(f"   {r['strategy']:<24} ГРЕШКА: {r['error']}")
        else:
            ret = f"{r['total_return']:+.2f}%"
            bnh = f"{r['buy_and_hold_return_same_period']:+.2f}%"
            acc = f"{r['accuracy']:.1f}%" if pd.notna(r['accuracy']) else '—'
            edge = f"{r['edge']:+.1f}%" if pd.notna(r['edge']) else '—'
            beats = 'бие B&H' if r['total_return'] > r['buy_and_hold_return_same_period'] else 'под B&H'
            print(f"   {r['strategy']:<24} return={ret:<10} B&H={bnh:<10} "
                 f"({beats})  accuracy={acc:<8} edge={edge}")

    return df, last_model_info


if __name__ == "__main__":
    print("[START] Ablation сравнение\n")
    df, model_info = run_comparison('AAPL', period='2y', epochs=25)
    print("\n[INFO] Финална таблица:")
    print(df[['strategy', 'total_return', 'buy_and_hold_return_same_period',
             'accuracy', 'edge', 'n_features']].to_string(index=False))
