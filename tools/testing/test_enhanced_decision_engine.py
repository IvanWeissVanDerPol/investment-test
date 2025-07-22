#!/usr/bin/env python3
"""
Test script for Enhanced AI Investment Decision Engine

Tests the integration of YouTube market intelligence with AI analysis and ethics
screening to create comprehensive investment decisions.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from investment_system.ai import get_enhanced_decision_engine

def safe_print(text):
    """Print text with fallback for Unicode encoding issues"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Remove emojis and use ASCII alternatives
        fallback = text.replace("🧪", "[TEST]").replace("✅", "[PASS]").replace("❌", "[FAIL]")
        fallback = fallback.replace("🚀", "[START]").replace("⚠️", "[WARN]").replace("💾", "[SAVE]")
        fallback = fallback.replace("🎬", "[YT]").replace("♻️", "[ECO]").replace("🤖", "[AI]")
        fallback = fallback.replace("📊", "[DATA]").replace("🎯", "[TARGET]").replace("📖", "[DOC]")
        print(fallback)

def test_enhanced_engine_setup():
    """Test enhanced decision engine initialization"""
    safe_print("🧪 Testing Enhanced Decision Engine Setup...")
    
    try:
        engine = get_enhanced_decision_engine()
        safe_print("✅ Enhanced decision engine initialized successfully")
        print(f"   YouTube intelligence: {len(engine.youtube_intelligence.channels)} channels")
        print(f"   Decision weights: {engine.decision_weights}")
        print(f"   YouTube weights: {engine.youtube_weights}")
        return True, engine
    except Exception as e:
        safe_print(f"❌ Failed to initialize enhanced decision engine: {e}")
        return False, None

def test_comprehensive_decision_analysis(engine, symbol="NVDA"):
    """Test comprehensive investment decision analysis"""
    safe_print(f"\n🧪 Testing Comprehensive Decision Analysis for {symbol}...")
    
    # Sample portfolio context
    portfolio_context = {
        'total_value': 900.00,
        'cash_available': 200.00,
        'current_positions': {
            'AAPL': {'shares': 1, 'value': 150.00},
            'TSLA': {'shares': 2, 'value': 300.00},
            'ICLN': {'shares': 10, 'value': 250.00}
        },
        'green_allocation_target': 0.30,
        'risk_tolerance': 'medium',
        'investment_horizon': 'long_term'
    }
    
    try:
        print(f"   Running analysis for {symbol}...")
        decision = engine.analyze_investment_decision(symbol, portfolio_context, 'buy')
        
        safe_print("✅ Comprehensive decision analysis completed!")
        print(f"   Processing time: {decision.get('processing_time_seconds', 0):.1f}s")
        print(f"   Recommendation: {decision['recommendation'].upper()}")
        print(f"   Overall score: {decision['overall_score']:.3f}")
        print(f"   Confidence level: {decision['confidence_level']}")
        print(f"   Position size: {decision['position_size_recommendation']}")
        
        # Component scores
        print(f"\n   📊 Component Scores:")
        components = decision['component_scores']
        for component, score in components.items():
            print(f"     • {component.replace('_', ' ').title()}: {score:.3f}")
        
        # YouTube intelligence
        youtube_summary = decision['youtube_intelligence_summary']
        print(f"\n   🎬 YouTube Intelligence:")
        print(f"     • Has coverage: {youtube_summary['has_coverage']}")
        print(f"     • Analyst count: {youtube_summary['analyst_count']}")
        print(f"     • Total mentions: {youtube_summary['total_mentions']}")
        print(f"     • Sentiment: {youtube_summary['sentiment']:.2f}")
        if youtube_summary['primary_recommendation']:
            print(f"     • Primary rec: {youtube_summary['primary_recommendation']}")
        if youtube_summary['signal_type']:
            print(f"     • Signal type: {youtube_summary['signal_type']}")
            print(f"     • Signal confidence: {youtube_summary['signal_confidence']:.2f}")
        
        # Ethics summary
        ethics_summary = decision['ethics_summary']
        print(f"\n   ♻️ Ethics Summary:")
        print(f"     • Green investment: {ethics_summary['is_green_investment']}")
        print(f"     • ESG score: {ethics_summary['esg_score']}")
        print(f"     • Sustainability rating: {ethics_summary['sustainability_rating']}")
        
        # Risk assessment
        risk = decision['risk_assessment']
        print(f"\n   ⚠️ Risk Assessment:")
        print(f"     • Risk level: {risk['risk_level']}")
        if risk['risk_factors']:
            print(f"     • Risk factors: {len(risk['risk_factors'])}")
            for factor in risk['risk_factors'][:2]:
                print(f"       - {factor}")
        
        # Key insights
        if decision['key_insights']:
            print(f"\n   💡 Key Insights:")
            for insight in decision['key_insights'][:3]:
                print(f"     • {insight}")
        
        # Action items
        if decision['action_items']:
            print(f"\n   🎯 Action Items:")
            for action in decision['action_items'][:3]:
                print(f"     • {action}")
        
        return True, decision
        
    except Exception as e:
        safe_print(f"❌ Error in comprehensive decision analysis: {e}")
        return False, None

