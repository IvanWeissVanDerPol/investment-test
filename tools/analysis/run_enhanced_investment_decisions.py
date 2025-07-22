#!/usr/bin/env python3
"""
Enhanced Investment Decisions Runner

Runs comprehensive investment analysis using YouTube intelligence, AI analysis,
and ethics screening for your investment watchlist.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add src to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from investment_system.ai import get_enhanced_decision_engine
from investment_system.utils.config_loader import ConfigurationManager

def load_portfolio_context() -> Dict[str, Any]:
    """Load current portfolio context from configuration"""
    try:
        config_manager = ConfigurationManager()
        config = config_manager.load_config('data')
        
        # Extract portfolio information
        portfolio_context = {
            'total_value': 900.00,  # From Ivan's $900 balance
            'cash_available': 200.00,  # Estimated available cash
            'current_positions': {},  # Would be loaded from actual portfolio
            'green_allocation_target': 0.30,  # 30% green target
            'risk_tolerance': 'medium',
            'investment_horizon': 'long_term',
            'user_profile': {
                'name': 'Ivan',
                'balance': 900.00,
                'risk_tolerance': 'medium',
                'green_investment_target': 30
            }
        }
        
        return portfolio_context
        
    except Exception as e:
        print(f"⚠️ Could not load portfolio context: {e}")
        return {
            'total_value': 900.00,
            'cash_available': 200.00,
            'green_allocation_target': 0.30,
            'risk_tolerance': 'medium'
        }

def load_watchlist() -> List[str]:
    """Load stock watchlist from configuration"""
    try:
        config_manager = ConfigurationManager()
        data_config = config_manager.load_config('data')
        
        # Extract primary stocks from config
        watchlist = []
        
        # AI companies
        ai_companies = data_config.get('companies', {}).get('ai_companies', {})
        primary_ai = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'TSLA', 'META', 'AMZN']
        watchlist.extend([symbol for symbol in primary_ai if symbol in ai_companies])
        
        # Green energy ETFs
        green_etfs = data_config.get('etfs', {}).get('green_energy', {})
        primary_green = ['ICLN', 'QCLN', 'PBW', 'TAN']
        watchlist.extend([symbol for symbol in primary_green if symbol in green_etfs])
        
        # AI/Robotics ETFs
        ai_etfs = data_config.get('etfs', {}).get('ai_robotics', {})
        primary_ai_etfs = ['ARKQ', 'BOTZ', 'ROBO']
        watchlist.extend([symbol for symbol in primary_ai_etfs if symbol in ai_etfs])
        
        if not watchlist:
            # Fallback watchlist
            watchlist = ['NVDA', 'MSFT', 'TSLA', 'AAPL', 'GOOGL', 'ICLN', 'ARKQ', 'QCLN']
        
        return watchlist[:15]  # Limit to 15 stocks for performance
        
    except Exception as e:
        print(f"⚠️ Could not load watchlist from config: {e}")
        # Default watchlist based on Ivan's interests
        return ['NVDA', 'MSFT', 'TSLA', 'AAPL', 'GOOGL', 'META', 'AMZN', 'ICLN', 'QCLN', 'ARKQ', 'BOTZ']

def analyze_watchlist(engine, watchlist: List[str], portfolio_context: Dict) -> List[Dict]:
    """Analyze entire watchlist with enhanced decision engine"""
    results = []
    
    print(f"🔍 Analyzing {len(watchlist)} stocks with enhanced AI decision engine...")
    print("   Combining: YouTube Intelligence + Claude AI + Ethics Screening")
    print("=" * 70)
    
    for i, symbol in enumerate(watchlist, 1):
        print(f"📊 Analyzing {symbol} ({i}/{len(watchlist)})...")
        
        try:
            # Run enhanced decision analysis
            decision = engine.analyze_investment_decision(symbol, portfolio_context, 'buy')
            
            # Add to results
            results.append(decision)
            
            # Show quick summary
            rec = decision['recommendation']
            score = decision['overall_score']
            confidence = decision['confidence_level']
            youtube_coverage = decision['youtube_intelligence_summary']['has_coverage']
            is_green = decision['ethics_summary']['is_green_investment']
            
            # Status indicators
            youtube_icon = "🎬" if youtube_coverage else "❌"
            green_icon = "🌱" if is_green else "💼"
            conf_icon = "🔥" if confidence in ['very_high', 'high'] else "⚡" if confidence == 'medium' else "⚠️"
            
            print(f"   Result: {rec.upper():12s} | Score: {score:.3f} | {conf_icon} {confidence} | {youtube_icon} | {green_icon}")
            
        except Exception as e:
            print(f"   ❌ Error analyzing {symbol}: {e}")
            results.append({
                'symbol': symbol,
                'error': True,
                'error_message': str(e),
                'recommendation': 'hold',
                'overall_score': 0.5
            })
    
    return results

def generate_investment_report(results: List[Dict], portfolio_context: Dict) -> Dict:
    """Generate comprehensive investment report"""
    
    # Categorize recommendations
    strong_buys = [r for r in results if r.get('recommendation') == 'strong_buy' and not r.get('error')]
    buys = [r for r in results if r.get('recommendation') == 'buy' and not r.get('error')]
    holds = [r for r in results if r.get('recommendation') == 'hold' and not r.get('error')]
    sells = [r for r in results if r.get('recommendation') in ['sell', 'strong_sell'] and not r.get('error')]
    avoids = [r for r in results if r.get('recommendation') == 'avoid' and not r.get('error')]
    errors = [r for r in results if r.get('error')]
    
    # Sort by score within each category
    strong_buys.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
    buys.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
    
    # Calculate portfolio recommendations
    available_cash = portfolio_context.get('cash_available', 200)
    total_value = portfolio_context.get('total_value', 900)
    
    # Generate specific investment allocations
    investment_plan = []
    remaining_cash = available_cash
    
    # Allocate to strong buys first
    for stock in strong_buys[:3]:  # Top 3 strong buys
        if remaining_cash > 50:  # Minimum $50 per position
            allocation = min(remaining_cash * 0.4, 150)  # Max $150 per position
            shares = int(allocation / 100)  # Rough estimate assuming $100/share
            if shares > 0:
                investment_plan.append({
                    'symbol': stock['symbol'],
                    'recommendation': stock['recommendation'],
                    'allocation': allocation,
                    'estimated_shares': shares,
                    'rationale': 'Top confidence strong buy signal'
                })
                remaining_cash -= allocation
    
    # Allocate to regular buys
    for stock in buys[:2]:  # Top 2 buys
        if remaining_cash > 30:
            allocation = min(remaining_cash * 0.3, 100)  # Max $100 per position
            shares = int(allocation / 80)  # Estimate
            if shares > 0:
                investment_plan.append({
                    'symbol': stock['symbol'],
                    'recommendation': stock['recommendation'],
                    'allocation': allocation,
                    'estimated_shares': shares,
                    'rationale': 'Solid buy opportunity'
                })
                remaining_cash -= allocation
    
    # Compile report
    report = {
        'analysis_timestamp': datetime.now().isoformat(),
        'portfolio_context': portfolio_context,
        'summary': {
            'total_analyzed': len(results),
            'strong_buys': len(strong_buys),
            'buys': len(buys),
            'holds': len(holds),
            'sells': len(sells),
            'avoids': len(avoids),
            'errors': len(errors)
        },
        'recommendations': {
            'strong_buy': [r['symbol'] for r in strong_buys],
            'buy': [r['symbol'] for r in buys],
            'hold': [r['symbol'] for r in holds],
            'sell': [r['symbol'] for r in sells],
            'avoid': [r['symbol'] for r in avoids]
        },
        'investment_plan': investment_plan,
        'cash_allocation': {
            'available': available_cash,
            'allocated': available_cash - remaining_cash,
            'remaining': remaining_cash,
            'allocation_percentage': ((available_cash - remaining_cash) / available_cash * 100) if available_cash > 0 else 0
        },
        'top_opportunities': strong_buys[:3] + buys[:2],
        'green_investments': [
            r for r in results 
            if r.get('ethics_summary', {}).get('is_green_investment', False) 
            and r.get('recommendation') in ['strong_buy', 'buy']
            and not r.get('error')
        ],
        'youtube_coverage': [
            r for r in results 
            if r.get('youtube_intelligence_summary', {}).get('has_coverage', False)
            and not r.get('error')
        ],
        'detailed_results': results
    }
    
    return report

def save_investment_report(report: Dict, output_dir: str = "reports/ai-analysis") -> str:
    """Save comprehensive investment report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save complete JSON report
    json_file = output_path / f"enhanced_investment_decisions_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Save executive summary
    summary_file = output_path / f"investment_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        write_executive_summary(f, report)
    
    print(f"💾 Investment analysis saved:")
    print(f"   📊 Complete report: {json_file}")
    print(f"   📋 Executive summary: {summary_file}")
    
    return str(json_file)

