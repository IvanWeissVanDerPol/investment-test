"""
Comprehensive Backtesting Engine
Advanced backtesting system for portfolio optimization strategies and trading algorithms
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
from pathlib import Path
import json
import pickle

from ..data.market_data_collector import MarketDataCollector
from ..portfolio.advanced_portfolio_optimizer import AdvancedPortfolioOptimizer, OptimizationResult
from ..ai.ml_prediction_engine import MLPredictionEngine
from ..utils.cache_manager import CacheManager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

logger = logging.getLogger(__name__)


@dataclass
class BacktestMetrics:
    """Comprehensive backtest performance metrics"""
    total_return: float
    annual_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    average_trade_return: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    benchmark_return: float
    alpha: float
    beta: float
    information_ratio: float
    tracking_error: float
    var_95: float
    var_99: float
    conditional_var_95: float


@dataclass
class Trade:
    """Individual trade record"""
    symbol: str
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    trade_type: str  # 'buy' or 'sell'
    signal_strength: float
    pnl: Optional[float] = None
    return_pct: Optional[float] = None


@dataclass
class PortfolioSnapshot:
    """Portfolio state at a point in time"""
    timestamp: datetime
    positions: Dict[str, float]
    cash: float
    total_value: float
    weights: Dict[str, float]
    returns: float = 0.0


@dataclass
class BacktestResult:
    """Complete backtest results"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_value: float
    benchmark_symbol: str
    metrics: BacktestMetrics
    portfolio_history: List[PortfolioSnapshot]
    trades: List[Trade]
    drawdown_periods: List[Dict[str, Any]]
    monthly_returns: pd.Series
    rolling_metrics: Dict[str, pd.Series]
    metadata: Dict[str, Any]


class Strategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        
    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame], 
                        portfolio: PortfolioSnapshot, 
                        context: Dict[str, Any]) -> Dict[str, float]:
        """
        Generate trading signals for each symbol
        Returns: Dict mapping symbol to target weight (-1 to 1)
        """
        pass
        
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters"""
        pass


class BuyAndHoldStrategy(Strategy):
    """Buy and hold strategy implementation"""
    
    def __init__(self, symbols: List[str], equal_weight: bool = True):
        super().__init__("BuyAndHold")
        self.symbols = symbols
        self.equal_weight = equal_weight
        self._initialized = False
        
    def generate_signals(self, data: Dict[str, pd.DataFrame], 
                        portfolio: PortfolioSnapshot, 
                        context: Dict[str, Any]) -> Dict[str, float]:
        """Generate buy and hold signals"""
        if not self._initialized:
            if self.equal_weight:
                weight = 1.0 / len(self.symbols)
                signals = {symbol: weight for symbol in self.symbols}
            else:
                # Market cap weighting would go here
                signals = {symbol: 1.0 / len(self.symbols) for symbol in self.symbols}
            self._initialized = True
            return signals
        
        # After initialization, maintain current positions
        return {symbol: portfolio.weights.get(symbol, 0.0) for symbol in self.symbols}
        
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'symbols': self.symbols,
            'equal_weight': self.equal_weight
        }


class MeanReversionStrategy(Strategy):
    """Mean reversion strategy using RSI and Bollinger Bands"""
    
    def __init__(self, symbols: List[str], rsi_period: int = 14, 
                 rsi_oversold: float = 30, rsi_overbought: float = 70,
                 bb_period: int = 20, bb_std: float = 2):
        super().__init__("MeanReversion")
        self.symbols = symbols
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.bb_period = bb_period
        self.bb_std = bb_std
        
    def generate_signals(self, data: Dict[str, pd.DataFrame], 
                        portfolio: PortfolioSnapshot, 
                        context: Dict[str, Any]) -> Dict[str, float]:
        """Generate mean reversion signals"""
        signals = {}
        
        for symbol in self.symbols:
            if symbol not in data or len(data[symbol]) < max(self.rsi_period, self.bb_period):
                signals[symbol] = 0.0
                continue
                
            symbol_data = data[symbol]
            current_price = symbol_data['Close'].iloc[-1]
            
            # Calculate RSI
            delta = symbol_data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Calculate Bollinger Bands
            sma = symbol_data['Close'].rolling(self.bb_period).mean()
            std = symbol_data['Close'].rolling(self.bb_period).std()
            bb_upper = sma + (std * self.bb_std)
            bb_lower = sma - (std * self.bb_std)
            
            # Generate signal
            signal_strength = 0.0
            
            # RSI signals
            if current_rsi < self.rsi_oversold:
                signal_strength += 0.5  # Buy signal
            elif current_rsi > self.rsi_overbought:
                signal_strength -= 0.5  # Sell signal
                
            # Bollinger Band signals
            bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
            if bb_position < 0.2:  # Near lower band
                signal_strength += 0.3
            elif bb_position > 0.8:  # Near upper band
                signal_strength -= 0.3
                
            # Normalize to target weight
            max_position = 0.2  # Max 20% position size
            signals[symbol] = np.clip(signal_strength * max_position, -max_position, max_position)
            
        return signals
        
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'symbols': self.symbols,
            'rsi_period': self.rsi_period,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'bb_period': self.bb_period,
            'bb_std': self.bb_std
        }


class MLEnhancedStrategy(Strategy):
    """Machine learning enhanced portfolio strategy"""
    
    def __init__(self, symbols: List[str], ml_engine: MLPredictionEngine,
                 rebalance_frequency: int = 30, confidence_threshold: float = 0.6):
        super().__init__("MLEnhanced")
        self.symbols = symbols
        self.ml_engine = ml_engine
        self.rebalance_frequency = rebalance_frequency
        self.confidence_threshold = confidence_threshold
        self.last_rebalance = None
        
    def generate_signals(self, data: Dict[str, pd.DataFrame], 
                        portfolio: PortfolioSnapshot, 
                        context: Dict[str, Any]) -> Dict[str, float]:
        """Generate ML-enhanced signals"""
        current_date = portfolio.timestamp
        
        # Check if rebalancing is needed
        if (self.last_rebalance is None or 
            (current_date - self.last_rebalance).days >= self.rebalance_frequency):
            
            signals = {}
            total_confidence = 0
            predictions = {}
            
            # Get ML predictions for each symbol
            for symbol in self.symbols:
                try:
                    # Get price prediction
                    price_pred = self.ml_engine.predict_price(symbol, horizon=1, model_type='ensemble')
                    direction_pred = self.ml_engine.predict_direction(symbol, horizon=1)
                    
                    if (price_pred.confidence > self.confidence_threshold and 
                        direction_pred.confidence > self.confidence_threshold):
                        
                        # Combine predictions
                        combined_signal = (
                            price_pred.predicted_value * 0.6 +
                            (direction_pred.predicted_value - 0.5) * 2 * 0.4
                        )
                        combined_confidence = (price_pred.confidence + direction_pred.confidence) / 2
                        
                        predictions[symbol] = {
                            'signal': combined_signal,
                            'confidence': combined_confidence
                        }
                        total_confidence += combined_confidence
                    else:
                        predictions[symbol] = {'signal': 0.0, 'confidence': 0.0}
                        
                except Exception as e:
                    logger.warning(f"ML prediction failed for {symbol}: {e}")
                    predictions[symbol] = {'signal': 0.0, 'confidence': 0.0}
            
            # Normalize signals by confidence
            if total_confidence > 0:
                for symbol in self.symbols:
                    pred = predictions[symbol]
                    weight = (pred['confidence'] / total_confidence) * pred['signal']
                    signals[symbol] = np.clip(weight, -0.3, 0.3)  # Max 30% position
            else:
                # No confident predictions, maintain current positions
                signals = {symbol: portfolio.weights.get(symbol, 0.0) for symbol in self.symbols}
                
            self.last_rebalance = current_date
            return signals
        else:
            # Maintain current positions
            return {symbol: portfolio.weights.get(symbol, 0.0) for symbol in self.symbols}
            
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'symbols': self.symbols,
            'rebalance_frequency': self.rebalance_frequency,
            'confidence_threshold': self.confidence_threshold
        }


class BacktestingEngine:
    """
    Comprehensive backtesting engine for portfolio strategies
    """
    
    def __init__(self, initial_capital: float = 100000, 
                 commission_rate: float = 0.001,
                 slippage_rate: float = 0.0005):
        """Initialize backtesting engine"""
        self.data_collector = MarketDataCollector()
        self.cache_manager = CacheManager()
        self.audit_logger = get_audit_logger()
        
        # Trading parameters
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate  # 0.1% commission
        self.slippage_rate = slippage_rate      # 0.05% slippage
        
        # Results storage
        self.results_dir = Path("reports/backtests")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Backtesting Engine initialized")
        
    def run_backtest(self, strategy: Strategy, start_date: str, end_date: str,
                    benchmark_symbol: str = "SPY", 
                    rebalance_frequency: int = 1) -> BacktestResult:
        """
        Run comprehensive backtest for given strategy
        
        Args:
            strategy: Trading strategy to test
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            benchmark_symbol: Benchmark for comparison
            rebalance_frequency: Days between rebalancing
        """
        try:
            logger.info(f"Starting backtest for {strategy.name}")
            
            # Get required symbols
            symbols = list(set(strategy.symbols + [benchmark_symbol]))
            
            # Load historical data
            data = self._load_historical_data(symbols, start_date, end_date)
            if not data:
                raise ValueError("Failed to load historical data")
            
            # Initialize portfolio
            portfolio_history = []
            trades = []
            current_portfolio = PortfolioSnapshot(
                timestamp=pd.to_datetime(start_date),
                positions={symbol: 0.0 for symbol in strategy.symbols},
                cash=self.initial_capital,
                total_value=self.initial_capital,
                weights={symbol: 0.0 for symbol in strategy.symbols}
            )
            
            # Get trading dates
            trading_dates = sorted(set().union(*[data[symbol].index for symbol in data.keys()]))
            trading_dates = [d for d in trading_dates if d >= pd.to_datetime(start_date)]
            
            last_rebalance_date = None
            
            # Run simulation
            for i, current_date in enumerate(trading_dates):
                # Update portfolio values with current prices
                current_portfolio = self._update_portfolio_values(
                    current_portfolio, data, current_date
                )
                current_portfolio.timestamp = current_date
                
                # Check if rebalancing is needed
                if (last_rebalance_date is None or 
                    (current_date - last_rebalance_date).days >= rebalance_frequency):
                    
                    # Get current data window for strategy
                    data_window = self._get_data_window(data, current_date, lookback_days=252)
                    
                    # Generate trading signals
                    context = {
                        'current_date': current_date,
                        'lookback_days': 252,
                        'trading_day': i
                    }
                    
                    target_weights = strategy.generate_signals(
                        data_window, current_portfolio, context
                    )
                    
                    # Execute rebalancing
                    new_trades = self._rebalance_portfolio(
                        current_portfolio, target_weights, data, current_date
                    )
                    trades.extend(new_trades)
                    
                    last_rebalance_date = current_date
                
                # Save portfolio snapshot
                portfolio_history.append(current_portfolio.copy() if hasattr(current_portfolio, 'copy') else
                                       PortfolioSnapshot(
                                           timestamp=current_portfolio.timestamp,
                                           positions=current_portfolio.positions.copy(),
                                           cash=current_portfolio.cash,
                                           total_value=current_portfolio.total_value,
                                           weights=current_portfolio.weights.copy(),
                                           returns=current_portfolio.returns
                                       ))
            
            # Calculate comprehensive metrics
            benchmark_data = data[benchmark_symbol]
            metrics = self._calculate_metrics(
                portfolio_history, benchmark_data, self.initial_capital
            )
            
            # Create result object
            result = BacktestResult(
                strategy_name=strategy.name,
                start_date=pd.to_datetime(start_date),
                end_date=pd.to_datetime(end_date),
                initial_capital=self.initial_capital,
                final_value=portfolio_history[-1].total_value,
                benchmark_symbol=benchmark_symbol,
                metrics=metrics,
                portfolio_history=portfolio_history,
                trades=trades,
                drawdown_periods=self._identify_drawdown_periods(portfolio_history),
                monthly_returns=self._calculate_monthly_returns(portfolio_history),
                rolling_metrics=self._calculate_rolling_metrics(portfolio_history),
                metadata={
                    'strategy_parameters': strategy.get_parameters(),
                    'commission_rate': self.commission_rate,
                    'slippage_rate': self.slippage_rate,
                    'rebalance_frequency': rebalance_frequency
                }
            )
            
            # Cache and save results
            self._save_backtest_result(result)
            
            # Audit log
            self.audit_logger.log_event(
                EventType.ANALYSIS_COMPLETED,
                SeverityLevel.LOW,
                resource='backtesting_engine',
                details={
                    'strategy': strategy.name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'final_value': result.final_value,
                    'total_return': metrics.total_return
                }
            )
            
            logger.info(f"Backtest completed for {strategy.name}")
            return result
            
        except Exception as e:
            logger.error(f"Backtest failed for {strategy.name}: {e}")
            self.audit_logger.log_event(
                EventType.ERROR_OCCURRED,
                SeverityLevel.HIGH,
                resource='backtesting_engine',
                error_message=str(e),
                details={'strategy': strategy.name}
            )
            raise
    
    def compare_strategies(self, strategies: List[Strategy], start_date: str, 
                          end_date: str, benchmark_symbol: str = "SPY") -> Dict[str, BacktestResult]:
        """Compare multiple strategies"""
        results = {}
        
        for strategy in strategies:
            try:
                result = self.run_backtest(strategy, start_date, end_date, benchmark_symbol)
                results[strategy.name] = result
            except Exception as e:
                logger.error(f"Strategy {strategy.name} failed: {e}")
                continue
        
        return results
    
    def _load_historical_data(self, symbols: List[str], start_date: str, 
                             end_date: str) -> Dict[str, pd.DataFrame]:
        """Load historical data for all symbols"""
        data = {}
        
        for symbol in symbols:
            try:
                symbol_data = self.data_collector.get_historical_data(
                    symbol, 
                    start_date=start_date, 
                    end_date=end_date
                )
                
                if symbol_data is not None and not symbol_data.empty:
                    data[symbol] = symbol_data
                else:
                    logger.warning(f"No data available for {symbol}")
                    
            except Exception as e:
                logger.error(f"Failed to load data for {symbol}: {e}")
        
        return data
    
    def _get_data_window(self, data: Dict[str, pd.DataFrame], current_date: pd.Timestamp,
                        lookback_days: int = 252) -> Dict[str, pd.DataFrame]:
        """Get data window for strategy analysis"""
        start_date = current_date - timedelta(days=lookback_days)
        
        data_window = {}
        for symbol, symbol_data in data.items():
            # Filter data up to current date
            filtered_data = symbol_data[symbol_data.index <= current_date]
            # Get lookback window
            filtered_data = filtered_data[filtered_data.index >= start_date]
            
            if not filtered_data.empty:
                data_window[symbol] = filtered_data
        
        return data_window
    
    def _update_portfolio_values(self, portfolio: PortfolioSnapshot, 
                               data: Dict[str, pd.DataFrame],
                               current_date: pd.Timestamp) -> PortfolioSnapshot:
        """Update portfolio values based on current prices"""
        total_value = portfolio.cash
        new_positions = portfolio.positions.copy()
        
        for symbol, shares in portfolio.positions.items():
            if symbol in data and shares != 0:
                # Get current price
                symbol_data = data[symbol]
                price_data = symbol_data[symbol_data.index <= current_date]
                
                if not price_data.empty:
                    current_price = price_data['Close'].iloc[-1]
                    position_value = shares * current_price
                    total_value += position_value
        
        # Calculate weights
        weights = {}
        if total_value > 0:
            for symbol, shares in new_positions.items():
                if symbol in data and shares != 0:
                    symbol_data = data[symbol]
                    price_data = symbol_data[symbol_data.index <= current_date]
                    if not price_data.empty:
                        current_price = price_data['Close'].iloc[-1]
                        position_value = shares * current_price
                        weights[symbol] = position_value / total_value
                    else:
                        weights[symbol] = 0.0
                else:
                    weights[symbol] = 0.0
        
        # Calculate returns
        returns = (total_value - self.initial_capital) / self.initial_capital if self.initial_capital > 0 else 0.0
        
        return PortfolioSnapshot(
            timestamp=current_date,
            positions=new_positions,
            cash=portfolio.cash,
            total_value=total_value,
            weights=weights,
            returns=returns
        )
    
    def _rebalance_portfolio(self, portfolio: PortfolioSnapshot, 
                           target_weights: Dict[str, float],
                           data: Dict[str, pd.DataFrame],
                           current_date: pd.Timestamp) -> List[Trade]:
        """Rebalance portfolio to target weights"""
        trades = []
        
        for symbol, target_weight in target_weights.items():
            if symbol not in data:
                continue
                
            # Get current price
            symbol_data = data[symbol]
            price_data = symbol_data[symbol_data.index <= current_date]
            if price_data.empty:
                continue
                
            current_price = price_data['Close'].iloc[-1]
            
            # Apply slippage
            execution_price = current_price * (1 + self.slippage_rate)
            
            # Calculate target position
            current_weight = portfolio.weights.get(symbol, 0.0)
            weight_diff = target_weight - current_weight
            
            if abs(weight_diff) > 0.01:  # Only trade if significant difference
                target_value = target_weight * portfolio.total_value
                current_shares = portfolio.positions.get(symbol, 0.0)
                target_shares = target_value / execution_price
                
                shares_diff = target_shares - current_shares
                
                if abs(shares_diff) > 0.01:  # Minimum trade size
                    # Calculate commission
                    trade_value = abs(shares_diff * execution_price)
                    commission = trade_value * self.commission_rate
                    
                    # Create trade
                    trade = Trade(
                        symbol=symbol,
                        entry_date=current_date,
                        exit_date=None,
                        entry_price=execution_price,
                        exit_price=None,
                        quantity=shares_diff,
                        trade_type='buy' if shares_diff > 0 else 'sell',
                        signal_strength=abs(weight_diff)
                    )
                    trades.append(trade)
                    
                    # Update portfolio
                    portfolio.positions[symbol] = target_shares
                    
                    # Update cash (subtract trade value and commission)
                    cash_change = -shares_diff * execution_price - commission
                    portfolio.cash += cash_change
        
        return trades
    
    def _calculate_metrics(self, portfolio_history: List[PortfolioSnapshot],
                          benchmark_data: pd.DataFrame, 
                          initial_capital: float) -> BacktestMetrics:
        """Calculate comprehensive performance metrics"""
        if not portfolio_history:
            raise ValueError("No portfolio history available")
        
        # Convert to returns series
        portfolio_values = [p.total_value for p in portfolio_history]
        dates = [p.timestamp for p in portfolio_history]
        
        portfolio_series = pd.Series(portfolio_values, index=dates)
        portfolio_returns = portfolio_series.pct_change().dropna()
        
        # Benchmark returns
        benchmark_aligned = benchmark_data.reindex(dates, method='ffill')
        benchmark_returns = benchmark_aligned['Close'].pct_change().dropna()
        
        # Align series
        common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
        portfolio_returns = portfolio_returns.reindex(common_dates)
        benchmark_returns = benchmark_returns.reindex(common_dates)
        
        # Basic metrics
        total_return = (portfolio_values[-1] - initial_capital) / initial_capital
        annual_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
        volatility = portfolio_returns.std() * np.sqrt(252)
        
        # Risk-free rate (assume 2%)
        risk_free_rate = 0.02
        
        # Sharpe ratio
        excess_returns = portfolio_returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_returns / volatility if volatility > 0 else 0
        
        # Sortino ratio
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = excess_returns / downside_volatility if downside_volatility > 0 else 0
        
        # Maximum drawdown
        cumulative_returns = (1 + portfolio_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        # Calmar ratio
        calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
        
        # Win rate and profit factor
        positive_returns = portfolio_returns[portfolio_returns > 0]
        negative_returns = portfolio_returns[portfolio_returns < 0]
        win_rate = len(positive_returns) / len(portfolio_returns) if len(portfolio_returns) > 0 else 0
        
        total_gains = positive_returns.sum() if len(positive_returns) > 0 else 0
        total_losses = abs(negative_returns.sum()) if len(negative_returns) > 0 else 1
        profit_factor = total_gains / total_losses if total_losses > 0 else 0
        
        # Average trade return
        avg_trade_return = portfolio_returns.mean()
        
        # Consecutive wins/losses
        consecutive_wins = consecutive_losses = 0
        max_consecutive_wins = max_consecutive_losses = 0
        
        for ret in portfolio_returns:
            if ret > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            elif ret < 0:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        
        # Benchmark comparison
        benchmark_total_return = (benchmark_returns + 1).prod() - 1 if len(benchmark_returns) > 0 else 0
        
        # Alpha and Beta
        if len(benchmark_returns) > 1 and len(portfolio_returns) > 1:
            covariance = np.cov(portfolio_returns, benchmark_returns)[0][1]
            benchmark_variance = benchmark_returns.var()
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 1
            
            benchmark_annual_return = (1 + benchmark_total_return) ** (252 / len(benchmark_returns)) - 1
            alpha = annual_return - (risk_free_rate + beta * (benchmark_annual_return - risk_free_rate))
        else:
            beta = 1.0
            alpha = 0.0
        
        # Information ratio and tracking error
        active_returns = portfolio_returns - benchmark_returns
        tracking_error = active_returns.std() * np.sqrt(252) if len(active_returns) > 1 else 0
        information_ratio = (active_returns.mean() * 252) / tracking_error if tracking_error > 0 else 0
        
        # Value at Risk
        var_95 = np.percentile(portfolio_returns, 5)
        var_99 = np.percentile(portfolio_returns, 1)
        
        # Conditional VaR (Expected Shortfall)
        conditional_var_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        
        return BacktestMetrics(
            total_return=total_return,
            annual_return=annual_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            average_trade_return=avg_trade_return,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            benchmark_return=benchmark_total_return,
            alpha=alpha,
            beta=beta,
            information_ratio=information_ratio,
            tracking_error=tracking_error,
            var_95=var_95,
            var_99=var_99,
            conditional_var_95=conditional_var_95
        )
    
    def _identify_drawdown_periods(self, portfolio_history: List[PortfolioSnapshot]) -> List[Dict[str, Any]]:
        """Identify major drawdown periods"""
        values = [p.total_value for p in portfolio_history]
        dates = [p.timestamp for p in portfolio_history]
        
        drawdown_periods = []
        peak_value = values[0]
        peak_date = dates[0]
        in_drawdown = False
        
        for i, (value, date) in enumerate(zip(values, dates)):
            if value > peak_value:
                # New peak
                if in_drawdown:
                    # End of drawdown period
                    drawdown_periods.append({
                        'start_date': peak_date,
                        'end_date': date,
                        'peak_value': peak_value,
                        'trough_value': min(values[peak_idx:i]),
                        'drawdown_pct': (min(values[peak_idx:i]) - peak_value) / peak_value,
                        'duration_days': (date - peak_date).days,
                        'recovery_days': (date - trough_date).days
                    })
                    in_drawdown = False
                
                peak_value = value
                peak_date = date
                peak_idx = i
            else:
                if not in_drawdown:
                    in_drawdown = True
                    trough_value = value
                    trough_date = date
                elif value < trough_value:
                    trough_value = value
                    trough_date = date
        
        return drawdown_periods
    
    def _calculate_monthly_returns(self, portfolio_history: List[PortfolioSnapshot]) -> pd.Series:
        """Calculate monthly returns"""
        values = [p.total_value for p in portfolio_history]
        dates = [p.timestamp for p in portfolio_history]
        
        portfolio_series = pd.Series(values, index=dates)
        monthly_values = portfolio_series.groupby(pd.Grouper(freq='M')).last()
        monthly_returns = monthly_values.pct_change().dropna()
        
        return monthly_returns
    
    def _calculate_rolling_metrics(self, portfolio_history: List[PortfolioSnapshot]) -> Dict[str, pd.Series]:
        """Calculate rolling performance metrics"""
        values = [p.total_value for p in portfolio_history]
        dates = [p.timestamp for p in portfolio_history]
        
        portfolio_series = pd.Series(values, index=dates)
        returns = portfolio_series.pct_change().dropna()
        
        # Rolling windows
        windows = [30, 60, 90, 180, 252]
        rolling_metrics = {}
        
        for window in windows:
            if len(returns) >= window:
                rolling_returns = returns.rolling(window)
                rolling_metrics[f'volatility_{window}d'] = rolling_returns.std() * np.sqrt(252)
                rolling_metrics[f'sharpe_{window}d'] = (rolling_returns.mean() * 252 - 0.02) / rolling_metrics[f'volatility_{window}d']
                
                # Rolling max drawdown
                rolling_cumret = (1 + returns).rolling(window).apply(lambda x: x.prod(), raw=False)
                rolling_peak = rolling_cumret.rolling(window).max()
                rolling_dd = (rolling_cumret - rolling_peak) / rolling_peak
                rolling_metrics[f'max_drawdown_{window}d'] = rolling_dd.rolling(window).min().abs()
        
        return rolling_metrics
    
    def _save_backtest_result(self, result: BacktestResult):
        """Save backtest result to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{result.strategy_name}_{timestamp}.pkl"
            filepath = self.results_dir / filename
            
            with open(filepath, 'wb') as f:
                pickle.dump(result, f)
            
            logger.info(f"Backtest result saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save backtest result: {e}")
    
    def generate_backtest_report(self, result: BacktestResult) -> str:
        """Generate comprehensive backtest report"""
        report = f"""
BACKTEST REPORT: {result.strategy_name}
{'=' * 50}

PERIOD: {result.start_date.strftime('%Y-%m-%d')} to {result.end_date.strftime('%Y-%m-%d')}
INITIAL CAPITAL: ${result.initial_capital:,.2f}
FINAL VALUE: ${result.final_value:,.2f}

PERFORMANCE METRICS:
{'─' * 30}
Total Return: {result.metrics.total_return:.2%}
Annual Return: {result.metrics.annual_return:.2%}
Volatility: {result.metrics.volatility:.2%}
Sharpe Ratio: {result.metrics.sharpe_ratio:.3f}
Sortino Ratio: {result.metrics.sortino_ratio:.3f}
Maximum Drawdown: {result.metrics.max_drawdown:.2%}
Calmar Ratio: {result.metrics.calmar_ratio:.3f}

TRADE STATISTICS:
{'─' * 30}
Win Rate: {result.metrics.win_rate:.2%}
Profit Factor: {result.metrics.profit_factor:.3f}
Average Trade Return: {result.metrics.average_trade_return:.4%}
Max Consecutive Wins: {result.metrics.max_consecutive_wins}
Max Consecutive Losses: {result.metrics.max_consecutive_losses}

BENCHMARK COMPARISON ({result.benchmark_symbol}):
{'─' * 30}
Strategy Return: {result.metrics.total_return:.2%}
Benchmark Return: {result.metrics.benchmark_return:.2%}
Alpha: {result.metrics.alpha:.2%}
Beta: {result.metrics.beta:.3f}
Information Ratio: {result.metrics.information_ratio:.3f}
Tracking Error: {result.metrics.tracking_error:.2%}

RISK METRICS:
{'─' * 30}
Value at Risk (95%): {result.metrics.var_95:.4%}
Value at Risk (99%): {result.metrics.var_99:.4%}
Conditional VaR (95%): {result.metrics.conditional_var_95:.4%}

STRATEGY PARAMETERS:
{'─' * 30}
{json.dumps(result.metadata['strategy_parameters'], indent=2)}

DRAWDOWN PERIODS:
{'─' * 30}
"""
        
        for i, period in enumerate(result.drawdown_periods[:5]):  # Top 5 drawdowns
            report += f"""
{i+1}. {period['start_date'].strftime('%Y-%m-%d')} to {period['end_date'].strftime('%Y-%m-%d')}
   Drawdown: {period['drawdown_pct']:.2%}
   Duration: {period['duration_days']} days
   Recovery: {period.get('recovery_days', 'N/A')} days
"""
        
        return report


