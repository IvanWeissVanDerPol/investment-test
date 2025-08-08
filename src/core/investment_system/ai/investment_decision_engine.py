"""
AI-Enhanced Investment Decision Engine
Combines ethics screening with Claude AI analysis for intelligent investment decisions
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .claude_client import ClaudeInvestmentClient
from ..integrations.ethics_integration import EthicsIntegratedAnalyzer
from ..utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class AIInvestmentDecisionEngine:
    """
    AI-powered investment decision engine that combines:
    - Ethics screening and sustainability analysis
    - Claude AI market insights and analysis
    - Portfolio optimization recommendations
    - Green investment prioritization
    """
    
    def __init__(self, config_path: str = "config"):
        """Initialize the AI decision engine"""
        
        self.ethics_analyzer = EthicsIntegratedAnalyzer(config_path)
        self.claude_client = ClaudeInvestmentClient()
        self.cache_manager = CacheManager()
        
        # Decision engine configuration
        self.decision_weights = {
            "ethics_score": 0.40,        # 40% weight on ethics/sustainability
            "ai_analysis": 0.35,         # 35% weight on AI analysis
            "technical_analysis": 0.15,  # 15% weight on technical factors
            "market_context": 0.10       # 10% weight on market conditions
        }
        
        self.confidence_thresholds = {
            "high_confidence": 0.80,
            "medium_confidence": 0.60,
            "low_confidence": 0.40
        }
        
        logger.info("AI Investment Decision Engine initialized with ethics and Claude integration")
    
    def analyze_investment_decision(self, symbol: str, portfolio_context: Dict, decision_type: str = "buy") -> Dict:
        """
        Comprehensive AI-powered investment decision analysis
        
        Args:
            symbol: Stock symbol to analyze
            portfolio_context: Current portfolio information
            decision_type: "buy", "sell", or "hold"
            
        Returns:
            Comprehensive decision analysis with recommendation
        """
        logger.info(f"Running AI decision analysis for {symbol} ({decision_type})")
        
        # Check cache first
        cache_key = f"ai_decision_{symbol}_{decision_type}_{datetime.now().strftime('%Y%m%d')}"
        cached_result = self.cache_manager.get_cached_data("ai_decisions", cache_key)
        
        if cached_result:
            logger.debug(f"Using cached AI decision for {symbol}")
            return cached_result
        
        try:
            # Step 1: Ethics screening with portfolio context
            ethics_result = self.ethics_analyzer.screen_investment_with_context(
                symbol, portfolio_context
            )
            
            # Step 2: AI analysis if Claude is available
            ai_analysis = None
            if self.claude_client.is_available():
                stock_data = self._prepare_stock_data(symbol, portfolio_context)
                ai_analysis = self.claude_client.analyze_stock(symbol, stock_data, ethics_result)
            
            # Step 3: Market context analysis
            market_context = None
            if self.claude_client.is_available():
                market_context = self.claude_client.analyze_market_conditions()
            
            # Step 4: Generate final decision
            final_decision = self._generate_final_decision(
                symbol, ethics_result, ai_analysis, market_context, 
                portfolio_context, decision_type
            )
            
            # Cache the result
            self.cache_manager.cache_data("ai_decisions", cache_key, final_decision)
            
            return final_decision
            
        except Exception as e:
            logger.error(f"AI decision analysis failed for {symbol}: {e}")
            return self._generate_error_decision(symbol, str(e))
    
    def _prepare_stock_data(self, symbol: str, portfolio_context: Dict) -> Dict:
        """Prepare stock data for AI analysis"""
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "portfolio_context": {
                "total_value": portfolio_context.get("total_value", 900),
                "current_green_allocation": portfolio_context.get("green_allocation", 0),
                "current_ai_allocation": portfolio_context.get("ai_allocation", 0),
                "target_green_allocation": 0.30,
                "target_ai_allocation": 0.50
            },
            "investment_profile": {
                "risk_tolerance": "medium",
                "timeline": "long_term",
                "focus": "sustainable_growth_with_earth_preservation"
            }
        }
    
    def _generate_final_decision(self, symbol: str, ethics_result: Dict, ai_analysis: Optional[Dict], 
                               market_context: Optional[Dict], portfolio_context: Dict, 
                               decision_type: str) -> Dict:
        """Generate final investment decision combining all analysis"""
        
        # Calculate component scores
        ethics_score = self._calculate_ethics_score(ethics_result)
        ai_score = self._calculate_ai_score(ai_analysis) if ai_analysis else 0.5
        market_score = self._calculate_market_score(market_context) if market_context else 0.5
        technical_score = self._calculate_technical_score(symbol, portfolio_context)
        
        # Calculate weighted final score
        final_score = (
            ethics_score * self.decision_weights["ethics_score"] +
            ai_score * self.decision_weights["ai_analysis"] +
            technical_score * self.decision_weights["technical_analysis"] +
            market_score * self.decision_weights["market_context"]
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(final_score, decision_type, ethics_result)
        
        # Calculate confidence level
        confidence = self._calculate_confidence(ethics_result, ai_analysis, final_score)
        
        # Prepare comprehensive decision result
        decision_result = {
            "symbol": symbol,
            "decision_type": decision_type,
            "recommendation": recommendation,
            "confidence_level": confidence,
            "final_score": final_score,
            "timestamp": datetime.now().isoformat(),
            
            # Component scores
            "component_scores": {
                "ethics_score": ethics_score,
                "ai_score": ai_score,
                "technical_score": technical_score,
                "market_score": market_score
            },
            
            # Detailed analysis
            "ethics_analysis": ethics_result,
            "ai_analysis": ai_analysis.get("ai_analysis", "AI analysis unavailable") if ai_analysis else "Claude API not configured",
            "market_analysis": market_context.get("market_analysis", "Market analysis unavailable") if market_context else "Market analysis unavailable",
            
            # Key factors
            "key_factors": self._extract_key_factors(ethics_result, ai_analysis),
            "risk_factors": self._extract_risk_factors(ethics_result, ai_analysis),
            "sustainability_impact": self._assess_sustainability_impact(ethics_result),
            
            # Portfolio fit
            "portfolio_fit": self._assess_portfolio_fit(ethics_result, portfolio_context),
            
            # Action items
            "action_items": self._generate_action_items(recommendation, ethics_result, portfolio_context)
        }
        
        logger.info(f"AI decision for {symbol}: {recommendation} (confidence: {confidence}, score: {final_score:.2f})")
        
        return decision_result
    
    def _calculate_ethics_score(self, ethics_result: Dict) -> float:
        """Calculate ethics component score (0-1)"""
        
        status = ethics_result.get("status", "unknown")
        priority_score = ethics_result.get("priority_score", 1)
        
        # Base scores by ethics status
        status_scores = {
            "mission_critical": 1.0,
            "priority": 0.85,
            "preferred": 0.70,
            "approved": 0.60,
            "unknown": 0.40,
            "concerns": 0.25,
            "blocked": 0.0
        }
        
        base_score = status_scores.get(status, 0.40)
        
        # Adjust for green impact
        if ethics_result.get("green_impact", False):
            base_score = min(1.0, base_score + 0.15)
        
        # Adjust for ESG score if available
        esg_score = ethics_result.get("esg_score", 0)
        if esg_score > 0:
            esg_adjustment = (esg_score - 5.0) / 5.0 * 0.10  # -0.10 to +0.10 adjustment
            base_score = max(0.0, min(1.0, base_score + esg_adjustment))
        
        return base_score
    
    def _calculate_ai_score(self, ai_analysis: Dict) -> float:
        """Calculate AI analysis component score (0-1)"""
        
        if not ai_analysis or "error" in ai_analysis:
            return 0.5  # Neutral score if AI unavailable
        
        ai_text = ai_analysis.get("ai_analysis", "").lower()
        
        # Look for key recommendation indicators
        buy_indicators = ["buy", "strong buy", "recommended", "excellent", "outstanding"]
        sell_indicators = ["sell", "avoid", "poor", "concerning", "risky"]
        positive_indicators = ["growth", "potential", "strong", "good", "solid"]
        negative_indicators = ["decline", "weak", "loss", "problem", "issue"]
        
        score = 0.5  # Start neutral
        
        # Adjust based on recommendation indicators
        for indicator in buy_indicators:
            if indicator in ai_text:
                score += 0.15
        
        for indicator in sell_indicators:
            if indicator in ai_text:
                score -= 0.20
        
        for indicator in positive_indicators:
            if indicator in ai_text:
                score += 0.05
        
        for indicator in negative_indicators:
            if indicator in ai_text:
                score -= 0.05
        
        # Look for confidence indicators
        if any(conf in ai_text for conf in ["high confidence", "strong confidence", "very confident"]):
            score += 0.10
        elif any(conf in ai_text for conf in ["low confidence", "uncertain", "risky"]):
            score -= 0.10
        
        return max(0.0, min(1.0, score))
    
    def _calculate_technical_score(self, symbol: str, portfolio_context: Dict) -> float:
        """Calculate technical analysis score (simplified)"""
        
        # This is a simplified technical score
        # In a real implementation, you would integrate with technical analysis APIs
        
        base_score = 0.5
        
        # Adjust for portfolio balance
        total_value = portfolio_context.get("total_value", 900)
        if total_value < 500:
            base_score += 0.10  # Favor growth for smaller portfolios
        elif total_value > 2000:
            base_score -= 0.05  # Favor stability for larger portfolios
        
        # Adjust for diversification needs
        position_count = portfolio_context.get("position_count", 0)
        if position_count < 5:
            base_score += 0.05  # Favor diversification
        elif position_count > 15:
            base_score -= 0.05  # Favor concentration
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_market_score(self, market_context: Dict) -> float:
        """Calculate market context score (0-1)"""
        
        if not market_context:
            return 0.5
        
        market_text = market_context.get("market_analysis", "").lower()
        
        score = 0.5
        
        # Look for market sentiment indicators
        positive_market = ["bullish", "positive", "growth", "opportunity", "strong"]
        negative_market = ["bearish", "negative", "decline", "risk", "weak"]
        
        for indicator in positive_market:
            if indicator in market_text:
                score += 0.08
        
        for indicator in negative_market:
            if indicator in market_text:
                score -= 0.08
        
        # Look for sector-specific indicators
        green_positive = ["renewable", "sustainable", "green technology", "climate"]
        ai_positive = ["artificial intelligence", "robotics", "automation", "ai advancement"]
        
        for indicator in green_positive + ai_positive:
            if indicator in market_text:
                score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _generate_recommendation(self, final_score: float, decision_type: str, ethics_result: Dict) -> str:
        """Generate final recommendation based on score and ethics"""
        
        # Override for blocked investments
        if ethics_result.get("status") == "blocked":
            return "STRONG SELL" if decision_type == "sell" else "AVOID"
        
        # Generate recommendation based on score
        if final_score >= 0.80:
            return "STRONG BUY" if decision_type == "buy" else "STRONG HOLD"
        elif final_score >= 0.65:
            return "BUY" if decision_type == "buy" else "HOLD"
        elif final_score >= 0.50:
            return "MODERATE BUY" if decision_type == "buy" else "HOLD"
        elif final_score >= 0.35:
            return "HOLD" if decision_type == "buy" else "CONSIDER SELL"
        else:
            return "AVOID" if decision_type == "buy" else "SELL"
    
    def _calculate_confidence(self, ethics_result: Dict, ai_analysis: Optional[Dict], final_score: float) -> str:
        """Calculate confidence level in the recommendation"""
        
        confidence_factors = []
        
        # Ethics confidence
        if ethics_result.get("status") in ["mission_critical", "priority", "blocked"]:
            confidence_factors.append(0.25)  # High confidence from clear ethics status
        else:
            confidence_factors.append(0.10)  # Lower confidence from unclear ethics
        
        # AI confidence
        if ai_analysis and self.claude_client.is_available():
            confidence_factors.append(0.20)  # AI available
        else:
            confidence_factors.append(0.05)  # AI unavailable
        
        # Score confidence
        if final_score > 0.75 or final_score < 0.25:
            confidence_factors.append(0.20)  # Clear high/low score
        elif final_score > 0.60 or final_score < 0.40:
            confidence_factors.append(0.15)  # Moderate score
        else:
            confidence_factors.append(0.05)  # Unclear score
        
        total_confidence = sum(confidence_factors)
        
        if total_confidence >= self.confidence_thresholds["high_confidence"]:
            return "HIGH"
        elif total_confidence >= self.confidence_thresholds["medium_confidence"]:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _extract_key_factors(self, ethics_result: Dict, ai_analysis: Optional[Dict]) -> List[str]:
        """Extract key positive factors supporting the decision"""
        
        factors = []
        
        # Ethics factors
        if ethics_result.get("green_impact"):
            factors.append("Strong environmental impact and sustainability credentials")
        
        if ethics_result.get("status") == "mission_critical":
            factors.append("Mission-critical earth preservation investment")
        
        if ethics_result.get("esg_score", 0) > 8.0:
            factors.append(f"Excellent ESG score: {ethics_result.get('esg_score')}/10")
        
        # AI factors
        if ai_analysis and "strong" in ai_analysis.get("ai_analysis", "").lower():
            factors.append("AI analysis indicates strong fundamentals")
        
        if not factors:
            factors.append("Standard investment analysis completed")
        
        return factors
    
    def _extract_risk_factors(self, ethics_result: Dict, ai_analysis: Optional[Dict]) -> List[str]:
        """Extract risk factors and concerns"""
        
        risks = []
        
        # Ethics risks
        if ethics_result.get("status") == "blocked":
            risks.extend([concern["reason"] for concern in ethics_result.get("concerns", [])])
        elif ethics_result.get("status") == "concerns":
            risks.append("Ethics concerns identified - review required")
        
        # AI risks
        if ai_analysis and any(word in ai_analysis.get("ai_analysis", "").lower() 
                             for word in ["risk", "concern", "volatile", "uncertain"]):
            risks.append("AI analysis identifies potential risks")
        
        # General risks
        if not risks:
            risks.append("Standard market and business risks apply")
        
        return risks
    
    def _assess_sustainability_impact(self, ethics_result: Dict) -> Dict:
        """Assess sustainability and environmental impact"""
        
        impact = {
            "environmental_score": 0,
            "social_score": 0,
            "governance_score": 0,
            "overall_impact": "neutral"
        }
        
        if ethics_result.get("green_impact"):
            impact["environmental_score"] = 8
            impact["overall_impact"] = "positive"
            
            if ethics_result.get("status") == "mission_critical":
                impact["environmental_score"] = 10
                impact["overall_impact"] = "highly_positive"
        
        # Use ESG score if available
        esg_score = ethics_result.get("esg_score", 0)
        if esg_score > 0:
            impact["environmental_score"] = min(10, int(esg_score))
            impact["social_score"] = min(10, int(esg_score * 0.9))
            impact["governance_score"] = min(10, int(esg_score * 0.8))
        
        return impact
    
    def _assess_portfolio_fit(self, ethics_result: Dict, portfolio_context: Dict) -> Dict:
        """Assess how well the investment fits current portfolio"""
        
        current_green = portfolio_context.get("green_allocation", 0)
        target_green = 0.30
        
        fit_assessment = {
            "allocation_fit": "good",
            "diversification_impact": "neutral",
            "risk_balance": "appropriate"
        }
        
        # Allocation fit
        if ethics_result.get("green_impact") and current_green < target_green:
            fit_assessment["allocation_fit"] = "excellent"
            fit_assessment["allocation_reason"] = f"Helps reach {target_green:.1%} green target"
        elif ethics_result.get("status") == "blocked":
            fit_assessment["allocation_fit"] = "poor"
            fit_assessment["allocation_reason"] = "Conflicts with ethics standards"
        
        return fit_assessment
    
    def _generate_action_items(self, recommendation: str, ethics_result: Dict, portfolio_context: Dict) -> List[Dict]:
        """Generate specific action items based on recommendation"""
        
        actions = []
        
        if recommendation in ["STRONG BUY", "BUY"]:
            actions.append({
                "action": "BUY",
                "priority": "HIGH" if "STRONG" in recommendation else "MEDIUM",
                "details": f"Add to portfolio targeting sustainability goals"
            })
            
            if ethics_result.get("green_impact"):
                actions.append({
                    "action": "ALLOCATE",
                    "priority": "MEDIUM",
                    "details": "Count towards 30% green allocation target"
                })
        
        elif recommendation in ["SELL", "STRONG SELL", "AVOID"]:
            if ethics_result.get("status") == "blocked":
                actions.append({
                    "action": "SELL",
                    "priority": "HIGH",
                    "details": "Ethics violation - immediate divestment recommended"
                })
                
                # Add alternative suggestions
                alternatives = ethics_result.get("alternatives", [])
                if alternatives:
                    actions.append({
                        "action": "RESEARCH_ALTERNATIVES",
                        "priority": "HIGH",
                        "details": f"Consider green alternatives: {', '.join(alternatives[:3])}"
                    })
        
        elif recommendation == "HOLD":
            actions.append({
                "action": "MONITOR",
                "priority": "LOW",
                "details": "Continue monitoring for changes in ethics or fundamentals"
            })
        
        return actions
    
    def _generate_error_decision(self, symbol: str, error_message: str) -> Dict:
        """Generate error decision when analysis fails"""
        
        return {
            "symbol": symbol,
            "recommendation": "ANALYSIS_FAILED",
            "confidence_level": "NONE",
            "final_score": 0.0,
            "timestamp": datetime.now().isoformat(),
            "error": error_message,
            "action_items": [{
                "action": "RETRY",
                "priority": "LOW",
                "details": "Retry analysis when systems are available"
            }]
        }
    
    def analyze_portfolio_decisions(self, portfolio_positions: List[Dict]) -> Dict:
        """Analyze all portfolio positions for buy/sell/hold decisions"""
        
        logger.info(f"Running AI portfolio decision analysis on {len(portfolio_positions)} positions")
        
        portfolio_context = self._build_portfolio_context(portfolio_positions)
        
        position_decisions = []
        portfolio_summary = {
            "strong_buys": 0,
            "buys": 0,
            "holds": 0,
            "sells": 0,
            "avoids": 0,
            "total_analyzed": len(portfolio_positions)
        }
        
        for position in portfolio_positions:
            symbol = position.get("symbol", position.get("ticker", ""))
            if not symbol:
                continue
            
            # Analyze each position
            decision = self.analyze_investment_decision(symbol, portfolio_context, "hold")
            position_decisions.append(decision)
            
            # Update summary
            recommendation = decision.get("recommendation", "").upper()
            if "STRONG BUY" in recommendation:
                portfolio_summary["strong_buys"] += 1
            elif "BUY" in recommendation:
                portfolio_summary["buys"] += 1
            elif "SELL" in recommendation or "AVOID" in recommendation:
                portfolio_summary["sells"] += 1
            else:
                portfolio_summary["holds"] += 1
        
        return {
            "portfolio_decisions": position_decisions,
            "summary": portfolio_summary,
            "analysis_timestamp": datetime.now().isoformat(),
            "ai_available": self.claude_client.is_available()
        }
    
    def _build_portfolio_context(self, portfolio_positions: List[Dict]) -> Dict:
        """Build comprehensive portfolio context for analysis"""
        
        total_value = sum(pos.get("value", pos.get("market_value", 0)) for pos in portfolio_positions)
        
        # Calculate current allocations using ethics system
        comprehensive_screening = self.ethics_analyzer.screen_portfolio_comprehensive(portfolio_positions)
        allocation_analysis = comprehensive_screening.get("allocation_analysis", {})
        
        return {
            "total_value": total_value,
            "position_count": len(portfolio_positions),
            "green_allocation": allocation_analysis.get("green_value_percent", 0),
            "ai_allocation": 0.50,  # Placeholder - would need to calculate from holdings
            "ethics_compliance_score": comprehensive_screening.get("ethics_compliance", {}).get("score", 0),
            "sustainability_rating": comprehensive_screening.get("sustainability_rating", "Unknown")
        }
    
    def get_green_investment_recommendations(self, portfolio_context: Dict, budget: float = 100) -> List[Dict]:
        """Get AI-powered green investment recommendations for specific budget"""
        
        logger.info(f"Getting green investment recommendations for ${budget} budget")
        
        # Get top green opportunities from ethics system
        green_stocks = list(self.ethics_analyzer.ethics_manager.green_whitelist.values())
        
        # Sort by priority and ESG score
        top_candidates = sorted(green_stocks, 
                              key=lambda x: (x.priority, x.esg_score), 
                              reverse=True)[:10]
        
        recommendations = []
        
        for candidate in top_candidates:
            # Run full AI decision analysis
            decision = self.analyze_investment_decision(
                candidate.symbol, portfolio_context, "buy"
            )
            
            if decision.get("recommendation") in ["STRONG BUY", "BUY", "MODERATE BUY"]:
                recommendations.append({
                    "symbol": candidate.symbol,
                    "recommendation": decision.get("recommendation"),
                    "confidence": decision.get("confidence_level"),
                    "final_score": decision.get("final_score"),
                    "esg_score": candidate.esg_score,
                    "priority_level": candidate.priority,
                    "category": candidate.category,
                    "reason": candidate.reason,
                    "ai_analysis_summary": decision.get("ai_analysis", "")[:200] + "..."
                })
        
        # Sort by final score and limit to budget
        recommendations.sort(key=lambda x: x["final_score"], reverse=True)
        
        return recommendations[:5]  # Top 5 recommendations

def main():
    """Test the AI Investment Decision Engine"""
    
    print("="*80)
    print("TESTING AI INVESTMENT DECISION ENGINE")
    print("="*80)
    
    # Initialize engine
    engine = AIInvestmentDecisionEngine()
    
    # Test portfolio context
    test_portfolio_context = {
        "total_value": 900,
        "position_count": 6,
        "green_allocation": 0.20,
        "ai_allocation": 0.45,
        "ethics_compliance_score": 0.75
    }
    
    # Test individual stock decision
    print("\n[TEST] Individual Stock Decision Analysis")
    print("-" * 50)
    
    test_symbols = ["FSLR", "TSLA", "NVDA", "ICLN"]
    
    for symbol in test_symbols:
        decision = engine.analyze_investment_decision(symbol, test_portfolio_context, "buy")
        
        print(f"\n{symbol}:")
        print(f"  Recommendation: {decision['recommendation']}")
        print(f"  Confidence: {decision['confidence_level']}")
        print(f"  Final Score: {decision['final_score']:.2f}")
        print(f"  Key Factor: {decision['key_factors'][0] if decision['key_factors'] else 'None'}")
    
    # Test green recommendations
    print(f"\n[TEST] Green Investment Recommendations")
    print("-" * 50)
    
    green_recs = engine.get_green_investment_recommendations(test_portfolio_context, 200)
    
    for i, rec in enumerate(green_recs[:3], 1):
        print(f"{i}. {rec['symbol']} - {rec['recommendation']} (Score: {rec['final_score']:.2f})")
        print(f"   ESG: {rec['esg_score']}/10 | Category: {rec['category']}")
    
    print(f"\n[SUCCESS] AI Decision Engine testing complete!")
    print(f"Claude API Available: {engine.claude_client.is_available()}")

if __name__ == "__main__":
    main()