# YouTube API Setup Guide

This guide walks you through setting up YouTube Data API v3 integration for monitoring stock analysis channels and extracting market insights.

## 🎯 Overview

The YouTube API integration allows you to:
- Monitor 39+ international stock analysis channels
- Extract transcripts from market analysis videos
- Process content for stock mentions and sentiment
- Integrate insights with your AI investment decisions

## 📋 Prerequisites

- Google Cloud Platform account
- Python 3.8+ with project dependencies installed
- YouTube Data API v3 access

## 🔧 Setup Steps

### Step 1: Google Cloud Console Setup

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create or Select Project**
   - Click "Select a project" → "New Project"
   - Name: "Investment Analysis YouTube API"
   - Click "Create"

3. **Enable YouTube Data API v3**
   - Go to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click on it and press "Enable"

4. **Create API Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the generated API key
   - **Optional**: Restrict the key to YouTube Data API v3 for security

### Step 2: Environment Setup

1. **Set Environment Variable**
   ```bash
   # Windows (Command Prompt)
   set YOUTUBE_API_KEY=your_api_key_here
   
   # Windows (PowerShell)
   $env:YOUTUBE_API_KEY="your_api_key_here"
   
   # Linux/Mac
   export YOUTUBE_API_KEY=your_api_key_here
   ```

2. **Add to .env file** (recommended for persistence)
   ```bash
   # Add to your .env file
   YOUTUBE_API_KEY=your_api_key_here
   ```

3. **Install Required Packages**
   ```bash
   pip install google-api-python-client youtube-transcript-api
   ```

### Step 3: Test Installation

Run the test script to verify everything works:

```bash
cd C:\Users\jandr\Documents\ivan
python scripts\test_youtube_api.py
```

Expected output:
```
🎬 YouTube API Integration Test Suite
==================================================
🧪 Testing YouTube API Setup...
✅ YouTube API client initialized successfully

🧪 Testing Channel Database...
✅ Loaded 39 stock analysis channels

📺 Channels by Region:
  North America: 15 channels
    Example: Bloomberg Markets and Finance (English)
  Europe: 8 channels
    Example: Arte de Invertir (Spanish)
  Asia: 10 channels
    Example: Trading Chanakya (English)
  ...

✅ All tests passed! YouTube API integration is ready.
```

## 🎬 Available Channels

Your system monitors these categories of stock analysis channels:

### 📺 North America (15 channels)
- **Bloomberg Markets and Finance** - Daily market updates and analysis
- **CNBC** - Breaking market news and expert analysis  
- **Yahoo Finance** - Market trends and stock discussions
- **Benzinga** - Trading insights and market commentary
- **And 11 more...**

### 🌍 Europe (8 channels)
- **Arte de Invertir** (Spanish) - Daily stock analysis and market commentary
- **Kolja Barghoorn** (German) - Investment education and market analysis
- **L'Investisseur (The Investor)** (French) - Investment strategies and analysis
- **And 5 more...**

### 🌏 Asia-Pacific (10 channels)
- **Trading Chanakya** (English/Hindi) - Indian stock market analysis
- **Pranjal Kamra** (Hindi) - Investment advice and market insights
- **Asia Markets** (English) - Asian market coverage
- **And 7 more...**

### 🌎 Latin America (4 channels)
- **Me Poupe!** (Portuguese) - Brazilian market analysis
- **Canal do Holder** (Portuguese) - Investment strategies
- **And 2 more...**

### 🌍 Global/Multi-language (2 channels)
- **Real Vision Finance** - Global macro analysis
- **The Acquirer's Multiple** - Value investing insights

## ⚙️ Configuration

The YouTube API is configured in `config/system.json`:

```json
{
  "youtube_api": {
    "requests_per_day": 10000,
    "requests_per_second": 100,
    "max_results_per_request": 50,
    "days_lookback": 7,
    "cache_duration_hours": 6,
    "transcript_cache_hours": 168,
    "preferred_languages": ["en", "es", "pt", "fr", "de", "it", "ja", "ko", "zh"],
    "channel_monitoring": {
      "check_interval_hours": 6,
      "max_videos_per_check": 25,
      "parallel_processing": true,
      "max_concurrent_requests": 5
    },
    "content_processing": {
      "extract_transcripts": true,
      "analyze_sentiment": true,
      "extract_stock_mentions": true,
      "min_video_duration_seconds": 300,
      "max_video_duration_seconds": 3600
    }
  }
}
```