# Global backtesting engine instance
_backtesting_engine: Optional[BacktestingEngine] = None


def get_backtesting_engine() -> BacktestingEngine:
    """Get the global backtesting engine instance"""
    global _backtesting_engine
    if _backtesting_engine is None:
        _backtesting_engine = BacktestingEngine()
    return _backtesting_engine


if __name__ == "__main__":
    # Test backtesting engine
    engine = BacktestingEngine()
    
    # Test with buy and hold strategy
    symbols = ["NVDA", "MSFT", "TSLA", "GOOGL", "AMZN"]
    buy_hold_strategy = BuyAndHoldStrategy(symbols)
    
    try:
        result = engine.run_backtest(
            strategy=buy_hold_strategy,
            start_date="2022-01-01",
            end_date="2023-12-31",
            benchmark_symbol="SPY"
        )
        
        print(engine.generate_backtest_report(result))
        
        # Test mean reversion strategy
        mean_reversion = MeanReversionStrategy(symbols)
        
        result2 = engine.run_backtest(
            strategy=mean_reversion,
            start_date="2022-01-01", 
            end_date="2023-12-31",
            benchmark_symbol="SPY"
        )
        
        print(f"\nMean Reversion Strategy Results:")
        print(f"Total Return: {result2.metrics.total_return:.2%}")
        print(f"Sharpe Ratio: {result2.metrics.sharpe_ratio:.3f}")
        print(f"Max Drawdown: {result2.metrics.max_drawdown:.2%}")
        
    except Exception as e:
        print(f"Backtest failed: {e}")