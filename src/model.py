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
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, log_loss
)
import joblib
import os
import json

# Версия на архитектурата. Стари модели (v2) бяха регресия върху нормализирана
# цена и връщат съвсем различни числа при същата форма на тегла — затова
# load_model отказва да ги зареди вместо да ги подаде мълчаливо като вероятности.
ARCHITECTURE_VERSION = 'lstm_attention_v3_clf'

# Проверка дали има GPU
print("[CHECK] Проверка на GPU...")
if torch.cuda.is_available():
    print(f"[OK] Открито GPU: {torch.cuda.get_device_name(0)}")
    print(f"   CUDA версия: {torch.version.cuda}")
    device = torch.device('cuda')
else:
    print("[WARN] GPU не е открито, използва се CPU")
    device = torch.device('cpu')


class AttentionLayer(nn.Module):
    """
    Attention mechanism за LSTM.
    Позволява на модела да се фокусира върху най-важните time steps.
    """

    def __init__(self, hidden_size):
        super(AttentionLayer, self).__init__()
        self.attention = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, lstm_output):
        # lstm_output: (batch, seq_len, hidden_size)
        attention_weights = self.attention(lstm_output)  # (batch, seq_len, 1)
        attention_weights = torch.softmax(attention_weights, dim=1)

        # Weighted sum
        context = torch.sum(attention_weights * lstm_output, dim=1)  # (batch, hidden_size)
        return context, attention_weights


