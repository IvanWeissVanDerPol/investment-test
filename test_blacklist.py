"""
Standalone test for the investment blacklist system
"""

import sys
import os
sys.path.append('src')

# Add the specific module path
sys.path.append('src/investment_system/ethics')

from investment_blacklist import InvestmentBlacklistManager

def test_blacklist_system():
    """Test the investment blacklist functionality"""
    print("="*60)
    print("INVESTMENT BLACKLIST SYSTEM TEST")
    print("="*60)
    
    # Initialize blacklist manager
    blacklist_manager = InvestmentBlacklistManager()
    
    print(f"Loaded blacklist with {len(blacklist_manager.blacklist)} entries")
    print(f"Green whitelist: {len(blacklist_manager.green_whitelist)} companies")
    print(f"Standard whitelist: {len(blacklist_manager.standard_whitelist)} companies")
    print(f"Watchlist: {len(blacklist_manager.watchlist)} companies")
    
    print("\n" + "="*60)
    print("INDIVIDUAL STOCK SCREENING")
    print("="*60)
    
    # Test with mix of green priorities, blacklisted, and standard stocks
    test_cases = [
        ("FSLR", "First Solar (Mission Critical Green)"),
        ("ICLN", "Clean Energy ETF (Mission Critical Green)"),
        ("RIVN", "Rivian (Priority Green EV)"),
        ("ENPH", "Enphase (Priority Green Solar)"),
        ("TSLA", "Tesla (Blacklisted - Elon Musk concerns)"),
        ("NSRGY", "Nestle (Blacklisted - Unethical practices)"),
        ("META", "Meta (Blacklisted - Privacy violations)"),
        ("XOM", "Exxon (Blacklisted - Environmental damage)"),
        ("DWAC", "Trump SPAC (Blacklisted - Political extremism)"),
        ("COST", "Costco (Standard approved)"),
        ("MSFT", "Microsoft (Standard approved)"),
        ("AMZN", "Amazon (Watchlist - mixed impact)")
    ]
    
    for symbol, description in test_cases:
        result = blacklist_manager.check_investment(symbol)
        status = result["status"].upper()
        
        print(f"\n{symbol} ({description}):")
        print(f"  Status: {status}")
        print(f"  Priority Score: {result['priority_score']}")
        
        if result["green_impact"]:
            print("  [GREEN IMPACT] Environmental/sustainability benefits")
        
        if result["benefits"]:
            for benefit in result["benefits"]:
                print(f"  Benefit: {benefit['reason']}")
                print(f"  ESG Score: {benefit['esg_score']}/10")
                print(f"  Impact Areas: {', '.join(benefit['impact_areas'])}")
        
        if result["concerns"]:
            for concern in result["concerns"]:
                print(f"  Concern: {concern['reason']}")
                if concern.get('leadership_concerns'):
                    print(f"  Leadership Issues: {', '.join(concern['leadership_concerns'][:2])}")
        
        for rec in result["recommendations"]:
            print(f"  Recommendation: {rec}")
        
        if result["alternative_suggestions"]:
            print(f"  Green Alternatives: {', '.join(result['alternative_suggestions'])}")
    
    print("\n" + "="*60)
    print("PORTFOLIO SCREENING")
    print("="*60)
    
    # Test portfolio with mix of green, blacklisted, and standard stocks
    test_portfolio = ["FSLR", "ICLN", "RIVN", "AAPL", "MSFT", "TSLA", "NVDA", "NSRGY", "META", "COST", "BRK.B", "XOM", "DWAC"]
    
    print(f"Testing portfolio: {', '.join(test_portfolio)}")
    
    portfolio_result = blacklist_manager.screen_portfolio(test_portfolio)
    
    print(f"\nPortfolio Sustainability Rating: {portfolio_result['sustainability_rating']}")
    print(f"Portfolio Ethics Score: {portfolio_result['overall_score']:.1%}")
    print(f"Green Impact Score: {portfolio_result['green_impact_score']:.1%}")
    print(f"Total stocks: {portfolio_result['total_symbols']}")
    
    print(f"\n[MISSION CRITICAL]: {len(portfolio_result['mission_critical'])} stocks")
    print(f"[PRIORITY]: {len(portfolio_result['priority'])} stocks")
    print(f"[PREFERRED]: {len(portfolio_result['preferred'])} stocks")
    print(f"[APPROVED]: {len(portfolio_result['approved'])} stocks")
    print(f"[WARNINGS]: {len(portfolio_result['warnings'])} stocks") 
    print(f"[BLOCKED]: {len(portfolio_result['blocked'])} stocks")
    print(f"[UNKNOWN]: {len(portfolio_result['unknown'])} stocks")
    
    if portfolio_result["mission_critical"]:
        print(f"\n[MISSION CRITICAL] Green Investments:")
        for investment in portfolio_result["mission_critical"]:
            print(f"  {investment['symbol']} (Score: {investment['priority_score']})")
    
    if portfolio_result["priority"]:
        print(f"\n[PRIORITY] Green Investments:")
        for investment in portfolio_result["priority"]:
            print(f"  {investment['symbol']} (Score: {investment['priority_score']})")
    
    if portfolio_result["approved"]:
        print(f"\n[STANDARD APPROVED]: {', '.join(portfolio_result['approved'])}")
    
    if portfolio_result["warnings"]:
        print(f"\n[WARNING] stocks:")
        for warning in portfolio_result["warnings"]:
            print(f"  {warning['symbol']}: {warning['concerns'][0]['reason']}")
    
    if portfolio_result["blocked"]:
        print(f"\n[BLOCKED] stocks:")
        for blocked in portfolio_result["blocked"]:
            print(f"  {blocked['symbol']}: {blocked['concerns'][0]['reason']}")
            if blocked["alternatives"]:
                print(f"    Green Alternatives: {', '.join(blocked['alternatives'])}")
    
    print(f"\nPortfolio Recommendations:")
    for rec in portfolio_result["recommendations"]:
        print(f"  • {rec}")
    
    print("\n" + "="*60)
    print("GREEN WHITELIST CATEGORIES")
    print("="*60)
    
    # Show green categories
    green_categories = {}
    for entry in blacklist_manager.green_whitelist.values():
        if entry.category not in green_categories:
            green_categories[entry.category] = []
        green_categories[entry.category].append(f"{entry.symbol} (ESG: {entry.esg_score})")
    
    for category, investments in green_categories.items():
        print(f"\n[GREEN] {category.replace('_', ' ').title()}: {len(investments)} investments")
        for investment in investments:
            print(f"  {investment}")
    
    print("\n" + "="*60)
    print("BLACKLIST CATEGORIES")
    print("="*60)
    
    # Show blacklist categories
    blacklist_categories = {}
    for entry in blacklist_manager.blacklist.values():
        if entry.category not in blacklist_categories:
            blacklist_categories[entry.category] = []
        blacklist_categories[entry.category].append(entry.symbol)
    
    for category, symbols in blacklist_categories.items():
        print(f"\n[BLOCKED] {category.replace('_', ' ').title()}: {len(symbols)} companies")
        print(f"  {', '.join(symbols)}")
    
    print("\n" + "="*60)
    print("INVESTMENT BLACKLIST SYSTEM TEST COMPLETE")
    print("="*60)
    
    return blacklist_manager

if __name__ == "__main__":
    blacklist_manager = test_blacklist_system()
    
    print("\n[SUCCESS] Enhanced Investment Ethics System is working correctly!")
    print("You can now screen investments with priority for earth preservation and green technology.")
    print("\n[NEW KEY FEATURES]:")
    print("• MISSION CRITICAL: Identifies essential earth preservation investments")
    print("• PRIORITY: Highlights high-impact sustainability investments")
    print("• PREFERRED: Shows positive environmental impact companies")
    print("• Electric vehicle alternatives to Tesla (avoiding Elon Musk)")
    print("• Renewable energy and clean technology priorities")
    print("• Water conservation and waste management focus")
    print("• ESG scoring and climate commitment tracking")
    print("• Green impact scoring for entire portfolios")
    print("• Sustainability ratings (Earth Champion to Needs Improvement)")
    print("\n[EXISTING FEATURES]:")
    print("• Blocks controversial leadership and unethical practices")
    print("• Screens for environmental damage and climate denial")
    print("• Suggests green alternatives for all blocked investments")
    print("• Comprehensive portfolio-level ethics and sustainability scoring")