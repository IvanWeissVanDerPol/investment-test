#!/usr/bin/env python3
"""
YouTube Channel Monitoring Script

Monitors stock analysis YouTube channels for new content and extracts
actionable investment insights. Designed for daily execution to capture
fresh market analysis from global analysts.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from investment_system.data import get_youtube_client, get_stock_analysis_channels
from investment_system.analysis import get_content_processor

def monitor_channels(days_back: int = 1, max_channels: int = None, 
                    target_symbols: List[str] = None) -> Dict[str, Any]:
    """
    Monitor YouTube channels for new stock analysis content
    
    Args:
        days_back: Number of days to look back for new videos
        max_channels: Maximum number of channels to monitor (None = all)
        target_symbols: Specific stock symbols to focus on (None = all)
        
    Returns:
        Dictionary with monitoring results and insights
    """
    print(f"🎬 Starting YouTube Channel Monitoring")
    print(f"   Lookback period: {days_back} days")
    print(f"   Max channels: {max_channels or 'all'}")
    print(f"   Target symbols: {target_symbols or 'all stocks'}")
    print("=" * 60)
    
    # Initialize components
    try:
        youtube_client = get_youtube_client()
        content_processor = get_content_processor()
        channels = get_stock_analysis_channels()
        
        if max_channels:
            channels = channels[:max_channels]
            
        print(f"✅ Initialized components successfully")
        print(f"📺 Monitoring {len(channels)} channels")
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return {}
    
    # Results storage
    results = {
        'monitoring_timestamp': datetime.now().isoformat(),
        'days_back': days_back,
        'channels_monitored': len(channels),
        'total_videos_found': 0,
        'total_videos_processed': 0,
        'channels_data': {},
        'stock_insights': {},
        'market_insights': [],
        'top_mentioned_stocks': {},
        'analyst_consensus': {}
    }
    
    # Monitor each channel
    for i, channel in enumerate(channels, 1):
        print(f"\n📡 Monitoring Channel {i}/{len(channels)}: {channel.channel_name}")
        print(f"   Region: {channel.region.value}, Language: {channel.language.value}")
        
        try:
            # Get recent videos with transcripts
            recent_videos = youtube_client.get_recent_videos(channel.channel_id, days_back)
            videos_with_transcripts = [v for v in recent_videos if v.transcript]
            
            print(f"   Found {len(recent_videos)} recent videos, {len(videos_with_transcripts)} with transcripts")
            
            if not videos_with_transcripts:
                results['channels_data'][channel.channel_name] = {
                    'videos_found': len(recent_videos),
                    'videos_processed': 0,
                    'stock_mentions': [],
                    'status': 'no_transcripts'
                }
                continue
            
            # Process videos for insights
            channel_insights = []
            channel_stock_mentions = []
            
            for video in videos_with_transcripts:
                processed = content_processor.process_video_content(video)
                if processed and processed.stock_mentions:
                    channel_insights.append(processed)
                    channel_stock_mentions.extend(processed.stock_mentions)
            
            # Filter by target symbols if specified
            if target_symbols:
                channel_stock_mentions = [
                    mention for mention in channel_stock_mentions 
                    if mention.symbol in target_symbols
                ]
            
            # Store channel results
            results['channels_data'][channel.channel_name] = {
                'channel_id': channel.channel_id,
                'region': channel.region.value,
                'language': channel.language.value,
                'videos_found': len(recent_videos),
                'videos_processed': len(channel_insights),
                'stock_mentions': len(channel_stock_mentions),
                'processed_content': [
                    {
                        'video_id': p.video_id,
                        'title': p.video_title,
                        'sentiment': p.overall_sentiment,
                        'stock_count': len(p.stock_mentions),
                        'insights_count': len(p.market_insights)
                    } for p in channel_insights
                ],
                'status': 'success'
            }
            
            # Aggregate stock mentions
            for mention in channel_stock_mentions:
                symbol = mention.symbol
                if symbol not in results['stock_insights']:
                    results['stock_insights'][symbol] = {
                        'symbol': symbol,
                        'company_name': mention.company_name,
                        'total_mentions': 0,
                        'channels_mentioning': set(),
                        'sentiments': [],
                        'recommendations': [],
                        'price_targets': [],
                        'latest_mention': None
                    }
                
                stock_data = results['stock_insights'][symbol]
                stock_data['total_mentions'] += mention.mentions_count
                stock_data['channels_mentioning'].add(channel.channel_name)
                stock_data['sentiments'].append(mention.sentiment_score)
                
                if mention.recommendation:
                    stock_data['recommendations'].append(mention.recommendation)
                if mention.price_target:
                    stock_data['price_targets'].append(mention.price_target)
                
                # Update latest mention
                if (stock_data['latest_mention'] is None or 
                    processed.published_at > stock_data['latest_mention']):
                    stock_data['latest_mention'] = processed.published_at
            
            # Aggregate market insights
            for insight_content in channel_insights:
                results['market_insights'].extend(insight_content.market_insights)
            
            results['total_videos_found'] += len(recent_videos)
            results['total_videos_processed'] += len(channel_insights)
            
            print(f"   ✅ Processed {len(channel_insights)} videos, found {len(channel_stock_mentions)} stock mentions")
            
        except Exception as e:
            print(f"   ❌ Error monitoring channel: {e}")
            results['channels_data'][channel.channel_name] = {
                'videos_found': 0,
                'videos_processed': 0,
                'stock_mentions': 0,
                'status': f'error: {e}'
            }
    
    # Post-process results
    print(f"\n📊 Processing Final Results...")
    
    # Convert sets to lists and calculate aggregates
    for symbol, data in results['stock_insights'].items():
        data['channels_mentioning'] = list(data['channels_mentioning'])
        data['channel_count'] = len(data['channels_mentioning'])
        data['avg_sentiment'] = sum(data['sentiments']) / len(data['sentiments']) if data['sentiments'] else 0.0
        data['sentiment_range'] = [min(data['sentiments']), max(data['sentiments'])] if data['sentiments'] else [0.0, 0.0]
        
        # Most common recommendation
        if data['recommendations']:
            from collections import Counter
            rec_counts = Counter(data['recommendations'])
            data['primary_recommendation'] = rec_counts.most_common(1)[0][0]
            data['recommendation_distribution'] = dict(rec_counts)
        else:
            data['primary_recommendation'] = None
            data['recommendation_distribution'] = {}
        
        # Price target statistics
        if data['price_targets']:
            data['avg_price_target'] = sum(data['price_targets']) / len(data['price_targets'])
            data['price_target_range'] = [min(data['price_targets']), max(data['price_targets'])]
        else:
            data['avg_price_target'] = None
            data['price_target_range'] = None
    
    # Top mentioned stocks
    results['top_mentioned_stocks'] = dict(
        sorted(results['stock_insights'].items(), 
               key=lambda x: x[1]['total_mentions'], 
               reverse=True)[:10]
    )
    
    return results

def save_results(results: Dict[str, Any], output_file: str = None):
    """Save monitoring results to JSON file"""
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"reports/market-intelligence/youtube_monitoring_{timestamp}.json"
    
    # Ensure reports directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True)
    
    # Convert datetime objects to strings for JSON serialization
    json_results = json.loads(json.dumps(results, default=str))
    
    with open(output_path, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"💾 Results saved to: {output_path}")

def print_summary(results: Dict[str, Any]):
    """Print a summary of monitoring results"""
    print(f"\n" + "=" * 60)
    print(f"📊 YOUTUBE MONITORING SUMMARY")
    print(f"=" * 60)
    
    print(f"🕐 Monitoring Period: {results['days_back']} days")
    print(f"📺 Channels Monitored: {results['channels_monitored']}")
    print(f"🎬 Total Videos Found: {results['total_videos_found']}")
    print(f"📝 Videos Processed: {results['total_videos_processed']}")
    print(f"📈 Unique Stocks Mentioned: {len(results['stock_insights'])}")
    
    # Top mentioned stocks
    if results['top_mentioned_stocks']:
        print(f"\n🏆 Top Mentioned Stocks:")
        for i, (symbol, data) in enumerate(list(results['top_mentioned_stocks'].items())[:5], 1):
            sentiment_emoji = "📈" if data['avg_sentiment'] > 0.1 else "📉" if data['avg_sentiment'] < -0.1 else "➡️"
            print(f"   {i}. {symbol} ({data['company_name'] or 'N/A'})")
            print(f"      Mentions: {data['total_mentions']}, Channels: {data['channel_count']}")
            print(f"      Sentiment: {sentiment_emoji} {data['avg_sentiment']:.2f}")
            if data['primary_recommendation']:
                print(f"      Primary Rec: {data['primary_recommendation']}")
            if data['avg_price_target']:
                print(f"      Avg Price Target: ${data['avg_price_target']:.2f}")
    
    # Channel performance
    successful_channels = sum(1 for c in results['channels_data'].values() if c['status'] == 'success')
    print(f"\n📡 Channel Performance:")
    print(f"   Successful: {successful_channels}/{results['channels_monitored']}")
    
    # Market insights summary
    if results['market_insights']:
        print(f"🌍 Market Insights: {len(results['market_insights'])} total insights captured")
    
    print(f"\n💡 This intelligence is now ready for integration with your AI investment decisions!")

def main():
    """Main monitoring function with command line arguments"""
    parser = argparse.ArgumentParser(description='Monitor YouTube stock analysis channels')
    parser.add_argument('--days', type=int, default=1, help='Days to look back (default: 1)')
    parser.add_argument('--channels', type=int, help='Max channels to monitor (default: all)')
    parser.add_argument('--symbols', nargs='+', help='Specific symbols to focus on (default: all)')
    parser.add_argument('--output', type=str, help='Output file path (default: auto-generated)')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv('YOUTUBE_API_KEY'):
        print("❌ YOUTUBE_API_KEY environment variable not set")
        print("📋 Please set up YouTube API access first:")
        print("   See docs/guides/youtube_api_setup.md")
        return
    
    # Run monitoring
    try:
        results = monitor_channels(
            days_back=args.days,
            max_channels=args.channels,
            target_symbols=args.symbols
        )
        
        if results:
            if not args.quiet:
                print_summary(results)
            
            save_results(results, args.output)
            
            print(f"\n✅ YouTube monitoring completed successfully!")
            
        else:
            print(f"❌ Monitoring failed - check logs above")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Monitoring interrupted by user")
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")

if __name__ == "__main__":
    main()