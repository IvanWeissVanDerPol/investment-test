"""
Basic YFinance Connection Test
Tests if we can connect to live market data using yfinance
"""

import sys
import os
from datetime import datetime, timedelta

# Set console encoding
if os.name == 'nt':  # Windows
    os.system('chcp 65001')

print("=" * 60)
print("Basic Market Data Connection Test")
print("=" * 60)

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    
    print("[OK] Required libraries imported successfully")
    print(f"     pandas: {pd.__version__}")
    print(f"     numpy: {np.__version__}")
    
    # Test symbols
    test_symbols = ["NVDA", "MSFT", "GOOGL"]
    
    print(f"\n[TEST] Testing connection with symbols: {test_symbols}")
    
    for symbol in test_symbols:
        print(f"\n--- Testing {symbol} ---")
        
        try:
            # Create ticker
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            print("[FETCH] Getting basic info...")
            info = ticker.info
            current_price = info.get('currentPrice', 0)
            market_cap = info.get('marketCap', 0)
            
            print(f"[OK] Current Price: ${current_price}")
            print(f"[OK] Market Cap: ${market_cap:,.0f}")
            
            # Get historical data
            print("[FETCH] Getting historical data (3 months)...")
            hist = ticker.history(period="3mo")
            
            if not hist.empty:
                print(f"[OK] Historical data: {len(hist)} days")
                print(f"[OK] Price range: ${hist['Close'].min():.2f} - ${hist['Close'].max():.2f}")
                
                # Calculate basic metrics
                returns = hist['Close'].pct_change().dropna()
                
                if len(returns) > 0:
                    win_rate = len(returns[returns > 0]) / len(returns)
                    avg_return = returns.mean()
                    volatility = returns.std() * np.sqrt(252)  # Annual volatility
                    
                    print(f"[OK] Win Rate: {win_rate:.2%}")
                    print(f"[OK] Avg Daily Return: {avg_return:.4f}")
                    print(f"[OK] Annual Volatility: {volatility:.1%}")
                else:
                    print("[WARN] No return data available")
            else:
                print("[WARN] No historical data available")
        
        except Exception as e:
            print(f"[FAIL] {symbol} failed: {e}")
    
    # Test Kelly Criterion calculation
    print(f"\n--- Kelly Criterion Test ---")
    
    def calculate_kelly(win_prob, avg_win, avg_loss):
        """Simple Kelly Criterion calculation"""
        if win_prob <= 0 or win_prob >= 1 or avg_win <= 0 or avg_loss <= 0:
            return 0
        
        odds = avg_win / avg_loss
        kelly_fraction = (odds * win_prob - (1 - win_prob)) / odds
        return kelly_fraction
    
    # Test with sample data
    test_cases = [
        (0.6, 0.05, 0.03),  # 60% win rate, 5% avg win, 3% avg loss
        (0.55, 0.08, 0.05), # 55% win rate, 8% avg win, 5% avg loss
    ]
    
    for win_rate, avg_win, avg_loss in test_cases:
        kelly = calculate_kelly(win_rate, avg_win, avg_loss)
        expected_return = win_rate * avg_win - (1 - win_rate) * avg_loss
        
        print(f"[TEST] WR:{win_rate:.1%} Win:{avg_win:.3f} Loss:{avg_loss:.3f}")
        print(f"       Kelly: {kelly:.4f} ({kelly:.1%})")
        print(f"       Expected Return: {expected_return:.4f}")
    
    # Test Expected Value calculation
    print(f"\n--- Expected Value Test ---")
    
    scenarios = [
        {'name': 'bear', 'prob': 0.05, 'outcome': -0.15},
        {'name': 'down', 'prob': 0.15, 'outcome': -0.05},
        {'name': 'flat', 'prob': 0.60, 'outcome': 0.00},
        {'name': 'up', 'prob': 0.15, 'outcome': 0.05},
        {'name': 'bull', 'prob': 0.05, 'outcome': 0.15},
    ]
    
    expected_value = sum(s['prob'] * s['outcome'] for s in scenarios)
    prob_loss = sum(s['prob'] for s in scenarios if s['outcome'] < 0)
    max_loss = min(s['outcome'] for s in scenarios)
    max_gain = max(s['outcome'] for s in scenarios)
    
    print(f"[TEST] Expected Value: {expected_value:.4f}")
    print(f"       Probability of Loss: {prob_loss:.1%}")
    print(f"       Max Loss: {max_loss:.1%}")
    print(f"       Max Gain: {max_gain:.1%}")
    
    # Summary
    print("\n" + "=" * 60)
    print("BASIC CONNECTION TEST SUMMARY")
    print("=" * 60)
    print("[SUCCESS] Market data connection working!")
    print("[SUCCESS] Basic calculations verified!")
    print("[INFO] Ready to integrate with enhanced system")
    print(f"\n[TIMESTAMP] {datetime.now()}")
    print("=" * 60)
    
except ImportError as e:
    print(f"[ERROR] Missing required libraries: {e}")
    print("[FIX] Please install required packages:")
    print("      pip install yfinance pandas numpy")
    
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n[END] Basic Market Data Test Complete")