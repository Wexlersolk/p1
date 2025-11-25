"""
Analyzer component for performance analysis
"""
import pandas as pd
import numpy as np

class Analyzer:
    def __init__(self):
        print("✅ Analyzer component initialized")
    
    def compare_assets(self, results):
        """
        Compare performance across multiple assets
        
        Args:
            results: Dictionary of backtest results by asset
            
        Returns:
            DataFrame with comparison metrics
        """
        print("📊 Comparing assets...")
        
        comparison_data = []
        
        for asset, result in results.items():
            if "error" in result:
                # Skip assets with errors
                continue
                
            metrics = {
                'asset': asset,
                'final_capital': result.get('final_capital', 0),
                'total_trades': result.get('total_trades', 0),
                'winning_trades': result.get('winning_trades', 0),
                'win_rate': result.get('win_rate', 0),
                'total_pnl': result.get('total_pnl', 0),
                'total_return_percent': result.get('total_return_percent', 0),
                'strategy': result.get('strategy', 'unknown')
            }
            
            # Calculate additional metrics
            if result.get('trades'):
                trades = result['trades']
                completed_trades = [t for t in trades if 'pnl' in t]
                if completed_trades:
                    pnls = [t['pnl'] for t in completed_trades]
                    metrics['avg_trade_pnl'] = np.mean(pnls)
                    metrics['best_trade'] = max(pnls) if pnls else 0
                    metrics['worst_trade'] = min(pnls) if pnls else 0
                else:
                    metrics['avg_trade_pnl'] = 0
                    metrics['best_trade'] = 0
                    metrics['worst_trade'] = 0
            
            comparison_data.append(metrics)
        
        # Create DataFrame and sort by performance
        df = pd.DataFrame(comparison_data)
        if not df.empty and 'total_return_percent' in df.columns:
            df = df.sort_values('total_return_percent', ascending=False)
        
        print(f"✅ Compared {len(comparison_data)} assets")
        return df
    
    def calculate_detailed_metrics(self, trades, portfolio_values):
        """Calculate detailed performance metrics for a single asset"""
        if not trades or not portfolio_values:
            return {}
        
        completed_trades = [t for t in trades if 'pnl' in t]
        if not completed_trades:
            return {}
        
        pnls = [t['pnl'] for t in completed_trades]
        returns = [t['pnl_percent'] for t in completed_trades]
        
        # Basic metrics
        total_trades = len(completed_trades)
        winning_trades = len([t for t in completed_trades if t['pnl'] > 0])
        win_rate = winning_trades / total_trades
        
        # Advanced metrics
        avg_win = np.mean([t['pnl'] for t in completed_trades if t['pnl'] > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t['pnl'] for t in completed_trades if t['pnl'] < 0]) if (total_trades - winning_trades) > 0 else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Drawdown calculation
        portfolio_values_df = pd.DataFrame(portfolio_values)
        portfolio_values_df['peak'] = portfolio_values_df['value'].cummax()
        portfolio_values_df['drawdown'] = (portfolio_values_df['value'] - portfolio_values_df['peak']) / portfolio_values_df['peak']
        max_drawdown = portfolio_values_df['drawdown'].min()
        
        return {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': max(pnls) if pnls else 0,
            'largest_loss': min(pnls) if pnls else 0,
            'avg_trade_return': np.mean(returns) if returns else 0,
            'total_return': portfolio_values[-1]['value'] - portfolio_values[0]['value'],
            'max_drawdown': max_drawdown,
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'calmar_ratio': self._calculate_calmar_ratio(returns, max_drawdown)
        }
    
    def _calculate_sharpe_ratio(self, returns, risk_free_rate=0.02):
        """Calculate Sharpe ratio (annualized)"""
        if not returns or np.std(returns) == 0:
            return 0
        excess_returns = [r - risk_free_rate/252 for r in returns]  # Daily risk-free rate
        return (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(252)
    
    def _calculate_calmar_ratio(self, returns, max_drawdown):
        """Calculate Calmar ratio"""
        if not returns or max_drawdown == 0:
            return 0
        annual_return = np.mean(returns) * 252
        return annual_return / abs(max_drawdown)

# Create global instance
analyzer = Analyzer()
