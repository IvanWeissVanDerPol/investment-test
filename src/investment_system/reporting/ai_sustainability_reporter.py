"""
AI-Powered Sustainability Reporter
Generates comprehensive daily reports combining ethics analysis with AI insights
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..ai.investment_decision_engine import AIInvestmentDecisionEngine
from ..integrations.ethics_integration import EthicsIntegratedAnalyzer
from ..utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class AISustainabilityReporter:
    """
    AI-powered sustainability reporting system that generates:
    - Daily portfolio sustainability reports
    - Green investment opportunity reports
    - Ethics compliance tracking
    - AI-enhanced market analysis
    """
    
    def __init__(self, config_path: str = "config"):
        """Initialize the AI sustainability reporter"""
        
        self.ai_engine = AIInvestmentDecisionEngine(config_path)
        self.ethics_analyzer = EthicsIntegratedAnalyzer(config_path)
        self.cache_manager = CacheManager()
        
        self.config_path = Path(config_path)
        self.reports_dir = Path("reports/sustainability")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Load reporting configuration
        self.load_reporting_config()
        
        logger.info("AI Sustainability Reporter initialized")
    
    def load_reporting_config(self):
        """Load reporting configuration"""
        config_file = self.config_path / "config.json"
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            self.reporting_config = config.get("reporting_preferences", {
                "include_ai_analysis": True,
                "include_market_context": True,
                "include_alternatives": True,
                "daily_summary_enabled": True,
                "detailed_analysis_enabled": True
            })
            
            self.user_profile = config.get("user_profile", {})
            
        except Exception as e:
            logger.error(f"Failed to load reporting config: {e}")
            # Use defaults
            self.reporting_config = {
                "include_ai_analysis": True,
                "include_market_context": True,
                "include_alternatives": True,
                "daily_summary_enabled": True,
                "detailed_analysis_enabled": True
            }
            self.user_profile = {"name": "Ivan", "balance": 900}
    
    def generate_daily_sustainability_report(self, portfolio_positions: List[Dict]) -> Dict:
        """Generate comprehensive daily sustainability report"""
        
        logger.info("Generating daily sustainability report")
        
        # Date for report
        report_date = datetime.now()
        
        # Run comprehensive analysis
        ethics_analysis = self.ethics_analyzer.screen_portfolio_comprehensive(portfolio_positions)
        ai_portfolio_analysis = self.ai_engine.analyze_portfolio_decisions(portfolio_positions)
        
        # Build portfolio context
        portfolio_context = self.ai_engine._build_portfolio_context(portfolio_positions)
        
        # Get green recommendations
        green_recommendations = self.ai_engine.get_green_investment_recommendations(
            portfolio_context, budget=200
        )
        
        # Get market analysis if AI available
        market_analysis = None
        if self.ai_engine.claude_client.is_available():
            market_analysis = self.ai_engine.claude_client.analyze_market_conditions()
        
        # Compile comprehensive report
        report = {
            "report_metadata": {
                "report_date": report_date.isoformat(),
                "report_type": "daily_sustainability_report",
                "portfolio_positions": len(portfolio_positions),
                "ai_analysis_available": self.ai_engine.claude_client.is_available()
            },
            
            "executive_summary": self._generate_executive_summary(
                ethics_analysis, ai_portfolio_analysis, portfolio_context
            ),
            
            "sustainability_metrics": self._extract_sustainability_metrics(ethics_analysis),
            
            "portfolio_analysis": {
                "ethics_screening": ethics_analysis,
                "ai_decisions": ai_portfolio_analysis,
                "allocation_analysis": ethics_analysis.get("allocation_analysis", {})
            },
            
            "green_opportunities": {
                "top_recommendations": green_recommendations,
                "budget_allocation": self._calculate_green_budget_allocation(portfolio_context),
                "sector_analysis": self._analyze_green_sectors(green_recommendations)
            },
            
            "compliance_tracking": {
                "ethics_compliance": ethics_analysis.get("ethics_compliance", {}),
                "target_tracking": self._track_sustainability_targets(ethics_analysis),
                "improvement_areas": self._identify_improvement_areas(ethics_analysis)
            },
            
            "ai_insights": self._generate_ai_insights(ai_portfolio_analysis, market_analysis),
            
            "action_plan": self._generate_daily_action_plan(
                ethics_analysis, ai_portfolio_analysis, green_recommendations
            )
        }
        
        # Save report
        self._save_report(report, "daily_sustainability")
        
        logger.info(f"Daily sustainability report generated successfully")
        
        return report
    
    def _generate_executive_summary(self, ethics_analysis: Dict, ai_analysis: Dict, portfolio_context: Dict) -> Dict:
        """Generate executive summary of portfolio sustainability"""
        
        # Key metrics
        total_value = portfolio_context.get("total_value", 0)
        green_allocation = ethics_analysis.get("allocation_analysis", {}).get("green_value_percent", 0)
        compliance_score = ethics_analysis.get("ethics_compliance", {}).get("score", 0)
        sustainability_rating = ethics_analysis.get("sustainability_rating", "Unknown")
        
        # Decision summary
        ai_summary = ai_analysis.get("summary", {})
        
        # Key insights
        key_insights = []
        
        if green_allocation < 0.30:
            gap = 0.30 - green_allocation
            key_insights.append(f"Green allocation {gap:.1%} below 30% target - opportunity for sustainable growth")
        
        if compliance_score < 0.70:
            key_insights.append("Ethics compliance below threshold - immediate action required")
        
        blocked_count = len(ethics_analysis.get("blocked", []))
        if blocked_count > 0:
            key_insights.append(f"{blocked_count} blocked holdings require divestment")
        
        if ai_summary.get("strong_buys", 0) > 0:
            key_insights.append(f"AI identified {ai_summary['strong_buys']} strong buy opportunities")
        
        return {
            "portfolio_value": total_value,
            "sustainability_rating": sustainability_rating,
            "green_allocation": f"{green_allocation:.1%}",
            "green_target": "30.0%",
            "compliance_score": f"{compliance_score:.1%}",
            "compliance_grade": ethics_analysis.get("ethics_compliance", {}).get("grade", "N/A"),
            "key_insights": key_insights,
            "immediate_actions_required": blocked_count > 0 or compliance_score < 0.70,
            "ai_analysis_summary": {
                "total_analyzed": ai_summary.get("total_analyzed", 0),
                "buy_recommendations": ai_summary.get("strong_buys", 0) + ai_summary.get("buys", 0),
                "sell_recommendations": ai_summary.get("sells", 0),
                "hold_recommendations": ai_summary.get("holds", 0)
            }
        }
    
    def _extract_sustainability_metrics(self, ethics_analysis: Dict) -> Dict:
        """Extract key sustainability metrics"""
        
        allocation = ethics_analysis.get("allocation_analysis", {})
        
        return {
            "green_technology_allocation": allocation.get("green_value_percent", 0),
            "mission_critical_allocation": allocation.get("mission_critical_value_percent", 0),
            "priority_green_allocation": allocation.get("priority_value_percent", 0),
            "blocked_allocation": allocation.get("blocked_value_percent", 0),
            
            "sustainability_counts": {
                "mission_critical_stocks": len(ethics_analysis.get("mission_critical", [])),
                "priority_green_stocks": len(ethics_analysis.get("priority", [])),
                "preferred_sustainable": len(ethics_analysis.get("preferred", [])),
                "blocked_stocks": len(ethics_analysis.get("blocked", []))
            },
            
            "category_breakdown": allocation.get("category_breakdown", {}),
            
            "target_progress": {
                "green_target": 0.30,
                "current_green": allocation.get("green_value_percent", 0),
                "gap_to_target": max(0, 0.30 - allocation.get("green_value_percent", 0)),
                "target_achievement": min(1.0, allocation.get("green_value_percent", 0) / 0.30)
            }
        }
    
    def _calculate_green_budget_allocation(self, portfolio_context: Dict) -> Dict:
        """Calculate optimal green investment budget allocation"""
        
        total_value = portfolio_context.get("total_value", 900)
        current_green = portfolio_context.get("green_allocation", 0)
        target_green = 0.30
        
        # Calculate funding needed to reach target
        gap = max(0, target_green - current_green)
        target_investment = total_value * gap
        
        # Suggest allocation strategy
        allocation_strategy = {}
        
        if target_investment > 0:
            allocation_strategy = {
                "immediate_investment_needed": target_investment,
                "mission_critical_allocation": target_investment * 0.60,  # 60% to mission critical
                "priority_green_allocation": target_investment * 0.30,    # 30% to priority
                "preferred_allocation": target_investment * 0.10,         # 10% to preferred
                
                "suggested_timeline": "immediate" if gap > 0.15 else "gradual",
                "priority_level": "high" if gap > 0.15 else "medium"
            }
        
        return allocation_strategy
    
    def _analyze_green_sectors(self, green_recommendations: List[Dict]) -> Dict:
        """Analyze green investment opportunities by sector"""
        
        sector_analysis = {
            "renewable_energy": {"count": 0, "avg_score": 0, "top_pick": None},
            "electric_vehicles": {"count": 0, "avg_score": 0, "top_pick": None},
            "water_conservation": {"count": 0, "avg_score": 0, "top_pick": None},
            "energy_storage": {"count": 0, "avg_score": 0, "top_pick": None},
            "clean_technology": {"count": 0, "avg_score": 0, "top_pick": None}
        }
        
        # Group recommendations by sector
        sector_groups = {}
        for rec in green_recommendations:
            category = rec.get("category", "").replace("_", " ").title()
            if category not in sector_groups:
                sector_groups[category] = []
            sector_groups[category].append(rec)
        
        # Calculate sector metrics
        for category, recs in sector_groups.items():
            category_key = category.lower().replace(" ", "_")
            if category_key in sector_analysis:
                sector_analysis[category_key]["count"] = len(recs)
                sector_analysis[category_key]["avg_score"] = sum(r["final_score"] for r in recs) / len(recs)
                sector_analysis[category_key]["top_pick"] = max(recs, key=lambda x: x["final_score"])["symbol"]
        
        return sector_analysis
    
    def _track_sustainability_targets(self, ethics_analysis: Dict) -> Dict:
        """Track progress toward sustainability targets"""
        
        allocation = ethics_analysis.get("allocation_analysis", {})
        
        targets = {
            "green_allocation": {
                "target": 0.30,
                "current": allocation.get("green_value_percent", 0),
                "status": "on_track" if allocation.get("green_value_percent", 0) >= 0.25 else "behind"
            },
            "mission_critical": {
                "target": 0.20,
                "current": allocation.get("mission_critical_value_percent", 0),
                "status": "on_track" if allocation.get("mission_critical_value_percent", 0) >= 0.15 else "behind"
            },
            "blocked_elimination": {
                "target": 0.00,
                "current": allocation.get("blocked_value_percent", 0),
                "status": "achieved" if allocation.get("blocked_value_percent", 0) == 0 else "needs_action"
            },
            "ethics_compliance": {
                "target": 0.90,
                "current": ethics_analysis.get("ethics_compliance", {}).get("score", 0),
                "status": "excellent" if ethics_analysis.get("ethics_compliance", {}).get("score", 0) >= 0.90 else "needs_improvement"
            }
        }
        
        return targets
    
    def _identify_improvement_areas(self, ethics_analysis: Dict) -> List[Dict]:
        """Identify specific areas for sustainability improvement"""
        
        improvements = []
        allocation = ethics_analysis.get("allocation_analysis", {})
        
        # Green allocation improvement
        green_current = allocation.get("green_value_percent", 0)
        if green_current < 0.30:
            improvements.append({
                "area": "Green Technology Allocation",
                "current": f"{green_current:.1%}",
                "target": "30.0%",
                "priority": "high" if green_current < 0.20 else "medium",
                "action": f"Increase green investments by {(0.30 - green_current) * allocation.get('total_value', 900):.0f}"
            })
        
        # Mission critical improvement
        mission_current = allocation.get("mission_critical_value_percent", 0)
        if mission_current < 0.20:
            improvements.append({
                "area": "Mission Critical Earth Preservation",
                "current": f"{mission_current:.1%}",
                "target": "20.0%",
                "priority": "high",
                "action": "Add mission-critical green stocks (FSLR, ICLN, XYL, VWDRY, EOSE)"
            })
        
        # Blocked holdings
        blocked = ethics_analysis.get("blocked", [])
        if blocked:
            improvements.append({
                "area": "Ethics Compliance",
                "current": f"{len(blocked)} blocked holdings",
                "target": "0 blocked holdings",
                "priority": "urgent",
                "action": f"Divest from {', '.join([b['symbol'] for b in blocked])}"
            })
        
        return improvements
    
    def _generate_ai_insights(self, ai_analysis: Dict, market_analysis: Optional[Dict]) -> Dict:
        """Generate AI-powered insights"""
        
        insights = {
            "ai_available": self.ai_engine.claude_client.is_available(),
            "portfolio_insights": [],
            "market_insights": [],
            "strategic_recommendations": []
        }
        
        if ai_analysis:
            summary = ai_analysis.get("summary", {})
            
            # Portfolio insights
            if summary.get("strong_buys", 0) > 0:
                insights["portfolio_insights"].append(
                    f"AI identifies {summary['strong_buys']} strong buy opportunities in current holdings"
                )
            
            if summary.get("sells", 0) > 0:
                insights["portfolio_insights"].append(
                    f"AI recommends selling {summary['sells']} positions for portfolio optimization"
                )
            
            # Strategic recommendations
            insights["strategic_recommendations"].extend([
                "Focus on mission-critical green investments for maximum sustainability impact",
                "Consider gradual rebalancing to achieve 30% green allocation target",
                "Monitor AI recommendations daily for optimal entry/exit timing"
            ])
        
        if market_analysis and self.ai_engine.claude_client.is_available():
            insights["market_insights"].append("AI market analysis integrated for enhanced decision making")
        else:
            insights["market_insights"].append("Enable Claude API for AI-powered market insights")
        
        return insights
    
    def _generate_daily_action_plan(self, ethics_analysis: Dict, ai_analysis: Dict, green_recommendations: List[Dict]) -> Dict:
        """Generate specific daily action plan"""
        
        action_plan = {
            "immediate_actions": [],
            "this_week": [],
            "this_month": [],
            "priority_investments": []
        }
        
        # Immediate actions from ethics analysis
        blocked = ethics_analysis.get("blocked", [])
        for blocked_item in blocked:
            action_plan["immediate_actions"].append({
                "action": f"SELL {blocked_item['symbol']}",
                "reason": blocked_item["concerns"][0]["reason"],
                "priority": "URGENT",
                "timeline": "Today"
            })
        
        # Green investment actions
        if green_recommendations:
            top_green = green_recommendations[0]
            action_plan["immediate_actions"].append({
                "action": f"RESEARCH {top_green['symbol']}",
                "reason": f"Top green opportunity: {top_green['reason'][:50]}...",
                "priority": "HIGH",
                "timeline": "Today"
            })
        
        # Weekly actions
        allocation = ethics_analysis.get("allocation_analysis", {})
        if allocation.get("green_value_percent", 0) < 0.30:
            action_plan["this_week"].append({
                "action": "Increase green allocation",
                "details": f"Target ${(0.30 - allocation.get('green_value_percent', 0)) * allocation.get('total_value', 900):.0f} investment",
                "priority": "HIGH"
            })
        
        # Monthly actions
        action_plan["this_month"].extend([
            {
                "action": "Review portfolio sustainability metrics",
                "details": "Comprehensive monthly sustainability assessment",
                "priority": "MEDIUM"
            },
            {
                "action": "Evaluate new green investment opportunities",
                "details": "Research emerging sustainable technologies and companies",
                "priority": "MEDIUM"
            }
        ])
        
        # Priority investments
        for rec in green_recommendations[:3]:
            action_plan["priority_investments"].append({
                "symbol": rec["symbol"],
                "recommendation": rec["recommendation"],
                "esg_score": rec["esg_score"],
                "reason": rec["reason"]
            })
        
        return action_plan
    
    def _save_report(self, report: Dict, report_type: str):
        """Save report to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}.json"
        filepath = self.reports_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Report saved: {filepath}")
            
            # Also save a latest copy
            latest_filepath = self.reports_dir / f"{report_type}_latest.json"
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
    
    def generate_formatted_report(self, portfolio_positions: List[Dict]) -> str:
        """Generate human-readable formatted report"""
        
        report_data = self.generate_daily_sustainability_report(portfolio_positions)
        
        # Format for display
        formatted_report = f"""
================================================================================
IVAN'S DAILY AI SUSTAINABILITY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

[EXECUTIVE SUMMARY]
Portfolio Value: ${report_data['executive_summary']['portfolio_value']:.0f}
Sustainability Rating: {report_data['executive_summary']['sustainability_rating']}
Green Allocation: {report_data['executive_summary']['green_allocation']} (Target: {report_data['executive_summary']['green_target']})
Ethics Compliance: {report_data['executive_summary']['compliance_grade']} ({report_data['executive_summary']['compliance_score']})

[KEY INSIGHTS]
"""
        
        for insight in report_data['executive_summary']['key_insights']:
            formatted_report += f"• {insight}\n"
        
        formatted_report += f"""
[SUSTAINABILITY METRICS]
Mission Critical: {report_data['sustainability_metrics']['mission_critical_allocation']:.1%}
Priority Green: {report_data['sustainability_metrics']['priority_green_allocation']:.1%}
Blocked Holdings: {report_data['sustainability_metrics']['blocked_allocation']:.1%}

Green Target Progress: {report_data['sustainability_metrics']['target_progress']['target_achievement']:.1%} complete

[AI ANALYSIS SUMMARY]
"""
        
        if report_data['report_metadata']['ai_analysis_available']:
            ai_summary = report_data['executive_summary']['ai_analysis_summary']
            formatted_report += f"Buy Recommendations: {ai_summary['buy_recommendations']}\n"
            formatted_report += f"Sell Recommendations: {ai_summary['sell_recommendations']}\n"
            formatted_report += f"Hold Recommendations: {ai_summary['hold_recommendations']}\n"
        else:
            formatted_report += "Claude API not configured - Enable for AI-powered insights\n"
        
        formatted_report += f"""
[TOP GREEN OPPORTUNITIES]
"""
        
        for i, opp in enumerate(report_data['green_opportunities']['top_recommendations'][:3], 1):
            formatted_report += f"{i}. {opp['symbol']} - {opp['recommendation']} (ESG: {opp['esg_score']}/10)\n"
            formatted_report += f"   Category: {opp['category'].replace('_', ' ').title()}\n"
        
        formatted_report += f"""
[IMMEDIATE ACTION ITEMS]
"""
        
        for action in report_data['action_plan']['immediate_actions']:
            formatted_report += f"• {action['action']} - {action['reason']} [{action['priority']}]\n"
        
        formatted_report += f"""
================================================================================
Report saved to: reports/sustainability/daily_sustainability_latest.json
Run daily for optimal portfolio sustainability tracking
================================================================================
"""
        
        return formatted_report
    
    def generate_weekly_summary(self) -> Dict:
        """Generate weekly sustainability summary"""
        
        # This would analyze trends over the past week
        # For now, return a placeholder structure
        
        return {
            "report_type": "weekly_sustainability_summary",
            "week_ending": datetime.now().isoformat(),
            "sustainability_trends": {
                "green_allocation_change": "+2.5%",
                "compliance_score_change": "+5%",
                "new_green_investments": 2
            },
            "performance_summary": {
                "best_performer": "FSLR",
                "most_sustainable": "VWDRY",
                "needs_attention": "Review blocked holdings"
            }
        }

def main():
    """Test the AI Sustainability Reporter"""
    
    print("="*80)
    print("TESTING AI SUSTAINABILITY REPORTER")
    print("="*80)
    
    # Initialize reporter
    reporter = AISustainabilityReporter()
    
    # Test portfolio
    test_portfolio = [
        {"symbol": "FSLR", "value": 150, "shares": 1},    # Mission critical
        {"symbol": "TSLA", "value": 200, "shares": 1},    # Blocked
        {"symbol": "MSFT", "value": 180, "shares": 1},    # Standard
        {"symbol": "ICLN", "value": 120, "shares": 1},    # Mission critical ETF
        {"symbol": "RIVN", "value": 150, "shares": 1},    # Priority green
        {"symbol": "AAPL", "value": 100, "shares": 1}     # Standard
    ]
    
    print(f"\nGenerating daily sustainability report for {len(test_portfolio)} positions...")
    
    # Generate formatted report
    formatted_report = reporter.generate_formatted_report(test_portfolio)
    
    print(formatted_report)
    
    print("\n[SUCCESS] AI Sustainability Reporter testing complete!")

if __name__ == "__main__":
    main()