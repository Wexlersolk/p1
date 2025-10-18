# Trading strategy configuration for multiple assets
STRATEGY_CONFIG = {
    "default": {
        "ib_start": "13:30",
        "ib_end": "14:30",
        "session_start": "22:00", 
        "session_end": "20:00",
        "initial_balance": 10000,
    },
    
    # Asset-specific configurations (optional)
    "XAUUSD": {
        "commission": 0.001,
        "slippage": 0.0005,
    },
    "BTCUSD": {
        "commission": 0.002,
        "slippage": 0.001,
    },
    "ETHUSD": {
        "commission": 0.002,
        "slippage": 0.001,
    }
}

# List of assets to backtest
ASSETS = ["XAUUSD", "BTCUSD", "ETHUSD", "SP500"]
