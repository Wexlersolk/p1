#!/usr/bin/env python3
"""
Simple server runner for Financial Analytics API
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import uvicorn
from api.app import app

def start_server():
    """Start the FastAPI server on port 8080"""
    print("🚀 Starting Financial Analytics API Server...")
    print("📊 Available endpoints:")
    print("   http://localhost:8080/docs - API Documentation")
    print("   http://localhost:8080/api/v1/assets - List all assets")
    print("   http://localhost:8080/api/v1/strategies - List all strategies")
    print("   http://localhost:8080/api/v1/visualization/strategy-dashboard/XAUUSD - Strategy Dashboard")
    print("\n⏳ Starting server on http://0.0.0.0:8080 ...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    start_server()
