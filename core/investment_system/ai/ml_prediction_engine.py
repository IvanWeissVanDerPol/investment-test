"""
Machine Learning Prediction Engine
Advanced ML models for stock price prediction, risk assessment, and market forecasting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import pickle
import joblib
import json
import logging
from pathlib import Path

# ML libraries
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.feature_selection import SelectKBest, f_regression
import xgboost as xgb
from scipy.stats import zscore

# Time series analysis
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, Attention
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

from ..data.market_data_collector import MarketDataCollector
from ..utils.cache_manager import CacheManager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """ML prediction result"""
    symbol: str
    prediction_type: str  # 'price', 'return', 'volatility', 'direction'
    predicted_value: float
    confidence: float
    prediction_horizon: int  # days
    model_used: str
    feature_importance: Dict[str, float]
    timestamp: datetime


@dataclass
class ModelPerformance:
    """Model performance metrics"""
    model_name: str
    mse: float
    mae: float
    r2_score: float
    accuracy: float  # for classification
    precision: float
    recall: float
    training_samples: int
    last_updated: datetime


class MLPredictionEngine:
    """
    Advanced ML prediction engine with multiple models and ensemble methods
    """
    
    def __init__(self, models_dir: str = "models"):
        """Initialize ML prediction engine"""
        self.data_collector = MarketDataCollector()
        self.cache_manager = CacheManager()
        self.audit_logger = get_audit_logger()
        
        # Model storage
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Scalers for different features
        self.scalers = {
            'price': StandardScaler(),
            'volume': RobustScaler(),
            'technical': MinMaxScaler(),
            'sentiment': StandardScaler()
        }
        
        # Model registry
        self.models = {
            'price_prediction': {},
            'volatility_prediction': {},
            'direction_prediction': {},
            'risk_prediction': {}
        }
        
        # Model configurations
        self.model_configs = {
            'random_forest': {
                'n_estimators': [100, 200],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5],
                'min_samples_leaf': [1, 2]
            },
            'xgboost': {
                'n_estimators': [100, 200],
                'max_depth': [6, 10],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 1.0]
            },
            'neural_network': {
                'hidden_layer_sizes': [(50, 25), (100, 50), (100, 50, 25)],
                'learning_rate_init': [0.001, 0.01],
                'alpha': [0.0001, 0.001],
                'max_iter': [500, 1000]
            }
        }
        
        # Feature engineering parameters
        self.feature_params = {
            'lookback_periods': [5, 10, 20, 30],
            'technical_indicators': ['rsi', 'macd', 'bollinger', 'stochastic', 'williams'],
            'lag_features': [1, 2, 3, 5, 10],
            'rolling_windows': [5, 10, 20, 50]
        }
        
        # Initialize models
        self._initialize_models()
        
        # Performance tracking
        self.performance_history = {}
        
        logger.info("ML Prediction Engine initialized")
    
    def _initialize_models(self):
        """Initialize base ML models"""
        try:
            # Price prediction models
            self.models['price_prediction'] = {
                'random_forest': RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                ),
                'xgboost': xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    n_jobs=-1
                ),
                'gradient_boosting': GradientBoostingRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42
                ),
                'neural_network': MLPRegressor(
                    hidden_layer_sizes=(100, 50),
                    learning_rate_init=0.001,
                    max_iter=500,
                    random_state=42
                )
            }
            
            # Volatility prediction models
            self.models['volatility_prediction'] = {
                'svr': SVR(kernel='rbf', C=1.0, gamma='scale'),
                'ridge': Ridge(alpha=1.0),
                'xgboost': xgb.XGBRegressor(
                    n_estimators=50,
                    max_depth=4,
                    learning_rate=0.1,
                    random_state=42
                )
            }
            
            # Direction prediction models (classification)
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.linear_model import LogisticRegression
            
            self.models['direction_prediction'] = {
                'random_forest_clf': RandomForestClassifier(
                    n_estimators=100,
                    random_state=42
                ),
                'logistic_regression': LogisticRegression(
                    random_state=42,
                    max_iter=1000
                ),
                'xgboost_clf': xgb.XGBClassifier(
                    n_estimators=100,
                    random_state=42
                )
            }
            
            logger.info("Base ML models initialized")
            
        except Exception as e:
            logger.error(f"Model initialization error: {e}")
    
    def predict_price(self, symbol: str, horizon: int = 1, 
                     model_type: str = 'ensemble') -> PredictionResult:
        """
        Predict stock price for given horizon
        
        Args:
            symbol: Stock symbol
            horizon: Prediction horizon in days
            model_type: 'ensemble', 'random_forest', 'xgboost', 'lstm', etc.
        """
        try:
            # Get training data
            market_data = self._get_training_data(symbol, period="2y")
            if market_data is None or len(market_data) < 100:
                raise ValueError(f"Insufficient data for {symbol}")
            
            # Prepare features and targets
            features, targets = self._prepare_features_targets(
                market_data, prediction_type='price', horizon=horizon
            )
            
            if len(features) < 50:
                raise ValueError("Insufficient features for training")
            
            # Train/load model
            model = self._get_or_train_model(
                symbol, 'price_prediction', model_type, features, targets
            )
            
            # Make prediction
            latest_features = features.iloc[-1:].values
            prediction = model.predict(latest_features)[0]
            
            # Calculate confidence
            confidence = self._calculate_prediction_confidence(
                model, features, targets, latest_features
            )
            
            # Feature importance
            feature_importance = self._get_feature_importance(
                model, features.columns if hasattr(features, 'columns') else []
            )
            
            result = PredictionResult(
                symbol=symbol,
                prediction_type='price',
                predicted_value=prediction,
                confidence=confidence,
                prediction_horizon=horizon,
                model_used=model_type,
                feature_importance=feature_importance,
                timestamp=datetime.utcnow()
            )
            
            # Cache result
            self._cache_prediction(result)
            
            # Audit log
            self.audit_logger.log_event(
                EventType.AI_PREDICTION_GENERATED,
                SeverityLevel.LOW,
                resource='ml_prediction_engine',
                details={
                    'symbol': symbol,
                    'prediction_type': 'price',
                    'model': model_type,
                    'horizon': horizon,
                    'confidence': confidence
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Price prediction error for {symbol}: {e}")
            raise
    
    def predict_volatility(self, symbol: str, horizon: int = 5) -> PredictionResult:
        """Predict volatility for given horizon"""
        try:
            # Get training data
            market_data = self._get_training_data(symbol, period="2y")
            if market_data is None or len(market_data) < 100:
                raise ValueError(f"Insufficient data for {symbol}")
            
            # Calculate realized volatility
            returns = market_data['Close'].pct_change().dropna()
            volatility = returns.rolling(window=horizon).std() * np.sqrt(252)  # Annualized
            
            # Prepare features for volatility prediction
            features = self._prepare_volatility_features(market_data, returns)
            targets = volatility.dropna()
            
            # Align features and targets
            min_length = min(len(features), len(targets))
            features = features.iloc[-min_length:]
            targets = targets.iloc[-min_length:]
            
            if len(features) < 30:
                raise ValueError("Insufficient features for volatility prediction")
            
            # Train/load model
            model = self._get_or_train_model(
                symbol, 'volatility_prediction', 'svr', features, targets
            )
            
            # Make prediction
            latest_features = features.iloc[-1:].values
            prediction = model.predict(latest_features)[0]
            
            # Calculate confidence
            confidence = self._calculate_prediction_confidence(
                model, features, targets, latest_features
            )
            
            result = PredictionResult(
                symbol=symbol,
                prediction_type='volatility',
                predicted_value=prediction,
                confidence=confidence,
                prediction_horizon=horizon,
                model_used='svr',
                feature_importance={},
                timestamp=datetime.utcnow()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Volatility prediction error for {symbol}: {e}")
            raise
    
    def predict_direction(self, symbol: str, horizon: int = 1) -> PredictionResult:
        """Predict price direction (up/down) for given horizon"""
        try:
            # Get training data
            market_data = self._get_training_data(symbol, period="2y")
            if market_data is None or len(market_data) < 100:
                raise ValueError(f"Insufficient data for {symbol}")
            
            # Prepare features and binary targets (1 for up, 0 for down)
            features, _ = self._prepare_features_targets(
                market_data, prediction_type='price', horizon=horizon
            )
            
            # Create direction targets
            returns = market_data['Close'].pct_change(periods=horizon).shift(-horizon)
            targets = (returns > 0).astype(int).dropna()
            
            # Align features and targets
            min_length = min(len(features), len(targets))
            features = features.iloc[:min_length]
            targets = targets.iloc[:min_length]
            
            if len(features) < 50:
                raise ValueError("Insufficient features for direction prediction")
            
            # Train/load model
            model = self._get_or_train_model(
                symbol, 'direction_prediction', 'random_forest_clf', features, targets
            )
            
            # Make prediction
            latest_features = features.iloc[-1:].values
            prediction_proba = model.predict_proba(latest_features)[0]
            prediction = prediction_proba[1]  # Probability of upward movement
            
            # Confidence is the max probability
            confidence = max(prediction_proba)
            
            result = PredictionResult(
                symbol=symbol,
                prediction_type='direction',
                predicted_value=prediction,
                confidence=confidence,
                prediction_horizon=horizon,
                model_used='random_forest_clf',
                feature_importance={},
                timestamp=datetime.utcnow()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Direction prediction error for {symbol}: {e}")
            raise
    
    def create_lstm_model(self, input_shape: Tuple[int, int], 
                         output_size: int = 1) -> tf.keras.Model:
        """Create LSTM model for time series prediction"""
        try:
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=input_shape),
                Dropout(0.2),
                LSTM(50, return_sequences=True),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(output_size)
            ])
            
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
            
            return model
            
        except Exception as e:
            logger.error(f"LSTM model creation error: {e}")
            raise
    
    def predict_with_lstm(self, symbol: str, horizon: int = 1) -> PredictionResult:
        """Predict using LSTM neural network"""
        try:
            # Get training data
            market_data = self._get_training_data(symbol, period="3y")
            if market_data is None or len(market_data) < 200:
                raise ValueError(f"Insufficient data for LSTM training for {symbol}")
            
            # Prepare LSTM features
            sequence_length = 60  # Use 60 days of history
            features, targets = self._prepare_lstm_features(
                market_data, sequence_length, horizon
            )
            
            if len(features) < 100:
                raise ValueError("Insufficient sequences for LSTM training")
            
            # Split data
            train_size = int(len(features) * 0.8)
            X_train, X_test = features[:train_size], features[train_size:]
            y_train, y_test = targets[:train_size], targets[train_size:]
            
            # Create and train LSTM model
            model = self.create_lstm_model((sequence_length, features.shape[2]))
            
            # Training callbacks
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            )
            
            # Train model
            history = model.fit(
                X_train, y_train,
                epochs=50,
                batch_size=32,
                validation_data=(X_test, y_test),
                callbacks=[early_stopping],
                verbose=0
            )
            
            # Make prediction
            latest_sequence = features[-1:] 
            prediction = model.predict(latest_sequence)[0][0]
            
            # Calculate confidence based on validation loss
            val_loss = min(history.history['val_loss'])
            confidence = max(0.1, min(0.95, 1 - val_loss))
            
            result = PredictionResult(
                symbol=symbol,
                prediction_type='price',
                predicted_value=prediction,
                confidence=confidence,
                prediction_horizon=horizon,
                model_used='lstm',
                feature_importance={},
                timestamp=datetime.utcnow()
            )
            
            # Save model
            model_path = self.models_dir / f"lstm_{symbol}_{horizon}d.h5"
            model.save(str(model_path))
            
            return result
            
        except Exception as e:
            logger.error(f"LSTM prediction error for {symbol}: {e}")
            raise
    
    def create_ensemble_prediction(self, symbol: str, horizon: int = 1) -> PredictionResult:
        """Create ensemble prediction from multiple models"""
        try:
            predictions = []
            confidences = []
            models_used = []
            
            # Get predictions from different models
            model_types = ['random_forest', 'xgboost', 'gradient_boosting']
            
            for model_type in model_types:
                try:
                    pred = self.predict_price(symbol, horizon, model_type)
                    predictions.append(pred.predicted_value)
                    confidences.append(pred.confidence)
                    models_used.append(model_type)
                except Exception as e:
                    logger.warning(f"Model {model_type} failed for {symbol}: {e}")
                    continue
            
            if not predictions:
                raise ValueError("No models produced valid predictions")
            
            # Weight predictions by confidence
            weights = np.array(confidences) / sum(confidences)
            ensemble_prediction = np.average(predictions, weights=weights)
            
            # Ensemble confidence (weighted average of individual confidences)
            ensemble_confidence = np.average(confidences, weights=weights)
            
            # Add uncertainty discount for ensemble
            ensemble_confidence *= 0.9
            
            result = PredictionResult(
                symbol=symbol,
                prediction_type='price',
                predicted_value=ensemble_prediction,
                confidence=ensemble_confidence,
                prediction_horizon=horizon,
                model_used='ensemble(' + ','.join(models_used) + ')',
                feature_importance={},
                timestamp=datetime.utcnow()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ensemble prediction error for {symbol}: {e}")
            raise
    
    def _get_training_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """Get training data for model"""
        try:
            return self.data_collector.get_historical_data(symbol, period)
        except Exception as e:
            logger.error(f"Training data retrieval error for {symbol}: {e}")
            return None
    
    def _prepare_features_targets(self, data: pd.DataFrame, prediction_type: str,
                                horizon: int = 1) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and targets for training"""
        try:
            features = pd.DataFrame()
            
            # Price-based features
            features['open'] = data['Open']
            features['high'] = data['High']
            features['low'] = data['Low']
            features['close'] = data['Close']
            features['volume'] = data['Volume']
            
            # Returns
            features['returns'] = data['Close'].pct_change()
            features['log_returns'] = np.log(data['Close'] / data['Close'].shift(1))
            
            # Price ratios
            features['high_low_ratio'] = data['High'] / data['Low']
            features['close_open_ratio'] = data['Close'] / data['Open']
            
            # Technical indicators
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            features['rsi'] = 100 - (100 / (1 + rs))
            
            # Simple moving averages
            for period in [5, 10, 20, 50]:
                features[f'sma_{period}'] = data['Close'].rolling(period).mean()
                features[f'price_sma_{period}_ratio'] = data['Close'] / features[f'sma_{period}']
            
            # Exponential moving averages
            for period in [12, 26]:
                features[f'ema_{period}'] = data['Close'].ewm(span=period).mean()
            
            # MACD
            ema_12 = data['Close'].ewm(span=12).mean()
            ema_26 = data['Close'].ewm(span=26).mean()
            features['macd'] = ema_12 - ema_26
            features['macd_signal'] = features['macd'].ewm(span=9).mean()
            features['macd_histogram'] = features['macd'] - features['macd_signal']
            
            # Bollinger Bands
            sma_20 = data['Close'].rolling(20).mean()
            std_20 = data['Close'].rolling(20).std()
            features['bb_upper'] = sma_20 + (std_20 * 2)
            features['bb_lower'] = sma_20 - (std_20 * 2)
            features['bb_position'] = (data['Close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
            
            # Volatility features
            for period in [5, 10, 20]:
                features[f'volatility_{period}'] = features['returns'].rolling(period).std()
            
            # Volume features
            features['volume_sma_20'] = data['Volume'].rolling(20).mean()
            features['volume_ratio'] = data['Volume'] / features['volume_sma_20']
            
            # Lag features
            for lag in [1, 2, 3, 5]:
                features[f'close_lag_{lag}'] = data['Close'].shift(lag)
                features[f'returns_lag_{lag}'] = features['returns'].shift(lag)
                features[f'volume_lag_{lag}'] = data['Volume'].shift(lag)
            
            # Rolling statistics
            for window in [5, 10, 20]:
                features[f'close_mean_{window}'] = data['Close'].rolling(window).mean()
                features[f'close_std_{window}'] = data['Close'].rolling(window).std()
                features[f'volume_mean_{window}'] = data['Volume'].rolling(window).mean()
            
            # Prepare targets based on prediction type
            if prediction_type == 'price':
                # Predict future close price
                targets = data['Close'].shift(-horizon).dropna()
            elif prediction_type == 'returns':
                # Predict future returns
                targets = data['Close'].pct_change(periods=horizon).shift(-horizon).dropna()
            else:
                targets = data['Close'].shift(-horizon).dropna()
            
            # Remove NaN values and align
            features = features.dropna()
            min_length = min(len(features), len(targets))
            features = features.iloc[:min_length]
            targets = targets.iloc[:min_length]
            
            return features, targets
            
        except Exception as e:
            logger.error(f"Feature preparation error: {e}")
            raise
    
    def _prepare_volatility_features(self, data: pd.DataFrame, returns: pd.Series) -> pd.DataFrame:
        """Prepare features specifically for volatility prediction"""
        try:
            features = pd.DataFrame()
            
            # Historical volatility features
            for window in [5, 10, 20, 30]:
                features[f'vol_{window}'] = returns.rolling(window).std()
                features[f'vol_mean_{window}'] = features[f'vol_{window}'].rolling(window).mean()
            
            # GARCH-like features
            features['vol_lag_1'] = returns.rolling(5).std().shift(1)
            features['vol_lag_2'] = returns.rolling(5).std().shift(2)
            features['vol_lag_3'] = returns.rolling(5).std().shift(3)
            
            # Return-based features
            features['abs_returns'] = returns.abs()
            features['squared_returns'] = returns ** 2
            
            # Range-based volatility
            features['high_low_vol'] = (data['High'] - data['Low']) / data['Close']
            features['close_open_vol'] = abs(data['Close'] - data['Open']) / data['Open']
            
            # Volume-volatility relationship
            features['volume_vol'] = data['Volume'].pct_change().rolling(10).std()
            
            return features.dropna()
            
        except Exception as e:
            logger.error(f"Volatility feature preparation error: {e}")
            return pd.DataFrame()
    
    def _prepare_lstm_features(self, data: pd.DataFrame, sequence_length: int,
                              horizon: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features for LSTM model"""
        try:
            # Use scaled close prices
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(data[['Close']].values)
            
            X, y = [], []
            
            for i in range(sequence_length, len(scaled_data) - horizon):
                X.append(scaled_data[i-sequence_length:i])
                y.append(scaled_data[i + horizon - 1])
            
            X = np.array(X)
            y = np.array(y)
            
            # Store scaler for inverse transform
            self.scalers[f'lstm_scaler'] = scaler
            
            return X, y
            
        except Exception as e:
            logger.error(f"LSTM feature preparation error: {e}")
            raise
    
    def _get_or_train_model(self, symbol: str, model_category: str, model_type: str,
                           features: pd.DataFrame, targets: pd.Series):
        """Get existing model or train new one"""
        try:
            model_key = f"{model_category}_{model_type}_{symbol}"
            
            # Try to load existing model
            model_path = self.models_dir / f"{model_key}.pkl"
            
            if model_path.exists():
                try:
                    model = joblib.load(model_path)
                    logger.info(f"Loaded existing model: {model_key}")
                    return model
                except Exception as e:
                    logger.warning(f"Failed to load model {model_key}: {e}")
            
            # Train new model
            model = self.models[model_category][model_type]
            
            # Scale features if needed
            if hasattr(model, 'kernel') or 'neural' in model_type:  # SVM or neural network
                scaler = self.scalers['technical']
                features_scaled = scaler.fit_transform(features)
                model.fit(features_scaled, targets)
                
                # Store scaler
                scaler_path = self.models_dir / f"{model_key}_scaler.pkl"
                joblib.dump(scaler, scaler_path)
            else:
                model.fit(features, targets)
            
            # Save model
            joblib.dump(model, model_path)
            
            logger.info(f"Trained and saved model: {model_key}")
            return model
            
        except Exception as e:
            logger.error(f"Model training error: {e}")
            raise
    
    def _calculate_prediction_confidence(self, model, features: pd.DataFrame,
                                       targets: pd.Series, latest_features: np.ndarray) -> float:
        """Calculate confidence score for prediction"""
        try:
            # Use cross-validation or out-of-sample performance
            train_size = int(len(features) * 0.8)
            
            X_train = features.iloc[:train_size]
            X_test = features.iloc[train_size:]
            y_train = targets.iloc[:train_size] 
            y_test = targets.iloc[train_size:]
            
            if len(X_test) < 5:  # Not enough test data
                return 0.5
            
            # Test model performance
            if hasattr(model, 'predict'):
                predictions = model.predict(X_test)
                
                # Calculate R² score
                r2 = r2_score(y_test, predictions)
                
                # Convert to confidence (0.5 to 0.95 range)
                confidence = max(0.1, min(0.95, (r2 + 1) / 2))
                
                return confidence
            
            return 0.5
            
        except Exception as e:
            logger.error(f"Confidence calculation error: {e}")
            return 0.5
    
    def _get_feature_importance(self, model, feature_names: List[str]) -> Dict[str, float]:
        """Get feature importance from model"""
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                if len(importances) == len(feature_names):
                    return dict(zip(feature_names, importances.tolist()))
            elif hasattr(model, 'coef_'):
                coefficients = np.abs(model.coef_).flatten()
                if len(coefficients) == len(feature_names):
                    return dict(zip(feature_names, coefficients.tolist()))
            
            return {}
            
        except Exception as e:
            logger.error(f"Feature importance error: {e}")
            return {}
    
    def _cache_prediction(self, result: PredictionResult):
        """Cache prediction result"""
        try:
            cache_key = f"ml_prediction_{result.symbol}_{result.prediction_type}_{result.prediction_horizon}"
            
            # Convert to dict for caching
            data = {
                'symbol': result.symbol,
                'prediction_type': result.prediction_type,
                'predicted_value': result.predicted_value,
                'confidence': result.confidence,
                'prediction_horizon': result.prediction_horizon,
                'model_used': result.model_used,
                'timestamp': result.timestamp.isoformat()
            }
            
            # Cache for 1 hour
            self.cache_manager.set(cache_key, data, ttl=3600)
            
        except Exception as e:
            logger.error(f"Prediction caching error: {e}")
    
    def evaluate_model_performance(self, symbol: str, model_type: str, 
                                 test_period: int = 30) -> ModelPerformance:
        """Evaluate model performance over test period"""
        try:
            # Get test data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=test_period + 100)  # Extra data for features
            
            test_data = self.data_collector.get_historical_data(
                symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
            )
            
            if test_data is None or len(test_data) < test_period:
                raise ValueError("Insufficient test data")
            
            # Prepare features and actual values
            features, actual_values = self._prepare_features_targets(test_data, 'price', 1)
            
            # Use last test_period days for evaluation
            test_features = features.iloc[-test_period:]
            test_actual = actual_values.iloc[-test_period:]
            
            # Load model and make predictions
            model_key = f"price_prediction_{model_type}_{symbol}"
            model_path = self.models_dir / f"{model_key}.pkl"
            
            if not model_path.exists():
                raise ValueError(f"Model not found: {model_key}")
            
            model = joblib.load(model_path)
            predictions = model.predict(test_features)
            
            # Calculate metrics
            mse = mean_squared_error(test_actual, predictions)
            mae = mean_absolute_error(test_actual, predictions)
            r2 = r2_score(test_actual, predictions)
            
            # Direction accuracy
            actual_direction = (test_actual.diff() > 0).astype(int)
            predicted_direction = (pd.Series(predictions).diff() > 0).astype(int)
            direction_accuracy = (actual_direction == predicted_direction).mean()
            
            performance = ModelPerformance(
                model_name=f"{model_type}_{symbol}",
                mse=mse,
                mae=mae,
                r2_score=r2,
                accuracy=direction_accuracy,
                precision=direction_accuracy,  # Simplified
                recall=direction_accuracy,     # Simplified
                training_samples=len(features),
                last_updated=datetime.utcnow()
            )
            
            return performance
            
        except Exception as e:
            logger.error(f"Model evaluation error: {e}")
            raise
    
    def get_model_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostics for all models"""
        try:
            diagnostics = {
                'models_loaded': 0,
                'models_trained': 0,
                'cache_hit_rate': 0,
                'avg_confidence': 0,
                'model_files': [],
                'recent_predictions': 0
            }
            
            # Count model files
            model_files = list(self.models_dir.glob("*.pkl"))
            diagnostics['models_trained'] = len(model_files)
            diagnostics['model_files'] = [f.name for f in model_files]
            
            # Cache statistics (if available)
            try:
                cache_stats = self.cache_manager.get_stats()
                diagnostics.update(cache_stats)
            except:
                pass
            
            return diagnostics
            
        except Exception as e:
            logger.error(f"Diagnostics error: {e}")
            return {}


# Global ML engine instance
_ml_engine: Optional[MLPredictionEngine] = None


def get_ml_engine() -> MLPredictionEngine:
    """Get the global ML prediction engine instance"""
    global _ml_engine
    if _ml_engine is None:
        _ml_engine = MLPredictionEngine()
    return _ml_engine


if __name__ == "__main__":
    # Test ML prediction engine
    engine = MLPredictionEngine()
    
    try:
        # Test price prediction
        result = engine.predict_price("NVDA", horizon=1, model_type='random_forest')
        print(f"Price Prediction for NVDA:")
        print(f"Predicted Price: ${result.predicted_value:.2f}")
        print(f"Confidence: {result.confidence:.2%}")
        print(f"Model: {result.model_used}")
        
        # Test volatility prediction
        vol_result = engine.predict_volatility("NVDA", horizon=5)
        print(f"\nVolatility Prediction for NVDA:")
        print(f"Predicted Volatility: {vol_result.predicted_value:.2%}")
        print(f"Confidence: {vol_result.confidence:.2%}")
        
        # Test direction prediction
        dir_result = engine.predict_direction("NVDA", horizon=1)
        print(f"\nDirection Prediction for NVDA:")
        print(f"Upward Probability: {dir_result.predicted_value:.2%}")
        print(f"Confidence: {dir_result.confidence:.2%}")
        
    except Exception as e:
        print(f"Test failed: {e}")