def test_multiple_stock_analysis(engine):
    """Test analysis across multiple stocks"""
    print(f"\n🧪 Testing Multiple Stock Analysis...")
    
    test_symbols = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'ICLN']
    portfolio_context = {
        'total_value': 900.00,
        'cash_available': 300.00,
        'green_allocation_target': 0.30,
        'risk_tolerance': 'medium'
    }
    
    results = []
    
    try:
        for symbol in test_symbols:
            print(f"   Analyzing {symbol}...")
            decision = engine.analyze_investment_decision(symbol, portfolio_context, 'buy')
            
            results.append({
                'symbol': symbol,
                'recommendation': decision['recommendation'],
                'overall_score': decision['overall_score'],
                'confidence': decision['confidence_level'],
                'youtube_coverage': decision['youtube_intelligence_summary']['has_coverage'],
                'is_green': decision['ethics_summary']['is_green_investment']
            })
        
        print("✅ Multiple stock analysis completed!")
        print(f"\n   📊 Results Summary:")
        print("   Symbol  | Recommendation | Score | Confidence | YouTube | Green")
        print("   --------|----------------|-------|------------|---------|-------")
        
        for result in results:
            youtube_icon = "✓" if result['youtube_coverage'] else "✗"
            green_icon = "🌱" if result['is_green'] else "💼"
            print(f"   {result['symbol']:6s} | {result['recommendation']:14s} | {result['overall_score']:.3f} | {result['confidence']:10s} | {youtube_icon:7s} | {green_icon}")
        
        # Find best recommendations
        strong_buys = [r for r in results if r['recommendation'] == 'strong_buy']
        buys = [r for r in results if r['recommendation'] == 'buy']
        
        if strong_buys:
            print(f"\n   🚀 Strong Buy Recommendations: {[r['symbol'] for r in strong_buys]}")
        if buys:
            print(f"   📈 Buy Recommendations: {[r['symbol'] for r in buys]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in multiple stock analysis: {e}")
        return False

def test_decision_components(engine):
    """Test individual decision components"""
    print(f"\n🧪 Testing Decision Components...")
    
    portfolio_context = {'total_value': 900, 'risk_tolerance': 'medium'}
    
    try:
        # Test with different scenarios
        scenarios = [
            ('NVDA', 'High-profile AI stock'),
            ('ICLN', 'Green energy ETF'),
            ('XOM', 'Traditional energy (potential ethics conflict)')
        ]
        
        for symbol, description in scenarios:
            print(f"\n   Testing {symbol} ({description}):")
            decision = engine.analyze_investment_decision(symbol, portfolio_context, 'buy')
            
            print(f"     Recommendation: {decision['recommendation']}")
            print(f"     Ethics score: {decision['component_scores']['ethics_score']:.3f}")
            print(f"     YouTube score: {decision['component_scores']['youtube_intelligence_score']:.3f}")
            print(f"     Overall score: {decision['overall_score']:.3f}")
            print(f"     Green investment: {decision['ethics_summary']['is_green_investment']}")
            print(f"     YouTube coverage: {decision['youtube_intelligence_summary']['has_coverage']}")
        
        print("✅ Decision components testing completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in decision components testing: {e}")
        return False

