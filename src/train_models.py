import pandas as pd
import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now use relative imports
from api.strategies import registry
from api.models.signal_classifier import SignalClassifier
from data_loader import DataLoader

def ensure_models_directory():
    """Create models directory if it doesn't exist"""
    # Create models directory in project root (same level as src)
    project_root = os.path.dirname(current_dir)
    models_dir = os.path.join(project_root, "models")
    os.makedirs(models_dir, exist_ok=True)
    return models_dir

def train_signal_validator(strategy_id: str, asset: str = "XAUUSD"):
    """Train signal validator for a specific strategy with error handling"""
    print(f"🎯 Training Signal Validator for {strategy_id} on {asset}")
    
    # Load data - let DataLoader auto-detect the path
    loader = DataLoader()
    assets_data = loader.load_all_assets()
    
    if not assets_data:
        print(f"❌ No data loaded. Please check your data folder.")
        return
    
    if asset not in assets_data:
        print(f"❌ Asset {asset} not found. Available assets: {list(assets_data.keys())}")
        return
    
    data = assets_data[asset]
    
    # Generate historical signals
    try:
        strategy = registry.get_strategy(strategy_id)
        historical_signals = strategy.generate_signals(data, asset)
        
        if historical_signals.empty:
            print(f"❌ No historical signals generated for {strategy_id}")
            return
        
        print(f"📊 Generated {len(historical_signals)} historical signals")
        
        # Add strategy type to signals for feature engineering
        historical_signals['strategy_type'] = strategy_id
        
        # Train signal classifier with error handling
        classifier = SignalClassifier(model_type="random_forest")
        
        try:
            classifier.train(historical_signals, data)
            
            # Save model
            models_dir = ensure_models_directory()
            model_path = os.path.join(models_dir, f"signal_classifier_{strategy_id}.pkl")
            classifier.save_model(model_path)
            
            print(f"✅ Signal validator training completed for {strategy_id}")
            
        except Exception as e:
            print(f"❌ Error during ML training for {strategy_id}: {e}")
            print("💡 This might be due to insufficient data or feature calculation issues")
            return
        
    except Exception as e:
        print(f"❌ Error generating signals for {strategy_id}: {e}")
        import traceback
        traceback.print_exc()

def train_all_strategies():
    """Train signal validators for all major strategies"""
    print("🚀 Starting ML Model Training for All Strategies...")
    print("=" * 60)
    
    strategies_to_train = ["vwap_ib", "sma_crossover", "rsi_oversold"]
    
    successful = 0
    for strategy_id in strategies_to_train:
        try:
            train_signal_validator(strategy_id)
            successful += 1
        except Exception as e:
            print(f"❌ Failed to train {strategy_id}: {e}")
        print("-" * 40)
    
    print(f"🎉 Training completed! {successful}/{len(strategies_to_train)} strategies trained successfully!")

if __name__ == "__main__":
    train_all_strategies()
