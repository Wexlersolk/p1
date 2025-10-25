import pandas as pd
from typing import Dict
# Add this import to use strategy registry
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
            
            # Your existing backtest logic continues here...
            config = {
                "position_size": 0.1,
                "stop_loss_pct": 0.005,
                "take_profit_pct": 0.01,
                "commission": 0.001
            }
            
            trades = []
            capital = self.initial_capital
            
            for _, signal in signals.iterrows():
                entry_price = signal['price']
                entry_time = signal['timestamp']
                
                # Risk management parameters
                position_size = config["position_size"]
                stop_loss_pct = config["stop_loss_pct"]
                take_profit_pct = config["take_profit_pct"]
                commission = config["commission"]
                
                if signal['signal'] == 'LONG':
                    stop_price = entry_price * (1 - stop_loss_pct)
                    target_price = entry_price * (1 + take_profit_pct)
                else:  # SHORT
                    stop_price = entry_price * (1 + stop_loss_pct)
                    target_price = entry_price * (1 - take_profit_pct)
                
                # Find exit conditions
                exit_data = df[df.index > entry_time]
                if exit_data.empty:
                    continue
                    
                exit_reason = "time_exit"
                exit_price = exit_data.iloc[0]['open']  # Default exit
                exit_time = exit_data.index[0]
                
                for idx, row in exit_data.iterrows():
                    current_low = row['low']
                    current_high = row['high']
                    
                    # Check for stop loss
                    if (signal['signal'] == 'LONG' and current_low <= stop_price) or \
                       (signal['signal'] == 'SHORT' and current_high >= stop_price):
                        exit_price = stop_price
                        exit_reason = "stop_loss"
                        exit_time = idx
                        break
                    # Check for take profit
                    elif (signal['signal'] == 'LONG' and current_high >= target_price) or \
                         (signal['signal'] == 'SHORT' and current_low <= target_price):
                        exit_price = target_price
                        exit_reason = "take_profit" 
                        exit_time = idx
                        break
                    # End of data
                    elif idx == exit_data.index[-1]:
                        exit_price = row['close']
                        exit_reason = "end_of_data"
                        exit_time = idx
                
                # Calculate P&L with commission
                if signal['signal'] == 'LONG':
                    pnl_pct = (exit_price - entry_price) / entry_price
                else:  # SHORT
                    pnl_pct = (entry_price - exit_price) / entry_price
                
                # Apply commission
                pnl_pct -= commission * 2
                
                risk_amount = capital * position_size
                pnl = risk_amount * pnl_pct
                capital += pnl
                
                # Add ML confidence if available
                ml_confidence = signal.get('ml_confidence', None)
                ml_validated = signal.get('ml_validated', None)
                
                trade_data = {
                    'asset': asset,
                    'entry_time': entry_time,
                    'exit_time': exit_time,
                    'signal': signal['signal'],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'exit_reason': exit_reason,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'capital': capital
                }
                
                # Add ML data if present
                if ml_confidence is not None:
                    trade_data['ml_confidence'] = ml_confidence
                if ml_validated is not None:
                    trade_data['ml_validated'] = ml_validated
                
                trades.append(trade_data)
            
            return {
                'trades': trades,
                'total_trades': len(trades),
                'final_capital': capital,
                'total_return': (capital - self.initial_capital) / self.initial_capital,
                'strategy_id': strategy_id
            }
            
        except Exception as e:
            return {"error": f"Strategy error: {str(e)}"}
    
    # Keep legacy method for backward compatibility
    def run_backtest_legacy(self, signals: pd.DataFrame, price_data: pd.DataFrame, asset: str) -> Dict:
        """Legacy method using pre-generated signals"""
        # Your existing implementation here
        pass
