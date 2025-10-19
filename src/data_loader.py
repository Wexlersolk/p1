import pandas as pd
import os
from typing import Dict

class DataLoader:
    def __init__(self, data_folder: str = "data"):
        self.data_folder = data_folder
    
    def load_all_assets(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files from data folder"""
        assets_data = {}
        
        for file in os.listdir(self.data_folder):
            if file.endswith('.csv'):
                asset_name = file.replace('.csv', '').replace('_5M', '')
                file_path = os.path.join(self.data_folder, file)
                
                try:
                    df = pd.read_csv(file_path, parse_dates=['datetime'], index_col='datetime')
                    assets_data[asset_name] = df
                    print(f"✅ Loaded {asset_name} with {len(df)} rows")
                except Exception as e:
                    print(f"❌ Error loading {file}: {e}")
        
        return assets_data
    
    def validate_data(self, df: pd.DataFrame, asset: str) -> bool:
        """Basic data validation"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            print(f"❌ Missing columns in {asset}")
            return False
        return True
