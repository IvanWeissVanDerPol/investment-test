"""
Daily Ethics Check Script
Simple script to check your portfolio for ethics compliance and green allocation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.investment_system.integrations.ethics_integration import EthicsIntegratedAnalyzer

def main():
    """Run daily ethics check on your portfolio"""
    
    print("="*80)
    print("IVAN'S DAILY PORTFOLIO ETHICS CHECK")
    print("="*80)
    
    # Initialize ethics analyzer
    try:
        ethics_analyzer = EthicsIntegratedAnalyzer()
        print("[SUCCESS] Ethics system initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize ethics system: {e}")
        return
    
    # Your current portfolio (update these with your actual holdings)
    # Format: {"symbol": "STOCK", "value": dollar_amount, "shares": number_of_shares}
    your_portfolio = [
        # Update these with your actual holdings
        {"symbol": "MSFT", "value": 200, "shares": 1},
        {"symbol": "AAPL", "value": 180, "shares": 1},
        {"symbol": "NVDA", "value": 300, "shares": 1},
        # Add your other holdings here...
    ]
    
    print(f"\nAnalyzing portfolio with {len(your_portfolio)} positions...")
    print(f"Total portfolio value: ${sum(pos['value'] for pos in your_portfolio)}")
    
    # Run comprehensive ethics screening
    try:
        result = ethics_analyzer.screen_portfolio_comprehensive(your_portfolio)
        
        print(f"\n[RESULTS] PORTFOLIO ANALYSIS")
        print("-"*60)
        print(f"Sustainability Rating: {result['sustainability_rating']}")
        print(f"Ethics Compliance: {result['ethics_compliance']['grade']} ({result['ethics_compliance']['score']:.1%})")
        print(f"Green Impact Score: {result['green_impact_score']:.1%}")
        
        # Key metrics
        allocation = result['allocation_analysis']
        print(f"\n[ALLOCATION] CURRENT vs TARGET")
        print("-"*40)
        print(f"Green Technology: {allocation.get('green_value_percent', 0):.1%} (Target: 30.0%)")
        print(f"Mission Critical: {allocation.get('mission_critical_value_percent', 0):.1%}")
        print(f"Blocked Holdings: {allocation.get('blocked_value_percent', 0):.1%}")
        
        # Urgent actions
        blocked_holdings = result.get('blocked', [])
        if blocked_holdings:
            print(f"\n[URGENT] BLOCKED HOLDINGS TO SELL:")
            print("-"*40)
            for blocked in blocked_holdings:
                print(f"• SELL {blocked['symbol']}: {blocked['concerns'][0]['reason'][:60]}...")
                if blocked.get('alternatives'):
                    print(f"  Green alternatives: {', '.join(blocked['alternatives'][:3])}")
        
        # Green opportunities
        green_opportunities = []
        mission_critical = result.get('mission_critical', [])
        priority = result.get('priority', [])
        
        if len(mission_critical) + len(priority) < 3:  # Less than 3 green investments
            print(f"\n[OPPORTUNITY] TOP GREEN INVESTMENTS TO CONSIDER:")
            print("-"*50)
            
            # Get top recommendations from the ethics manager
            green_stocks = ethics_analyzer.ethics_manager.green_whitelist
            top_recommendations = sorted(green_stocks.values(), 
                                       key=lambda x: (x.priority, x.esg_score), 
                                       reverse=True)[:5]
            
            for stock in top_recommendations:
                priority_text = {4: "MISSION CRITICAL", 3: "PRIORITY", 2: "PREFERRED"}.get(stock.priority, "STANDARD")
                print(f"• {stock.symbol} ({priority_text}): {stock.reason[:60]}...")
                print(f"  ESG Score: {stock.esg_score}/10 | Category: {stock.category.replace('_', ' ').title()}")
        
        # Daily brief
        print(f"\n[BRIEF] DAILY SUSTAINABILITY SUMMARY")
        print("="*80)
        daily_brief = ethics_analyzer.generate_daily_ethics_brief(your_portfolio)
        print(daily_brief)
        
        # Action recommendations
        print(f"\n[ACTION] TODAY'S RECOMMENDATIONS")
        print("-"*50)
        
        current_green = allocation.get('green_value_percent', 0)
        if current_green < 0.30:
            print(f"1. INCREASE GREEN ALLOCATION: Currently {current_green:.1%}, target 30%")
            print(f"   Recommended investment: ${(0.30 - current_green) * allocation['total_value']:.0f}")
        
        if blocked_holdings:
            print(f"2. SELL BLOCKED HOLDINGS: {len(blocked_holdings)} positions violate ethics standards")
            for blocked in blocked_holdings[:2]:
                print(f"   • Sell {blocked['symbol']} → Buy {blocked['alternatives'][0] if blocked.get('alternatives') else 'Green alternative'}")
        
        if len(mission_critical) == 0:
            print(f"3. ADD MISSION-CRITICAL GREEN: Consider FSLR, ICLN, XYL, VWDRY, or EOSE")
        
        if allocation.get('mission_critical_value_percent', 0) < 0.20:
            print(f"4. INCREASE EARTH PRESERVATION: Target 20% in mission-critical green investments")
        
        print(f"\n[SUCCESS] Daily ethics check complete!")
        print("Update your portfolio and run this script daily for optimal sustainability.")
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()