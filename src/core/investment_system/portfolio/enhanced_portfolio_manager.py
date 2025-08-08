"""
Enhanced Portfolio Manager with Dynamic Risk Management
Integrates Dynamic Risk Manager, Kelly Criterion, and Expected Value analysis
"""

import json
import logging
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass

# Import our enhanced components
from .dynamic_risk_manager import get_risk_manager, DynamicRiskManager, RiskLimits, RiskAdjustment
from .kelly_criterion_optimizer import get_kelly_optimizer, KellyCriterionOptimizer, PositionSizeResult
from ..analysis.expected_value_calculator import get_ev_calculator, ExpectedValueCalculator, EVAnalysis
from .live_portfolio_manager import LivePortfolioManager
from ..data.enhanced_market_data_manager import get_enhanced_market_data_manager, EnhancedMarketDataManager
from ..utils.cache_manager import CacheManager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

logger = logging.getLogger(__name__)


@dataclass
class EnhancedPositionRecommendation:
    """Enhanced position recommendation with risk management"""
    symbol: str
    recommended_action: str  # 'buy', 'sell', 'hold', 'reduce'
    position_size: float  # Dollar amount
    percentage_of_portfolio: float
    risk_adjusted_size: float
    kelly_fraction: float
    expected_value: float
    ev_confidence: float
    dynamic_limits: RiskLimits
    stop_loss_level: Optional[float]
    take_profit_level: Optional[float]
    rationale: str
    risk_warnings: List[str]


@dataclass
class PortfolioHealthReport:
    """Comprehensive portfolio health assessment"""
    overall_score: float  # 0-100
    performance_category: str  # 'excellent', 'good', 'average', 'poor', 'bad'
    risk_level: str  # 'low', 'medium', 'high', 'extreme'
    rebalancing_needed: bool
    position_adjustments: List[EnhancedPositionRecommendation]
    risk_summary: Dict
    performance_metrics: Dict
    kelly_optimization_summary: Dict
    ev_analysis_summary: Dict
    timestamp: datetime


