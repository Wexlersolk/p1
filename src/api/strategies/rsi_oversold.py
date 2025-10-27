import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    """RSI Oversold/Overbought Strategy"""
    
    def __init__(self, parameters: dict = None):
        default_params = {
            "rsi_period": 14,
            "oversold": 30,
            "overbought": 70
        }
        if parameters:
            default_params.update(parameters)
        super().__init__(default_params)
        self.name = "RSI Strategy"
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, df: pd.DataFrame, asset: str) -> pd.DataFrame:
        """Generate signals based on RSI levels"""
        df = df.copy()
        
        period = self.parameters["rsi_period"]
        oversold = self.parameters["oversold"]
        overbought = self.parameters["overbought"]
        
        # Calculate RSI
        df['rsi'] = self.calculate_rsi(df['close'], period)
        
        signals = []
        position = None
        
        for index, row in df.iterrows():
            rsi = row['rsi']
            price = row['close']
            
            if pd.notna(rsi):
                if rsi < oversold and position != 'LONG':
                    signals.append({
                        'timestamp': index,
                        'asset': asset,
                        'signal': 'LONG',
                        'price': price,
                        'rsi': rsi
                    })
                    position = 'LONG'
                elif rsi > overbought and position != 'SHORT':
                    signals.append({
                        'timestamp': index,
                        'asset': asset,
                        'signal': 'SHORT', 
                        'price': price,
                        'rsi': rsi
                    })
                    position = 'SHORT'
        
        return pd.DataFrame(signals)
