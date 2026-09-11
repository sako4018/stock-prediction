"""
Feature Importance Module
===========================
Нашият LSTM модел няма вградена feature importance (за разлика от
дървовидни модели като XGBoost/RandomForest), затова ползваме
model-агностичен permutation importance: разбъркваме стойностите на
ЕДНА feature колона през тестовия сет, мерим спада в точност спрямо
baseline, повтаряме няколко пъти и осредняваме.

Работи директно с нашия PyTorch модел (model.predict() приема X с
форма (n, seq_length, n_features)) — не изисква sklearn wrapper.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score


def permutation_importance(model, X_test, y_test, feature_names,
                           n_repeats: int = 5, seed: int = 0) -> pd.DataFrame:
    """
    Параметри:
    ----------
    model : StockPredictionModel
        Трениран модел (.predict() връща вероятности)
    X_test : numpy.array
        (n, seq_length, n_features)
    y_test : numpy.array
        (n,) реални посоки 0/1
    feature_names : list[str]
        Имена на feature-ите, в реда на последната ос на X_test
    n_repeats : int
        Колко пъти да се повтори shuffle-ването за всяка feature
        (осредняваме — един shuffle може случайно да е неинформативен)

    Връща:
    -------
    pandas.DataFrame
        Колони: feature, importance (среден спад в accuracy при
        разбъркване, по-голямо = по-важна feature), importance_std.
        Сортирано низходящо по importance.
    """
    if X_test.shape[2] != len(feature_names):
        raise ValueError(
            f"[FAIL] X_test има {X_test.shape[2]} features, "
            f"а feature_names са {len(feature_names)} — не съвпадат"
        )

    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_test).ravel().astype(int)

    baseline_probs = model.predict(X_test).flatten()
    baseline_acc = accuracy_score(y_true, (baseline_probs > 0.5).astype(int))

    rows = []
    for j, name in enumerate(feature_names):
        drops = []
        for _ in range(n_repeats):
            X_shuffled = X_test.copy()
            # Разбъркваме кой example получава чии стойности за feature j
            # (по ос 0 — примерите), пазим времевата структура вътре във
            # всяка последователност недокосната.
            perm = rng.permutation(len(X_shuffled))
            X_shuffled[:, :, j] = X_shuffled[perm, :, j]

            probs = model.predict(X_shuffled).flatten()
            acc = accuracy_score(y_true, (probs > 0.5).astype(int))
            drops.append(baseline_acc - acc)

        rows.append({
            'feature': name,
            'importance': float(np.mean(drops)),
            'importance_std': float(np.std(drops)),
        })

    df = pd.DataFrame(rows).sort_values('importance', ascending=False).reset_index(drop=True)
    return df


def print_importance_table(df: pd.DataFrame, top_n: int = 15):
    print(f"\n[INFO] Топ {top_n} features по важност (permutation importance):")
    for _, row in df.head(top_n).iterrows():
        bar = '#' * max(0, int(row['importance'] * 200))
        print(f"   {row['feature']:<28} {row['importance']:+.4f}  {bar}")
