import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class SMACrossover(BaseStrategy):
    """Simple Moving Average Crossover Strategy"""
    
    def __init__(self, parameters: dict = None):
        default_params = {
            "fast_period": 10,
            "slow_period": 20
        }
        if parameters:
            default_params.update(parameters)
        super().__init__(default_params)
        self.name = "SMA Crossover"
    
    def generate_signals(self, df: pd.DataFrame, asset: str) -> pd.DataFrame:
        """Generate signals based on SMA crossovers"""
        df = df.copy()
        
        fast_period = self.parameters["fast_period"]
        slow_period = self.parameters["slow_period"]
        
        # Calculate SMAs
        df['sma_fast'] = df['close'].rolling(window=fast_period).mean()
        df['sma_slow'] = df['close'].rolling(window=slow_period).mean()
        
        # Generate signals (1 when fast > slow, 0 otherwise)
        df['position'] = (df['sma_fast'] > df['sma_slow']).astype(int)
        df['crossover'] = df['position'].diff()
        
        signals = []
        for index, row in df.iterrows():
            if row['crossover'] == 1:  # Golden cross - BUY
                signals.append({
                    'timestamp': index,
                    'asset': asset,
                    'signal': 'LONG',
                    'price': row['close'],
                    'sma_fast': row['sma_fast'],
                    'sma_slow': row['sma_slow']
                })
            elif row['crossover'] == -1:  # Death cross - SELL
                signals.append({
                    'timestamp': index,
                    'asset': asset, 
                    'signal': 'SHORT',
                    'price': row['close'],
                    'sma_fast': row['sma_fast'],
                    'sma_slow': row['sma_slow']
                })
        
        return pd.DataFrame(signals)
