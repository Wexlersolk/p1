from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
from ..cache import get_from_cache, save_to_cache
from ..components import data_loader, strategy as vwap_strategy, backtester, analyzer

router = APIRouter()

@router.get("/{asset}")
async def run_backtest(
    asset: str,
    lookback: int = Query(100, ge=1, le=10000),
    initial_capital: float = Query(10000, ge=100)
):
    """Run backtest for a specific asset"""
    cache_key = f"backtest_{asset}_{lookback}_{initial_capital}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    try:
        assets_data = data_loader.load_all_assets()
        if asset not in assets_data:
            raise HTTPException(status_code=404, detail=f"Asset {asset} not found")
        
        df = assets_data[asset]
        df_subset = df.tail(lookback)
        
        # Оскільки у нас немає методу generate_signals, створимо сигнали на основі VWAP
        vwap_series = vwap_strategy.calculate_vwap(df_subset)
        
        # Створюємо прості сигнали: якщо ціна закриття вища за VWAP, то LONG
        signals_data = []
        
        for idx, row in df_subset.iterrows():
            if idx not in vwap_series.index:
                continue
                
            vwap_value = vwap_series.loc[idx]
            if pd.isna(vwap_value):
                continue
                
            if row['close'] > vwap_value and row['close'] > row['open']:
                signals_data.append({
                    'timestamp': idx,
                    'asset': asset,
                    'signal': 'LONG',
                    'price': row['close'],
                    'vwap': vwap_value
                })
            elif row['close'] < vwap_value and row['close'] < row['open']:
                signals_data.append({
                    'timestamp': idx,
                    'asset': asset,
                    'signal': 'SHORT',
                    'price': row['close'],
                    'vwap': vwap_value
                })
        
        signals = pd.DataFrame(signals_data)
        
        if signals.empty:
            return {"error": f"No signals generated for {asset} with current parameters"}
        
        # Run backtest using existing engine
        backtester.initial_capital = initial_capital
        results = backtester.run_backtest(signals, df_subset, asset)
        
        # Process results for JSON serialization
        if "trades" in results:
            for trade in results["trades"]:
                if "entry_time" in trade and isinstance(trade["entry_time"], datetime):
                    trade["entry_time"] = trade["entry_time"].isoformat()
                if "exit_time" in trade and isinstance(trade["exit_time"], datetime):
                    trade["exit_time"] = trade["exit_time"].isoformat()
        
        # Cache the result
        save_to_cache(cache_key, results)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")

@router.get("/metrics/{asset}")
async def get_metrics(asset: str, lookback: int = Query(100, ge=1, le=10000)):
    """Get performance metrics for a specific asset"""
    cache_key = f"metrics_{asset}_{lookback}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    try:
        assets_data = data_loader.load_all_assets()
        if asset not in assets_data:
            raise HTTPException(status_code=404, detail=f"Asset {asset} not found")
        
        df = assets_data[asset]
        df_subset = df.tail(lookback)
        
        # Створюємо сигнали на основі VWAP (аналогічно до методу run_backtest)
        vwap_series = vwap_strategy.calculate_vwap(df_subset)
        
        signals_data = []
        for idx, row in df_subset.iterrows():
            if idx not in vwap_series.index:
                continue
                
            vwap_value = vwap_series.loc[idx]
            if pd.isna(vwap_value):
                continue
                
            if row['close'] > vwap_value and row['close'] > row['open']:
                signals_data.append({
                    'timestamp': idx,
                    'asset': asset,
                    'signal': 'LONG',
                    'price': row['close'],
                    'vwap': vwap_value
                })
            elif row['close'] < vwap_value and row['close'] < row['open']:
                signals_data.append({
                    'timestamp': idx,
                    'asset': asset,
                    'signal': 'SHORT',
                    'price': row['close'],
                    'vwap': vwap_value
                })
        
        signals = pd.DataFrame(signals_data)
        
        if signals.empty:
            return {"error": f"No signals generated for {asset} with current parameters"}
        
        # Run backtest
        results = backtester.run_backtest(signals, df_subset, asset)
        
        # Calculate metrics
        if "trades" in results and results["trades"]:
            metrics = analyzer.calculate_metrics(results["trades"])
            
            # Cache the result
            save_to_cache(cache_key, metrics)
            
            return metrics
        else:
            return {"error": f"No trades for {asset} with current parameters"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating metrics: {str(e)}")

@router.get("/compare")
async def compare_assets(lookback: int = Query(100, ge=1, le=10000)):
    """Compare performance across all assets"""
    cache_key = f"compare_{lookback}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    try:
        assets_data = data_loader.load_all_assets()
        all_results = {}
        
        for asset, data in assets_data.items():
            df_subset = data.tail(lookback)
            
            # Створюємо сигнали на основі VWAP
            vwap_series = vwap_strategy.calculate_vwap(df_subset)
            
            signals_data = []
            for idx, row in df_subset.iterrows():
                if idx not in vwap_series.index:
                    continue
                    
                vwap_value = vwap_series.loc[idx]
                if pd.isna(vwap_value):
                    continue
                    
                if row['close'] > vwap_value and row['close'] > row['open']:
                    signals_data.append({
                        'timestamp': idx,
                        'asset': asset,
                        'signal': 'LONG',
                        'price': row['close'],
                        'vwap': vwap_value
                    })
                elif row['close'] < vwap_value and row['close'] < row['open']:
                    signals_data.append({
                        'timestamp': idx,
                        'asset': asset,
                        'signal': 'SHORT',
                        'price': row['close'],
                        'vwap': vwap_value
                    })
            
            signals = pd.DataFrame(signals_data)
            
            if not signals.empty:
                # Run backtest
                results = backtester.run_backtest(signals, df_subset, asset)
                all_results[asset] = results
        
        # Compare assets
        comparison_df = analyzer.compare_assets(all_results)
        result = comparison_df.to_dict(orient="records")
        
        # Cache the result
        save_to_cache(cache_key, result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing assets: {str(e)}")