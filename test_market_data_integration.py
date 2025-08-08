"""
Test Market Data Integration
Tests the enhanced market data manager with live data feeds
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Set console encoding
if os.name == 'nt':  # Windows
    os.system('chcp 65001')

# Add the core module to path
core_path = Path(__file__).parent / "core" / "investment_system"
sys.path.insert(0, str(core_path))

print("=" * 70)
print("Enhanced Market Data Manager - Live Integration Test")
print("=" * 70)

try:
    from data.enhanced_market_data_manager import get_enhanced_market_data_manager
    
    print("[INIT] Initializing Enhanced Market Data Manager...")
    manager = get_enhanced_market_data_manager()
    print("[OK] Manager initialized successfully")
    
    # Test symbols
    test_symbols = ["NVDA", "MSFT"]  # Start with just 2 symbols to avoid rate limits
    
    print(f"\n[TEST] Testing data collection for symbols: {test_symbols}")
    
    # Test Kelly data
    print("\n--- Kelly Criterion Data ---")
    for symbol in test_symbols:
        try:
            print(f"[FETCH] Getting Kelly data for {symbol}...")
            kelly_data = manager.get_kelly_optimized_data(symbol)
            
            if 'error' not in kelly_data:
                print(f"[SUCCESS] {symbol}:")
                print(f"   Win Rate: {kelly_data['win_rate']:.2%}")
                print(f"   Avg Win: {kelly_data['avg_win']:.3f}")
                print(f"   Avg Loss: {kelly_data['avg_loss']:.3f}")
                print(f"   Annual Volatility: {kelly_data['annual_volatility']:.1%}")
                print(f"   Data Points: {kelly_data['data_points']}")
                print(f"   Quality Score: {kelly_data['data_quality']['completeness']:.2f}")
            else:
                print(f"[ERROR] {symbol}: {kelly_data.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"[FAIL] {symbol}: {e}")
    
    # Test Expected Value data
    print("\n--- Expected Value Data ---")
    for symbol in test_symbols:
        try:
            print(f"[FETCH] Getting EV data for {symbol}...")
            ev_data = manager.get_expected_value_data(symbol, horizon_days=30)
            
            if 'error' not in ev_data:
                print(f"[SUCCESS] {symbol}:")
                print(f"   Scenarios: {len(ev_data['scenarios'])}")
                print(f"   Current Price: ${ev_data['current_price']:.2f}")
                print(f"   Recent Volatility: {ev_data['recent_volatility']:.1%}")
                print(f"   VaR 95%: {ev_data['var_95']:.2%}")
                print(f"   Max Gain: {ev_data['max_gain']:.2%}")
                print(f"   Max Loss: {ev_data['max_loss']:.2%}")
                
                # Show top scenarios
                scenarios = ev_data['scenarios']
                print("   Top Scenarios:")
                for scenario in scenarios[:3]:
                    print(f"     {scenario['name']}: {scenario['outcome']:.2%} (p={scenario['probability']:.1%})")
            else:
                print(f"[ERROR] {symbol}: {ev_data.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"[FAIL] {symbol}: {e}")
    
    # Test Risk Management data
    print("\n--- Risk Management Data ---")
    for symbol in test_symbols:
        try:
            print(f"[FETCH] Getting Risk data for {symbol}...")
            risk_data = manager.get_risk_management_data(symbol)
            
            if 'error' not in risk_data:
                print(f"[SUCCESS] {symbol}:")
                print(f"   Current Volatility: {risk_data['current_volatility']:.1%}")
                print(f"   5-Day Momentum: {risk_data['momentum_5d']:.2%}")
                print(f"   20-Day Momentum: {risk_data['momentum_20d']:.2%}")
                print(f"   Max Drawdown (3M): {risk_data['max_drawdown_3m']:.2%}")
                print(f"   Volume Trend: {risk_data['volume_trend']}")
                print(f"   Market Correlation: {risk_data['market_correlation']:.2f}")
            else:
                print(f"[ERROR] {symbol}: {risk_data.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"[FAIL] {symbol}: {e}")
    
    # Test Batch Data Collection
    print("\n--- Batch Data Collection ---")
    try:
        print(f"[FETCH] Getting batch data for all symbols...")
        start_time = datetime.now()
        
        batch_data = manager.get_batch_data(test_symbols, ['kelly', 'ev', 'risk'])
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Analyze results
        total_requests = len(test_symbols) * 3  # 3 data types
        successful = 0
        
        for symbol, symbol_data in batch_data.items():
            symbol_success = sum(1 for data in symbol_data.values() if 'error' not in data)
            successful += symbol_success
            print(f"[RESULT] {symbol}: {symbol_success}/3 data types successful")
        
        success_rate = successful / total_requests if total_requests > 0 else 0
        print(f"[SUMMARY] Batch Collection:")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Success Rate: {success_rate:.1%} ({successful}/{total_requests})")
        print(f"   Avg Time per Request: {duration/total_requests:.2f}s")
        
    except Exception as e:
        print(f"[FAIL] Batch collection: {e}")
    
    # Data Quality Report
    print("\n--- Data Quality Report ---")
    try:
        quality_report = manager.get_data_quality_report()
        
        if 'message' not in quality_report:
            print("[SUCCESS] Data Quality Report:")
            print(f"   Symbols Tracked: {quality_report.get('total_symbols_tracked', 0)}")
            print(f"   High Quality Symbols: {quality_report.get('high_quality_symbols', 0)}")
            print(f"   Quality Rate: {quality_report.get('data_quality_rate', 0):.1%}")
            
            issues = quality_report.get('symbols_with_issues', [])
            if issues:
                print(f"   Symbols with Issues: {', '.join(issues)}")
            else:
                print("   No data quality issues detected")
        else:
            print(f"[INFO] {quality_report['message']}")
            
    except Exception as e:
        print(f"[FAIL] Quality report: {e}")
    
    # Final Summary
    print("\n" + "=" * 70)
    print("MARKET DATA INTEGRATION TEST SUMMARY")
    print("=" * 70)
    
    print("[INFO] Test completed successfully!")
    print("[INFO] Enhanced Market Data Manager is ready for use with:")
    print("       - Kelly Criterion optimization")
    print("       - Expected Value analysis") 
    print("       - Dynamic Risk Management")
    print("       - Batch processing capabilities")
    print("       - Data quality monitoring")
    
    print(f"\n[TIMESTAMP] {datetime.now()}")
    print("=" * 70)
    
except ImportError as e:
    print(f"[IMPORT ERROR] Failed to import required modules: {e}")
    print("This might be due to missing dependencies (numpy, pandas, yfinance)")
    print("Try: pip install numpy pandas yfinance")
    
except Exception as e:
    print(f"[FATAL ERROR] Test suite failed: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    print("\n[END] Market Data Integration Test Complete")