## 🚀 Usage Examples

### Basic Channel Monitoring

```python
from investment_system.data import get_youtube_client, get_stock_analysis_channels

# Initialize client
client = get_youtube_client()

# Get all channels
channels = get_stock_analysis_channels()

# Monitor specific channel for recent videos
channel_id = "UCrp_UI8XtuYfpiqluWLD7Lw"  # Example: Bloomberg
recent_videos = client.get_recent_videos(channel_id, days_back=3)

print(f"Found {len(recent_videos)} recent videos")
for video in recent_videos:
    print(f"- {video.title}")
    print(f"  Published: {video.published_at}")
    print(f"  Views: {video.view_count:,}")
```

### Transcript Extraction

```python
# Get video transcript
video_id = "example_video_id"
transcript, language = client.get_video_transcript(video_id)

if transcript:
    print(f"Transcript in {language}:")
    print(transcript[:500] + "...")
else:
    print("No transcript available")
```

### Bulk Channel Monitoring

```python
# Monitor all channels for new content
channel_ids = [channel.channel_id for channel in channels[:5]]  # First 5 channels
results = client.monitor_channels(channel_ids, days_back=1)

for channel_id, videos in results.items():
    print(f"Channel {channel_id}: {len(videos)} new videos")
```

## 📊 Rate Limits and Quotas

**YouTube Data API v3 Quotas:**
- **Daily Quota**: 10,000 units per day (default)
- **Common Operations**:
  - Channel details: 1 unit
  - Video list: 1 unit  
  - Search: 100 units
  - Playlist items: 1 unit

**Cost Management:**
- Enable caching to reduce API calls
- Monitor usage in Google Cloud Console
- Consider upgrading quota for heavy usage

## 🔧 Troubleshooting

### Common Issues

**1. "API key not valid" Error**
```
Solution: Check that your API key is correctly set and YouTube Data API v3 is enabled
```

**2. "Quota exceeded" Error**
```
Solution: Wait for quota reset (daily) or request quota increase in Google Cloud Console
```

**3. "No transcript available" Warning**
```
Solution: Normal behavior - not all videos have transcripts. The system will skip these.
```

**4. "Channel not found" Error**
```
Solution: Verify channel ID is correct. Some channels may have changed or been deleted.
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

client = get_youtube_client()
# Now you'll see detailed API request/response logs
```

### Manual Testing

Test individual components:

```bash
# Test specific channel
python -c "
from investment_system.data import get_youtube_client
client = get_youtube_client()
info = client.get_channel_info('UCrp_UI8XtuYfpiqluWLD7Lw')
print(f'Channel: {info.channel_title if info else \"Not found\"}')
"
```

## 🔒 Security Best Practices

1. **Restrict API Key**
   - Limit to YouTube Data API v3 only
   - Set HTTP referrer restrictions if using in web app
   - Regenerate key periodically

2. **Environment Variables**
   - Never commit API keys to version control
   - Use `.env` files for local development
   - Use secure secret management in production

3. **Rate Limiting**
   - Respect YouTube's terms of service
   - Implement exponential backoff for retries
   - Monitor usage to avoid quota violations

## 📈 Next Steps

After setup, you can proceed to:

1. **Channel Monitoring**: Monitor all 39 channels for new content
2. **Content Processing**: Extract stock mentions and sentiment from transcripts  
3. **Market Intelligence**: Aggregate insights from multiple analysts
4. **Integration**: Connect YouTube signals to your AI decision engine

See the main investment analysis documentation for integration guides.

## 🆘 Support

If you encounter issues:

1. Check the test script output for specific errors
2. Verify your API key and quota in Google Cloud Console
3. Review the troubleshooting section above
4. Check YouTube Data API v3 documentation: https://developers.google.com/youtube/v3

---

**Last Updated**: January 2025  
**YouTube Data API Version**: v3  
**Integration Status**: Active - 39 channels monitored