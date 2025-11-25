from fastapi import FastAPI, HTTPException, Query, Depends
from typing import Dict, List, Optional
import pandas as pd
from .config import API_PREFIX
from .components import data_loader, strategy, backtester, analyzer
import json
from functools import lru_cache
from datetime import datetime
import time

# Create FastAPI application
app = FastAPI(
    title="Financial Market Prediction API",
    description="API for predicting financial market movements using VWAP and other strategies",
    version="1.0.0",
)

# In-memory cache
cache = {}
cache_ttl = 300  # 5 minutes cache TTL

# Dependency to load asset data
@lru_cache(maxsize=32)
def get_assets_data():
    """Load all asset data with caching"""
    return data_loader.load_all_assets()

def get_asset_data(asset: str):
    """Get specific asset data or raise 404"""
    assets_data = get_assets_data()
    if asset not in assets_data:
        raise HTTPException(status_code=404, detail=f"Asset {asset} not found")
    return assets_data[asset]

# Endpoints
@app.get(f"{API_PREFIX}/assets", response_model=List[str])
async def list_assets():
    """List all available assets"""
    assets_data = get_assets_data()
    return list(assets_data.keys())

@app.get(f"{API_PREFIX}/assets/{{asset}}/data")
async def get_asset_data_endpoint(asset: str, limit: int = Query(100, ge=1, le=10000)):
    """Get OHLCV data for a specific asset"""
    cache_key = f"asset_data_{asset}_{limit}"
    if cache_key in cache and time.time() - cache[cache_key]["timestamp"] < cache_ttl:
        return cache[cache_key]["data"]
    
    df = get_asset_data(asset)
    result = df.tail(limit).reset_index().to_dict(orient="records")
    
    # Convert datetime objects to ISO strings
    for item in result:
        if "datetime" in item and isinstance(item["datetime"], datetime):
            item["datetime"] = item["datetime"].isoformat()
    
    # Cache the result
    cache[cache_key] = {
        "timestamp": time.time(),
        "data": result
    }
    
    return result

@app.get(f"{API_PREFIX}/strategies")
async def list_strategies():
    """List all available strategies"""
    # Currently only VWAP is implemented
    return ["vwap"]

@app.get(f"{API_PREFIX}/strategies/vwap/signals/{{asset}}")
async def generate_vwap_signals(
    asset: str, 
    lookback: int = Query(100, ge=1, le=1000)
):
    """Generate VWAP signals for a specific asset"""
    cache_key = f"vwap_signals_{asset}_{lookback}"
    if cache_key in cache and time.time() - cache[cache_key]["timestamp"] < cache_ttl:
        return cache[cache_key]["data"]
    
    df = get_asset_data(asset)
    signals = strategy.generate_signals(df.tail(lookback), asset)
    
    if signals.empty:
        result = []
    else:
        result = signals.reset_index().to_dict(orient="records")
        # Convert datetime objects to ISO strings
        for item in result:
            if "timestamp" in item and isinstance(item["timestamp"], datetime):
                item["timestamp"] = item["timestamp"].isoformat()
    
    # Cache the result
    cache[cache_key] = {
        "timestamp": time.time(),
        "data": result
    }
    
    return result

@app.get(f"{API_PREFIX}/backtest/{{asset}}")
async def run_backtest(
    asset: str,
    lookback: int = Query(100, ge=1, le=10000),
    initial_capital: float = Query(10000, ge=100)
):
    """Run backtest for a specific asset"""
    cache_key = f"backtest_{asset}_{lookback}_{initial_capital}"
    if cache_key in cache and time.time() - cache[cache_key]["timestamp"] < cache_ttl:
        return cache[cache_key]["data"]
    
    df = get_asset_data(asset)
    df_subset = df.tail(lookback)
    
    # Generate signals
    signals = strategy.generate_signals(df_subset, asset)
    if signals.empty:
        return {"error": f"No signals generated for {asset} with current parameters"}
    
    # Run backtest
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
    cache[cache_key] = {
        "timestamp": time.time(),
        "data": results
    }
    
    return results

@app.get(f"{API_PREFIX}/metrics/{{asset}}")
async def get_metrics(asset: str, lookback: int = Query(100, ge=1, le=10000)):
    """Get performance metrics for a specific asset"""
    cache_key = f"metrics_{asset}_{lookback}"
    if cache_key in cache and time.time() - cache[cache_key]["timestamp"] < cache_ttl:
        return cache[cache_key]["data"]
    
    # Run backtest to get trades
    df = get_asset_data(asset)
    df_subset = df.tail(lookback)
    
    # Generate signals
    signals = strategy.generate_signals(df_subset, asset)
    if signals.empty:
        return {"error": f"No signals generated for {asset} with current parameters"}
    
    # Run backtest
    results = backtester.run_backtest(signals, df_subset, asset)
    
    # Calculate metrics
    if "trades" in results and results["trades"]:
        metrics = analyzer.calculate_metrics(results["trades"])
        
        # Cache the result
        cache[cache_key] = {
            "timestamp": time.time(),
            "data": metrics
        }
        
        return metrics
    else:
        return {"error": f"No trades for {asset} with current parameters"}

@app.get(f"{API_PREFIX}/compare")
async def compare_assets(lookback: int = Query(100, ge=1, le=10000)):
    """Compare performance across all assets"""
    cache_key = f"compare_{lookback}"
    if cache_key in cache and time.time() - cache[cache_key]["timestamp"] < cache_ttl:
        return cache[cache_key]["data"]
    
    assets_data = get_assets_data()
    all_results = {}
    
    for asset, data in assets_data.items():
        # Generate signals
        signals = strategy.generate_signals(data.tail(lookback), asset)
        if not signals.empty:
            # Run backtest
            results = backtester.run_backtest(signals, data.tail(lookback), asset)
            all_results[asset] = results
    
    # Compare assets
    comparison_df = analyzer.compare_assets(all_results)
    result = comparison_df.to_dict(orient="records")
    
    # Cache the result
    cache[cache_key] = {
        "timestamp": time.time(),
        "data": result
    }
    
    return result