class EnhancedPortfolioManager:
    """
    Advanced portfolio manager integrating:
    - Dynamic Risk Management
    - Kelly Criterion position sizing
    - Expected Value analysis
    - Live portfolio tracking
    - Performance-based limit adjustments
    """
    
    def __init__(self, config_file: str = "config/config.json"):
        """Initialize enhanced portfolio manager"""
        self.config_file = config_file
        self.config = self._load_config()
        
        # Initialize core components
        self.live_portfolio = LivePortfolioManager(config_file)
        self.risk_manager = get_risk_manager()
        self.kelly_optimizer = get_kelly_optimizer()
        self.ev_calculator = get_ev_calculator()
        self.market_data = get_enhanced_market_data_manager()
        
        # Caching and logging
        self.cache_manager = CacheManager()
        self.audit_logger = get_audit_logger()
        
        # Performance tracking
        self.last_analysis = None
        self.analysis_history = []
        
        logger.info("Enhanced Portfolio Manager initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def analyze_portfolio_with_risk_management(self, 
                                             symbols: Optional[List[str]] = None,
                                             portfolio_value: Optional[float] = None) -> PortfolioHealthReport:
        """
        Comprehensive portfolio analysis with integrated risk management
        """
        try:
            logger.info("Starting enhanced portfolio analysis with risk management")
            
            # Get current portfolio data
            if not symbols:
                symbols = self.config.get('target_stocks', []) + self.config.get('ai_robotics_etfs', [])
            
            if not portfolio_value:
                portfolio_summary = self.live_portfolio.get_portfolio_summary_for_analysis()
                portfolio_value = portfolio_summary.get('account_info', {}).get('balance', 900)
            
            # Get performance metrics from risk manager
            performance_metrics = self.risk_manager.calculate_performance_metrics()
            performance_category = self.risk_manager._categorize_performance(performance_metrics)
            
            # Get Kelly optimization for all symbols
            kelly_results = self.kelly_optimizer.optimize_portfolio_kelly(symbols, portfolio_value)
            kelly_summary = self.kelly_optimizer.get_optimization_summary(kelly_results)
            
            # Get EV analysis for opportunities
            ev_rankings = self.ev_calculator.rank_opportunities(symbols, max_risk_level='medium')
            
            # Generate position recommendations
            position_recommendations = []
            risk_warnings = []
            
            for symbol in symbols:
                try:
                    recommendation = self._analyze_symbol_with_risk_management(
                        symbol, portfolio_value, kelly_results, ev_rankings
                    )
                    position_recommendations.append(recommendation)
                    
                    if recommendation.risk_warnings:
                        risk_warnings.extend(recommendation.risk_warnings)
                        
                except Exception as e:
                    logger.error(f"Failed to analyze {symbol}: {e}")
                    continue
            
            # Calculate overall portfolio score
            overall_score = self._calculate_portfolio_score(
                performance_metrics, kelly_summary, ev_rankings, position_recommendations
            )
            
            # Determine risk level
            risk_level = self._assess_overall_risk_level(performance_metrics, position_recommendations)
            
            # Check if rebalancing is needed
            rebalancing_needed = self._assess_rebalancing_needs(position_recommendations)
            
            # Get comprehensive risk summary
            risk_summary = self.risk_manager.get_risk_summary()
            
            # Create EV analysis summary
            ev_summary = {
                'total_opportunities': len(ev_rankings),
                'premium_tier_count': len([r for r in ev_rankings if r.tier == 'premium']),
                'average_ev_score': sum(r.ev_score for r in ev_rankings) / len(ev_rankings) if ev_rankings else 0,
                'top_opportunity': ev_rankings[0].symbol if ev_rankings else None
            }
            
            # Create portfolio health report
            health_report = PortfolioHealthReport(
                overall_score=overall_score,
                performance_category=performance_category,
                risk_level=risk_level,
                rebalancing_needed=rebalancing_needed,
                position_adjustments=position_recommendations,
                risk_summary=risk_summary,
                performance_metrics={
                    'win_rate': performance_metrics.win_rate,
                    'avg_return': performance_metrics.avg_return,
                    'sharpe_ratio': performance_metrics.sharpe_ratio,
                    'max_drawdown': performance_metrics.max_drawdown,
                    'total_trades': performance_metrics.total_trades,
                    'profit_factor': performance_metrics.profit_factor
                },
                kelly_optimization_summary=kelly_summary,
                ev_analysis_summary=ev_summary,
                timestamp=datetime.now()
            )
            
            # Cache and log results
            self.last_analysis = health_report
            self.analysis_history.append(health_report)
            
            # Log the analysis
            self.audit_logger.log_event(
                EventType.PORTFOLIO_ANALYZED,
                SeverityLevel.LOW,
                resource='enhanced_portfolio_manager',
                details={
                    'symbols_analyzed': len(symbols),
                    'overall_score': overall_score,
                    'performance_category': performance_category,
                    'risk_level': risk_level,
                    'rebalancing_needed': rebalancing_needed,
                    'total_recommendations': len(position_recommendations)
                }
            )
            
            logger.info(f"Enhanced portfolio analysis complete - Score: {overall_score:.1f}, "
                       f"Category: {performance_category}, Risk: {risk_level}")
            
            return health_report
            
        except Exception as e:
            logger.error(f"Enhanced portfolio analysis failed: {e}")
            raise
    
    def _analyze_symbol_with_risk_management(self, 
                                           symbol: str, 
                                           portfolio_value: float,
                                           kelly_results: Dict[str, PositionSizeResult],
                                           ev_rankings: List) -> EnhancedPositionRecommendation:
        """Analyze individual symbol with comprehensive risk management"""
        try:
            # Get Kelly analysis
            kelly_result = kelly_results.get(symbol)
            kelly_analysis = self.kelly_optimizer.analyze_symbol_kelly(symbol)
            
            # Get EV analysis
            ev_analysis = self.ev_calculator.calculate_expected_value(symbol)
            
            # Get dynamic risk limits
            risk_adjustment = self.risk_manager.adjust_risk_limits(symbol)
            
            # Get position sizing from risk manager
            max_position_from_risk = self.risk_manager.get_position_size_limit(symbol, portfolio_value)
            
            # Determine recommended action
            action, position_size, rationale, warnings = self._determine_position_action(
                symbol, kelly_result, kelly_analysis, ev_analysis, risk_adjustment, 
                max_position_from_risk, portfolio_value
            )
            
            # Calculate stop loss and take profit levels if buying
            stop_loss_level = None
            take_profit_level = None
            current_price = 100.0  # Would get from live data
            
            if action in ['buy', 'strong_buy']:
                stop_loss_level = self.risk_manager.get_stop_loss_level(symbol, current_price)
                take_profit_level = self.risk_manager.get_take_profit_level(symbol, current_price)
            
            return EnhancedPositionRecommendation(
                symbol=symbol,
                recommended_action=action,
                position_size=position_size,
                percentage_of_portfolio=position_size / portfolio_value if portfolio_value > 0 else 0,
                risk_adjusted_size=min(position_size, max_position_from_risk),
                kelly_fraction=kelly_analysis.optimal_fraction,
                expected_value=ev_analysis.expected_value,
                ev_confidence=ev_analysis.confidence_level,
                dynamic_limits=risk_adjustment.recommended_limits,
                stop_loss_level=stop_loss_level,
                take_profit_level=take_profit_level,
                rationale=rationale,
                risk_warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Symbol analysis failed for {symbol}: {e}")
            # Return safe default
            return EnhancedPositionRecommendation(
                symbol=symbol,
                recommended_action='hold',
                position_size=0,
                percentage_of_portfolio=0,
                risk_adjusted_size=0,
                kelly_fraction=0,
                expected_value=0,
                ev_confidence=0,
                dynamic_limits=self.risk_manager.base_limits,
                stop_loss_level=None,
                take_profit_level=None,
                rationale="Analysis failed - holding position",
                risk_warnings=["Analysis error - conservative hold recommendation"]
            )
    
    def _determine_position_action(self, symbol: str, kelly_result: Optional[PositionSizeResult],
                                 kelly_analysis, ev_analysis, risk_adjustment: RiskAdjustment,
                                 max_position_from_risk: float, portfolio_value: float) -> Tuple[str, float, str, List[str]]:
        """Determine recommended action based on all analyses"""
        warnings = []
        
        # Default values
        action = 'hold'
        position_size = 0
        rationale = "Insufficient analysis data"
        
        try:
            # Check if we should enter position at all
            if not self.risk_manager.should_enter_position(symbol):
                return 'avoid', 0, "Risk manager blocks position entry", ["Position blocked by risk limits"]
            
            # Combine Kelly and EV recommendations
            kelly_recommendation = kelly_analysis.recommendation if kelly_analysis else 'hold'
            ev_recommendation = ev_analysis.recommendation if ev_analysis else 'hold'
            
            # Get position sizes
            kelly_position = kelly_result.recommended_size if kelly_result else 0
            ev_score = ev_analysis.expected_value if ev_analysis else 0
            
            # Decision logic combining all factors
            if (kelly_recommendation in ['strong_buy', 'buy'] and 
                ev_recommendation in ['strong_buy', 'buy'] and 
                ev_score > 0.03):  # 3% minimum expected value
                
                if kelly_recommendation == 'strong_buy' and ev_recommendation == 'strong_buy':
                    action = 'strong_buy'
                else:
                    action = 'buy'
                
                # Use the smaller of Kelly or risk-adjusted size for safety
                position_size = min(kelly_position, max_position_from_risk)
                
                rationale = f"Kelly: {kelly_recommendation}, EV: {ev_recommendation} " \
                           f"(EV: {ev_score:.3f}, Kelly fraction: {kelly_analysis.optimal_fraction:.3f})"
                
            elif (kelly_recommendation in ['buy', 'hold'] and 
                  ev_recommendation in ['buy', 'hold'] and 
                  ev_score > 0.01):  # 1% minimum for small position
                
                action = 'buy'
                position_size = min(kelly_position * 0.5, max_position_from_risk * 0.5)  # Half size for marginal opportunities
                rationale = f"Marginal opportunity - reduced position size"
                
            elif ev_score < -0.01 or kelly_analysis.expected_value < -0.01:
                action = 'avoid'
                rationale = f"Negative expected value detected"
                warnings.append("Negative expected value - avoid position")
                
            else:
                action = 'hold'
                rationale = f"Neutral signals - maintaining current position"
            
            # Add warnings based on risk analysis
            if risk_adjustment.confidence < 0.5:
                warnings.append("Low confidence in risk assessment")
            
            if kelly_analysis.risk_category in ['high', 'extreme']:
                warnings.append(f"High risk category: {kelly_analysis.risk_category}")
            
            if ev_analysis.probability_of_loss > 0.4:
                warnings.append(f"High loss probability: {ev_analysis.probability_of_loss:.1%}")
                
        except Exception as e:
            logger.error(f"Position decision failed for {symbol}: {e}")
            action = 'hold'
            rationale = "Decision analysis failed - holding position"
            warnings.append("Analysis error in position decision")
        
        return action, position_size, rationale, warnings
    
    def _calculate_portfolio_score(self, performance_metrics, kelly_summary, ev_rankings, recommendations) -> float:
        """Calculate overall portfolio health score (0-100)"""
        try:
            score = 50  # Base score
            
            # Performance component (30% weight)
            if performance_metrics.win_rate > 0.7:
                score += 15
            elif performance_metrics.win_rate > 0.6:
                score += 10
            elif performance_metrics.win_rate < 0.4:
                score -= 10
            
            if performance_metrics.sharpe_ratio > 2.0:
                score += 15
            elif performance_metrics.sharpe_ratio > 1.0:
                score += 10
            elif performance_metrics.sharpe_ratio < 0:
                score -= 15
            
            # Kelly optimization component (25% weight)
            if kelly_summary and kelly_summary.get('total_positions', 0) > 0:
                avg_kelly = kelly_summary.get('average_kelly_fraction', 0)
                if 0.05 <= avg_kelly <= 0.15:  # Sweet spot for Kelly
                    score += 12
                elif 0.02 <= avg_kelly <= 0.20:
                    score += 8
                else:
                    score -= 5
            
            # EV analysis component (25% weight)
            if ev_rankings:
                premium_pct = len([r for r in ev_rankings if r.tier == 'premium']) / len(ev_rankings)
                score += premium_pct * 15  # Up to 15 points for premium opportunities
                
                avg_ev_score = sum(r.ev_score for r in ev_rankings) / len(ev_rankings)
                if avg_ev_score > 20:
                    score += 10
                elif avg_ev_score < 5:
                    score -= 5
            
            # Risk management component (20% weight)
            buy_recommendations = len([r for r in recommendations if r.recommended_action in ['buy', 'strong_buy']])
            avoid_recommendations = len([r for r in recommendations if r.recommended_action == 'avoid'])
            
            if buy_recommendations > 0:
                score += min(10, buy_recommendations * 2)
            if avoid_recommendations > len(recommendations) * 0.3:  # Too many avoids
                score -= 10
                
            # Ensure score is within bounds
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Portfolio score calculation failed: {e}")
            return 50  # Neutral score on error
    
    def _assess_overall_risk_level(self, performance_metrics, recommendations) -> str:
        """Assess overall portfolio risk level"""
        try:
            risk_factors = 0
            
            # Performance-based risk
            if performance_metrics.win_rate < 0.45:
                risk_factors += 2
            if performance_metrics.max_drawdown > 0.15:
                risk_factors += 2
            if performance_metrics.sharpe_ratio < 0:
                risk_factors += 2
            
            # Position-based risk
            high_risk_positions = len([r for r in recommendations 
                                     if any('high' in w.lower() or 'extreme' in w.lower() 
                                           for w in r.risk_warnings)])
            if high_risk_positions > len(recommendations) * 0.3:
                risk_factors += 2
            
            # Large position risk
            large_positions = len([r for r in recommendations 
                                 if r.percentage_of_portfolio > 0.15])
            if large_positions > 2:
                risk_factors += 1
            
            # Classify risk level
            if risk_factors >= 6:
                return 'extreme'
            elif risk_factors >= 4:
                return 'high'
            elif risk_factors >= 2:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return 'medium'
    
    def _assess_rebalancing_needs(self, recommendations) -> bool:
        """Determine if portfolio needs rebalancing"""
        try:
            # Check for strong buy/sell signals
            strong_signals = len([r for r in recommendations 
                                if r.recommended_action in ['strong_buy', 'strong_sell']])
            
            # Check for large position adjustments
            large_adjustments = len([r for r in recommendations 
                                   if abs(r.position_size) > r.percentage_of_portfolio * 1000 * 0.05])  # 5% change
            
            return strong_signals > 0 or large_adjustments > len(recommendations) * 0.3
            
        except Exception as e:
            logger.error(f"Rebalancing assessment failed: {e}")
            return False
    
    def get_position_recommendations_summary(self) -> Dict:
        """Get summary of current position recommendations"""
        if not self.last_analysis:
            return {'error': 'No recent analysis available'}
        
        recommendations = self.last_analysis.position_adjustments
        
        summary = {
            'total_symbols_analyzed': len(recommendations),
            'buy_recommendations': len([r for r in recommendations if r.recommended_action == 'buy']),
            'strong_buy_recommendations': len([r for r in recommendations if r.recommended_action == 'strong_buy']),
            'hold_recommendations': len([r for r in recommendations if r.recommended_action == 'hold']),
            'avoid_recommendations': len([r for r in recommendations if r.recommended_action == 'avoid']),
            'total_warnings': sum(len(r.risk_warnings) for r in recommendations),
            'average_kelly_fraction': np.mean([r.kelly_fraction for r in recommendations]),
            'average_expected_value': np.mean([r.expected_value for r in recommendations]),
            'total_recommended_allocation': sum(r.percentage_of_portfolio for r in recommendations 
                                              if r.recommended_action in ['buy', 'strong_buy']),
            'top_recommendations': [
                {
                    'symbol': r.symbol,
                    'action': r.recommended_action,
                    'position_pct': r.percentage_of_portfolio,
                    'expected_value': r.expected_value,
                    'rationale': r.rationale
                }
                for r in sorted(recommendations, key=lambda x: x.expected_value, reverse=True)[:5]
            ],
            'analysis_timestamp': self.last_analysis.timestamp.isoformat()
        }
        
        return summary
    
    def execute_rebalancing(self, dry_run: bool = True) -> Dict:
        """Execute portfolio rebalancing based on recommendations"""
        if not self.last_analysis:
            return {'error': 'No analysis available for rebalancing'}
        
        if not self.last_analysis.rebalancing_needed:
            return {'message': 'No rebalancing needed based on current analysis'}
        
        try:
            execution_plan = []
            total_changes = 0
            
            for recommendation in self.last_analysis.position_adjustments:
                if recommendation.recommended_action in ['buy', 'strong_buy']:
                    execution_plan.append({
                        'action': 'buy',
                        'symbol': recommendation.symbol,
                        'amount': recommendation.risk_adjusted_size,
                        'percentage': recommendation.percentage_of_portfolio,
                        'rationale': recommendation.rationale,
                        'stop_loss': recommendation.stop_loss_level,
                        'take_profit': recommendation.take_profit_level
                    })
                    total_changes += recommendation.risk_adjusted_size
                elif recommendation.recommended_action == 'sell':
                    execution_plan.append({
                        'action': 'sell',
                        'symbol': recommendation.symbol,
                        'rationale': recommendation.rationale
                    })
            
            if dry_run:
                return {
                    'execution_plan': execution_plan,
                    'total_capital_changes': total_changes,
                    'execution_count': len(execution_plan),
                    'dry_run': True,
                    'message': 'Dry run complete - no actual trades executed'
                }
            else:
                # TODO: Implement actual trade execution via broker API
                logger.warning("Actual trade execution not yet implemented")
                return {
                    'message': 'Actual execution not implemented - use dry_run=True for planning',
                    'execution_plan': execution_plan
                }
                
        except Exception as e:
            logger.error(f"Rebalancing execution failed: {e}")
            return {'error': f'Rebalancing failed: {e}'}


# Global enhanced portfolio manager instance
_enhanced_portfolio_manager: Optional[EnhancedPortfolioManager] = None


def get_enhanced_portfolio_manager() -> EnhancedPortfolioManager:
    """Get the global enhanced portfolio manager instance"""
    global _enhanced_portfolio_manager
    if _enhanced_portfolio_manager is None:
        _enhanced_portfolio_manager = EnhancedPortfolioManager()
    return _enhanced_portfolio_manager


if __name__ == "__main__":
    # Test enhanced portfolio manager
    import numpy as np
    
    manager = EnhancedPortfolioManager()
    
    try:
        print("=== Enhanced Portfolio Manager Test ===")
        
        # Test comprehensive analysis
        symbols = ["NVDA", "MSFT", "GOOGL", "TSLA", "AMZN"]
        portfolio_value = 100000
        
        print(f"Analyzing portfolio with {len(symbols)} symbols...")
        health_report = manager.analyze_portfolio_with_risk_management(symbols, portfolio_value)
        
        print(f"\n📊 Portfolio Health Report:")
        print(f"   Overall Score: {health_report.overall_score:.1f}/100")
        print(f"   Performance Category: {health_report.performance_category}")
        print(f"   Risk Level: {health_report.risk_level}")
        print(f"   Rebalancing Needed: {health_report.rebalancing_needed}")
        
        print(f"\n🎯 Position Recommendations:")
        for rec in health_report.position_adjustments:
            print(f"   {rec.symbol}: {rec.recommended_action.upper()} "
                  f"${rec.position_size:.0f} ({rec.percentage_of_portfolio:.1%}) "
                  f"- EV: {rec.expected_value:.3f}")
            if rec.risk_warnings:
                print(f"      ⚠️  {'; '.join(rec.risk_warnings)}")
        
        print(f"\n📈 Performance Metrics:")
        perf = health_report.performance_metrics
        print(f"   Win Rate: {perf['win_rate']:.2%}")
        print(f"   Average Return: {perf['avg_return']:.3f}")
        print(f"   Sharpe Ratio: {perf['sharpe_ratio']:.2f}")
        print(f"   Total Trades: {perf['total_trades']}")
        
        # Get recommendations summary
        summary = manager.get_position_recommendations_summary()
        print(f"\n💡 Recommendations Summary:")
        print(f"   Buy Recommendations: {summary['buy_recommendations']}")
        print(f"   Strong Buy: {summary['strong_buy_recommendations']}")
        print(f"   Total Warnings: {summary['total_warnings']}")
        print(f"   Recommended Allocation: {summary['total_recommended_allocation']:.1%}")
        
        # Test dry run rebalancing
        rebalancing_result = manager.execute_rebalancing(dry_run=True)
        if 'execution_plan' in rebalancing_result:
            print(f"\n🔄 Rebalancing Plan:")
            for plan in rebalancing_result['execution_plan']:
                print(f"   {plan['action'].upper()} {plan['symbol']}: "
                      f"${plan.get('amount', 0):.0f} - {plan['rationale']}")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()