from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from datetime import datetime
import math
from ..cache import get_from_cache, save_to_cache
from ..components import data_loader, strategy as vwap_strategy, backtester, analyzer
router = APIRouter()



def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    return obj

@router.get("/compare")
async def compare_assets(
    lookback: int = Query(100, ge=1, le=10000),
    strategy_id: str = Query("vwap_ib", description="Strategy to use for comparison")
):
    import traceback

    print(f"🔎 Starting compare_assets with lookback={lookback}")
    try:
        assets_data = data_loader.load_all_assets()
        print(f"✅ Loaded assets: {list(assets_data.keys())}")

        all_results = {}

        for asset, data in assets_data.items():
            print(f"➡ Processing {asset}")
            df_subset = data.tail(lookback)

            print(f"   🧠 Running backtest for {asset} with strategy '{strategy_id}'...")
            backtester.initial_capital = 10000  # Default capital for comparison

            results = backtester.run_backtest(strategy_id, df_subset, asset)
            
            if "error" in results:
                print(f"   ⚠️  Error for {asset}: {results['error']}")
                continue
                
            print(f"   ✅ Backtest done for {asset}")
            print(f"      Total trades: {results.get('total_trades', 0)}")
            
            all_results[asset] = results
        
        if not all_results:
            return {"error": "No successful backtests completed"}

        print("📊 Running analyzer.compare_assets ...")
        comparison_df = analyzer.compare_assets(all_results)
        print("✅ Comparison done")

        result = comparison_df.to_dict(orient="records")
        result = sanitize_for_json(result)  # sanitize before returning

        print("🗄️ Saving to cache ...")
        save_to_cache(f"compare_{lookback}", result)
        print("✅ Done successfully")

        return result

    except Exception as e:
        print("❌ Exception caught in compare_assets():", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error comparing assets: {str(e)}")



@router.get("/{asset}")
async def run_backtest(
    asset: str,
    lookback: int = Query(100, ge=1, le=10000),
    initial_capital: float = Query(10000, ge=100),
    strategy_id: str = Query("vwap_ib", description="Strategy to use (vwap, opening_range, etc.)")
):
    """Run backtest for a specific asset"""
    cache_key = f"backtest_{asset}_{lookback}_{initial_capital}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    try:
        print(f"🔎 Starting backtest for {asset}, lookback={lookback}")
        
        assets_data = data_loader.load_all_assets()
        if asset not in assets_data:
            raise HTTPException(status_code=404, detail=f"Asset {asset} not found")
        
        df = assets_data[asset]
        df_subset = df.tail(lookback)
        
        print(f"✅ Data loaded: {len(df_subset)} rows")
        
        # Run backtest using the registry strategy
        print(f"🧠 Running backtest with strategy '{strategy_id}'...")
        backtester.initial_capital = initial_capital
        results = backtester.run_backtest(strategy_id, df_subset, asset)
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        print(f"✅ Backtest completed")
        print(f"   Results keys: {list(results.keys())}")
        
        # Deep convert all DataFrames and Series to dicts
        serialized_results = {}
        for key, val in results.items():
            print(f"   Processing key '{key}': type={type(val)}")
            
            if isinstance(val, pd.DataFrame):
                print(f"      Converting DataFrame with shape {val.shape}")
                serialized_results[key] = val.to_dict(orient="records")
            elif isinstance(val, pd.Series):
                print(f"      Converting Series with length {len(val)}")
                serialized_results[key] = val.to_dict()
            elif isinstance(val, (list, dict)):
                serialized_results[key] = sanitize_for_json(val)
            else:
                serialized_results[key] = val
        
        # Process datetime objects in trades
        if "trades" in serialized_results and isinstance(serialized_results["trades"], list):
            for trade in serialized_results["trades"]:
                if isinstance(trade, dict):
                    # Handle entry_time
                    if "entry_time" in trade:
                        if isinstance(trade["entry_time"], datetime):
                            trade["entry_time"] = trade["entry_time"].isoformat()
                        elif hasattr(trade["entry_time"], 'isoformat'):
                            trade["entry_time"] = trade["entry_time"].isoformat()
                        elif isinstance(trade["entry_time"], str):
                            pass  # Already a string
                        else:
                            trade["entry_time"] = str(trade["entry_time"])
                    
                    # Handle exit_time
                    if "exit_time" in trade:
                        if isinstance(trade["exit_time"], datetime):
                            trade["exit_time"] = trade["exit_time"].isoformat()
                        elif hasattr(trade["exit_time"], 'isoformat'):
                            trade["exit_time"] = trade["exit_time"].isoformat()
                        elif isinstance(trade["exit_time"], str):
                            pass  # Already a string
                        else:
                            trade["exit_time"] = str(trade["exit_time"])
        
        # Final sanitization
        serialized_results = sanitize_for_json(serialized_results)
        
        print("🗄️ Saving to cache...")
        save_to_cache(cache_key, serialized_results)
        print("✅ Done successfully")
        
        return serialized_results
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