def write_executive_summary(file, report: Dict):
    """Write executive summary to file"""
    summary = report['summary']
    recommendations = report['recommendations']
    investment_plan = report['investment_plan']
    cash_allocation = report['cash_allocation']
    
    file.write("ENHANCED AI INVESTMENT DECISIONS - EXECUTIVE SUMMARY\n")
    file.write("=" * 60 + "\n\n")
    
    file.write(f"Generated: {report['analysis_timestamp']}\n")
    file.write(f"Portfolio Value: ${report['portfolio_context']['total_value']:.2f}\n")
    file.write(f"Available Cash: ${report['portfolio_context']['cash_available']:.2f}\n\n")
    
    # Analysis summary
    file.write("ANALYSIS SUMMARY\n")
    file.write("-" * 20 + "\n")
    file.write(f"Total Stocks Analyzed: {summary['total_analyzed']}\n")
    file.write(f"Strong Buy Signals: {summary['strong_buys']}\n")
    file.write(f"Buy Signals: {summary['buys']}\n")
    file.write(f"Hold Recommendations: {summary['holds']}\n")
    file.write(f"Sell Signals: {summary['sells']}\n")
    file.write(f"Avoid Recommendations: {summary['avoids']}\n\n")
    
    # Top recommendations
    if recommendations['strong_buy']:
        file.write("🚀 STRONG BUY RECOMMENDATIONS:\n")
        for symbol in recommendations['strong_buy']:
            file.write(f"   • {symbol}\n")
        file.write("\n")
    
    if recommendations['buy']:
        file.write("📈 BUY RECOMMENDATIONS:\n")
        for symbol in recommendations['buy']:
            file.write(f"   • {symbol}\n")
        file.write("\n")
    
    # Investment plan
    if investment_plan:
        file.write("💰 SUGGESTED INVESTMENT PLAN:\n")
        file.write("-" * 30 + "\n")
        total_allocation = sum(plan['allocation'] for plan in investment_plan)
        file.write(f"Total Allocation: ${total_allocation:.2f}\n\n")
        
        for plan in investment_plan:
            file.write(f"{plan['symbol']:6s} - ${plan['allocation']:6.2f} ({plan['estimated_shares']} shares)\n")
            file.write(f"         Rationale: {plan['rationale']}\n\n")
    
    # Green investments
    green_investments = report.get('green_investments', [])
    if green_investments:
        file.write("🌱 GREEN INVESTMENT OPPORTUNITIES:\n")
        for investment in green_investments[:3]:
            symbol = investment['symbol']
            rec = investment['recommendation']
            file.write(f"   • {symbol} - {rec.upper()}\n")
        file.write("\n")
    
    # YouTube coverage
    youtube_coverage = report.get('youtube_coverage', [])
    if youtube_coverage:
        file.write("🎬 STOCKS WITH YOUTUBE ANALYST COVERAGE:\n")
        for stock in youtube_coverage[:5]:
            symbol = stock['symbol']
            analyst_count = stock.get('youtube_intelligence_summary', {}).get('analyst_count', 0)
            file.write(f"   • {symbol} - {analyst_count} analysts\n")
        file.write("\n")
    
    # Cash allocation
    file.write("💵 CASH ALLOCATION:\n")
    file.write("-" * 20 + "\n")
    file.write(f"Available: ${cash_allocation['available']:.2f}\n")
    file.write(f"Allocated: ${cash_allocation['allocated']:.2f} ({cash_allocation['allocation_percentage']:.1f}%)\n")
    file.write(f"Remaining: ${cash_allocation['remaining']:.2f}\n\n")
    
    file.write("=" * 60 + "\n")
    file.write("This analysis combines YouTube intelligence from 39+ global analysts,\n")
    file.write("Claude AI analysis, and comprehensive ethics screening.\n")
    file.write("Always consider your risk tolerance and seek additional research.\n")

