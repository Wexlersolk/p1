from ..data_loader import DataLoader
from ..backtest_engine import BacktestEngine
from ..results_analyzer import ResultsAnalyzer
from .strategies.vwap_strategy import VWAPStrategy

# Create shared instances
data_loader = DataLoader()
backtester = BacktestEngine()
analyzer = ResultsAnalyzer()
strategy = VWAPStrategy()
