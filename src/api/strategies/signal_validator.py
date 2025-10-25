import pandas as pd
from typing import Dict, List
from .base_strategy import BaseStrategy
from ..models.signal_classifier import SignalClassifier
from ..models.feature_engineer import FeatureEngineer

class SignalValidatorStrategy(BaseStrategy):
    """
    ML-powered signal validator that acts as an ensemble filter
    Answers: "Should I trust this trading signal right now?"
    """
    
    def __init__(self, parameters: dict = None):
        default_params = {
            "base_strategy": "vwap_ib",  # Strategy to validate
            "confidence_threshold": 0.65,  # Minimum confidence to accept signal
            "ml_model_type": "random_forest",  # random_forest, xgboost, logistic_regression
            "fallback_to_original": True,  # Use original signal if ML not trained
        }
        if parameters:
            default_params.update(parameters)
        super().__init__(default_params)
        
        self.signal_classifier = SignalClassifier(self.parameters["ml_model_type"])
        self.base_strategy = None
        self.load_base_strategy()
        self.load_trained_model()
    
    def load_base_strategy(self):
        """Load the base strategy to validate"""
        from . import registry  # Import your strategy registry
        
        try:
            self.base_strategy = registry.get_strategy(
                self.parameters["base_strategy"],
                self.parameters
            )
        except Exception as e:
            print(f"❌ Error loading base strategy: {e}")
            self.base_strategy = None
    
    def load_trained_model(self):
        """Load pre-trained signal classifier model"""
        model_path = f"models/signal_classifier_{self.parameters['base_strategy']}.pkl"
        try:
            self.signal_classifier.load_model(model_path)
            print(f"✅ Loaded trained signal validator for {self.parameters['base_strategy']}")
        except Exception as e:
            print(f"⚠️  Could not load trained model: {e}")
            print("🤖 Using untrained validator (will return default confidence)")
    
    def generate_signals(self, df: pd.DataFrame, asset: str) -> pd.DataFrame:
        """Generate validated signals using ML confidence"""
        if self.base_strategy is None:
            print("❌ No base strategy available")
            return pd.DataFrame()
        
        # Get original signals from base strategy
        original_signals = self.base_strategy.generate_signals(df, asset)
        
        if original_signals.empty:
            return original_signals
        
        print(f"🔍 Validating {len(original_signals)} signals with ML...")
        
        # Validate each signal with ML
        validated_signals = []
        for _, signal in original_signals.iterrows():
            confidence = self.signal_classifier.predict_confidence(
                signal, df, self.parameters["base_strategy"]
            )
            
            signal_dict = signal.to_dict()
            signal_dict['original_signal'] = signal_dict['signal']
            signal_dict['ml_confidence'] = confidence
            signal_dict['ml_validated'] = confidence >= self.parameters["confidence_threshold"]
            
            # Only include signals that pass ML validation OR if we're using fallback
            if (self.parameters["fallback_to_original"] and not self.signal_classifier.is_trained) or \
               signal_dict['ml_validated']:
                validated_signals.append(signal_dict)
        
        validated_df = pd.DataFrame(validated_signals)
        
        if not validated_df.empty:
            accepted = len(validated_df[validated_df['ml_validated']])
            total = len(validated_df)
            print(f"✅ ML Validation: {accepted}/{total} signals accepted "
                  f"({accepted/total*100:.1f}% acceptance rate)")
        
        return validated_df
    
    def get_validation_stats(self, df: pd.DataFrame, asset: str) -> Dict:
        """Get statistics about signal validation"""
        signals = self.generate_signals(df, asset)
        
        if signals.empty:
            return {}
        
        stats = {
            "total_signals": len(signals),
            "accepted_signals": len(signals[signals['ml_validated']]),
            "rejected_signals": len(signals[~signals['ml_validated']]),
            "average_confidence": signals['ml_confidence'].mean(),
            "acceptance_rate": len(signals[signals['ml_validated']]) / len(signals),
        }
        
        return stats
