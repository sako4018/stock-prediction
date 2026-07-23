"""
Backtesting Module
==================
Този модул оценява колко добре работи модела и симулира trading стратегия.

Функции:
- backtest_predictions(): Тества предсказанията върху исторически данни
- calculate_trading_signals(): Създава BUY/SELL сигнали
- simulate_trading(): Симулира реални търговски операции
- calculate_returns(): Изчислява печалби/загуби
"""

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import os

class StockBacktester:
    """
    Клас за backtesting на stock prediction модел.

    Параметри:
    ----------
    predictions : numpy.array
        Предсказани стойности от модела
    actual_values : numpy.array
        Реални стойности
    prices : numpy.array
        Реални цени на акциите
    initial_capital : float
        Начален капитал за симулация (по подразбиране $10,000)
    """

    def __init__(self, predictions, actual_values, prices, initial_capital=10000):
        self.predictions = predictions.flatten() if len(predictions.shape) > 1 else predictions
        self.actual_values = actual_values
        self.prices = prices
        self.initial_capital = initial_capital
        self.results = {}

    def calculate_accuracy_metrics(self):
        """
        Изчислява метрики за точност на предсказанията.

        Връща:
        -------
        dict
            Accuracy, Precision, Recall, F1-score
        """
        print("\n[INFO] Изчисляване на метрики за точност...\n")

        # Конвертиране на regression predictions в classification (нагоре/надолу)
        # Ако предсказаната цена е > 0.5 (нормализирано) => нагоре (1), иначе надолу (0)
        pred_direction = (self.predictions > 0.5).astype(int)
        actual_direction = (self.actual_values > 0.5).astype(int)

        # Accuracy: Общ процент правилни предсказания
        accuracy = accuracy_score(actual_direction, pred_direction)

        # Precision: От всички "buy" сигнали, колко са били правилни
        precision = precision_score(actual_direction, pred_direction, zero_division=0)

        # Recall: От всички реални покачвания, колко сме уловили
        recall = recall_score(actual_direction, pred_direction, zero_division=0)

        # F1-score: Баланс между precision и recall
        f1 = f1_score(actual_direction, pred_direction, zero_division=0)

        self.results['accuracy'] = accuracy * 100
        self.results['precision'] = precision * 100
        self.results['recall'] = recall * 100
        self.results['f1_score'] = f1 * 100

        print(f"[OK] Accuracy (Точност): {accuracy*100:.2f}%")
        print(f"   → Колко често предсказваме правилно посоката")
        print(f"\n[OK] Precision (Прецизност): {precision*100:.2f}%")
        print(f"   → От всички BUY сигнали, колко реално са се качили")
        print(f"\n[OK] Recall (Чувствителност): {recall*100:.2f}%")
        print(f"   → От всички покачвания, колко сме уловили")
        print(f"\n[OK] F1-Score: {f1*100:.2f}%")
        print(f"   → Общ балансиран резултат\n")

        return self.results

    def generate_trading_signals(self, threshold=0.52):
        """
        Генерира BUY/SELL/HOLD сигнали базирани на предсказанията.

        Логика:
        - BUY: Ако моделът предсказва покачване > threshold
        - SELL: Ако моделът предсказва спад < (1 - threshold)
        - HOLD: В останалите случаи

        Параметри:
        ----------
        threshold : float
            Праг за BUY сигнал (по подразбиране 0.52)

        Връща:
        -------
        numpy.array
            Масив със сигнали: 1 (BUY), -1 (SELL), 0 (HOLD)
        """
        print(f"\n[UP] Генериране на trading сигнали (threshold={threshold})...\n")

        signals = np.zeros(len(self.predictions))

        for i in range(len(self.predictions)):
            if self.predictions[i] > threshold:
                signals[i] = 1  # BUY
            elif self.predictions[i] < (1 - threshold):
                signals[i] = -1  # SELL
            else:
                signals[i] = 0  # HOLD

        buy_count = np.sum(signals == 1)
        sell_count = np.sum(signals == -1)
        hold_count = np.sum(signals == 0)

        print(f"[INFO] Генерирани сигнали:")
        print(f"   [BUY]  {buy_count} ({buy_count/len(signals)*100:.1f}%)")
        print(f"   [SELL] {sell_count} ({sell_count/len(signals)*100:.1f}%)")
        print(f"   [HOLD] {hold_count} ({hold_count/len(signals)*100:.1f}%)\n")

        self.signals = signals
        return signals

    def simulate_trading(self, transaction_cost=0.001):
        """
        Симулира trading стратегия и изчислява печалби/загуби.

        Параметри:
        ----------
        transaction_cost : float
            Процент транзакционна такса (по подразбиране 0.1%)

        Връща:
        -------
        dict
            Резултати от симулацията: total_return, final_capital, win_rate и др.
        """
        print(f"\n[MONEY] Симулация на trading с начален капитал ${self.initial_capital:,.2f}...\n")

        capital = self.initial_capital
        position = 0  # 0 = нямаме акции, 1 = имаме акции
        shares = 0
        trades = []
        portfolio_values = [capital]

        for i in range(len(self.signals)):
            current_price = self.prices[i]

            # BUY сигнал
            if self.signals[i] == 1 and position == 0:
                # Купуваме акции с целия наличен капитал
                shares = capital / current_price
                cost = shares * current_price * (1 + transaction_cost)
                capital -= cost
                position = 1

                trades.append({
                    'type': 'BUY',
                    'price': current_price,
                    'shares': shares,
                    'cost': cost,
                    'index': i
                })

            # SELL сигнал
            elif self.signals[i] == -1 and position == 1:
                # Продаваме всички акции
                revenue = shares * current_price * (1 - transaction_cost)
                capital += revenue
                profit = revenue - trades[-1]['cost']
                position = 0

                trades.append({
                    'type': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'revenue': revenue,
                    'profit': profit,
                    'index': i
                })

                shares = 0

            # Изчисляване на текуща стойност на портфолиото
            if position == 1:
                portfolio_value = capital + (shares * current_price)
            else:
                portfolio_value = capital

            portfolio_values.append(portfolio_value)

        # Ако все още имаме отворена позиция в края, затваряме я
        if position == 1:
            final_revenue = shares * self.prices[-1] * (1 - transaction_cost)
            capital += final_revenue
            profit = final_revenue - trades[-1]['cost']

            trades.append({
                'type': 'SELL (final)',
                'price': self.prices[-1],
                'shares': shares,
                'revenue': final_revenue,
                'profit': profit,
                'index': len(self.signals) - 1
            })

        # Изчисляване на резултати
        final_capital = capital
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100

        # Брой profitable trades
        profitable_trades = [t for t in trades if t['type'].startswith('SELL') and t.get('profit', 0) > 0]
        losing_trades = [t for t in trades if t['type'].startswith('SELL') and t.get('profit', 0) <= 0]

        total_trades = len(profitable_trades) + len(losing_trades)
        win_rate = (len(profitable_trades) / total_trades * 100) if total_trades > 0 else 0

        # Buy and Hold стратегия за сравнение
        buy_and_hold_shares = self.initial_capital / self.prices[0]
        buy_and_hold_final = buy_and_hold_shares * self.prices[-1]
        buy_and_hold_return = ((buy_and_hold_final - self.initial_capital) / self.initial_capital) * 100

        self.results.update({
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'total_trades': total_trades,
            'profitable_trades': len(profitable_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'buy_and_hold_return': buy_and_hold_return,
            'outperformance': total_return - buy_and_hold_return,
            'portfolio_values': portfolio_values,
            'trades': trades
        })

        # Risk Management Metrics
        portfolio_array = np.array(portfolio_values)
        daily_returns = np.diff(portfolio_array) / portfolio_array[:-1]

        # Sharpe Ratio (risk-adjusted return)
        # > 1 = добър, > 2 = много добър
        risk_free_rate = 0.02 / 252  # 2% годишно, дневно
        if np.std(daily_returns) > 0:
            sharpe_ratio = (np.mean(daily_returns) - risk_free_rate) / np.std(daily_returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # Sortino Ratio (penalizes only downside volatility)
        downside_returns = daily_returns[daily_returns < 0]
        if len(downside_returns) > 0 and np.std(downside_returns) > 0:
            sortino_ratio = (np.mean(daily_returns) - risk_free_rate) / np.std(downside_returns) * np.sqrt(252)
        else:
            sortino_ratio = 0

        # Max Drawdown (най-голям спад от връх до дъно)
        peak = np.maximum.accumulate(portfolio_array)
        drawdown = (portfolio_array - peak) / peak
        max_drawdown = np.min(drawdown) * 100

        # Volatility (годишна волатилност)
        volatility = np.std(daily_returns) * np.sqrt(252) * 100

        # Calmar Ratio (return / max drawdown)
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

        self.results.update({
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'calmar_ratio': calmar_ratio
        })

        # Принтиране на резултати
        print("="*60)
        print("[INFO] РЕЗУЛТАТИ ОТ СИМУЛАЦИЯТА")
        print("="*60)
        print(f"\n[MONEY] Финанси:")
        print(f"   Начален капитал:  ${self.initial_capital:,.2f}")
        print(f"   Финален капитал:  ${final_capital:,.2f}")
        print(f"   Печалба/Загуба:   ${final_capital - self.initial_capital:,.2f}")
        print(f"   Total Return:     {total_return:+.2f}%")
        print(f"\n[UP] Търговия:")
        print(f"   Общо сделки:      {total_trades}")
        print(f"   Печеливши:        {len(profitable_trades)} ({win_rate:.1f}%)")
        print(f"   Загубени:         {len(losing_trades)}")
        print(f"\n[VS] Buy & Hold сравнение:")
        print(f"   Buy & Hold Return: {buy_and_hold_return:+.2f}%")
        print(f"   Нашата стратегия:  {total_return:+.2f}%")
        print(f"   Разлика:          {total_return - buy_and_hold_return:+.2f}%")

        if total_return > buy_and_hold_return:
            print(f"\n   [OK] Печелим срещу Buy & Hold!")
        else:
            print(f"\n   [FAIL] Buy & Hold е по-добра стратегия")

        print(f"\n[INFO] RISK METRICS:")
        print(f"   Sharpe Ratio:     {sharpe_ratio:.2f} {'[OK]' if sharpe_ratio > 1 else '[WARN]' if sharpe_ratio > 0 else '[FAIL]'}")
        print(f"   Sortino Ratio:    {sortino_ratio:.2f} {'[OK]' if sortino_ratio > 1 else '[WARN]' if sortino_ratio > 0 else '[FAIL]'}")
        print(f"   Max Drawdown:     {max_drawdown:.2f}% {'[OK]' if max_drawdown > -20 else '[WARN]' if max_drawdown > -40 else '[FAIL]'}")
        print(f"   Volatility:       {volatility:.2f}%")
        print(f"   Calmar Ratio:     {calmar_ratio:.2f}")

        print("\n" + "="*60)

        return self.results

    def plot_results(self, save_path=None):
        """
        Визуализира резултатите от backtesting.

        Параметри:
        ----------
        save_path : str, optional
            Път за запазване на графиката
        """
        print("\n[INFO] Създаване на визуализации...\n")

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Backtesting Results', fontsize=16, fontweight='bold')

        # 1. Цени и сигнали
        ax1 = axes[0, 0]
        ax1.plot(self.prices, label='Actual Price', color='blue', alpha=0.7)

        # Маркиране на BUY/SELL точките
        if hasattr(self, 'signals'):
            buy_indices = np.where(self.signals == 1)[0]
            sell_indices = np.where(self.signals == -1)[0]

            ax1.scatter(buy_indices, self.prices[buy_indices],
                       color='green', marker='^', s=100, label='BUY', zorder=5)
            ax1.scatter(sell_indices, self.prices[sell_indices],
                       color='red', marker='v', s=100, label='SELL', zorder=5)

        ax1.set_title('Price & Trading Signals')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Price ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Portfolio Value
        ax2 = axes[0, 1]
        if 'portfolio_values' in self.results:
            ax2.plot(self.results['portfolio_values'], color='green', linewidth=2)
            ax2.axhline(y=self.initial_capital, color='red', linestyle='--',
                       label=f'Initial Capital (${self.initial_capital:,.0f})')
            ax2.fill_between(range(len(self.results['portfolio_values'])),
                            self.initial_capital,
                            self.results['portfolio_values'],
                            alpha=0.3, color='green')

        ax2.set_title('Portfolio Value Over Time')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Portfolio Value ($)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Predictions vs Actual
        ax3 = axes[1, 0]
        ax3.plot(self.actual_values, label='Actual', color='blue', alpha=0.7)
        ax3.plot(self.predictions, label='Predicted', color='orange', alpha=0.7)
        ax3.set_title('Predictions vs Actual Values')
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Normalized Value')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. Metrics Summary
        ax4 = axes[1, 1]
        ax4.axis('off')

        metrics_text = f"""
        PERFORMANCE METRICS
        {'='*40}

        Accuracy:        {self.results.get('accuracy', 0):.2f}%
        Precision:       {self.results.get('precision', 0):.2f}%
        Recall:          {self.results.get('recall', 0):.2f}%
        F1-Score:        {self.results.get('f1_score', 0):.2f}%

        Total Return:    {self.results.get('total_return', 0):+.2f}%
        Win Rate:        {self.results.get('win_rate', 0):.2f}%
        Total Trades:    {self.results.get('total_trades', 0)}

        Buy & Hold:      {self.results.get('buy_and_hold_return', 0):+.2f}%
        Outperformance:  {self.results.get('outperformance', 0):+.2f}%
        """

        ax4.text(0.1, 0.5, metrics_text, fontsize=11, family='monospace',
                verticalalignment='center')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"[SAVE] Графика запазена: {save_path}")
        else:
            plt.savefig('backtest_results.png', dpi=150, bbox_inches='tight')
            print(f"[SAVE] Графика запазена: backtest_results.png")

        plt.close()

    def get_summary(self):
        """
        Връща обобщение на резултатите като DataFrame.
        """
        summary = pd.DataFrame([self.results])
        return summary


class WalkForwardValidator:
    """
    Walk-Forward Validation - по-реалистичен backtest.
    Вместо да разделим данните веднъж, тренираме на滾ing window.

    Параметри:
    ----------
    train_window : int
        Брой дни за трениране (по подразбиране 252 = 1 година)
    test_window : int
        Брой дни за тестване (по подразбиране 63 = 1 тримесечие)
    step_size : int
        Колко дни да преместим window-а (по подразбиране 21 = 1 месец)
    """

    def __init__(self, train_window=252, test_window=63, step_size=21):
        self.train_window = train_window
        self.test_window = test_window
        self.step_size = step_size
        self.fold_results = []

    def run(self, model_class, X, y, prices, initial_capital=10000, **model_kwargs):
        """
        Изпълнява walk-forward validation.

        Параметри:
        ----------
        model_class : class
            Класът на модела (напр. StockPredictionModel)
        X : numpy.array
            Входни данни (3D за LSTM)
        y : numpy.array
            Target стойности
        prices : numpy.array
            Реални цени
        initial_capital : float
            Начален капитал
        model_kwargs : dict
            Допълнителни параметри за модела

        Връща:
        -------
        dict
            Резултати от walk-forward validation
        """
        print(f"\n[RUN] Walk-Forward Validation")
        print(f"   Train window: {self.train_window} дни")
        print(f"   Test window: {self.test_window} дни")
        print(f"   Step size: {self.step_size} дни")
        print(f"   Total data: {len(X)} дни\n")

        self.fold_results = []
        all_predictions = []
        all_actuals = []
        all_prices = []

        start = self.train_window
        fold = 0

        while start + self.test_window <= len(X):
            fold += 1
            train_end = start
            test_end = min(start + self.test_window, len(X))

            # Train data
            X_train = X[:train_end]
            y_train = y[:train_end]

            # Test data
            X_test = X[train_end:test_end]
            y_test = y[train_end:test_end]
            test_prices = prices[train_end:test_end] if len(prices) > test_end else prices[train_end:]

            if len(X_test) == 0 or len(test_prices) == 0:
                break

            # Трениране на модел
            model = model_class(
                sequence_length=X_train.shape[1],
                n_features=X_train.shape[2],
                **model_kwargs
            )
            model.build_lstm_model()

            # Split за validation
            val_split = int(len(X_train) * 0.9)
            model.train_model(
                X_train[:val_split], y_train[:val_split],
                X_train[val_split:], y_train[val_split:],
                epochs=30, batch_size=32
            )

            # Предсказания
            predictions = model.predict(X_test).flatten()

            # Оценка на fold-а
            direction_pred = (predictions > 0.5).astype(int)
            direction_true = (y_test > 0.5).astype(int)
            accuracy = accuracy_score(direction_true, direction_pred) * 100

            # Trading simulation за този fold
            capital = initial_capital
            position = 0
            for i in range(len(predictions)):
                if predictions[i] > 0.55 and position == 0:
                    shares = capital / test_prices[i]
                    capital -= shares * test_prices[i] * 1.001
                    position = 1
                elif predictions[i] < 0.45 and position == 1:
                    capital += shares * test_prices[i] * 0.999
                    position = 0

            if position == 1:
                capital += shares * test_prices[-1] * 0.999

            fold_return = ((capital - initial_capital) / initial_capital) * 100

            fold_result = {
                'fold': fold,
                'train_end': train_end,
                'test_start': train_end,
                'test_end': test_end,
                'accuracy': accuracy,
                'return_pct': fold_return,
                'final_capital': capital
            }
            self.fold_results.append(fold_result)

            all_predictions.extend(predictions)
            all_actuals.extend(y_test)
            all_prices.extend(test_prices)

            print(f"   Fold {fold}: accuracy={accuracy:.1f}%, return={fold_return:+.2f}%")

            start += self.step_size

        # Общ резултат
        total_return = 0
        if self.fold_results:
            avg_accuracy = np.mean([f['accuracy'] for f in self.fold_results])
            avg_return = np.mean([f['return_pct'] for f in self.fold_results])
            total_return = self.fold_results[-1]['return_pct']

            # Buy and Hold сравнение
            if len(all_prices) > 1:
                bnh_return = ((all_prices[-1] - all_prices[0]) / all_prices[0]) * 100
            else:
                bnh_return = 0
        else:
            avg_accuracy = 0
            avg_return = 0
            bnh_return = 0

        results = {
            'total_folds': fold,
            'avg_accuracy': avg_accuracy,
            'avg_return': avg_return,
            'total_return': total_return,
            'buy_and_hold_return': bnh_return,
            'outperformance': total_return - bnh_return,
            'fold_results': self.fold_results
        }

        print(f"\n[INFO] Walk-Forward Summary:")
        print(f"   Folds: {fold}")
        print(f"   Avg Accuracy: {avg_accuracy:.1f}%")
        print(f"   Avg Return: {avg_return:+.2f}%")
        print(f"   Total Return: {total_return:+.2f}%")
        print(f"   Buy & Hold: {bnh_return:+.2f}%")

        return results


# Тестване на модула
if __name__ == "__main__":
    print("[START] Тестване на Backtesting Module\n")

    # Симулиране на данни
    n_samples = 200

    # Генериране на симулирани цени (random walk)
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(n_samples) * 2)

    # Симулиране на predictions и actual values
    actual_values = np.random.rand(n_samples)
    predictions = actual_values + np.random.randn(n_samples) * 0.1  # Малък шум

    # Създаване на backtester
    backtester = StockBacktester(
        predictions=predictions,
        actual_values=actual_values,
        prices=prices,
        initial_capital=10000
    )

    # Изчисляване на метрики
    backtester.calculate_accuracy_metrics()

    # Генериране на сигнали
    backtester.generate_trading_signals(threshold=0.52)

    # Симулация на trading
    backtester.simulate_trading(transaction_cost=0.001)

    # Визуализация
    backtester.plot_results()

    print("\n[OK] Тестването завърши успешно!")
