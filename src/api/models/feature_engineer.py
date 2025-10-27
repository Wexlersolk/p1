import pandas as pd
import numpy as np
from typing import Dict, List

class FeatureEngineer:
    """Enhanced feature engineering for signal validation with safe data access"""
    
    def create_market_context_features(self, df: pd.DataFrame, signal_timestamp: pd.Timestamp = None) -> Dict[str, float]:
        """Create market context features for signal validation - with safe data access"""
        if signal_timestamp:
            # Use data up to the signal timestamp
            context_data = df[df.index <= signal_timestamp].tail(100)
        else:
            context_data = df.tail(100)
        
        if len(context_data) < 20:
            return {}
        
        features = {}
        
        try:
            # 1. Volatility Features (safe calculation)
            returns = context_data['close'].pct_change().dropna()
            if len(returns) >= 12:
                features['volatility_1h'] = returns.tail(12).std()  # 1-hour volatility (5min * 12)
            else:
                features['volatility_1h'] = returns.std() if len(returns) > 1 else 0.0
            
            if len(returns) >= 48:
                features['volatility_4h'] = returns.tail(48).std()  # 4-hour volatility
            else:
                features['volatility_4h'] = returns.std() if len(returns) > 1 else 0.0
            
            # 2. Trend Strength (safe calculation)
            features['trend_strength_short'] = self.calculate_trend_strength(context_data['close'], min(6, len(context_data)))
            features['trend_strength_medium'] = self.calculate_trend_strength(context_data['close'], min(24, len(context_data)))
            features['trend_strength_long'] = self.calculate_trend_strength(context_data['close'], min(96, len(context_data)))
            
            # 3. Volume Features
            if len(context_data) >= 12:
                recent_volume = context_data['volume'].tail(12).mean()
            else:
                recent_volume = context_data['volume'].mean()
                
            if len(context_data) >= 96:
                historical_volume = context_data['volume'].tail(96).mean()
            else:
                historical_volume = context_data['volume'].mean()
                
            features['volume_ratio'] = recent_volume / historical_volume if historical_volume > 0 else 1.0
            features['volume_trend'] = self.calculate_volume_trend(context_data['volume'])
            
            # 4. Price Position Features (safe calculation)
            high_period = min(288, len(context_data))
            low_period = min(288, len(context_data))
            
            high_24h = context_data['high'].tail(high_period).max()
            low_24h = context_data['low'].tail(low_period).min()
            current_price = context_data['close'].iloc[-1]
            
            if high_24h != low_24h:
                features['price_position_24h'] = (current_price - low_24h) / (high_24h - low_24h)
            else:
                features['price_position_24h'] = 0.5
            
            # 5. Mean Reversion Features
            ma_period = min(20, len(context_data))
            features['price_vs_ma'] = current_price / context_data['close'].tail(ma_period).mean() - 1
            features['bollinger_position'] = self.calculate_bollinger_position(context_data)
            
            # 6. Momentum Features (safe calculation)
            if len(context_data) >= 12:
                features['momentum_1h'] = context_data['close'].iloc[-1] / context_data['close'].iloc[-min(12, len(context_data))] - 1
            else:
                features['momentum_1h'] = 0.0
                
            if len(context_data) >= 48:
                features['momentum_4h'] = context_data['close'].iloc[-1] / context_data['close'].iloc[-min(48, len(context_data))] - 1
            else:
                features['momentum_4h'] = 0.0
            
            # 7. Session-based Features (for forex/commodities)
            features['is_london_session'] = self.is_trading_session(context_data.index[-1], 'london')
            features['is_ny_session'] = self.is_trading_session(context_data.index[-1], 'new_york')
            features['is_asia_session'] = self.is_trading_session(context_data.index[-1], 'asia')
            
        except (IndexError, KeyError) as e:
            print(f"⚠️  Error calculating features: {e}")
            return {}
        
        return features
    
    def create_strategy_specific_features(self, df: pd.DataFrame, signal: Dict, strategy_type: str) -> Dict[str, float]:
        """Create features specific to each strategy type"""
        features = {}
        
        try:
            if strategy_type == "vwap_ib":
                if 'vwap' in signal and signal['vwap'] > 0:
                    features['vwap_distance'] = (signal['price'] - signal['vwap']) / signal['vwap']
                else:
                    features['vwap_distance'] = 0.0
                    
                if 'ib_high' in signal and 'ib_low' in signal and signal['ib_low'] > 0:
                    features['ib_range_width'] = (signal['ib_high'] - signal['ib_low']) / signal['ib_low']
                    if signal['signal'] == 'LONG' and signal['ib_high'] > 0:
                        features['breakout_strength'] = abs(signal['price'] - signal['ib_high']) / signal['ib_high']
                    elif signal['signal'] == 'SHORT' and signal['ib_low'] > 0:
                        features['breakout_strength'] = abs(signal['price'] - signal['ib_low']) / signal['ib_low']
                    else:
                        features['breakout_strength'] = 0.0
                else:
                    features['ib_range_width'] = 0.0
                    features['breakout_strength'] = 0.0
            
            elif strategy_type == "sma_crossover":
                if 'sma_fast' in signal and 'sma_slow' in signal and signal['sma_slow'] > 0:
                    features['sma_spread'] = (signal['sma_fast'] - signal['sma_slow']) / signal['sma_slow']
                else:
                    features['sma_spread'] = 0.0
                    
                if 'sma_fast' in signal and signal['sma_fast'] > 0:
                    features['price_vs_sma_fast'] = signal['price'] / signal['sma_fast'] - 1
                else:
                    features['price_vs_sma_fast'] = 0.0
                    
                if 'sma_slow' in signal and signal['sma_slow'] > 0:
                    features['price_vs_sma_slow'] = signal['price'] / signal['sma_slow'] - 1
                else:
                    features['price_vs_sma_slow'] = 0.0
            
            elif strategy_type == "rsi_oversold":
                if 'rsi' in signal:
                    features['rsi_value'] = signal['rsi']
                    features['rsi_extremeness'] = abs(signal['rsi'] - 50) / 50
                else:
                    features['rsi_value'] = 50.0
                    features['rsi_extremeness'] = 0.0
        
        except Exception as e:
            print(f"⚠️  Error calculating strategy features for {strategy_type}: {e}")
        
        return features
    
    def calculate_trend_strength(self, prices: pd.Series, window: int) -> float:
        """Calculate trend strength using linear regression slope"""
        if len(prices) < window or window < 2:
            return 0.0
        
        y = prices.tail(window).values
        x = np.arange(len(y))
        
        # Remove NaN values
        mask = ~np.isnan(y)
        if np.sum(mask) < 2:
            return 0.0
            
        x_clean = x[mask]
        y_clean = y[mask]
        
        try:
            # Linear regression
            A = np.vstack([x_clean, np.ones(len(x_clean))]).T
            slope, _ = np.linalg.lstsq(A, y_clean, rcond=None)[0]
            
            # Normalize by price level
            trend_strength = abs(slope) / np.mean(y_clean)
            return trend_strength
        except:
            return 0.0
    
    def calculate_volume_trend(self, volume: pd.Series) -> float:
        """Calculate volume trend (increasing/decreasing)"""
        if len(volume) < 10:
            return 0.0
        
        recent_period = min(6, len(volume))
        historical_period = min(48, len(volume))
        
        recent_volume = volume.tail(recent_period).mean()
        historical_volume = volume.tail(historical_period).mean()
        
        if historical_volume == 0:
            return 0.0
            
        return recent_volume / historical_volume - 1
    
    def calculate_bollinger_position(self, df: pd.DataFrame, window: int = 20) -> float:
        """Calculate position within Bollinger Bands"""
        if len(df) < window:
            return 0.5
        
        try:
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
        except:
            return 0.5
    
    def is_trading_session(self, timestamp: pd.Timestamp, session: str) -> int:
        """Check if current time is within trading session"""
        try:
            hour = timestamp.hour
            
            if session == 'london':
                return 1 if 8 <= hour < 16 else 0  # London: 8 AM - 4 PM UTC
            elif session == 'new_york':
                return 1 if 13 <= hour < 21 else 0  # New York: 1 PM - 9 PM UTC
            elif session == 'asia':
                return 1 if 22 <= hour or hour < 6 else 0  # Asia: 10 PM - 6 AM UTC
            else:
                return 0
        except:
            return 0
