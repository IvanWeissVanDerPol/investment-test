"""
Modular analyzer system with AI hooks.
Each analyzer is independent and can be enhanced by AI without breaking others.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
import numpy as np
import pandas as pd
from decimal import Decimal

from investment_system.core.contracts import (
    MarketData, TradingSignal, SignalType, IndicatorType,
    AIHookRequest, AIHookResponse
)


class AnalyzerHooks:
    """Registry for AI hooks in analyzers"""
    
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {}
    
    def register(self, hook_name: str, handler: Callable):
        """Register an AI hook handler"""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(handler)
    
    def execute(self, hook_name: str, data: Any) -> Any:
        """Execute all handlers for a hook"""
        if hook_name not in self._hooks:
            return data
            
        result = data
        for handler in self._hooks[hook_name]:
            try:
                hook_request = AIHookRequest(
                    hook_id=hook_name,
                    data={"input": result}
                )
                hook_response = handler(hook_request)
                if hook_response.modifications_made:
                    result = hook_response.processed_data.get("output", result)
            except Exception as e:
                # Log error but don't break the flow
                print(f"Hook {hook_name} failed: {e}")
                continue
        
        return result


class BaseAnalyzer(ABC):
    """Abstract base analyzer that all analyzers must extend"""
    
    def __init__(self):
        self.hooks = AnalyzerHooks()
        self._register_default_hooks()
    
    def _register_default_hooks(self):
        """Register default AI hooks"""
        # These are placeholders - actual AI handlers are registered at runtime
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[IndicatorType, float]:
        """Calculate technical indicators from price data"""
        pass
    
    @abstractmethod
    def generate_signal(self, indicators: Dict[IndicatorType, float]) -> SignalType:
        """Generate trading signal from indicators"""
        pass
    
    @abstractmethod
    def calculate_confidence(self, indicators: Dict[IndicatorType, float], signal: SignalType) -> float:
        """Calculate confidence score for the signal"""
        pass
    
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """Main analysis pipeline with AI hooks"""
        
        # Convert to DataFrame for analysis
        df = self._market_data_to_df(market_data)
        
        # Hook: pre_analysis - AI can modify input data
        df = self.hooks.execute("pre_analysis", df)
        
        # Calculate indicators
        indicators = self.calculate_indicators(df)
        
        # Hook: post_indicators - AI can modify indicators
        indicators = self.hooks.execute("post_indicators", indicators)
        
        # Generate signal
        signal = self.generate_signal(indicators)
        
        # Hook: signal_override - AI can override signal
        signal = self.hooks.execute("signal_override", signal)
        
        # Calculate confidence
        confidence = self.calculate_confidence(indicators, signal)
        
        # Hook: confidence_adjustment - AI can adjust confidence
        confidence = self.hooks.execute("confidence_adjustment", confidence)
        
        # Create trading signal
        trading_signal = TradingSignal(
            symbol=market_data.symbol,
            signal=signal,
            confidence=confidence,
            price=Decimal(str(df['close'].iloc[-1])),
            indicators=indicators,
            ai_enhanced=self._has_ai_hooks()
        )
        
        # Hook: post_analysis - AI can modify final signal
        trading_signal = self.hooks.execute("post_analysis", trading_signal)
        
        return trading_signal
    
    def _market_data_to_df(self, market_data: MarketData) -> pd.DataFrame:
        """Convert MarketData to DataFrame"""
        data = []
        for price in market_data.prices:
            data.append({
                'timestamp': price.timestamp,
                'open': float(price.open),
                'high': float(price.high),
                'low': float(price.low),
                'close': float(price.close),
                'volume': price.volume
            })
        return pd.DataFrame(data)
    
    def _has_ai_hooks(self) -> bool:
        """Check if any AI hooks are registered"""
        return len(self.hooks._hooks) > 0


class TechnicalAnalyzer(BaseAnalyzer):
    """Technical analysis using standard indicators"""
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[IndicatorType, float]:
        """Calculate technical indicators"""
        indicators = {}
        
        # RSI
        indicators[IndicatorType.RSI] = self._calculate_rsi(data['close'])
        
        # Simple Moving Averages
        indicators[IndicatorType.SMA_20] = data['close'].rolling(window=20).mean().iloc[-1]
        indicators[IndicatorType.SMA_50] = data['close'].rolling(window=50).mean().iloc[-1]
        
        # Volume indicator
        indicators[IndicatorType.VOLUME] = data['volume'].iloc[-1]
        
        # Round all values
        indicators = {k: round(v, 2) for k, v in indicators.items()}
        
        return indicators
    
    def generate_signal(self, indicators: Dict[IndicatorType, float]) -> SignalType:
        """Generate signal based on indicators"""
        rsi = indicators.get(IndicatorType.RSI, 50)
        sma_20 = indicators.get(IndicatorType.SMA_20, 0)
        sma_50 = indicators.get(IndicatorType.SMA_50, 0)
        
        # Golden cross / Death cross
        if sma_20 > sma_50:
            if rsi < 30:  # Oversold in uptrend
                return SignalType.BUY
            elif rsi > 70:  # Overbought in uptrend
                return SignalType.SELL
            else:
                return SignalType.BUY  # Uptrend
        else:
            if rsi < 30:  # Oversold in downtrend
                return SignalType.HOLD
            elif rsi > 70:  # Overbought in downtrend
                return SignalType.SELL
            else:
                return SignalType.SELL  # Downtrend
    
    def calculate_confidence(self, indicators: Dict[IndicatorType, float], signal: SignalType) -> float:
        """Calculate confidence based on indicator alignment"""
        confidence = 0.5  # Base confidence
        
        rsi = indicators.get(IndicatorType.RSI, 50)
        sma_20 = indicators.get(IndicatorType.SMA_20, 0)
        sma_50 = indicators.get(IndicatorType.SMA_50, 0)
        
        # RSI contribution
        if signal == SignalType.BUY and rsi < 30:
            confidence += 0.2
        elif signal == SignalType.SELL and rsi > 70:
            confidence += 0.2
        
        # SMA contribution
        sma_diff_pct = abs(sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0
        if sma_diff_pct > 0.02:  # 2% difference
            confidence += min(0.3, sma_diff_pct * 10)
        
        return min(0.95, confidence)  # Cap at 95%
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0


class MomentumAnalyzer(BaseAnalyzer):
    """Momentum-based analysis"""
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[IndicatorType, float]:
        """Calculate momentum indicators"""
        indicators = {}
        
        # Price momentum
        momentum_5 = (data['close'].iloc[-1] - data['close'].iloc[-5]) / data['close'].iloc[-5]
        momentum_10 = (data['close'].iloc[-1] - data['close'].iloc[-10]) / data['close'].iloc[-10]
        
        # Volume momentum
        vol_avg_5 = data['volume'].tail(5).mean()
        vol_avg_20 = data['volume'].tail(20).mean()
        vol_momentum = vol_avg_5 / vol_avg_20 if vol_avg_20 > 0 else 1
        
        # Use RSI as a momentum indicator
        indicators[IndicatorType.RSI] = self._calculate_momentum_rsi(data['close'])
        indicators[IndicatorType.VOLUME] = vol_momentum
        
        # Store momentum as SMA values (hacky but works with existing contracts)
        indicators[IndicatorType.SMA_20] = momentum_5 * 100
        indicators[IndicatorType.SMA_50] = momentum_10 * 100
        
        return {k: round(v, 2) for k, v in indicators.items()}
    
    def generate_signal(self, indicators: Dict[IndicatorType, float]) -> SignalType:
        """Generate signal based on momentum"""
        momentum_5 = indicators.get(IndicatorType.SMA_20, 0) / 100
        momentum_10 = indicators.get(IndicatorType.SMA_50, 0) / 100
        vol_momentum = indicators.get(IndicatorType.VOLUME, 1)
        
        # Strong upward momentum
        if momentum_5 > 0.03 and momentum_10 > 0.05 and vol_momentum > 1.2:
            return SignalType.BUY
        # Strong downward momentum
        elif momentum_5 < -0.03 and momentum_10 < -0.05:
            return SignalType.SELL
        # Mixed or weak momentum
        else:
            return SignalType.HOLD
    
    def calculate_confidence(self, indicators: Dict[IndicatorType, float], signal: SignalType) -> float:
        """Calculate confidence based on momentum strength"""
        momentum_5 = abs(indicators.get(IndicatorType.SMA_20, 0) / 100)
        momentum_10 = abs(indicators.get(IndicatorType.SMA_50, 0) / 100)
        vol_momentum = indicators.get(IndicatorType.VOLUME, 1)
        
        # Base confidence on momentum strength
        confidence = 0.4
        confidence += min(0.3, momentum_5 * 5)  # Up to 0.3 from 5-day momentum
        confidence += min(0.2, momentum_10 * 3)  # Up to 0.2 from 10-day momentum
        
        # Volume confirmation
        if vol_momentum > 1.5:
            confidence += 0.1
        
        return min(0.95, confidence)
    
    def _calculate_momentum_rsi(self, prices: pd.Series) -> float:
        """Calculate momentum-adjusted RSI"""
        # Standard RSI with shorter period for momentum
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0


class AIEnhancedAnalyzer(BaseAnalyzer):
    """Analyzer that primarily relies on AI hooks"""
    
    def __init__(self, fallback_analyzer: Optional[BaseAnalyzer] = None):
        super().__init__()
        self.fallback = fallback_analyzer or TechnicalAnalyzer()
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[IndicatorType, float]:
        """Minimal indicators - let AI enhance"""
        # Calculate basic indicators as input for AI
        indicators = {
            IndicatorType.RSI: 50.0,
            IndicatorType.SMA_20: data['close'].tail(20).mean(),
            IndicatorType.SMA_50: data['close'].tail(50).mean(),
            IndicatorType.VOLUME: data['volume'].iloc[-1]
        }
        return {k: round(v, 2) for k, v in indicators.items()}
    
    def generate_signal(self, indicators: Dict[IndicatorType, float]) -> SignalType:
        """Simple signal - AI will override"""
        # Basic logic as fallback
        if indicators[IndicatorType.RSI] < 30:
            return SignalType.BUY
        elif indicators[IndicatorType.RSI] > 70:
            return SignalType.SELL
        else:
            return SignalType.HOLD
    
    def calculate_confidence(self, indicators: Dict[IndicatorType, float], signal: SignalType) -> float:
        """Low confidence - AI will adjust"""
        return 0.5  # Neutral confidence, expecting AI enhancement


# Analyzer Factory
class AnalyzerFactory:
    """Factory for creating analyzers"""
    
    _analyzers = {
        "technical": TechnicalAnalyzer,
        "momentum": MomentumAnalyzer,
        "ai_enhanced": AIEnhancedAnalyzer
    }
    
    @classmethod
    def create(cls, analyzer_type: str = "technical") -> BaseAnalyzer:
        """Create an analyzer instance"""
        analyzer_class = cls._analyzers.get(analyzer_type, TechnicalAnalyzer)
        return analyzer_class()
    
    @classmethod
    def register(cls, name: str, analyzer_class: type):
        """Register a new analyzer type"""
        if not issubclass(analyzer_class, BaseAnalyzer):
            raise ValueError(f"{analyzer_class} must extend BaseAnalyzer")
        cls._analyzers[name] = analyzer_class
    
    @classmethod
    def list_available(cls) -> List[str]:
        """List available analyzer types"""
        return list(cls._analyzers.keys())