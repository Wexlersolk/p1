from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from datetime import datetime
import math
import joblib
import os
import sys

# Fix import paths for your project structure
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the project root to Python path to find components
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import your modules with clean, simple imports
try:
    from src.api.strategies.registry import registry
    from src.api.models.signal_classifier import SignalClassifier
    print("✅ API modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import API modules: {e}")
    # Create fallbacks
    registry = None
    SignalClassifier = None

# SIMPLE COMPONENT IMPORTS - this should work now!
try:
    from components import data_loader, backtester, analyzer
    print("✅ Components imported successfully")
except ImportError as e:
    print(f"❌ Failed to import components: {e}")
    raise ImportError("Components not found. Please make sure components directory exists with all required files.")

try:
    from ..cache import get_from_cache, save_to_cache
    print("✅ Cache imported successfully")
except ImportError as e:
    print(f"❌ Failed to import cache: {e}")
    # Create dummy cache functions
    def get_from_cache(key):
        return None
    def save_to_cache(key, value):
        pass

# Create router WITH /backtest prefix
router = APIRouter(prefix="/backtest", tags=["backtest"])

class AIBacktester:
    """
    AI-enhanced backtester that uses trained ML models to filter signals
    """
    
    def __init__(self, original_backtester):
        self.original_backtester = original_backtester
        self.ai_models = {}
        self.load_ai_models()
    
    def load_ai_models(self):
        """Load all trained AI models for signal validation"""
        # Go up from src/api/routes to project root where models are stored
        project_root = os.path.join(current_dir, '..', '..', '..')
        models_dir = os.path.join(project_root, "models")
        
        strategies = ["vwap_ib", "sma_crossover", "rsi_oversold", "mean_reversion"]
        
        print("🤖 Loading AI models...")
        for strategy_id in strategies:
            model_path = os.path.join(models_dir, f"signal_classifier_{strategy_id}.pkl")
            if os.path.exists(model_path):
                try:
                    classifier = SignalClassifier()
                    classifier.load_model(model_path)
                    self.ai_models[strategy_id] = classifier
                    print(f"   ✅ Loaded AI model for {strategy_id}")
                except Exception as e:
                    print(f"   ❌ Failed to load {strategy_id}: {e}")
            else:
                print(f"   ⚠️  No model found for {strategy_id} at {model_path}")
        
        print(f"📊 Total AI models loaded: {len(self.ai_models)}")
    
    def run_ai_backtest(self, strategy_id: str, data: pd.DataFrame, asset: str, 
                       initial_capital: float = 10000, min_confidence: float = 0.6) -> dict:
        """
        Run backtest with AI signal filtering
        """
        print(f"🎯 Starting AI backtest for {asset} with {strategy_id}")
        print(f"   Min Confidence: {min_confidence}")
        
        # Check if registry is available
        if registry is None:
            return self._empty_result(initial_capital, data, min_confidence, True)
        
        # Get strategy from registry
        try:
            strategy = registry.get_strategy(strategy_id)
        except Exception as e:
            return self._empty_result(initial_capital, data, min_confidence, True, error=f"Strategy {strategy_id} not found: {e}")
        
        # Generate raw signals
        raw_signals = strategy.generate_signals(data, asset)
        
        if raw_signals.empty:
            # For VWAP strategy, try alternative signals if no standard signals
            if strategy_id == "vwap_ib" and hasattr(strategy, 'generate_alternative_signals'):
                print("🔄 No standard VWAP signals, trying alternative signals...")
                raw_signals = strategy.generate_alternative_signals(data, asset)
            
            if raw_signals.empty:
                print(f"⚠️ No signals generated for {asset}, returning empty results")
                return self._empty_result(initial_capital, data, min_confidence, True, original_signals=0)
        
        print(f"📊 Raw signals: {len(raw_signals)}")
        
        # Filter signals with AI
        if strategy_id in self.ai_models:
            filtered_signals = self._filter_signals_with_ai(
                raw_signals, data, strategy_id, min_confidence
            )
            
            if filtered_signals.empty:
                print(f"⚠️ No signals passed AI filtering (min_confidence: {min_confidence}), returning empty results")
                return self._empty_result(initial_capital, data, min_confidence, True, original_signals=len(raw_signals))
            
            print(f"🤖 AI filtered: {len(filtered_signals)}/{len(raw_signals)} signals")
            
            # Run backtest with filtered signals
            results = self._run_backtest_with_signals(filtered_signals, data, asset, initial_capital)
            
            # Add AI metrics
            results["ai_metrics"] = {
                "original_signals": len(raw_signals),
                "filtered_signals": len(filtered_signals),
                "filter_ratio": len(filtered_signals) / len(raw_signals),
                "min_confidence": min_confidence,
                "ai_used": True
            }
            
            return results
        else:
            print(f"⚠️  No AI model for {strategy_id}, using regular backtest")
            self.original_backtester.initial_capital = initial_capital
            try:
                results = self.original_backtester.run_backtest(strategy_id, data, asset)
                results["ai_metrics"] = {"ai_used": False}
                return results
            except Exception as e:
                print(f"❌ Error in regular backtest: {e}")
                return self._empty_result(initial_capital, data, min_confidence, False, error=str(e))
    
    def _empty_result(self, initial_capital: float, data: pd.DataFrame, min_confidence: float, 
                     ai_used: bool, original_signals: int = 0, error: str = None) -> dict:
        """Return empty result structure"""
        result = {
            "trades": [],
            "portfolio_values": [{"timestamp": data.index[0], "value": initial_capital}],
            "final_capital": initial_capital,
            "total_trades": 0,
            "winning_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "total_return_percent": 0,
            "ai_metrics": {
                "original_signals": original_signals,
                "filtered_signals": 0,
                "filter_ratio": 0,
                "min_confidence": min_confidence,
                "ai_used": ai_used
            }
        }
        
        if error:
            result["note"] = error
            
        return result
    
    def _filter_signals_with_ai(self, signals: pd.DataFrame, data: pd.DataFrame,
                               strategy_id: str, min_confidence: float) -> pd.DataFrame:
        """Filter signals using AI model confidence"""
        classifier = self.ai_models[strategy_id]
        filtered_signals = []
        
        print(f"🔍 AI Filtering: {len(signals)} signals with min_confidence={min_confidence}")
        
        for idx, signal in signals.iterrows():
            try:
                confidence = classifier.predict_confidence(
                    signal.to_dict(), data, strategy_id
                )
                
                print(f"   Signal {idx}: confidence={confidence:.3f}")
                
                if confidence >= min_confidence:
                    signal_with_conf = signal.copy()
                    signal_with_conf['ai_confidence'] = confidence
                    filtered_signals.append(signal_with_conf)
                    
            except Exception as e:
                print(f"⚠️  Error evaluating signal: {e}")
                continue
        
        print(f"✅ AI Filtered: {len(filtered_signals)}/{len(signals)} signals passed")
        return pd.DataFrame(filtered_signals)
    
    def _run_backtest_with_signals(self, signals: pd.DataFrame, data: pd.DataFrame,
                                  asset: str, initial_capital: float) -> dict:
        """
        Run backtest using pre-filtered signals
        """
        # Set initial capital
        self.original_backtester.initial_capital = initial_capital
        
        try:
            # Try to use existing backtester with modified approach
            if hasattr(self.original_backtester, 'run_backtest_with_signals'):
                return self.original_backtester.run_backtest_with_signals(signals, data, asset)
            else:
                # Fallback: use simple backtest implementation
                print("📝 Using fallback backtest method")
                return self._simple_backtest_with_signals(signals, data, asset, initial_capital)
                
        except Exception as e:
            print(f"❌ Error in backtest execution: {e}")
            return self._empty_result(initial_capital, data, 0.6, True, error=f"Backtest execution failed: {e}")
    
    def _simple_backtest_with_signals(self, signals: pd.DataFrame, data: pd.DataFrame,
                                     asset: str, initial_capital: float) -> dict:
        """
        Simple backtest implementation when main backtester doesn't support external signals
        """
        capital = initial_capital
        position = None
        trades = []
        portfolio = [{"timestamp": data.index[0], "value": capital}]
        
        for idx, signal in signals.iterrows():
            current_time = signal['timestamp']
            current_price = signal['price']
            signal_type = signal['signal']
            
            if position is None:
                # Enter position
                position_size = capital * 0.1  # Risk 10% per trade
                units = position_size / current_price
                
                position = {
                    'entry_time': current_time,
                    'entry_price': current_price,
                    'type': signal_type,
                    'units': units,
                    'ai_confidence': signal.get('ai_confidence', None)
                }
                
                trades.append({
                    'entry_time': current_time,
                    'entry_price': current_price,
                    'type': signal_type,
                    'units': units,
                    'ai_confidence': signal.get('ai_confidence', None)
                })
                
                capital -= position_size  # Reserve the position amount
                
            else:
                # Exit position
                exit_price = current_price
                
                if position['type'] == 'LONG':
                    pnl = (exit_price - position['entry_price']) * position['units']
                else:  # SHORT
                    pnl = (position['entry_price'] - exit_price) * position['units']
                
                capital += (position['entry_price'] * position['units']) + pnl
                
                trades[-1].update({
                    'exit_time': current_time,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_percent': (pnl / (position['entry_price'] * position['units'])) * 100
                })
                
                position = None
            
            # Update portfolio value
            portfolio.append({
                'timestamp': current_time,
                'value': capital
            })
        
        # Calculate basic metrics
        completed_trades = [t for t in trades if 'pnl' in t]
        winning_trades = [t for t in completed_trades if t['pnl'] > 0]
        
        return {
            'trades': trades,
            'portfolio_values': portfolio,
            'final_capital': capital,
            'total_trades': len(completed_trades),
            'winning_trades': len(winning_trades),
            'win_rate': len(winning_trades) / len(completed_trades) if completed_trades else 0,
            'total_pnl': capital - initial_capital,
            'total_return_percent': ((capital - initial_capital) / initial_capital) * 100
        }

