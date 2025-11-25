import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class VWAPStrategy(BaseStrategy):
    """VWAP + Initial Balance Strategy - Enhanced for multiple timeframes"""
    
    def __init__(self, parameters: dict = None):
        default_params = {
            "vwap_period": 20,
            "ib_period": 30,  # Default initial balance period
            "min_breakout_percent": 0.001,  # Minimum breakout percentage
        }
        if parameters:
            default_params.update(parameters)
        super().__init__(default_params)
        self.name = "VWAP Initial Balance"
    
    def detect_timeframe(self, asset: str, data: pd.DataFrame) -> str:
        """Detect the timeframe from asset name or data frequency"""
        # Check asset name first
        asset_lower = asset.lower()
        if '5m' in asset_lower:
            return '5m'
        elif '15m' in asset_lower:
            return '15m'
        elif '1h' in asset_lower:
            return '1h'
        elif '4h' in asset_lower:
            return '4h'
        elif '1d' in asset_lower:
            return '1d'
        elif '1w' in asset_lower:
            return '1w'
        
        # If not in name, try to detect from data frequency
        if len(data) > 1:
            time_diff = data.index[1] - data.index[0]
            if time_diff <= pd.Timedelta(minutes=5):
                return '5m'
            elif time_diff <= pd.Timedelta(minutes=15):
                return '15m'
            elif time_diff <= pd.Timedelta(hours=1):
                return '1h'
            elif time_diff <= pd.Timedelta(hours=4):
                return '4h'
            elif time_diff <= pd.Timedelta(days=1):
                return '1d'
            else:
                return '1w'
        
        return 'unknown'
    
    def get_adaptive_parameters(self, timeframe: str) -> dict:
        """Get strategy parameters adapted for the specific timeframe"""
        base_params = self.parameters.copy()
        
        if timeframe in ['5m', '15m']:
            # Intraday short-term
            base_params.update({
                "ib_period": 12,  # 1-3 hours for 5m/15m
                "min_breakout_percent": 0.002,  # 0.2% breakout
            })
        elif timeframe in ['1h', '4h']:
            # Intraday medium-term
            base_params.update({
                "ib_period": 6,   # 6-24 hours for 1h/4h
                "min_breakout_percent": 0.005,  # 0.5% breakout
            })
        elif timeframe in ['1d']:
            # Daily
            base_params.update({
                "ib_period": 5,   # First 5 days
                "min_breakout_percent": 0.01,   # 1% breakout
            })
        elif timeframe in ['1w']:
            # Weekly
            base_params.update({
                "ib_period": 4,   # First 4 weeks
                "min_breakout_percent": 0.02,   # 2% breakout
            })
        
        return base_params
    
    def generate_signals(self, df: pd.DataFrame, asset: str) -> pd.DataFrame:
        """
        Generate signals based on VWAP and initial balance breakout
        Enhanced to work across different timeframes
        """
        print(f"\n{'='*60}")
        print(f"🔍 VWAP+IB Strategy Analysis for {asset}")
        print(f"{'='*60}")
        
        df = df.copy()
        
        # Detect timeframe and get adaptive parameters
        timeframe = self.detect_timeframe(asset, df)
        params = self.get_adaptive_parameters(timeframe)
        
        print(f"📊 Data Analysis:")
        print(f"   Rows: {len(df)}")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")
        print(f"   Detected timeframe: {timeframe}")
        print(f"   Price range: {df['close'].min():.6f} to {df['close'].max():.6f}")
        print(f"   Volume range: {df['volume'].min():.2f} to {df['volume'].max():.2f}")
        
        # Calculate VWAP
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        
        # Calculate initial balance with adaptive period
        ib_period = min(params["ib_period"], len(df))
        if len(df) > ib_period:
            ib_high = df['high'].head(ib_period).max()
            ib_low = df['low'].head(ib_period).min()
            ib_avg_volume = df['volume'].head(ib_period).mean()
        else:
            ib_high = df['high'].max()
            ib_low = df['low'].min()
            ib_avg_volume = df['volume'].mean()
        
        # Calculate current VWAP range for context
        current_vwap_min = vwap.min()
        current_vwap_max = vwap.max()
        current_vwap_avg = vwap.mean()
        
        print(f"\n📈 Strategy Parameters:")
        print(f"   IB Period: {ib_period} periods")
        print(f"   IB High: {ib_high:.6f}")
        print(f"   IB Low: {ib_low:.6f}")
        print(f"   IB Avg Volume: {ib_avg_volume:.2f}")
        print(f"   Min Breakout %: {params['min_breakout_percent']*100:.2f}%")
        print(f"   Current VWAP Range: {current_vwap_min:.6f} to {current_vwap_max:.6f}")
        print(f"   Current VWAP Avg: {current_vwap_avg:.6f}")
        
        signals = []
        signals_generated = 0
        
        # Analyze price vs VWAP relationship
        above_vwap = df['close'] > vwap
        below_vwap = df['close'] < vwap
        
        print(f"\n📊 Market Context:")
        print(f"   Periods above VWAP: {above_vwap.sum()}/{len(df)} ({above_vwap.sum()/len(df)*100:.1f}%)")
        print(f"   Periods below VWAP: {below_vwap.sum()}/{len(df)} ({below_vwap.sum()/len(df)*100:.1f}%)")
        
        # Check if price has touched IB levels recently
        touched_ib_high = (df['high'] >= ib_high).any()
        touched_ib_low = (df['low'] <= ib_low).any()
        
        print(f"   Touched IB High recently: {touched_ib_high}")
        print(f"   Touched IB Low recently: {touched_ib_low}")
        
        for index, row in df.iterrows():
            current_vwap = vwap.loc[index] if index in vwap.index else None
            if pd.isna(current_vwap):
                continue
            
            current_price = row['close']
            current_high = row['high']
            current_low = row['low']
            current_volume = row['volume']
            
            # Calculate breakout percentages
            breakout_above_ib = (current_price - ib_high) / ib_high
            breakout_below_ib = (ib_low - current_price) / ib_low
            
            # Volume confirmation (relative to IB average)
            volume_ratio = current_volume / ib_avg_volume if ib_avg_volume > 0 else 1.0
            
            # LONG signal: Price above VWAP and breaks above IB high with minimum breakout
            long_condition = (
                current_price > current_vwap and 
                current_price > ib_high and
                breakout_above_ib >= params["min_breakout_percent"] and
                volume_ratio >= 0.8  # Some volume confirmation
            )
            
            # SHORT signal: Price below VWAP and breaks below IB low with minimum breakout  
            short_condition = (
                current_price < current_vwap and 
                current_price < ib_low and
                breakout_below_ib >= params["min_breakout_percent"] and
                volume_ratio >= 0.8  # Some volume confirmation
            )
            
            if long_condition:
                signals.append({
                    'timestamp': index,
                    'asset': asset,
                    'signal': 'LONG',
                    'price': current_price,
                    'vwap': current_vwap,
                    'ib_high': ib_high,
                    'ib_low': ib_low,
                    'breakout_percent': breakout_above_ib * 100,
                    'volume_ratio': volume_ratio,
                    'timeframe': timeframe
                })
                signals_generated += 1
                print(f"✅ LONG signal at {index}:")
                print(f"   Price {current_price:.6f} > VWAP {current_vwap:.6f}")
                print(f"   Breakout: +{breakout_above_ib*100:.2f}% above IB High {ib_high:.6f}")
                print(f"   Volume: {volume_ratio:.2f}x average")
            
            elif short_condition:
                signals.append({
                    'timestamp': index,
                    'asset': asset,
                    'signal': 'SHORT',
                    'price': current_price,
                    'vwap': current_vwap,
                    'ib_high': ib_high,
                    'ib_low': ib_low,
                    'breakout_percent': breakout_below_ib * 100,
                    'volume_ratio': volume_ratio,
                    'timeframe': timeframe
                })
                signals_generated += 1
                print(f"✅ SHORT signal at {index}:")
                print(f"   Price {current_price:.6f} < VWAP {current_vwap:.6f}")
                print(f"   Breakout: +{breakout_below_ib*100:.2f}% below IB Low {ib_low:.6f}")
                print(f"   Volume: {volume_ratio:.2f}x average")
        
        print(f"\n🎯 Signal Generation Summary:")
        print(f"   Total signals generated: {signals_generated}")
        
        if signals_generated == 0:
            print(f"   ❌ No signals - Potential reasons:")
            print(f"      - Price never broke IB levels with sufficient margin")
            print(f"      - Insufficient volume confirmation")
            print(f"      - Price/VWAP relationship didn't align")
            print(f"      - Try different timeframe or adjust parameters")
        
        print(f"{'='*60}\n")
        
        return pd.DataFrame(signals)
    
    def generate_alternative_signals(self, df: pd.DataFrame, asset: str) -> pd.DataFrame:
        """
        Alternative VWAP-based signals for when standard IB breakout doesn't work
        Uses VWAP as dynamic support/resistance
        """
        print(f"\n🔄 Trying Alternative VWAP Signals for {asset}")
        
        df = df.copy()
        timeframe = self.detect_timeframe(asset, df)
        
        # Calculate VWAP
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        
        signals = []
        
        for i in range(1, len(df)):
            current_idx = df.index[i]
            prev_idx = df.index[i-1]
            
            current_price = df['close'].iloc[i]
            prev_price = df['close'].iloc[i-1]
            current_vwap = vwap.iloc[i]
            prev_vwap = vwap.iloc[i-1]
            
            # Signal 1: Price crosses above VWAP with momentum
            if (prev_price <= prev_vwap and 
                current_price > current_vwap and 
                current_price > prev_price):
                signals.append({
                    'timestamp': current_idx,
                    'asset': asset,
                    'signal': 'LONG',
                    'price': current_price,
                    'vwap': current_vwap,
                    'signal_type': 'VWAP_Cross_Above',
                    'timeframe': timeframe
                })
            
            # Signal 2: Price crosses below VWAP with momentum
            elif (prev_price >= prev_vwap and 
                  current_price < current_vwap and 
                  current_price < prev_price):
                signals.append({
                    'timestamp': current_idx,
                    'asset': asset,
                    'signal': 'SHORT',
                    'price': current_price,
                    'vwap': current_vwap,
                    'signal_type': 'VWAP_Cross_Below',
                    'timeframe': timeframe
                })
            
            # Signal 3: Bounce off VWAP support
            elif (abs(current_price - current_vwap) / current_vwap < 0.001 and  # Very close to VWAP
                  current_price > prev_price and  # Bouncing up
                  df['low'].iloc[i] <= current_vwap):  # Touched VWAP as support
                signals.append({
                    'timestamp': current_idx,
                    'asset': asset,
                    'signal': 'LONG',
                    'price': current_price,
                    'vwap': current_vwap,
                    'signal_type': 'VWAP_Support_Bounce',
                    'timeframe': timeframe
                })
            
            # Signal 4: Rejection at VWAP resistance
            elif (abs(current_price - current_vwap) / current_vwap < 0.001 and  # Very close to VWAP
                  current_price < prev_price and  # Rejecting down
                  df['high'].iloc[i] >= current_vwap):  # Touched VWAP as resistance
                signals.append({
                    'timestamp': current_idx,
                    'asset': asset,
                    'signal': 'SHORT',
                    'price': current_price,
                    'vwap': current_vwap,
                    'signal_type': 'VWAP_Resistance_Rejection',
                    'timeframe': timeframe
                })
        
        print(f"   Alternative signals generated: {len(signals)}")
        return pd.DataFrame(signals)