def print_live_summary(report: Dict):
    """Print live summary to console"""
    summary = report['summary']
    recommendations = report['recommendations']
    investment_plan = report['investment_plan']
    
    print("\n" + "=" * 70)
    print("🚀 ENHANCED AI INVESTMENT DECISIONS SUMMARY")
    print("=" * 70)
    
    print(f"📊 Analysis: {summary['total_analyzed']} stocks")
    print(f"🎯 Signals: {summary['strong_buys']} strong buy, {summary['buys']} buy, {summary['sells']} sell")
    
    if recommendations['strong_buy']:
        print(f"🚀 STRONG BUYS: {', '.join(recommendations['strong_buy'])}")
    
    if recommendations['buy']:
        print(f"📈 BUYS: {', '.join(recommendations['buy'])}")
    
    if investment_plan:
        total_allocation = sum(plan['allocation'] for plan in investment_plan)
        print(f"\n💰 INVESTMENT PLAN (${total_allocation:.2f} total):")
        for plan in investment_plan:
            print(f"   • {plan['symbol']:6s} - ${plan['allocation']:6.2f}")
    
    # Green and YouTube highlights
    green_count = len(report.get('green_investments', []))
    youtube_count = len(report.get('youtube_coverage', []))
    print(f"\n🌱 Green opportunities: {green_count}")
    print(f"🎬 YouTube coverage: {youtube_count} stocks")
    
    print("=" * 70)

