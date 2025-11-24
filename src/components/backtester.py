"""
Backtester component
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class Backtester:
    def __init__(self):
        self.initial_capital = 10000
        print("✅ Backtester component initialized")
    
    def run_backtest(self, strategy_id, data, asset):
        """
        Run backtest for a strategy on given data
        
        Args:
            strategy_id: Strategy identifier
            data: Market data DataFrame
            asset: Asset name
            
        Returns:
            Dictionary with backtest results
        """
        print(f"🧮 Running backtest for {asset} with {strategy_id}")
        print(f"   Data shape: {data.shape}")
        
        if data.empty:
            return {"error": "No data available for backtest"}
        
        try:
            # This is a simplified backtest implementation
            # You can expand this with your actual backtesting logic
            
            # Generate some sample trades based on simple logic
            trades = self._generate_sample_trades(data, asset)
            
            # Calculate portfolio values
            portfolio_values = self._calculate_portfolio_values(trades, data)
            
            # Calculate performance metrics
            metrics = self._calculate_metrics(trades, portfolio_values)
            
            return {
                "trades": trades,
                "portfolio_values": portfolio_values,
                "final_capital": metrics["final_capital"],
                "total_trades": metrics["total_trades"],
                "winning_trades": metrics["winning_trades"],
                "win_rate": metrics["win_rate"],
                "total_pnl": metrics["total_pnl"],
                "total_return_percent": metrics["total_return_percent"],
                "strategy": strategy_id,
                "asset": asset
            }
            
        except Exception as e:
            print(f"❌ Backtest error: {e}")
            return {"error": f"Backtest failed: {str(e)}"}
    
    def _generate_sample_trades(self, data, asset):
        """Generate sample trades for demonstration"""
        trades = []
        position = None
        
        for i in range(1, len(data)-1):
            current_time = data.index[i]
            current_price = data['close'].iloc[i]
            prev_price = data['close'].iloc[i-1]
            
            # Simple strategy: buy on dip, sell on rise
            if position is None and current_price < prev_price * 0.99:  # 1% drop
                # Enter long position
                position = {
                    'entry_time': current_time,
                    'entry_price': current_price,
                    'type': 'LONG',
                    'units': self.initial_capital * 0.1 / current_price  # 10% of capital
                }
                trades.append({
                    'entry_time': current_time,
                    'entry_price': current_price,
                    'type': 'LONG',
                    'units': position['units']
                })
                
            elif position is not None and current_price > position['entry_price'] * 1.02:  # 2% profit
                # Exit position
                exit_trade = {
                    'exit_time': current_time,
                    'exit_price': current_price,
                    'pnl': (current_price - position['entry_price']) * position['units'],
                    'pnl_percent': (current_price / position['entry_price'] - 1) * 100
                }
                trades[-1].update(exit_trade)
                position = None
        
        return trades
    
    def _calculate_portfolio_values(self, trades, data):
        """Calculate portfolio values over time"""
        portfolio = [{"timestamp": data.index[0], "value": self.initial_capital}]
        capital = self.initial_capital
        
        for trade in trades:
            if 'exit_time' in trade:
                # Update capital after trade completion
                capital += trade['pnl']
                portfolio.append({
                    "timestamp": trade['exit_time'],
                    "value": capital
                })
        
        return portfolio
    
    def _calculate_metrics(self, trades, portfolio_values):
        """Calculate performance metrics"""
        completed_trades = [t for t in trades if 'pnl' in t]
        winning_trades = [t for t in completed_trades if t['pnl'] > 0]
        
        final_capital = portfolio_values[-1]['value'] if portfolio_values else self.initial_capital
        total_pnl = final_capital - self.initial_capital
        
        return {
            "final_capital": final_capital,
            "total_trades": len(completed_trades),
            "winning_trades": len(winning_trades),
            "win_rate": len(winning_trades) / len(completed_trades) if completed_trades else 0,
            "total_pnl": total_pnl,
            "total_return_percent": (total_pnl / self.initial_capital) * 100
        }

# Create global instance
backtester = Backtester()
