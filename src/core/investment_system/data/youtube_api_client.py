"""
YouTube Data API v3 Client for Stock Analysis Channels

Handles authentication, channel monitoring, video discovery, and transcript extraction
for stock analysis YouTube channels. Integrates with the investment analysis system.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import requests
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from ..utils.cache_manager import CacheManager
from ..utils.config_loader import ConfigurationManager
from config.settings import get_settings

logger = logging.getLogger(__name__)

@dataclass
class YouTubeVideo:
    """Data class for YouTube video metadata"""
    video_id: str
    title: str
    description: str
    published_at: datetime
    channel_id: str
    channel_title: str
    duration: str
    view_count: int
    like_count: int
    tags: List[str]
    transcript: Optional[str] = None
    transcript_language: Optional[str] = None
    stock_mentions: List[str] = None
    sentiment_score: Optional[float] = None
    processing_status: str = "pending"  # pending, processed, failed

@dataclass
class ChannelStats:
    """Channel statistics and metadata"""
    channel_id: str
    channel_title: str
    subscriber_count: int
    video_count: int
    view_count: int
    last_upload: datetime
    upload_frequency: str
    topics: List[str]

class YouTubeAPIClient:
    """
    YouTube Data API v3 client for stock analysis channel monitoring
    
    Features:
    - Channel monitoring and video discovery
    - Transcript extraction and processing
    - Rate limiting and error handling
    - Caching for performance optimization
    - Integration with investment analysis system
    """
    
    def __init__(self, config_manager: ConfigurationManager = None):
        """
        Initialize YouTube API client
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager or ConfigurationManager()
        self.cache_manager = CacheManager()
        
        # Load configuration
        try:
            system_config = self.config_manager.load_config('system')
            self.youtube_config = system_config.get('youtube_api', {})
        except Exception as e:
            logger.warning(f"Could not load YouTube config: {e}")
            self.youtube_config = {}
        
        # API setup
        self.api_key = get_settings().apis.youtube_api_key
        if not self.api_key:
            logger.error("YOUTUBE_API_KEY environment variable not set")
            raise ValueError("YouTube API key is required")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        
        # Rate limiting configuration
        self.requests_per_day = self.youtube_config.get('requests_per_day', 10000)
        self.requests_per_second = self.youtube_config.get('requests_per_second', 100)
        self.current_requests = 0
        self.last_reset = datetime.now()
        
        # Default parameters
        self.max_results = self.youtube_config.get('max_results_per_request', 50)
        self.days_lookback = self.youtube_config.get('days_lookback', 7)
        
        logger.info("YouTube API client initialized successfully")
    
    def _check_rate_limits(self) -> bool:
        """
        Check if we're within API rate limits
        
        Returns:
            bool: True if within limits, False otherwise
        """
        now = datetime.now()
        
        # Reset daily counter if needed
        if (now - self.last_reset).days >= 1:
            self.current_requests = 0
            self.last_reset = now
        
        # Check daily limit
        if self.current_requests >= self.requests_per_day:
            logger.warning("Daily YouTube API quota reached")
            return False
        
        return True
    
    def _make_api_request(self, request_func, **kwargs) -> Optional[Dict]:
        """
        Make API request with rate limiting and error handling
        
        Args:
            request_func: API request function
            **kwargs: Request parameters
            
        Returns:
            API response or None if failed
        """
        if not self._check_rate_limits():
            return None
        
        try:
            response = request_func(**kwargs).execute()
            self.current_requests += 1
            return response
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in YouTube API request: {e}")
            return None
    
    def get_channel_info(self, channel_id: str) -> Optional[ChannelStats]:
        """
        Get detailed information about a YouTube channel
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            ChannelStats object or None if failed
        """
        cache_key = f"channel_info_{channel_id}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            return ChannelStats(**cached_result)
        
        response = self._make_api_request(
            self.youtube.channels().list,
            part='statistics,snippet,topicDetails',
            id=channel_id
        )
        
        if not response or not response.get('items'):
            logger.warning(f"No channel found for ID: {channel_id}")
            return None
        
        channel_data = response['items'][0]
        snippet = channel_data.get('snippet', {})
        statistics = channel_data.get('statistics', {})
        
        # Get recent uploads to calculate frequency
        uploads_playlist_id = channel_data.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
        upload_frequency = "unknown"
        last_upload = datetime.now()
        
        if uploads_playlist_id:
            recent_videos = self._get_playlist_videos(uploads_playlist_id, max_results=10)
            if recent_videos:
                # Calculate upload frequency based on recent videos
                dates = [video.published_at for video in recent_videos]
                if len(dates) >= 2:
                    avg_gap = sum((dates[i] - dates[i+1]).days for i in range(len(dates)-1)) / (len(dates)-1)
                    if avg_gap <= 1:
                        upload_frequency = "daily"
                    elif avg_gap <= 7:
                        upload_frequency = "weekly"
                    elif avg_gap <= 30:
                        upload_frequency = "monthly"
                    else:
                        upload_frequency = "irregular"
                
                last_upload = dates[0]
        
        channel_stats = ChannelStats(
            channel_id=channel_id,
            channel_title=snippet.get('title', ''),
            subscriber_count=int(statistics.get('subscriberCount', 0)),
            video_count=int(statistics.get('videoCount', 0)),
            view_count=int(statistics.get('viewCount', 0)),
            last_upload=last_upload,
            upload_frequency=upload_frequency,
            topics=channel_data.get('topicDetails', {}).get('topicCategories', [])
        )
        
        # Cache for 6 hours
        self.cache_manager.set(cache_key, asdict(channel_stats), expire_hours=6)
        
        return channel_stats
    
    def _get_playlist_videos(self, playlist_id: str, max_results: int = 50) -> List[YouTubeVideo]:
        """
        Get videos from a playlist (used for uploads playlist)
        
        Args:
            playlist_id: YouTube playlist ID
            max_results: Maximum number of videos to fetch
            
        Returns:
            List of YouTubeVideo objects
        """
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            response = self._make_api_request(
                self.youtube.playlistItems().list,
                part='snippet',
                playlistId=playlist_id,
                maxResults=min(50, max_results - len(videos)),
                pageToken=next_page_token
            )
            
            if not response:
                break
            
            for item in response.get('items', []):
                snippet = item['snippet']
                
                video = YouTubeVideo(
                    video_id=snippet['resourceId']['videoId'],
                    title=snippet['title'],
                    description=snippet['description'],
                    published_at=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                    channel_id=snippet['channelId'],
                    channel_title=snippet['channelTitle'],
                    duration="",  # Will be filled by get_video_details
                    view_count=0,  # Will be filled by get_video_details
                    like_count=0,  # Will be filled by get_video_details
                    tags=[]  # Will be filled by get_video_details
                )
                videos.append(video)
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return videos
    
    def get_recent_videos(self, channel_id: str, days_back: int = None) -> List[YouTubeVideo]:
        """
        Get recent videos from a channel
        
        Args:
            channel_id: YouTube channel ID
            days_back: Number of days to look back (default from config)
            
        Returns:
            List of recent YouTubeVideo objects
        """
        days_back = days_back or self.days_lookback
        since_date = datetime.now() - timedelta(days=days_back)
        
        cache_key = f"recent_videos_{channel_id}_{days_back}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            return [YouTubeVideo(**video) for video in cached_result]
        
        # Get channel's uploads playlist
        channel_response = self._make_api_request(
            self.youtube.channels().list,
            part='contentDetails',
            id=channel_id
        )
        
        if not channel_response or not channel_response.get('items'):
            return []
        
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get recent videos from uploads playlist
        videos = self._get_playlist_videos(uploads_playlist_id, max_results=self.max_results)
        
        # Filter by date and get detailed info
        recent_videos = []
        for video in videos:
            if video.published_at >= since_date:
                detailed_video = self.get_video_details(video.video_id)
                if detailed_video:
                    recent_videos.append(detailed_video)
        
        # Cache for 1 hour
        self.cache_manager.set(cache_key, [asdict(video) for video in recent_videos], expire_hours=1)
        
        return recent_videos
    
    def get_video_details(self, video_id: str) -> Optional[YouTubeVideo]:
        """
        Get detailed information about a specific video
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            YouTubeVideo object with complete details
        """
        cache_key = f"video_details_{video_id}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            return YouTubeVideo(**cached_result)
        
        response = self._make_api_request(
            self.youtube.videos().list,
            part='snippet,statistics,contentDetails',
            id=video_id
        )
        
        if not response or not response.get('items'):
            return None
        
        video_data = response['items'][0]
        snippet = video_data['snippet']
        statistics = video_data.get('statistics', {})
        content_details = video_data.get('contentDetails', {})
        
        video = YouTubeVideo(
            video_id=video_id,
            title=snippet['title'],
            description=snippet['description'],
            published_at=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
            channel_id=snippet['channelId'],
            channel_title=snippet['channelTitle'],
            duration=content_details.get('duration', ''),
            view_count=int(statistics.get('viewCount', 0)),
            like_count=int(statistics.get('likeCount', 0)),
            tags=snippet.get('tags', [])
        )
        
        # Cache for 24 hours (video details don't change much)
        self.cache_manager.set(cache_key, asdict(video), expire_hours=24)
        
        return video
    
    def get_video_transcript(self, video_id: str, preferred_languages: List[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract transcript from a YouTube video
        
        Args:
            video_id: YouTube video ID
            preferred_languages: List of preferred language codes (e.g., ['en', 'es'])
            
        Returns:
            Tuple of (transcript_text, language_code) or (None, None) if failed
        """
        preferred_languages = preferred_languages or ['en', 'es', 'pt', 'fr', 'de', 'it', 'ja', 'ko', 'zh']
        
        cache_key = f"transcript_{video_id}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            return cached_result['transcript'], cached_result['language']
        
        try:
            # Get available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to find transcript in preferred languages
            for lang in preferred_languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    transcript_data = transcript.fetch()
                    
                    # Format transcript to plain text
                    formatter = TextFormatter()
                    transcript_text = formatter.format_transcript(transcript_data)
                    
                    # Cache for 7 days (transcripts don't change)
                    cache_data = {'transcript': transcript_text, 'language': lang}
                    self.cache_manager.set(cache_key, cache_data, expire_hours=24*7)
                    
                    return transcript_text, lang
                except:
                    continue
            
            # If no preferred language found, try auto-generated English
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
                transcript_data = transcript.fetch()
                formatter = TextFormatter()
                transcript_text = formatter.format_transcript(transcript_data)
                
                cache_data = {'transcript': transcript_text, 'language': 'en-auto'}
                self.cache_manager.set(cache_key, cache_data, expire_hours=24*7)
                
                return transcript_text, 'en-auto'
            except:
                pass
            
        except Exception as e:
            logger.warning(f"Could not extract transcript for video {video_id}: {e}")
        
        return None, None
    
    def monitor_channels(self, channel_ids: List[str], days_back: int = 1) -> Dict[str, List[YouTubeVideo]]:
        """
        Monitor multiple channels for new videos
        
        Args:
            channel_ids: List of YouTube channel IDs to monitor
            days_back: Number of days to look back for new videos
            
        Returns:
            Dictionary mapping channel_id to list of recent videos
        """
        results = {}
        
        logger.info(f"Monitoring {len(channel_ids)} channels for videos from last {days_back} days")
        
        for channel_id in channel_ids:
            try:
                recent_videos = self.get_recent_videos(channel_id, days_back)
                results[channel_id] = recent_videos
                
                logger.info(f"Found {len(recent_videos)} recent videos for channel {channel_id}")
                
                # Add transcript to each video
                for video in recent_videos:
                    if not video.transcript:
                        transcript, lang = self.get_video_transcript(video.video_id)
                        video.transcript = transcript
                        video.transcript_language = lang
                        
            except Exception as e:
                logger.error(f"Error monitoring channel {channel_id}: {e}")
                results[channel_id] = []
        
        return results
    
    def search_videos(self, query: str, max_results: int = 25, days_back: int = 7) -> List[YouTubeVideo]:
        """
        Search for videos by query
        
        Args:
            query: Search query
            max_results: Maximum number of results
            days_back: Number of days to look back
            
        Returns:
            List of YouTubeVideo objects matching the query
        """
        since_date = datetime.now() - timedelta(days=days_back)
        
        response = self._make_api_request(
            self.youtube.search().list,
            part='snippet',
            q=query,
            type='video',
            order='date',
            publishedAfter=since_date.isoformat() + 'Z',
            maxResults=max_results
        )
        
        if not response:
            return []
        
        videos = []
        for item in response.get('items', []):
            snippet = item['snippet']
            
            video = YouTubeVideo(
                video_id=item['id']['videoId'],
                title=snippet['title'],
                description=snippet['description'],
                published_at=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                channel_id=snippet['channelId'],
                channel_title=snippet['channelTitle'],
                duration="",  # Will be filled by get_video_details if needed
                view_count=0,
                like_count=0,
                tags=[]
            )
            videos.append(video)
        
        return videos

# Convenience function for easy import
def get_youtube_client() -> YouTubeAPIClient:
    """Get configured YouTube API client instance"""
    return YouTubeAPIClient()