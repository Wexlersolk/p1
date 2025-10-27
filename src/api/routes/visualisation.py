from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
import traceback
from src.visualisation.strategy_dashboard import StrategyDashboard
from src.visualisation.confidence_analysis import ConfidenceAnalysis
from src.visualisation.signal_timeline import SignalTimeline
import pandas as pd

router = APIRouter(prefix="/api/v1/visualization", tags=["visualization"])
import pprint

def deep_inspect(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            deep_inspect(v, f"{path}.{k}")
    elif isinstance(obj, list):
        if obj:
            print(f"{path}: list, first element type: {type(obj[0])}")
            if isinstance(obj[0], list):
                print(f"  {path}: ⚠️ first element is a list of length {len(obj[0])}")
            elif isinstance(obj[0], dict):
                print(f"  {path}: first element keys: {list(obj[0].keys())}")
            else:
                print(f"  {path}: first element value: {obj[0]}")
        else:
            print(f"{path}: empty list")
    else:
        print(f"{path}: {type(obj)}")


def sanitize_for_json(obj):
    import pandas as pd
    import numpy as np

    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Якщо це список списків (наприклад, [[0, "#000"], ...]), конвертуємо у список словників
        if obj and isinstance(obj[0], list):
            # Якщо це colorscale (довжина 2), робимо список словників
            if len(obj[0]) == 2:
                return [{"value": v[0], "color": v[1]} for v in obj]
            # Якщо це просто список списків, конвертуємо у список з ключами "item0", "item1", ...
            else:
                return [
                    {f"item{i}": val for i, val in enumerate(v)}
                    for v in obj
                ]
        else:
            return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    else:
        return obj
    
@router.get("/strategy-dashboard/{asset}")
async def get_strategy_dashboard(
    asset: str,
    days: int = Query(30, description="Number of days to analyze"),
    initial_capital: float = Query(10000, description="Initial capital for backtesting")
):
    """Get comprehensive strategy performance dashboard"""
    try:

        dashboard = StrategyDashboard()
        result = dashboard.generate_dashboard(asset, days, initial_capital)
        
        print("=== DASHBOARD RESULT TYPE ===", type(result))
        if isinstance(result, dict):
            for k, v in result.items():
                print(f"KEY: {k}, TYPE: {type(v)}")
                if isinstance(v, list):
                    print(f"  First element type: {type(v[0]) if v else 'empty'}")
                    if isinstance(v[0], list):
                        print(f"  First element (list) length: {len(v[0])}")
        elif isinstance(result, list):
            print(f"List element type: {type(result[0]) if result else 'empty'}")
        deep_inspect(result)
        return sanitize_for_json(result)
    except Exception as e:

        print("❌ Error in get_strategy_dashboard:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating dashboard: {str(e)}")

@router.get("/confidence-analysis/{strategy_id}/{asset}")
async def get_confidence_analysis(
    strategy_id: str,
    asset: str,
    days: int = Query(30, description="Number of days to analyze")
):
    """Get ML confidence analysis for a specific strategy"""
    try:
        analysis = ConfidenceAnalysis()
        result = analysis.generate_analysis(strategy_id, asset, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating confidence analysis: {str(e)}")

@router.get("/signal-timeline/{strategy_id}/{asset}")
async def get_signal_timeline(
    strategy_id: str,
    asset: str,
    days: int = Query(30, description="Number of days to analyze")
):
    """Get price chart with ML-validated signals overlay"""
    try:
        timeline = SignalTimeline()
        result = timeline.generate_timeline(strategy_id, asset, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signal timeline: {str(e)}")
