"""
Daily AI Sustainability Analysis Script
Comprehensive portfolio analysis with AI insights and sustainability focus
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.investment_system.reporting.ai_sustainability_reporter import AISustainabilityReporter
from src.investment_system.ai.investment_decision_engine import AIInvestmentDecisionEngine

def main():
    """Run comprehensive AI sustainability analysis"""
    
    print("="*80)
    print("IVAN'S AI-POWERED SUSTAINABILITY ANALYSIS")
    print("="*80)
    
    # Initialize systems
    try:
        reporter = AISustainabilityReporter()
        ai_engine = AIInvestmentDecisionEngine()
        print("[SUCCESS] AI analysis systems initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize systems: {e}")
        return
    
    # Your current portfolio (update these with your actual holdings)
    your_portfolio = [
        # Update with your actual positions - format: {"symbol": "STOCK", "value": amount, "shares": count}
        {"symbol": "MSFT", "value": 200, "shares": 1},
        {"symbol": "AAPL", "value": 180, "shares": 1},
        {"symbol": "NVDA", "value": 300, "shares": 1},
        {"symbol": "FSLR", "value": 120, "shares": 1},    # Green solar
        # Add your other holdings here...
    ]
    
    print(f"\nAnalyzing portfolio: {len(your_portfolio)} positions")
    print(f"Total value: ${sum(pos['value'] for pos in your_portfolio)}")
    
    try:
        # Generate comprehensive AI sustainability report
        print("\n[GENERATING] AI Sustainability Report...")
        formatted_report = reporter.generate_formatted_report(your_portfolio)
        
        # Display the report
        print(formatted_report)
        
        # Additional AI insights if available
        if ai_engine.claude_client.is_available():
            print("\n[AI INSIGHTS] Claude-Powered Analysis")
            print("-" * 50)
            
            # Get market insights
            market_insights = ai_engine.claude_client.analyze_market_conditions()
            if market_insights:
                print("Market Analysis:")
                print(market_insights.get('market_analysis', 'No analysis available')[:300] + "...")
        else:
            print("\n[SETUP] Enable AI Features")
            print("-" * 30)
            print("To unlock AI-powered insights:")
            print("1. Install anthropic: pip install anthropic")
            print("2. Get Claude API key: https://console.anthropic.com/")
            print("3. Set environment variable: CLAUDE_API_KEY=your_key")
        
        # Green investment opportunities
        print(f"\n[GREEN OPPORTUNITIES] Top Sustainable Investments")
        print("-" * 55)
        
        portfolio_context = ai_engine._build_portfolio_context(your_portfolio)
        green_recs = ai_engine.get_green_investment_recommendations(portfolio_context, 200)
        
        for i, rec in enumerate(green_recs[:5], 1):
            print(f"{i}. {rec['symbol']} - {rec['recommendation']}")
            print(f"   ESG Score: {rec['esg_score']}/10 | Priority: {rec['priority_level']}")
            print(f"   Category: {rec['category'].replace('_', ' ').title()}")
            print(f"   Reason: {rec['reason'][:60]}...")
            print()
        
        # Portfolio optimization suggestions
        print(f"\n[OPTIMIZATION] AI-Powered Portfolio Suggestions")
        print("-" * 50)
        
        current_green = portfolio_context.get('green_allocation', 0)
        if current_green < 0.30:
            gap = 0.30 - current_green
            investment_needed = gap * portfolio_context['total_value']
            print(f"• INCREASE GREEN: Currently {current_green:.1%}, target 30%")
            print(f"  Recommended additional investment: ${investment_needed:.0f}")
        else:
            print(f"• GREEN TARGET ACHIEVED: {current_green:.1%} (exceeds 30% target)")
        
        print(f"• SUSTAINABILITY RATING: {portfolio_context.get('sustainability_rating', 'Unknown')}")
        print(f"• COMPLIANCE SCORE: {portfolio_context.get('ethics_compliance_score', 0):.1%}")
        
        # Daily action summary
        print(f"\n[ACTION PLAN] Today's Priorities")
        print("-" * 35)
        print("1. Review and act on any blocked holdings")
        print("2. Consider top green investment opportunities")
        print("3. Monitor sustainability allocation targets")
        print("4. Track AI recommendations for optimal timing")
        
        print(f"\n[SUCCESS] AI sustainability analysis complete!")
        print(f"Reports saved to: reports/sustainability/daily_sustainability_latest.json")
        print("Run this script daily for optimal sustainable portfolio management.")
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()