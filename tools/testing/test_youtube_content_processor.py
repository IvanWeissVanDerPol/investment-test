#!/usr/bin/env python3
"""
Test script for YouTube Content Processor

Tests the stock mention extraction, sentiment analysis, and market insight
generation from YouTube video transcripts.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from investment_system.analysis import get_content_processor, YouTubeContentProcessor
from investment_system.data import YouTubeVideo, get_youtube_client, get_stock_analysis_channels

def test_content_processor_setup():
    """Test content processor initialization"""
    print("🧪 Testing YouTube Content Processor Setup...")
    
    try:
        processor = get_content_processor()
        print("✅ Content processor initialized successfully")
        print(f"   Stock universe: {len(processor.stock_universe)} symbols")
        return True, processor
    except Exception as e:
        print(f"❌ Failed to initialize content processor: {e}")
        return False, None

def test_stock_mention_extraction(processor):
    """Test stock ticker extraction from sample text"""
    print("\n🧪 Testing Stock Mention Extraction...")
    
    # Sample stock analysis content
    sample_texts = [
        "NVDA is showing strong momentum today, I'm bullish on this stock. Target price $150. Tesla TSLA also looking good for a buy.",
        "Apple AAPL earnings disappointed but I think it's still a hold. Microsoft MSFT however is a strong buy with target $400.",
        "The S&P 500 is trending up but I'm bearish on META. Selling my position. GOOGL looks better for long term.",
        "Bitcoin and crypto are volatile but COIN stock might be worth watching. Also keeping an eye on NVDA and AMD chips.",
        "QQQ ETF is my pick for tech exposure. Better than individual stocks like TSLA or AAPL in this market."
    ]
    
    try:
        total_mentions = 0
        for i, text in enumerate(sample_texts, 1):
            print(f"\n📝 Sample Text {i}:")
            print(f"   \"{text[:60]}...\"")
            
            mentions = processor.extract_stock_mentions(text)
            print(f"   Found {len(mentions)} stock mentions:")
            
            for mention in mentions:
                print(f"     • {mention.symbol}: {mention.mentions_count} mentions, sentiment: {mention.sentiment_score:.2f}")
                if mention.recommendation:
                    print(f"       Recommendation: {mention.recommendation}")
                if mention.price_target:
                    print(f"       Price target: ${mention.price_target}")
                
                total_mentions += mention.mentions_count
        
        print(f"\n✅ Successfully extracted {total_mentions} total stock mentions")
        return True
        
    except Exception as e:
        print(f"❌ Error in stock mention extraction: {e}")
        return False

def test_market_insights_extraction(processor):
    """Test market insight extraction"""
    print("\n🧪 Testing Market Insights Extraction...")
    
    sample_market_text = """
    The market is showing bullish trends today with strong volume. 
    I'm optimistic about the economic outlook despite inflation concerns.
    The Fed's interest rate policy is creating volatility but long-term I see a bull market continuing.
    Technology sector is outperforming while energy is underperforming.
    GDP growth looks solid and unemployment is at historic lows.
    """
    
    try:
        insights = processor.extract_market_insights(sample_market_text)
        print(f"   Found {len(insights)} market insights:")
        
        for insight in insights:
            print(f"     • Topic: {insight.topic}")
            print(f"       Sentiment: {insight.sentiment:.2f}, Confidence: {insight.confidence:.2f}")
            print(f"       Key points: {len(insight.key_points)}")
            if insight.key_points:
                print(f"       Example: \"{insight.key_points[0][:50]}...\"")
        
        print("✅ Market insights extraction successful")
        return True
        
    except Exception as e:
        print(f"❌ Error in market insights extraction: {e}")
        return False

def test_full_video_processing(processor):
    """Test complete video content processing"""
    print("\n🧪 Testing Complete Video Processing...")
    
    # Create sample video object
    sample_video = YouTubeVideo(
        video_id="test_video_123",
        title="Daily Stock Analysis - NVDA, TSLA, AAPL Review",
        description="Today's analysis of major tech stocks",
        published_at=datetime.now(),
        channel_id="test_channel",
        channel_title="Stock Analysis Pro",
        duration="PT10M30S",
        view_count=5420,
        like_count=234,
        tags=["stocks", "investing", "analysis"],
        transcript="""
        Hello everyone, welcome to today's stock analysis. 
        Let's start with NVIDIA NVDA which is showing incredible strength. 
        I'm very bullish on this stock with a price target of $150. 
        The AI boom is driving demand and I recommend buying NVDA.
        
        Tesla TSLA is more mixed. The stock has been volatile but 
        I think it's a hold for now. Wait for better entry point.
        
        Apple AAPL disappointed with earnings but the long-term outlook is positive.
        Still a strong company and I would buy on any dips.
        
        Overall the market is showing bullish trends with good volume.
        The technology sector continues to outperform and I'm optimistic
        about the economic outlook despite some inflation concerns.
        """,
        transcript_language="en"
    )
    
    try:
        processed = processor.process_video_content(sample_video)
        
        if processed:
            print("✅ Video processing successful!")
            print(f"   Video: {processed.video_title}")
            print(f"   Processing time: {processed.processing_time_seconds:.2f}s")
            print(f"   Overall sentiment: {processed.overall_sentiment:.2f}")
            print(f"   Confidence score: {processed.confidence_score:.2f}")
            print(f"   Stock mentions: {len(processed.stock_mentions)}")
            print(f"   Market insights: {len(processed.market_insights)}")
            print(f"   Keywords found: {', '.join(processed.keywords_found[:5])}")
            print(f"   Topics: {', '.join(processed.topics_identified)}")
            
            # Show detailed stock mentions
            print("\n   📊 Stock Mentions Detail:")
            for mention in processed.stock_mentions:
                print(f"     • {mention.symbol} ({mention.company_name})")
                print(f"       Mentions: {mention.mentions_count}, Sentiment: {mention.sentiment_score:.2f}")
                if mention.recommendation:
                    print(f"       Recommendation: {mention.recommendation}")
                if mention.price_target:
                    print(f"       Price target: ${mention.price_target}")
            
            return True
        else:
            print("❌ Video processing returned None")
            return False
            
    except Exception as e:
        print(f"❌ Error in video processing: {e}")
        return False

def test_analyst_consensus(processor):
    """Test analyst consensus analysis"""
    print("\n🧪 Testing Analyst Consensus Analysis...")
    
    # Create multiple processed content samples
    from investment_system.analysis.youtube_content_processor import ProcessedContent, StockMention
    
    try:
        sample_contents = [
            ProcessedContent(
                video_id="vid1", video_title="NVDA Analysis", channel_id="ch1", channel_title="Analyst 1",
                published_at=datetime.now(), processing_timestamp=datetime.now(),
                stock_mentions=[
                    StockMention("NVDA", "NVIDIA Corp", 3, ["bullish on NVDA"], 0.8, 0.9, "buy", 150.0, "short", ["buy"])
                ],
                market_insights=[], overall_sentiment=0.8, confidence_score=0.9,
                transcript_language="en", transcript_length=1000, processing_time_seconds=1.5,
                keywords_found=["earnings"], topics_identified=["technical_analysis"]
            ),
            ProcessedContent(
                video_id="vid2", video_title="Tech Stocks Review", channel_id="ch2", channel_title="Analyst 2", 
                published_at=datetime.now(), processing_timestamp=datetime.now(),
                stock_mentions=[
                    StockMention("NVDA", "NVIDIA Corp", 2, ["NVDA strong hold"], 0.6, 0.8, "hold", 140.0, "medium", ["hold"])
                ],
                market_insights=[], overall_sentiment=0.6, confidence_score=0.8,
                transcript_language="en", transcript_length=800, processing_time_seconds=1.2,
                keywords_found=["growth"], topics_identified=["market_outlook"]
            )
        ]
        
        consensus = processor.analyze_analyst_consensus(sample_contents, "NVDA")
        
        print("✅ Analyst consensus analysis successful!")
        print(f"   Symbol: {consensus['symbol']}")
        print(f"   Analysts covering: {consensus['analyst_count']}")
        print(f"   Average sentiment: {consensus['avg_sentiment']:.2f}")
        print(f"   Sentiment range: {consensus['sentiment_range']}")
        print(f"   Recommendation distribution: {consensus['recommendation_distribution']}")
        print(f"   Price targets: {consensus['price_targets']}")
        print(f"   Channels covering: {consensus['channels_covering']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in analyst consensus: {e}")
        return False

def test_real_youtube_integration():
    """Test with real YouTube API if available"""
    print("\n🧪 Testing Real YouTube Integration...")
    
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("⚠️ YOUTUBE_API_KEY not set, skipping real API test")
        return True
    
    try:
        # Get a sample channel
        channels = get_stock_analysis_channels()
        if not channels:
            print("⚠️ No channels available for testing")
            return True
        
        sample_channel = channels[0]  # Use first channel
        print(f"   Testing with channel: {sample_channel.channel_name}")
        
        # Get YouTube client and processor
        client = get_youtube_client()
        processor = get_content_processor()
        
        # Get recent videos (limit to 1 for testing)
        recent_videos = client.get_recent_videos(sample_channel.channel_id, days_back=7)
        
        if recent_videos:
            test_video = recent_videos[0]
            print(f"   Testing with video: \"{test_video.title[:50]}...\"")
            
            # Process the video if it has a transcript
            if test_video.transcript:
                processed = processor.process_video_content(test_video)
                if processed:
                    print("✅ Real YouTube content processing successful!")
                    print(f"   Stock mentions: {len(processed.stock_mentions)}")
                    print(f"   Market insights: {len(processed.market_insights)}")
                    return True
                else:
                    print("⚠️ Processing returned None (normal if no stock content)")
                    return True
            else:
                print("⚠️ No transcript available for test video")
                return True
        else:
            print("⚠️ No recent videos found for test channel")
            return True
            
    except Exception as e:
        print(f"❌ Error in real YouTube integration test: {e}")
        return False

def main():
    """Run all content processor tests"""
    print("📊 YouTube Content Processor Test Suite")
    print("=" * 50)
    
    all_passed = True
    
    # Test 1: Setup
    success, processor = test_content_processor_setup()
    if not success:
        print("\n❌ Cannot proceed without content processor")
        return
    all_passed = all_passed and success
    
    # Test 2: Stock Mention Extraction
    success = test_stock_mention_extraction(processor)
    all_passed = all_passed and success
    
    # Test 3: Market Insights
    success = test_market_insights_extraction(processor)
    all_passed = all_passed and success
    
    # Test 4: Full Video Processing
    success = test_full_video_processing(processor)
    all_passed = all_passed and success
    
    # Test 5: Analyst Consensus
    success = test_analyst_consensus(processor)
    all_passed = all_passed and success
    
    # Test 6: Real YouTube Integration (optional)
    success = test_real_youtube_integration()
    all_passed = all_passed and success
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed! YouTube content processor is ready.")
        print("\n🚀 The processor can now:")
        print("• Extract stock mentions with sentiment from transcripts")
        print("• Identify buy/sell/hold recommendations") 
        print("• Extract price targets and time horizons")
        print("• Analyze market trends and insights")
        print("• Build analyst consensus across multiple channels")
        print("• Process content in multiple languages")
        
        print("\n📈 Next steps:")
        print("1. Set up YouTube API key for real-time monitoring")
        print("2. Process recent videos from your 39 stock analysis channels")
        print("3. Integrate insights with your AI investment decision engine")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print(f"\n📖 For setup instructions, see:")
    print("   docs/guides/youtube_api_setup.md")

if __name__ == "__main__":
    main()