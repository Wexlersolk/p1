import pandas as pd
from typing import Dict, List
from .config import STRATEGY_CONFIG

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
    
    def run_backtest(self, signals: pd.DataFrame, price_data: pd.DataFrame, asset: str) -> Dict:
        """Simple backtest assuming we exit at session end"""
        if signals.empty:
            return {"error": f"No signals generated for {asset}"}
        
        config = STRATEGY_CONFIG.get(asset, STRATEGY_CONFIG["default"])
        trades = []
        capital = self.initial_capital
        
        for _, signal in signals.iterrows():
            entry_price = signal['price']
            entry_time = signal['timestamp']
            
            # Find exit price (next session open or end of data)
            exit_data = price_data[price_data.index > entry_time]
            if not exit_data.empty:
                exit_price = exit_data.iloc[0]['open']  # Simple exit at next open
                
                # Calculate P&L
                if signal['signal'] == 'LONG':
                    pnl_pct = (exit_price - entry_price) / entry_price
                else:  # SHORT
                    pnl_pct = (entry_price - exit_price) / entry_price
                
                pnl = capital * pnl_pct
                capital += pnl
                
                trades.append({
                    'asset': asset,
                    'entry_time': entry_time,
                    'exit_time': exit_data.index[0],
                    'signal': signal['signal'],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'capital': capital
                })
        
        return {
            'trades': trades,
            'total_trades': len(trades),
            'final_capital': capital,
            'total_return': (capital - self.initial_capital) / self.initial_capital
        }
