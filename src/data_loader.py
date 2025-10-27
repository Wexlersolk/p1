import pandas as pd
import os
from typing import Dict
import glob

class DataLoader:
    def __init__(self, data_folder: str = None):
        # If no data folder specified, try to find it automatically
        if data_folder is None:
            # First, try relative to current directory (for running from root)
            if os.path.exists("data"):
                self.data_folder = "data"
            # Then try going up one level (for running from src/)
            elif os.path.exists("../data"):
                self.data_folder = "../data"
            else:
                self.data_folder = "data"  # Default, will show error if not found
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
                # Extract asset name from file path
                file_name = os.path.basename(file_path)
                asset_name = file_name.replace('.csv', '').replace('_5M', '')

                # Read CSV and handle datetime/timestamp column
                # First, read columns only
                cols = pd.read_csv(file_path, nrows=0).columns
                if 'datetime' in cols:
                    df = pd.read_csv(file_path, parse_dates=['datetime'], index_col='datetime')
                elif 'timestamp' in cols:
                    df = pd.read_csv(file_path, parse_dates=['timestamp'], index_col='timestamp')
                else:
                    df = pd.read_csv(file_path)  # fallback, no datetime/timestamp column

                assets_data[asset_name] = df
                print(f"✅ Loaded {asset_name} with {len(df)} rows from {file_path}")

                
            except Exception as e:
                print(f"❌ Error loading {file_path}: {e}")
        
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
