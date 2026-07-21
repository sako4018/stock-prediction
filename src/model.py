"""
Model Module
============
Този модул създава и тренира LSTM neural network за предсказване на акции.

LSTM (Long Short-Term Memory) е тип neural network, който е много добър
за анализ на time series данни като цени на акции.

Функции:
- build_lstm_model(): Създава архитектурата на модела
- train_model(): Тренира модела
- predict(): Прави предсказания
- evaluate(): Оценява точността
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score
import joblib
import os
import json

# Проверка дали има GPU
print("🔍 Проверка на GPU...")
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print(f"✅ Открити {len(gpus)} GPU устройства")
    for gpu in gpus:
        print(f"   {gpu}")
else:
    print("⚠️ GPU не е открито, използва се CPU")


class StockPredictionModel:
    """
    LSTM модел за предсказване на цени на акции.

    Параметри:
    ----------
    sequence_length : int
        Колко предишни дни данни да използваме за предсказание
    n_features : int
        Брой features (колони) в данните
    """

    def __init__(self, sequence_length=60, n_features=20):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model = None
        self.history = None

    def build_lstm_model(self, lstm_units=[128, 64, 32], dropout_rate=0.2):
        """
        Създава LSTM neural network архитектурата.

        Архитектура:
        - LSTM слоеве: научават се от последователностите
        - Dropout: предотвратява overfitting
        - Dense слой: финален изход с предсказанието

        Параметри:
        ----------
        lstm_units : list
            Брой неврони в всеки LSTM слой [128, 64, 32]
        dropout_rate : float
            Процент dropout за регуларизация (0.2 = 20%)

        Връща:
        -------
        keras.Model
            Компилиран LSTM модел
        """
        print("🏗️ Създаване на LSTM модел...")

        model = Sequential(name='Stock_LSTM_Model')

        # Първи LSTM слой (return_sequences=True защото имаме още LSTM слоеве след него)
        model.add(LSTM(
            units=lstm_units[0],
            return_sequences=True,
            input_shape=(self.sequence_length, self.n_features),
            name='LSTM_1'
        ))
        model.add(Dropout(dropout_rate, name='Dropout_1'))
        model.add(BatchNormalization(name='BatchNorm_1'))

        # Втори LSTM слой
        model.add(LSTM(
            units=lstm_units[1],
            return_sequences=True,
            name='LSTM_2'
        ))
        model.add(Dropout(dropout_rate, name='Dropout_2'))
        model.add(BatchNormalization(name='BatchNorm_2'))

        # Трети LSTM слой (return_sequences=False защото е последният LSTM)
        model.add(LSTM(
            units=lstm_units[2],
            return_sequences=False,
            name='LSTM_3'
        ))
        model.add(Dropout(dropout_rate, name='Dropout_3'))
        model.add(BatchNormalization(name='BatchNorm_3'))

        # Dense слоеве за финалното предсказание
        model.add(Dense(units=25, activation='relu', name='Dense_1'))
        model.add(Dropout(dropout_rate / 2, name='Dropout_4'))

        # Изходен слой (1 неврон = 1 предсказание)
        model.add(Dense(units=1, activation='linear', name='Output'))

        # Компилиране на модела
        # Adam optimizer: адаптивен learning rate
        # MSE loss: mean squared error за регресия
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mean_squared_error',
            metrics=['mae']  # mean absolute error
        )

        self.model = model

        print("✅ Модел създаден успешно!")
        print("\n📊 Архитектура на модела:")
        model.summary()

        return model

    def train_model(self, X_train, y_train, X_val, y_val, epochs=100, batch_size=32):
        """
        Тренира LSTM модела.

        Параметри:
        ----------
        X_train : numpy.array
            Тренировъчни входни данни
        y_train : numpy.array
            Тренировъчни target данни
        X_val : numpy.array
            Валидационни входни данни
        y_val : numpy.array
            Валидационни target данни
        epochs : int
            Брой епохи за обучение (по подразбиране 100)
        batch_size : int
            Размер на batch (по подразбиране 32)

        Връща:
        -------
        keras.History
            История на обучението
        """
        if self.model is None:
            raise ValueError("❌ Моделът не е създаден! Извикай build_lstm_model() първо.")

        print(f"\n🚀 Стартиране на тренировка...")
        print(f"📊 Тренировъчни данни: {X_train.shape}")
        print(f"📊 Валидационни данни: {X_val.shape}")
        print(f"⚙️ Epochs: {epochs}, Batch size: {batch_size}")

        # Callbacks за оптимизация на обучението

        # EarlyStopping: спира обучението ако няма подобрение
        early_stop = EarlyStopping(
            monitor='val_loss',  # следи validation loss
            patience=15,  # изчаква 15 епохи без подобрение
            restore_best_weights=True,  # връща най-добрите тегла
            verbose=1
        )

        # ModelCheckpoint: записва най-добрия модел
        models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        os.makedirs(models_dir, exist_ok=True)
        checkpoint_path = os.path.join(models_dir, 'best_model.keras')

        checkpoint = ModelCheckpoint(
            checkpoint_path,
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )

        # ReduceLROnPlateau: намалява learning rate при plateau
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,  # намалява LR с 50%
            patience=7,
            min_lr=0.00001,
            verbose=1
        )

        # Тренировка
        print("\n🎯 Започва обучението...\n")

        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop, checkpoint, reduce_lr],
            verbose=1
        )

        print("\n✅ Обучението завърши успешно!")

        return self.history

    def predict(self, X):
        """
        Прави предсказания с тренирания модел.

        Параметри:
        ----------
        X : numpy.array
            Входни данни за предсказание

        Връща:
        -------
        numpy.array
            Предсказани стойности
        """
        if self.model is None:
            raise ValueError("❌ Моделът не е създаден или зареден!")

        predictions = self.model.predict(X, verbose=0)
        return predictions

    def evaluate(self, X_test, y_test):
        """
        Оценява модела на тестови данни.

        Параметри:
        ----------
        X_test : numpy.array
            Тестови входни данни
        y_test : numpy.array
            Истински target стойности

        Връща:
        -------
        dict
            Метрики за точност (MSE, MAE, RMSE, MAPE)
        """
        print("\n📊 Оценка на модела...")

        # Предсказване
        y_pred = self.predict(X_test)

        # Изчисляване на метрики
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mse)

        # MAPE (Mean Absolute Percentage Error)
        # Колко процента грешим средно
        mape = np.mean(np.abs((y_test - y_pred.flatten()) / y_test)) * 100

        # Точност на посоката (нагоре/надолу)
        # Създаваме classification от regression predictions
        direction_pred = (y_pred.flatten() > 0.5).astype(int)
        direction_true = (y_test > 0.5).astype(int)
        direction_accuracy = accuracy_score(direction_true, direction_pred) * 100

        metrics = {
            'MSE': mse,
            'MAE': mae,
            'RMSE': rmse,
            'MAPE': mape,
            'Direction_Accuracy': direction_accuracy
        }

        print("\n📈 Резултати:")
        print(f"   MSE (Mean Squared Error): {mse:.6f}")
        print(f"   MAE (Mean Absolute Error): {mae:.6f}")
        print(f"   RMSE (Root Mean Squared Error): {rmse:.6f}")
        print(f"   MAPE (Mean Absolute % Error): {mape:.2f}%")
        print(f"   Точност на посоката: {direction_accuracy:.2f}%")

        return metrics

    def save_model(self, model_name='stock_lstm_model'):
        """
        Записва модела на диск.

        Параметри:
        ----------
        model_name : str
            Име на модела (без разширение)
        """
        if self.model is None:
            raise ValueError("❌ Няма модел за записване!")

        models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        os.makedirs(models_dir, exist_ok=True)

        # Записване на модела
        model_path = os.path.join(models_dir, f'{model_name}.keras')
        self.model.save(model_path)
        print(f"💾 Модел записан: {model_path}")

        # Записване на конфигурацията
        config = {
            'sequence_length': self.sequence_length,
            'n_features': self.n_features,
            'model_name': model_name
        }

        config_path = os.path.join(models_dir, f'{model_name}_config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"📄 Конфигурация записана: {config_path}")

        # Записване на историята на обучението
        if self.history is not None:
            history_path = os.path.join(models_dir, f'{model_name}_history.json')
            history_dict = {key: [float(val) for val in values]
                          for key, values in self.history.history.items()}

            with open(history_path, 'w') as f:
                json.dump(history_dict, f, indent=4)
            print(f"📊 История записана: {history_path}")

    def load_model(self, model_name='stock_lstm_model'):
        """
        Зарежда записан модел от диск.

        Параметри:
        ----------
        model_name : str
            Име на модела за зареждане
        """
        models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')

        # Зареждане на конфигурацията
        config_path = os.path.join(models_dir, f'{model_name}_config.json')
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"❌ Конфигурацията не е намерена: {config_path}")

        with open(config_path, 'r') as f:
            config = json.load(f)

        self.sequence_length = config['sequence_length']
        self.n_features = config['n_features']

        # Зареждане на модела
        model_path = os.path.join(models_dir, f'{model_name}.keras')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"❌ Моделът не е намерен: {model_path}")

        self.model = keras.models.load_model(model_path)
        print(f"✅ Модел зареден: {model_path}")

        return self.model


# Тестване на модула
if __name__ == "__main__":
    print("🚀 Тестване на Model Module\n")

    # Симулиране на данни за бързо тестване
    sequence_length = 60
    n_features = 20
    n_samples = 1000

    # Генериране на random данни
    X_train = np.random.rand(n_samples, sequence_length, n_features)
    y_train = np.random.rand(n_samples)
    X_val = np.random.rand(200, sequence_length, n_features)
    y_val = np.random.rand(200)
    X_test = np.random.rand(100, sequence_length, n_features)
    y_test = np.random.rand(100)

    # Създаване и обучение на модел
    model = StockPredictionModel(sequence_length=sequence_length, n_features=n_features)
    model.build_lstm_model()

    # Тренировка (само 5 епохи за тест)
    model.train_model(X_train, y_train, X_val, y_val, epochs=5, batch_size=32)

    # Оценка
    metrics = model.evaluate(X_test, y_test)

    # Записване
    model.save_model('test_model')

    print("\n✅ Тестването завърши успешно!")
