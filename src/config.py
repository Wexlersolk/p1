# Trading strategy configuration for multiple assets
STRATEGY_CONFIG = {
    "default": {
        "ib_start": "13:30",      # Initial Balance start
        "ib_end": "14:30",        # Initial Balance end  
        "session_start": "22:00", # Session start (UTC)
        "session_end": "20:00",   # Session end (UTC) - next day
        "initial_balance": 10000,
        "commission": 0.001,
        "slippage": 0.0005,
    },
    
    # Asset-specific configurations (optional overrides)
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
