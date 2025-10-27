import pandas as pd
from .base_strategy import BaseStrategy

class VWAPStrategy(BaseStrategy):
    """VWAP + Initial Balance Strategy"""
    
    def __init__(self, parameters: dict = None):
        default_params = {
            "ib_start": "13:30",
            "ib_end": "14:30", 
            "session_start": "22:00",
            "session_end": "20:00",
        }
        if parameters:
            default_params.update(parameters)
        super().__init__(default_params)
        self.name = "VWAP + Initial Balance"
    
    def generate_signals(self, df: pd.DataFrame, asset: str) -> pd.DataFrame:
        """Generate trading signals using VWAP + Initial Balance"""
        IB_START_UTC = pd.to_datetime(self.parameters["ib_start"]).time()
        IB_END_UTC = pd.to_datetime(self.parameters["ib_end"]).time()
        SESSION_START_UTC = pd.to_datetime(self.parameters["session_start"]).time()
        SESSION_END_UTC = pd.to_datetime(self.parameters["session_end"]).time()
        SESSION_ANCHOR = pd.to_timedelta(self.parameters["session_start"] + ":00")
        
        df = df.copy()
        df["session_date"] = (df.index - SESSION_ANCHOR).date
        
        signals = []
        daily_groups = df.groupby(df["session_date"])

        for day, daily_data in daily_groups:
            session_data = daily_data.between_time(SESSION_START_UTC, SESSION_END_UTC)
            if session_data.empty:
                continue

            ib_data = session_data.between_time(IB_START_UTC, IB_END_UTC)
            if ib_data.empty:
                continue

            ib_high = ib_data["high"].max()
            ib_low = ib_data["low"].min()

            trading_candles = session_data.between_time(IB_END_UTC, SESSION_END_UTC).copy()
            if trading_candles.empty:
                continue
                
            trading_candles["vwap"] = self.calculate_vwap(trading_candles)

            trade_entered = False
            for index, row in trading_candles.iterrows():
                if trade_entered:
                    break

                close_price = row["close"]
                current_vwap = row["vwap"]

                long_flag = close_price > ib_high and close_price > current_vwap
                short_flag = close_price < ib_low and close_price < current_vwap

                if long_flag:
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
                elif short_flag:
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
