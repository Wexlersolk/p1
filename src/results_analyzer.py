import pandas as pd
from typing import Dict

class ResultsAnalyzer:
    @staticmethod
    def calculate_metrics(trades: list) -> Dict:
        """Calculate performance metrics"""
        if not trades:
            return {}
        
        df = pd.DataFrame(trades)
        
        # Basic metrics
        total_return = df['pnl'].sum()
        win_rate = (df['pnl'] > 0).mean()
        avg_win = df[df['pnl'] > 0]['pnl'].mean()
        avg_loss = df[df['pnl'] < 0]['pnl'].mean()
        profit_factor = abs(df[df['pnl'] > 0]['pnl'].sum() / df[df['pnl'] < 0]['pnl'].sum()) if df[df['pnl'] < 0]['pnl'].sum() != 0 else float('inf')
        
        return {
            'total_trades': len(df),
            'total_return': total_return,
            'total_return_pct': (df['capital'].iloc[-1] - df['capital'].iloc[0]) / df['capital'].iloc[0] if len(df) > 0 else 0,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'largest_win': df['pnl'].max(),
            'largest_loss': df['pnl'].min(),
        }
    
    @staticmethod
    def compare_assets(results: Dict[str, Dict]) -> pd.DataFrame:
        """Compare performance across all assets"""
        comparison = []
        for asset, result in results.items():
            if 'trades' in result:
                metrics = ResultsAnalyzer.calculate_metrics(result['trades'])
                metrics['asset'] = asset
                comparison.append(metrics)
        
        return pd.DataFrame(comparison)