def test_cache_functionality(engine):
    """Test caching functionality for performance"""
    print(f"\n🧪 Testing Cache Functionality...")
    
    portfolio_context = {'total_value': 900}
    symbol = 'AAPL'
    
    try:
        # First analysis (should be fresh)
        start_time = datetime.now()
        decision1 = engine.analyze_investment_decision(symbol, portfolio_context, 'buy')
        first_time = (datetime.now() - start_time).total_seconds()
        
        # Second analysis (should use cache)
        start_time = datetime.now()
        decision2 = engine.analyze_investment_decision(symbol, portfolio_context, 'buy')
        second_time = (datetime.now() - start_time).total_seconds()
        
        print("✅ Cache functionality test completed!")
        print(f"   First analysis: {first_time:.2f}s")
        print(f"   Cached analysis: {second_time:.2f}s")
        print(f"   Cache speedup: {first_time/second_time:.1f}x faster")
        print(f"   Results match: {decision1['overall_score'] == decision2['overall_score']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in cache functionality test: {e}")
        return False

def test_save_decision_report(decisions):
    """Save decision analysis report"""
    print(f"\n💾 Saving Decision Analysis Report...")
    
    try:
        # Create reports directory
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"enhanced_decisions_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(decisions, f, indent=2, default=str)
        
        print(f"✅ Decision report saved: {report_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving decision report: {e}")
        return False

def main():
    """Run all enhanced decision engine tests"""
    safe_print("🚀 Enhanced AI Investment Decision Engine Test Suite")
    print("=" * 65)
    
    # Check YouTube API availability
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        safe_print("⚠️ YOUTUBE_API_KEY not set - some features may be limited")
    
    all_passed = True
    decisions = []
    
    # Test 1: Setup
    success, engine = test_enhanced_engine_setup()
    if not success:
        print("\n❌ Cannot proceed without enhanced decision engine")
        return
    all_passed = all_passed and success
    
    # Test 2: Comprehensive Decision Analysis
    success, decision = test_comprehensive_decision_analysis(engine)
    if decision:
        decisions.append(decision)
    all_passed = all_passed and success
    
    # Test 3: Multiple Stock Analysis
    success = test_multiple_stock_analysis(engine)
    all_passed = all_passed and success
    
    # Test 4: Decision Components
    success = test_decision_components(engine)
    all_passed = all_passed and success
    
    # Test 5: Cache Functionality
    success = test_cache_functionality(engine)
    all_passed = all_passed and success
    
    # Test 6: Save Report
    if decisions:
        success = test_save_decision_report(decisions)
        all_passed = all_passed and success
    
    # Summary
    print("\n" + "=" * 65)
    if all_passed:
        print("✅ All tests passed! Enhanced Decision Engine is ready.")
        print("\n🚀 The enhanced engine now combines:")
        print("• ♻️ Ethics screening and sustainability analysis")
        print("• 🤖 Claude AI market insights and analysis")
        print("• 🎬 YouTube intelligence from 39+ global analysts")
        print("• 📊 Multi-dimensional confidence scoring")
        print("• ⚠️ Comprehensive risk assessment")
        print("• 🎯 Actionable investment recommendations")
        
        print("\n🎯 Next steps:")
        print("1. Run daily enhanced decision analysis")
        print("2. Integrate with automated trading systems")
        print("3. Build performance tracking dashboard")
        print("4. Set up automated reporting")
        
        if not api_key:
            print("\n📋 To unlock full YouTube intelligence:")
            print("   Set YOUTUBE_API_KEY environment variable")
            print("   See docs/guides/youtube_api_setup.md")
        
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print(f"\n📖 For complete integration guide, see:")
    print("   docs/guides/enhanced_decision_engine.md")

if __name__ == "__main__":
    main()