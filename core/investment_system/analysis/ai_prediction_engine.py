"""
AI Prediction Engine
Advanced ML models for price forecasting, pattern recognition, and anomaly detection
"""

import json
import numpy as np
import pandas as pd
import yfinance as yf
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIPredictionEngine:
    def __init__(self, config_file: str = "config.json"):
        """Initialize AI prediction engine"""
        self.config = self.load_config(config_file)
        self.scaler = StandardScaler()
        
        # Model storage
        self.price_models = {}
        self.volatility_models = {}
        self.pattern_models = {}
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return {}
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare technical features for ML models"""
        try:
            features = df.copy()
            
            # Price-based features
            features['returns'] = features['Close'].pct_change()
            features['log_returns'] = np.log(features['Close'] / features['Close'].shift(1))
            features['price_momentum_5'] = features['Close'] / features['Close'].shift(5) - 1
            features['price_momentum_10'] = features['Close'] / features['Close'].shift(10) - 1
            features['price_momentum_20'] = features['Close'] / features['Close'].shift(20) - 1
            
            # Moving averages
            features['sma_5'] = features['Close'].rolling(5).mean()
            features['sma_10'] = features['Close'].rolling(10).mean()
            features['sma_20'] = features['Close'].rolling(20).mean()
            features['sma_50'] = features['Close'].rolling(50).mean()
            
            # Moving average ratios
            features['price_to_sma20'] = features['Close'] / features['sma_20']
            features['price_to_sma50'] = features['Close'] / features['sma_50']
            features['sma20_to_sma50'] = features['sma_20'] / features['sma_50']
            
            # Volatility features
            features['volatility_5'] = features['returns'].rolling(5).std()
            features['volatility_10'] = features['returns'].rolling(10).std()
            features['volatility_20'] = features['returns'].rolling(20).std()
            
            # Volume features
            features['volume_sma'] = features['Volume'].rolling(20).mean()
            features['volume_ratio'] = features['Volume'] / features['volume_sma']
            features['price_volume'] = features['Close'] * features['Volume']
            
            # High-Low features
            features['hl_ratio'] = features['High'] / features['Low']
            features['close_position'] = (features['Close'] - features['Low']) / (features['High'] - features['Low'])
            
            # RSI
            delta = features['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            features['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = features['Close'].ewm(span=12).mean()
            exp2 = features['Close'].ewm(span=26).mean()
            features['macd'] = exp1 - exp2
            features['macd_signal'] = features['macd'].ewm(span=9).mean()
            features['macd_histogram'] = features['macd'] - features['macd_signal']
            
            # Bollinger Bands
            features['bb_middle'] = features['Close'].rolling(20).mean()
            bb_std = features['Close'].rolling(20).std()
            features['bb_upper'] = features['bb_middle'] + (bb_std * 2)
            features['bb_lower'] = features['bb_middle'] - (bb_std * 2)
            features['bb_position'] = (features['Close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
            
            # Lag features
            for lag in [1, 2, 3, 5]:
                features[f'close_lag_{lag}'] = features['Close'].shift(lag)
                features[f'volume_lag_{lag}'] = features['Volume'].shift(lag)
                features[f'returns_lag_{lag}'] = features['returns'].shift(lag)
            
            # Time-based features
            features['day_of_week'] = pd.to_datetime(features.index).dayofweek
            features['month'] = pd.to_datetime(features.index).month
            features['quarter'] = pd.to_datetime(features.index).quarter
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return df
    
    def detect_patterns(self, df: pd.DataFrame) -> Dict:
        """AI-driven technical pattern detection"""
        try:
            patterns = {
                'timestamp': datetime.now().isoformat(),
                'patterns_detected': [],
                'pattern_strength': {},
                'bullish_patterns': 0,
                'bearish_patterns': 0
            }
            
            if len(df) < 50:
                return patterns
            
            # Double top/bottom detection
            highs = df['High'].rolling(window=5, center=True).max()
            lows = df['Low'].rolling(window=5, center=True).min()
            
            # Find local peaks and troughs
            local_highs = df['High'] == highs
            local_lows = df['Low'] == lows
            
            # Support and resistance levels
            resistance_levels = df[local_highs]['High'].tail(10).tolist()
            support_levels = df[local_lows]['Low'].tail(10).tolist()
            
            current_price = df['Close'].iloc[-1]
            
            # Check for breakouts
            if resistance_levels:
                recent_resistance = max(resistance_levels[-3:]) if len(resistance_levels) >= 3 else max(resistance_levels)
                if current_price > recent_resistance * 1.02:  # 2% breakout
                    patterns['patterns_detected'].append("Resistance breakout")
                    patterns['pattern_strength']['resistance_breakout'] = 'strong'
                    patterns['bullish_patterns'] += 1
            
            if support_levels:
                recent_support = min(support_levels[-3:]) if len(support_levels) >= 3 else min(support_levels)
                if current_price < recent_support * 0.98:  # 2% breakdown
                    patterns['patterns_detected'].append("Support breakdown")
                    patterns['pattern_strength']['support_breakdown'] = 'strong'
                    patterns['bearish_patterns'] += 1
            
            # Moving average patterns
            sma20 = df['Close'].rolling(20).mean().iloc[-1]
            sma50 = df['Close'].rolling(50).mean().iloc[-1]
            
            if current_price > sma20 > sma50:
                patterns['patterns_detected'].append("Bullish MA alignment")
                patterns['bullish_patterns'] += 1
            elif current_price < sma20 < sma50:
                patterns['patterns_detected'].append("Bearish MA alignment")
                patterns['bearish_patterns'] += 1
            
            # Volume confirmation
            recent_volume = df['Volume'].tail(5).mean()
            avg_volume = df['Volume'].tail(20).mean()
            
            if recent_volume > avg_volume * 1.5:
                patterns['patterns_detected'].append("High volume confirmation")
                patterns['pattern_strength']['volume_confirmation'] = 'strong'
            
            # RSI divergence detection
            price_trend = (df['Close'].iloc[-1] - df['Close'].iloc[-10]) / df['Close'].iloc[-10]
            rsi_current = self.calculate_rsi(df['Close'])
            rsi_10_ago = self.calculate_rsi(df['Close'].iloc[:-10]) if len(df) > 20 else rsi_current
            rsi_trend = rsi_current - rsi_10_ago
            
            # Bullish divergence: price down, RSI up
            if price_trend < -0.02 and rsi_trend > 5:
                patterns['patterns_detected'].append("Bullish RSI divergence")
                patterns['bullish_patterns'] += 1
            
            # Bearish divergence: price up, RSI down
            if price_trend > 0.02 and rsi_trend < -5:
                patterns['patterns_detected'].append("Bearish RSI divergence")
                patterns['bearish_patterns'] += 1
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return {'patterns_detected': [], 'error': str(e)}
    
    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> float:
        """Calculate RSI for pattern detection"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not rsi.empty else 50.0
        except:
            return 50.0
    
    def predict_price_ml(self, symbol: str, forecast_days: int = 5) -> Dict:
        """ML-based price prediction using Random Forest"""
        try:
            logger.info(f"Generating ML price prediction for {symbol}")
            
            # Get historical data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            
            if len(hist) < 100:
                return {'error': 'Insufficient data for prediction'}
            
            # Prepare features
            features_df = self.prepare_features(hist)
            features_df = features_df.dropna()
            
            if len(features_df) < 50:
                return {'error': 'Insufficient clean data for prediction'}
            
            # Define feature columns (exclude target and non-predictive columns)
            exclude_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
            feature_cols = [col for col in features_df.columns if col not in exclude_cols]
            
            # Prepare training data with better target engineering
            X = features_df[feature_cols].fillna(method='ffill').fillna(0)
            
            # Predict percentage change instead of absolute price
            y = features_df['Close'].pct_change().shift(-1).dropna()  # Predict next day's return
            
            # Remove outliers (beyond 3 standard deviations)
            y_std = y.std()
            y_mean = y.mean()
            outlier_mask = (np.abs(y - y_mean) <= 3 * y_std)
            
            # Align X and y and remove outliers
            min_len = min(len(X), len(y))
            X = X.iloc[:min_len][outlier_mask]
            y = y.iloc[:min_len][outlier_mask]
            
            if len(X) < 30:
                return {'error': 'Insufficient clean data after outlier removal'}
            
            # Feature scaling
            scaler = StandardScaler()
            X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns, index=X.index)
            
            # Time series split for better validation
            train_size = int(len(X_scaled) * 0.8)
            X_train, X_test = X_scaled.iloc[:train_size], X_scaled.iloc[train_size:]
            y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]
            
            # Ensemble model with multiple algorithms
            from sklearn.ensemble import GradientBoostingRegressor, VotingRegressor
            from sklearn.linear_model import Ridge
            
            rf_model = RandomForestRegressor(
                n_estimators=200,
                max_depth=8,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            
            gb_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            ridge_model = Ridge(alpha=1.0)
            
            # Ensemble model
            model = VotingRegressor([
                ('rf', rf_model),
                ('gb', gb_model),
                ('ridge', ridge_model)
            ])
            
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate accuracy metrics
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Predict future returns and convert to prices
            current_features = X_scaled.iloc[-1:].values
            current_price = features_df['Close'].iloc[-1]
            predictions = []
            predicted_price = current_price
            
            # Use walk-forward prediction
            for i in range(forecast_days):
                pred_return = model.predict(current_features.reshape(1, -1))[0]
                
                # Convert return to price
                predicted_price = predicted_price * (1 + pred_return)
                predictions.append(predicted_price)
                
                # Update features for next prediction using predicted values
                if i < forecast_days - 1:
                    # Simple feature update - in practice, recalculate all technical indicators
                    new_features = current_features.copy()
                    # Update price-based features with predicted price
                    new_features[0][0] = pred_return  # Update returns feature
                    current_features = new_features
            
            # Calculate confidence intervals using prediction errors
            prediction_errors = np.abs(y_test - y_pred)
            error_std = np.std(prediction_errors)
            current_price = features_df['Close'].iloc[-1]
            volatility = features_df['Close'].pct_change().std() * np.sqrt(252)  # Annualized volatility
            
            prediction_results = {
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'predictions': [round(p, 2) for p in predictions],
                'forecast_days': forecast_days,
                'model_accuracy': {
                    'r2_score': round(r2, 3),
                    'mse': round(mse, 2),
                    'accuracy_rating': 'high' if r2 > 0.7 else 'medium' if r2 > 0.5 else 'low'
                },
                'confidence_intervals': [],
                'prediction_trend': self.analyze_prediction_trend(predictions, current_price),
                'feature_importance': self.get_ensemble_feature_importance(model, feature_cols)
            }
            
            # Calculate confidence intervals using model uncertainty
            for i, pred in enumerate(predictions):
                # Confidence interval widens with forecast horizon
                confidence_multiplier = 1 + (i * 0.2)  # Increase uncertainty over time
                error_margin = error_std * confidence_multiplier * pred
                
                lower_bound = pred - error_margin
                upper_bound = pred + error_margin
                prediction_results['confidence_intervals'].append({
                    'lower': round(max(0, lower_bound), 2),  # Price can't be negative
                    'upper': round(upper_bound, 2)
                })
            
            return prediction_results
            
        except Exception as e:
            logger.error(f"Error in ML price prediction for {symbol}: {e}")
            return {'error': str(e)}
    
    def get_ensemble_feature_importance(self, ensemble_model, feature_cols: List[str]) -> Dict:
        """Get feature importance from ensemble model"""
        try:
            # Get importance from Random Forest (first estimator)
            rf_model = ensemble_model.estimators_[0]
            if hasattr(rf_model, 'feature_importances_'):
                return dict(zip(feature_cols, rf_model.feature_importances_))
            else:
                # Fallback: equal importance
                equal_importance = 1.0 / len(feature_cols)
                return {col: equal_importance for col in feature_cols}
        except Exception as e:
            logger.warning(f"Error getting feature importance: {e}")
            return {}
    
    def analyze_prediction_trend(self, predictions: List[float], current_price: float) -> Dict:
        """Analyze the trend in predictions"""
        try:
            if not predictions:
                return {'trend': 'unknown', 'confidence': 0}
            
            final_price = predictions[-1]
            price_change = (final_price - current_price) / current_price * 100
            
            # Calculate trend consistency
            changes = [predictions[i] - predictions[i-1] for i in range(1, len(predictions))]
            positive_changes = sum(1 for change in changes if change > 0)
            negative_changes = sum(1 for change in changes if change < 0)
            
            trend_consistency = max(positive_changes, negative_changes) / len(changes) if changes else 0
            
            if price_change > 2:
                trend = 'strongly_bullish'
            elif price_change > 0.5:
                trend = 'bullish'
            elif price_change > -0.5:
                trend = 'sideways'
            elif price_change > -2:
                trend = 'bearish'
            else:
                trend = 'strongly_bearish'
            
            return {
                'trend': trend,
                'price_change_pct': round(price_change, 2),
                'consistency': round(trend_consistency, 2),
                'confidence': round(trend_consistency * 100, 1)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing prediction trend: {e}")
            return {'trend': 'unknown', 'confidence': 0}
    
    def detect_anomalies(self, symbol: str) -> Dict:
        """Detect unusual trading patterns using Isolation Forest"""
        try:
            logger.info(f"Detecting anomalies for {symbol}")
            
            # Get historical data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="6mo")
            
            if len(hist) < 50:
                return {'error': 'Insufficient data for anomaly detection'}
            
            # Prepare features for anomaly detection
            features_df = self.prepare_features(hist)
            
            # Select relevant features for anomaly detection
            anomaly_features = [
                'returns', 'volume_ratio', 'volatility_20', 'rsi',
                'price_to_sma20', 'bb_position', 'close_position'
            ]
            
            # Filter features and handle missing values
            available_features = [f for f in anomaly_features if f in features_df.columns]
            X = features_df[available_features].fillna(method='ffill').fillna(0)
            
            if len(X) < 30:
                return {'error': 'Insufficient clean data for anomaly detection'}
            
            # Fit Isolation Forest
            iso_forest = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100
            )
            
            anomaly_scores = iso_forest.fit_predict(X)
            anomaly_probs = iso_forest.score_samples(X)
            
            # Identify recent anomalies
            recent_days = 10
            recent_anomalies = anomaly_scores[-recent_days:]
            recent_probs = anomaly_probs[-recent_days:]
            recent_dates = hist.index[-recent_days:]
            
            anomalies_detected = []
            for i, (score, prob, date) in enumerate(zip(recent_anomalies, recent_probs, recent_dates)):
                if score == -1:  # Anomaly detected
                    day_data = hist.iloc[-(recent_days-i)]
                    anomalies_detected.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'anomaly_score': round(prob, 3),
                        'price': round(day_data['Close'], 2),
                        'volume': int(day_data['Volume']),
                        'price_change': round(day_data['Close'] / day_data['Open'] - 1, 4),
                        'description': self.describe_anomaly(features_df.iloc[-(recent_days-i)], available_features)
                    })
            
            # Overall anomaly assessment
            anomaly_count = sum(1 for score in recent_anomalies if score == -1)
            
            return {
                'symbol': symbol,
                'analysis_period': f"{len(hist)} days",
                'recent_anomalies': anomalies_detected,
                'anomaly_count_recent': anomaly_count,
                'anomaly_level': 'high' if anomaly_count > 3 else 'medium' if anomaly_count > 1 else 'low',
                'overall_pattern': 'unusual' if anomaly_count > 2 else 'normal',
                'recommendation': self.get_anomaly_recommendation(anomaly_count, anomalies_detected)
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies for {symbol}: {e}")
            return {'error': str(e)}
    
    def describe_anomaly(self, row_data: pd.Series, features: List[str]) -> str:
        """Describe what makes this data point anomalous"""
        try:
            descriptions = []
            
            if 'volume_ratio' in features and row_data.get('volume_ratio', 1) > 3:
                descriptions.append("Extremely high volume")
            elif 'volume_ratio' in features and row_data.get('volume_ratio', 1) < 0.3:
                descriptions.append("Unusually low volume")
            
            if 'returns' in features:
                returns = row_data.get('returns', 0)
                if abs(returns) > 0.1:  # 10% move
                    direction = "surge" if returns > 0 else "drop"
                    descriptions.append(f"Large price {direction}")
            
            if 'volatility_20' in features and row_data.get('volatility_20', 0) > 0.05:
                descriptions.append("High volatility")
            
            if 'rsi' in features:
                rsi = row_data.get('rsi', 50)
                if rsi > 80:
                    descriptions.append("Extreme overbought")
                elif rsi < 20:
                    descriptions.append("Extreme oversold")
            
            return "; ".join(descriptions) if descriptions else "Unusual pattern detected"
            
        except Exception as e:
            return "Pattern analysis error"
    
    def get_anomaly_recommendation(self, anomaly_count: int, anomalies: List[Dict]) -> str:
        """Get recommendation based on anomaly analysis"""
        if anomaly_count == 0:
            return "Normal trading patterns - no special action needed"
        elif anomaly_count == 1:
            return "Minor anomaly detected - monitor closely"
        elif anomaly_count <= 3:
            return "Multiple anomalies - exercise caution and wait for pattern confirmation"
        else:
            return "High anomaly activity - consider avoiding new positions until patterns normalize"
    
    def predict_volatility(self, symbol: str, forecast_days: int = 5) -> Dict:
        """Predict future volatility using historical patterns"""
        try:
            logger.info(f"Predicting volatility for {symbol}")
            
            # Get historical data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            
            if len(hist) < 100:
                return {'error': 'Insufficient data for volatility prediction'}
            
            # Calculate returns and rolling volatility
            returns = hist['Close'].pct_change().dropna()
            
            # Different volatility windows
            vol_5 = returns.rolling(5).std() * np.sqrt(252)
            vol_10 = returns.rolling(10).std() * np.sqrt(252)
            vol_20 = returns.rolling(20).std() * np.sqrt(252)
            
            # Current volatility metrics
            current_vol_20 = vol_20.iloc[-1]
            avg_vol_20 = vol_20.mean()
            vol_percentile = (vol_20.iloc[-1] - vol_20.min()) / (vol_20.max() - vol_20.min())
            
            # Simple volatility forecasting using mean reversion
            # High volatility tends to revert to mean
            reversion_factor = 0.1  # How quickly volatility reverts
            
            predictions = []
            current_vol = current_vol_20
            
            for i in range(forecast_days):
                # Mean reversion formula
                predicted_vol = current_vol + reversion_factor * (avg_vol_20 - current_vol)
                predictions.append(predicted_vol)
                current_vol = predicted_vol
            
            # Volatility regime classification
            if current_vol_20 > avg_vol_20 * 1.5:
                regime = "high_volatility"
            elif current_vol_20 < avg_vol_20 * 0.7:
                regime = "low_volatility"
            else:
                regime = "normal_volatility"
            
            return {
                'symbol': symbol,
                'current_volatility': round(current_vol_20 * 100, 2),
                'average_volatility': round(avg_vol_20 * 100, 2),
                'volatility_percentile': round(vol_percentile * 100, 1),
                'volatility_regime': regime,
                'predicted_volatility': [round(v * 100, 2) for v in predictions],
                'forecast_days': forecast_days,
                'trend': 'increasing' if predictions[-1] > current_vol_20 else 'decreasing',
                'trading_recommendation': self.get_volatility_recommendation(regime, predictions[-1], current_vol_20)
            }
            
        except Exception as e:
            logger.error(f"Error predicting volatility for {symbol}: {e}")
            return {'error': str(e)}
    
    def get_volatility_recommendation(self, regime: str, future_vol: float, current_vol: float) -> str:
        """Get trading recommendation based on volatility forecast"""
        if regime == "high_volatility":
            if future_vol < current_vol:
                return "High volatility expected to decrease - good entry opportunity"
            else:
                return "Volatility remaining high - use smaller position sizes"
        elif regime == "low_volatility":
            if future_vol > current_vol:
                return "Volatility expected to increase - prepare for larger moves"
            else:
                return "Low volatility persisting - consider strategies that benefit from stability"
        else:
            return "Normal volatility expected - standard position sizing appropriate"
    
    def generate_ai_analysis(self, symbols: List[str]) -> Dict:
        """Generate comprehensive AI analysis for all symbols"""
        try:
            logger.info(f"Generating AI analysis for {len(symbols)} symbols")
            
            analysis = {
                'generated_at': datetime.now().isoformat(),
                'symbols_analyzed': symbols,
                'price_predictions': {},
                'pattern_analysis': {},
                'anomaly_detection': {},
                'volatility_forecasts': {},
                'ai_summary': {}
            }
            
            for symbol in symbols[:5]:  # Limit to 5 for performance
                print(f"   AI analysis for {symbol}...")
                
                # Price predictions
                try:
                    analysis['price_predictions'][symbol] = self.predict_price_ml(symbol)
                except Exception as e:
                    logger.warning(f"Price prediction failed for {symbol}: {e}")
                
                # Pattern detection
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="3mo")
                    if not hist.empty:
                        analysis['pattern_analysis'][symbol] = self.detect_patterns(hist)
                except Exception as e:
                    logger.warning(f"Pattern analysis failed for {symbol}: {e}")
                
                # Anomaly detection
                try:
                    analysis['anomaly_detection'][symbol] = self.detect_anomalies(symbol)
                except Exception as e:
                    logger.warning(f"Anomaly detection failed for {symbol}: {e}")
                
                # Volatility forecasting
                try:
                    analysis['volatility_forecasts'][symbol] = self.predict_volatility(symbol)
                except Exception as e:
                    logger.warning(f"Volatility prediction failed for {symbol}: {e}")
                
                time.sleep(0.5)  # Rate limiting
            
            # Generate AI summary
            analysis['ai_summary'] = self.create_ai_summary(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}")
            return {'error': str(e)}
    
    def create_ai_summary(self, analysis: Dict) -> Dict:
        """Create AI-powered summary of all analysis"""
        summary = {
            'overall_sentiment': 'neutral',
            'high_confidence_predictions': [],
            'pattern_signals': [],
            'anomaly_alerts': [],
            'volatility_warnings': [],
            'ai_recommendations': []
        }
        
        try:
            # Analyze price predictions
            predictions = analysis.get('price_predictions', {})
            bullish_count = 0
            bearish_count = 0
            
            for symbol, pred in predictions.items():
                if isinstance(pred, dict) and 'prediction_trend' in pred:
                    trend = pred['prediction_trend']
                    if trend.get('trend') in ['bullish', 'strongly_bullish']:
                        bullish_count += 1
                        if pred.get('model_accuracy', {}).get('accuracy_rating') == 'high':
                            summary['high_confidence_predictions'].append({
                                'symbol': symbol,
                                'trend': trend.get('trend'),
                                'confidence': trend.get('confidence', 0)
                            })
                    elif trend.get('trend') in ['bearish', 'strongly_bearish']:
                        bearish_count += 1
            
            # Overall sentiment
            if bullish_count > bearish_count:
                summary['overall_sentiment'] = 'bullish'
            elif bearish_count > bullish_count:
                summary['overall_sentiment'] = 'bearish'
            
            # Pattern analysis
            patterns = analysis.get('pattern_analysis', {})
            for symbol, pattern_data in patterns.items():
                if isinstance(pattern_data, dict):
                    detected = pattern_data.get('patterns_detected', [])
                    for pattern in detected:
                        summary['pattern_signals'].append({
                            'symbol': symbol,
                            'pattern': pattern
                        })
            
            # Anomaly alerts
            anomalies = analysis.get('anomaly_detection', {})
            for symbol, anomaly_data in anomalies.items():
                if isinstance(anomaly_data, dict):
                    if anomaly_data.get('anomaly_level') in ['high', 'medium']:
                        summary['anomaly_alerts'].append({
                            'symbol': symbol,
                            'level': anomaly_data.get('anomaly_level'),
                            'count': anomaly_data.get('anomaly_count_recent', 0)
                        })
            
            # Volatility warnings
            volatility = analysis.get('volatility_forecasts', {})
            for symbol, vol_data in volatility.items():
                if isinstance(vol_data, dict):
                    if vol_data.get('volatility_regime') == 'high_volatility':
                        summary['volatility_warnings'].append({
                            'symbol': symbol,
                            'current_vol': vol_data.get('current_volatility', 0),
                            'trend': vol_data.get('trend', 'unknown')
                        })
            
            # Generate AI recommendations
            if summary['high_confidence_predictions']:
                summary['ai_recommendations'].append(
                    f"High confidence ML predictions available for {len(summary['high_confidence_predictions'])} stocks"
                )
            
            if summary['anomaly_alerts']:
                summary['ai_recommendations'].append(
                    f"Unusual patterns detected in {len(summary['anomaly_alerts'])} stocks - exercise caution"
                )
            
            if summary['volatility_warnings']:
                summary['ai_recommendations'].append(
                    f"High volatility expected in {len(summary['volatility_warnings'])} stocks - adjust position sizes"
                )
        
        except Exception as e:
            logger.error(f"Error creating AI summary: {e}")
        
        return summary
    
    def save_ai_analysis(self, analysis: Dict, filename: str = None):
        """Save AI analysis to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_analysis_{timestamp}.json"
        
        filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, default=str)
            logger.info(f"AI analysis saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving AI analysis: {e}")

def main():
    """Main execution function"""
    engine = AIPredictionEngine()
    
    # Target stocks for AI analysis
    target_stocks = ["NVDA", "MSFT", "TSLA", "AMZN", "GOOGL"]
    
    print("Starting AI Prediction Analysis...")
    print("This includes: ML Price Predictions, Pattern Recognition, Anomaly Detection, Volatility Forecasting")
    
    # Generate AI analysis
    analysis = engine.generate_ai_analysis(target_stocks)
    
    # Save analysis
    engine.save_ai_analysis(analysis)
    
    # Print summary
    print("\n=== AI ANALYSIS SUMMARY ===")
    
    ai_summary = analysis.get('ai_summary', {})
    print(f"Overall AI Sentiment: {ai_summary.get('overall_sentiment', 'unknown').upper()}")
    
    # High confidence predictions
    high_conf = ai_summary.get('high_confidence_predictions', [])
    if high_conf:
        print(f"\nHigh Confidence ML Predictions:")
        for pred in high_conf:
            print(f"  {pred['symbol']}: {pred['trend']} ({pred['confidence']}% confidence)")
    
    # Pattern signals
    patterns = ai_summary.get('pattern_signals', [])
    if patterns:
        print(f"\nPattern Recognition Signals:")
        for pattern in patterns[:5]:  # Top 5
            print(f"  {pattern['symbol']}: {pattern['pattern']}")
    
    # Anomaly alerts
    anomalies = ai_summary.get('anomaly_alerts', [])
    if anomalies:
        print(f"\nAnomaly Detection Alerts:")
        for anomaly in anomalies:
            print(f"  {anomaly['symbol']}: {anomaly['level']} anomaly level ({anomaly['count']} recent)")
    
    # AI recommendations
    recommendations = ai_summary.get('ai_recommendations', [])
    if recommendations:
        print(f"\nAI Recommendations:")
        for rec in recommendations:
            print(f"  • {rec}")

if __name__ == "__main__":
    main()