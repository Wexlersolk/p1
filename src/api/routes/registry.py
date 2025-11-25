# src/api/strategies/registry.py
from typing import Dict, List, Optional

# Strategy registry
STRATEGY_REGISTRY = {
    "vwap_ib": {
        "name": "VWAP with Inside Bar",
        "description": "Volume Weighted Average Price with Inside Bar pattern detection",
        "parameters": {
            "lookback": {"type": "int", "default": 100, "description": "Lookback period for VWAP calculation"},
            "volume_threshold": {"type": "float", "default": 1.5, "description": "Minimum volume threshold"},
        },
        "type": "core"
    },
    "sma_crossover": {
        "name": "Simple Moving Average Crossover",
        "description": "Dual moving average crossover strategy",
        "parameters": {
            "fast_ma": {"type": "int", "default": 20, "description": "Fast moving average period"},
            "slow_ma": {"type": "int", "default": 50, "description": "Slow moving average period"}
        },
        "type": "core"
    },
    "rsi_oversold": {
        "name": "RSI Oversold Strategy", 
        "description": "RSI-based oversold/overbought signals",
        "parameters": {
            "rsi_period": {"type": "int", "default": 14, "description": "RSI period"},
            "oversold": {"type": "int", "default": 30, "description": "Oversold threshold"},
            "overbought": {"type": "int", "default": 70, "description": "Overbought threshold"}
        },
        "type": "core"
    }
}

def list_strategies() -> List[str]:
    """Get list of all available strategy IDs"""
    return list(STRATEGY_REGISTRY.keys())

def get_strategy_info(strategy_id: str) -> Optional[Dict]:
    """Get detailed information about a specific strategy"""
    return STRATEGY_REGISTRY.get(strategy_id)

def get_strategies_by_type(strategy_type: str) -> List[str]:
    """Get strategies filtered by type"""
    return [
        strategy_id for strategy_id, info in STRATEGY_REGISTRY.items()
        if info.get("type") == strategy_type
    ]

def get_strategy(strategy_id: str):
    """Get strategy instance - placeholder for actual strategy objects"""
    # This would return actual strategy objects in a real implementation
    return {"id": strategy_id, **STRATEGY_REGISTRY.get(strategy_id, {})}

def get_all_strategies() -> Dict:
    """Get all strategies"""
    return STRATEGY_REGISTRY
