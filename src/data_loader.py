import pandas as pd
import os
import glob
from typing import Dict, List, Set

class DataLoader:
    def __init__(self, data_folder: str = "data"):
        self.data_folder = data_folder
        self._all_files = []  # Cached list of all files
    
    def load_all_assets(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files from data folder and its subdirectories"""
        assets_data = {}
        
        if not os.path.exists(self.data_folder):
            print(f"❌ Data folder not found: {self.data_folder}")
            return assets_data
        
        print(f"🔍 Searching for CSV files in: {self.data_folder}")

        # Find all CSV files in all directories recursively
        self._all_files = glob.glob(os.path.join(self.data_folder, "**/*.csv"), recursive=True)
        print(f"🔍 Found {len(self._all_files)} CSV files in {self.data_folder} and subdirectories")
        
        for file_path in self._all_files:
            # Create asset name based on path
            rel_path = os.path.relpath(file_path, self.data_folder)
            parts = rel_path.split(os.sep)
            file_name = os.path.basename(file_path)
            
            if len(parts) == 1:
                asset_name = file_name.replace('.csv', '')
            else:
                exchange = parts[0]
                market_type = parts[1]
                
                # Base asset name
                asset_name = f"{exchange}_{market_type}_{file_name.replace('.csv', '')}"
                
                # Add symbol if present (e.g., BTC, ETH, etc.)
                if len(parts) >= 4:  # Є exchange/type/symbol/file.csv
                    symbol = parts[2]
                    if symbol not in ["spot", "futures", "Spot", "Futures"]:
                        asset_name = f"{exchange}_{symbol}_{market_type}_{file_name.replace('.csv', '')}"
            
            print(f"🔍 Processing file: {file_path} -> asset_name: {asset_name}")
            
            try:
                
                df = pd.read_csv(file_path)
                
                # Check for timestamp column
                if 'timestamp' in df.columns:
                    # Convert timestamp to datetime and set as index
                    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('datetime', inplace=True)
                    # Remove original timestamp
                    if 'timestamp' in df.columns:
                        df.drop('timestamp', axis=1, inplace=True)
                        
  
                elif 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df.set_index('datetime', inplace=True)
                
                if self.validate_data(df, asset_name):
                    assets_data[asset_name] = df
                    print(f"✅ Loaded {asset_name} with {len(df)} rows")
            except Exception as e:
                print(f"❌ Error loading {file_path}: {e}")
                
        print(f"🔍 Total assets loaded: {len(assets_data)}")
        return assets_data
    
    def validate_data(self, df: pd.DataFrame, asset: str) -> bool:
        """Basic data validation"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            print(f"❌ Missing columns in {asset}")
            return False
        return True
        
    def get_available_exchanges(self) -> List[str]:
        """Get list of unique exchanges in the data folder"""
        if not os.path.exists(self.data_folder):
            print(f"❌ Data folder not found: {self.data_folder}")
            return []
        
        if not self._all_files:
            self._all_files = glob.glob(os.path.join(self.data_folder, "**/*.csv"), recursive=True)
        
        exchanges = set()
        
        for file_path in self._all_files:
            rel_path = os.path.relpath(file_path, self.data_folder)
            parts = rel_path.split(os.sep)
            
            if len(parts) > 1:
                exchanges.add(parts[0])
        
        return sorted(list(exchanges))
    
    def get_available_timeframes(self) -> List[str]:
        """Get list of unique timeframes in the data folder"""
        if not os.path.exists(self.data_folder):
            print(f"❌ Data folder not found: {self.data_folder}")
            return []
        
        if not self._all_files:
            self._all_files = glob.glob(os.path.join(self.data_folder, "**/*.csv"), recursive=True)
        
        timeframes = set()
        
        for file_path in self._all_files:
            file_name = os.path.basename(file_path)
            
            for tf in ["5m", "15m", "1h", "4h", "1d", "1w"]:
                if tf in file_name:
                    timeframes.add(tf)
        
        return sorted(list(timeframes))
