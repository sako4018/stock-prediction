"""
Ensemble Model Module
=====================
Комбинира предсказания от няколко ML модела за по-точни резултати.

Модели:
- LSTM (deep learning)
- XGBoost (gradient boosting)
- Random Forest (ensemble)

Предимство: Ensemble обикновено е по-точен от всеки отделен модел.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score
import joblib
import os
import json


class EnsembleModel:
    """
    Ensemble модел комбиниращ LSTM, XGBoost и Random Forest.

    Параметри:
    ----------
    sequence_length : int
        Дължина на последователността
    n_features : int
        Брой features
    """

    def __init__(self, sequence_length=60, n_features=20):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_model = None
        self.rf_model = None
        self.gb_model = None
        self.weights = {'lstm': 0.5, 'rf': 0.25, 'gb': 0.25}

    def prepare_flat_data(self, X):
        """
        Конвертира 3D LSTM данни в 2D за tree-based модели.
        Flatten: (batch, seq_len, features) -> (batch, seq_len * features)
        """
        return X.reshape(X.shape[0], -1)

    def train_rf_model(self, X_train, y_train, n_estimators=100):
        """
        Тренира Random Forest модел.
        """
        print("🌲 Трениране на Random Forest...")
        X_flat = self.prepare_flat_data(X_train)

        self.rf_model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        self.rf_model.fit(X_flat, y_train)
        print("✅ Random Forest трениран!")
        return self.rf_model

    def train_gb_model(self, X_train, y_train, n_estimators=100):
        """
        Тренира Gradient Boosting модел (XGBoost-style).
        """
        print("🚀 Трениране на Gradient Boosting...")
        X_flat = self.prepare_flat_data(X_train)

        self.gb_model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            max_depth=5,
            learning_rate=0.1,
            min_samples_split=5,
            random_state=42
        )
        self.gb_model.fit(X_flat, y_train)
        print("✅ Gradient Boosting трениран!")
        return self.gb_model

    def predict(self, X, lstm_predictions=None):
        """
        Прави предсказания комбинирайки всички модели.

        Параметри:
        ----------
        X : numpy.array
            Входни данни (3D за LSTM)
        lstm_predictions : numpy.array, optional
            Предсказания от LSTM модела (ако вече са налични)

        Връща:
        -------
        numpy.array
            Комбинирани предсказания
        """
        predictions = []

        # LSTM предсказания
        if lstm_predictions is not None:
            lstm_pred = lstm_predictions.flatten()
        elif self.lstm_model is not None:
            import torch
            self.lstm_model.eval()
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X).to(next(self.lstm_model.parameters()).device)
                lstm_pred = self.lstm_model(X_tensor).cpu().numpy().flatten()
        else:
            lstm_pred = np.zeros(len(X))

        predictions.append(lstm_pred * self.weights['lstm'])

        # Random Forest предсказания
        if self.rf_model is not None:
            X_flat = self.prepare_flat_data(X)
            rf_pred = self.rf_model.predict(X_flat)
            predictions.append(rf_pred * self.weights['rf'])

        # Gradient Boosting предсказания
        if self.gb_model is not None:
            X_flat = self.prepare_flat_data(X)
            gb_pred = self.gb_model.predict(X_flat)
            predictions.append(gb_pred * self.weights['gb'])

        # Комбиниране
        ensemble_pred = np.sum(predictions, axis=0)
        return ensemble_pred

    def evaluate(self, X_test, y_test, lstm_predictions=None):
        """
        Оценява ensemble модела.
        """
        print("\n📊 Оценка на Ensemble модела...")

        ensemble_pred = self.predict(X_test, lstm_predictions)

        # Метрики
        mse = mean_squared_error(y_test, ensemble_pred)
        mae = mean_absolute_error(y_test, ensemble_pred)
        rmse = np.sqrt(mse)

        direction_pred = (ensemble_pred > 0.5).astype(int)
        direction_true = (y_test > 0.5).astype(int)
        direction_accuracy = accuracy_score(direction_true, direction_pred) * 100

        # Индивидуални метрики
        results = {
            'ensemble': {'mse': mse, 'mae': mae, 'rmse': rmse, 'accuracy': direction_accuracy}
        }

        if self.rf_model is not None:
            X_flat = self.prepare_flat_data(X_test)
            rf_pred = self.rf_model.predict(X_flat)
            rf_acc = accuracy_score(direction_true, (rf_pred > 0.5).astype(int)) * 100
            results['random_forest'] = {'accuracy': rf_acc}

        if self.gb_model is not None:
            X_flat = self.prepare_flat_data(X_test)
            gb_pred = self.gb_model.predict(X_flat)
            gb_acc = accuracy_score(direction_true, (gb_pred > 0.5).astype(int)) * 100
            results['gradient_boosting'] = {'accuracy': gb_acc}

        print(f"\n📈 Резултати:")
        print(f"   {'Модел':<25} {'Точност':<10}")
        print(f"   {'-'*35}")
        for name, metrics in results.items():
            print(f"   {name:<25} {metrics.get('accuracy', 0):.2f}%")

        return results

    def save_models(self, model_name='ensemble'):
        """Записва всички модели."""
        models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        os.makedirs(models_dir, exist_ok=True)

        if self.rf_model is not None:
            joblib.dump(self.rf_model, os.path.join(models_dir, f'{model_name}_rf.joblib'))
        if self.gb_model is not None:
            joblib.dump(self.gb_model, os.path.join(models_dir, f'{model_name}_gb.joblib'))

        config = {
            'weights': self.weights,
            'sequence_length': self.sequence_length,
            'n_features': self.n_features
        }
        with open(os.path.join(models_dir, f'{model_name}_config.json'), 'w') as f:
            json.dump(config, f, indent=4)

        print(f"💾 Ensemble модели записани")

    def load_models(self, model_name='ensemble'):
        """Зарежда записаните модели."""
        models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')

        config_path = os.path.join(models_dir, f'{model_name}_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.weights = config.get('weights', self.weights)

        rf_path = os.path.join(models_dir, f'{model_name}_rf.joblib')
        if os.path.exists(rf_path):
            self.rf_model = joblib.load(rf_path)

        gb_path = os.path.join(models_dir, f'{model_name}_gb.joblib')
        if os.path.exists(gb_path):
            self.gb_model = joblib.load(gb_path)

        print(f"✅ Ensemble модели заредени")
