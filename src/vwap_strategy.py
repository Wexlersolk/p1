import pandas as pd
from .config import STRATEGY_CONFIG

class VWAPStrategy:
    def __init__(self, config: dict = None):
        self.config = config or STRATEGY_CONFIG["default"]
    
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate VWAP for given dataframe"""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        vwap = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()
        return vwap
    
    def generate_signals(self, df: pd.DataFrame, asset: str = "default") -> pd.DataFrame:
        """Generate trading signals using VWAP + Initial Balance"""
        config = STRATEGY_CONFIG.get(asset, STRATEGY_CONFIG["default"])
        
        # Your existing strategy logic here
        df = df.copy()
        df['vwap'] = self.calculate_vwap(df)
        
        # Session grouping (your existing logic)
        session_anchor = pd.to_timedelta(config["session_start"])
        df["session_date"] = (df.index - session_anchor).date
        
        signals = []
        
        for day, daily_data in df.groupby(df["session_date"]):
            session_data = daily_data.between_time(
                config["session_start"], 
                config["session_end"]
            )
            
            if session_data.empty:
                continue
                
            # Initial Balance calculation
            ib_data = session_data.between_time(config["ib_start"], config["ib_end"])
            if ib_data.empty:
                continue
                
            ib_high = ib_data["high"].max()
            ib_low = ib_data["low"].min()
            
            # Trading signals (your existing logic)
            trading_candles = session_data.between_time(config["ib_end"], config["session_end"])
            trading_candles["vwap"] = self.calculate_vwap(trading_candles)
            
            trade_entered = False
            for index, row in trading_candles.iterrows():
                if trade_entered:
                break
                    
                close_price = row["close"]
                current_vwap = row["vwap"]
                
                long_signal = close_price > ib_high and close_price > current_vwap
                short_signal = close_price < ib_low and close_price < current_vwap
                
                if long_signal:
                    signals.append({
                        'timestamp': index,
                        'asset': asset,
                        'signal': 'LONG',
                        'price': close_price,
                        'vwap': current_vwap,
                        'ib_high': ib_high,
                        'ib_low': ib_low
                    })
                    trade_entered = True
                elif short_signal:
                    signals.append({
                        'timestamp': index,
                        'asset': asset,
                        'signal': 'SHORT', 
                        'price': close_price,
                        'vwap': current_vwap,
                        'ib_high': ib_high,
                        'ib_low': ib_low
                    })
                    trade_entered = True
        
        return pd.DataFrame(signals)
