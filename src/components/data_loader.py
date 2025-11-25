"""
Data loader component - wraps your existing data loader
"""
import sys
import os

# Add the project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # Import your existing data loader
    from src.data_loader import DataLoader
    
    # Create an instance
    data_loader = DataLoader()
    print("✅ Data loader component initialized")
    
except ImportError as e:
    print(f"❌ Failed to import data loader: {e}")
    
    # Fallback implementation
    class FallbackDataLoader:
        def __init__(self):
            print("⚠️  Using fallback data loader")
        
        def load_all_assets(self):
            print("📁 Fallback: Loading empty asset data")
            return {}
    
    data_loader = FallbackDataLoader()
