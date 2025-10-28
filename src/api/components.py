from src.data_loader import DataLoader
from src.backtest_engine import BacktestEngine
from src.results_analyzer import ResultsAnalyzer
from src.api.strategies.vwap_strategy import VWAPStrategy

# Create shared instances
data_loader = DataLoader()
backtester = BacktestEngine()
analyzer = ResultsAnalyzer()
strategy = VWAPStrategy()
