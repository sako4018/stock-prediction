"""
Stock Prediction API
===================
FastAPI backend за stock prediction систем.

API Endpoints:
- GET  /api/stocks/{ticker}          — Real-time цена + info
- GET  /api/stocks/{ticker}/history  — Исторически данни
- POST /api/stocks/{ticker}/predict  — ML предсказание
- POST /api/stocks/{ticker}/train    — Тренировка на модел
- GET  /api/stocks/{ticker}/backtest — Backtest резултати
- GET  /api/stocks/{ticker}/signals  — Trading сигнали
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Добавяне на src директорията в path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_collection import StockDataCollector
from preprocessing import StockDataPreprocessor
from model import StockPredictionModel
from backtest import StockBacktester

app = FastAPI(
    title="Stock Prediction API",
    description="ML-powered stock prediction system",
    version="1.0.0"
)

# CORS middleware за React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TrainRequest(BaseModel):
    period: str = "2y"
    epochs: int = 100
    batch_size: int = 32


class PredictResponse(BaseModel):
    ticker: str
    current_price: float
    prediction: float
    signal: str
    confidence: float


@app.get("/")
def root():
    return {"message": "Stock Prediction API", "version": "1.0.0"}


@app.get("/api/stocks/{ticker}")
def get_stock_info(ticker: str):
    """Real-time цена и информация за акцията."""
    try:
        collector = StockDataCollector(ticker=ticker, period="1d", interval="1d")
        price_info = collector.get_real_time_price()
        company_info = collector.get_company_info()

        if not price_info:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")

        return {
            "ticker": ticker.upper(),
            "price": price_info,
            "company": company_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/{ticker}/history")
def get_stock_history(ticker: str, period: str = "1y", interval: str = "1d"):
    """Исторически данни с технически индикатори."""
    try:
        collector = StockDataCollector(ticker=ticker, period=period, interval=interval)
        data = collector.fetch_stock_data(save_to_csv=False)

        if data is None or len(data) == 0:
            raise HTTPException(status_code=404, detail=f"No history data for {ticker}")

        # Добавяне на технически индикатори
        preprocessor = StockDataPreprocessor(data)
        data_with_indicators = preprocessor.calculate_technical_indicators()

        # Конвертиране в JSON
        result = data_with_indicators.copy()
        result['Date'] = result['Date'].astype(str)

        return {
            "ticker": ticker.upper(),
            "period": period,
            "interval": interval,
            "data": result.to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stocks/{ticker}/predict")
def predict_stock(ticker: str, period: str = "2y"):
    """Прави ML предсказание за акцията."""
    try:
        # Събиране на данни
        collector = StockDataCollector(ticker=ticker, period=period, interval="1d")
        data = collector.fetch_stock_data(save_to_csv=False)

        if data is None or len(data) == 0:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        # Обработка
        preprocessor = StockDataPreprocessor(data)
        preprocessor.calculate_technical_indicators()
        preprocessor.create_target_variable(days_ahead=1)
        preprocessor.normalize_data()

        # Подготовка на последователности
        scaled_data = preprocessor.scaled_data
        feature_cols = [col for col in scaled_data.columns if col not in ['Date']]
        model_data = scaled_data[feature_cols].values

        seq_length = 60
        if len(model_data) < seq_length:
            raise HTTPException(status_code=400, detail="Not enough data for prediction")

        X, y = preprocessor.create_sequences(model_data, seq_length=seq_length)

        # Зареждане на модел
        model = StockPredictionModel(sequence_length=seq_length, n_features=X.shape[2])
        model_name = f'{ticker.upper()}_stock_model'

        try:
            model.load_model(model_name)
        except:
            # Ако няма модел, тренираме нов
            split_idx = int(len(X) * 0.9)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            model.build_lstm_model()
            model.train_model(X_train, y_train, X_val, y_val, epochs=50, batch_size=32)
            model.save_model(model_name)

        # Предсказание
        latest_data = model_data[-seq_length:].reshape(1, seq_length, -1)
        prediction = model.predict(latest_data)
        predicted_value = prediction[0][0]

        current_price = data['Close'].values[-1]

        # Определяне на сигнал
        if predicted_value > 0.5:
            signal = "BUY"
            confidence = (predicted_value - 0.5) * 200
        else:
            signal = "SELL"
            confidence = (0.5 - predicted_value) * 200

        return {
            "ticker": ticker.upper(),
            "current_price": float(current_price),
            "prediction": float(predicted_value),
            "signal": signal,
            "confidence": float(confidence),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stocks/{ticker}/train")
def train_model(ticker: str, request: TrainRequest):
    """Тренира нов ML модел за акцията."""
    try:
        # Събиране на данни
        collector = StockDataCollector(ticker=ticker, period=request.period, interval="1d")
        data = collector.fetch_stock_data(save_to_csv=False)

        if data is None or len(data) == 0:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        # Обработка
        preprocessor = StockDataPreprocessor(data)
        preprocessor.calculate_technical_indicators()
        preprocessor.create_target_variable(days_ahead=1)
        preprocessor.normalize_data()

        # Подготовка на последователности
        scaled_data = preprocessor.scaled_data
        feature_cols = [col for col in scaled_data.columns if col not in ['Date']]
        model_data = scaled_data[feature_cols].values

        X, y = preprocessor.create_sequences(model_data, seq_length=60)

        # Разделяне
        split_idx = int(len(X) * 0.9)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Тренировка
        model = StockPredictionModel(sequence_length=60, n_features=X.shape[2])
        model.build_lstm_model()
        history = model.train_model(X_train, y_train, X_val, y_val,
                                   epochs=request.epochs, batch_size=request.batch_size)

        # Запазване
        model_name = f'{ticker.upper()}_stock_model'
        model.save_model(model_name)

        return {
            "ticker": ticker.upper(),
            "status": "trained",
            "epochs": request.epochs,
            "train_loss": history['train_loss'][-1] if history['train_loss'] else None,
            "val_loss": history['val_loss'][-1] if history['val_loss'] else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/{ticker}/backtest")
def run_backtest(ticker: str, period: str = "2y", initial_capital: float = 10000):
    """Изпълнява backtest на модела."""
    try:
        # Събиране на данни
        collector = StockDataCollector(ticker=ticker, period=period, interval="1d")
        data = collector.fetch_stock_data(save_to_csv=False)

        if data is None or len(data) == 0:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        # Обработка
        preprocessor = StockDataPreprocessor(data)
        preprocessor.calculate_technical_indicators()
        preprocessor.create_target_variable(days_ahead=1)
        preprocessor.normalize_data()

        # Подготовка
        scaled_data = preprocessor.scaled_data
        feature_cols = [col for col in scaled_data.columns if col not in ['Date']]
        model_data = scaled_data[feature_cols].values

        X, y = preprocessor.create_sequences(model_data, seq_length=60)
        train_size = 0.8
        split_idx = int(len(X) * train_size)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Зареждане/трениране на модел
        model = StockPredictionModel(sequence_length=60, n_features=X.shape[2])
        model_name = f'{ticker.upper()}_stock_model'

        try:
            model.load_model(model_name)
        except:
            val_split = int(len(X_train) * 0.9)
            model.build_lstm_model()
            model.train_model(X_train[:val_split], y_train[:val_split],
                            X_train[val_split:], y_train[val_split:],
                            epochs=50, batch_size=32)
            model.save_model(model_name)

        # Предсказания
        predictions = model.predict(X_test)

        # Реални цени
        all_prices = preprocessor.data['Close'].values[60:]
        test_prices = all_prices[split_idx:]

        # Backtest
        backtester = StockBacktester(
            predictions=predictions,
            actual_values=y_test,
            prices=test_prices,
            initial_capital=initial_capital
        )

        backtester.calculate_accuracy_metrics()
        backtester.generate_trading_signals(threshold=0.52)
        results = backtester.simulate_trading(transaction_cost=0.001)

        # Чистене на не-serializable данни
        clean_results = {k: v for k, v in results.items()
                        if k not in ['portfolio_values', 'trades']}

        return {
            "ticker": ticker.upper(),
            "initial_capital": initial_capital,
            "results": clean_results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/{ticker}/signals")
def get_signals(ticker: str, period: str = "1y"):
    """Генерира BUY/SELL сигнали."""
    try:
        collector = StockDataCollector(ticker=ticker, period=period, interval="1d")
        data = collector.fetch_stock_data(save_to_csv=False)

        if data is None or len(data) == 0:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        # Технически индикатори за сигнали
        preprocessor = StockDataPreprocessor(data)
        preprocessor.calculate_technical_indicators()

        df = preprocessor.data

        # RSI сигнал
        latest_rsi = df['RSI'].iloc[-1]
        rsi_signal = "OVERSOLD (BUY)" if latest_rsi < 30 else "OVERBOUGHT (SELL)" if latest_rsi > 70 else "NEUTRAL"

        # MACD сигнал
        latest_macd = df['MACD'].iloc[-1]
        latest_signal = df['MACD_Signal'].iloc[-1]
        macd_signal = "BUY" if latest_macd > latest_signal else "SELL"

        # Bollinger Bands
        latest_close = df['Close'].iloc[-1]
        bb_upper = df['BB_Upper'].iloc[-1]
        bb_lower = df['BB_Lower'].iloc[-1]

        if latest_close > bb_upper:
            bb_signal = "OVERBOUGHT (SELL)"
        elif latest_close < bb_lower:
            bb_signal = "OVERSOLD (BUY)"
        else:
            bb_signal = "NEUTRAL"

        # ATR (Average True Range) - волатилност
        latest_atr = df['ATR'].iloc[-1]
        atr_percent = (latest_atr / latest_close) * 100
        atr_signal = "HIGH VOLATILITY" if atr_percent > 3 else "LOW VOLATILITY" if atr_percent < 1 else "NORMAL"

        # Stochastic Oscillator
        latest_stoch_k = df['Stoch_K'].iloc[-1]
        latest_stoch_d = df['Stoch_D'].iloc[-1]
        if latest_stoch_k > 80 and latest_stoch_d > 80:
            stoch_signal = "OVERBOUGHT (SELL)"
        elif latest_stoch_k < 20 and latest_stoch_d < 20:
            stoch_signal = "OVERSOLD (BUY)"
        elif latest_stoch_k > latest_stoch_d:
            stoch_signal = "BULLISH (BUY)"
        else:
            stoch_signal = "BEARISH (SELL)"

        # Williams %R
        latest_wr = df['Williams_R'].iloc[-1]
        if latest_wr > -20:
            wr_signal = "OVERBOUGHT (SELL)"
        elif latest_wr < -80:
            wr_signal = "OVERSOLD (BUY)"
        else:
            wr_signal = "NEUTRAL"

        # Overall recommendation (weighted average of signals)
        buy_signals = sum([
            1 if rsi_signal.startswith("OVERSOLD") else 0,
            1 if macd_signal == "BUY" else 0,
            1 if bb_signal.startswith("OVERSOLD") else 0,
            1 if stoch_signal.startswith("OVERSOLD") or stoch_signal.startswith("BULLISH") else 0,
            1 if wr_signal.startswith("OVERSOLD") else 0
        ])

        sell_signals = sum([
            1 if rsi_signal.startswith("OVERBOUGHT") else 0,
            1 if macd_signal == "SELL" else 0,
            1 if bb_signal.startswith("OVERBOUGHT") else 0,
            1 if stoch_signal.startswith("OVERBOUGHT") or stoch_signal.startswith("BEARISH") else 0,
            1 if wr_signal.startswith("OVERBOUGHT") else 0
        ])

        if buy_signals >= 3:
            recommendation = "STRONG BUY"
        elif buy_signals >= 2:
            recommendation = "BUY"
        elif sell_signals >= 3:
            recommendation = "STRONG SELL"
        elif sell_signals >= 2:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"

        return {
            "ticker": ticker.upper(),
            "current_price": float(latest_close),
            "indicators": {
                "rsi": {"value": float(latest_rsi), "signal": rsi_signal},
                "macd": {"value": float(latest_macd), "signal": macd_signal},
                "bollinger": {
                    "upper": float(bb_upper),
                    "lower": float(bb_lower),
                    "signal": bb_signal
                },
                "atr": {"value": float(latest_atr), "percent": float(atr_percent), "signal": atr_signal},
                "stochastic": {"k": float(latest_stoch_k), "d": float(latest_stoch_d), "signal": stoch_signal},
                "williams_r": {"value": float(latest_wr), "signal": wr_signal}
            },
            "recommendation": recommendation
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
