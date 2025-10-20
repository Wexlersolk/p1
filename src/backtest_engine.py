import pandas as pd
from typing import Dict
# Import the strategy registry
from .api.strategies import registry

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
    
    def run_backtest(self, strategy_id: str, df: pd.DataFrame, asset: str, parameters: dict = None) -> Dict:
        """Run backtest with specified strategy"""
        try:
            # Get strategy from registry
            strategy = registry.get_strategy(strategy_id, parameters)
            
            # Generate signals using the strategy
            signals = strategy.generate_signals(df, asset)
            
            if signals.empty:
                return {"error": f"No signals generated for {asset} with strategy {strategy_id}"}
            
            # Your existing backtest logic continues here...
            trades = []
            capital = self.initial_capital
            
            for _, signal in signals.iterrows():
                # Your existing trade execution logic...
                # [Keep all your existing backtest code here]
                pass
                
            return {
                'trades': trades,
                'total_trades': len(trades),
                'final_capital': capital,
                'total_return': (capital - self.initial_capital) / self.initial_capital
            }
            
        except Exception as e:
            return {"error": f"Strategy error: {str(e)}"}
