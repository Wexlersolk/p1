from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import pandas as pd
from ..cache import get_from_cache, save_to_cache
from ..components import data_loader, strategy as vwap_strategy
from datetime import datetime

router = APIRouter()

@router.get("/")
async def list_strategies():
    """List all available strategies"""
    # Currently only VWAP is implemented, but can be expanded
    return ["vwap"]

@router.get("/vwap/signals/{asset}")
async def generate_vwap_signals(
    asset: str, 
    lookback: int = Query(100, ge=1, le=1000)
):
    """Generate VWAP signals for a specific asset"""
    cache_key = f"vwap_signals_{asset}_{lookback}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    try:
        # Import the function used in original code
        from ...vwap_strategy import VWAPStrategy
        
        assets_data = data_loader.load_all_assets()
        if asset not in assets_data:
            raise HTTPException(status_code=404, detail=f"Asset {asset} not found")
        
        df = assets_data[asset]
        
        # Використовуємо публічні методи класу VWAPStrategy
        vwap = vwap_strategy.calculate_vwap(df.tail(lookback))
        
        # Створюємо спрощений результат, оскільки оригінальна функція generate_signals не доступна
        result = []
        for idx, row in df.tail(lookback).iterrows():
            vwap_value = vwap.loc[idx] if idx in vwap.index else None
            if vwap_value is not None and not pd.isna(vwap_value):
                signal = None
                if row['close'] > vwap_value and row['close'] > row['open']:
                    signal = 'LONG'
                elif row['close'] < vwap_value and row['close'] < row['open']:
                    signal = 'SHORT'
                
                if signal:
                    result.append({
                        'timestamp': idx.isoformat(),
                        'asset': asset,
                        'signal': signal,
                        'price': row['close'],
                        'vwap': vwap_value
                    })
        
        # Cache the result
        save_to_cache(cache_key, result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signals: {str(e)}")

@router.get("/vwap/parameters")
async def get_vwap_parameters():
    """Get VWAP strategy parameters"""
    from ...config import STRATEGY_CONFIG
    
    return {
        "default": STRATEGY_CONFIG["default"],
        "assets": {k: v for k, v in STRATEGY_CONFIG.items() if k != "default"}
    }

@router.get("/vwap/calculation/{asset}")
async def get_vwap_calculation(
    asset: str,
    lookback: int = Query(100, ge=1, le=1000)
):
    """Get VWAP calculation for a specific asset"""
    cache_key = f"vwap_calc_{asset}_{lookback}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    try:
        assets_data = data_loader.load_all_assets()
        if asset not in assets_data:
            raise HTTPException(status_code=404, detail=f"Asset {asset} not found")
        
        df = assets_data[asset].tail(lookback).copy()
        df['vwap'] = vwap_strategy.calculate_vwap(df)
        
        result = []
        for idx, row in df.iterrows():
            if not pd.isna(row['vwap']):
                result.append({
                    'timestamp': idx.isoformat(),
                    'close': row['close'],
                    'vwap': row['vwap']
                })
        
        # Cache the result
        save_to_cache(cache_key, result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating VWAP: {str(e)}")