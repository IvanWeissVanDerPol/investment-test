#!/usr/bin/env python3
"""
YouTube Market Intelligence Cycle Runner

Runs complete market intelligence analysis across all YouTube stock analysis
channels and generates actionable investment signals for the AI decision engine.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from investment_system.analysis import get_market_intelligence

def save_intelligence_report(report: Dict[str, Any], output_dir: str = "reports"):
    """Save complete intelligence report with multiple formats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save complete JSON report
    json_file = output_path / f"market_intelligence_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Save executive summary
    summary_file = output_path / f"intelligence_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        write_executive_summary(f, report)
    
    # Save investment signals CSV
    signals_file = output_path / f"investment_signals_{timestamp}.csv"
    save_signals_csv(signals_file, report.get('investment_signals', {}))
    
    print(f"💾 Intelligence report saved:")
    print(f"   📊 Complete report: {json_file}")
    print(f"   📋 Executive summary: {summary_file}")
    print(f"   📈 Investment signals: {signals_file}")
    
    return json_file

def write_executive_summary(file, report: Dict[str, Any]):
    """Write executive summary to file"""
    metadata = report.get('metadata', {})
    market_overview = report.get('market_overview', {})
    signals = report.get('investment_signals', {})
    
    file.write("YOUTUBE MARKET INTELLIGENCE - EXECUTIVE SUMMARY\n")
    file.write("=" * 60 + "\n\n")
    
    # Metadata
    file.write(f"Generated: {metadata.get('generated_at', 'Unknown')}\n")
    file.write(f"Analysis Period: {metadata.get('days_analyzed', 0)} days\n")
    file.write(f"Processing Time: {metadata.get('processing_time_seconds', 0):.1f} seconds\n")
    file.write(f"Channels Processed: {metadata.get('channels_processed', 0)}\n")
    file.write(f"Videos Analyzed: {metadata.get('total_videos', 0)}\n")
    file.write(f"Stocks Covered: {metadata.get('stocks_analyzed', 0)}\n")
    file.write(f"Investment Signals: {metadata.get('signals_generated', 0)}\n\n")
    
    # Market Overview
    file.write("MARKET OVERVIEW\n")
    file.write("-" * 20 + "\n")
    
    overall_sentiment = market_overview.get('overall_market_sentiment', 0.0)
    sentiment_emoji = "📈" if overall_sentiment > 0.1 else "📉" if overall_sentiment < -0.1 else "➡️"
    file.write(f"Overall Market Sentiment: {sentiment_emoji} {overall_sentiment:.3f}\n")
    file.write(f"Market Uncertainty: {market_overview.get('market_uncertainty', 0.0):.3f}\n")
    file.write(f"Analyst Consensus Strength: {market_overview.get('analyst_consensus_strength', 0.0):.3f}\n\n")
    
    # Top Buy Signals
    buy_signals = market_overview.get('top_buy_signals', [])
    if buy_signals:
        file.write("TOP BUY SIGNALS\n")
        file.write("-" * 20 + "\n")
        for i, signal in enumerate(buy_signals[:5], 1):
            file.write(f"{i}. {signal['symbol']} - {signal['signal_type'].upper()}\n")
            file.write(f"   Confidence: {signal['confidence']:.2f}\n")
            file.write(f"   Analysts: {signal['analysts_covering']}\n")
            file.write(f"   Sentiment: {signal['sentiment_score']:.2f}\n")
            if signal.get('price_target_consensus'):
                file.write(f"   Price Target: ${signal['price_target_consensus']:.2f}\n")
            file.write("\n")
    
    # Top Sell Signals
    sell_signals = market_overview.get('top_sell_signals', [])
    if sell_signals:
        file.write("TOP SELL SIGNALS\n")
        file.write("-" * 20 + "\n")
        for i, signal in enumerate(sell_signals[:3], 1):
            file.write(f"{i}. {signal['symbol']} - {signal['signal_type'].upper()}\n")
            file.write(f"   Confidence: {signal['confidence']:.2f}\n")
            file.write(f"   Analysts: {signal['analysts_covering']}\n")
            file.write(f"   Sentiment: {signal['sentiment_score']:.2f}\n\n")
    
    # Most Discussed Stocks
    most_discussed = market_overview.get('most_discussed_stocks', [])
    if most_discussed:
        file.write("MOST DISCUSSED STOCKS\n")
        file.write("-" * 20 + "\n")
        for i, symbol in enumerate(most_discussed[:10], 1):
            signal_info = signals.get(symbol, {})
            signal_type = signal_info.get('signal_type', 'No Signal')
            file.write(f"{i:2d}. {symbol:6s} - {signal_type}\n")
        file.write("\n")
    
    # Trending Topics
    trending = market_overview.get('trending_topics', [])
    if trending:
        file.write("TRENDING TOPICS\n")
        file.write("-" * 20 + "\n")
        for topic in trending[:10]:
            file.write(f"• {topic}\n")
        file.write("\n")
    
    # Investment Recommendations
    file.write("INVESTMENT RECOMMENDATIONS\n")
    file.write("-" * 30 + "\n")
    
    strong_buys = [s for s in signals.values() if s.get('signal_type') == 'strong_buy']
    buys = [s for s in signals.values() if s.get('signal_type') == 'buy']
    sells = [s for s in signals.values() if s.get('signal_type') in ['sell', 'strong_sell']]
    
    if strong_buys:
        file.write("STRONG BUY RECOMMENDATIONS:\n")
        for signal in sorted(strong_buys, key=lambda x: x['confidence'], reverse=True)[:3]:
            file.write(f"• {signal['symbol']} (Confidence: {signal['confidence']:.2f})\n")
        file.write("\n")
    
    if buys:
        file.write("BUY RECOMMENDATIONS:\n")
        for signal in sorted(buys, key=lambda x: x['confidence'], reverse=True)[:5]:
            file.write(f"• {signal['symbol']} (Confidence: {signal['confidence']:.2f})\n")
        file.write("\n")
    
    if sells:
        file.write("SELL/AVOID RECOMMENDATIONS:\n")
        for signal in sorted(sells, key=lambda x: x['confidence'], reverse=True)[:3]:
            file.write(f"• {signal['symbol']} (Confidence: {signal['confidence']:.2f})\n")
        file.write("\n")
    
    # Risk Assessment
    file.write("RISK ASSESSMENT\n")
    file.write("-" * 20 + "\n")
    uncertainty = market_overview.get('market_uncertainty', 0.0)
    if uncertainty > 0.7:
        file.write("⚠️  HIGH UNCERTAINTY - Exercise caution with new positions\n")
    elif uncertainty > 0.4:
        file.write("⚡ MODERATE UNCERTAINTY - Normal risk management applies\n")
    else:
        file.write("✅ LOW UNCERTAINTY - Favorable conditions for investment\n")
    
    file.write(f"\nRisk Sentiment: {market_overview.get('risk_sentiment', 0.0):.3f}\n")
    file.write(f"Volatility Expectations: {market_overview.get('volatility_expectations', 'Unknown')}\n\n")
    
    file.write("=" * 60 + "\n")
    file.write("This analysis is based on YouTube content from global stock analysts.\n")
    file.write("Combine with fundamental analysis and risk management for best results.\n")

