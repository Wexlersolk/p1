import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os
from typing import Dict, List, Tuple

class SignalClassifier:
    """ML model to validate trading signals with enhanced error handling"""
    
    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        self.model = None
        self.feature_names = []
        self.is_trained = False
        
    def initialize_model(self):
        """Initialize the ML model based on type"""
        if self.model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                class_weight='balanced'
            )
        elif self.model_type == "xgboost":
            from xgboost import XGBClassifier
            self.model = XGBClassifier(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.1,
                random_state=42,
                eval_metric='logloss'
            )
        elif self.model_type == "logistic_regression":
            self.model = LogisticRegression(
                random_state=42,
                class_weight='balanced',
                max_iter=1000
            )
        else:
            self.model = RandomForestClassifier(random_state=42)
    
    def prepare_training_data(self, historical_signals: pd.DataFrame, historical_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data from historical signals and outcomes with error handling"""
        from .feature_engineer import FeatureEngineer
        
        feature_engineer = FeatureEngineer()
        features_list = []
        labels = []
        
        for _, signal in historical_signals.iterrows():
            try:
                # Get market context features at signal time
                market_features = feature_engineer.create_market_context_features(
                    historical_data, signal['timestamp']
                )
                
                # Get strategy-specific features
                strategy_features = feature_engineer.create_strategy_specific_features(
                    historical_data, signal, signal.get('strategy_type', 'vwap_ib')
                )
                
                # Combine all features
                all_features = {**market_features, **strategy_features}
                
                if all_features:
                    features_list.append(all_features)
                    
                    # Label: 1 if trade was profitable, 0 otherwise
                    label = self.calculate_signal_success(signal, historical_data)
                    labels.append(label)
            except Exception as e:
                print(f"⚠️  Skipping signal due to error: {e}")
                continue
        
        # Create DataFrame
        if features_list and labels:
            X = pd.DataFrame(features_list)
            y = pd.Series(labels, dtype=int)
            self.feature_names = X.columns.tolist()
            return X, y
        else:
            return pd.DataFrame(), pd.Series()
    
    def calculate_signal_success(self, signal: pd.Series, historical_data: pd.DataFrame, lookforward_bars: int = 12) -> int:
        """Calculate if a signal was successful (1) or not (0)"""
        signal_time = signal['timestamp']
        
        # Find data after the signal
        future_data = historical_data[historical_data.index > signal_time]
        
        if len(future_data) < lookforward_bars:
            return 0  # Not enough data to evaluate
        
        # Get prices after signal
        entry_price = signal['price']
        future_prices = future_data.head(lookforward_bars)
        
        if signal['signal'] == 'LONG':
            # Check if price went up after entry
            max_price = future_prices['high'].max()
            min_price = future_prices['low'].min()
            
            # Success if price increased by 0.5% before decreasing by 0.5%
            if max_price >= entry_price * 1.005:
                return 1
            elif min_price <= entry_price * 0.995:
                return 0
            else:
                # Inconclusive - use final price
                final_price = future_prices['close'].iloc[-1]
                return 1 if final_price > entry_price else 0
        
        elif signal['signal'] == 'SHORT':
            # Check if price went down after entry
            max_price = future_prices['high'].max()
            min_price = future_prices['low'].min()
            
            # Success if price decreased by 0.5% before increasing by 0.5%
            if min_price <= entry_price * 0.995:
                return 1
            elif max_price >= entry_price * 1.005:
                return 0
            else:
                # Inconclusive - use final price
                final_price = future_prices['close'].iloc[-1]
                return 1 if final_price < entry_price else 0
        
        return 0
    
    def train(self, historical_signals: pd.DataFrame, historical_data: pd.DataFrame, test_size: float = 0.2):
        """Train the signal classifier model with enhanced error handling"""
        print("🏋️ Training Signal Classifier...")
        
        # Prepare training data
        X, y = self.prepare_training_data(historical_signals, historical_data)
        
        if X.empty or y.empty:
            print("❌ No training data available after preprocessing")
            return
        
        # Check if we have enough samples for both classes
        class_counts = y.value_counts()
        if len(class_counts) < 2:
            print(f"❌ Insufficient class diversity. Only one class present: {class_counts.to_dict()}")
            return
        
        print(f"📊 Training on {len(X)} samples with {len(self.feature_names)} features")
        print(f"📈 Class distribution: {class_counts.to_dict()}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Initialize and train model
        self.initialize_model()
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Model trained - Train Score: {train_score:.3f}, Test Score: {test_score:.3f}")
        print(f"🎯 Test Accuracy: {accuracy:.3f}")
        print("\n📋 Classification Report:")
        print(classification_report(y_test, y_pred))
        
        # Feature importance (if available)
        if hasattr(self.model, 'feature_importances_'):
            feature_importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("\n🎯 Top 10 Feature Importances:")
            print(feature_importance.head(10))
        
        self.is_trained = True
    
    def predict_confidence(self, signal: Dict, current_data: pd.DataFrame, strategy_type: str) -> float:
        """Predict confidence score for a signal (0-1)"""
        if not self.is_trained or self.model is None:
            # Return default confidence if model not trained
            return 0.5
        
        from .feature_engineer import FeatureEngineer
        
        feature_engineer = FeatureEngineer()
        
        try:
            # Create features for current signal
            market_features = feature_engineer.create_market_context_features(current_data)
            strategy_features = feature_engineer.create_strategy_specific_features(
                current_data, signal, strategy_type
            )
            
            all_features = {**market_features, **strategy_features}
            
            # Ensure we have all expected features
            feature_vector = []
            for feature_name in self.feature_names:
                feature_vector.append(all_features.get(feature_name, 0.0))
            
            # Make prediction
            confidence = self.model.predict_proba([feature_vector])[0][1]  # Probability of class 1 (success)
            return float(confidence)
        except Exception as e:
            print(f"❌ Error predicting confidence: {e}")
            return 0.5
    
    def save_model(self, filepath: str):
        """Save trained model to file"""
        if self.is_trained:
            joblib.dump({
                'model': self.model,
                'feature_names': self.feature_names,
                'model_type': self.model_type
            }, filepath)
            print(f"💾 Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        if os.path.exists(filepath):
            loaded = joblib.load(filepath)
            self.model = loaded['model']
            self.feature_names = loaded['feature_names']
            self.model_type = loaded['model_type']
            self.is_trained = True
            print(f"📂 Model loaded from {filepath}")
