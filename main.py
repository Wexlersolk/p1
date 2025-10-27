import uvicorn
from .app import app
import os

def start_server():
    """Start the FastAPI server on port 8080"""
    print("🚀 Starting Financial Analytics API Server...")
    print("📊 Available endpoints:")
    print("   http://localhost:8080/docs - API Documentation")
    print("   http://localhost:8080/api/v1/visualization/strategy-dashboard/XAUUSD")
    print("   http://localhost:8080/api/v1/visualization/confidence-analysis/vwap_strategy/XAUUSD")
    print("   http://localhost:8080/api/v1/visualization/signal-timeline/vwap_strategy/XAUUSD")
    print("\n⏳ Starting server...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

if __name__ == "__main__":
    start_server()
