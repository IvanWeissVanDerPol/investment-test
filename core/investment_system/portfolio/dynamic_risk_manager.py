"""
Dynamic Risk Manager
Performance-based risk management inspired by money-machine project
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from collections import deque

from ..utils.cache_manager import CacheManager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    win_rate: float
    avg_return: float
    sharpe_ratio: float
    max_drawdown: float
    consecutive_wins: int
    consecutive_losses: int
    total_trades: int
    profit_factor: float
    average_holding_period: float


@dataclass
class RiskLimits:
    """Dynamic risk limits"""
    max_position_size: float
    max_portfolio_exposure: float
    max_daily_trades: int
    max_correlation: float
    stop_loss_percent: float
    take_profit_percent: float
    cooling_period_hours: int


@dataclass
class RiskAdjustment:
    """Risk adjustment recommendation"""
    symbol: str
    current_limits: RiskLimits
    recommended_limits: RiskLimits
    adjustment_reason: str
    confidence: float
    effective_date: datetime


class DynamicRiskManager:
    """
    Dynamic risk management system that adjusts limits based on performance
    """
    
    def __init__(self, lookback_days: int = 30):
        """
        Initialize dynamic risk manager
        
        Args:
            lookback_days: Number of days to look back for performance calculation
        """
        self.lookback_days = lookback_days
        self.cache_manager = CacheManager()
        self.audit_logger = get_audit_logger()
        
        # Performance tracking
        self.performance_history = deque(maxlen=1000)  # Last 1000 trades
        self.daily_performance = {}
        
        # Base risk limits (conservative starting point)
        self.base_limits = RiskLimits(
            max_position_size=0.05,      # 5% of portfolio
            max_portfolio_exposure=0.80,  # 80% of portfolio
            max_daily_trades=10,         # 10 trades per day
            max_correlation=0.70,        # 70% max correlation
            stop_loss_percent=0.08,      # 8% stop loss
            take_profit_percent=0.15,    # 15% take profit
            cooling_period_hours=4       # 4 hour cooling period after loss
        )
        
        # Performance thresholds for adjustments
        self.performance_thresholds = {
            'excellent': {'win_rate': 0.75, 'sharpe': 2.0, 'multiplier': 2.0},
            'good': {'win_rate': 0.65, 'sharpe': 1.5, 'multiplier': 1.5},
            'average': {'win_rate': 0.55, 'sharpe': 1.0, 'multiplier': 1.0},
            'poor': {'win_rate': 0.45, 'sharpe': 0.5, 'multiplier': 0.7},
            'bad': {'win_rate': 0.35, 'sharpe': 0.0, 'multiplier': 0.4}
        }
        
        logger.info("Dynamic Risk Manager initialized")
    
    def record_trade(self, symbol: str, entry_price: float, exit_price: float,
                    position_size: float, entry_time: datetime, exit_time: datetime,
                    trade_type: str = 'buy') -> None:
        """
        Record a completed trade for performance tracking
        """
        try:
            # Calculate trade metrics
            if trade_type == 'buy':
                return_pct = (exit_price - entry_price) / entry_price
            else:  # sell
                return_pct = (entry_price - exit_price) / entry_price
            
            profit = position_size * return_pct
            holding_period = (exit_time - entry_time).total_seconds() / 3600  # hours
            
            trade_record = {
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'position_size': position_size,
                'return_pct': return_pct,
                'profit': profit,
                'holding_period': holding_period,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'trade_type': trade_type
            }
            
            # Add to performance history
            self.performance_history.append(trade_record)
            
            # Update daily performance
            date_key = exit_time.strftime('%Y-%m-%d')
            if date_key not in self.daily_performance:
                self.daily_performance[date_key] = []
            self.daily_performance[date_key].append(trade_record)
            
            # Log the trade
            self.audit_logger.log_event(
                EventType.TRADE_RECORDED,
                SeverityLevel.LOW,
                resource='dynamic_risk_manager',
                details={
                    'symbol': symbol,
                    'return_pct': return_pct,
                    'profit': profit,
                    'holding_period': holding_period
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to record trade: {e}")
    
    def calculate_performance_metrics(self, symbol: Optional[str] = None) -> PerformanceMetrics:
        """
        Calculate current performance metrics
        """
        try:
            # Filter trades
            if symbol:
                trades = [t for t in self.performance_history if t['symbol'] == symbol]
            else:
                trades = list(self.performance_history)
            
            if not trades:
                return self._create_default_metrics()
            
            # Filter to lookback period
            cutoff_time = datetime.now() - timedelta(days=self.lookback_days)
            recent_trades = [t for t in trades if t['exit_time'] >= cutoff_time]
            
            if not recent_trades:
                return self._create_default_metrics()
            
            # Calculate metrics
            returns = [t['return_pct'] for t in recent_trades]
            profits = [t['profit'] for t in recent_trades]
            holding_periods = [t['holding_period'] for t in recent_trades]
            
            # Win rate
            wins = [r for r in returns if r > 0]
            win_rate = len(wins) / len(returns)
            
            # Average return
            avg_return = np.mean(returns)
            
            # Sharpe ratio (simplified)
            return_std = np.std(returns) if len(returns) > 1 else 0.1
            sharpe_ratio = avg_return / return_std if return_std > 0 else 0
            
            # Max drawdown
            cumulative_returns = np.cumprod([1 + r for r in returns])
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0
            
            # Consecutive wins/losses
            consecutive_wins = self._calculate_consecutive_wins(returns)
            consecutive_losses = self._calculate_consecutive_losses(returns)
            
            # Profit factor
            total_wins = sum([p for p in profits if p > 0])
            total_losses = abs(sum([p for p in profits if p < 0]))
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Average holding period
            avg_holding_period = np.mean(holding_periods)
            
            return PerformanceMetrics(
                win_rate=win_rate,
                avg_return=avg_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                consecutive_wins=consecutive_wins,
                consecutive_losses=consecutive_losses,
                total_trades=len(recent_trades),
                profit_factor=profit_factor,
                average_holding_period=avg_holding_period
            )
            
        except Exception as e:
            logger.error(f"Performance calculation failed: {e}")
            return self._create_default_metrics()
    
    def adjust_risk_limits(self, symbol: Optional[str] = None) -> RiskAdjustment:
        """
        Adjust risk limits based on current performance
        """
        try:
            # Get current performance
            performance = self.calculate_performance_metrics(symbol)
            
            # Determine performance category
            perf_category = self._categorize_performance(performance)
            
            # Get multiplier for this performance level
            multiplier = self.performance_thresholds[perf_category]['multiplier']
            
            # Calculate new limits
            new_limits = RiskLimits(
                max_position_size=min(0.25, self.base_limits.max_position_size * multiplier),
                max_portfolio_exposure=min(0.95, self.base_limits.max_portfolio_exposure * 
                                         (0.8 + 0.2 * multiplier)),  # More conservative scaling
                max_daily_trades=int(self.base_limits.max_daily_trades * multiplier),
                max_correlation=min(0.85, self.base_limits.max_correlation + 
                                  (multiplier - 1) * 0.1),
                stop_loss_percent=max(0.05, self.base_limits.stop_loss_percent / 
                                    (0.5 + 0.5 * multiplier)),
                take_profit_percent=min(0.30, self.base_limits.take_profit_percent * multiplier),
                cooling_period_hours=max(1, int(self.base_limits.cooling_period_hours / multiplier))
            )
            
            # Generate adjustment reason
            reason = f"Performance category: {perf_category} " \
                    f"(Win Rate: {performance.win_rate:.2%}, " \
                    f"Sharpe: {performance.sharpe_ratio:.2f})"
            
            # Calculate confidence based on number of trades
            confidence = min(0.95, performance.total_trades / 50)  # Max confidence at 50+ trades
            
            adjustment = RiskAdjustment(
                symbol=symbol or 'GLOBAL',
                current_limits=self.base_limits,
                recommended_limits=new_limits,
                adjustment_reason=reason,
                confidence=confidence,
                effective_date=datetime.now()
            )
            
            # Log the adjustment
            self.audit_logger.log_event(
                EventType.RISK_LIMITS_ADJUSTED,
                SeverityLevel.MEDIUM,
                resource='dynamic_risk_manager',
                details={
                    'symbol': symbol,
                    'performance_category': perf_category,
                    'multiplier': multiplier,
                    'confidence': confidence,
                    'new_max_position': new_limits.max_position_size
                }
            )
            
            return adjustment
            
        except Exception as e:
            logger.error(f"Risk adjustment failed: {e}")
            return self._create_default_adjustment(symbol)
    
    def get_position_size_limit(self, symbol: str, portfolio_value: float) -> float:
        """
        Get maximum position size for a symbol based on current performance
        """
        try:
            adjustment = self.adjust_risk_limits(symbol)
            max_percentage = adjustment.recommended_limits.max_position_size
            
            # Apply confidence scaling
            confidence_adjusted = max_percentage * adjustment.confidence
            
            # Never exceed 25% regardless of performance
            final_percentage = min(0.25, confidence_adjusted)
            
            return portfolio_value * final_percentage
            
        except Exception as e:
            logger.error(f"Position size limit calculation failed: {e}")
            return portfolio_value * 0.05  # Conservative fallback
    
    def should_enter_position(self, symbol: str, current_correlation: float = 0.0) -> bool:
        """
        Check if we should enter a position based on current risk limits
        """
        try:
            adjustment = self.adjust_risk_limits(symbol)
            limits = adjustment.recommended_limits
            
            # Check correlation limit
            if current_correlation > limits.max_correlation:
                logger.warning(f"Position blocked due to high correlation: {current_correlation:.2%}")
                return False
            
            # Check daily trade limit
            today = datetime.now().strftime('%Y-%m-%d')
            today_trades = len(self.daily_performance.get(today, []))
            
            if today_trades >= limits.max_daily_trades:
                logger.warning(f"Daily trade limit reached: {today_trades}/{limits.max_daily_trades}")
                return False
            
            # Check cooling period after losses
            if self._is_in_cooling_period(symbol, limits.cooling_period_hours):
                logger.warning(f"Symbol {symbol} in cooling period")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Position entry check failed: {e}")
            return False  # Conservative fallback
    
    def get_stop_loss_level(self, symbol: str, entry_price: float) -> float:
        """Get stop loss level based on current performance"""
        try:
            adjustment = self.adjust_risk_limits(symbol)
            stop_loss_pct = adjustment.recommended_limits.stop_loss_percent
            
            return entry_price * (1 - stop_loss_pct)
            
        except Exception as e:
            logger.error(f"Stop loss calculation failed: {e}")
            return entry_price * 0.92  # 8% stop loss fallback
    
    def get_take_profit_level(self, symbol: str, entry_price: float) -> float:
        """Get take profit level based on current performance"""
        try:
            adjustment = self.adjust_risk_limits(symbol)
            take_profit_pct = adjustment.recommended_limits.take_profit_percent
            
            return entry_price * (1 + take_profit_pct)
            
        except Exception as e:
            logger.error(f"Take profit calculation failed: {e}")
            return entry_price * 1.15  # 15% take profit fallback
    
    def _categorize_performance(self, metrics: PerformanceMetrics) -> str:
        """Categorize performance into excellence levels"""
        for category, thresholds in self.performance_thresholds.items():
            if (metrics.win_rate >= thresholds['win_rate'] and 
                metrics.sharpe_ratio >= thresholds['sharpe']):
                return category
        
        return 'bad'  # Worst category if no thresholds met
    
    def _calculate_consecutive_wins(self, returns: List[float]) -> int:
        """Calculate current consecutive wins"""
        consecutive = 0
        for ret in reversed(returns):
            if ret > 0:
                consecutive += 1
            else:
                break
        return consecutive
    
    def _calculate_consecutive_losses(self, returns: List[float]) -> int:
        """Calculate current consecutive losses"""
        consecutive = 0
        for ret in reversed(returns):
            if ret < 0:
                consecutive += 1
            else:
                break
        return consecutive
    
    def _is_in_cooling_period(self, symbol: str, cooling_hours: int) -> bool:
        """Check if symbol is in cooling period after recent loss"""
        if not self.performance_history:
            return False
        
        # Find last trade for this symbol
        symbol_trades = [t for t in reversed(self.performance_history) 
                        if t['symbol'] == symbol]
        
        if not symbol_trades:
            return False
        
        last_trade = symbol_trades[0]
        if last_trade['return_pct'] >= 0:  # Last trade was profitable
            return False
        
        # Check if cooling period has passed
        time_since = datetime.now() - last_trade['exit_time']
        cooling_period = timedelta(hours=cooling_hours)
        
        return time_since < cooling_period
    
    def _create_default_metrics(self) -> PerformanceMetrics:
        """Create default performance metrics"""
        return PerformanceMetrics(
            win_rate=0.50,
            avg_return=0.01,
            sharpe_ratio=0.5,
            max_drawdown=0.10,
            consecutive_wins=0,
            consecutive_losses=0,
            total_trades=0,
            profit_factor=1.0,
            average_holding_period=24.0
        )
    
    def _create_default_adjustment(self, symbol: Optional[str]) -> RiskAdjustment:
        """Create default risk adjustment"""
        return RiskAdjustment(
            symbol=symbol or 'GLOBAL',
            current_limits=self.base_limits,
            recommended_limits=self.base_limits,
            adjustment_reason="Insufficient data for adjustment",
            confidence=0.1,
            effective_date=datetime.now()
        )
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk management summary"""
        try:
            performance = self.calculate_performance_metrics()
            adjustment = self.adjust_risk_limits()
            
            return {
                'performance_category': self._categorize_performance(performance),
                'current_metrics': {
                    'win_rate': performance.win_rate,
                    'avg_return': performance.avg_return,
                    'sharpe_ratio': performance.sharpe_ratio,
                    'max_drawdown': performance.max_drawdown,
                    'total_trades': performance.total_trades,
                    'profit_factor': performance.profit_factor
                },
                'current_limits': {
                    'max_position_size': adjustment.recommended_limits.max_position_size,
                    'max_portfolio_exposure': adjustment.recommended_limits.max_portfolio_exposure,
                    'max_daily_trades': adjustment.recommended_limits.max_daily_trades,
                    'stop_loss_percent': adjustment.recommended_limits.stop_loss_percent,
                    'take_profit_percent': adjustment.recommended_limits.take_profit_percent
                },
                'adjustment_confidence': adjustment.confidence,
                'last_adjustment': adjustment.effective_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Risk summary generation failed: {e}")
            return {'error': str(e)}


# Global dynamic risk manager instance
_risk_manager: Optional[DynamicRiskManager] = None


def get_risk_manager() -> DynamicRiskManager:
    """Get the global dynamic risk manager instance"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = DynamicRiskManager()
    return _risk_manager


if __name__ == "__main__":
    # Test dynamic risk manager
    risk_manager = DynamicRiskManager()
    
    try:
        # Simulate some trades
        print("Simulating trades...")
        from datetime import datetime, timedelta
        
        base_time = datetime.now() - timedelta(days=10)
        
        # Simulate winning streak
        for i in range(5):
            trade_time = base_time + timedelta(hours=i*6)
            risk_manager.record_trade(
                symbol="NVDA",
                entry_price=100.0,
                exit_price=105.0,  # 5% win
                position_size=1000,
                entry_time=trade_time,
                exit_time=trade_time + timedelta(hours=2),
                trade_type='buy'
            )
        
        # Calculate performance
        metrics = risk_manager.calculate_performance_metrics()
        print(f"Performance Metrics:")
        print(f"  Win Rate: {metrics.win_rate:.2%}")
        print(f"  Average Return: {metrics.avg_return:.2%}")
        print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print(f"  Total Trades: {metrics.total_trades}")
        
        # Get risk adjustment
        adjustment = risk_manager.adjust_risk_limits("NVDA")
        print(f"\nRisk Adjustment:")
        print(f"  Max Position Size: {adjustment.recommended_limits.max_position_size:.2%}")
        print(f"  Max Daily Trades: {adjustment.recommended_limits.max_daily_trades}")
        print(f"  Adjustment Reason: {adjustment.adjustment_reason}")
        print(f"  Confidence: {adjustment.confidence:.2%}")
        
        # Test position sizing
        portfolio_value = 100000
        max_position = risk_manager.get_position_size_limit("NVDA", portfolio_value)
        print(f"\nPosition Sizing:")
        print(f"  Portfolio Value: ${portfolio_value:,.2f}")
        print(f"  Max Position for NVDA: ${max_position:,.2f}")
        
        # Get summary
        summary = risk_manager.get_risk_summary()
        print(f"\nRisk Summary:")
        print(f"  Performance Category: {summary['performance_category']}")
        print(f"  Current Win Rate: {summary['current_metrics']['win_rate']:.2%}")
        
    except Exception as e:
        print(f"Test failed: {e}")