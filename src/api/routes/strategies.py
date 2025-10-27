from fastapi import APIRouter, HTTPException, Query
from src.api.strategies import registry

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])

@router.get("/")
async def get_all_strategies():
    """Get all available strategies"""
    strategies = registry.list_strategies()
    return {
        "strategies": strategies,
        "count": len(strategies),
        "categories": {
            "core": registry.get_strategies_by_type("core"),
            "ml_validated": registry.get_strategies_by_type("ml_validated"),
            "ensemble": registry.get_strategies_by_type("ensemble")
        }
    }

@router.get("/{strategy_id}")
async def get_strategy_info(strategy_id: str):
    """Get detailed information about a specific strategy"""
    strategy_info = registry.get_strategy_info(strategy_id)
    if not strategy_info:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_id}' not found")
    
    return {
        "strategy_id": strategy_id,
        "name": strategy_info["name"],
        "description": strategy_info["description"],
        "parameters": strategy_info["parameters"]
    }

@router.get("/{strategy_id}/signals/{asset}")
async def get_strategy_signals(
    strategy_id: str,
    asset: str,
    lookback: int = Query(100, description="Number of records to analyze"),
    # You can add strategy parameters as query parameters
):
    """Get signals for a specific strategy and asset"""
    try:
        # This would need to integrate with your data loader
        # For now, return strategy info
        strategy_info = registry.get_strategy_info(strategy_id)
        return {
            "strategy": strategy_id,
            "asset": asset,
            "lookback": lookback,
            "parameters": strategy_info["parameters"] if strategy_info else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train/{strategy_id}")
async def train_strategy_model(strategy_id: str, asset: str = "XAUUSD"):
    """Train ML model for a strategy (async endpoint)"""
    try:
        # In production, you'd want to run this in background
        from ...train_models import train_signal_validator
        train_signal_validator(strategy_id, asset)
        
        return {
            "message": f"Training initiated for {strategy_id} on {asset}",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
