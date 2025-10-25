import pandas as pd
import numpy as np
from typing import Dict, List

class FeatureEngineer:
    """Enhanced feature engineering for signal validation"""
    
    def create_market_context_features(self, df: pd.DataFrame, signal_timestamp: pd.Timestamp = None) -> Dict[str, float]:
        """Create market context features for signal validation"""
        if signal_timestamp:
            # Use data up to the signal timestamp
            context_data = df[df.index <= signal_timestamp].tail(100)
        else:
            context_data = df.tail(100)
        
        if len(context_data) < 20:
            return {}
        
        features = {}
        
        # 1. Volatility Features
        returns = context_data['close'].pct_change()
        features['volatility_1h'] = returns.tail(12).std()  # 1-hour volatility (5min * 12)
        features['volatility_4h'] = returns.tail(48).std()  # 4-hour volatility
        features['volatility_24h'] = returns.tail(288).std()  # 24-hour volatility
        
        # 2. Trend Strength
        features['trend_strength_short'] = self.calculate_trend_strength(context_data['close'], 6)   # 30min
        features['trend_strength_medium'] = self.calculate_trend_strength(context_data['close'], 24)  # 2 hours
        features['trend_strength_long'] = self.calculate_trend_strength(context_data['close'], 96)    # 8 hours
        
        # 3. Volume Features
        features['volume_ratio'] = context_data['volume'].tail(12).mean() / context_data['volume'].tail(96).mean()
        features['volume_trend'] = self.calculate_volume_trend(context_data['volume'])
        
        # 4. Price Position Features
        high_24h = context_data['high'].tail(288).max()
        low_24h = context_data['low'].tail(288).min()
        current_price = context_data['close'].iloc[-1]
        features['price_position_24h'] = (current_price - low_24h) / (high_24h - low_24h) if high_24h != low_24h else 0.5
        
        # 5. Mean Reversion Features
        features['price_vs_ma'] = current_price / context_data['close'].tail(20).mean() - 1
        features['bollinger_position'] = self.calculate_bollinger_position(context_data)
        
        # 6. Momentum Features
        features['momentum_1h'] = context_data['close'].iloc[-1] / context_data['close'].iloc[-12] - 1
        features['momentum_4h'] = context_data['close'].iloc[-1] / context_data['close'].iloc[-48] - 1
        
        # 7. Session-based Features (for forex/commodities)
        features['is_london_session'] = self.is_trading_session(context_data.index[-1], 'london')
        features['is_ny_session'] = self.is_trading_session(context_data.index[-1], 'new_york')
        features['is_asia_session'] = self.is_trading_session(context_data.index[-1], 'asia')
        
        return features
    
    def create_strategy_specific_features(self, df: pd.DataFrame, signal: Dict, strategy_type: str) -> Dict[str, float]:
        """Create features specific to each strategy type"""
        features = {}
        
        if strategy_type == "vwap_ib":
            features['vwap_distance'] = (signal['price'] - signal['vwap']) / signal['vwap']
            features['ib_range_width'] = (signal['ib_high'] - signal['ib_low']) / signal['ib_low']
            features['breakout_strength'] = abs(signal['price'] - signal['ib_high']) / signal['ib_high'] if signal['signal'] == 'LONG' else abs(signal['price'] - signal['ib_low']) / signal['ib_low']
        
        elif strategy_type == "sma_crossover":
            features['sma_spread'] = (signal['sma_fast'] - signal['sma_slow']) / signal['sma_slow']
            features['price_vs_sma_fast'] = signal['price'] / signal['sma_fast'] - 1
            features['price_vs_sma_slow'] = signal['price'] / signal['sma_slow'] - 1
        
        elif strategy_type == "rsi_oversold":
            features['rsi_value'] = signal['rsi']
            features['rsi_extremeness'] = abs(signal['rsi'] - 50) / 50
        
        return features
    
    def calculate_trend_strength(self, prices: pd.Series, window: int) -> float:
        """Calculate trend strength using linear regression slope"""
        if len(prices) < window:
            return 0.0
        
        y = prices.tail(window).values
        x = np.arange(len(y))
        
        # Remove NaN values
        mask = ~np.isnan(y)
        if np.sum(mask) < 2:
            return 0.0
            
        x_clean = x[mask]
        y_clean = y[mask]
        
        # Linear regression
        A = np.vstack([x_clean, np.ones(len(x_clean))]).T
        slope, _ = np.linalg.lstsq(A, y_clean, rcond=None)[0]
        
        # Normalize by price level
        trend_strength = abs(slope) / np.mean(y_clean)
        return trend_strength
    
    def calculate_volume_trend(self, volume: pd.Series) -> float:
        """Calculate volume trend (increasing/decreasing)"""
        if len(volume) < 10:
            return 0.0
        
        recent_volume = volume.tail(6).mean()  # Last 30min
        historical_volume = volume.tail(48).mean()  # Last 4 hours
        
        if historical_volume == 0:
            return 0.0
            
        return recent_volume / historical_volume - 1
    
    def calculate_bollinger_position(self, df: pd.DataFrame, window: int = 20) -> float:
        """Calculate position within Bollinger Bands"""
        if len(df) < window:
            return 0.5
        
        prices = df['close'].tail(window)
        current_price = prices.iloc[-1]
        
        ma = prices.mean()
        std = prices.std()
        
        if std == 0:
            return 0.5
            
        upper_band = ma + 2 * std
        lower_band = ma - 2 * std
        
        # Normalize position between 0 (lower band) and 1 (upper band)
        if current_price <= lower_band:
            return 0.0
        elif current_price >= upper_band:
            return 1.0
        else:
            return (current_price - lower_band) / (upper_band - lower_band)
    
    def is_trading_session(self, timestamp: pd.Timestamp, session: str) -> int:
        """Check if current time is within trading session"""
        hour = timestamp.hour
        
        if session == 'london':
            return 1 if 8 <= hour < 16 else 0  # London: 8 AM - 4 PM UTC
        elif session == 'new_york':
            return 1 if 13 <= hour < 21 else 0  # New York: 1 PM - 9 PM UTC
        elif session == 'asia':
            return 1 if 22 <= hour or hour < 6 else 0  # Asia: 10 PM - 6 AM UTC
        else:
            return 0
