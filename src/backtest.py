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
        print("\n📊 Изчисляване на метрики за точност...\n")

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

        print(f"✅ Accuracy (Точност): {accuracy*100:.2f}%")
        print(f"   → Колко често предсказваме правилно посоката")
        print(f"\n✅ Precision (Прецизност): {precision*100:.2f}%")
        print(f"   → От всички BUY сигнали, колко реално са се качили")
        print(f"\n✅ Recall (Чувствителност): {recall*100:.2f}%")
        print(f"   → От всички покачвания, колко сме уловили")
        print(f"\n✅ F1-Score: {f1*100:.2f}%")
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
        print(f"\n📈 Генериране на trading сигнали (threshold={threshold})...\n")

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

        print(f"📊 Генерирани сигнали:")
        print(f"   🟢 BUY:  {buy_count} ({buy_count/len(signals)*100:.1f}%)")
        print(f"   🔴 SELL: {sell_count} ({sell_count/len(signals)*100:.1f}%)")
        print(f"   ⚪ HOLD: {hold_count} ({hold_count/len(signals)*100:.1f}%)\n")

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
        print(f"\n💰 Симулация на trading с начален капитал ${self.initial_capital:,.2f}...\n")

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

        # Принтиране на резултати
        print("="*60)
        print("📊 РЕЗУЛТАТИ ОТ СИМУЛАЦИЯТА")
        print("="*60)
        print(f"\n💵 Финанси:")
        print(f"   Начален капитал:  ${self.initial_capital:,.2f}")
        print(f"   Финален капитал:  ${final_capital:,.2f}")
        print(f"   Печалба/Загуба:   ${final_capital - self.initial_capital:,.2f}")
        print(f"   Total Return:     {total_return:+.2f}%")
        print(f"\n📈 Търговия:")
        print(f"   Общо сделки:      {total_trades}")
        print(f"   Печеливши:        {len(profitable_trades)} ({win_rate:.1f}%)")
        print(f"   Загубени:         {len(losing_trades)}")
        print(f"\n🆚 Buy & Hold сравнение:")
        print(f"   Buy & Hold Return: {buy_and_hold_return:+.2f}%")
        print(f"   Нашата стратегия:  {total_return:+.2f}%")
        print(f"   Разлика:          {total_return - buy_and_hold_return:+.2f}%")

        if total_return > buy_and_hold_return:
            print(f"\n   ✅ Печелим срещу Buy & Hold!")
        else:
            print(f"\n   ❌ Buy & Hold е по-добра стратегия")

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
        print("\n📊 Създаване на визуализации...\n")

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
            print(f"💾 Графика запазена: {save_path}")
        else:
            plt.savefig('backtest_results.png', dpi=150, bbox_inches='tight')
            print(f"💾 Графика запазена: backtest_results.png")

        plt.close()

    def get_summary(self):
        """
        Връща обобщение на резултатите като DataFrame.
        """
        summary = pd.DataFrame([self.results])
        return summary


# Тестване на модула
if __name__ == "__main__":
    print("🚀 Тестване на Backtesting Module\n")

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

    print("\n✅ Тестването завърши успешно!")
