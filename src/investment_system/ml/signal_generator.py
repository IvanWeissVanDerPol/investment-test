"""
Basic ML signal generation with technical indicators.
Foundation for more advanced ML models (to be optimized in Phase 3).
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from investment_system.cache import cached
from investment_system.utils.resilience import retry_with_backoff

logger = logging.getLogger(__name__)


@dataclass
class SignalConfig:
    """Configuration for signal generation"""
    
    # RSI parameters
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    
    # SMA parameters
    sma_fast: int = 20
    sma_slow: int = 50
    
    # EMA parameters
    ema_fast: int = 12
    ema_slow: int = 26
    
    # ATR parameters
    atr_period: int = 14
    
    # Risk parameters
    min_confidence: float = 0.6
    target_volatility: float = 0.12
    kelly_fraction: float = 0.25
    
    # ML model parameters (basic for now)
    use_ml_ensemble: bool = False  # Will be True in Phase 3
    model_version: str = "basic_v1"


class TechnicalIndicators:
    """Calculate technical indicators for signal generation"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index
        
        Args:
            prices: Price series
            period: RSI period
            
        Returns:
            RSI values
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period
            
        Returns:
            ATR values
        """
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, num_std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Returns:
            Tuple of (middle_band, upper_band, lower_band)
        """
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)
        
        return middle, upper, lower
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD
        
        Returns:
            Tuple of (macd, signal, histogram)
        """
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator
        
        Returns:
            Tuple of (%K, %D)
        """
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=3).mean()
        
        return k_percent, d_percent
    
    @staticmethod
    def calculate_volume_indicators(volume: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """Calculate volume-based indicators"""
        # On-Balance Volume (OBV)
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        
        # Volume Rate of Change
        vroc = ((volume - volume.shift(12)) / volume.shift(12)) * 100
        
        # Money Flow Index (simplified)
        typical_price = close  # Simplified, should use (high + low + close) / 3
        raw_money_flow = typical_price * volume
        
        return {
            "obv": obv,
            "vroc": vroc,
            "money_flow": raw_money_flow
        }


class BasicSignalGenerator:
    """
    Basic signal generator using technical indicators.
    This is the foundation that will be enhanced with ML in Phase 3.
    """
    
    def __init__(self, config: Optional[SignalConfig] = None):
        self.config = config or SignalConfig()
        self.indicators = TechnicalIndicators()
    
    @cached(ttl=60, key_prefix="signals")
    async def generate_signals(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals from OHLCV data.
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Symbol identifier
            timeframe: Data timeframe
            
        Returns:
            List of signal dictionaries
        """
        if df.empty or len(df) < max(self.config.sma_slow, self.config.rsi_period):
            logger.warning(f"Insufficient data for {symbol}")
            return []
        
        # Calculate all indicators
        features = self._calculate_features(df)
        
        # Generate signals based on indicators
        signals = self._generate_signal_logic(features, symbol, timeframe)
        
        # Calculate risk metrics
        signals = self._add_risk_metrics(signals, features)
        
        # Filter by confidence
        signals = [s for s in signals if s.get("confidence", 0) >= self.config.min_confidence]
        
        return signals
    
    def _calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical features"""
        features = df.copy()
        
        # Price-based indicators
        features["rsi"] = self.indicators.calculate_rsi(df["close"], self.config.rsi_period)
        features["sma_fast"] = self.indicators.calculate_sma(df["close"], self.config.sma_fast)
        features["sma_slow"] = self.indicators.calculate_sma(df["close"], self.config.sma_slow)
        features["ema_fast"] = self.indicators.calculate_ema(df["close"], self.config.ema_fast)
        features["ema_slow"] = self.indicators.calculate_ema(df["close"], self.config.ema_slow)
        
        # Volatility indicators
        features["atr"] = self.indicators.calculate_atr(df["high"], df["low"], df["close"], self.config.atr_period)
        
        # Bollinger Bands
        bb_middle, bb_upper, bb_lower = self.indicators.calculate_bollinger_bands(df["close"])
        features["bb_middle"] = bb_middle
        features["bb_upper"] = bb_upper
        features["bb_lower"] = bb_lower
        features["bb_width"] = bb_upper - bb_lower
        features["bb_position"] = (df["close"] - bb_lower) / (bb_upper - bb_lower)
        
        # MACD
        macd, macd_signal, macd_hist = self.indicators.calculate_macd(df["close"])
        features["macd"] = macd
        features["macd_signal"] = macd_signal
        features["macd_histogram"] = macd_hist
        
        # Stochastic
        stoch_k, stoch_d = self.indicators.calculate_stochastic(df["high"], df["low"], df["close"])
        features["stoch_k"] = stoch_k
        features["stoch_d"] = stoch_d
        
        # Volume indicators
        if "volume" in df.columns:
            volume_indicators = self.indicators.calculate_volume_indicators(df["volume"], df["close"])
            for key, value in volume_indicators.items():
                features[f"vol_{key}"] = value
        
        # Price changes
        features["returns_1"] = df["close"].pct_change(1)
        features["returns_5"] = df["close"].pct_change(5)
        features["returns_20"] = df["close"].pct_change(20)
        
        # Volatility
        features["volatility_20"] = features["returns_1"].rolling(20).std() * np.sqrt(252)
        
        return features
    
    def _generate_signal_logic(
        self,
        features: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """
        Generate signals based on technical indicators.
        This is the basic version - ML ensemble will be added in Phase 3.
        """
        signals = []
        
        # Get latest row for signal generation
        if len(features) < 2:
            return signals
        
        latest = features.iloc[-1]
        prev = features.iloc[-2]
        
        # Initialize signal
        signal = {
            "ts": datetime.utcnow().isoformat(),
            "symbolId": symbol,
            "tf": timeframe,
            "horizonBars": 16,  # Default prediction horizon
            "score": 0.0,
            "probUp": 0.5,
            "conf": 0.0,
            "expectedReturn": 0.0,
            "model": {
                "ensemble": "basic_technical",
                "members": ["rsi", "sma_crossover", "macd"],
                "version": self.config.model_version
            }
        }
        
        # Signal components (will be ensemble weights in Phase 3)
        signal_components = []
        
        # 1. RSI Signal
        if not pd.isna(latest["rsi"]):
            if latest["rsi"] < self.config.rsi_oversold:
                signal_components.append(("rsi_oversold", 0.7, "buy"))
            elif latest["rsi"] > self.config.rsi_overbought:
                signal_components.append(("rsi_overbought", 0.3, "sell"))
            else:
                rsi_neutral = 0.5 + (latest["rsi"] - 50) / 100
                signal_components.append(("rsi_neutral", rsi_neutral, "hold"))
        
        # 2. SMA Crossover Signal
        if not pd.isna(latest["sma_fast"]) and not pd.isna(latest["sma_slow"]):
            if latest["sma_fast"] > latest["sma_slow"] and prev["sma_fast"] <= prev["sma_slow"]:
                signal_components.append(("sma_golden_cross", 0.8, "buy"))
            elif latest["sma_fast"] < latest["sma_slow"] and prev["sma_fast"] >= prev["sma_slow"]:
                signal_components.append(("sma_death_cross", 0.2, "sell"))
            else:
                sma_trend = 0.5 + 0.3 * np.tanh((latest["sma_fast"] - latest["sma_slow"]) / latest["close"])
                signal_components.append(("sma_trend", sma_trend, "hold"))
        
        # 3. MACD Signal
        if not pd.isna(latest["macd_histogram"]):
            if latest["macd_histogram"] > 0 and prev["macd_histogram"] <= 0:
                signal_components.append(("macd_bullish", 0.75, "buy"))
            elif latest["macd_histogram"] < 0 and prev["macd_histogram"] >= 0:
                signal_components.append(("macd_bearish", 0.25, "sell"))
            else:
                macd_strength = 0.5 + 0.3 * np.tanh(latest["macd_histogram"])
                signal_components.append(("macd_momentum", macd_strength, "hold"))
        
        # 4. Bollinger Bands Signal
        if not pd.isna(latest["bb_position"]):
            if latest["bb_position"] < 0.2:
                signal_components.append(("bb_oversold", 0.65, "buy"))
            elif latest["bb_position"] > 0.8:
                signal_components.append(("bb_overbought", 0.35, "sell"))
        
        # 5. Stochastic Signal
        if not pd.isna(latest["stoch_k"]) and not pd.isna(latest["stoch_d"]):
            if latest["stoch_k"] < 20 and latest["stoch_k"] > latest["stoch_d"]:
                signal_components.append(("stoch_oversold", 0.7, "buy"))
            elif latest["stoch_k"] > 80 and latest["stoch_k"] < latest["stoch_d"]:
                signal_components.append(("stoch_overbought", 0.3, "sell"))
        
        # Aggregate signals (simple average for now, ML ensemble in Phase 3)
        if signal_components:
            probabilities = [comp[1] for comp in signal_components]
            signal["probUp"] = np.mean(probabilities)
            signal["conf"] = 1 - np.std(probabilities)  # Higher agreement = higher confidence
            signal["score"] = (signal["probUp"] - 0.5) * signal["conf"]
            
            # Determine direction
            if signal["probUp"] > 0.6:
                signal["direction"] = "buy"
            elif signal["probUp"] < 0.4:
                signal["direction"] = "sell"
            else:
                signal["direction"] = "hold"
            
            # Expected return (simplified - will use ML prediction in Phase 3)
            if not pd.isna(latest["volatility_20"]):
                signal["expectedReturn"] = (signal["probUp"] - 0.5) * latest["volatility_20"] / np.sqrt(252/16)
            
            signals.append(signal)
        
        return signals
    
    def _add_risk_metrics(
        self,
        signals: List[Dict[str, Any]],
        features: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Add risk and sizing metrics to signals"""
        
        latest = features.iloc[-1] if len(features) > 0 else None
        
        for signal in signals:
            # Risk metrics
            realized_vol = latest["volatility_20"] if latest is not None and not pd.isna(latest.get("volatility_20")) else 0.2
            
            signal["risk"] = {
                "targetVol": self.config.target_volatility,
                "realizedVol": float(realized_vol),
                "kellyFrac": self._calculate_kelly_fraction(signal["probUp"], signal["expectedReturn"])
            }
            
            # Sizing
            position_size = min(
                self.config.kelly_fraction * signal["risk"]["kellyFrac"],
                self.config.target_volatility / max(realized_vol, 0.01)
            )
            
            signal["sizing"] = {
                "navFrac": min(position_size, 0.1),  # Max 10% per position
                "maxAdvShare": 0.02  # Max 2% of average daily volume
            }
            
            # Add confidence based on indicator agreement
            signal["confidence"] = signal.get("conf", 0.5)
        
        return signals
    
    def _calculate_kelly_fraction(self, prob_up: float, expected_return: float) -> float:
        """
        Calculate Kelly fraction for position sizing.
        
        Args:
            prob_up: Probability of positive return
            expected_return: Expected return
            
        Returns:
            Kelly fraction (0-1)
        """
        if expected_return <= 0:
            return 0.0
        
        # Simplified Kelly: f = p - q/b
        # where p = prob_win, q = prob_loss, b = win/loss ratio
        prob_loss = 1 - prob_up
        
        # Assume symmetric wins/losses for simplicity (will be refined in Phase 3)
        win_loss_ratio = 1.0
        
        kelly = prob_up - (prob_loss / win_loss_ratio)
        
        # Apply safety factor and bounds
        return max(0, min(kelly * self.config.kelly_fraction, 0.25))
    
    async def score_symbol(
        self,
        symbol: str,
        timeframe: str,
        lookback_bars: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Score a single symbol for trading.
        
        Args:
            symbol: Symbol to score
            timeframe: Timeframe for analysis
            lookback_bars: Number of bars to analyze
            
        Returns:
            Signal dictionary or None
        """
        # This would fetch data and generate signal
        # Placeholder for integration with data pipeline
        logger.info(f"Scoring {symbol} on {timeframe} timeframe")
        
        # Mock signal for now
        return {
            "ts": datetime.utcnow().isoformat(),
            "symbolId": symbol,
            "tf": timeframe,
            "horizonBars": 16,
            "score": np.random.uniform(-0.1, 0.1),
            "probUp": np.random.uniform(0.4, 0.6),
            "conf": np.random.uniform(0.5, 0.9),
            "expectedReturn": np.random.uniform(-0.02, 0.02),
            "direction": np.random.choice(["buy", "sell", "hold"]),
            "risk": {
                "targetVol": 0.12,
                "realizedVol": 0.18,
                "kellyFrac": 0.15
            },
            "sizing": {
                "navFrac": 0.02,
                "maxAdvShare": 0.01
            },
            "model": {
                "ensemble": "basic_technical",
                "members": ["rsi", "sma", "macd"],
                "version": "basic_v1"
            }
        }


# TODO: Phase 3 - ML Enhancement
class MLSignalGenerator(BasicSignalGenerator):
    """
    Advanced ML signal generator (to be implemented in Phase 3).
    Will include:
    - LightGBM/XGBoost for tabular predictions
    - Temporal Fusion Transformer (TFT) for time-series
    - Thompson Sampling bandit for ensemble
    - Conformal prediction for confidence intervals
    - Online learning and drift detection
    """
    
    def __init__(self, config: Optional[SignalConfig] = None):
        super().__init__(config)
        # TODO: Initialize ML models
        logger.info("ML Signal Generator initialized (Phase 3 placeholder)")
    
    async def train_models(self, training_data: pd.DataFrame):
        """Train ML models (Phase 3)"""
        logger.info("Model training will be implemented in Phase 3")
        pass
    
    async def generate_ml_signals(self, features: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate signals using ML ensemble (Phase 3)"""
        logger.info("ML signal generation will be implemented in Phase 3")
        # For now, fallback to basic signals
        return await self.generate_signals(features, "UNKNOWN", "1h")