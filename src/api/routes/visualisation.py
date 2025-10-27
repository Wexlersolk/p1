from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any

from src.visualisation.strategy_dashboard import StrategyDashboard
from src.visualisation.confidence_analysis import ConfidenceAnalysis
from src.visualisation.signal_timeline import SignalTimeline
from ...visualization.signal_timeline import SignalTimeline

router = APIRouter(prefix="/api/v1/visualization", tags=["visualization"])

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
        return result
    except Exception as e:
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
