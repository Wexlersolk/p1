from .assets import router as assets_router
from .backtest import router as backtest_router
from .strategies import router as strategies_router
from .visualization import router as visualization_router  # NEW

# Include all routers
routers = [
    assets_router,
    backtest_router, 
    strategies_router,
    visualization_router  # NEW
]
