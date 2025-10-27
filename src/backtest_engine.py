import pandas as pd
from typing import Dict
from .api.strategies import registry

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
    
    def run_backtest(self, strategy_id: str, df: pd.DataFrame, asset: str, parameters: dict = None) -> Dict:
        """Run backtest with specified strategy from registry"""
        try:
            # Get strategy from registry
            strategy = registry.get_strategy(strategy_id, parameters)
            
            # Generate signals using the strategy
            signals = strategy.generate_signals(df, asset)
            
            if signals.empty:
                return {"error": f"No signals generated for {asset} with strategy {strategy_id}"}
            
            # Configuration
            config = {
                "position_size": 0.1,  # Risk 10% per trade
                "stop_loss_pct": 0.005,  # 0.5% stop loss
                "take_profit_pct": 0.01,  # 1% take profit
                "commission": 0.001,  # 0.1% commission
                "slippage": 0.0005  # 0.05% slippage
            }
            
            trades = []
            capital = self.initial_capital
            
            for _, signal in signals.iterrows():
                entry_price = signal['price']
                entry_time = signal['timestamp']
                
                # Skip if we don't have enough capital
                if capital <= 0:
                    break
                
                # Risk management parameters
                position_size = config["position_size"]
                stop_loss_pct = config["stop_loss_pct"]
                take_profit_pct = config["take_profit_pct"]
                commission = config["commission"]
                slippage = config["slippage"]
                
                # Calculate stop loss and take profit prices
                if signal['signal'] == 'LONG':
                    stop_price = entry_price * (1 - stop_loss_pct)
                    target_price = entry_price * (1 + take_profit_pct)
                else:  # SHORT
                    stop_price = entry_price * (1 + stop_loss_pct)
                    target_price = entry_price * (1 - take_profit_pct)
                
                # Find data after the signal
                exit_data = df[df.index > entry_time]
                if exit_data.empty:
                    continue
                    
                exit_reason = "time_exit"
                exit_price = exit_data.iloc[0]['open']  # Default exit at next open
                exit_time_idx = exit_data.index[0]
                
                # Check for exit conditions in subsequent bars
                for idx, row in exit_data.iterrows():
                    current_low = row['low']
                    current_high = row['high']
                    current_close = row['close']
                    
                    # Check for stop loss hit
                    if (signal['signal'] == 'LONG' and current_low <= stop_price) or \
                       (signal['signal'] == 'SHORT' and current_high >= stop_price):
                        exit_price = stop_price
                        exit_reason = "stop_loss"
                        exit_time_idx = idx
                        break
                    
                    # Check for take profit hit
                    elif (signal['signal'] == 'LONG' and current_high >= target_price) or \
                         (signal['signal'] == 'SHORT' and current_low <= target_price):
                        exit_price = target_price
                        exit_reason = "take_profit"
                        exit_time_idx = idx
                        break
                    
                    # If we reach the end of data, use the close
                    elif idx == exit_data.index[-1]:
                        exit_price = current_close
                        exit_reason = "end_of_data"
                        exit_time_idx = idx
                
                # Apply slippage
                if signal['signal'] == 'LONG':
                    exit_price = exit_price * (1 - slippage)
                else:  # SHORT
                    exit_price = exit_price * (1 + slippage)
                
                # Calculate P&L with commission
                if signal['signal'] == 'LONG':
                    pnl_pct = (exit_price - entry_price) / entry_price
                else:  # SHORT
                    pnl_pct = (entry_price - exit_price) / entry_price
                
                # Apply commission (both entry and exit)
                pnl_pct -= commission * 2
                
                # Calculate actual P&L amount
                risk_amount = capital * position_size
                pnl = risk_amount * pnl_pct
                capital += pnl
                
                # Create trade record
                trade_data = {
                    'asset': asset,
                    'entry_time': entry_time,
                    'exit_time': exit_time_idx,
                    'signal': signal['signal'],
                    'entry_price': float(entry_price),
                    'exit_price': float(exit_price),
                    'exit_reason': exit_reason,
                    'pnl': float(pnl),
                    'pnl_pct': float(pnl_pct),
                    'capital': float(capital),
                    'stop_price': float(stop_price),
                    'target_price': float(target_price)
                }
                
                # Add ML confidence and validation if available
                if 'ml_confidence' in signal:
                    trade_data['ml_confidence'] = float(signal['ml_confidence'])
                if 'ml_validated' in signal:
                    trade_data['ml_validated'] = bool(signal['ml_validated'])
                if 'original_signal' in signal:
                    trade_data['original_signal'] = signal['original_signal']
                
                # Add strategy-specific data
                strategy_specific_fields = ['vwap', 'ib_high', 'ib_low', 'sma_fast', 'sma_slow', 'rsi', 
                                          'bb_upper', 'bb_lower', 'bb_middle', 'bb_position']
                for field in strategy_specific_fields:
                    if field in signal:
                        trade_data[field] = float(signal[field]) if isinstance(signal[field], (int, float)) else signal[field]
                
                trades.append(trade_data)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(trades, self.initial_capital)
            
            return {
                'trades': trades,
                'total_trades': len(trades),
                'final_capital': capital,
                'total_return': (capital - self.initial_capital) / self.initial_capital,
                'strategy_id': strategy_id,
                'performance_metrics': performance_metrics
            }
            
        except Exception as e:
            return {"error": f"Strategy error: {str(e)}"}
    
    def _calculate_performance_metrics(self, trades: list, initial_capital: float) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return {}
        
        df = pd.DataFrame(trades)
        
        # Basic metrics
        total_return = (df['capital'].iloc[-1] - initial_capital) / initial_capital
        total_trades = len(df)
        
        # Win/loss metrics
        winning_trades = df[df['pnl'] > 0]
        losing_trades = df[df['pnl'] < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else float('inf')
        
        # Risk metrics
        if len(df) > 0:
            # Max drawdown
            equity_curve = df['capital']
            rolling_max = equity_curve.expanding().max()
            drawdowns = (equity_curve - rolling_max) / rolling_max
            max_drawdown = drawdowns.min()
            
            # Sharpe ratio (simplified - using daily returns)
            daily_returns = equity_curve.pct_change().dropna()
            if len(daily_returns) > 1:
                sharpe_ratio = daily_returns.mean() / daily_returns.std() * (252 ** 0.5)  # Annualized
            else:
                sharpe_ratio = 0
        else:
            max_drawdown = 0
            sharpe_ratio = 0
        
        # Trade duration statistics
        if len(df) > 0:
            df['entry_time'] = pd.to_datetime(df['entry_time'])
            df['exit_time'] = pd.to_datetime(df['exit_time'])
            df['trade_duration'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 3600  # in hours
            avg_trade_duration = df['trade_duration'].mean()
        else:
            avg_trade_duration = 0
        
        # ML-specific metrics (if available)
        ml_metrics = {}
        if 'ml_confidence' in df.columns:
            ml_trades = df[df['ml_confidence'].notna()]
            if len(ml_trades) > 0:
                ml_winning = ml_trades[ml_trades['pnl'] > 0]
                ml_win_rate = len(ml_winning) / len(ml_trades) if len(ml_trades) > 0 else 0
                avg_ml_confidence = ml_trades['ml_confidence'].mean()
                
                ml_metrics = {
                    'ml_trades_count': len(ml_trades),
                    'ml_win_rate': ml_win_rate,
                    'avg_ml_confidence': avg_ml_confidence
                }
                
                # High confidence performance (>= 70%)
                high_conf_trades = ml_trades[ml_trades['ml_confidence'] >= 0.7]
                if len(high_conf_trades) > 0:
                    high_conf_wins = high_conf_trades[high_conf_trades['pnl'] > 0]
                    ml_metrics['high_confidence_win_rate'] = len(high_conf_wins) / len(high_conf_trades)
                    ml_metrics['high_confidence_trades'] = len(high_conf_trades)
        
        return {
            'total_return': float(total_return),
            'total_trades': total_trades,
            'win_rate': float(win_rate),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'profit_factor': float(profit_factor) if profit_factor != float('inf') else float('inf'),
            'max_drawdown': float(max_drawdown),
            'sharpe_ratio': float(sharpe_ratio),
            'avg_trade_duration_hours': float(avg_trade_duration),
            'ml_metrics': ml_metrics
        }
    
    def run_backtest_legacy(self, signals: pd.DataFrame, price_data: pd.DataFrame, asset: str) -> Dict:
        """Legacy method using pre-generated signals"""
        try:
            if signals.empty:
                return {"error": f"No signals provided for {asset}"}
            
            # Use the main backtest method but with a dummy strategy
            # This maintains compatibility with existing code
            class DummyStrategy:
                def __init__(self, signals):
                    self.signals = signals
                
                def generate_signals(self, df, asset):
                    return self.signals
            
            dummy_strategy = DummyStrategy(signals)
            
            # Temporarily register the dummy strategy
            original_strategies = registry._strategies.copy()
            registry._strategies['dummy'] = {
                'class': lambda params: dummy_strategy,
                'name': 'Dummy Strategy',
                'description': 'Temporary strategy for legacy backtest',
                'parameters': {}
            }
            
            result = self.run_backtest('dummy', price_data, asset)
            
            # Restore original strategies
            registry._strategies = original_strategies
            
            return result
            
        except Exception as e:
            return {"error": f"Legacy backtest error: {str(e)}"}
    
    def optimize_parameters(self, strategy_id: str, df: pd.DataFrame, asset: str, 
                          parameter_grid: Dict, initial_capital: float = 10000) -> Dict:
        """Optimize strategy parameters using grid search"""
        best_result = None
        best_return = -float('inf')
        best_params = None
        
        print(f"🔍 Optimizing parameters for {strategy_id}...")
        
        # Generate parameter combinations
        from itertools import product
        param_names = list(parameter_grid.keys())
        param_values = list(parameter_grid.values())
        
        param_combinations = list(product(*param_values))
        
        results = []
        
        for i, combination in enumerate(param_combinations):
            params = dict(zip(param_names, combination))
            
            try:
                result = self.run_backtest(strategy_id, df, asset, params)
                
                if "error" not in result and result.get("total_trades", 0) > 0:
                    total_return = result.get("total_return", 0)
                    results.append({
                        'parameters': params,
                        'total_return': total_return,
                        'total_trades': result.get("total_trades", 0),
                        'win_rate': result.get("performance_metrics", {}).get("win_rate", 0)
                    })
                    
                    if total_return > best_return:
                        best_return = total_return
                        best_result = result
                        best_params = params
                        
                    print(f"  Parameters {i+1}/{len(param_combinations)}: {params} → Return: {total_return:.2%}")
                    
            except Exception as e:
                print(f"  ⚠️  Failed with parameters {params}: {e}")
                continue
        
        if best_result is None:
            return {"error": "No successful parameter combinations found"}
        
        return {
            'best_parameters': best_params,
            'best_return': best_return,
            'best_result': best_result,
            'all_results': results,
            'total_combinations_tested': len(param_combinations),
            'successful_combinations': len(results)
        }
