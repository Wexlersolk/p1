import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class MeanReversionStrategy(BaseStrategy):
    """Bollinger Bands Mean Reversion Strategy"""
    
    def __init__(self, parameters: dict = None):
        default_params = {
            "bb_period": 20,
            "std_dev": 2.0,
        }
        if parameters:
            default_params.update(parameters)
        super().__init__(default_params)
        self.name = "Mean Reversion"
    
    def calculate_bollinger_bands(self, prices, window=20, num_std=2):
        """Calculate Bollinger Bands"""
        rolling_mean = prices.rolling(window=window).mean()
        rolling_std = prices.rolling(window=window).std()
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        return upper_band, rolling_mean, lower_band
    
    def generate_signals(self, df: pd.DataFrame, asset: str) -> pd.DataFrame:
        """Generate signals based on Bollinger Bands mean reversion"""
        df = df.copy()
        
        bb_period = self.parameters["bb_period"]
        std_dev = self.parameters["std_dev"]
        
        # Calculate Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.calculate_bollinger_bands(
            df['close'], bb_period, std_dev
        )
        
        signals = []
        position = None  # Track current position
        
        for index, row in df.iterrows():
            if pd.isna(row['bb_upper']) or pd.isna(row['bb_lower']):
                continue
                
            close_price = row['close']
            bb_upper = row['bb_upper']
            bb_lower = row['bb_lower']
            bb_middle = row['bb_middle']
            
            # Buy signal: price touches or crosses below lower band
            if close_price <= bb_lower and position != 'LONG':
                signals.append({
                    'timestamp': index,
                    'asset': asset,
                    'signal': 'LONG',
                    'price': close_price,
                    'bb_upper': bb_upper,
                    'bb_middle': bb_middle,
                    'bb_lower': bb_lower,
                    'bb_position': (close_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0
                })
                position = 'LONG'
            
            # Sell signal: price touches or crosses above upper band  
            elif close_price >= bb_upper and position != 'SHORT':
                signals.append({
                    'timestamp': index,
                    'asset': asset,
                    'signal': 'SHORT',
                    'price': close_price,
                    'bb_upper': bb_upper,
                    'bb_middle': bb_middle,
                    'bb_lower': bb_lower,
                    'bb_position': (close_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0
                })
                position = 'SHORT'
            
            # Exit signal: price returns to middle band
            elif position == 'LONG' and close_price >= bb_middle:
                # For simplicity, we'll just close the position
                position = None
            elif position == 'SHORT' and close_price <= bb_middle:
                position = None
        
        return pd.DataFrame(signals)
