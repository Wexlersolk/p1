from .base_strategy import BaseStrategy
from .vwap_strategy import VWAPStrategy
from .sma_crossover import SMACrossover
from .rsi_oversold import RSIStrategy
from .mean_reversion import MeanReversionStrategy
from .signal_validator import SignalValidatorStrategy

class StrategyRegistry:
    """Registry for all available trading strategies"""
    
    def __init__(self):
        self._strategies = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register all available strategies"""
        
        # ========== CORE STRATEGIES ==========
        
        # VWAP + Initial Balance
        self.register(
            "vwap_ib",
            VWAPStrategy,
            "VWAP + Initial Balance",
            "Breakout strategy using VWAP and initial balance range",
            {
                "ib_start": {"type": "time", "default": "13:30", "description": "Initial Balance start time"},
                "ib_end": {"type": "time", "default": "14:30", "description": "Initial Balance end time"},
                "session_start": {"type": "time", "default": "22:00", "description": "Trading session start"},
                "session_end": {"type": "time", "default": "20:00", "description": "Trading session end"},
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
                "slow_period": {"type": "number", "default": 20, "min": 10, "max": 100},
                "stop_loss": {"type": "percent", "default": 1.0, "min": 0.1, "max": 5.0},
                "take_profit": {"type": "percent", "default": 2.0, "min": 0.5, "max": 10.0}
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
                "overbought": {"type": "number", "default": 70, "min": 60, "max": 80},
                "stop_loss": {"type": "percent", "default": 1.0, "min": 0.1, "max": 5.0},
                "take_profit": {"type": "percent", "default": 2.0, "min": 0.5, "max": 10.0}
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
                "std_dev": {"type": "number", "default": 2.0, "min": 1.5, "max": 3.0},
                "stop_loss": {"type": "percent", "default": 1.0, "min": 0.1, "max": 5.0},
                "take_profit": {"type": "percent", "default": 1.5, "min": 0.5, "max": 10.0}
            }
        )
        
        # ========== ML VALIDATED STRATEGIES ==========
        
        # VWAP + ML Validation
        self.register(
            "vwap_ml_validated",
            SignalValidatorStrategy,
            "VWAP + ML Validation", 
            "VWAP strategy filtered by ML signal validation - answers 'Should I trust this VWAP signal?'",
            {
                "base_strategy": {"type": "string", "default": "vwap_ib", "options": ["vwap_ib"], "description": "Base strategy to validate"},
                "confidence_threshold": {"type": "float", "default": 0.65, "min": 0.5, "max": 0.95, "description": "Minimum ML confidence to accept signal"},
                "ml_model_type": {"type": "select", "default": "random_forest", "options": ["random_forest", "xgboost", "logistic_regression"], "description": "ML model type for validation"},
                "fallback_to_original": {"type": "boolean", "default": True, "description": "Use original signal if ML model not trained"},
                "stop_loss": {"type": "percent", "default": 0.5, "min": 0.1, "max": 5.0},
                "take_profit": {"type": "percent", "default": 1.0, "min": 0.5, "max": 10.0}
            }
        )
        
        # SMA + ML Validation
        self.register(
            "sma_ml_validated", 
            SignalValidatorStrategy,
            "SMA + ML Validation",
            "SMA crossover strategy filtered by ML signal validation",
            {
                "base_strategy": {"type": "string", "default": "sma_crossover", "options": ["sma_crossover"], "description": "Base strategy to validate"},
                "confidence_threshold": {"type": "float", "default": 0.65, "min": 0.5, "max": 0.95, "description": "Minimum ML confidence to accept signal"},
                "ml_model_type": {"type": "select", "default": "random_forest", "options": ["random_forest", "xgboost", "logistic_regression"], "description": "ML model type for validation"},
                "fallback_to_original": {"type": "boolean", "default": True, "description": "Use original signal if ML model not trained"},
                "stop_loss": {"type": "percent", "default": 1.0, "min": 0.1, "max": 5.0},
                "take_profit": {"type": "percent", "default": 2.0, "min": 0.5, "max": 10.0}
            }
        )
        
        # RSI + ML Validation
        self.register(
            "rsi_ml_validated",
            SignalValidatorStrategy,
            "RSI + ML Validation",
            "RSI strategy filtered by ML signal validation", 
            {
                "base_strategy": {"type": "string", "default": "rsi_oversold", "options": ["rsi_oversold"], "description": "Base strategy to validate"},
                "confidence_threshold": {"type": "float", "default": 0.65, "min": 0.5, "max": 0.95, "description": "Minimum ML confidence to accept signal"},
                "ml_model_type": {"type": "select", "default": "random_forest", "options": ["random_forest", "xgboost", "logistic_regression"], "description": "ML model type for validation"},
                "fallback_to_original": {"type": "boolean", "default": True, "description": "Use original signal if ML model not trained"},
                "stop_loss": {"type": "percent", "default": 1.0, "min": 0.1, "max": 5.0},
                "take_profit": {"type": "percent", "default": 2.0, "min": 0.5, "max": 10.0}
            }
        )
        
        # Mean Reversion + ML Validation
        self.register(
            "mean_reversion_ml_validated",
            SignalValidatorStrategy,
            "Mean Reversion + ML Validation",
            "Mean reversion strategy filtered by ML signal validation",
            {
                "base_strategy": {"type": "string", "default": "mean_reversion", "options": ["mean_reversion"], "description": "Base strategy to validate"},
                "confidence_threshold": {"type": "float", "default": 0.65, "min": 0.5, "max": 0.95, "description": "Minimum ML confidence to accept signal"},
                "ml_model_type": {"type": "select", "default": "random_forest", "options": ["random_forest", "xgboost", "logistic_regression"], "description": "ML model type for validation"},
                "fallback_to_original": {"type": "boolean", "default": True, "description": "Use original signal if ML model not trained"},
                "stop_loss": {"type": "percent", "default": 1.0, "min": 0.1, "max": 5.0},
                "take_profit": {"type": "percent", "default": 1.5, "min": 0.5, "max": 10.0}
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
        
        # For ML validated strategies, ensure base_strategy parameter is set
        if strategy_id.endswith('_ml_validated') and parameters:
            base_strategy_name = strategy_info["parameters"]["base_strategy"]["default"]
            if 'base_strategy' not in parameters:
                parameters['base_strategy'] = base_strategy_name
        
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
    
    def get_strategies_by_type(self, strategy_type: str = "all"):
        """Get strategies filtered by type"""
        all_strategies = self.list_strategies()
        
        if strategy_type == "all":
            return all_strategies
        elif strategy_type == "core":
            return {k: v for k, v in all_strategies.items() if not k.endswith('_ml_validated') and not k.startswith('ensemble')}
        elif strategy_type == "ml_validated":
            return {k: v for k, v in all_strategies.items() if k.endswith('_ml_validated')}
        elif strategy_type == "ensemble":
            return {k: v for k, v in all_strategies.items() if k.startswith('ensemble')}
        else:
            return all_strategies

# Global registry instance
registry = StrategyRegistry()
