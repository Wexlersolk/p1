"""
Strategy registry for managing trading strategies
"""
from typing import Dict, Any, Type
from .base_strategy import BaseStrategy

class StrategyRegistry:
    def __init__(self):
        self._strategies = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register all available strategies with direct imports"""
        print("📋 Registering trading strategies...")
        
        try:
            # Import and register each strategy directly
            from .vwap_strategy import VWAPStrategy
            self._strategies['vwap_ib'] = VWAPStrategy
            print("   ✅ vwap_ib -> VWAPStrategy")
        except ImportError as e:
            print(f"   ❌ Failed to register vwap_ib: {e}")
        
        try:
            from .sma_crossover import SMACrossover
            self._strategies['sma_crossover'] = SMACrossover
            print("   ✅ sma_crossover -> SMACrossover")
        except ImportError as e:
            print(f"   ❌ Failed to register sma_crossover: {e}")
        
        try:
            from .rsi_oversold import RSIStrategy
            self._strategies['rsi_oversold'] = RSIStrategy
            print("   ✅ rsi_oversold -> RSIStrategy")
        except ImportError as e:
            print(f"   ❌ Failed to register rsi_oversold: {e}")
        
        try:
            from .mean_reversion import MeanReversionStrategy
            self._strategies['mean_reversion'] = MeanReversionStrategy
            print("   ✅ mean_reversion -> MeanReversionStrategy")
        except ImportError as e:
            print(f"   ❌ Failed to register mean_reversion: {e}")
        
        print(f"🎯 Total strategies registered: {len(self._strategies)}")
        print(f"📋 Available: {list(self._strategies.keys())}")
    
    def register(self, strategy_id: str, strategy_class):
        """Register a new strategy"""
        if not issubclass(strategy_class, BaseStrategy):
            raise TypeError(f"Strategy must inherit from BaseStrategy")
        self._strategies[strategy_id] = strategy_class
    
    def get_strategy(self, strategy_id: str, parameters: Dict[str, Any] = None):
        """Get a strategy instance by ID"""
        if strategy_id not in self._strategies:
            available = list(self._strategies.keys())
            raise KeyError(f"Strategy '{strategy_id}' not found. Available: {available}")
        
        strategy_class = self._strategies[strategy_id]
        return strategy_class(parameters)
    
    def get_all_strategies(self) -> Dict[str, Type[BaseStrategy]]:
        """Get all registered strategies"""
        return self._strategies.copy()

# Global registry instance
registry = StrategyRegistry()
