"""
Ethics Integration Module
Integrates the enhanced ethics system into the main investment workflow
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from ..ethics.investment_blacklist import InvestmentBlacklistManager
from ..utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class EthicsIntegratedAnalyzer:
    """
    Integrates ethics screening into all investment analysis workflows
    """
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.ethics_manager = InvestmentBlacklistManager(config_path)
        self.cache_manager = CacheManager()
        
        # Load ethics preferences from config
        self.load_ethics_config()
        
        logger.info("Ethics Integration initialized with enhanced green technology focus")
        
    def load_ethics_config(self):
        """Load ethics preferences from configuration"""
        config_file = self.config_path / "config.json"
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            self.ethics_preferences = config.get("ethics_preferences", {})
            self.green_targets = config.get("green_investment_targets", [])
            self.target_green_allocation = config.get("user_profile", {}).get("target_green_allocation_percent", 30) / 100
            
            logger.info(f"Loaded ethics config - Green target: {self.target_green_allocation:.1%}")
            
        except Exception as e:
            logger.error(f"Failed to load ethics config: {e}")
            # Use defaults
            self.ethics_preferences = {
                "enable_ethics_screening": True,
                "prioritize_green_investments": True,
                "minimum_esg_score": 7.0
            }
            self.target_green_allocation = 0.30
    
    def screen_investment_with_context(self, symbol: str, portfolio_context: Optional[Dict] = None) -> Dict:
        """
        Enhanced investment screening with portfolio context
        """
        # Basic ethics screening
        ethics_result = self.ethics_manager.check_investment(symbol)
        
        # Add portfolio context analysis
        if portfolio_context:
            ethics_result = self._enhance_with_portfolio_context(ethics_result, symbol, portfolio_context)
        
        # Add priority recommendations based on current allocations
        ethics_result = self._add_allocation_recommendations(ethics_result, symbol, portfolio_context)
        
        # Cache result for performance
        cache_key = f"ethics_screen_{symbol}_{datetime.now().strftime('%Y%m%d')}"
        self.cache_manager.cache_data("ethics", cache_key, ethics_result)
        
        return ethics_result
    
    def _enhance_with_portfolio_context(self, ethics_result: Dict, symbol: str, portfolio_context: Dict) -> Dict:
        """Add portfolio-specific insights to ethics screening"""
        
        current_green_allocation = portfolio_context.get("green_allocation", 0)
        current_ai_allocation = portfolio_context.get("ai_allocation", 0)
        total_value = portfolio_context.get("total_value", 900)
        
        # Add portfolio fit analysis
        portfolio_fit = {
            "current_green_allocation": current_green_allocation,
            "target_green_allocation": self.target_green_allocation,
            "green_allocation_gap": self.target_green_allocation - current_green_allocation,
            "portfolio_value": total_value
        }
        
        # Enhance recommendations based on allocation gaps
        if ethics_result["green_impact"] and current_green_allocation < self.target_green_allocation:
            if ethics_result["status"] == "mission_critical":
                ethics_result["recommendations"].insert(0, 
                    f"[URGENT GREEN ALLOCATION] Currently {current_green_allocation:.1%}, targeting {self.target_green_allocation:.1%} - PRIORITY BUY")
            elif ethics_result["status"] == "priority":
                ethics_result["recommendations"].insert(0,
                    f"[GREEN ALLOCATION OPPORTUNITY] Helps reach {self.target_green_allocation:.1%} target - RECOMMENDED")
        
        ethics_result["portfolio_fit"] = portfolio_fit
        return ethics_result
    
    def _add_allocation_recommendations(self, ethics_result: Dict, symbol: str, portfolio_context: Optional[Dict]) -> Dict:
        """Add allocation-specific recommendations"""
        
        if not portfolio_context:
            return ethics_result
        
        current_green = portfolio_context.get("green_allocation", 0)
        
        # Priority recommendations based on allocation gaps
        allocation_recs = []
        
        if ethics_result["green_impact"]:
            if current_green < 0.20:  # Below 20% green
                allocation_recs.append("[CRITICAL] Green allocation severely below target - HIGH PRIORITY")
            elif current_green < self.target_green_allocation:
                gap = self.target_green_allocation - current_green
                allocation_recs.append(f"[OPPORTUNITY] {gap:.1%} gap to green target - CONSIDER")
        
        if allocation_recs:
            ethics_result["allocation_recommendations"] = allocation_recs
        
        return ethics_result
    
    def screen_portfolio_comprehensive(self, portfolio_positions: List[Dict]) -> Dict:
        """
        Comprehensive portfolio screening with detailed sustainability analysis
        """
        logger.info(f"Running comprehensive ethics screening on {len(portfolio_positions)} positions")
        
        # Extract symbols for batch screening
        symbols = [pos.get("symbol", pos.get("ticker", "")) for pos in portfolio_positions]
        
        # Run portfolio screening
        portfolio_result = self.ethics_manager.screen_portfolio(symbols)
        
        # Calculate detailed allocations
        allocation_analysis = self._calculate_detailed_allocations(portfolio_positions)
        
        # Generate action plan
        action_plan = self._generate_action_plan(portfolio_result, allocation_analysis)
        
        # Combine results
        comprehensive_result = {
            **portfolio_result,
            "allocation_analysis": allocation_analysis,
            "action_plan": action_plan,
            "screening_timestamp": datetime.now().isoformat(),
            "ethics_compliance": self._calculate_compliance_score(portfolio_result)
        }
        
        logger.info(f"Portfolio screening complete - Sustainability rating: {portfolio_result['sustainability_rating']}")
        
        return comprehensive_result
    
    def _calculate_detailed_allocations(self, portfolio_positions: List[Dict]) -> Dict:
        """Calculate detailed allocation breakdown"""
        
        total_value = sum(pos.get("value", pos.get("market_value", 0)) for pos in portfolio_positions)
        
        allocations = {
            "total_value": total_value,
            "green_value": 0,
            "ai_value": 0,
            "blocked_value": 0,
            "mission_critical_value": 0,
            "priority_value": 0,
            "preferred_value": 0
        }
        
        category_breakdown = {
            "renewable_energy": 0,
            "electric_vehicles": 0,
            "clean_technology": 0,
            "water_conservation": 0,
            "waste_management": 0,
            "sustainable_agriculture": 0
        }
        
        for position in portfolio_positions:
            symbol = position.get("symbol", position.get("ticker", ""))
            value = position.get("value", position.get("market_value", 0))
            
            # Get ethics screening
            ethics_result = self.ethics_manager.check_investment(symbol)
            
            # Categorize by status
            if ethics_result["status"] == "mission_critical":
                allocations["mission_critical_value"] += value
                allocations["green_value"] += value
            elif ethics_result["status"] == "priority":
                allocations["priority_value"] += value
                allocations["green_value"] += value
            elif ethics_result["status"] == "preferred":
                allocations["preferred_value"] += value
                allocations["green_value"] += value
            elif ethics_result["status"] == "blocked":
                allocations["blocked_value"] += value
            
            # Category breakdown for green investments
            if ethics_result["green_impact"] and ethics_result["benefits"]:
                category = ethics_result["benefits"][0].get("category", "")
                if category in category_breakdown:
                    category_breakdown[category] += value
        
        # Calculate percentages
        if total_value > 0:
            # Create a copy of keys to avoid dictionary size change during iteration
            allocation_keys = list(allocations.keys())
            for key in allocation_keys:
                if key != "total_value":
                    allocations[f"{key}_percent"] = allocations[key] / total_value
        
        allocations["category_breakdown"] = category_breakdown
        
        return allocations
    
    def _generate_action_plan(self, portfolio_result: Dict, allocation_analysis: Dict) -> Dict:
        """Generate specific action plan for portfolio improvement"""
        
        action_plan = {
            "immediate_actions": [],
            "optimization_opportunities": [],
            "rebalancing_suggestions": [],
            "priority_buys": [],
            "priority_sells": []
        }
        
        # Immediate actions for blocked holdings
        if portfolio_result.get("blocked"):
            for blocked in portfolio_result["blocked"]:
                action_plan["immediate_actions"].append({
                    "action": "SELL",
                    "symbol": blocked["symbol"],
                    "reason": blocked["concerns"][0]["reason"],
                    "alternatives": blocked.get("alternatives", []),
                    "urgency": "HIGH"
                })
                
                # Add alternative buys
                for alt in blocked.get("alternatives", [])[:2]:  # Top 2 alternatives
                    alt_ethics = self.ethics_manager.check_investment(alt)
                    if alt_ethics["status"] in ["mission_critical", "priority"]:
                        action_plan["priority_buys"].append({
                            "symbol": alt,
                            "reason": f"Green alternative to {blocked['symbol']}",
                            "priority_score": alt_ethics["priority_score"],
                            "category": alt_ethics.get("benefits", [{}])[0].get("category", "")
                        })
        
        # Green allocation optimization
        current_green_pct = allocation_analysis.get("green_value_percent", 0)
        if current_green_pct < self.target_green_allocation:
            gap = self.target_green_allocation - current_green_pct
            target_value = allocation_analysis["total_value"] * gap
            
            action_plan["optimization_opportunities"].append({
                "type": "GREEN_ALLOCATION_INCREASE",
                "current": f"{current_green_pct:.1%}",
                "target": f"{self.target_green_allocation:.1%}",
                "gap": f"{gap:.1%}",
                "target_investment_value": target_value,
                "recommendation": f"Invest ${target_value:.0f} in mission-critical green stocks"
            })
            
            # Get top green recommendations
            green_opportunities = self._get_top_green_opportunities()
            action_plan["priority_buys"].extend(green_opportunities[:3])
        
        # Mission critical opportunities
        if allocation_analysis.get("mission_critical_value_percent", 0) < 0.20:  # Target 20% mission critical
            mission_critical_stocks = [
                entry for entry in self.ethics_manager.green_whitelist.values()
                if entry.priority == 4  # Mission critical
            ]
            
            for stock in sorted(mission_critical_stocks, key=lambda x: x.esg_score, reverse=True)[:2]:
                action_plan["priority_buys"].append({
                    "symbol": stock.symbol,
                    "reason": "Mission-critical earth preservation investment",
                    "priority_score": 10,
                    "esg_score": stock.esg_score,
                    "category": stock.category
                })
        
        return action_plan
    
    def _get_top_green_opportunities(self) -> List[Dict]:
        """Get top green investment opportunities"""
        
        opportunities = []
        
        # Mission critical first
        mission_critical = [
            entry for entry in self.ethics_manager.green_whitelist.values()
            if entry.priority == 4
        ]
        
        for entry in sorted(mission_critical, key=lambda x: x.esg_score, reverse=True)[:3]:
            opportunities.append({
                "symbol": entry.symbol,
                "reason": f"Mission-critical: {entry.reason}",
                "priority_score": 10,
                "esg_score": entry.esg_score,
                "category": entry.category,
                "climate_commitment": entry.climate_commitment
            })
        
        return opportunities
    
    def _calculate_compliance_score(self, portfolio_result: Dict) -> Dict:
        """Calculate ethics compliance score"""
        
        total_stocks = portfolio_result.get("total_symbols", 0)
        if total_stocks == 0:
            return {"score": 1.0, "grade": "A", "status": "COMPLIANT"}
        
        blocked_count = len(portfolio_result.get("blocked", []))
        green_count = (len(portfolio_result.get("mission_critical", [])) + 
                      len(portfolio_result.get("priority", [])) + 
                      len(portfolio_result.get("preferred", [])))
        
        # Calculate compliance score
        compliance_score = max(0, (total_stocks - blocked_count) / total_stocks)
        green_bonus = min(0.2, green_count / total_stocks * 0.5)  # Up to 20% bonus for green
        
        final_score = min(1.0, compliance_score + green_bonus)
        
        # Assign grade
        if final_score >= 0.9:
            grade = "A"
            status = "EXCELLENT"
        elif final_score >= 0.8:
            grade = "B"
            status = "GOOD"
        elif final_score >= 0.7:
            grade = "C"
            status = "ACCEPTABLE"
        elif final_score >= 0.6:
            grade = "D"
            status = "NEEDS_IMPROVEMENT"
        else:
            grade = "F"
            status = "NON_COMPLIANT"
        
        return {
            "score": final_score,
            "grade": grade,
            "status": status,
            "blocked_count": blocked_count,
            "green_count": green_count,
            "total_count": total_stocks
        }
    
    def generate_daily_ethics_brief(self, portfolio_positions: List[Dict]) -> str:
        """Generate daily ethics and sustainability brief"""
        
        screening_result = self.screen_portfolio_comprehensive(portfolio_positions)
        
        brief = f"""
