"""
Enhanced Market Analysis Engine
Advanced technical analysis, sentiment processing, and market intelligence
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import talib
import logging

from ..data.market_data_collector import MarketDataCollector
from ..utils.cache_manager import CacheManager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

logger = logging.getLogger(__name__)


@dataclass
class TechnicalSignals:
    """Technical analysis signals"""
    rsi: float
    macd_signal: str  # 'bullish', 'bearish', 'neutral'
    bollinger_position: str  # 'oversold', 'overbought', 'neutral'
    moving_average_trend: str  # 'uptrend', 'downtrend', 'sideways'
    volume_trend: str  # 'increasing', 'decreasing', 'stable'
    support_resistance: Dict[str, float]
    momentum_score: float  # -100 to 100
    volatility_percentile: float  # 0 to 100


@dataclass
class SentimentAnalysis:
    """Sentiment analysis results"""
    news_sentiment: float  # -1 to 1
    social_sentiment: float  # -1 to 1
    analyst_sentiment: float  # -1 to 1
    combined_sentiment: float  # -1 to 1
    sentiment_trend: str  # 'improving', 'declining', 'stable'
    confidence: float  # 0 to 1


@dataclass
class MarketIntelligence:
    """Comprehensive market intelligence"""
    symbol: str
    timestamp: datetime
    price: float
    technical_signals: TechnicalSignals
    sentiment_analysis: SentimentAnalysis
    risk_metrics: Dict[str, float]
    prediction_confidence: float
    recommendation: str  # 'strong_buy', 'buy', 'hold', 'sell', 'strong_sell'
    target_price: float
    stop_loss: float
    time_horizon: str  # 'short', 'medium', 'long'


class EnhancedMarketAnalyzer:
    """
    Advanced market analysis engine combining technical analysis,
    sentiment analysis, and machine learning predictions
    """
    
    def __init__(self):
        """Initialize the enhanced market analyzer"""
        self.data_collector = MarketDataCollector()
        self.cache_manager = CacheManager()
        self.audit_logger = get_audit_logger()
        
        # Technical analysis parameters
        self.ta_params = {
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_std': 2,
            'sma_short': 20,
            'sma_long': 50,
            'volume_sma': 20
        }
        
        # Machine learning models
        self.price_predictor = None
        self.volatility_predictor = None
        self.sentiment_predictor = None
        self._initialize_models()
        
        # Risk thresholds
        self.risk_thresholds = {
            'max_volatility': 0.05,  # 5% daily volatility
            'max_drawdown': 0.15,    # 15% maximum drawdown
            'min_liquidity': 1000000,  # $1M average daily volume
            'correlation_limit': 0.8   # Maximum correlation with market
        }
    
    def _initialize_models(self):
        """Initialize machine learning models"""
        try:
            # Price prediction model (Random Forest)
            self.price_predictor = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            # Volatility prediction model (Gradient Boosting)
            self.volatility_predictor = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            logger.info("Machine learning models initialized")
            
        except Exception as e:
            logger.error(f"Model initialization error: {e}")
    
    def analyze_symbol(self, symbol: str, period: str = "1y") -> MarketIntelligence:
        """
        Comprehensive analysis of a single symbol
        """
        try:
            # Get market data
            market_data = self._get_market_data(symbol, period)
            if market_data is None or market_data.empty:
                raise ValueError(f"No market data available for {symbol}")
            
            # Technical analysis
            technical_signals = self._analyze_technical_indicators(market_data)
            
            # Sentiment analysis
            sentiment_analysis = self._analyze_sentiment(symbol)
            
            # Risk metrics
            risk_metrics = self._calculate_risk_metrics(market_data)
            
            # ML predictions
            price_prediction, confidence = self._predict_price_movement(market_data)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                technical_signals, sentiment_analysis, risk_metrics, confidence
            )
            
            # Calculate targets
            current_price = market_data['Close'].iloc[-1]
            target_price, stop_loss = self._calculate_price_targets(
                current_price, technical_signals, risk_metrics
            )
            
            # Create comprehensive intelligence report
            intelligence = MarketIntelligence(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                price=current_price,
                technical_signals=technical_signals,
                sentiment_analysis=sentiment_analysis,
                risk_metrics=risk_metrics,
                prediction_confidence=confidence,
                recommendation=recommendation,
                target_price=target_price,
                stop_loss=stop_loss,
                time_horizon=self._determine_time_horizon(technical_signals, sentiment_analysis)
            )
            
            # Cache results
            self._cache_analysis(symbol, intelligence)
            
            # Audit log
            self.audit_logger.log_event(
                EventType.ANALYSIS_COMPLETED,
                SeverityLevel.LOW,
                resource='enhanced_market_analyzer',
                details={
                    'symbol': symbol,
                    'recommendation': recommendation,
                    'confidence': confidence,
                    'analysis_type': 'comprehensive'
                }
            )
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Analysis error for {symbol}: {e}")
            self.audit_logger.log_event(
                EventType.ERROR_OCCURRED,
                SeverityLevel.HIGH,
                resource='enhanced_market_analyzer',
                error_message=str(e),
                details={'symbol': symbol}
            )
            raise
    
    def _get_market_data(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """Get comprehensive market data"""
        try:
            # Check cache first
            cache_key = f"market_data_{symbol}_{period}"
            cached_data = self.cache_manager.get(cache_key)
            
            if cached_data is not None:
                return cached_data
            
            # Fetch from data collector
            data = self.data_collector.get_historical_data(symbol, period)
            
            if data is not None and not data.empty:
                # Cache for 15 minutes
                self.cache_manager.set(cache_key, data, ttl=900)
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Market data retrieval error for {symbol}: {e}")
            return None
    
    def _analyze_technical_indicators(self, data: pd.DataFrame) -> TechnicalSignals:
        """Comprehensive technical analysis"""
        try:
            # Price data
            high = data['High'].values
            low = data['Low'].values
            close = data['Close'].values
            volume = data['Volume'].values
            
            # RSI
            rsi = talib.RSI(close, timeperiod=self.ta_params['rsi_period'])[-1]
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(
                close,
                fastperiod=self.ta_params['macd_fast'],
                slowperiod=self.ta_params['macd_slow'],
                signalperiod=self.ta_params['macd_signal']
            )
            
            # MACD signal
            if macd[-1] > macd_signal[-1] and macd[-2] <= macd_signal[-2]:
                macd_signal_str = 'bullish'
            elif macd[-1] < macd_signal[-1] and macd[-2] >= macd_signal[-2]:
                macd_signal_str = 'bearish'
            else:
                macd_signal_str = 'neutral'
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(
                close,
                timeperiod=self.ta_params['bb_period'],
                nbdevup=self.ta_params['bb_std'],
                nbdevdn=self.ta_params['bb_std']
            )
            
            # Bollinger position
            current_price = close[-1]
            if current_price <= bb_lower[-1]:
                bb_position = 'oversold'
            elif current_price >= bb_upper[-1]:
                bb_position = 'overbought'
            else:
                bb_position = 'neutral'
            
            # Moving averages
            sma_short = talib.SMA(close, timeperiod=self.ta_params['sma_short'])
            sma_long = talib.SMA(close, timeperiod=self.ta_params['sma_long'])
            
            if sma_short[-1] > sma_long[-1] and sma_short[-5] > sma_short[-1]:
                ma_trend = 'uptrend'
            elif sma_short[-1] < sma_long[-1] and sma_short[-5] < sma_short[-1]:
                ma_trend = 'downtrend'
            else:
                ma_trend = 'sideways'
            
            # Volume analysis
            volume_sma = talib.SMA(volume.astype(float), timeperiod=self.ta_params['volume_sma'])
            current_volume = volume[-1]
            avg_volume = volume_sma[-1]
            
            if current_volume > avg_volume * 1.5:
                volume_trend = 'increasing'
            elif current_volume < avg_volume * 0.5:
                volume_trend = 'decreasing'
            else:
                volume_trend = 'stable'
            
            # Support and resistance
            support_resistance = self._calculate_support_resistance(high, low, close)
            
            # Momentum score
            momentum_score = self._calculate_momentum_score(close, rsi, macd_hist[-1])
            
            # Volatility percentile
            volatility = self._calculate_volatility_percentile(close)
            
            return TechnicalSignals(
                rsi=rsi,
                macd_signal=macd_signal_str,
                bollinger_position=bb_position,
                moving_average_trend=ma_trend,
                volume_trend=volume_trend,
                support_resistance=support_resistance,
                momentum_score=momentum_score,
                volatility_percentile=volatility
            )
            
        except Exception as e:
            logger.error(f"Technical analysis error: {e}")
            # Return neutral signals on error
            return TechnicalSignals(
                rsi=50,
                macd_signal='neutral',
                bollinger_position='neutral',
                moving_average_trend='sideways',
                volume_trend='stable',
                support_resistance={'support': 0, 'resistance': 0},
                momentum_score=0,
                volatility_percentile=50
            )
    
    def _analyze_sentiment(self, symbol: str) -> SentimentAnalysis:
        """Multi-source sentiment analysis"""
        try:
            # Get news sentiment (from news analyzer)
            news_sentiment = self._get_news_sentiment(symbol)
            
            # Get social sentiment (from social analyzer)
            social_sentiment = self._get_social_sentiment(symbol)
            
            # Get analyst sentiment (from analyst ratings)
            analyst_sentiment = self._get_analyst_sentiment(symbol)
            
            # Combined sentiment (weighted average)
            weights = {'news': 0.4, 'social': 0.3, 'analyst': 0.3}
            combined_sentiment = (
                news_sentiment * weights['news'] +
                social_sentiment * weights['social'] +
                analyst_sentiment * weights['analyst']
            )
            
            # Sentiment trend (compare with historical)
            sentiment_trend = self._calculate_sentiment_trend(symbol, combined_sentiment)
            
            # Confidence based on agreement between sources
            sentiment_values = [news_sentiment, social_sentiment, analyst_sentiment]
            confidence = 1 - (np.std(sentiment_values) / 2)  # Lower std = higher confidence
            
            return SentimentAnalysis(
                news_sentiment=news_sentiment,
                social_sentiment=social_sentiment,
                analyst_sentiment=analyst_sentiment,
                combined_sentiment=combined_sentiment,
                sentiment_trend=sentiment_trend,
                confidence=max(0.1, min(1.0, confidence))
            )
            
        except Exception as e:
            logger.error(f"Sentiment analysis error for {symbol}: {e}")
            return SentimentAnalysis(
                news_sentiment=0,
                social_sentiment=0,
                analyst_sentiment=0,
                combined_sentiment=0,
                sentiment_trend='stable',
                confidence=0.5
            )
    
    def _calculate_risk_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate comprehensive risk metrics"""
        try:
            returns = data['Close'].pct_change().dropna()
            
            # Volatility (annualized)
            volatility = returns.std() * np.sqrt(252)
            
            # Value at Risk (95% confidence)
            var_95 = np.percentile(returns, 5)
            
            # Maximum drawdown
            rolling_max = data['Close'].expanding().max()
            drawdown = (data['Close'] - rolling_max) / rolling_max
            max_drawdown = abs(drawdown.min())
            
            # Sharpe ratio (assuming 2% risk-free rate)
            risk_free_rate = 0.02 / 252  # Daily risk-free rate
            excess_returns = returns.mean() - risk_free_rate
            sharpe_ratio = excess_returns / returns.std() if returns.std() > 0 else 0
            
            # Beta (vs SPY - would need market data)
            beta = 1.0  # Default, would calculate vs market index
            
            # Liquidity score (based on volume)
            avg_volume = data['Volume'].mean()
            avg_price = data['Close'].mean()
            liquidity_score = avg_volume * avg_price  # Dollar volume
            
            return {
                'volatility': volatility,
                'var_95': var_95,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'beta': beta,
                'liquidity_score': liquidity_score
            }
            
        except Exception as e:
            logger.error(f"Risk metrics calculation error: {e}")
            return {
                'volatility': 0.25,
                'var_95': -0.05,
                'max_drawdown': 0.20,
                'sharpe_ratio': 0.0,
                'beta': 1.0,
                'liquidity_score': 1000000
            }
    
    def _predict_price_movement(self, data: pd.DataFrame) -> Tuple[float, float]:
        """ML-based price movement prediction"""
        try:
            if self.price_predictor is None:
                return 0.0, 0.5
            
            # Prepare features
            features = self._prepare_features(data)
            
            if len(features) < 30:  # Need minimum data for prediction
                return 0.0, 0.5
            
            # Split features and target
            X = features[:-5]  # All but last 5 days for training
            y = data['Close'].pct_change().shift(-1).dropna()[:-5]  # Next day returns
            
            if len(X) != len(y):
                X = X[:len(y)]
            
            # Train model (in production, this would be pre-trained)
            if len(X) > 50:  # Minimum training samples
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                self.price_predictor.fit(X_train, y_train)
                
                # Predict next period
                last_features = features[-1:] if len(features) > 0 else X_test[-1:] 
                prediction = self.price_predictor.predict(last_features)[0]
                
                # Calculate confidence based on model performance
                if len(X_test) > 0:
                    test_predictions = self.price_predictor.predict(X_test)
                    accuracy = 1 - np.mean(np.abs(test_predictions - y_test))
                    confidence = max(0.1, min(0.95, accuracy))
                else:
                    confidence = 0.5
                
                return prediction, confidence
            
            return 0.0, 0.5
            
        except Exception as e:
            logger.error(f"Price prediction error: {e}")
            return 0.0, 0.5
    
    def _prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ML models"""
        try:
            features = pd.DataFrame()
            
            # Price features
            features['returns'] = data['Close'].pct_change()
            features['log_returns'] = np.log(data['Close'] / data['Close'].shift(1))
            features['high_low_ratio'] = data['High'] / data['Low']
            features['close_open_ratio'] = data['Close'] / data['Open']
            
            # Technical indicators as features
            features['rsi'] = talib.RSI(data['Close'].values, timeperiod=14)
            macd, macd_signal, macd_hist = talib.MACD(data['Close'].values)
            features['macd'] = macd
            features['macd_signal'] = macd_signal
            features['macd_histogram'] = macd_hist
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(data['Close'].values)
            features['bb_position'] = (data['Close'] - bb_lower) / (bb_upper - bb_lower)
            
            # Volume features
            features['volume_ratio'] = data['Volume'] / data['Volume'].rolling(20).mean()
            features['price_volume'] = data['Close'] * data['Volume']
            
            # Lag features
            for lag in [1, 2, 3, 5]:
                features[f'return_lag_{lag}'] = features['returns'].shift(lag)
            
            # Rolling statistics
            features['volatility_20'] = features['returns'].rolling(20).std()
            features['return_mean_5'] = features['returns'].rolling(5).mean()
            features['return_mean_20'] = features['returns'].rolling(20).mean()
            
            # Drop NaN values
            features = features.dropna()
            
            return features
            
        except Exception as e:
            logger.error(f"Feature preparation error: {e}")
            return pd.DataFrame()
    
    def _generate_recommendation(self, technical: TechnicalSignals, sentiment: SentimentAnalysis,
                                risk: Dict[str, float], confidence: float) -> str:
        """Generate investment recommendation"""
        try:
            # Scoring system
            score = 0
            
            # Technical analysis score
            if technical.rsi < 30:  # Oversold
                score += 2
            elif technical.rsi > 70:  # Overbought
                score -= 2
            
            if technical.macd_signal == 'bullish':
                score += 1
            elif technical.macd_signal == 'bearish':
                score -= 1
            
            if technical.bollinger_position == 'oversold':
                score += 1
            elif technical.bollinger_position == 'overbought':
                score -= 1
            
            if technical.moving_average_trend == 'uptrend':
                score += 1
            elif technical.moving_average_trend == 'downtrend':
                score -= 1
            
            # Momentum score
            score += technical.momentum_score / 50  # Normalize to -2 to 2
            
            # Sentiment score
            score += sentiment.combined_sentiment * 3  # -3 to 3
            
            # Risk adjustment
            if risk['volatility'] > self.risk_thresholds['max_volatility']:
                score -= 1
            if risk['max_drawdown'] > self.risk_thresholds['max_drawdown']:
                score -= 1
            if risk['sharpe_ratio'] > 1:
                score += 1
            elif risk['sharpe_ratio'] < 0:
                score -= 1
            
            # Confidence adjustment
            score *= confidence
            
            # Map score to recommendation
            if score >= 3:
                return 'strong_buy'
            elif score >= 1:
                return 'buy'
            elif score <= -3:
                return 'strong_sell'
            elif score <= -1:
                return 'sell'
            else:
                return 'hold'
            
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return 'hold'
    
    def _calculate_price_targets(self, current_price: float, technical: TechnicalSignals,
                                risk: Dict[str, float]) -> Tuple[float, float]:
        """Calculate target price and stop loss"""
        try:
            # Support and resistance levels
            resistance = technical.support_resistance.get('resistance', current_price * 1.1)
            support = technical.support_resistance.get('support', current_price * 0.9)
            
            # Target price based on resistance and volatility
            volatility_factor = min(0.2, risk.get('volatility', 0.2))  # Cap at 20%
            target_price = min(resistance, current_price * (1 + volatility_factor))
            
            # Stop loss based on support and risk tolerance
            risk_tolerance = 0.08  # 8% maximum loss
            stop_loss = max(support, current_price * (1 - risk_tolerance))
            
            return target_price, stop_loss
            
        except Exception as e:
            logger.error(f"Price target calculation error: {e}")
            return current_price * 1.05, current_price * 0.95
    
    def _determine_time_horizon(self, technical: TechnicalSignals, sentiment: SentimentAnalysis) -> str:
        """Determine recommended time horizon"""
        try:
            # Short-term indicators
            if (technical.rsi < 30 or technical.rsi > 70 or 
                technical.bollinger_position in ['oversold', 'overbought']):
                return 'short'  # Days to weeks
            
            # Medium-term indicators
            if (technical.moving_average_trend != 'sideways' or 
                abs(sentiment.combined_sentiment) > 0.3):
                return 'medium'  # Weeks to months
            
            # Default to long-term
            return 'long'  # Months to years
            
        except Exception:
            return 'medium'
    
    def _calculate_support_resistance(self, high: np.ndarray, low: np.ndarray, 
                                    close: np.ndarray) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        try:
            # Simple pivot point calculation
            recent_high = np.max(high[-20:])  # 20-day high
            recent_low = np.min(low[-20:])    # 20-day low
            recent_close = close[-1]
            
            # Pivot point
            pivot = (recent_high + recent_low + recent_close) / 3
            
            # Support and resistance
            resistance = recent_high
            support = recent_low
            
            return {
                'support': support,
                'resistance': resistance,
                'pivot': pivot
            }
            
        except Exception as e:
            logger.error(f"Support/resistance calculation error: {e}")
            current_price = close[-1] if len(close) > 0 else 100
            return {
                'support': current_price * 0.95,
                'resistance': current_price * 1.05,
                'pivot': current_price
            }
    
    def _calculate_momentum_score(self, close: np.ndarray, rsi: float, macd_hist: float) -> float:
        """Calculate momentum score (-100 to 100)"""
        try:
            # Price momentum (last 10 days)
            if len(close) >= 10:
                price_momentum = (close[-1] - close[-10]) / close[-10] * 100
            else:
                price_momentum = 0
            
            # RSI momentum
            rsi_momentum = (rsi - 50) * 2  # Scale to -100 to 100
            
            # MACD momentum
            macd_momentum = macd_hist * 1000  # Scale appropriately
            
            # Combined momentum
            momentum = (price_momentum + rsi_momentum + macd_momentum) / 3
            
            return max(-100, min(100, momentum))
            
        except Exception:
            return 0
    
    def _calculate_volatility_percentile(self, close: np.ndarray) -> float:
        """Calculate volatility percentile (0 to 100)"""
        try:
            if len(close) < 20:
                return 50
            
            # Calculate returns
            returns = np.diff(close) / close[:-1]
            
            # Current volatility (last 20 days)
            current_vol = np.std(returns[-20:]) if len(returns) >= 20 else np.std(returns)
            
            # Historical volatility distribution (rolling 20-day)
            vol_series = []
            for i in range(20, len(returns)):
                vol_series.append(np.std(returns[i-20:i]))
            
            if not vol_series:
                return 50
            
            # Percentile rank
            percentile = stats.percentileofscore(vol_series, current_vol)
            
            return percentile
            
        except Exception:
            return 50
    
    def _get_news_sentiment(self, symbol: str) -> float:
        """Get news sentiment from news analyzer"""
        # This would integrate with your news sentiment analyzer
        return 0.0  # Placeholder
    
    def _get_social_sentiment(self, symbol: str) -> float:
        """Get social sentiment from social analyzer"""
        # This would integrate with your social sentiment analyzer
        return 0.0  # Placeholder
    
    def _get_analyst_sentiment(self, symbol: str) -> float:
        """Get analyst sentiment from ratings data"""
        # This would integrate with analyst ratings data
        return 0.0  # Placeholder
    
    def _calculate_sentiment_trend(self, symbol: str, current_sentiment: float) -> str:
        """Calculate sentiment trend"""
        # This would compare with historical sentiment data
        return 'stable'  # Placeholder
    
    def _cache_analysis(self, symbol: str, intelligence: MarketIntelligence):
        """Cache analysis results"""
        try:
            cache_key = f"market_intelligence_{symbol}"
            # Convert to dict for caching
            data = {
                'symbol': intelligence.symbol,
                'timestamp': intelligence.timestamp.isoformat(),
                'price': intelligence.price,
                'recommendation': intelligence.recommendation,
                'target_price': intelligence.target_price,
                'stop_loss': intelligence.stop_loss,
                'confidence': intelligence.prediction_confidence
            }
            
            # Cache for 30 minutes
            self.cache_manager.set(cache_key, data, ttl=1800)
            
        except Exception as e:
            logger.error(f"Cache error: {e}")


if __name__ == "__main__":
    # Test the enhanced market analyzer
    analyzer = EnhancedMarketAnalyzer()
    
    try:
        # Test with NVDA
        intelligence = analyzer.analyze_symbol("NVDA")
        print(f"Analysis for NVDA:")
        print(f"Recommendation: {intelligence.recommendation}")
        print(f"Current Price: ${intelligence.price:.2f}")
        print(f"Target Price: ${intelligence.target_price:.2f}")
        print(f"Stop Loss: ${intelligence.stop_loss:.2f}")
        print(f"Confidence: {intelligence.prediction_confidence:.2%}")
        print(f"Time Horizon: {intelligence.time_horizon}")
        
    except Exception as e:
        print(f"Test failed: {e}")