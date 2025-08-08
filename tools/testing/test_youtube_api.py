#!/usr/bin/env python3
"""
Test script for YouTube API integration

This script tests the basic functionality of the YouTube API client
including channel monitoring, video discovery, and transcript extraction.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from investment_system.data import get_youtube_client, get_stock_analysis_channels

def test_youtube_api_setup():
    """Test YouTube API client initialization"""
    print("🧪 Testing YouTube API Setup...")
    
    # Check if API key is set
    try:
        from config.settings import get_settings
        api_key = get_settings().apis.youtube_api_key
    except Exception:
        api_key = None
    if not api_key:
        print("❌ YOUTUBE_API_KEY environment variable not set")
        print("📋 To set up YouTube API:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable YouTube Data API v3")
        print("4. Create credentials (API Key)")
        print("5. Set environment variable: YOUTUBE_API_KEY=your_api_key")
        return False
    
    try:
        client = get_youtube_client()
        print("✅ YouTube API client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize YouTube API client: {e}")
        return False

def test_channel_database():
    """Test the stock analysis channels database"""
    print("\n🧪 Testing Channel Database...")
    
    try:
        channels = get_stock_analysis_channels()
        print(f"✅ Loaded {len(channels)} stock analysis channels")
        
        # Show sample channels by region
        regions = {}
        for channel in channels:
            region = channel.region.value
            if region not in regions:
                regions[region] = []
            regions[region].append(channel)
        
        print("\n📺 Channels by Region:")
        for region, region_channels in regions.items():
            print(f"  {region}: {len(region_channels)} channels")
            if region_channels:
                sample = region_channels[0]
                print(f"    Example: {sample.channel_name} ({sample.language.value})")
        
        return True
    except Exception as e:
        print(f"❌ Failed to load channel database: {e}")
        return False

def test_channel_info(client, sample_channel_id="UCrp_UI8XtuYfpiqluWLD7Lw"):
    """Test getting channel information"""
    print(f"\n🧪 Testing Channel Info for {sample_channel_id}...")
    
    try:
        channel_stats = client.get_channel_info(sample_channel_id)
        if channel_stats:
            print(f"✅ Channel: {channel_stats.channel_title}")
            print(f"   Subscribers: {channel_stats.subscriber_count:,}")
            print(f"   Videos: {channel_stats.video_count:,}")
            print(f"   Upload Frequency: {channel_stats.upload_frequency}")
            return True
        else:
            print("❌ Could not retrieve channel information")
            return False
    except Exception as e:
        print(f"❌ Error getting channel info: {e}")
        return False

def test_recent_videos(client, sample_channel_id="UCrp_UI8XtuYfpiqluWLD7Lw"):
    """Test getting recent videos from a channel"""
    print(f"\n🧪 Testing Recent Videos for {sample_channel_id}...")
    
    try:
        videos = client.get_recent_videos(sample_channel_id, days_back=7)
        print(f"✅ Found {len(videos)} recent videos")
        
        if videos:
            latest = videos[0]
            print(f"   Latest: '{latest.title[:50]}...'")
            print(f"   Published: {latest.published_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Views: {latest.view_count:,}")
        
        return True
    except Exception as e:
        print(f"❌ Error getting recent videos: {e}")
        return False

def test_transcript_extraction(client, sample_video_id="dQw4w9WgXcQ"):
    """Test transcript extraction (using Rick Roll as safe test video)"""
    print(f"\n🧪 Testing Transcript Extraction for {sample_video_id}...")
    
    try:
        transcript, language = client.get_video_transcript(sample_video_id)
        if transcript:
            print(f"✅ Extracted transcript in {language}")
            print(f"   Length: {len(transcript)} characters")
            print(f"   Preview: {transcript[:100]}...")
            return True
        else:
            print("⚠️ No transcript available for this video")
            return True  # Not an error, just no transcript
    except Exception as e:
        print(f"❌ Error extracting transcript: {e}")
        return False

def main():
    """Run all YouTube API tests"""
    print("🎬 YouTube API Integration Test Suite")
    print("=" * 50)
    
    all_passed = True
    
    # Test 1: API Setup
    if not test_youtube_api_setup():
        print("\n❌ Cannot proceed without YouTube API key")
        return
    
    # Test 2: Channel Database
    if not test_channel_database():
        all_passed = False
    
    # Get client for further tests
    try:
        client = get_youtube_client()
    except Exception as e:
        print(f"❌ Cannot create client for further tests: {e}")
        return
    
    # Test 3: Channel Info
    if not test_channel_info(client):
        all_passed = False
    
    # Test 4: Recent Videos
    if not test_recent_videos(client):
        all_passed = False
    
    # Test 5: Transcript Extraction
    if not test_transcript_extraction(client):
        all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed! YouTube API integration is ready.")
        print("\n🚀 Next steps:")
        print("1. Set up YouTube API key if not already done")
        print("2. Run channel monitoring on your 39 stock analysis channels")
        print("3. Implement stock mention extraction from transcripts")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print("\n📖 For full setup instructions, see:")
    print("   docs/guides/youtube_api_setup.md")

if __name__ == "__main__":
    main()