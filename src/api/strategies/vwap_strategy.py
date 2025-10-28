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
        
        """Generate trading signals using VWAP + Initial Balance"""
        
        print(f"\n{'='*60}")
        print(f"🔍 VWAP+IB Strategy Debug for {asset}")
        print(f"{'='*60}")
        df = df.copy()
        df["session_date"] = (df.index - SESSION_ANCHOR).date
        
        if not isinstance(df.index, pd.DatetimeIndex):
            print("⚠️  Converting index to DatetimeIndex")
            if df.index.dtype in ['int64', 'float64']:
                sample_value = df.index[0]
                if sample_value > 1e12:
                    df.index = pd.to_datetime(df.index, unit='ms')
                else:
                    df.index = pd.to_datetime(df.index, unit='s')
            else:
                df.index = pd.to_datetime(df.index)
        
        print(f"📊 Data info:")
        print(f"   Rows: {len(df)}")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")

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
        
        if signals:
            from ..models.signal_classifier import SignalClassifier
            import os
            
            # Завантажити ML модель
            # project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) #Correct, but commented due to error
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', )) #TODO: Fix ml
            model_path = os.path.join(project_root, 'models', 'signal_classifier_vwap_ib.pkl')
            if os.path.exists(model_path):
                try:
                    classifier = SignalClassifier()
                    classifier.load_model(model_path)
                    
                    # Додати ML confidence до кожного сигналу
                    for signal in signals:
                        signal['ml_confidence'] = classifier.predict_confidence(
                            signal, df, 'vwap_ib'
                        )
                    
                    print(f"✅ ML validation added to {len(signals)} signals")
                except Exception as e:
                    print(f"⚠️  ML model loading failed: {e}")
                    # Продовжуємо без ML
            else:
                print(f"⚠️  ML model not found at {model_path}")

        return pd.DataFrame(signals)
