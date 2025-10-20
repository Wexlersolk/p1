from .base_strategy import BaseStrategy
from .vwap_strategy import VWAPStrategy
from .sma_crossover import SMACrossover
from .rsi_oversold import RSIStrategy
from .mean_reversion import MeanReversionStrategy

class StrategyRegistry:
    """Registry for all available trading strategies"""
    
    def __init__(self):
        self._strategies = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register all available strategies"""
        # VWAP + Initial Balance
        self.register(
            "vwap_ib",
            VWAPStrategy,
            "VWAP + Initial Balance",
            "Breakout strategy using VWAP and initial balance range",
            {
                "ib_start": {"type": "time", "default": "13:30", "description": "Initial Balance start time"},
                "ib_end": {"type": "time", "default": "14:30", "description": "Initial Balance end time"},
                "stop_loss": {"type": "percent", "default": 0.5, "min": 0.1, "max": 5.0},
                "take_profit": {"type": "percent", "default": 1.0, "min": 0.5, "max": 10.0}
            }
        )
        
        # SMA Crossover
        self.register(
            "sma_crossover", 
            SMACrossover,
            "SMA Crossover",
            "Buy when fast SMA crosses above slow SMA, sell when crosses below",
            {
                "fast_period": {"type": "number", "default": 10, "min": 5, "max": 50},
                "slow_period": {"type": "number", "default": 20, "min": 10, "max": 100}
            }
        )
        
        # RSI Oversold
        self.register(
            "rsi_oversold",
            RSIStrategy,
            "RSI Oversold",
            "Buy when RSI is oversold, sell when overbought",
            {
                "rsi_period": {"type": "number", "default": 14, "min": 7, "max": 21},
                "oversold": {"type": "number", "default": 30, "min": 20, "max": 40},
                "overbought": {"type": "number", "default": 70, "min": 60, "max": 80}
            }
        )
        
        # Mean Reversion
        self.register(
            "mean_reversion",
            MeanReversionStrategy,
            "Bollinger Bands Mean Reversion", 
            "Buy at lower band, sell at upper band",
            {
                "bb_period": {"type": "number", "default": 20, "min": 10, "max": 50},
                "std_dev": {"type": "number", "default": 2.0, "min": 1.5, "max": 3.0}
            }
        )
    
    def register(self, strategy_id: str, strategy_class, name: str, description: str, parameters: dict):
        """Register a new strategy"""
        self._strategies[strategy_id] = {
            "class": strategy_class,
            "name": name,
            "description": description,
            "parameters": parameters
        }
    
    def get_strategy(self, strategy_id: str, parameters: dict = None):
        """Get strategy instance by ID"""
        if strategy_id not in self._strategies:
            raise ValueError(f"Strategy '{strategy_id}' not found")
        
        strategy_info = self._strategies[strategy_id]
        return strategy_info["class"](parameters)
    
    def list_strategies(self):
        """List all available strategies"""
        return {
            strategy_id: {
                "name": info["name"],
                "description": info["description"],
                "parameters": info["parameters"]
            }
            for strategy_id, info in self._strategies.items()
        }
    
    def get_strategy_info(self, strategy_id: str):
        """Get detailed info about a specific strategy"""
        if strategy_id not in self._strategies:
            return None
        return self._strategies[strategy_id]

# Global registry instance
registry = StrategyRegistry()
