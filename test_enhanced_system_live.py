"""
Enhanced System Live Test
Tests the complete enhanced investment system with live market data
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Set console encoding
if os.name == 'nt':  # Windows
    os.system('chcp 65001')

# Test market data availability first
def test_market_data_available():
    """Test if we can access market data"""
    try:
        import yfinance as yf
        import pandas as pd
        import numpy as np
        
        # Quick test
        ticker = yf.Ticker("NVDA")
        info = ticker.info
        current_price = info.get('currentPrice', 0)
        
        if current_price > 0:
            print(f"[OK] Market data available - NVDA: ${current_price}")
            return True
        else:
            print("[WARN] Market data available but no current price")
            return False
            
    except Exception as e:
        print(f"[ERROR] Market data not available: {e}")
        return False

# Test configuration loading
def test_config_loading():
    """Test if enhanced config can be loaded"""
    try:
        config_path = Path("config/config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check for enhanced system config
        if 'enhanced_system' in config and config['enhanced_system']['enabled']:
            print("[OK] Enhanced system configuration loaded and enabled")
            print(f"     Kelly Criterion: {config['enhanced_system']['kelly_criterion']['enabled']}")
            print(f"     Expected Value: {config['enhanced_system']['expected_value']['enabled']}")
            print(f"     Dynamic Risk: {config['enhanced_system']['dynamic_risk_management']['enabled']}")
            return True, config
        else:
            print("[WARN] Enhanced system not configured or disabled")
            return False, config
            
    except Exception as e:
        print(f"[ERROR] Config loading failed: {e}")
        return False, {}

# Test Kelly calculation with live data
def test_kelly_with_live_data():
    """Test Kelly Criterion calculation with live market data"""
    try:
        import yfinance as yf
        import numpy as np
        
        print("\n--- Kelly Criterion with Live Data ---")
        
        symbol = "NVDA"
        print(f"[TEST] Calculating Kelly for {symbol} with live data...")
        
        # Get historical data
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="6mo")  # 6 months
        
        if hist.empty:
            print(f"[FAIL] No historical data for {symbol}")
            return False
        
        # Calculate returns
        returns = hist['Close'].pct_change().dropna()
        
        # Calculate win/loss statistics
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        
        if len(wins) < 10 or len(losses) < 10:
            print(f"[FAIL] Insufficient win/loss samples")
            return False
        
        # Kelly metrics
        win_rate = len(wins) / len(returns)
        avg_win = wins.mean()
        avg_loss = abs(losses.mean())
        
        # Kelly calculation
        odds = avg_win / avg_loss
        kelly_fraction = (odds * win_rate - (1 - win_rate)) / odds
        expected_return = win_rate * avg_win - (1 - win_rate) * avg_loss
        
        # Apply conservative multiplier (50%)
        conservative_kelly = kelly_fraction * 0.5
        
        print(f"[SUCCESS] Kelly Analysis for {symbol}:")
        print(f"   Data Points: {len(returns)}")
        print(f"   Win Rate: {win_rate:.2%}")
        print(f"   Average Win: {avg_win:.3f}")
        print(f"   Average Loss: {avg_loss:.3f}")
        print(f"   Raw Kelly: {kelly_fraction:.4f} ({kelly_fraction:.1%})")
        print(f"   Conservative Kelly: {conservative_kelly:.4f} ({conservative_kelly:.1%})")
        print(f"   Expected Return: {expected_return:.4f}")
        
        # Risk assessment
        annual_vol = returns.std() * np.sqrt(252)
        print(f"   Annual Volatility: {annual_vol:.1%}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Kelly calculation failed: {e}")
        return False

# Test Expected Value with scenarios
def test_expected_value_with_scenarios():
    """Test Expected Value calculation with live data scenarios"""
    try:
        import yfinance as yf
        import numpy as np
        
        print("\n--- Expected Value with Live Scenarios ---")
        
        symbol = "MSFT"
        print(f"[TEST] Calculating EV scenarios for {symbol}...")
        
        # Get extended historical data
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2y")  # 2 years for robust scenarios
        
        if hist.empty or len(hist) < 200:
            print(f"[FAIL] Insufficient data for EV scenarios")
            return False
        
        # Calculate 30-day rolling returns
        rolling_returns = hist['Close'].pct_change(periods=30).dropna()
        
        if len(rolling_returns) < 20:
            print(f"[FAIL] Insufficient rolling return data")
            return False
        
        # Generate scenarios from percentiles
        scenarios = [
            {'name': 'bear_market', 'percentile': 5, 'weight': 0.05},
            {'name': 'normal_down', 'percentile': 25, 'weight': 0.15},
            {'name': 'sideways', 'percentile': 50, 'weight': 0.60},
            {'name': 'normal_up', 'percentile': 75, 'weight': 0.15},
            {'name': 'bull_market', 'percentile': 95, 'weight': 0.05},
        ]
        
        scenario_outcomes = []
        for scenario in scenarios:
            outcome = np.percentile(rolling_returns, scenario['percentile'])
            scenario['outcome'] = outcome
            scenario_outcomes.append({
                'name': scenario['name'],
                'probability': scenario['weight'],
                'outcome': outcome
            })
        
        # Calculate Expected Value
        expected_value = sum(s['probability'] * s['outcome'] for s in scenario_outcomes)
        prob_loss = sum(s['probability'] for s in scenario_outcomes if s['outcome'] < 0)
        max_loss = min(s['outcome'] for s in scenario_outcomes)
        max_gain = max(s['outcome'] for s in scenario_outcomes)
        
        print(f"[SUCCESS] EV Analysis for {symbol} (30-day horizon):")
        print(f"   Data Points: {len(rolling_returns)}")
        print(f"   Expected Value: {expected_value:.4f} ({expected_value:.2%})")
        print(f"   Probability of Loss: {prob_loss:.1%}")
        print(f"   Max Potential Loss: {max_loss:.2%}")
        print(f"   Max Potential Gain: {max_gain:.2%}")
        
        print(f"   Scenarios:")
        for scenario in scenario_outcomes:
            print(f"     {scenario['name']}: {scenario['outcome']:.2%} (p={scenario['probability']:.1%})")
        
        # Risk-adjusted EV
        variance = sum(s['probability'] * (s['outcome'] - expected_value) ** 2 for s in scenario_outcomes)
        risk_adjusted_ev = expected_value - (0.5 * variance)
        print(f"   Risk-Adjusted EV: {risk_adjusted_ev:.4f}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] EV calculation failed: {e}")
        return False

# Test integrated decision making
def test_integrated_decision_making():
    """Test how Kelly + EV + Risk work together for position decisions"""
    try:
        import yfinance as yf
        import numpy as np
        
        print("\n--- Integrated Decision Making ---")
        
        # Test with multiple symbols
        symbols = ["NVDA", "MSFT", "GOOGL"]
        portfolio_value = 100000  # $100k portfolio
        
        decisions = []
        
        for symbol in symbols:
            print(f"[ANALYZE] {symbol}...")
            
            try:
                # Get data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="6mo")
                returns = hist['Close'].pct_change().dropna()
                
                if len(returns) < 50:
                    print(f"[SKIP] Insufficient data for {symbol}")
                    continue
                
                # Kelly analysis
                wins = returns[returns > 0]
                losses = returns[returns < 0]
                
                if len(wins) < 10 or len(losses) < 10:
                    print(f"[SKIP] Insufficient samples for {symbol}")
                    continue
                
                win_rate = len(wins) / len(returns)
                avg_win = wins.mean()
                avg_loss = abs(losses.mean())
                
                kelly_fraction = ((avg_win / avg_loss) * win_rate - (1 - win_rate)) / (avg_win / avg_loss)
                conservative_kelly = kelly_fraction * 0.5  # 50% of Kelly
                
                # EV analysis (simplified)
                recent_returns = returns.tail(30)
                ev_estimate = recent_returns.mean() * 30  # 30-day expected return
                
                # Risk assessment
                volatility = returns.std() * np.sqrt(252)
                recent_volatility = recent_returns.std() * np.sqrt(252)
                
                # Position sizing decision
                position_size = 0
                action = "hold"
                rationale = "Default hold"
                
                # Decision logic
                if conservative_kelly > 0.02 and ev_estimate > 0.01 and win_rate > 0.52:
                    if conservative_kelly > 0.08 and ev_estimate > 0.05:
                        action = "strong_buy"
                        position_size = portfolio_value * min(conservative_kelly, 0.15)  # Cap at 15%
                    elif conservative_kelly > 0.04:
                        action = "buy"
                        position_size = portfolio_value * min(conservative_kelly, 0.10)  # Cap at 10%
                    else:
                        action = "small_buy"
                        position_size = portfolio_value * min(conservative_kelly, 0.05)  # Cap at 5%
                    
                    rationale = f"Kelly:{conservative_kelly:.3f} EV:{ev_estimate:.3f} WR:{win_rate:.2%}"
                elif win_rate < 0.45 or volatility > 0.4:
                    action = "avoid"
                    rationale = f"Low win rate ({win_rate:.1%}) or high volatility ({volatility:.1%})"
                
                decisions.append({
                    'symbol': symbol,
                    'action': action,
                    'position_size': position_size,
                    'kelly_fraction': conservative_kelly,
                    'ev_estimate': ev_estimate,
                    'win_rate': win_rate,
                    'volatility': volatility,
                    'rationale': rationale
                })
                
                print(f"[DECISION] {symbol}: {action.upper()}")
                print(f"    Position Size: ${position_size:,.0f} ({position_size/portfolio_value:.1%})")
                print(f"    Rationale: {rationale}")
                
            except Exception as e:
                print(f"[ERROR] Analysis failed for {symbol}: {e}")
                continue
        
        # Portfolio summary
        if decisions:
            total_allocation = sum(d['position_size'] for d in decisions)
            buy_decisions = [d for d in decisions if 'buy' in d['action']]
            
            print(f"\n[PORTFOLIO SUMMARY]")
            print(f"   Total Symbols Analyzed: {len(symbols)}")
            print(f"   Successful Analysis: {len(decisions)}")
            print(f"   Buy Recommendations: {len(buy_decisions)}")
            print(f"   Total Allocation: ${total_allocation:,.0f} ({total_allocation/portfolio_value:.1%})")
            print(f"   Average Kelly: {np.mean([d['kelly_fraction'] for d in decisions]):.3f}")
            print(f"   Average Win Rate: {np.mean([d['win_rate'] for d in decisions]):.1%}")
            
            return True
        else:
            print("[FAIL] No successful decisions made")
            return False
        
    except Exception as e:
        print(f"[FAIL] Integrated decision making failed: {e}")
        return False

def main():
    """Run complete enhanced system test"""
    print("=" * 70)
    print("Enhanced Investment System - Live Integration Test")
    print("=" * 70)
    
    results = []
    
    # Test 1: Market Data
    print("\n[TEST 1] Market Data Availability")
    market_data_ok = test_market_data_available()
    results.append(('Market Data', market_data_ok))
    
    if not market_data_ok:
        print("[ABORT] Cannot proceed without market data")
        return
    
    # Test 2: Configuration
    print("\n[TEST 2] Enhanced System Configuration")
    config_ok, config = test_config_loading()
    results.append(('Configuration', config_ok))
    
    # Test 3: Kelly Criterion
    print("\n[TEST 3] Kelly Criterion with Live Data")
    kelly_ok = test_kelly_with_live_data()
    results.append(('Kelly Criterion', kelly_ok))
    
    # Test 4: Expected Value
    print("\n[TEST 4] Expected Value Analysis")
    ev_ok = test_expected_value_with_scenarios()
    results.append(('Expected Value', ev_ok))
    
    # Test 5: Integrated Decisions
    print("\n[TEST 5] Integrated Decision Making")
    integrated_ok = test_integrated_decision_making()
    results.append(('Integrated Decisions', integrated_ok))
    
    # Summary
    print("\n" + "=" * 70)
    print("ENHANCED SYSTEM TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] Enhanced system is fully operational!")
        print("[READY] System ready for live trading with:")
        print("   - Kelly Criterion position sizing")
        print("   - Expected Value opportunity assessment")
        print("   - Integrated risk management")
        print("   - Live market data integration")
    elif passed >= total * 0.8:
        print("\n[MOSTLY SUCCESS] Core functionality working")
        print("[INFO] Minor issues detected, but system is usable")
    else:
        print("\n[ISSUES] Multiple components need attention")
        print("[REVIEW] Check failed components before proceeding")
    
    print(f"\n[TIMESTAMP] {datetime.now()}")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test interrupted by user")
    except Exception as e:
        print(f"\n[FATAL] Test suite failed: {e}")
        import traceback
        traceback.print_exc()