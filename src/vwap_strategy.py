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
        # Merge default config with asset-specific config
        default_config = STRATEGY_CONFIG["default"]
        asset_config = STRATEGY_CONFIG.get(asset, {})
        config = {**default_config, **asset_config}
        
        # Your existing strategy logic here
        df = df.copy()
        df['vwap'] = self.calculate_vwap(df)
        
        # FIXED: Session grouping - use time directly, not timedelta
        # Create session date based on the session start time
        session_start_time = pd.to_datetime(config["session_start"]).time()
        df["session_date"] = df.index.normalize()  # Start with regular date
        
        # Adjust session date for sessions that cross midnight
        early_hours = df.index.time < pd.to_datetime("12:00").time()
        late_hours = df.index.time >= session_start_time
        
        # If session crosses midnight, adjust dates for early hours
        if pd.to_datetime(config["session_end"]).time() < session_start_time:
            # Session crosses midnight - early hours belong to previous session
            df.loc[early_hours, "session_date"] = df.loc[early_hours].index.normalize() - pd.Timedelta(days=1)
        
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
            if trading_candles.empty:
                continue
                
            trading_candles = trading_candles.copy()
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
