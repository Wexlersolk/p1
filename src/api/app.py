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

# Include all routers
for router in routers:
    app.include_router(router)

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Financial Analytics API Server",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Server is running normally",
        "endpoints": {
            "docs": "/docs",
            "assets": "/api/v1/assets",
            "backtest": "/api/v1/backtest",
            "strategies": "/api/v1/strategies", 
            "visualization": "/api/v1/visualization"
        }
    }
