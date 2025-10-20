"""
Shared components for API
"""
from ..data_loader import DataLoader
from ..vwap_strategy import VWAPStrategy
from ..backtest_engine import BacktestEngine
from ..results_analyzer import ResultsAnalyzer
import os
from pathlib import Path

# Initialize components
PROJECT_ROOT = Path(__file__).parent.parent.parent
data_path = os.path.join(PROJECT_ROOT, "data_many")

print(f"🔍 Looking for data in: {data_path}")
print(f"🔍 Path exists: {os.path.exists(data_path)}")
if os.path.exists(data_path):
    print(f"🔍 Directory contents: {os.listdir(data_path)}")

# Ініціалізуйте з абсолютним шляхом
data_loader = DataLoader(data_folder=data_path)
strategy = VWAPStrategy()
backtester = BacktestEngine()
analyzer = ResultsAnalyzer()