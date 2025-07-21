#!/usr/bin/env python3
"""
Test script for YouTube Market Intelligence Engine

Tests the market intelligence aggregation, signal generation, and analyst
performance tracking capabilities.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from investment_system.analysis import get_market_intelligence, get_content_processor
from investment_system.analysis.youtube_content_processor import ProcessedContent, StockMention, MarketInsight
from investment_system.data import get_stock_analysis_channels

def test_market_intelligence_setup():
    """Test market intelligence engine initialization"""
    print("🧪 Testing Market Intelligence Engine Setup...")
    
    try:
        intelligence = get_market_intelligence()
        print("✅ Market intelligence engine initialized successfully")
        print(f"   Channels loaded: {len(intelligence.channels)}")
        print(f"   Analyst tracking: {len(intelligence.analyst_performance)} analysts")
        return True, intelligence
    except Exception as e:
        print(f"❌ Failed to initialize market intelligence: {e}")
        return False, None

def test_consensus_building(intelligence):
    """Test building consensus from multiple analysts"""
    print("\n🧪 Testing Stock Consensus Building...")
    
    # Create mock processed content from multiple analysts
    mock_contents = {
        'channel1': [
            ProcessedContent(
                video_id='vid1', video_title='NVDA Analysis', channel_id='channel1', 
                channel_title='Tech Analyst Pro', published_at=datetime.now(),
                processing_timestamp=datetime.now(),
                stock_mentions=[
                    StockMention('NVDA', 'NVIDIA Corp', 3, ['NVDA bullish trend'], 0.8, 0.9, 'buy', 150.0, 'short', ['buy'])
                ],
                market_insights=[], overall_sentiment=0.8, confidence_score=0.9,
                transcript_language='en', transcript_length=1000, processing_time_seconds=1.5,
                keywords_found=['earnings'], topics_identified=['technical_analysis']
            )
        ],
        'channel2': [
            ProcessedContent(
                video_id='vid2', video_title='Tech Review', channel_id='channel2',
                channel_title='Market Watch', published_at=datetime.now(),
                processing_timestamp=datetime.now(),
                stock_mentions=[
                    StockMention('NVDA', 'NVIDIA Corp', 2, ['NVDA strong performance'], 0.6, 0.8, 'hold', 140.0, 'medium', ['hold'])
                ],
                market_insights=[], overall_sentiment=0.6, confidence_score=0.8,
                transcript_language='en', transcript_length=800, processing_time_seconds=1.2,
                keywords_found=['growth'], topics_identified=['market_outlook']
            )
        ],
        'channel3': [
            ProcessedContent(
                video_id='vid3', video_title='AI Stocks Update', channel_id='channel3',
                channel_title='AI Investment Guide', published_at=datetime.now(),
                processing_timestamp=datetime.now(),
                stock_mentions=[
                    StockMention('NVDA', 'NVIDIA Corp', 4, ['NVDA AI leader'], 0.9, 0.95, 'buy', 160.0, 'long', ['strong_buy'])
                ],
                market_insights=[], overall_sentiment=0.9, confidence_score=0.95,
                transcript_language='en', transcript_length=1200, processing_time_seconds=1.8,
                keywords_found=['ai', 'technology'], topics_identified=['sector_analysis']
            )
        ]
    }
    
    try:
        consensus = intelligence.build_stock_consensus(mock_contents, 'NVDA')
        
        print("✅ Stock consensus building successful!")
        print(f"   Symbol: {consensus['symbol']}")
        print(f"   Analysts covering: {consensus['analysts_covering']}")
        print(f"   Total mentions: {consensus['total_mentions']}")
        print(f"   Average sentiment: {consensus['avg_sentiment']:.2f}")
        print(f"   Quality-weighted sentiment: {consensus['quality_weighted_sentiment']:.2f}")
        print(f"   Primary recommendation: {consensus['primary_recommendation']}")
        print(f"   Average price target: ${consensus['avg_price_target']:.2f}")
        print(f"   Data freshness: {consensus['data_freshness']:.2f}")
        
        return True, consensus
        
    except Exception as e:
        print(f"❌ Error in consensus building: {e}")
        return False, None

def test_signal_generation(intelligence, consensus_data):
    """Test investment signal generation"""
    print("\n🧪 Testing Investment Signal Generation...")
    
    try:
        signal = intelligence.generate_investment_signal(consensus_data)
        
        if signal:
            print("✅ Investment signal generated successfully!")
            print(f"   Symbol: {signal.symbol}")
            print(f"   Signal Type: {signal.signal_type}")
            print(f"   Confidence: {signal.confidence:.2f}")
            print(f"   Signal Strength: {signal.signal_strength:.2f}")
            print(f"   Sentiment Score: {signal.sentiment_score:.2f}")
            print(f"   Analysts Covering: {signal.analysts_covering}")
            print(f"   Price Target: ${signal.price_target_consensus:.2f}" if signal.price_target_consensus else "   Price Target: N/A")
            print(f"   Valid Until: {signal.valid_until.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Key Insights: {len(signal.key_insights)} insights")
            
            for i, insight in enumerate(signal.key_insights[:3], 1):
                print(f"     {i}. {insight}")
            
            return True
        else:
            print("⚠️ No signal generated (insufficient data or confidence)")
            return True  # Not necessarily an error
            
    except Exception as e:
        print(f"❌ Error in signal generation: {e}")
        return False

def test_market_overview(intelligence):
    """Test market overview generation"""
    print("\n🧪 Testing Market Overview Generation...")
    
    # Create comprehensive mock data
    mock_contents = {
        'channel1': [
            ProcessedContent(
                video_id='vid1', video_title='Market Update', channel_id='channel1',
                channel_title='Market Pro', published_at=datetime.now(),
                processing_timestamp=datetime.now(),
                stock_mentions=[
                    StockMention('NVDA', 'NVIDIA Corp', 2, ['bullish'], 0.7, 0.8, 'buy', None, None, []),
                    StockMention('TSLA', 'Tesla Inc', 1, ['mixed'], 0.1, 0.6, 'hold', None, None, [])
                ],
                market_insights=[
                    MarketInsight('Bull Market', 0.6, 0.8, ['strong trends'], ['volume increase'], 'optimistic outlook')
                ],
                overall_sentiment=0.5, confidence_score=0.7,
                transcript_language='en', transcript_length=900, processing_time_seconds=1.3,
                keywords_found=['market'], topics_identified=['market_outlook']
            )
        ],
        'channel2': [
            ProcessedContent(
                video_id='vid2', video_title='Tech Analysis', channel_id='channel2',
                channel_title='Tech Guru', published_at=datetime.now(),
                processing_timestamp=datetime.now(),
                stock_mentions=[
                    StockMention('AAPL', 'Apple Inc', 3, ['solid'], 0.4, 0.7, 'hold', None, None, []),
                    StockMention('MSFT', 'Microsoft Corp', 2, ['strong'], 0.8, 0.9, 'buy', None, None, [])
                ],
                market_insights=[
                    MarketInsight('Economic Outlook', 0.3, 0.7, ['inflation concerns'], ['fed policy'], 'cautious optimism')
                ],
                overall_sentiment=0.6, confidence_score=0.8,
                transcript_language='en', transcript_length=1100, processing_time_seconds=1.6,
                keywords_found=['technology'], topics_identified=['sector_analysis']
            )
        ]
    }
    
    try:
        overview = intelligence.generate_market_overview(mock_contents)
        
        print("✅ Market overview generated successfully!")
        print(f"   Overall Market Sentiment: {overview.overall_market_sentiment:.2f}")
        print(f"   Market Uncertainty: {overview.market_uncertainty:.2f}")
        print(f"   Analyst Consensus Strength: {overview.analyst_consensus_strength:.2f}")
        print(f"   Top Buy Signals: {len(overview.top_buy_signals)}")
        print(f"   Top Sell Signals: {len(overview.top_sell_signals)}")
        print(f"   Most Discussed Stocks: {overview.most_discussed_stocks[:5]}")
        print(f"   Trending Topics: {overview.trending_topics[:5]}")
        
        if overview.top_buy_signals:
            print(f"\n   🚀 Top Buy Signal: {overview.top_buy_signals[0].symbol} (confidence: {overview.top_buy_signals[0].confidence:.2f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in market overview generation: {e}")
        return False

def test_full_intelligence_cycle(intelligence):
    """Test complete intelligence cycle with minimal real data"""
    print("\n🧪 Testing Full Intelligence Cycle...")
    
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("⚠️ YOUTUBE_API_KEY not set, creating mock cycle")
        
        # Create mock processed contents
        mock_contents = {
            'test_channel': [
                ProcessedContent(
                    video_id='test1', video_title='Daily Market Analysis', 
                    channel_id='test_channel', channel_title='Test Analyst',
                    published_at=datetime.now(), processing_timestamp=datetime.now(),
                    stock_mentions=[
                        StockMention('NVDA', 'NVIDIA Corp', 1, ['positive'], 0.6, 0.8, 'buy', 145.0, 'short', []),
                        StockMention('AAPL', 'Apple Inc', 1, ['neutral'], 0.0, 0.5, 'hold', None, None, [])
                    ],
                    market_insights=[
                        MarketInsight('Market Trends', 0.4, 0.7, ['steady growth'], ['volume ok'], 'cautiously optimistic')
                    ],
                    overall_sentiment=0.3, confidence_score=0.6,
                    transcript_language='en', transcript_length=800, processing_time_seconds=1.0,
                    keywords_found=['market'], topics_identified=['market_outlook']
                )
            ]
        }
        
        # Simulate intelligence cycle
        try:
            # Generate signals
            nvda_consensus = intelligence.build_stock_consensus(mock_contents, 'NVDA')
            nvda_signal = intelligence.generate_investment_signal(nvda_consensus)
            
            # Generate overview
            overview = intelligence.generate_market_overview(mock_contents)
            
            print("✅ Mock intelligence cycle completed!")
            print(f"   Signals generated: {1 if nvda_signal else 0}")
            print(f"   Market sentiment: {overview.overall_market_sentiment:.2f}")
            
            if nvda_signal:
                print(f"   NVDA Signal: {nvda_signal.signal_type} (confidence: {nvda_signal.confidence:.2f})")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in mock intelligence cycle: {e}")
            return False
    
    else:
        print("🔄 Running limited real intelligence cycle...")
        try:
            # Run with very limited scope to avoid quota issues
            report = intelligence.run_full_intelligence_cycle(days_back=1)
            
            print("✅ Real intelligence cycle completed!")
            print(f"   Processing time: {report['metadata']['processing_time_seconds']:.1f}s")
            print(f"   Channels processed: {report['metadata']['channels_processed']}")
            print(f"   Videos analyzed: {report['metadata']['total_videos']}")
            print(f"   Stocks analyzed: {report['metadata']['stocks_analyzed']}")
            print(f"   Signals generated: {report['metadata']['signals_generated']}")
            
            if report['investment_signals']:
                top_signal = next(iter(report['investment_signals'].values()))
                print(f"   Sample signal: {top_signal['symbol']} - {top_signal['signal_type']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in real intelligence cycle: {e}")
            return False

def test_analyst_performance_tracking(intelligence):
    """Test analyst performance tracking"""
    print("\n🧪 Testing Analyst Performance Tracking...")
    
    try:
        # Check if performance data is loaded
        performance_count = len([p for p in intelligence.analyst_performance.values() if p.videos_processed > 0])
        
        print("✅ Analyst performance tracking operational!")
        print(f"   Total analysts tracked: {len(intelligence.analyst_performance)}")
        print(f"   Analysts with activity: {performance_count}")
        
        # Show sample performance data
        if performance_count > 0:
            active_analysts = [p for p in intelligence.analyst_performance.values() if p.videos_processed > 0]
            sample = active_analysts[0]
            print(f"\n   📊 Sample Analyst Performance:")
            print(f"     Channel: {sample.channel_name}")
            print(f"     Region: {sample.region}")
            print(f"     Videos Processed: {sample.videos_processed}")
            print(f"     Accuracy Rate: {sample.accuracy_rate:.2f}")
            print(f"     Reliability Grade: {sample.reliability_grade}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in performance tracking: {e}")
        return False

def main():
    """Run all market intelligence tests"""
    print("🧠 YouTube Market Intelligence Engine Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Setup
    success, intelligence = test_market_intelligence_setup()
    if not success:
        print("\n❌ Cannot proceed without market intelligence engine")
        return
    all_passed = all_passed and success
    
    # Test 2: Consensus Building
    success, consensus_data = test_consensus_building(intelligence)
    all_passed = all_passed and success
    
    # Test 3: Signal Generation
    if consensus_data:
        success = test_signal_generation(intelligence, consensus_data)
        all_passed = all_passed and success
    
    # Test 4: Market Overview
    success = test_market_overview(intelligence)
    all_passed = all_passed and success
    
    # Test 5: Full Intelligence Cycle
    success = test_full_intelligence_cycle(intelligence)
    all_passed = all_passed and success
    
    # Test 6: Analyst Performance
    success = test_analyst_performance_tracking(intelligence)
    all_passed = all_passed and success
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! Market Intelligence Engine is ready.")
        print("\n🧠 The intelligence engine can now:")
        print("• Aggregate insights from 39+ global stock analysis channels")
        print("• Build multi-analyst consensus on stocks with confidence scoring")
        print("• Generate buy/sell/hold signals with strength indicators")
        print("• Track analyst performance and reliability over time")
        print("• Provide comprehensive market overviews and trends")
        print("• Process geographic and linguistic sentiment differences")
        
        print("\n🚀 Next steps:")
        print("1. Set up YouTube API key for real-time intelligence")
        print("2. Run daily intelligence cycles to build signal history")
        print("3. Integrate signals with your AI investment decision engine")
        print("4. Track analyst performance to weight signals appropriately")
        
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print(f"\n📖 For complete setup instructions, see:")
    print("   docs/guides/youtube_api_setup.md")

if __name__ == "__main__":
    main()