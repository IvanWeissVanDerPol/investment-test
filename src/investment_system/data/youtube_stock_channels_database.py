"""
YouTube Stock Analysis Channels Database
Comprehensive database of channels providing daily stock analysis, market updates, and trading insights
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ChannelType(Enum):
    DAILY_ANALYSIS = "daily_analysis"
    MARKET_NEWS = "market_news"
    TECHNICAL_ANALYSIS = "technical_analysis"
    TRADING_INSIGHTS = "trading_insights"
    EARNINGS_ANALYSIS = "earnings_analysis"
    SECTOR_ANALYSIS = "sector_analysis"
    LONG_TERM_INVESTING = "long_term_investing"
    OPTIONS_TRADING = "options_trading"
    CRYPTO_STOCKS = "crypto_stocks"
    DIVIDEND_INVESTING = "dividend_investing"
    PENNY_STOCKS = "penny_stocks"
    INTERNATIONAL_MARKETS = "international_markets"
    ECONOMIC_ANALYSIS = "economic_analysis"
    IPO_ANALYSIS = "ipo_analysis"
    MERGER_ACQUISITION = "merger_acquisition"
    EDUCATIONAL = "educational"
    LIVE_TRADING = "live_trading"
    PORTFOLIO_MANAGEMENT = "portfolio_management"

class Region(Enum):
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA = "asia"
    LATIN_AMERICA = "latin_america"
    AFRICA = "africa"
    OCEANIA = "oceania"

class Language(Enum):
    ENGLISH = "en"
    SPANISH = "es"
    PORTUGUESE = "pt"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    HINDI = "hi"
    JAPANESE = "ja"
    KOREAN = "ko"
    CHINESE = "zh"

@dataclass
class YouTubeStockChannel:
    """YouTube channel focused on stock analysis and market insights"""
    
    channel_id: str
    channel_name: str
    channel_url: str
    handle: Optional[str]
    region: Region
    language: Language
    primary_focus: ChannelType
    secondary_focus: List[ChannelType]
    
    # Channel metrics
    subscriber_count: Optional[int]
    average_views: Optional[int]
    upload_frequency: str  # daily, weekly, multiple_daily, etc.
    
    # Content characteristics
    covers_markets: List[str]  # US, Europe, Asia, etc.
    specializes_in: List[str]  # sectors, stock types, analysis styles
    typical_video_length: str  # short (1-5min), medium (5-20min), long (20min+)
    
    # Analysis quality indicators
    provides_charts: bool
    provides_price_targets: bool
    tracks_performance: bool
    has_live_streams: bool
    
    # Credibility indicators
    years_active: Optional[int]
    professional_background: Optional[str]
    accuracy_notes: Optional[str]
    
    # Technical details
    has_transcripts: bool
    typical_upload_time: Optional[str]  # UTC time when they usually upload
    last_checked: Optional[str]

class YouTubeStockChannelsDatabase:
    """Database of YouTube channels providing stock analysis and market insights"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the YouTube Stock Channels Database
        
        Args:
            config_path: Path to the main config.json file. If None, uses default path.
        """
        if config_path is None:
            # Default to main config.json in the config directory
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            config_path = project_root / "config" / "config.json"
        
        self.config_path = Path(config_path)
        self.channels: List[YouTubeStockChannel] = []
        self.channels_by_id: Dict[str, YouTubeStockChannel] = {}
        self.channels_by_name: Dict[str, YouTubeStockChannel] = {}
        self.last_loaded = None
        
        # Load channels from config
        self._load_channels_from_config()
        logger.info(f"Loaded {len(self.channels)} YouTube channels from config")
    
    def _load_channels_from_config(self) -> None:
        """Load YouTube channels from the consolidated config.json file"""
        try:
            if not self.config_path.exists():
                logger.error(f"Config file not found: {self.config_path}")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            youtube_config = config_data.get('youtube_channels', {})
            if not youtube_config.get('enabled', False):
                logger.warning("YouTube channels are disabled in config")
                return
            
            channels_data = youtube_config.get('channels', [])
            
            # Load channels
            for channel_data in channels_data:
                try:
                    channel = self._create_channel_from_dict(channel_data)
                    if channel:
                        self.channels.append(channel)
                        self.channels_by_id[channel.channel_id] = channel
                        self.channels_by_name[channel.channel_name.lower()] = channel
                except Exception as e:
                    logger.error(f"Error loading channel {channel_data.get('channel_name', 'unknown')}: {e}")
                    continue
            
            from datetime import datetime
            self.last_loaded = datetime.now()
            
        except Exception as e:
            logger.error(f"Error loading YouTube channels config: {e}")
            # Initialize with empty data to prevent crashes
            self.channels = []
            self.channels_by_id = {}
            self.channels_by_name = {}
    
    def _create_channel_from_dict(self, channel_data: Dict) -> Optional[YouTubeStockChannel]:
        """Create a YouTubeStockChannel from dictionary data"""
        try:
            # Convert string enums to enum objects
            region_str = channel_data.get('region', 'north_america')
            language_str = channel_data.get('language', 'en')
            primary_focus_str = channel_data.get('primary_focus', 'market_news')
            
            # Map strings to enums
            region = Region(region_str)
            language = Language(language_str)
            primary_focus = ChannelType(primary_focus_str)
            
            # Handle secondary focus list
            secondary_focus = []
            for focus_str in channel_data.get('secondary_focus', []):
                try:
                    secondary_focus.append(ChannelType(focus_str))
                except ValueError:
                    logger.warning(f"Unknown channel type: {focus_str}")
            
            # Create channel object
            channel = YouTubeStockChannel(
                channel_id=channel_data['channel_id'],
                channel_name=channel_data['channel_name'],
                channel_url=channel_data['channel_url'],
                handle=channel_data.get('handle'),
                region=region,
                language=language,
                primary_focus=primary_focus,
                secondary_focus=secondary_focus,
                subscriber_count=channel_data.get('subscriber_count'),
                average_views=channel_data.get('average_views'),
                upload_frequency=channel_data.get('upload_frequency', 'unknown'),
                covers_markets=channel_data.get('covers_markets', []),
                specializes_in=channel_data.get('specializes_in', []),
                typical_video_length=channel_data.get('typical_video_length', 'medium'),
                provides_charts=channel_data.get('provides_charts', False),
                provides_price_targets=channel_data.get('provides_price_targets', False),
                tracks_performance=channel_data.get('tracks_performance', False),
                has_live_streams=channel_data.get('has_live_streams', False),
                years_active=channel_data.get('years_active', 0),
                professional_background=channel_data.get('professional_background', ''),
                accuracy_notes=channel_data.get('accuracy_notes', ''),
                has_transcripts=channel_data.get('has_transcripts', False),
                typical_upload_time=channel_data.get('typical_upload_time'),
                last_checked=channel_data.get('last_checked')
            )
            
            return channel
            
        except Exception as e:
            logger.error(f"Error creating channel from data: {e}")
            return None
    
    def get_channel(self, channel_id: str) -> Optional[YouTubeStockChannel]:
        """Get a channel by its ID"""
        return self.channels_by_id.get(channel_id)
    
    def get_channel_by_name(self, channel_name: str) -> Optional[YouTubeStockChannel]:
        """Get a channel by its name (case insensitive)"""
        return self.channels_by_name.get(channel_name.lower())
    
    def get_all_channels(self) -> List[YouTubeStockChannel]:
        """Get all channels"""
        return self.channels.copy()
    
    def get_channels_by_region(self, region: Region) -> List[YouTubeStockChannel]:
        """Get channels filtered by region"""
        return [channel for channel in self.channels if channel.region == region]
    
    def get_channels_by_language(self, language: Language) -> List[YouTubeStockChannel]:
        """Get channels filtered by language"""
        return [channel for channel in self.channels if channel.language == language]
    
    def get_channels_by_focus(self, focus: ChannelType) -> List[YouTubeStockChannel]:
        """Get channels filtered by primary or secondary focus"""
        return [
            channel for channel in self.channels 
            if channel.primary_focus == focus or focus in channel.secondary_focus
        ]
    
    def get_high_credibility_channels(self, min_subscribers: int = 100000) -> List[YouTubeStockChannel]:
        """Get channels with high subscriber count (proxy for credibility)"""
        return [
            channel for channel in self.channels 
            if channel.subscriber_count and channel.subscriber_count >= min_subscribers
        ]
    
    def search_channels(self, query: str) -> List[YouTubeStockChannel]:
        """Search channels by name, specialization, or background"""
        query_lower = query.lower()
        results = []
        
        for channel in self.channels:
            # Search in channel name
            if query_lower in channel.channel_name.lower():
                results.append(channel)
                continue
            
            # Search in specializations
            if any(query_lower in spec.lower() for spec in channel.specializes_in):
                results.append(channel)
                continue
            
            # Search in professional background
            if query_lower in channel.professional_background.lower():
                results.append(channel)
                continue
        
        return results
    
    def get_channels_covering_stock(self, stock_symbol: str) -> List[YouTubeStockChannel]:
        """Get channels that might cover a specific stock (based on specializations)"""
        stock_lower = stock_symbol.lower()
        results = []
        
        for channel in self.channels:
            # Check if stock symbol is mentioned in specializations
            if any(stock_lower in spec.lower() for spec in channel.specializes_in):
                results.append(channel)
        
        return results
    
    def reload_channels(self) -> None:
        """Reload channels from config file"""
        self.channels.clear()
        self.channels_by_id.clear()
        self.channels_by_name.clear()
        self._load_channels_from_config()
        logger.info(f"Reloaded {len(self.channels)} YouTube channels from config")
    
    def add_channel_to_config(self, channel: YouTubeStockChannel) -> bool:
        """Add a new channel to the config file and reload"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            youtube_config = config_data.setdefault('youtube_channels', {})
            channels_data = youtube_config.setdefault('channels', [])
            
            # Convert channel to dict
            channel_dict = {
                'channel_id': channel.channel_id,
                'channel_name': channel.channel_name,
                'channel_url': channel.channel_url,
                'handle': channel.handle,
                'region': channel.region.value,
                'language': channel.language.value,
                'primary_focus': channel.primary_focus.value,
                'secondary_focus': [focus.value for focus in channel.secondary_focus],
                'subscriber_count': channel.subscriber_count,
                'average_views': channel.average_views,
                'upload_frequency': channel.upload_frequency,
                'covers_markets': channel.covers_markets,
                'specializes_in': channel.specializes_in,
                'typical_video_length': channel.typical_video_length,
                'provides_charts': channel.provides_charts,
                'provides_price_targets': channel.provides_price_targets,
                'tracks_performance': channel.tracks_performance,
                'has_live_streams': channel.has_live_streams,
                'years_active': channel.years_active,
                'professional_background': channel.professional_background,
                'accuracy_notes': channel.accuracy_notes,
                'has_transcripts': channel.has_transcripts,
                'typical_upload_time': channel.typical_upload_time,
                'last_checked': channel.last_checked
            }
            
            channels_data.append(channel_dict)
            
            # Write back to config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Reload channels
            self.reload_channels()
            return True
            
        except Exception as e:
            logger.error(f"Error adding channel to config: {e}")
            return False
    
    def remove_channel_from_config(self, channel_id: str) -> bool:
        """Remove a channel from the config file and reload"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            youtube_config = config_data.get('youtube_channels', {})
            channels_data = youtube_config.get('channels', [])
            
            # Remove channel with matching ID
            original_count = len(channels_data)
            channels_data[:] = [ch for ch in channels_data if ch.get('channel_id') != channel_id]
            
            if len(channels_data) < original_count:
                # Write back to config
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                # Reload channels
                self.reload_channels()
                return True
            else:
                logger.warning(f"Channel {channel_id} not found in config")
                return False
            
        except Exception as e:
            logger.error(f"Error removing channel from config: {e}")
            return False
    
    def get_summary(self) -> Dict:
        """Get a summary of the database"""
        if not self.channels:
            return {'total_channels': 0, 'message': 'No channels loaded'}
        
        # Count by region
        region_counts = {}
        for channel in self.channels:
            region = channel.region.value
            region_counts[region] = region_counts.get(region, 0) + 1
        
        # Count by language
        language_counts = {}
        for channel in self.channels:
            language = channel.language.value
            language_counts[language] = language_counts.get(language, 0) + 1
        
        # Count by focus
        focus_counts = {}
        for channel in self.channels:
            focus = channel.primary_focus.value
            focus_counts[focus] = focus_counts.get(focus, 0) + 1
        
        return {
            'total_channels': len(self.channels),
            'last_loaded': self.last_loaded.isoformat() if self.last_loaded else None,
            'by_region': region_counts,
            'by_language': language_counts,
            'by_primary_focus': focus_counts
        }


def main():
    """Test function to demonstrate database functionality"""
    print("YouTube Stock Channels Database Test")
    print("====================================")
    
    # Initialize database
    db = YouTubeStockChannelsDatabase()
    
    # Print summary
    summary = db.get_summary()
    print(f"\nDatabase Summary:")
    print(f"Total channels: {summary['total_channels']}")
    print(f"Last loaded: {summary.get('last_loaded', 'Never')}")
    
    if summary['total_channels'] > 0:
        print(f"\nBy Region: {summary['by_region']}")
        print(f"By Language: {summary['by_language']}")
        print(f"By Primary Focus: {summary['by_primary_focus']}")
        
        # Show some example queries
        print(f"\nHigh credibility channels (100k+ subscribers): {len(db.get_high_credibility_channels())}")
        print(f"English channels: {len(db.get_channels_by_language(Language.ENGLISH))}")
        print(f"Technical analysis channels: {len(db.get_channels_by_focus(ChannelType.TECHNICAL_ANALYSIS))}")
    else:
        print("\nNo channels loaded. Make sure config.json has youtube_channels section enabled.")


if __name__ == "__main__":
    main()
            
            YouTubeStockChannel(
                channel_id="UCkEqXbeH6XZNWPM7pPJNS8w",
                channel_name="InTheMoney",
                channel_url="https://www.youtube.com/@InTheMoney",
                handle="@InTheMoney",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.TECHNICAL_ANALYSIS, ChannelType.MARKET_NEWS],
                subscriber_count=450000,
                average_views=35000,
                upload_frequency="daily",
                covers_markets=["US"],
                specializes_in=["Stock Analysis", "Market Updates", "Technical Analysis"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=4,
                professional_background="Independent analyst",
                accuracy_notes="Good analytical approach with performance tracking",
                has_transcripts=True,
                typical_upload_time="16:00 EST",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UCdnzjFbCt5g4PFKlmGXL3ZQ",
                channel_name="Stock Moe",
                channel_url="https://www.youtube.com/@StockMoe",
                handle="@StockMoe",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=600000,
                average_views=40000,
                upload_frequency="daily",
                covers_markets=["US"],
                specializes_in=["Big Picture Analysis", "Market Trends", "Sector Rotation"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=False,
                tracks_performance=False,
                has_live_streams=False,
                years_active=5,
                professional_background="Independent market analyst",
                accuracy_notes="Good for understanding market context",
                has_transcripts=True,
                typical_upload_time="15:00 EST",
                last_checked=None
            ),
            
            # ========== LATIN AMERICA - SPANISH ==========
            
            YouTubeStockChannel(
                channel_id="UCMaFMr6m30EGr-jKgFiF4bg",
                channel_name="Arte de Invertir",
                channel_url="https://www.youtube.com/@Artedeinvertir",
                handle="@Artedeinvertir",
                region=Region.LATIN_AMERICA,
                language=Language.SPANISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.TECHNICAL_ANALYSIS, ChannelType.MARKET_NEWS],
                subscriber_count=185000,
                average_views=15000,
                upload_frequency="daily",
                covers_markets=["Spain", "US", "Europe"],
                specializes_in=["Spanish Stocks", "IBEX 35", "Technical Analysis", "Market Commentary"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=6,
                professional_background="Spanish market analyst",
                accuracy_notes="Strong focus on Spanish and European markets",
                has_transcripts=True,
                typical_upload_time="16:00 CET",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UC-ejemplo-hanseatic",
                channel_name="Hanseático",
                channel_url="https://www.youtube.com/@hanseatico",
                handle="@hanseatico",
                region=Region.EUROPE,
                language=Language.SPANISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.TECHNICAL_ANALYSIS, ChannelType.MARKET_NEWS],
                subscriber_count=95000,
                average_views=8000,
                upload_frequency="daily",
                covers_markets=["Spain", "Europe", "US"],
                specializes_in=["Spanish Market", "Technical Analysis", "Investment Education"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=4,
                professional_background="Financial educator and analyst",
                accuracy_notes="Educational approach with practical analysis",
                has_transcripts=True,
                typical_upload_time="18:00 CET",
                last_checked=None
            ),
            
            # ========== ASIA - ENGLISH & LOCAL LANGUAGES ==========
            
            # Indian Channels
            YouTubeStockChannel(
                channel_id="UC8Ea4fUMLKLc0fhIZSm_GRw",
                channel_name="Trading Chanakya",
                channel_url="https://www.youtube.com/@TradingChanakya",
                handle="@TradingChanakya",
                region=Region.ASIA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.TECHNICAL_ANALYSIS, ChannelType.TRADING_INSIGHTS],
                subscriber_count=470000,
                average_views=25000,
                upload_frequency="daily",
                covers_markets=["India", "US"],
                specializes_in=["Indian Stocks", "Technical Analysis", "Live Trading"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=True,
                years_active=5,
                professional_background="Indian stock market trader and educator",
                accuracy_notes="Good track record in Indian markets",
                has_transcripts=True,
                typical_upload_time="09:30 IST",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UCyWMHVbkfSWHFZGLDuZUV8g",
                channel_name="POWER OF STOCKS",
                channel_url="https://www.youtube.com/@POWEROFSTOCKS",
                handle="@POWEROFSTOCKS",
                region=Region.ASIA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.TECHNICAL_ANALYSIS,
                secondary_focus=[ChannelType.DAILY_ANALYSIS, ChannelType.TRADING_INSIGHTS],
                subscriber_count=315000,
                average_views=18000,
                upload_frequency="daily",
                covers_markets=["India"],
                specializes_in=["Technical Analysis", "Options Trading", "Trading Psychology"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=True,
                years_active=4,
                professional_background="Technical analyst Subasish Pani",
                accuracy_notes="Strong technical analysis focus",
                has_transcripts=True,
                typical_upload_time="15:00 IST",
                last_checked=None
            ),
            
            # ========== EUROPE - ENGLISH ==========
            
            YouTubeStockChannel(
                channel_id="UCQ4yrKE5_lE_vxGP_JB3A_A",
                channel_name="Sven Carlin, Ph.D.",
                channel_url="https://www.youtube.com/@ValueInvesting",
                handle="@ValueInvesting",
                region=Region.EUROPE,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=223000,
                average_views=12000,
                upload_frequency="multiple_weekly",
                covers_markets=["US", "Europe", "Global"],
                specializes_in=["Value Investing", "Market Analysis", "Economic Commentary"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=6,
                professional_background="PhD in Economics, professional investor",
                accuracy_notes="Strong long-term perspective and analysis",
                has_transcripts=True,
                typical_upload_time="14:00 CET",
                last_checked=None
            ),
            
            # ========== ADDITIONAL CHANNELS ==========
            
            # More US-based technical analysis channels
            YouTubeStockChannel(
                channel_id="UCl2oCaw-fEqFaMoHUZeI-Rw",
                channel_name="TradingLab",
                channel_url="https://www.youtube.com/@TradingLab",
                handle="@TradingLab",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.TECHNICAL_ANALYSIS,
                secondary_focus=[ChannelType.TRADING_INSIGHTS, ChannelType.DAILY_ANALYSIS],
                subscriber_count=235000,
                average_views=20000,
                upload_frequency="weekly",
                covers_markets=["US"],
                specializes_in=["Day Trading Strategies", "Technical Patterns", "Market Setups"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=3,
                professional_background="Day trading education",
                accuracy_notes="Focused on short-term trading strategies",
                has_transcripts=True,
                typical_upload_time="16:00 EST",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UCGy7_1cXOqKvnIhfOLo-_rA",
                channel_name="Investors Underground",
                channel_url="https://www.youtube.com/@InvestorsUnderground",
                handle="@InvestorsUnderground",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.TRADING_INSIGHTS,
                secondary_focus=[ChannelType.DAILY_ANALYSIS, ChannelType.TECHNICAL_ANALYSIS],
                subscriber_count=145000,
                average_views=10000,
                upload_frequency="daily",
                covers_markets=["US"],
                specializes_in=["Day Trading", "Small Cap Stocks", "Live Trading"],
                typical_video_length="long",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=True,
                years_active=8,
                professional_background="Professional day trading community",
                accuracy_notes="Focused on momentum and small-cap trading",
                has_transcripts=True,
                typical_upload_time="16:30 EST",
                last_checked=None
            ),
            
            # Brazilian channels
            YouTubeStockChannel(
                channel_id="UC-exemplo-nath-financas",
                channel_name="Nath Finanças",
                channel_url="https://www.youtube.com/@nathfinancas",
                handle="@nathfinancas",
                region=Region.LATIN_AMERICA,
                language=Language.PORTUGUESE,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=200000,
                average_views=15000,
                upload_frequency="daily",
                covers_markets=["Brazil", "US"],
                specializes_in=["Brazilian Stocks", "Bovespa", "Market Education"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=False,
                tracks_performance=False,
                has_live_streams=False,
                years_active=3,
                professional_background="Brazilian financial educator",
                accuracy_notes="Popular Brazilian market commentary",
                has_transcripts=True,
                typical_upload_time="16:00 BRT",
                last_checked=None
            ),
            
            # ========== MORE US CHANNELS ==========
            
            YouTubeStockChannel(
                channel_id="UCJkMwVnazgK8AS8C0HIpFZw",
                channel_name="Ricky Gutierrez",
                channel_url="https://www.youtube.com/@RickyGutierrezz",
                handle="@RickyGutierrezz",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.TRADING_INSIGHTS,
                secondary_focus=[ChannelType.DAILY_ANALYSIS, ChannelType.TECHNICAL_ANALYSIS],
                subscriber_count=1100000,
                average_views=45000,
                upload_frequency="daily",
                covers_markets=["US"],
                specializes_in=["Day Trading", "Penny Stocks", "Crypto", "Options"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=True,
                years_active=7,
                professional_background="Professional day trader",
                accuracy_notes="Focus on momentum trading",
                has_transcripts=True,
                typical_upload_time="09:00 EST",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UCSkR_H5p36mOWiOzfTYacBw",
                channel_name="Timothy Sykes",
                channel_url="https://www.youtube.com/@TimothySykes",
                handle="@TimothySykes",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.TRADING_INSIGHTS,
                secondary_focus=[ChannelType.DAILY_ANALYSIS],
                subscriber_count=155000,
                average_views=8000,
                upload_frequency="daily",
                covers_markets=["US"],
                specializes_in=["Penny Stocks", "Short Selling", "Day Trading"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=15,
                professional_background="Penny stock specialist, turned $12k into millions",
                accuracy_notes="Focused on penny stock patterns",
                has_transcripts=True,
                typical_upload_time="07:00 EST",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UCgCOOEJBjGtDMk_Y3TEaFrg",
                channel_name="The Trade Risk",
                channel_url="https://www.youtube.com/@TheTradeRisk",
                handle="@TheTradeRisk",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.TECHNICAL_ANALYSIS],
                subscriber_count=85000,
                average_views=12000,
                upload_frequency="weekly",
                covers_markets=["US"],
                specializes_in=["Market Recaps", "Trading Education", "Risk Management"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=False,
                tracks_performance=True,
                has_live_streams=False,
                years_active=4,
                professional_background="Evan Medeiros - Trading educator",
                accuracy_notes="Educational focus with good market recaps",
                has_transcripts=True,
                typical_upload_time="17:00 EST",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UCteGgELNr5V6rIRZJkLmYyw",
                channel_name="Ticker Symbol: YOU",
                channel_url="https://www.youtube.com/@TickerSymbolYOU",
                handle="@TickerSymbolYOU",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.SECTOR_ANALYSIS,
                secondary_focus=[ChannelType.DAILY_ANALYSIS, ChannelType.MARKET_NEWS],
                subscriber_count=275000,
                average_views=18000,
                upload_frequency="weekly",
                covers_markets=["US", "Global"],
                specializes_in=["Company Deep Dives", "Industry Analysis", "Investment Strategies"],
                typical_video_length="long",
                provides_charts=True,
                provides_price_targets=False,
                tracks_performance=False,
                has_live_streams=False,
                years_active=5,
                professional_background="Independent research analyst",
                accuracy_notes="High quality company analysis",
                has_transcripts=True,
                typical_upload_time="12:00 EST",
                last_checked=None
            ),
            
            # ========== CANADIAN CHANNELS ==========
            
            YouTubeStockChannel(
                channel_id="UCDVT1L-rANcnxLJqQIR4MQg",
                channel_name="Canadian in a T-Shirt",
                channel_url="https://www.youtube.com/@CanadianInATShirt",
                handle="@CanadianInATShirt",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=195000,
                average_views=22000,
                upload_frequency="daily",
                covers_markets=["Canada", "US"],
                specializes_in=["Canadian Stocks", "TSX Analysis", "Market Commentary"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=6,
                professional_background="Canadian market analyst",
                accuracy_notes="Good Canadian market coverage",
                has_transcripts=True,
                typical_upload_time="16:00 EST",
                last_checked=None
            ),
            
            # ========== MORE INDIAN CHANNELS ==========
            
            YouTubeStockChannel(
                channel_id="UCmGHkgDl8MBj4QhjOswPBmA",
                channel_name="Pranjal Kamra",
                channel_url="https://www.youtube.com/@PranjalKamra",
                handle="@PranjalKamra",
                region=Region.ASIA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=6230000,
                average_views=85000,
                upload_frequency="daily",
                covers_markets=["India", "US"],
                specializes_in=["Indian Stocks", "Value Investing", "Market Education"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=8,
                professional_background="Value investor, Finology founder",
                accuracy_notes="Strong educational content with good analysis",
                has_transcripts=True,
                typical_upload_time="18:00 IST",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UCJ7vJqGj10W8Nqd2JOJq5rw",
                channel_name="CA Rachana Ranade",
                channel_url="https://www.youtube.com/@rachanaphadkeranade",
                handle="@rachanaphadkeranade",
                region=Region.ASIA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.MARKET_NEWS,
                secondary_focus=[ChannelType.DAILY_ANALYSIS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=5050000,
                average_views=75000,
                upload_frequency="multiple_weekly",
                covers_markets=["India"],
                specializes_in=["Indian Market Education", "Stock Analysis", "Financial Planning"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=False,
                tracks_performance=False,
                has_live_streams=False,
                years_active=5,
                professional_background="Chartered Accountant",
                accuracy_notes="Educational focus with good fundamentals",
                has_transcripts=True,
                typical_upload_time="19:00 IST",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UC8vdOL8xFxtHOJFAmYIHEig",
                channel_name="Zerodha Varsity",
                channel_url="https://www.youtube.com/@zerodhaVarsity",
                handle="@zerodhaVarsity",
                region=Region.ASIA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.TECHNICAL_ANALYSIS,
                secondary_focus=[ChannelType.DAILY_ANALYSIS, ChannelType.TRADING_INSIGHTS],
                subscriber_count=1000000,
                average_views=35000,
                upload_frequency="weekly",
                covers_markets=["India"],
                specializes_in=["Technical Analysis", "Options Trading", "Market Education"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=6,
                professional_background="Zerodha brokerage educational wing",
                accuracy_notes="High quality educational content",
                has_transcripts=True,
                typical_upload_time="15:00 IST",
                last_checked=None
            ),
            
            # ========== UK CHANNELS ==========
            
            YouTubeStockChannel(
                channel_id="UCQOLhfgNxKBz8mqTFj8E1tA",
                channel_name="Pensioncraft",
                channel_url="https://www.youtube.com/@Pensioncraft",
                handle="@Pensioncraft",
                region=Region.EUROPE,
                language=Language.ENGLISH,
                primary_focus=ChannelType.MARKET_NEWS,
                secondary_focus=[ChannelType.DAILY_ANALYSIS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=285000,
                average_views=25000,
                upload_frequency="weekly",
                covers_markets=["UK", "Europe", "US"],
                specializes_in=["UK Stocks", "Pensions", "Investment Strategy"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=False,
                tracks_performance=True,
                has_live_streams=False,
                years_active=4,
                professional_background="UK financial advisor",
                accuracy_notes="Good UK market perspective",
                has_transcripts=True,
                typical_upload_time="16:00 GMT",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UCvKGlQhz8Jqg7X7MWnCsOxQ",
                channel_name="Damien Talks Money",
                channel_url="https://www.youtube.com/@DamienTalksMoney",
                handle="@DamienTalksMoney",
                region=Region.EUROPE,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=165000,
                average_views=15000,
                upload_frequency="daily",
                covers_markets=["UK", "Europe", "US"],
                specializes_in=["UK Stocks", "ETFs", "Investment Analysis"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=3,
                professional_background="UK investment analyst",
                accuracy_notes="Good UK market analysis",
                has_transcripts=True,
                typical_upload_time="17:00 GMT",
                last_checked=None
            ),
            
            # ========== GERMAN CHANNELS ==========
            
            YouTubeStockChannel(
                channel_id="UC-ejemplo-aktienanalyse",
                channel_name="Aktienanalyse",
                channel_url="https://www.youtube.com/@aktienanalyse",
                handle="@aktienanalyse",
                region=Region.EUROPE,
                language=Language.GERMAN,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.TECHNICAL_ANALYSIS, ChannelType.MARKET_NEWS],
                subscriber_count=125000,
                average_views=8000,
                upload_frequency="daily",
                covers_markets=["Germany", "Europe", "US"],
                specializes_in=["German Stocks", "DAX Analysis", "Technical Analysis"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=5,
                professional_background="German stock analyst",
                accuracy_notes="German market focus",
                has_transcripts=True,
                typical_upload_time="16:00 CET",
                last_checked=None
            ),
            
            # ========== FRENCH CHANNELS ==========
            
            YouTubeStockChannel(
                channel_id="UC-ejemplo-investir-france",
                channel_name="Investir en France",
                channel_url="https://www.youtube.com/@investirenfrance",
                handle="@investirenfrance",
                region=Region.EUROPE,
                language=Language.FRENCH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=95000,
                average_views=6000,
                upload_frequency="multiple_weekly",
                covers_markets=["France", "Europe", "US"],
                specializes_in=["French Stocks", "CAC 40", "European Markets"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=4,
                professional_background="French investment advisor",
                accuracy_notes="French market specialist",
                has_transcripts=True,
                typical_upload_time="18:00 CET",
                last_checked=None
            ),
            
            # ========== MORE LATIN AMERICA ==========
            
            YouTubeStockChannel(
                channel_id="UC-ejemplo-mexico-finanzas",
                channel_name="Finanzas México",
                channel_url="https://www.youtube.com/@finanzasmexico",
                handle="@finanzasmexico",
                region=Region.LATIN_AMERICA,
                language=Language.SPANISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.TRADING_INSIGHTS],
                subscriber_count=155000,
                average_views=12000,
                upload_frequency="daily",
                covers_markets=["Mexico", "US", "Latin America"],
                specializes_in=["Mexican Stocks", "BMV Analysis", "US-Mexico Relations"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=3,
                professional_background="Mexican financial analyst",
                accuracy_notes="Mexican market focus",
                has_transcripts=True,
                typical_upload_time="16:00 CST",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UC-ejemplo-argentina-bolsa",
                channel_name="Bolsa Argentina",
                channel_url="https://www.youtube.com/@bolsaargentina",
                handle="@bolsaargentina",
                region=Region.LATIN_AMERICA,
                language=Language.SPANISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=85000,
                average_views=7000,
                upload_frequency="daily",
                covers_markets=["Argentina", "Latin America", "US"],
                specializes_in=["Argentine Stocks", "Merval", "Economic Analysis"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=4,
                professional_background="Argentine economist",
                accuracy_notes="Argentine market specialist",
                has_transcripts=True,
                typical_upload_time="17:00 ART",
                last_checked=None
            ),
            
            # ========== MORE BRAZILIAN CHANNELS ==========
            
            YouTubeStockChannel(
                channel_id="UC-exemplo-brasil-investimentos",
                channel_name="Brasil Investimentos",
                channel_url="https://www.youtube.com/@brasilinvestimentos",
                handle="@brasilinvestimentos",
                region=Region.LATIN_AMERICA,
                language=Language.PORTUGUESE,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=275000,
                average_views=18000,
                upload_frequency="daily",
                covers_markets=["Brazil", "US"],
                specializes_in=["Brazilian Stocks", "Bovespa", "Economic Policy"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=5,
                professional_background="Brazilian investment advisor",
                accuracy_notes="Strong Brazilian market coverage",
                has_transcripts=True,
                typical_upload_time="16:00 BRT",
                last_checked=None
            ),
            
            # ========== ASIAN CHANNELS ==========
            
            # Japanese Channel
            YouTubeStockChannel(
                channel_id="UC-ejemplo-japan-stocks",
                channel_name="Japan Stock Analysis",
                channel_url="https://www.youtube.com/@japanstockanalysis",
                handle="@japanstockanalysis",
                region=Region.ASIA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=65000,
                average_views=5000,
                upload_frequency="daily",
                covers_markets=["Japan", "Asia"],
                specializes_in=["Japanese Stocks", "Nikkei", "Asian Markets"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=3,
                professional_background="Japan-based analyst",
                accuracy_notes="Japanese market specialist",
                has_transcripts=True,
                typical_upload_time="09:00 JST",
                last_checked=None
            ),
            
            # Korean Channel
            YouTubeStockChannel(
                channel_id="UC-ejemplo-korea-market",
                channel_name="Korea Market Today",
                channel_url="https://www.youtube.com/@koreamarkettoday",
                handle="@koreamarkettoday",
                region=Region.ASIA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.TECHNICAL_ANALYSIS],
                subscriber_count=45000,
                average_views=4000,
                upload_frequency="daily",
                covers_markets=["Korea", "Asia"],
                specializes_in=["Korean Stocks", "KOSPI", "K-tech Stocks"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=2,
                professional_background="Korean market analyst",
                accuracy_notes="Korean market focus",
                has_transcripts=True,
                typical_upload_time="09:00 KST",
                last_checked=None
            ),
            
            # ========== AUSTRALIAN CHANNELS ==========
            
            YouTubeStockChannel(
                channel_id="UC-ejemplo-aussie-stocks",
                channel_name="Aussie Stock Report",
                channel_url="https://www.youtube.com/@aussiestockreport",
                handle="@aussiestockreport",
                region=Region.OCEANIA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=75000,
                average_views=6000,
                upload_frequency="daily",
                covers_markets=["Australia", "Asia"],
                specializes_in=["Australian Stocks", "ASX", "Mining Stocks"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=4,
                professional_background="Australian investment advisor",
                accuracy_notes="Australian market specialist",
                has_transcripts=True,
                typical_upload_time="16:00 AEST",
                last_checked=None
            ),
            
            # ========== AFRICAN CHANNELS ==========
            
            YouTubeStockChannel(
                channel_id="UC-ejemplo-sa-stocks",
                channel_name="SA Shares",
                channel_url="https://www.youtube.com/@sashares",
                handle="@sashares",
                region=Region.AFRICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.DAILY_ANALYSIS,
                secondary_focus=[ChannelType.MARKET_NEWS, ChannelType.SECTOR_ANALYSIS],
                subscriber_count=11300,
                average_views=1200,
                upload_frequency="multiple_weekly",
                covers_markets=["South Africa", "Africa"],
                specializes_in=["South African Stocks", "JSE", "African Markets"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=3,
                professional_background="South African market analyst",
                accuracy_notes="African market specialist",
                has_transcripts=True,
                typical_upload_time="15:00 SAST",
                last_checked=None
            ),
            
            # ========== MORE SPECIALIZED US CHANNELS ==========
            
            YouTubeStockChannel(
                channel_id="UC-ejemplo-smallcap-trader",
                channel_name="Small Cap Trader",
                channel_url="https://www.youtube.com/@smallcaptrader",
                handle="@smallcaptrader",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.TRADING_INSIGHTS,
                secondary_focus=[ChannelType.DAILY_ANALYSIS, ChannelType.TECHNICAL_ANALYSIS],
                subscriber_count=125000,
                average_views=15000,
                upload_frequency="daily",
                covers_markets=["US"],
                specializes_in=["Small Cap Stocks", "Penny Stocks", "Momentum Trading"],
                typical_video_length="medium",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=True,
                years_active=6,
                professional_background="Small cap specialist",
                accuracy_notes="Small cap momentum focus",
                has_transcripts=True,
                typical_upload_time="09:30 EST",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UC-ejemplo-options-flow",
                channel_name="Options Flow Tracker",
                channel_url="https://www.youtube.com/@optionsflowtracker",
                handle="@optionsflowtracker",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.TRADING_INSIGHTS,
                secondary_focus=[ChannelType.DAILY_ANALYSIS, ChannelType.TECHNICAL_ANALYSIS],
                subscriber_count=85000,
                average_views=12000,
                upload_frequency="daily",
                covers_markets=["US"],
                specializes_in=["Options Flow", "Unusual Activity", "Smart Money Tracking"],
                typical_video_length="short",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=3,
                professional_background="Options specialist",
                accuracy_notes="Options flow analysis",
                has_transcripts=True,
                typical_upload_time="09:45 EST",
                last_checked=None
            ),
            
            # ========== MORE SECTOR-SPECIFIC CHANNELS ==========
            
            YouTubeStockChannel(
                channel_id="UC-ejemplo-biotech-stocks",
                channel_name="Biotech Stock Analysis",
                channel_url="https://www.youtube.com/@biotechstockanalysis",
                handle="@biotechstockanalysis",
                region=Region.NORTH_AMERICA,
                language=Language.ENGLISH,
                primary_focus=ChannelType.SECTOR_ANALYSIS,
                secondary_focus=[ChannelType.DAILY_ANALYSIS, ChannelType.MARKET_NEWS],
                subscriber_count=65000,
                average_views=8000,
                upload_frequency="multiple_weekly",
                covers_markets=["US", "Global"],
                specializes_in=["Biotech Stocks", "FDA Approvals", "Clinical Trials"],
                typical_video_length="long",
                provides_charts=True,
                provides_price_targets=True,
                tracks_performance=True,
                has_live_streams=False,
                years_active=4,
                professional_background="Biotech industry analyst",
                accuracy_notes="Biotech sector specialist",
                has_transcripts=True,
                typical_upload_time="16:00 EST",
                last_checked=None
            ),
            
            YouTubeStockChannel(
                channel_id="UC-ejemplo-tech-stocks",
                channel_name="Tech Stock Daily",
            )
            
            return channel
            
        except Exception as e:
            print(f"Error creating channel from data: {e}")
            return None
    
    def get_channel(self, channel_id: str) -> Optional[YouTubeStockChannel]:
        """Get channel by ID"""
        return self.channels_by_id.get(channel_id)
    
    def get_channels_by_region(self, region: Region) -> List[YouTubeStockChannel]:
        """Get all channels from a specific region"""
        return [channel for channel in self.channels if channel.region == region]
    
    def get_channels_by_language(self, language: Language) -> List[YouTubeStockChannel]:
        """Get all channels in a specific language"""
        return [channel for channel in self.channels if channel.language == language]
    
    def get_channels_by_focus(self, focus_type: ChannelType) -> List[YouTubeStockChannel]:
        """Get channels by primary focus type"""
        return [channel for channel in self.channels.values() if channel.primary_focus == focus_type]
    
    def get_daily_channels(self) -> List[YouTubeStockChannel]:
        """Get channels that upload daily content"""
        return [channel for channel in self.channels.values() 
                if channel.upload_frequency in ["daily", "multiple_daily"]]
    
    def get_high_quality_channels(self) -> List[YouTubeStockChannel]:
        """Get channels with high credibility indicators"""
        return [channel for channel in self.channels.values() 
                if (channel.provides_charts and 
                    channel.years_active and channel.years_active >= 3 and
                    channel.subscriber_count and channel.subscriber_count >= 50000)]
    
    def get_channels_covering_market(self, market: str) -> List[YouTubeStockChannel]:
        """Get channels that cover a specific market (e.g., 'US', 'Europe')"""
        return [channel for channel in self.channels.values() 
                if market in channel.covers_markets]
    
    def get_all_channel_ids(self) -> List[str]:
        """Get list of all channel IDs for API monitoring"""
        return list(self.channels.keys())
    
    def get_channel_summary(self) -> Dict:
        """Get summary statistics of the database"""
        total_channels = len(self.channels)
        by_region = {}
        by_language = {}
        by_focus = {}
        daily_uploaders = len(self.get_daily_channels())
        
        for channel in self.channels.values():
            # Count by region
            region_key = channel.region.value
            by_region[region_key] = by_region.get(region_key, 0) + 1
            
            # Count by language
            lang_key = channel.language.value
            by_language[lang_key] = by_language.get(lang_key, 0) + 1
            
            # Count by focus
            focus_key = channel.primary_focus.value
            by_focus[focus_key] = by_focus.get(focus_key, 0) + 1
        
        return {
            "total_channels": total_channels,
            "daily_uploaders": daily_uploaders,
            "by_region": by_region,
            "by_language": by_language,
            "by_focus": by_focus,
            "high_quality_channels": len(self.get_high_quality_channels())
        }

def main():
    """Test the YouTube stock channels database"""
    
    print("="*80)
    print("YOUTUBE STOCK ANALYSIS CHANNELS DATABASE")
    print("="*80)
    
    # Initialize database
    db = YouTubeStockChannelsDatabase()
    
    # Get summary
    summary = db.get_channel_summary()
    print(f"\nDATABASE SUMMARY:")
    print(f"Total Channels: {summary['total_channels']}")
    print(f"Daily Uploaders: {summary['daily_uploaders']}")
    print(f"High Quality Channels: {summary['high_quality_channels']}")
    
    print(f"\nBY REGION:")
    for region, count in summary['by_region'].items():
        print(f"  {region}: {count}")
    
    print(f"\nBY LANGUAGE:")
    for language, count in summary['by_language'].items():
        print(f"  {language}: {count}")
    
    print(f"\nBY FOCUS:")
    for focus, count in summary['by_focus'].items():
        print(f"  {focus}: {count}")
    
    # Show some example channels
    print(f"\nDAILY ANALYSIS CHANNELS:")
    daily_analysis = db.get_channels_by_focus(ChannelType.DAILY_ANALYSIS)
    for channel in daily_analysis[:5]:
        print(f"  {channel.channel_name} ({channel.language.value}) - {channel.subscriber_count:,} subs")
    
    print(f"\nCHANNELS COVERING US MARKET:")
    us_channels = db.get_channels_covering_market("US")
    for channel in us_channels[:5]:
        print(f"  {channel.channel_name} - {channel.covers_markets}")
    
    print(f"\n[SUCCESS] Database initialized with {len(db.channels)} stock analysis channels")

if __name__ == "__main__":
    main()