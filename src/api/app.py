from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import routers

# Create FastAPI app
app = FastAPI(
    title="Financial Analytics API",
    description="Real-time financial data analysis and ML-powered trading strategies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Server is running normally",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "backtest": "/backtest/{asset}",
            "backtest_compare": "/backtest/compare",
            "backtest_ai_status": "/backtest/debug/ai-status",
            "backtest_strategies": "/backtest/strategies/available"
        }
    }

# Include all routers
for router in routers:
    app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "Financial Analytics API Server",
        "status": "running",
        "version": "1.0.0"
    }