class LSTMModel(nn.Module):
    """
    PyTorch LSTM с Attention Mechanism за stock prediction.
    """

    def __init__(self, n_features, sequence_length, lstm_units=[32, 16, 8], dropout_rate=0.2):
        super(LSTMModel, self).__init__()

        self.n_features = n_features
        self.sequence_length = sequence_length

        # LSTM слоеве
        self.lstm1 = nn.LSTM(n_features, lstm_units[0], batch_first=True)
        self.dropout1 = nn.Dropout(dropout_rate)
        self.batch_norm1 = nn.BatchNorm1d(lstm_units[0])

        self.lstm2 = nn.LSTM(lstm_units[0], lstm_units[1], batch_first=True)
        self.dropout2 = nn.Dropout(dropout_rate)
        self.batch_norm2 = nn.BatchNorm1d(lstm_units[1])

        self.lstm3 = nn.LSTM(lstm_units[1], lstm_units[2], batch_first=True)
        self.dropout3 = nn.Dropout(dropout_rate)
        self.batch_norm3 = nn.BatchNorm1d(lstm_units[2])

        # Attention mechanism
        self.attention = AttentionLayer(lstm_units[2])

        # Dense слоеве
        self.fc1 = nn.Linear(lstm_units[2], 64)
        self.relu = nn.ReLU()
        self.dropout4 = nn.Dropout(dropout_rate / 2)
        self.fc2 = nn.Linear(64, 25)
        self.dropout5 = nn.Dropout(dropout_rate / 2)

        # Изход
        self.fc3 = nn.Linear(25, 1)

    def forward(self, x):
        # LSTM слой 1
        lstm_out, _ = self.lstm1(x)
        lstm_out = self.dropout1(lstm_out)
        lstm_out = lstm_out.permute(0, 2, 1)
        lstm_out = self.batch_norm1(lstm_out)
        lstm_out = lstm_out.permute(0, 2, 1)

        # LSTM слой 2
        lstm_out, _ = self.lstm2(lstm_out)
        lstm_out = self.dropout2(lstm_out)
        lstm_out = lstm_out.permute(0, 2, 1)
        lstm_out = self.batch_norm2(lstm_out)
        lstm_out = lstm_out.permute(0, 2, 1)

        # LSTM слой 3
        lstm_out, _ = self.lstm3(lstm_out)
        lstm_out = self.dropout3(lstm_out)
        lstm_out = lstm_out.permute(0, 2, 1)
        lstm_out = self.batch_norm3(lstm_out)
        lstm_out = lstm_out.permute(0, 2, 1)

        # Attention mechanism
        context, attention_weights = self.attention(lstm_out)

        # Dense слоеве
        out = self.fc1(context)
        out = self.relu(out)
        out = self.dropout4(out)
        out = self.fc2(out)
        out = self.dropout5(out)
        out = self.fc3(out)

        return out


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
        self.history = {'train_loss': [], 'val_loss': []}
        self.device = device
        self.scaler = None
        self.scaler_columns = None
        self.lstm_units = [32, 16, 8]
        self.dropout_rate = 0.2

    def build_lstm_model(self, lstm_units=[32, 16, 8], dropout_rate=0.2):
        """
        Създава LSTM neural network архитектурата.

        Архитектура:
        - LSTM слоеве: научават се от последователностите
        - Dropout: предотвратява overfitting
        - Dense слой: финален изход с предсказанието

        Параметри:
        ----------
        lstm_units : list
            Брой неврони в всеки LSTM слой [32, 16, 8]
        dropout_rate : float
            Процент dropout за регуларизация (0.2 = 20%)

        Връща:
        -------
        PyTorch Model
            Компилиран LSTM модел
        """
        print("Building LSTM model...")

        # Пазим ги, за да ги запишем в config-а — иначе модел с различни
        # размери не може да се зареди обратно.
        self.lstm_units = list(lstm_units)
        self.dropout_rate = dropout_rate

        self.model = LSTMModel(
            n_features=self.n_features,
            sequence_length=self.sequence_length,
            lstm_units=lstm_units,
            dropout_rate=dropout_rate
        ).to(self.device)

        # Optimizer и loss function
        # BCEWithLogits, защото задачата е класификация: утре нагоре или надолу.
        # Моделът връща logit; sigmoid-ът се прилага в loss-а и в predict().
        # weight_decay (L2): с няколкостотин тренировъчни последователности
        # дори намален модел лесно запаметява шум; малка L2 санкция върху
        # теглата е евтина добавка към dropout+early stopping.
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=0.001, weight_decay=1e-4
        )
        self.criterion = nn.BCEWithLogitsLoss()

        print("[OK] Модел създаден успешно!")
        print("\n[INFO] Архитектура на модела:")
        print(self.model)

        # Брой параметри
        total_params = sum(p.numel() for p in self.model.parameters())
        print(f"\n[SAVE] Общо параметри: {total_params:,}")

        return self.model

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
        dict
            История на обучението
        """
        if self.model is None:
            raise ValueError("[FAIL] Моделът не е създаден! Извикай build_lstm_model() първо.")

        print(f"\n[START] Стартиране на тренировка...")
        print(f"[INFO] Тренировъчни данни: {X_train.shape}")
        print(f"[INFO] Валидационни данни: {X_val.shape}")
        print(f"[CONFIG] Epochs: {epochs}, Batch size: {batch_size}")
        print(f"[DEVICE] Устройство: {self.device}")

        # Конвертиране в PyTorch tensors
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.FloatTensor(y_train).reshape(-1, 1).to(self.device)
        X_val_tensor = torch.FloatTensor(X_val).to(self.device)
        y_val_tensor = torch.FloatTensor(y_val).reshape(-1, 1).to(self.device)

        # DataLoaders
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        # Early stopping параметри
        best_val_loss = float('inf')
        patience = 15
        patience_counter = 0

        # Model checkpoint path
        models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        os.makedirs(models_dir, exist_ok=True)
        checkpoint_path = os.path.join(models_dir, 'best_model.pt')

        print("\n[TARGET] Започва обучението...\n")

        # Тренировъчен loop
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0

            for batch_X, batch_y in train_loader:
                # Forward pass
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)

                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)

            # Validation phase
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val_tensor)
                val_loss = self.criterion(val_outputs, y_val_tensor).item()

            # Запазване на историята
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)

            # Print progress
            if (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch+1}/{epochs}] - "
                      f"Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Запазване на най-добрия модел
                torch.save(self.model.state_dict(), checkpoint_path)
            else:
                patience_counter += 1

            if patience_counter >= patience:
                print(f"\n[WARN] Early stopping triggered на epoch {epoch+1}")
                print(f"   Няма подобрение след {patience} епохи")
                # Зареждане на най-добрия модел
                self.model.load_state_dict(torch.load(checkpoint_path))
                break

        print("\n[OK] Обучението завърши успешно!")
        print(f"[INFO] Най-добър validation loss: {best_val_loss:.6f}")

        return self.history

    def predict(self, X, return_logits=False):
        """
        Прави предсказания с тренирания модел.

        Параметри:
        ----------
        X : numpy.array
            Входни данни за предсказание
        return_logits : bool
            Ако е True, връща суровите logit-и вместо вероятности

        Връща:
        -------
        numpy.array
            Вероятност (0..1), че утре цената затваря по-високо.
            0.5 е неутрално — над него е bullish, под него bearish.
        """
        if self.model is None:
            raise ValueError("[FAIL] Моделът не е създаден или зареден!")

        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            logits = self.model(X_tensor)
            if return_logits:
                return logits.cpu().numpy()
            return torch.sigmoid(logits).cpu().numpy()

    def evaluate(self, X_test, y_test, threshold=0.5):
        """
        Оценява модела на тестови данни.

        Задачата е класификация, затова метриките са класификационни.
        Винаги се показва и baseline ("винаги предсказвай мнозинството") —
        без него accuracy от 55% изглежда добре, а може да е по-зле от нищо.

        Параметри:
        ----------
        X_test : numpy.array
            Тестови входни данни
        y_test : numpy.array
            Истински посоки (0/1)
        threshold : float
            Праг върху вероятността за клас 1

        Връща:
        -------
        dict
            Accuracy, Precision, Recall, F1, ROC-AUC, LogLoss, Baseline, Edge
        """
        print("\n[INFO] Оценка на модела...")

        probs = self.predict(X_test).flatten()
        y_true = np.asarray(y_test).ravel().astype(int)
        y_pred = (probs > threshold).astype(int)

        accuracy = accuracy_score(y_true, y_pred) * 100
        precision = precision_score(y_true, y_pred, zero_division=0) * 100
        recall = recall_score(y_true, y_pred, zero_division=0) * 100
        f1 = f1_score(y_true, y_pred, zero_division=0) * 100

        # ROC-AUC иска и двата класа да присъстват в y_true
        if len(np.unique(y_true)) < 2:
            roc_auc = float('nan')
        else:
            roc_auc = roc_auc_score(y_true, probs)

        logloss = log_loss(y_true, np.clip(probs, 1e-7, 1 - 1e-7), labels=[0, 1])

        # Честен baseline: винаги предсказвай по-честия клас
        majority_class = 1 if y_true.mean() >= 0.5 else 0
        baseline_accuracy = (y_true == majority_class).mean() * 100
        edge = accuracy - baseline_accuracy

        metrics = {
            'Accuracy': accuracy,
            'Precision': precision,
            'Recall': recall,
            'F1': f1,
            'ROC_AUC': roc_auc,
            'LogLoss': logloss,
            'Baseline_Accuracy': baseline_accuracy,
            'Edge': edge,
            # Запазено име за обратна съвместимост с batch_train / backend
            'Direction_Accuracy': accuracy,
        }

        print("\n[UP] Резултати (класификация на посоката):")
        print(f"   Accuracy:   {accuracy:.2f}%")
        print(f"   Precision:  {precision:.2f}%")
        print(f"   Recall:     {recall:.2f}%")
        print(f"   F1-Score:   {f1:.2f}%")
        print(f"   ROC-AUC:    {roc_auc:.4f}  (0.5 = случайно)")
        print(f"   LogLoss:    {logloss:.4f}")
        print(f"\n   Baseline (винаги '{majority_class}'): {baseline_accuracy:.2f}%")
        print(f"   Edge над baseline: {edge:+.2f}%", end=' ')
        if edge > 2:
            print("[OK]")
        elif edge > 0:
            print("[WARN] слаб")
        else:
            print("[FAIL] моделът не бие baseline")

        return metrics

    def save_model(self, model_name='stock_lstm_model', scaler=None,
                   feature_columns=None):
        """
        Записва модела на диск.

        Скалерът се записва заедно с теглата. Без него при зареждане се
        тренира нов скалер от новосвалените данни и моделът получава входове
        в друга скала от тази, в която е учил — предсказанията стават шум.

        Параметри:
        ----------
        model_name : str
            Име на модела (без разширение)
        scaler : sklearn scaler, optional
            Скалерът, с който са подготвени тренировъчните данни
        feature_columns : list, optional
            Колоните, върху които скалерът е трениран, в същия ред
        """
        if self.model is None:
            raise ValueError("[FAIL] Няма модел за записване!")

        models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        os.makedirs(models_dir, exist_ok=True)

        # Записване на модела (PyTorch format)
        model_path = os.path.join(models_dir, f'{model_name}.pt')
        torch.save(self.model.state_dict(), model_path)
        print(f"[SAVE] Модел записан: {model_path}")

        # Записване на конфигурацията
        config = {
            'sequence_length': self.sequence_length,
            'n_features': self.n_features,
            'model_name': model_name,
            'architecture': ARCHITECTURE_VERSION,
            'task': 'classification',
            'target': 'Price_Direction',
            'lstm_units': self.lstm_units,
            'dropout_rate': self.dropout_rate,
        }

        config_path = os.path.join(models_dir, f'{model_name}_config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"[FILE] Конфигурация записана: {config_path}")

        # Скалерът и редът на колоните — задължителни за коректно предсказване
        if scaler is not None:
            scaler_path = os.path.join(models_dir, f'{model_name}_scaler.joblib')
            joblib.dump({'scaler': scaler, 'columns': list(feature_columns or [])},
                        scaler_path)
            self.scaler = scaler
            self.scaler_columns = list(feature_columns or [])
            print(f"[SAVE] Скалер записан: {scaler_path}")

        # Записване на историята на обучението
        if self.history:
            history_path = os.path.join(models_dir, f'{model_name}_history.json')
            with open(history_path, 'w') as f:
                json.dump(self.history, f, indent=4)
            print(f"[INFO] История записана: {history_path}")

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
            raise FileNotFoundError(f"[FAIL] Конфигурацията не е намерена: {config_path}")

        with open(config_path, 'r') as f:
            config = json.load(f)

        saved_arch = config.get('architecture')
        if saved_arch != ARCHITECTURE_VERSION:
            raise ValueError(
                f"[FAIL] Несъвместим модел '{model_name}': записан е като "
                f"'{saved_arch}', а текущата архитектура е "
                f"'{ARCHITECTURE_VERSION}'. Старите модели предсказваха "
                f"нормализирана цена, не посока — трябва да се претренират."
            )

        self.sequence_length = config['sequence_length']
        self.n_features = config['n_features']

        # Създаване със същите размери, с които е бил трениран
        self.build_lstm_model(
            lstm_units=config.get('lstm_units', [32, 16, 8]),
            dropout_rate=config.get('dropout_rate', 0.2),
        )

        model_path = os.path.join(models_dir, f'{model_name}.pt')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"[FAIL] Моделът не е намерен: {model_path}")

        saved_state = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(saved_state)
        print(f"[OK] Модел зареден: {model_path}")

        # Скалерът, с който е трениран моделът. Без него входовете при
        # предсказване няма да са в същата скала като при обучението.
        scaler_path = os.path.join(models_dir, f'{model_name}_scaler.joblib')
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(
                f"[FAIL] Липсва скалерът на '{model_name}'. Моделът е записан "
                f"преди скалерите да се пазят — трябва да се претренира."
            )
        bundle = joblib.load(scaler_path)
        self.scaler = bundle['scaler']
        self.scaler_columns = bundle['columns']
        print(f"[OK] Скалер зареден: {len(self.scaler_columns)} колони")

        self.model.eval()

        return self.model


# Тестване на модула
if __name__ == "__main__":
    print("[START] Тестване на Model Module\n")

    # Симулиране на данни за бързо тестване
    sequence_length = 60
    n_features = 20
    n_samples = 1000

    # Генериране на random данни
    X_train = np.random.rand(n_samples, sequence_length, n_features).astype(np.float32)
    y_train = np.random.randint(0, 2, n_samples).astype(np.float32)
    X_val = np.random.rand(200, sequence_length, n_features).astype(np.float32)
    y_val = np.random.randint(0, 2, 200).astype(np.float32)
    X_test = np.random.rand(100, sequence_length, n_features).astype(np.float32)
    y_test = np.random.randint(0, 2, 100).astype(np.float32)

    # Създаване и обучение на модел
    model = StockPredictionModel(sequence_length=sequence_length, n_features=n_features)
    model.build_lstm_model()

    # Тренировка (само 5 епохи за тест)
    model.train_model(X_train, y_train, X_val, y_val, epochs=5, batch_size=32)

    # Оценка
    metrics = model.evaluate(X_test, y_test)

    # Записване
    model.save_model('test_model')

    print("\n[OK] Тестването завърши успешно!")
