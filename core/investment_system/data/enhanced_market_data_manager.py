"""
Enhanced Market Data Manager
Optimized market data collection for Kelly Criterion, Expected Value, and Dynamic Risk Management
"""

import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .market_data_collector import MarketDataCollector
from ..utils.cache_manager import CacheManager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

logger = logging.getLogger(__name__)


class EnhancedMarketDataManager:
    """
    Enhanced market data manager optimized for the enhanced portfolio system
    Provides data optimized for Kelly Criterion, Expected Value, and Risk Management
    """
    
    def __init__(self, config_file: str = "config/config.json"):
        """Initialize enhanced market data manager"""
        self.config_file = config_file
        self.config = self._load_config()
        
        # Initialize base collector
        self.base_collector = MarketDataCollector(config_file)
        
        # Enhanced caching and logging
        self.cache_manager = CacheManager()
        self.audit_logger = get_audit_logger()
        
        # Data quality tracking
        self.data_quality_log = {}
        
        # Performance optimization
        self.max_workers = 5  # Concurrent API requests
        self.batch_size = 10  # Symbols per batch
        
        logger.info("Enhanced Market Data Manager initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def get_kelly_optimized_data(self, symbol: str, lookback_days: int = 252) -> Dict[str, Any]:
        """
        Get data optimized for Kelly Criterion analysis
        Returns win/loss statistics and price movements
        """
        try:
            cache_key = f"kelly_data_{symbol}_{lookback_days}d"
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached Kelly data for {symbol}")
                return cached_data
            
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 50)  # Buffer for indicators
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise ValueError(f"No historical data available for {symbol}")
            
            # Calculate daily returns
            returns = hist['Close'].pct_change().dropna()
            
            # Calculate win/loss statistics
            wins = returns[returns > 0]
            losses = returns[returns < 0]
            
            if len(wins) < 10 or len(losses) < 10:
                raise ValueError(f"Insufficient win/loss samples for {symbol}")
            
            # Kelly Criterion specific metrics
            win_rate = len(wins) / len(returns)
            avg_win = wins.mean()
            avg_loss = abs(losses.mean())  # Positive value
            
            # Additional statistics for Kelly calculation
            median_win = wins.median()
            median_loss = abs(losses.median())
            win_std = wins.std()
            loss_std = losses.std()
            
            # Volatility measures
            daily_volatility = returns.std()
            annual_volatility = daily_volatility * np.sqrt(252)
            
            # Trend analysis
            recent_returns = returns.tail(30)  # Last 30 days
            recent_win_rate = len(recent_returns[recent_returns > 0]) / len(recent_returns)
            
            # Price momentum
            current_price = hist['Close'].iloc[-1]
            sma_20 = hist['Close'].tail(20).mean()
            sma_50 = hist['Close'].tail(50).mean() if len(hist) >= 50 else sma_20
            
            kelly_data = {
                'symbol': symbol,
                'data_date': datetime.now().isoformat(),
                'data_points': len(returns),
                'lookback_days': lookback_days,
                
                # Core Kelly metrics
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'median_win': median_win,
                'median_loss': median_loss,
                
                # Statistical measures
                'win_std': win_std,
                'loss_std': loss_std,
                'daily_volatility': daily_volatility,
                'annual_volatility': annual_volatility,
                
                # Trend indicators
                'recent_win_rate': recent_win_rate,
                'current_price': current_price,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'price_vs_sma20': (current_price - sma_20) / sma_20,
                'price_vs_sma50': (current_price - sma_50) / sma_50,
                
                # Raw data for further analysis
                'all_returns': returns.tolist(),
                'recent_returns': recent_returns.tolist(),
                'price_history': hist[['Close', 'Volume']].tail(50).to_dict(),
                
                # Data quality indicators
                'data_quality': {
                    'completeness': len(hist) / max(lookback_days, 1),
                    'win_sample_size': len(wins),
                    'loss_sample_size': len(losses),
                    'volatility_score': min(annual_volatility, 1.0)  # Cap at 100%
                }
            }
            
            # Cache the results
            self.cache_manager.set(cache_key, kelly_data, ttl=3600)  # 1 hour cache
            
            # Log data quality
            self._log_data_quality(symbol, kelly_data['data_quality'])
            
            return kelly_data
            
        except Exception as e:
            logger.error(f"Failed to get Kelly data for {symbol}: {e}")
            return self._create_fallback_kelly_data(symbol)
    
    def get_expected_value_data(self, symbol: str, horizon_days: int = 30) -> Dict[str, Any]:
        """
        Get data optimized for Expected Value analysis
        Returns scenario-based data for probability calculations
        """
        try:
            cache_key = f"ev_data_{symbol}_{horizon_days}d"
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached EV data for {symbol}")
                return cached_data
            
            # Get extended historical data for scenario generation
            end_date = datetime.now()
            start_date = end_date - timedelta(days=756)  # 3 years for robust scenarios
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty or len(hist) < 100:
                raise ValueError(f"Insufficient data for EV analysis: {symbol}")
            
            # Calculate rolling returns for the specified horizon
            rolling_returns = hist['Close'].pct_change(periods=horizon_days).dropna()
            
            if len(rolling_returns) < 20:
                # Fall back to daily returns scaled
                daily_returns = hist['Close'].pct_change().dropna()
                rolling_returns = daily_returns * horizon_days  # Approximate scaling
            
            # Generate scenario statistics
            scenarios = self._generate_ev_scenarios(rolling_returns)
            
            # Current market context
            current_price = hist['Close'].iloc[-1]
            recent_volatility = hist['Close'].pct_change().tail(30).std() * np.sqrt(252)
            
            # Volume analysis
            avg_volume = hist['Volume'].tail(50).mean()
            recent_volume = hist['Volume'].tail(10).mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Market cap and fundamentals (from yfinance info)
            try:
                info = ticker.info
                market_cap = info.get('marketCap', 0)
                pe_ratio = info.get('trailingPE', 0)
                forward_pe = info.get('forwardPE', 0)
                beta = info.get('beta', 1.0)
            except:
                market_cap = pe_ratio = forward_pe = 0
                beta = 1.0
            
            ev_data = {
                'symbol': symbol,
                'data_date': datetime.now().isoformat(),
                'horizon_days': horizon_days,
                'data_points': len(rolling_returns),
                
                # Scenario data
                'scenarios': scenarios,
                'scenario_count': len(scenarios),
                
                # Market context
                'current_price': current_price,
                'recent_volatility': recent_volatility,
                'volume_ratio': volume_ratio,
                
                # Fundamental context
                'market_cap': market_cap,
                'pe_ratio': pe_ratio,
                'forward_pe': forward_pe,
                'beta': beta,
                
                # Risk metrics
                'var_95': np.percentile(rolling_returns, 5) if len(rolling_returns) > 0 else -0.1,
                'var_99': np.percentile(rolling_returns, 1) if len(rolling_returns) > 0 else -0.2,
                'max_loss': rolling_returns.min() if len(rolling_returns) > 0 else -0.3,
                'max_gain': rolling_returns.max() if len(rolling_returns) > 0 else 0.3,
                
                # Data quality
                'data_quality': {
                    'sample_size': len(rolling_returns),
                    'data_completeness': len(hist) / 756,  # 3 years target
                    'volatility_stability': 1.0 - min(recent_volatility, 1.0)
                }
            }
            
            # Cache results
            self.cache_manager.set(cache_key, ev_data, ttl=1800)  # 30 minutes
            
            return ev_data
            
        except Exception as e:
            logger.error(f"Failed to get EV data for {symbol}: {e}")
            return self._create_fallback_ev_data(symbol, horizon_days)
    
    def get_risk_management_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get data optimized for Dynamic Risk Management
        Returns recent performance and volatility data
        """
        try:
            cache_key = f"risk_data_{symbol}"
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached risk data for {symbol}")
                return cached_data
            
            # Get recent data for risk assessment
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # 3 months
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise ValueError(f"No recent data for risk analysis: {symbol}")
            
            # Calculate risk metrics
            returns = hist['Close'].pct_change().dropna()
            
            # Rolling volatility
            rolling_vol_5d = returns.rolling(5).std() * np.sqrt(252)
            rolling_vol_20d = returns.rolling(20).std() * np.sqrt(252)
            
            # Price momentum
            momentum_5d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-6] - 1) if len(hist) >= 6 else 0
            momentum_20d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-21] - 1) if len(hist) >= 21 else 0
            
            # Volume patterns
            volume_sma = hist['Volume'].rolling(20).mean()
            volume_spike_ratio = hist['Volume'].iloc[-1] / volume_sma.iloc[-1] if not volume_sma.empty else 1.0
            
            # Drawdown analysis
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
            current_drawdown = drawdown.iloc[-1] if not drawdown.empty else 0
            
            risk_data = {
                'symbol': symbol,
                'data_date': datetime.now().isoformat(),
                'analysis_period_days': 90,
                
                # Volatility metrics
                'current_volatility': rolling_vol_20d.iloc[-1] if not rolling_vol_20d.empty else 0.3,
                'volatility_5d': rolling_vol_5d.iloc[-1] if not rolling_vol_5d.empty else 0.3,
                'volatility_trend': self._calculate_volatility_trend(rolling_vol_20d),
                
                # Momentum indicators
                'momentum_5d': momentum_5d,
                'momentum_20d': momentum_20d,
                'momentum_consistency': self._calculate_momentum_consistency(returns),
                
                # Volume analysis
                'volume_spike_ratio': volume_spike_ratio,
                'volume_trend': self._calculate_volume_trend(hist['Volume']),
                
                # Risk metrics
                'max_drawdown_3m': max_drawdown,
                'current_drawdown': current_drawdown,
                'var_5d': np.percentile(returns.tail(30), 5) if len(returns) >= 30 else -0.05,
                
                # Correlation with market (approximate using recent returns)
                'market_correlation': self._estimate_market_correlation(returns),
                
                # Data quality
                'data_quality': {
                    'data_points': len(returns),
                    'completeness': len(hist) / 90,
                    'reliability_score': min(len(returns) / 60, 1.0)  # 60+ days is reliable
                }
            }
            
            # Cache results
            self.cache_manager.set(cache_key, risk_data, ttl=1800)  # 30 minutes
            
            return risk_data
            
        except Exception as e:
            logger.error(f"Failed to get risk data for {symbol}: {e}")
            return self._create_fallback_risk_data(symbol)
    
    def get_batch_data(self, symbols: List[str], data_types: List[str] = None) -> Dict[str, Dict]:
        """
        Get data for multiple symbols efficiently using parallel processing
        
        Args:
            symbols: List of symbols to analyze
            data_types: List of data types ('kelly', 'ev', 'risk'). None = all types
        """
        if data_types is None:
            data_types = ['kelly', 'ev', 'risk']
        
        logger.info(f"Fetching batch data for {len(symbols)} symbols: {data_types}")
        
        results = {}
        
        # Process symbols in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for symbol in symbols:
                for data_type in data_types:
                    if data_type == 'kelly':
                        future = executor.submit(self.get_kelly_optimized_data, symbol)
                    elif data_type == 'ev':
                        future = executor.submit(self.get_expected_value_data, symbol)
                    elif data_type == 'risk':
                        future = executor.submit(self.get_risk_management_data, symbol)
                    else:
                        continue
                    
                    futures[future] = (symbol, data_type)
            
            # Collect results
            for future in as_completed(futures):
                symbol, data_type = futures[future]
                try:
                    data = future.result(timeout=30)  # 30 second timeout
                    
                    if symbol not in results:
                        results[symbol] = {}
                    results[symbol][data_type] = data
                    
                except Exception as e:
                    logger.error(f"Failed to get {data_type} data for {symbol}: {e}")
                    if symbol not in results:
                        results[symbol] = {}
                    results[symbol][data_type] = {'error': str(e)}
        
        # Log batch results
        successful = sum(1 for symbol_data in results.values() 
                        for data_type_data in symbol_data.values() 
                        if 'error' not in data_type_data)
        total = len(symbols) * len(data_types)
        
        self.audit_logger.log_event(
            EventType.DATA_FETCHED,
            SeverityLevel.LOW,
            resource='enhanced_market_data_manager',
            details={
                'symbols_requested': len(symbols),
                'data_types_requested': data_types,
                'successful_fetches': successful,
                'total_requests': total,
                'success_rate': successful / total if total > 0 else 0
            }
        )
        
        logger.info(f"Batch data fetch complete: {successful}/{total} successful")
        
        return results
    
    def _generate_ev_scenarios(self, returns: pd.Series) -> List[Dict]:
        """Generate scenario data for Expected Value analysis"""
        if len(returns) < 5:
            return self._create_default_scenarios()
        
        # Calculate percentiles for different market conditions
        percentiles = {
            'bear_market': 5,      # Worst 5%
            'normal_down': 25,     # Below average
            'sideways': 50,        # Median
            'normal_up': 75,       # Above average
            'bull_market': 95      # Best 5%
        }
        
        scenario_weights = {
            'bear_market': 0.05,
            'normal_down': 0.15,
            'sideways': 0.6,
            'normal_up': 0.15,
            'bull_market': 0.05
        }
        
        scenarios = []
        for name, percentile in percentiles.items():
            outcome = np.percentile(returns, percentile)
            probability = scenario_weights[name]
            
            scenarios.append({
                'name': name,
                'probability': probability,
                'outcome': outcome,
                'description': f"{name.replace('_', ' ').title()} scenario ({percentile}th percentile)"
            })
        
        return scenarios
    
    def _calculate_volatility_trend(self, volatility_series: pd.Series) -> str:
        """Calculate if volatility is increasing, decreasing, or stable"""
        if len(volatility_series) < 10:
            return 'stable'
        
        recent = volatility_series.tail(5).mean()
        older = volatility_series.head(5).mean()
        
        if recent > older * 1.2:
            return 'increasing'
        elif recent < older * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_momentum_consistency(self, returns: pd.Series) -> float:
        """Calculate momentum consistency (0-1, higher is more consistent)"""
        if len(returns) < 20:
            return 0.5
        
        # Calculate rolling 5-day returns
        rolling_returns = returns.rolling(5).sum()
        
        # Count sign changes
        sign_changes = (rolling_returns.diff().abs() > 0).sum()
        
        # Consistency is inverse of sign changes
        consistency = max(0, 1 - (sign_changes / len(rolling_returns)))
        
        return consistency
    
    def _calculate_volume_trend(self, volume_series: pd.Series) -> str:
        """Calculate volume trend"""
        if len(volume_series) < 10:
            return 'stable'
        
        recent_avg = volume_series.tail(10).mean()
        historical_avg = volume_series.head(len(volume_series)//2).mean()
        
        if recent_avg > historical_avg * 1.3:
            return 'increasing'
        elif recent_avg < historical_avg * 0.7:
            return 'decreasing'
        else:
            return 'stable'
    
    def _estimate_market_correlation(self, returns: pd.Series) -> float:
        """Estimate correlation with market (simplified)"""
        try:
            # Get SPY data for correlation
            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period="3mo")
            spy_returns = spy_hist['Close'].pct_change().dropna()
            
            # Align dates
            min_len = min(len(returns), len(spy_returns))
            if min_len < 10:
                return 0.5  # Default assumption
            
            correlation = np.corrcoef(returns.tail(min_len), spy_returns.tail(min_len))[0, 1]
            return correlation if not np.isnan(correlation) else 0.5
            
        except:
            return 0.5  # Default market correlation
    
    def _create_fallback_kelly_data(self, symbol: str) -> Dict:
        """Create fallback Kelly data when real data unavailable"""
        return {
            'symbol': symbol,
            'data_date': datetime.now().isoformat(),
            'win_rate': 0.5,
            'avg_win': 0.02,
            'avg_loss': 0.02,
            'daily_volatility': 0.02,
            'annual_volatility': 0.3,
            'data_quality': {'completeness': 0.0},
            'error': 'Insufficient market data'
        }
    
    def _create_fallback_ev_data(self, symbol: str, horizon_days: int) -> Dict:
        """Create fallback EV data"""
        return {
            'symbol': symbol,
            'data_date': datetime.now().isoformat(),
            'horizon_days': horizon_days,
            'scenarios': self._create_default_scenarios(),
            'data_quality': {'completeness': 0.0},
            'error': 'Insufficient market data'
        }
    
    def _create_fallback_risk_data(self, symbol: str) -> Dict:
        """Create fallback risk data"""
        return {
            'symbol': symbol,
            'data_date': datetime.now().isoformat(),
            'current_volatility': 0.3,
            'max_drawdown_3m': -0.15,
            'market_correlation': 0.5,
            'data_quality': {'completeness': 0.0},
            'error': 'Insufficient market data'
        }
    
    def _create_default_scenarios(self) -> List[Dict]:
        """Create default scenarios when data is unavailable"""
        return [
            {'name': 'bear_market', 'probability': 0.05, 'outcome': -0.2, 'description': 'Bear market scenario'},
            {'name': 'normal_down', 'probability': 0.15, 'outcome': -0.05, 'description': 'Normal down scenario'},
            {'name': 'sideways', 'probability': 0.6, 'outcome': 0.0, 'description': 'Sideways scenario'},
            {'name': 'normal_up', 'probability': 0.15, 'outcome': 0.05, 'description': 'Normal up scenario'},
            {'name': 'bull_market', 'probability': 0.05, 'outcome': 0.2, 'description': 'Bull market scenario'}
        ]
    
    def _log_data_quality(self, symbol: str, quality: Dict):
        """Log data quality metrics"""
        self.data_quality_log[symbol] = {
            'timestamp': datetime.now(),
            'quality_score': quality.get('completeness', 0),
            'issues': []
        }
        
        if quality.get('completeness', 0) < 0.8:
            self.data_quality_log[symbol]['issues'].append('Incomplete data')
    
    def get_data_quality_report(self) -> Dict:
        """Get comprehensive data quality report"""
        if not self.data_quality_log:
            return {'message': 'No data quality information available'}
        
        total_symbols = len(self.data_quality_log)
        high_quality = sum(1 for log in self.data_quality_log.values() if log['quality_score'] >= 0.8)
        
        return {
            'total_symbols_tracked': total_symbols,
            'high_quality_symbols': high_quality,
            'data_quality_rate': high_quality / total_symbols if total_symbols > 0 else 0,
            'last_updated': max(log['timestamp'] for log in self.data_quality_log.values()) if self.data_quality_log else None,
            'symbols_with_issues': [symbol for symbol, log in self.data_quality_log.items() if log['issues']],
            'detailed_log': self.data_quality_log
        }


# Global enhanced market data manager instance
_enhanced_market_data_manager: Optional[EnhancedMarketDataManager] = None


def get_enhanced_market_data_manager() -> EnhancedMarketDataManager:
    """Get the global enhanced market data manager instance"""
    global _enhanced_market_data_manager
    if _enhanced_market_data_manager is None:
        _enhanced_market_data_manager = EnhancedMarketDataManager()
    return _enhanced_market_data_manager


if __name__ == "__main__":
    # Test enhanced market data manager
    manager = EnhancedMarketDataManager()
    
    try:
        print("=== Enhanced Market Data Manager Test ===")
        
        # Test single symbol data
        symbol = "NVDA"
        print(f"\nTesting data collection for {symbol}...")
        
        # Test Kelly data
        kelly_data = manager.get_kelly_optimized_data(symbol)
        if 'error' not in kelly_data:
            print(f"✅ Kelly Data: Win Rate {kelly_data['win_rate']:.2%}, "
                  f"Avg Win {kelly_data['avg_win']:.3f}, "
                  f"Volatility {kelly_data['annual_volatility']:.1%}")
        else:
            print(f"⚠️ Kelly Data Error: {kelly_data['error']}")
        
        # Test EV data
        ev_data = manager.get_expected_value_data(symbol)
        if 'error' not in ev_data:
            print(f"✅ EV Data: {len(ev_data['scenarios'])} scenarios, "
                  f"VaR 95%: {ev_data['var_95']:.2%}")
        else:
            print(f"⚠️ EV Data Error: {ev_data['error']}")
        
        # Test Risk data
        risk_data = manager.get_risk_management_data(symbol)
        if 'error' not in risk_data:
            print(f"✅ Risk Data: Volatility {risk_data['current_volatility']:.1%}, "
                  f"Max DD {risk_data['max_drawdown_3m']:.2%}")
        else:
            print(f"⚠️ Risk Data Error: {risk_data['error']}")
        
        # Test batch data
        symbols = ["NVDA", "MSFT", "GOOGL"]
        print(f"\nTesting batch data for {symbols}...")
        
        batch_data = manager.get_batch_data(symbols, ['kelly', 'risk'])
        successful = sum(1 for symbol_data in batch_data.values() 
                        for data in symbol_data.values() 
                        if 'error' not in data)
        total = len(symbols) * 2  # kelly + risk
        
        print(f"✅ Batch Data: {successful}/{total} successful fetches")
        
        # Data quality report
        quality_report = manager.get_data_quality_report()
        print(f"\n📊 Data Quality Report:")
        print(f"   Symbols Tracked: {quality_report.get('total_symbols_tracked', 0)}")
        print(f"   High Quality Rate: {quality_report.get('data_quality_rate', 0):.1%}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()