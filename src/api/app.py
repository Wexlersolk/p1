from fastapi import FastAPI, APIRouter
from .config import API_PREFIX

# Import route modules
from .routes.assets import router as assets_router
from .routes.strategies import router as strategies_router
from .routes.backtest import router as backtest_router

def create_app():
    """Create and configure a FastAPI application"""
    app = FastAPI(
        title="Financial Market Prediction API",
        description="API for predicting financial market movements using VWAP and other strategies",
        version="1.0.0",
    )

    # Include all routers
    app.include_router(assets_router, prefix=f"{API_PREFIX}/assets", tags=["Assets"])
    app.include_router(strategies_router, prefix=f"{API_PREFIX}/strategies", tags=["Strategies"])
    app.include_router(backtest_router, prefix=f"{API_PREFIX}/backtest", tags=["Backtesting"])

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "message": "Welcome to the Financial Market Prediction API",
            "docs": "/docs",
            "version": "1.0.0"
        }

    return app