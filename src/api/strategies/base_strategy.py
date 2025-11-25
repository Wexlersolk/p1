from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        self.parameters = parameters or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame, asset: str) -> pd.DataFrame:
        """Generate trading signals - must be implemented by subclasses"""
        pass
    
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Common VWAP calculation that can be reused"""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        vwap = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()
        return vwap
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters with defaults"""
        return self.parameters
    
    def set_parameters(self, parameters: Dict[str, Any]):
        """Update strategy parameters"""
        self.parameters.update(parameters)
