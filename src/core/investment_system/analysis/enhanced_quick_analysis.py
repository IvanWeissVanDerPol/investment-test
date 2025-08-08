"""
Enhanced Quick Analysis with Risk Management Integration
Combines technical analysis with Dynamic Risk Management, Kelly Criterion, and Expected Value
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import our enhanced portfolio manager
from ..portfolio.enhanced_portfolio_manager import get_enhanced_portfolio_manager, EnhancedPortfolioManager

logger = logging.getLogger(__name__)


def run_enhanced_quick_analysis(symbols: Optional[List[str]] = None, 
                               portfolio_value: Optional[float] = None,
                               config_file: str = "config/config.json") -> Dict[str, Any]:
    """
    Run enhanced quick analysis with integrated risk management
    
    Args:
        symbols: List of symbols to analyze (defaults to config targets)
        portfolio_value: Current portfolio value (gets from live data if None)
        config_file: Path to configuration file
    
    Returns:
        Comprehensive analysis results with risk management insights
    """
    try:
        logger.info("🚀 Starting Enhanced Quick Analysis with Risk Management")
        
        # Load configuration
        config = load_config(config_file)
        
        # Get symbols if not provided
        if not symbols:
            symbols = config.get('target_stocks', []) + config.get('ai_robotics_etfs', [])
            logger.info(f"📊 Analyzing {len(symbols)} symbols from config")
        
        # Initialize enhanced portfolio manager
        portfolio_manager = get_enhanced_portfolio_manager()
        
        # Run comprehensive analysis
        start_time = datetime.now()
        health_report = portfolio_manager.analyze_portfolio_with_risk_management(
            symbols=symbols,
            portfolio_value=portfolio_value
        )
        analysis_duration = (datetime.now() - start_time).total_seconds()
        
        # Get recommendations summary
        recommendations_summary = portfolio_manager.get_position_recommendations_summary()
        
        # Generate executive summary
        executive_summary = generate_executive_summary(health_report, recommendations_summary)
        
        # Create comprehensive results
        results = {
            'analysis_type': 'enhanced_quick_analysis',
            'timestamp': datetime.now().isoformat(),
            'analysis_duration_seconds': analysis_duration,
            'symbols_analyzed': symbols,
            'portfolio_value': portfolio_value,
            
            # Executive Summary
            'executive_summary': executive_summary,
            
            # Portfolio Health
            'portfolio_health': {
                'overall_score': health_report.overall_score,
                'performance_category': health_report.performance_category,
                'risk_level': health_report.risk_level,
                'rebalancing_needed': health_report.rebalancing_needed,
                'total_warnings': sum(len(r.risk_warnings) for r in health_report.position_adjustments)
            },
            
            # Performance Metrics
            'performance_metrics': health_report.performance_metrics,
            
            # Position Recommendations
            'position_recommendations': [
                {
                    'symbol': rec.symbol,
                    'action': rec.recommended_action,
                    'position_size': rec.position_size,
                    'percentage': rec.percentage_of_portfolio,
                    'kelly_fraction': rec.kelly_fraction,
                    'expected_value': rec.expected_value,
                    'ev_confidence': rec.ev_confidence,
                    'rationale': rec.rationale,
                    'risk_warnings': rec.risk_warnings,
                    'stop_loss': rec.stop_loss_level,
                    'take_profit': rec.take_profit_level
                }
                for rec in health_report.position_adjustments
            ],
            
            # Risk Management Summary
            'risk_management': health_report.risk_summary,
            
            # Kelly Optimization Summary
            'kelly_optimization': health_report.kelly_optimization_summary,
            
            # Expected Value Summary
            'expected_value_analysis': health_report.ev_analysis_summary,
            
            # Recommendations Summary
            'recommendations_summary': recommendations_summary,
            
            # Top Opportunities
            'top_opportunities': recommendations_summary.get('top_recommendations', []),
            
            # Action Items
            'immediate_actions': generate_immediate_actions(health_report),
            
            # Risk Alerts
            'risk_alerts': generate_risk_alerts(health_report),
            
            # Next Steps
            'next_steps': generate_next_steps(health_report)
        }
        
        logger.info(f"✅ Enhanced Quick Analysis Complete - Score: {health_report.overall_score:.1f}/100 "
                   f"({analysis_duration:.1f}s)")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Enhanced quick analysis failed: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'enhanced_quick_analysis_failed'
        }


def load_config(config_file: str) -> Dict:
    """Load configuration file"""
    try:
        config_path = Path(config_file)
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config {config_file}: {e}")
        return {}


def generate_executive_summary(health_report, recommendations_summary) -> Dict[str, str]:
    """Generate executive summary of analysis results"""
    try:
        # Overall assessment
        score = health_report.overall_score
        category = health_report.performance_category
        risk_level = health_report.risk_level
        
        # Key metrics
        win_rate = health_report.performance_metrics.get('win_rate', 0)
        sharpe_ratio = health_report.performance_metrics.get('sharpe_ratio', 0)
        buy_count = recommendations_summary.get('buy_recommendations', 0)
        strong_buy_count = recommendations_summary.get('strong_buy_recommendations', 0)
        
        # Generate summary text
        if score >= 80:
            assessment = "🟢 **EXCELLENT** - Portfolio is performing very well"
        elif score >= 65:
            assessment = "🔵 **GOOD** - Portfolio shows solid performance"
        elif score >= 50:
            assessment = "🟡 **AVERAGE** - Portfolio performance is moderate"
        elif score >= 35:
            assessment = "🟠 **BELOW AVERAGE** - Portfolio needs attention"
        else:
            assessment = "🔴 **POOR** - Immediate portfolio review required"
        
        # Risk assessment
        if risk_level == 'low':
            risk_summary = "Risk levels are well-controlled"
        elif risk_level == 'medium':
            risk_summary = "Risk levels are acceptable but should be monitored"
        elif risk_level == 'high':
            risk_summary = "⚠️ Elevated risk levels detected"
        else:
            risk_summary = "🚨 High risk situation requires immediate attention"
        
        # Opportunities
        if strong_buy_count > 0:
            opportunity_summary = f"🎯 {strong_buy_count} strong buy opportunities identified"
        elif buy_count > 0:
            opportunity_summary = f"📈 {buy_count} buy opportunities available"
        else:
            opportunity_summary = "Current market conditions suggest holding positions"
        
        return {
            'overall_assessment': assessment,
            'performance_summary': f"Performance category: {category.upper()} (Win rate: {win_rate:.1%}, Sharpe: {sharpe_ratio:.2f})",
            'risk_summary': risk_summary,
            'opportunity_summary': opportunity_summary,
            'rebalancing_status': "🔄 Rebalancing recommended" if health_report.rebalancing_needed else "✅ Portfolio allocation is appropriate"
        }
        
    except Exception as e:
        logger.error(f"Executive summary generation failed: {e}")
        return {
            'overall_assessment': "Analysis summary unavailable due to error",
            'error': str(e)
        }


def generate_immediate_actions(health_report) -> List[str]:
    """Generate list of immediate action items"""
    actions = []
    
    try:
        # Check for urgent risk issues
        if health_report.risk_level == 'extreme':
            actions.append("🚨 URGENT: Review and reduce position sizes immediately")
        
        # Check for strong buy signals
        strong_buys = [r for r in health_report.position_adjustments 
                      if r.recommended_action == 'strong_buy']
        if strong_buys:
            actions.append(f"🎯 Consider strong buy positions: {', '.join([r.symbol for r in strong_buys[:3]])}")
        
        # Check for positions to avoid
        avoid_positions = [r for r in health_report.position_adjustments 
                          if r.recommended_action == 'avoid']
        if avoid_positions:
            actions.append(f"⚠️ Avoid these positions: {', '.join([r.symbol for r in avoid_positions])}")
        
        # Check for rebalancing needs
        if health_report.rebalancing_needed:
            actions.append("🔄 Execute portfolio rebalancing based on recommendations")
        
        # Check performance issues
        if health_report.performance_metrics.get('win_rate', 0) < 0.4:
            actions.append("📉 Review trading strategy - win rate below 40%")
        
        # Check for high-warning positions
        high_warning_positions = [r for r in health_report.position_adjustments 
                                 if len(r.risk_warnings) > 2]
        if high_warning_positions:
            actions.append(f"⚠️ Review high-risk positions: {', '.join([r.symbol for r in high_warning_positions])}")
        
        # Default action if no specific actions
        if not actions:
            actions.append("✅ Continue monitoring current positions")
            
    except Exception as e:
        logger.error(f"Immediate actions generation failed: {e}")
        actions.append("⚠️ Review analysis results manually due to processing error")
    
    return actions


def generate_risk_alerts(health_report) -> List[str]:
    """Generate risk alerts based on analysis"""
    alerts = []
    
    try:
        # Overall risk level alerts
        if health_report.risk_level in ['high', 'extreme']:
            alerts.append(f"🚨 Portfolio risk level: {health_report.risk_level.upper()}")
        
        # Performance alerts
        perf = health_report.performance_metrics
        if perf.get('max_drawdown', 0) > 0.15:
            alerts.append(f"📉 High drawdown detected: {perf['max_drawdown']:.1%}")
        
        if perf.get('sharpe_ratio', 0) < 0:
            alerts.append("📊 Negative Sharpe ratio indicates poor risk-adjusted returns")
        
        # Position-specific alerts
        for rec in health_report.position_adjustments:
            if rec.risk_warnings:
                for warning in rec.risk_warnings[:2]:  # Limit to top 2 warnings
                    alerts.append(f"⚠️ {rec.symbol}: {warning}")
        
        # Concentration risk
        large_positions = [r for r in health_report.position_adjustments 
                          if r.percentage_of_portfolio > 0.2]  # 20%+ positions
        if large_positions:
            alerts.append(f"🎯 High concentration in: {', '.join([r.symbol for r in large_positions])}")
            
    except Exception as e:
        logger.error(f"Risk alerts generation failed: {e}")
        alerts.append("⚠️ Risk assessment incomplete due to processing error")
    
    return alerts


def generate_next_steps(health_report) -> List[str]:
    """Generate next steps recommendations"""
    steps = []
    
    try:
        # Based on performance category
        if health_report.performance_category in ['excellent', 'good']:
            steps.append("🚀 Consider increasing position sizes within risk limits")
            steps.append("📊 Monitor performance for continued optimization")
        elif health_report.performance_category == 'average':
            steps.append("🎯 Focus on higher expected value opportunities")
            steps.append("🔍 Review and adjust trading strategy")
        else:  # poor, bad
            steps.append("🛡️ Reduce position sizes and focus on risk management")
            steps.append("📚 Review recent trades for improvement opportunities")
        
        # Based on EV analysis
        ev_summary = health_report.ev_analysis_summary
        if ev_summary.get('premium_tier_count', 0) > 0:
            steps.append(f"⭐ Prioritize {ev_summary['premium_tier_count']} premium-tier opportunities")
        
        # Based on Kelly optimization
        kelly_summary = health_report.kelly_optimization_summary
        if kelly_summary.get('total_positions', 0) > 0:
            steps.append("📐 Apply Kelly Criterion position sizing for optimal growth")
        
        # Regular monitoring steps
        steps.append("📅 Schedule next portfolio review in 1-2 weeks")
        steps.append("🔄 Update analysis after significant market moves")
        
    except Exception as e:
        logger.error(f"Next steps generation failed: {e}")
        steps.append("📋 Review analysis results and plan follow-up actions")
    
    return steps


def print_analysis_summary(results: Dict[str, Any]) -> None:
    """Print a formatted summary of analysis results"""
    try:
        print("\n" + "="*80)
        print("🚀 ENHANCED INVESTMENT ANALYSIS SUMMARY")
        print("="*80)
        
        # Executive Summary
        if 'executive_summary' in results:
            summary = results['executive_summary']
            print(f"\n📋 EXECUTIVE SUMMARY:")
            print(f"   {summary.get('overall_assessment', 'N/A')}")
            print(f"   {summary.get('performance_summary', 'N/A')}")
            print(f"   {summary.get('risk_summary', 'N/A')}")
            print(f"   {summary.get('opportunity_summary', 'N/A')}")
            print(f"   {summary.get('rebalancing_status', 'N/A')}")
        
        # Portfolio Health
        if 'portfolio_health' in results:
            health = results['portfolio_health']
            print(f"\n📊 PORTFOLIO HEALTH:")
            print(f"   Overall Score: {health.get('overall_score', 0):.1f}/100")
            print(f"   Performance Category: {health.get('performance_category', 'N/A').upper()}")
            print(f"   Risk Level: {health.get('risk_level', 'N/A').upper()}")
            print(f"   Rebalancing Needed: {'YES' if health.get('rebalancing_needed') else 'NO'}")
        
        # Top Opportunities
        if 'top_opportunities' in results and results['top_opportunities']:
            print(f"\n🎯 TOP OPPORTUNITIES:")
            for i, opp in enumerate(results['top_opportunities'][:3], 1):
                action = opp.get('action', 'N/A').upper()
                symbol = opp.get('symbol', 'N/A')
                ev = opp.get('expected_value', 0)
                pct = opp.get('position_pct', 0)
                print(f"   {i}. {action} {symbol}: {ev:.3f} EV, {pct:.1%} allocation")
        
        # Immediate Actions
        if 'immediate_actions' in results:
            print(f"\n⚡ IMMEDIATE ACTIONS:")
            for action in results['immediate_actions'][:5]:
                print(f"   • {action}")
        
        # Risk Alerts
        if 'risk_alerts' in results and results['risk_alerts']:
            print(f"\n🚨 RISK ALERTS:")
            for alert in results['risk_alerts'][:5]:
                print(f"   • {alert}")
        
        # Analysis Stats
        duration = results.get('analysis_duration_seconds', 0)
        timestamp = results.get('timestamp', 'N/A')
        print(f"\n📈 ANALYSIS STATS:")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Timestamp: {timestamp}")
        print(f"   Symbols Analyzed: {len(results.get('symbols_analyzed', []))}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        logger.error(f"Summary printing failed: {e}")
        print(f"Error printing summary: {e}")


def main():
    """Run enhanced quick analysis with default settings"""
    try:
        # Run the analysis
        results = run_enhanced_quick_analysis()
        
        # Print summary
        print_analysis_summary(results)
        
        # Save results (optional)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"reports/enhanced_quick_analysis_{timestamp}.json"
        
        try:
            Path("reports").mkdir(exist_ok=True)
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {results_file}")
        except Exception as e:
            logger.warning(f"Failed to save results: {e}")
        
        return results
        
    except Exception as e:
        logger.error(f"Enhanced quick analysis failed: {e}")
        print(f"\n❌ Analysis failed: {e}")
        return {}


if __name__ == "__main__":
    main()