# Initialize AI backtester
ai_backtester = AIBacktester(backtester)

def sanitize_for_json(obj):
    """Sanitize data for JSON serialization"""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    return obj

@router.get("/{asset}")
async def run_backtest(
    asset: str,
    lookback: int = Query(100, ge=1, le=10000),
    initial_capital: float = Query(10000, ge=100),
    strategy_id: str = Query("vwap_ib", description="Strategy to use"),
    use_ai: bool = Query(True, description="Use AI signal filtering"),
    min_confidence: float = Query(0.6, ge=0.0, le=1.0, description="Minimum AI confidence")
):
    """Run backtest for a specific asset with optional AI filtering"""
    
    # Skip if asset is actually a debug path or favicon
    excluded_paths = ["favicon.ico", "debug", "strategies", "compare", "test"]
    if asset in excluded_paths:
        raise HTTPException(status_code=404, detail=f"Asset '{asset}' not found")
    
    cache_key = f"backtest_{asset}_{lookback}_{initial_capital}_{strategy_id}_{use_ai}_{min_confidence}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    try:
        print(f"🔎 Starting backtest for {asset}, lookback={lookback}, AI={use_ai}")
        
        assets_data = data_loader.load_all_assets()
        if asset not in assets_data:
            available_assets = list(assets_data.keys()) if assets_data else ["No assets loaded"]
            raise HTTPException(status_code=404, detail=f"Asset '{asset}' not found. Available: {available_assets}")
        
        df = assets_data[asset]
        df_subset = df.tail(lookback)
        
        print(f"✅ Data loaded: {len(df_subset)} rows")
        print(f"   Columns: {list(df_subset.columns)}")
        if len(df_subset) > 0:
            print(f"   Date range: {df_subset.index[0]} to {df_subset.index[-1]}")
        
        # Run backtest with or without AI
        print(f"🧠 Running backtest with strategy '{strategy_id}'...")
        
        if use_ai:
            results = ai_backtester.run_ai_backtest(
                strategy_id, df_subset, asset, initial_capital, min_confidence
            )
        else:
            backtester.initial_capital = initial_capital
            try:
                results = backtester.run_backtest(strategy_id, df_subset, asset)
                results["ai_metrics"] = {"ai_used": False}
            except Exception as e:
                print(f"❌ Error in non-AI backtest: {e}")
                # Return empty results for non-AI errors too
                results = {
                    "trades": [],
                    "portfolio_values": [{"timestamp": df_subset.index[0], "value": initial_capital}],
                    "final_capital": initial_capital,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0,
                    "total_return_percent": 0,
                    "ai_metrics": {"ai_used": False, "error": str(e)}
                }
        
        print(f"✅ Backtest completed")
        print(f"   Results keys: {list(results.keys())}")
        
        # Add AI status to results
        if "ai_metrics" in results:
            ai_info = results["ai_metrics"]
            print(f"   AI Used: {ai_info.get('ai_used', False)}")
            if ai_info.get('ai_used'):
                print(f"   AI Filter Ratio: {ai_info.get('filter_ratio', 0):.2%}")
        
        # Serialize results for JSON
        serialized_results = {}
        for key, val in results.items():
            if isinstance(val, pd.DataFrame):
                serialized_results[key] = val.to_dict(orient="records")
            elif isinstance(val, pd.Series):
                serialized_results[key] = val.to_dict()
            elif isinstance(val, (list, dict)):
                serialized_results[key] = sanitize_for_json(val)
            else:
                serialized_results[key] = val
        
        # Process datetime objects
        if "trades" in serialized_results and isinstance(serialized_results["trades"], list):
            for trade in serialized_results["trades"]:
                for time_field in ['entry_time', 'exit_time']:
                    if time_field in trade and isinstance(trade[time_field], datetime):
                        trade[time_field] = trade[time_field].isoformat()
        
        # Final sanitization
        serialized_results = sanitize_for_json(serialized_results)
        
        print("🗄️ Saving to cache...")
        save_to_cache(cache_key, serialized_results)
        print("✅ Done successfully")
        
        return serialized_results
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        import traceback
        print(f"❌ Unexpected error in backtest:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")