[CHART] DAILY ETHICS & SUSTAINABILITY BRIEF
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

[TARGET] PORTFOLIO SUSTAINABILITY RATING: {screening_result['sustainability_rating']}
[GRAPH] Ethics Compliance Score: {screening_result['ethics_compliance']['grade']} ({screening_result['ethics_compliance']['score']:.1%})

[MONEY] ALLOCATION BREAKDOWN:
• Total Portfolio Value: ${screening_result['allocation_analysis']['total_value']:.0f}
• Green Technology: {screening_result['allocation_analysis'].get('green_value_percent', 0):.1%} (Target: {self.target_green_allocation:.1%})
• Mission Critical: {screening_result['allocation_analysis'].get('mission_critical_value_percent', 0):.1%}
• Blocked Holdings: {screening_result['allocation_analysis'].get('blocked_value_percent', 0):.1%}

[EARTH] GREEN IMPACT SUMMARY:
• Mission Critical Stocks: {len(screening_result.get('mission_critical', []))}
• Priority Green Stocks: {len(screening_result.get('priority', []))}
• Preferred Sustainable: {len(screening_result.get('preferred', []))}

[WARNING] IMMEDIATE ACTIONS REQUIRED:
"""
        
        # Add immediate actions
        immediate_actions = screening_result['action_plan']['immediate_actions']
        if immediate_actions:
            for action in immediate_actions:
                brief += f"• {action['action']} {action['symbol']}: {action['reason']}\n"
        else:
            brief += "• No immediate actions required\n"
        
        brief += f"""
