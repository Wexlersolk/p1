import pandas as pd
from src.data_loader import DataLoader
from src.vwap_strategy import VWAPStrategy
from src.backtest_engine import BacktestEngine
from src.results_analyzer import ResultsAnalyzer

def main():
    print("🚀 Starting Multi-Asset VWAP Backtest...")
    
    # Load data
    loader = DataLoader()
    assets_data = loader.load_all_assets()
    
    # Initialize components
    strategy = VWAPStrategy()
    backtester = BacktestEngine()
    analyzer = ResultsAnalyzer()
    
    # Run backtest for each asset
    all_results = {}
    
    for asset, data in assets_data.items():
        print(f"\n📊 Backtesting {asset}...")
        
        # Generate signals
        signals = strategy.generate_signals(data, asset)
        print(f"   Generated {len(signals)} signals")
        
        # Run backtest
        results = backtester.run_backtest(signals, data, asset)
        all_results[asset] = results
        
        if 'trades' in results:
            print(f"   Completed {len(results['trades'])} trades")
            print(f"   Total Return: {results['total_return']:.2f}%")
    
    # Compare all assets
    print("\n" + "="*50)
    print("📈 COMPARISON ACROSS ALL ASSETS")
    print("="*50)
    
    comparison_df = analyzer.compare_assets(all_results)
    print(comparison_df.to_string(index=False))

if __name__ == "__main__":
    main()
