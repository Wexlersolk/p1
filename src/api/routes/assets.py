from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
import time
from src.data_loader import DataLoader
from src.api.cache import get_from_cache, save_to_cache
from src.api.components import data_loader  # Використовуємо спільний екземпляр DataLoader

router = APIRouter()

@router.get("/", response_model=List[str])
async def list_assets():
    """List all available assets"""
    cache_key = "list_assets"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        print(f"🔍 Returning cached assets list with {len(cached_data)} assets")
        return cached_data
    
    print(f"🔍 Loading assets data from {data_loader.data_folder}")
    assets_data = data_loader.load_all_assets()
    result = list(assets_data.keys())
    
    print(f"🔍 Found {len(result)} assets: {result[:5]}{'...' if len(result) > 5 else ''}")
    
    # Cache the result
    save_to_cache(cache_key, result)
    
    return result

@router.get("/{asset}/data")
async def get_asset_data(asset: str, limit: int = Query(100, ge=1, le=10000)):
    """Get OHLCV data for a specific asset"""
    cache_key = f"asset_data_{asset}_{limit}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    try:
        assets_data = data_loader.load_all_assets()
        if asset not in assets_data:
            raise HTTPException(status_code=404, detail=f"Asset {asset} not found")
        
        df = assets_data[asset]
        result = df.tail(limit).reset_index().to_dict(orient="records")
        
        # Convert datetime objects to ISO strings
        for item in result:
            if "datetime" in item and isinstance(item["datetime"], datetime):
                item["datetime"] = item["datetime"].isoformat()
        
        # Cache the result
        save_to_cache(cache_key, result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading asset data: {str(e)}")

@router.get("/{asset}/info")
async def get_asset_info(asset: str):
    """Get general information about an asset"""
    cache_key = f"asset_info_{asset}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    try:
        assets_data = data_loader.load_all_assets()
        if asset not in assets_data:
            raise HTTPException(status_code=404, detail=f"Asset {asset} not found")
        
        df = assets_data[asset]
        
        # Calculate basic statistics
        result = {
            "asset": asset,
            "rows": len(df),
            "start_date": df.index[0].isoformat() if len(df) > 0 else None,
            "end_date": df.index[-1].isoformat() if len(df) > 0 else None,
            "mean_price": float(df["close"].mean()) if len(df) > 0 else None,
            "min_price": float(df["low"].min()) if len(df) > 0 else None,
            "max_price": float(df["high"].max()) if len(df) > 0 else None,
            "total_volume": float(df["volume"].sum()) if len(df) > 0 else None,
        }
        
        # Cache the result
        save_to_cache(cache_key, result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting asset info: {str(e)}")

@router.get("/exchanges")
async def list_exchanges():
    """List all available exchanges in the dataset"""
    cache_key = "list_exchanges"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Get unique exchanges from file paths
    exchanges = data_loader.get_available_exchanges()
    
    # Cache the result
    save_to_cache(cache_key, exchanges)
    
    return exchanges

@router.get("/timeframes")
async def list_timeframes():
    """List all available timeframes in the dataset"""
    cache_key = "list_timeframes"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Get unique timeframes from file paths
    timeframes = data_loader.get_available_timeframes()
    
    # Cache the result
    save_to_cache(cache_key, timeframes)
    
    return timeframes