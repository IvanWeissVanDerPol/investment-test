"""
Kelly Criterion Position Sizing Optimizer
Advanced position sizing using Kelly Criterion for optimal compound growth
Inspired by money-machine project's sophisticated risk management
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from scipy.optimize import minimize_scalar, minimize
import math

from ..data.market_data_collector import MarketDataCollector
from ..ai.ml_prediction_engine import get_ml_engine
from ..utils.cache_manager import CacheManager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

logger = logging.getLogger(__name__)


@dataclass
class KellyAnalysis:
    """Kelly Criterion analysis result"""
    symbol: str
    optimal_fraction: float  # Optimal position size (0-1)
    win_probability: float
    average_win: float
    average_loss: float
    expected_value: float
    kelly_fraction: float  # Raw Kelly calculation
    adjusted_fraction: float  # Risk-adjusted Kelly
    confidence_interval: Tuple[float, float]
    recommendation: str  # 'buy', 'sell', 'hold', 'avoid'
    risk_category: str  # 'low', 'medium', 'high', 'extreme'


@dataclass
class PositionSizeResult:
    """Position sizing recommendation"""
    symbol: str
    recommended_size: float  # Dollar amount
    percentage_of_portfolio: float
    risk_adjusted_size: float
    max_loss_potential: float
    expected_return: float
    sharpe_ratio: float
    kelly_fraction: float


class KellyCriterionOptimizer:
    """
    Advanced position sizing using Kelly Criterion and Expected Value optimization
    """
    
    def __init__(self, lookback_period: int = 252, min_trades: int = 50):
        """
        Initialize Kelly Criterion optimizer
        
        Args:
            lookback_period: Number of days to look back for historical analysis
            min_trades: Minimum number of trades required for reliable Kelly calculation
        """
        self.lookback_period = lookback_period
        self.min_trades = min_trades
        
        self.data_collector = MarketDataCollector()
        self.ml_engine = get_ml_engine()
        self.cache_manager = CacheManager()
        self.audit_logger = get_audit_logger()
        
        # Risk parameters
        self.max_kelly_fraction = 0.25  # Never risk more than 25% even if Kelly suggests it
        self.conservative_multiplier = 0.5  # Use half of Kelly suggestion (fractional Kelly)
        self.min_edge_threshold = 0.02  # Minimum edge required (2%)
        self.min_win_rate = 0.52  # Minimum win rate (52%)
        
        # Performance tracking
        self.historical_performance = {}
        self.success_rates = {}
        
        logger.info("Kelly Criterion Optimizer initialized")
    
    def calculate_kelly_fraction(self, win_probability: float, avg_win: float, 
                                avg_loss: float) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Kelly Criterion optimal fraction
        
        Kelly formula: f* = (bp - q) / b
        where:
        - b = odds received (avg_win / avg_loss)
        - p = probability of winning
        - q = probability of losing (1 - p)
        - f* = fraction of capital to wager
        """
        try:
            if win_probability <= 0 or win_probability >= 1:
                return 0.0, {"error": "Invalid win probability"}
            
            if avg_win <= 0 or avg_loss <= 0:
                return 0.0, {"error": "Invalid win/loss amounts"}
            
            # Calculate odds
            odds = avg_win / avg_loss
            
            # Kelly formula
            kelly_fraction = (odds * win_probability - (1 - win_probability)) / odds
            
            # Additional metrics
            edge = (win_probability * avg_win) - ((1 - win_probability) * avg_loss)
            expected_return = win_probability * avg_win - (1 - win_probability) * avg_loss
            
            # Risk metrics
            variance = (win_probability * (avg_win ** 2)) + ((1 - win_probability) * (avg_loss ** 2)) - (expected_return ** 2)
            volatility = math.sqrt(variance) if variance > 0 else 0
            
            # Sharpe-like ratio
            risk_adjusted_return = expected_return / volatility if volatility > 0 else 0
            
            analysis = {
                'kelly_fraction': kelly_fraction,
                'odds': odds,
                'edge': edge,
                'expected_return': expected_return,
                'variance': variance,
                'volatility': volatility,
                'risk_adjusted_return': risk_adjusted_return,
                'geometric_mean': math.log(1 + expected_return) if expected_return > -1 else float('-inf')
            }
            
            return kelly_fraction, analysis
            
        except Exception as e:
            logger.error(f"Kelly fraction calculation error: {e}")
            return 0.0, {"error": str(e)}
    
    def analyze_symbol_kelly(self, symbol: str, use_ml_predictions: bool = True) -> KellyAnalysis:
        """
        Analyze symbol using Kelly Criterion
        """
        try:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_period + 50)
            
            historical_data = self.data_collector.get_historical_data(
                symbol, 
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if historical_data is None or len(historical_data) < self.min_trades:
                raise ValueError(f"Insufficient historical data for {symbol}")
            
            # Calculate historical performance metrics
            returns = historical_data['Close'].pct_change().dropna()
            
            # Define win/loss criteria (could be customized)
            wins = returns[returns > 0]
            losses = returns[returns < 0]
            
            if len(wins) < 10 or len(losses) < 10:
                raise ValueError("Insufficient win/loss samples")
            
            # Calculate basic statistics
            win_probability = len(wins) / len(returns)
            avg_win = wins.mean()
            avg_loss = abs(losses.mean())  # Make positive
            
            # Enhanced analysis with ML predictions if enabled
            if use_ml_predictions:
                try:
                    # Get ML prediction for future performance
                    ml_prediction = self.ml_engine.predict_direction(symbol, horizon=1)
                    
                    # Adjust win probability based on ML confidence
                    if ml_prediction.confidence > 0.6:
                        ml_adjustment = (ml_prediction.confidence - 0.5) * 0.2  # Up to 10% adjustment
                        if ml_prediction.predicted_value > 0.5:  # Predicted upward movement
                            win_probability = min(0.95, win_probability + ml_adjustment)
                        else:
                            win_probability = max(0.05, win_probability - ml_adjustment)
                            
                except Exception as e:
                    logger.warning(f"ML prediction failed for {symbol}: {e}")
            
            # Calculate Kelly fraction
            kelly_fraction, analysis = self.calculate_kelly_fraction(
                win_probability, avg_win, avg_loss
            )
            
            # Risk adjustments
            adjusted_fraction = self._apply_risk_adjustments(
                kelly_fraction, analysis, symbol
            )
            
            # Determine recommendation
            recommendation = self._generate_recommendation(
                adjusted_fraction, analysis, win_probability
            )
            
            # Risk categorization
            risk_category = self._categorize_risk(analysis, win_probability)
            
            # Confidence interval (simplified)
            std_error = math.sqrt(win_probability * (1 - win_probability) / len(returns))
            confidence_interval = (
                max(0, win_probability - 1.96 * std_error),
                min(1, win_probability + 1.96 * std_error)
            )
            
            result = KellyAnalysis(
                symbol=symbol,
                optimal_fraction=max(0, adjusted_fraction),
                win_probability=win_probability,
                average_win=avg_win,
                average_loss=avg_loss,
                expected_value=analysis.get('expected_return', 0),
                kelly_fraction=kelly_fraction,
                adjusted_fraction=adjusted_fraction,
                confidence_interval=confidence_interval,
                recommendation=recommendation,
                risk_category=risk_category
            )
            
            # Cache result
            cache_key = f"kelly_analysis_{symbol}"
            self.cache_manager.set(cache_key, result, ttl=3600)  # 1 hour
            
            return result
            
        except Exception as e:
            logger.error(f"Kelly analysis failed for {symbol}: {e}")
            # Return safe default
            return KellyAnalysis(
                symbol=symbol,
                optimal_fraction=0.0,
                win_probability=0.5,
                average_win=0.0,
                average_loss=0.0,
                expected_value=0.0,
                kelly_fraction=0.0,
                adjusted_fraction=0.0,
                confidence_interval=(0.0, 1.0),
                recommendation='avoid',
                risk_category='extreme'
            )
    
    def optimize_portfolio_kelly(self, symbols: List[str], 
                                total_capital: float) -> Dict[str, PositionSizeResult]:
        """
        Optimize entire portfolio using Kelly Criterion
        """
        logger.info(f"Optimizing portfolio of {len(symbols)} symbols with Kelly Criterion")
        
        results = {}
        kelly_analyses = {}
        
        # Analyze each symbol
        for symbol in symbols:
            try:
                analysis = self.analyze_symbol_kelly(symbol)
                kelly_analyses[symbol] = analysis
            except Exception as e:
                logger.error(f"Failed to analyze {symbol}: {e}")
                continue
        
        # Filter out symbols with negative expected value
        profitable_symbols = {
            symbol: analysis for symbol, analysis in kelly_analyses.items()
            if analysis.expected_value > 0 and analysis.optimal_fraction > 0.01
        }
        
        if not profitable_symbols:
            logger.warning("No profitable symbols found")
            return results
        
        # Normalize Kelly fractions to ensure total doesn't exceed 100%
        total_kelly = sum(analysis.optimal_fraction for analysis in profitable_symbols.values())
        
        normalization_factor = min(1.0, 0.8 / total_kelly)  # Max 80% of capital
        
        # Calculate position sizes
        for symbol, analysis in profitable_symbols.items():
            normalized_fraction = analysis.optimal_fraction * normalization_factor
            position_value = total_capital * normalized_fraction
            
            # Additional risk adjustments
            risk_adjusted_size = self._apply_portfolio_risk_adjustments(
                position_value, analysis, total_capital
            )
            
            # Calculate metrics
            max_loss_potential = risk_adjusted_size * analysis.average_loss
            expected_return = risk_adjusted_size * analysis.expected_value
            
            # Sharpe-like ratio
            volatility = math.sqrt(
                analysis.win_probability * (analysis.average_win ** 2) +
                (1 - analysis.win_probability) * (analysis.average_loss ** 2)
            )
            sharpe_ratio = expected_return / (risk_adjusted_size * volatility) if volatility > 0 else 0
            
            result = PositionSizeResult(
                symbol=symbol,
                recommended_size=risk_adjusted_size,
                percentage_of_portfolio=risk_adjusted_size / total_capital,
                risk_adjusted_size=risk_adjusted_size,
                max_loss_potential=max_loss_potential,
                expected_return=expected_return,
                sharpe_ratio=sharpe_ratio,
                kelly_fraction=analysis.optimal_fraction
            )
            
            results[symbol] = result
        
        # Log portfolio summary
        total_allocated = sum(r.recommended_size for r in results.values())
        total_expected_return = sum(r.expected_return for r in results.values())
        
        self.audit_logger.log_event(
            EventType.PORTFOLIO_OPTIMIZED,
            SeverityLevel.LOW,
            resource='kelly_optimizer',
            details={
                'symbols_analyzed': len(symbols),
                'profitable_symbols': len(profitable_symbols),
                'total_allocated': total_allocated,
                'allocation_percentage': total_allocated / total_capital,
                'expected_portfolio_return': total_expected_return,
                'optimization_method': 'kelly_criterion'
            }
        )
        
        logger.info(f"Kelly optimization complete: {len(results)} positions, "
                   f"${total_allocated:.2f} allocated ({total_allocated/total_capital:.2%})")
        
        return results
    
    def calculate_dynamic_limits(self, symbol: str, current_performance: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate dynamic trading limits based on performance (inspired by money-machine)
        """
        try:
            base_limits = {
                'max_position_size': 0.1,  # 10% of portfolio
                'max_daily_trades': 10,
                'max_total_exposure': 0.8  # 80% of portfolio
            }
            
            # Get performance metrics
            win_rate = current_performance.get('win_rate', 0.5)
            avg_return = current_performance.get('avg_return', 0.0)
            sharpe_ratio = current_performance.get('sharpe_ratio', 0.0)
            consecutive_wins = current_performance.get('consecutive_wins', 0)
            
            # Performance multiplier (1.0 = no change, >1.0 = increase limits)
            performance_multiplier = 1.0
            
            # Adjust based on win rate
            if win_rate > 0.65:
                performance_multiplier *= 1.5
            elif win_rate > 0.55:
                performance_multiplier *= 1.2
            elif win_rate < 0.45:
                performance_multiplier *= 0.7
            elif win_rate < 0.35:
                performance_multiplier *= 0.5
            
            # Adjust based on Sharpe ratio
            if sharpe_ratio > 2.0:
                performance_multiplier *= 1.3
            elif sharpe_ratio > 1.0:
                performance_multiplier *= 1.1
            elif sharpe_ratio < 0:
                performance_multiplier *= 0.6
            
            # Adjust based on consecutive performance
            if consecutive_wins >= 5:
                performance_multiplier *= 1.2
            elif consecutive_wins <= -5:
                performance_multiplier *= 0.5
            
            # Apply limits to prevent extreme scaling
            performance_multiplier = max(0.1, min(3.0, performance_multiplier))
            
            # Calculate dynamic limits
            dynamic_limits = {
                key: value * performance_multiplier 
                for key, value in base_limits.items()
            }
            
            # Ensure reasonable bounds
            dynamic_limits['max_position_size'] = min(0.25, dynamic_limits['max_position_size'])
            dynamic_limits['max_total_exposure'] = min(0.95, dynamic_limits['max_total_exposure'])
            
            return dynamic_limits
            
        except Exception as e:
            logger.error(f"Dynamic limits calculation error: {e}")
            return {
                'max_position_size': 0.05,  # Conservative fallback
                'max_daily_trades': 5,
                'max_total_exposure': 0.5
            }
    
    def _apply_risk_adjustments(self, kelly_fraction: float, analysis: Dict[str, Any], symbol: str) -> float:
        """Apply risk adjustments to Kelly fraction"""
        adjusted = kelly_fraction
        
        # Never exceed maximum Kelly fraction
        adjusted = min(adjusted, self.max_kelly_fraction)
        
        # Apply conservative multiplier (fractional Kelly)
        adjusted *= self.conservative_multiplier
        
        # Check minimum edge requirement
        edge = analysis.get('edge', 0)
        if edge < self.min_edge_threshold:
            adjusted *= 0.5  # Reduce position size for low edge
        
        # Volatility adjustment
        volatility = analysis.get('volatility', 0)
        if volatility > 0.1:  # High volatility
            adjusted *= (0.1 / volatility)  # Scale down inversely
        
        # Ensure non-negative
        adjusted = max(0, adjusted)
        
        return adjusted
    
    def _apply_portfolio_risk_adjustments(self, position_size: float, 
                                        analysis: KellyAnalysis, 
                                        total_capital: float) -> float:
        """Apply portfolio-level risk adjustments"""
        adjusted = position_size
        
        # Maximum position size limit
        max_position = total_capital * 0.15  # 15% max per position
        adjusted = min(adjusted, max_position)
        
        # Risk category adjustments
        if analysis.risk_category == 'high':
            adjusted *= 0.7
        elif analysis.risk_category == 'extreme':
            adjusted *= 0.3
        
        # Confidence adjustment
        if analysis.confidence_interval[1] - analysis.confidence_interval[0] > 0.3:  # Wide confidence interval
            adjusted *= 0.8
        
        return adjusted
    
    def _generate_recommendation(self, adjusted_fraction: float, 
                               analysis: Dict[str, Any], 
                               win_probability: float) -> str:
        """Generate trading recommendation"""
        if adjusted_fraction <= 0:
            return 'avoid'
        elif adjusted_fraction < 0.02:  # Less than 2%
            return 'hold'
        elif adjusted_fraction < 0.05:  # Less than 5%
            return 'buy' if win_probability > 0.55 else 'hold'
        elif adjusted_fraction < 0.15:  # Less than 15%
            return 'buy'
        else:  # 15% or more
            return 'strong_buy' if analysis.get('risk_adjusted_return', 0) > 0.5 else 'buy'
    
    def _categorize_risk(self, analysis: Dict[str, Any], win_probability: float) -> str:
        """Categorize risk level"""
        volatility = analysis.get('volatility', 0)
        expected_return = analysis.get('expected_return', 0)
        
        if volatility > 0.15 or win_probability < 0.45 or expected_return < 0:
            return 'extreme'
        elif volatility > 0.1 or win_probability < 0.5:
            return 'high'
        elif volatility > 0.05 or win_probability < 0.55:
            return 'medium'
        else:
            return 'low'
    
    def get_optimization_summary(self, results: Dict[str, PositionSizeResult]) -> Dict[str, Any]:
        """Generate optimization summary"""
        if not results:
            return {'error': 'No optimization results'}
        
        total_allocated = sum(r.recommended_size for r in results.values())
        total_expected_return = sum(r.expected_return for r in results.values())
        avg_kelly_fraction = np.mean([r.kelly_fraction for r in results.values()])
        max_loss_potential = sum(r.max_loss_potential for r in results.values())
        
        return {
            'total_positions': len(results),
            'total_allocated': total_allocated,
            'total_expected_return': total_expected_return,
            'average_kelly_fraction': avg_kelly_fraction,
            'max_portfolio_loss': max_loss_potential,
            'expected_portfolio_return': total_expected_return,
            'risk_adjusted_score': total_expected_return / max_loss_potential if max_loss_potential > 0 else 0,
            'diversification_score': len(results) / 10,  # Simple diversification metric
            'positions': {
                symbol: {
                    'size': result.recommended_size,
                    'percentage': result.percentage_of_portfolio,
                    'expected_return': result.expected_return,
                    'kelly_fraction': result.kelly_fraction
                }
                for symbol, result in results.items()
            }
        }


# Global Kelly optimizer instance
_kelly_optimizer: Optional[KellyCriterionOptimizer] = None


def get_kelly_optimizer() -> KellyCriterionOptimizer:
    """Get the global Kelly Criterion optimizer instance"""
    global _kelly_optimizer
    if _kelly_optimizer is None:
        _kelly_optimizer = KellyCriterionOptimizer()
    return _kelly_optimizer


if __name__ == "__main__":
    # Test Kelly Criterion optimizer
    optimizer = KellyCriterionOptimizer()
    
    try:
        # Test single symbol analysis
        print("Testing Kelly Criterion analysis for NVDA...")
        analysis = optimizer.analyze_symbol_kelly("NVDA")
        
        print(f"Kelly Analysis Results:")
        print(f"  Optimal Fraction: {analysis.optimal_fraction:.4f}")
        print(f"  Win Probability: {analysis.win_probability:.4f}")
        print(f"  Expected Value: {analysis.expected_value:.4f}")
        print(f"  Recommendation: {analysis.recommendation}")
        print(f"  Risk Category: {analysis.risk_category}")
        
        # Test portfolio optimization
        print(f"\nTesting portfolio optimization...")
        symbols = ["NVDA", "MSFT", "GOOGL", "TSLA", "AMZN"]
        portfolio_results = optimizer.optimize_portfolio_kelly(symbols, 100000)
        
        print(f"Portfolio Optimization Results:")
        for symbol, result in portfolio_results.items():
            print(f"  {symbol}: ${result.recommended_size:.2f} "
                  f"({result.percentage_of_portfolio:.2%}) "
                  f"Kelly: {result.kelly_fraction:.4f}")
        
        # Generate summary
        summary = optimizer.get_optimization_summary(portfolio_results)
        print(f"\nOptimization Summary:")
        print(f"  Total Allocated: ${summary['total_allocated']:.2f}")
        print(f"  Expected Return: ${summary['total_expected_return']:.2f}")
        print(f"  Average Kelly: {summary['average_kelly_fraction']:.4f}")
        
    except Exception as e:
        print(f"Test failed: {e}")