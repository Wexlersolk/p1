#!/usr/bin/env python3
"""
Simple server runner for Financial Analytics API
"""
import sys
import os

# Add both current directory and src to Python path
current_dir = os.path.dirname(__file__)
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, current_dir)  # Add project root
sys.path.insert(0, src_dir)      # Add src directory

import uvicorn

def start_server():
    """Start the FastAPI server on port 8080"""
    print("🚀 Starting Financial Analytics API Server...")
    print("📊 Available endpoints:")
    print("   http://localhost:8080/docs - API Documentation")
    print("   http://localhost:8080/health - Health Check")
    print("   http://localhost:8080/backtest/debug/ai-status - AI Models Status")
    print("   http://localhost:8080/backtest/strategies/available - Available Strategies")
    print("\n⏳ Starting server on http://localhost:8080 ...")
    
    uvicorn.run(
        "api.app:app",  # Use import string instead of app object for reload
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
        reload_dirs=[src_dir]  # Watch src directory for changes
    )

if __name__ == "__main__":
    start_server()