def main():
    """Main investment decisions runner"""
    parser = argparse.ArgumentParser(description='Run Enhanced Investment Decisions')
    parser.add_argument('--symbols', nargs='+', help='Specific symbols to analyze')
    parser.add_argument('--output', type=str, default='reports', help='Output directory')
    parser.add_argument('--quiet', action='store_true', help='Minimal console output')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🚀 Enhanced AI Investment Decision System")
        print("   Combining YouTube Intelligence + Claude AI + Ethics Screening")
        print("=" * 70)
    
    # Initialize components
    try:
        engine = get_enhanced_decision_engine()
        portfolio_context = load_portfolio_context()
        
        if args.symbols:
            watchlist = args.symbols
        else:
            watchlist = load_watchlist()
        
        if not args.quiet:
            print(f"📋 Portfolio: ${portfolio_context['total_value']:.2f} total, ${portfolio_context['cash_available']:.2f} available")
            print(f"🎯 Watchlist: {len(watchlist)} symbols")
        
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return
    
    # Run analysis
    try:
        results = analyze_watchlist(engine, watchlist, portfolio_context)
        report = generate_investment_report(results, portfolio_context)
        
        if not args.quiet:
            print_live_summary(report)
        
        # Save report
        report_file = save_investment_report(report, args.output)
        
        if not args.quiet:
            print(f"\n🎯 Investment decisions ready!")
            print(f"📊 View detailed report: {report_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    main()