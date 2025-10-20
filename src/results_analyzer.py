import pandas as pd
from typing import Dict

class ResultsAnalyzer:
    @staticmethod
    def calculate_metrics(trades: list) -> Dict:
        """Calculate performance metrics"""
        if not trades:
            return {}
        
        # Convert trades to DataFrame
        df = pd.DataFrame(trades)
        
        # Handle both 'pnl' and 'profit' naming conventions
        if 'pnl' not in df.columns and 'profit' in df.columns:
            df['pnl'] = df['profit']
        
        # Make sure required columns exist
        if 'pnl' not in df.columns:
            print(f"Warning: No 'pnl' or 'profit' column found in trades data. Available columns: {df.columns.tolist()}")
            return {
                'total_trades': len(df),
                'error': "No profit/loss data available"
            }
        
        # Basic metrics
        total_return = df['pnl'].sum()
        win_rate = (df['pnl'] > 0).mean()
        avg_win = df[df['pnl'] > 0]['pnl'].mean() if not df[df['pnl'] > 0].empty else 0
        avg_loss = df[df['pnl'] < 0]['pnl'].mean() if not df[df['pnl'] < 0].empty else 0
        
        # Calculate profit factor safely
        if not df[df['pnl'] < 0].empty and df[df['pnl'] < 0]['pnl'].sum() != 0:
            profit_factor = abs(df[df['pnl'] > 0]['pnl'].sum() / df[df['pnl'] < 0]['pnl'].sum())
        else:
            profit_factor = float('inf')
        
        # Handle capital calculation if available
        total_return_pct = 0
        if 'capital' in df.columns and len(df) > 0:
            total_return_pct = (df['capital'].iloc[-1] - df['capital'].iloc[0]) / df['capital'].iloc[0]
        elif 'return_pct' in df.columns:
            total_return_pct = df['return_pct'].sum()
        
        return {
            'total_trades': len(df),
            'total_return': total_return,
            'total_return_pct': total_return_pct,
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
        import traceback
        
        print(f"ResultsAnalyzer.compare_assets called with {len(results)} assets")
        
        comparison = []
        for asset, result in results.items():
            try:
                print(f"Processing asset {asset} for comparison")
                if 'trades' in result and result['trades']:
                    print(f"Asset {asset} has {len(result['trades'])} trades")
                    
                    # Debug first trade
                    if len(result['trades']) > 0:
                        first_trade = result['trades'][0]
                        print(f"First trade keys: {list(first_trade.keys())}")
                    
                    metrics = ResultsAnalyzer.calculate_metrics(result['trades'])
                    metrics['asset'] = asset
                    comparison.append(metrics)
                    print(f"Added metrics for {asset}: {metrics}")
                else:
                    print(f"Skipping asset {asset}: No trades found or empty trades list")
            except Exception as e:
                print(f"Error processing asset {asset} in compare_assets: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                # Continue with other assets instead of failing entirely
                continue
        
        if not comparison:
            print("Warning: No assets produced valid metrics for comparison")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['asset', 'total_trades', 'total_return', 'win_rate'])
            
        print(f"Creating DataFrame from {len(comparison)} assets")
        return pd.DataFrame(comparison)