# Keep your other endpoints (debug, compare, etc.)
@router.get("/debug/ai-status")
async def debug_ai_status():
    """Check AI model status"""
    status = {
        "models_loaded": list(ai_backtester.ai_models.keys()),
        "total_models": len(ai_backtester.ai_models),
        "available_strategies": ["vwap_ib", "sma_crossover", "rsi_oversold", "mean_reversion"]
    }
    
    # Check model files exist
    project_root = os.path.join(current_dir, '..', '..', '..')
    models_dir = os.path.join(project_root, "models")
    status["models_directory"] = models_dir
    status["models_directory_exists"] = os.path.exists(models_dir)
    
    if os.path.exists(models_dir):
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
        status["model_files"] = model_files
    else:
        status["model_files"] = []
    
    return status

@router.get("/strategies/available")
async def get_available_strategies():
    """Get list of all available strategies"""
    try:
        if registry is None:
            raise Exception("Registry not available")
            
        strategies = registry.get_all_strategies()
        return {
            "strategies": list(strategies.keys()),
            "count": len(strategies)
        }
    except Exception as e:
        # Fallback list
        return {
            "strategies": ["vwap_ib", "sma_crossover", "rsi_oversold", "mean_reversion"],
            "count": 4,
            "note": "Using fallback list - registry not available",
            "error": str(e)
        }
