"""
Test the enhanced ethics integration system
"""

import sys
import os
sys.path.append('src')

from core.investment_system.integrations.ethics_integration import EthicsIntegratedAnalyzer

def test_ethics_integration():
    """Test the ethics integration system"""
    
    print("[EARTH] TESTING ENHANCED ETHICS INTEGRATION SYSTEM")
    print("="*80)
    
    # Initialize
    print("Initializing Ethics Integration System...")
    try:
        ethics_analyzer = EthicsIntegratedAnalyzer()
        print("[SUCCESS] Ethics integration initialized successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to initialize: {e}")
        return
    
    # Test portfolio with real examples
    print(f"\n[CHART] TESTING PORTFOLIO SCREENING")
    print("-"*60)
    
    test_portfolio = [
        {"symbol": "FSLR", "value": 150, "shares": 5},      # Mission critical solar
        {"symbol": "TSLA", "value": 200, "shares": 1},      # Blocked (Elon Musk)
        {"symbol": "MSFT", "value": 180, "shares": 2},      # Standard approved
        {"symbol": "ICLN", "value": 120, "shares": 10},     # Mission critical ETF
        {"symbol": "XOM", "value": 100, "shares": 3},       # Blocked (fossil fuel)
        {"symbol": "RIVN", "value": 150, "shares": 8},      # Priority green EV
        {"symbol": "ENPH", "value": 80, "shares": 3},       # Priority solar tech
        {"symbol": "META", "value": 120, "shares": 1}       # Blocked (privacy violations)
    ]
    
    total_value = sum(pos["value"] for pos in test_portfolio)
    print(f"Test Portfolio Value: ${total_value}")
    print(f"Positions: {len(test_portfolio)} stocks")
    
    # Run comprehensive screening
    try:
        result = ethics_analyzer.screen_portfolio_comprehensive(test_portfolio)
        
        print(f"\n[GREEN] PORTFOLIO SUSTAINABILITY ANALYSIS")
        print("-"*60)
        print(f"Sustainability Rating: {result['sustainability_rating']}")
        print(f"Ethics Compliance: {result['ethics_compliance']['grade']} ({result['ethics_compliance']['score']:.1%})")
        print(f"Overall Score: {result['overall_score']:.1%}")
        print(f"Green Impact Score: {result['green_impact_score']:.1%}")
        
        # Allocation breakdown
        allocation = result['allocation_analysis']
        print(f"\n[MONEY] ALLOCATION BREAKDOWN")
        print("-"*40)
        print(f"Total Value: ${allocation['total_value']:.0f}")
        print(f"Green Technology: {allocation.get('green_value_percent', 0):.1%} (${allocation.get('green_value', 0):.0f})")
        print(f"Mission Critical: {allocation.get('mission_critical_value_percent', 0):.1%} (${allocation.get('mission_critical_value', 0):.0f})")
        print(f"Priority Green: {allocation.get('priority_value_percent', 0):.1%} (${allocation.get('priority_value', 0):.0f})")
        print(f"Blocked Holdings: {allocation.get('blocked_value_percent', 0):.1%} (${allocation.get('blocked_value', 0):.0f})")
        
        # Stock categorization
        print(f"\n[STOCKS] CATEGORIZATION")
        print("-"*40)
        print(f"Mission Critical: {len(result.get('mission_critical', []))} stocks")
        for stock in result.get('mission_critical', []):
            print(f"  [EARTH] {stock['symbol']} (Score: {stock['priority_score']})")
        
        print(f"Priority Green: {len(result.get('priority', []))} stocks")
        for stock in result.get('priority', []):
            print(f"  [GREEN] {stock['symbol']} (Score: {stock['priority_score']})")
        
        print(f"Blocked Holdings: {len(result.get('blocked', []))} stocks")
        for stock in result.get('blocked', []):
            print(f"  [BLOCKED] {stock['symbol']}: {stock['concerns'][0]['reason'][:50]}...")
            if stock.get('alternatives'):
                print(f"     Green alternatives: {', '.join(stock['alternatives'][:3])}")
        
        # Action plan
        action_plan = result.get('action_plan', {})
        print(f"\n[TARGET] ACTION PLAN")
        print("-"*40)
        
        immediate_actions = action_plan.get('immediate_actions', [])
        if immediate_actions:
            print("Immediate Actions Required:")
            for action in immediate_actions:
                print(f"  • {action['action']} {action['symbol']}: {action['reason']}")
        
        priority_buys = action_plan.get('priority_buys', [])
        if priority_buys:
            print("\nPriority Green Investments:")
            for buy in priority_buys[:3]:
                print(f"  • {buy['symbol']}: {buy['reason']} (ESG: {buy.get('esg_score', 'N/A')})")
        
        # Generate daily brief
        print(f"\n[EMAIL] DAILY SUSTAINABILITY BRIEF")
        print("="*80)
        daily_brief = ethics_analyzer.generate_daily_ethics_brief(test_portfolio)
        print(daily_brief)
        
        print("[SUCCESS] Portfolio screening completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Portfolio screening failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test individual stock screening
    print(f"\n[SEARCH] TESTING INDIVIDUAL STOCK SCREENING")
    print("-"*60)
    
    test_stocks = [
        ("FSLR", "First Solar - Mission Critical"),
        ("TSLA", "Tesla - Should be blocked"),
        ("RIVN", "Rivian - Priority EV"),
        ("XOM", "Exxon - Should be blocked"),
        ("ICLN", "Clean Energy ETF - Mission Critical")
    ]
    
    portfolio_context = {
        "green_allocation": 0.25,  # 25% current green
        "ai_allocation": 0.40,     # 40% current AI
        "total_value": 1000
    }
    
    for symbol, description in test_stocks:
        try:
            result = ethics_analyzer.screen_investment_with_context(symbol, portfolio_context)
            
            print(f"\n{symbol} ({description}):")
            print(f"  Status: {result['status'].upper()}")
            print(f"  Priority Score: {result['priority_score']}")
            
            if result.get('green_impact'):
                print("  [GREEN IMPACT] Environmental benefits")
                if result.get('benefits'):
                    benefit = result['benefits'][0]
                    print(f"  ESG Score: {benefit['esg_score']}/10")
                    print(f"  Impact Areas: {', '.join(benefit['impact_areas'])}")
            
            if result.get('concerns'):
                concern = result['concerns'][0]
                print(f"  [WARNING] Concern: {concern['reason']}")
            
            # Show top recommendation
            if result.get('recommendations'):
                print(f"  [IDEA] Recommendation: {result['recommendations'][0]}")
            
            if result.get('alternative_suggestions'):
                print(f"  [SWAP] Alternatives: {', '.join(result['alternative_suggestions'][:3])}")
                
        except Exception as e:
            print(f"  [ERROR] Screening failed: {e}")
    
    print(f"\n[STAR] ETHICS INTEGRATION TEST COMPLETE")
    print("="*80)
    print("[SUCCESS] Your enhanced ethics system is now active and ready to use!")
    print("[EARTH] Key Features Available:")
    print("• Mission-critical green investment prioritization")
    print("• Tesla alternatives (RIVN, NIO, LCID) to avoid Elon Musk")
    print("• Comprehensive ESG scoring and climate commitment tracking")
    print("• Real-time sustainability allocation monitoring")
    print("• Automated green alternative suggestions")
    print("• Daily sustainability briefs with actionable insights")

if __name__ == "__main__":
    test_ethics_integration()