[GREEN] OPTIMIZATION OPPORTUNITIES:
"""
        
        # Add optimization opportunities
        opportunities = screening_result['action_plan']['optimization_opportunities']
        if opportunities:
            for opp in opportunities:
                brief += f"• {opp['recommendation']}\n"
        
        # Add top recommendations
        if screening_result['action_plan']['priority_buys']:
            brief += f"\n[TARGET] TOP GREEN INVESTMENT RECOMMENDATIONS:\n"
            for buy in screening_result['action_plan']['priority_buys'][:3]:
                brief += f"• {buy['symbol']}: {buy['reason']} (ESG: {buy.get('esg_score', 'N/A')})\n"
        
        return brief

def main():
    """Test the ethics integration"""
    
    print("Testing Ethics Integration System...")
    
    # Initialize
    ethics_analyzer = EthicsIntegratedAnalyzer()
    
    # Test portfolio
    test_portfolio = [
        {"symbol": "FSLR", "value": 150},    # Mission critical
        {"symbol": "TSLA", "value": 200},    # Blocked (Elon Musk)
        {"symbol": "MSFT", "value": 180},    # Unknown/approved
        {"symbol": "ICLN", "value": 120},    # Mission critical ETF
        {"symbol": "XOM", "value": 100},     # Blocked (fossil fuel)
        {"symbol": "RIVN", "value": 150}     # Priority green EV
    ]
    
    # Run comprehensive screening
    result = ethics_analyzer.screen_portfolio_comprehensive(test_portfolio)
    
    print(f"\nPortfolio Sustainability Rating: {result['sustainability_rating']}")
    print(f"Ethics Compliance: {result['ethics_compliance']['grade']} ({result['ethics_compliance']['score']:.1%})")
    print(f"Green Allocation: {result['allocation_analysis'].get('green_value_percent', 0):.1%}")
    
    # Generate daily brief
    daily_brief = ethics_analyzer.generate_daily_ethics_brief(test_portfolio)
    print("\n" + "="*80)
    print(daily_brief)
    
    print("\n✅ Ethics integration test completed successfully!")

if __name__ == "__main__":
    main()