def save_signals_csv(filename: Path, signals: Dict[str, Dict]):
    """Save investment signals in CSV format"""
    import csv
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = [
            'symbol', 'signal_type', 'confidence', 'sentiment_score',
            'analysts_covering', 'total_mentions', 'price_target_consensus',
            'signal_strength', 'data_freshness', 'analyst_quality_score',
            'primary_recommendation', 'geographic_regions'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for symbol, signal in signals.items():
            # Flatten geographic consensus
            geo_regions = ', '.join(signal.get('geographic_consensus', {}).keys())
            
            row = {
                'symbol': symbol,
                'signal_type': signal.get('signal_type', ''),
                'confidence': signal.get('confidence', 0.0),
                'sentiment_score': signal.get('sentiment_score', 0.0),
                'analysts_covering': signal.get('analysts_covering', 0),
                'total_mentions': signal.get('total_mentions', 0),
                'price_target_consensus': signal.get('price_target_consensus', ''),
                'signal_strength': signal.get('signal_strength', 0.0),
                'data_freshness': signal.get('data_freshness', 0.0),
                'analyst_quality_score': signal.get('analyst_quality_score', 0.0),
                'primary_recommendation': signal.get('analyst_consensus', {}).get('buy', 0),
                'geographic_regions': geo_regions
            }
            writer.writerow(row)

def print_live_summary(report: Dict[str, Any]):
    """Print live summary to console"""
    metadata = report.get('metadata', {})
    market_overview = report.get('market_overview', {})
    signals = report.get('investment_signals', {})
    
    print("\n" + "=" * 60)
    print("🧠 YOUTUBE MARKET INTELLIGENCE SUMMARY")
    print("=" * 60)
    
    # Quick stats
    print(f"⏱️  Processing Time: {metadata.get('processing_time_seconds', 0):.1f}s")
    print(f"📺 Channels: {metadata.get('channels_processed', 0)}")
    print(f"🎬 Videos: {metadata.get('total_videos', 0)}")
    print(f"📈 Stocks: {metadata.get('stocks_analyzed', 0)}")
    print(f"🎯 Signals: {metadata.get('signals_generated', 0)}")
    
    # Market sentiment
    sentiment = market_overview.get('overall_market_sentiment', 0.0)
    sentiment_emoji = "📈" if sentiment > 0.1 else "📉" if sentiment < -0.1 else "➡️"
    print(f"🌍 Market Sentiment: {sentiment_emoji} {sentiment:.3f}")
    
    # Top signals
    buy_signals = market_overview.get('top_buy_signals', [])
    sell_signals = market_overview.get('top_sell_signals', [])
    
    if buy_signals:
        print(f"\n🚀 TOP BUY SIGNALS:")
        for signal in buy_signals[:3]:
            print(f"   • {signal['symbol']} - {signal['signal_type']} (confidence: {signal['confidence']:.2f})")
    
    if sell_signals:
        print(f"\n⚠️  TOP SELL SIGNALS:")
        for signal in sell_signals[:3]:
            print(f"   • {signal['symbol']} - {signal['signal_type']} (confidence: {signal['confidence']:.2f})")
    
    # Most discussed
    discussed = market_overview.get('most_discussed_stocks', [])[:5]
    if discussed:
        print(f"\n💬 MOST DISCUSSED: {', '.join(discussed)}")
    
    # Trending topics
    trending = market_overview.get('trending_topics', [])[:5]
    if trending:
        print(f"🔥 TRENDING: {', '.join(trending)}")
    
    print("\n" + "=" * 60)

def main():
    """Main intelligence cycle runner"""
    parser = argparse.ArgumentParser(description='Run YouTube Market Intelligence Cycle')
    parser.add_argument('--days', type=int, default=1, help='Days to analyze (default: 1)')
    parser.add_argument('--output', type=str, default='reports', help='Output directory (default: reports)')
    parser.add_argument('--quiet', action='store_true', help='Minimal console output')
    parser.add_argument('--no-save', action='store_true', help='Skip saving reports')
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv('YOUTUBE_API_KEY'):
        print("❌ YOUTUBE_API_KEY environment variable not set")
        print("📋 Please set up YouTube API access first:")
        print("   See docs/guides/youtube_api_setup.md")
        return
    
    # Initialize intelligence engine
    if not args.quiet:
        print("🧠 Initializing YouTube Market Intelligence Engine...")
    
    try:
        intelligence = get_market_intelligence()
        if not args.quiet:
            print(f"✅ Initialized with {len(intelligence.channels)} channels")
    except Exception as e:
        print(f"❌ Failed to initialize intelligence engine: {e}")
        return
    
    # Run intelligence cycle
    if not args.quiet:
        print(f"🔄 Running intelligence cycle ({args.days} days)...")
        print("   This may take several minutes depending on content volume...")
    
    try:
        report = intelligence.run_full_intelligence_cycle(days_back=args.days)
        
        if not args.quiet:
            print("✅ Intelligence cycle completed successfully!")
            print_live_summary(report)
        
        # Save reports
        if not args.no_save:
            report_file = save_intelligence_report(report, args.output)
            
            if not args.quiet:
                print(f"\n🎯 Intelligence ready for AI investment decisions!")
                print(f"📊 Load report: {report_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Intelligence cycle interrupted by user")
    except Exception as e:
        print(f"❌ Intelligence cycle failed: {e}")
        import traceback
        if not args.quiet:
            traceback.print_exc()

if __name__ == "__main__":
    main()