import pandas as pd
import os
from typing import Dict, List, Set
import glob

class DataLoader:
    def __init__(self, data_folder: str = None):
        self._all_files = []  # Cached list of all files
        # If no data folder specified, try to find it automatically
        if data_folder is None:
            # First, try relative to current directory (for running from root)
            if os.path.exists("data_many"):
                self.data_folder = "data_many"
            # Then try going up one level (for running from src/)
            elif os.path.exists("../data_many"):
                self.data_folder = "../data_many"
            else:
                self.data_folder = "data_many"  # Default, will show error if not found
        else:
            self.data_folder = data_folder
        
        print(f"📁 Using data folder: {os.path.abspath(self.data_folder)}")
    
    def load_all_assets(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files from data folder"""
        assets_data = {}
        
        if not os.path.exists(self.data_folder):
            print(f"❌ Data folder not found: {self.data_folder}")
            print(f"💡 Current directory: {os.getcwd()}")
            print(f"💡 Available directories: {os.listdir('.')}")
            return assets_data
        
        # Support both .csv files and subdirectories
        csv_pattern = os.path.join(self.data_folder, "**", "*.csv")
        csv_files = glob.glob(csv_pattern, recursive=True)
        
        # Also check root data folder
        root_csv_files = glob.glob(os.path.join(self.data_folder, "*.csv"))
        csv_files.extend(root_csv_files)
        
        for file_path in set(csv_files):  # Remove duplicates
            try:
                # Extract asset name from FULL PATH, not just filename
                # Convert path like: data_many/Coinbase/Futures/BTC/1d.csv
                # Into asset name: Coinbase_Futures_BTC_1d
                
                rel_path = os.path.relpath(file_path, self.data_folder)
                
                # Remove .csv extension
                rel_path_no_ext = rel_path.replace('.csv', '')
                
                # Replace path separators with underscores
                asset_name = rel_path_no_ext.replace(os.sep, '_').replace('/', '_').replace('\\', '_')
                
                # Clean up any double underscores
                while '__' in asset_name:
                    asset_name = asset_name.replace('__', '_')
                
                print(f"📊 Processing: {rel_path} → {asset_name}")

                # Read CSV - first check what columns exist
                sample_df = pd.read_csv(file_path, nrows=1)
                
                # Determine time column
                time_column = None
                if 'datetime' in sample_df.columns:
                    time_column = 'datetime'
                elif 'timestamp' in sample_df.columns:
                    time_column = 'timestamp'
                elif 'time' in sample_df.columns:
                    time_column = 'time'
                elif 'date' in sample_df.columns:
                    time_column = 'date'
                
                if time_column:
                    # Read the full CSV
                    df = pd.read_csv(file_path)
                    
                    # Check if timestamp is numeric (Unix timestamp)
                    if pd.api.types.is_numeric_dtype(df[time_column]):
                        # Determine if milliseconds or seconds
                        sample_value = df[time_column].iloc[0]
                        
                        if sample_value > 1e12:  # Bigger than 1 trillion = milliseconds
                            print(f"   Converting Unix timestamp (ms) to datetime")
                            df[time_column] = pd.to_datetime(df[time_column], unit='ms')
                        elif sample_value > 1e9:  # Bigger than 1 billion = seconds
                            print(f"   Converting Unix timestamp (s) to datetime")
                            df[time_column] = pd.to_datetime(df[time_column], unit='s')
                        else:
                            # Might be already datetime or other format
                            df[time_column] = pd.to_datetime(df[time_column])
                    else:
                        # String datetime format
                        df[time_column] = pd.to_datetime(df[time_column])
                    
                    # Set as index
                    df.set_index(time_column, inplace=True)
                    
                    # Sort by index
                    df.sort_index(inplace=True)
                    
                    # Remove duplicate indices
                    df = df[~df.index.duplicated(keep='first')]
                    
                else:
                    # No time column found, just load as-is
                    print(f"⚠️  No time column found, loading without datetime index")
                    df = pd.read_csv(file_path)

                assets_data[asset_name] = df
                print(f"✅ Loaded {asset_name} with {len(df)} rows")
                if isinstance(df.index, pd.DatetimeIndex) and len(df) > 0:
                    print(f"   Date range: {df.index[0]} to {df.index[-1]}")
                
            except Exception as e:
                print(f"❌ Error loading {file_path}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n📋 Total assets loaded: {len(assets_data)}")
        print(f"📋 Asset names: {list(assets_data.keys())}")
        
        return assets_data
    
    def validate_data(self, df: pd.DataFrame, asset: str) -> bool:
        """Basic data validation"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            print(f"❌ Missing columns in {asset}")
            return False
        
        # Check for NaN values
        if df[required_columns].isna().any().any():
            print(f"⚠️  NaN values found in {asset}")
        
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