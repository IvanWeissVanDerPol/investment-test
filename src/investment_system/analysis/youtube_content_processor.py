"""
YouTube Stock Analysis Content Processor

Processes YouTube video transcripts to extract stock mentions, sentiment analysis,
market insights, and analyst recommendations. Integrates with the investment system
to provide real-time market intelligence from global stock analysis channels.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import json

from ..data.youtube_api_client import YouTubeVideo, YouTubeAPIClient
from ..data.youtube_stock_channels_database import YouTubeStockChannelsDatabase
from ..utils.cache_manager import CacheManager
from ..utils.config_loader import ConfigurationManager

logger = logging.getLogger(__name__)

@dataclass
class StockMention:
    """Individual stock mention in content"""
    symbol: str
    company_name: Optional[str]
    mentions_count: int
    context_snippets: List[str]
    sentiment_score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    recommendation: Optional[str]  # buy, sell, hold, avoid
    price_target: Optional[float]
    time_horizon: Optional[str]  # short, medium, long
    position_mentions: List[str]  # buy, sell, hold references

@dataclass
class MarketInsight:
    """Market trend or insight extracted from content"""
    topic: str
    sentiment: float
    confidence: float
    key_points: List[str]
    supporting_evidence: List[str]
    analyst_view: str

@dataclass
class ProcessedContent:
    """Processed YouTube video content with extracted insights"""
    video_id: str
    video_title: str
    channel_id: str
    channel_title: str
    published_at: datetime
    processing_timestamp: datetime
    
    # Extracted data
    stock_mentions: List[StockMention]
    market_insights: List[MarketInsight]
    overall_sentiment: float
    confidence_score: float
    
    # Metadata
    transcript_language: str
    transcript_length: int
    processing_time_seconds: float
    keywords_found: List[str]
    topics_identified: List[str]

class YouTubeContentProcessor:
    """
    Processes YouTube stock analysis content to extract actionable investment insights
    
    Features:
    - Stock ticker and company name extraction
    - Multi-language sentiment analysis
    - Recommendation classification (buy/sell/hold)
    - Price target extraction
    - Market trend identification
    - Analyst consensus building
    """
    
    def __init__(self, config_manager: ConfigurationManager = None):
        """Initialize the content processor"""
        self.config_manager = config_manager or ConfigurationManager()
        self.cache_manager = CacheManager()
        
        # Load stock universe for symbol matching
        try:
            data_config = self.config_manager.load_config('data')
            self.stock_universe = self._build_stock_universe(data_config)
        except Exception as e:
            logger.warning(f"Could not load stock universe: {e}")
            self.stock_universe = {}
        
        # Load processing configuration
        try:
            system_config = self.config_manager.load_config('system')
            self.processing_config = system_config.get('youtube_api', {}).get('content_processing', {})
        except Exception as e:
            logger.warning(f"Could not load processing config: {e}")
            self.processing_config = {}
        
        # Build regex patterns
        self._build_patterns()
        
        # Sentiment keywords by language
        self._load_sentiment_keywords()
        
        logger.info("YouTube content processor initialized")
    
    def _build_stock_universe(self, data_config: Dict) -> Dict[str, Dict]:
        """Build comprehensive stock symbol mapping"""
        universe = {}
        
        # Add major stocks from config
        for category, stocks in data_config.get('companies', {}).items():
            if isinstance(stocks, dict):
                for symbol, company_data in stocks.items():
                    if isinstance(company_data, dict):
                        universe[symbol.upper()] = {
                            'symbol': symbol.upper(),
                            'name': company_data.get('name', ''),
                            'category': category,
                            'aliases': company_data.get('aliases', [])
                        }
        
        # Add ETFs
        for category, etfs in data_config.get('etfs', {}).items():
            if isinstance(etfs, dict):
                for symbol, etf_data in etfs.items():
                    if isinstance(etf_data, dict):
                        universe[symbol.upper()] = {
                            'symbol': symbol.upper(),
                            'name': etf_data.get('name', ''),
                            'category': f"etf_{category}",
                            'aliases': etf_data.get('aliases', [])
                        }
        
        # Add common aliases and variations
        aliases_map = {}
        for symbol, data in universe.items():
            # Add company name as alias
            if data['name']:
                name_clean = re.sub(r'[^\w\s]', '', data['name']).strip()
                aliases_map[name_clean.upper()] = symbol
                
                # Add short versions
                words = name_clean.split()
                if len(words) > 1:
                    aliases_map[words[0].upper()] = symbol
            
            # Add configured aliases
            for alias in data.get('aliases', []):
                aliases_map[alias.upper()] = symbol
        
        # Merge aliases into universe
        for alias, symbol in aliases_map.items():
            if alias not in universe:
                universe[alias] = universe[symbol].copy()
                universe[alias]['is_alias'] = True
        
        logger.info(f"Built stock universe with {len(universe)} symbols/aliases")
        return universe
    
    def _build_patterns(self):
        """Build regex patterns for content extraction"""
        # Stock symbol patterns
        self.stock_patterns = [
            r'\b([A-Z]{1,5})\b',  # Basic ticker pattern
            r'\$([A-Z]{1,5})\b',  # $TICKER format
            r'\b([A-Z]{1,5})\s+stock\b',  # TICKER stock
            r'\bstock\s+([A-Z]{1,5})\b',  # stock TICKER
        ]
        
        # Price patterns
        self.price_patterns = [
            r'\$(\d+(?:\.\d{2})?)',  # $123.45
            r'(\d+(?:\.\d{2})?)\s*dollars?',  # 123.45 dollars
            r'price\s+target\s+(?:of\s+)?\$?(\d+(?:\.\d{2})?)',  # price target $123
            r'target\s+(?:price\s+)?(?:of\s+)?\$?(\d+(?:\.\d{2})?)',  # target price $123
        ]
        
        # Recommendation patterns
        self.recommendation_patterns = {
            'buy': [
                r'\bbuy\b', r'\bpurchase\b', r'\bacquire\b', r'\binvest\s+in\b',
                r'\blong\b', r'\bbullish\b', r'\bupgrade\b', r'\boverweight\b',
                r'\bstrong\s+buy\b', r'\brecommend\s+buy\b'
            ],
            'sell': [
                r'\bsell\b', r'\bdispose\b', r'\bexit\b', r'\bshort\b',
                r'\bbearish\b', r'\bdowngrade\b', r'\bunderweight\b',
                r'\bstrong\s+sell\b', r'\brecommend\s+sell\b', r'\bavoid\b'
            ],
            'hold': [
                r'\bhold\b', r'\bmaintain\b', r'\bneutral\b', r'\bkeep\b',
                r'\bstay\s+in\b', r'\bno\s+change\b', r'\bhold\s+position\b'
            ]
        }
        
        # Time horizon patterns
        self.time_horizon_patterns = {
            'short': [r'\bshort\s+term\b', r'\bnear\s+term\b', r'\bthis\s+week\b', r'\bthis\s+month\b'],
            'medium': [r'\bmedium\s+term\b', r'\bmid\s+term\b', r'\bthis\s+quarter\b', r'\bthis\s+year\b'],
            'long': [r'\blong\s+term\b', r'\blong\s+run\b', r'\bnext\s+year\b', r'\bmulti\s+year\b']
        }
    
    def _load_sentiment_keywords(self):
        """Load sentiment keywords for multiple languages"""
        self.sentiment_keywords = {
            'positive': {
                'en': ['bullish', 'positive', 'optimistic', 'strong', 'good', 'excellent', 'great', 'buy',
                       'growth', 'profit', 'gain', 'rally', 'surge', 'boom', 'uptrend', 'outperform'],
                'es': ['alcista', 'positivo', 'optimista', 'fuerte', 'bueno', 'excelente', 'comprar',
                       'crecimiento', 'ganancia', 'alza', 'subida', 'auge'],
                'pt': ['otimista', 'positivo', 'forte', 'bom', 'excelente', 'comprar',
                       'crescimento', 'lucro', 'ganho', 'alta', 'subida']
            },
            'negative': {
                'en': ['bearish', 'negative', 'pessimistic', 'weak', 'bad', 'poor', 'terrible', 'sell',
                       'loss', 'decline', 'crash', 'drop', 'fall', 'downtrend', 'underperform'],
                'es': ['bajista', 'negativo', 'pesimista', 'débil', 'malo', 'pobre', 'vender',
                       'pérdida', 'declive', 'caída', 'baja'],
                'pt': ['pessimista', 'negativo', 'fraco', 'ruim', 'pobre', 'vender',
                       'perda', 'declínio', 'queda', 'baixa']
            }
        }
    
    def extract_stock_mentions(self, text: str, language: str = 'en') -> List[StockMention]:
        """Extract stock mentions with context and sentiment"""
        mentions = defaultdict(lambda: {
            'count': 0,
            'contexts': [],
            'sentiments': [],
            'recommendations': [],
            'prices': []
        })
        
        # Normalize text
        text_upper = text.upper()
        sentences = re.split(r'[.!?]+', text)
        
        # Find stock symbols
        for pattern in self.stock_patterns:
            for match in re.finditer(pattern, text_upper, re.IGNORECASE):
                symbol = match.group(1).upper()
                
                # Check if valid symbol
                if symbol in self.stock_universe and len(symbol) > 1:
                    # Find sentence containing this mention
                    position = match.start()
                    sentence_idx = self._find_sentence_index(sentences, position)
                    if sentence_idx < len(sentences):
                        context = sentences[sentence_idx].strip()
                        
                        mentions[symbol]['count'] += 1
                        mentions[symbol]['contexts'].append(context)
                        
                        # Analyze sentiment of this context
                        sentiment = self._analyze_sentiment(context, language)
                        mentions[symbol]['sentiments'].append(sentiment)
                        
                        # Extract recommendations
                        recommendation = self._extract_recommendation(context)
                        if recommendation:
                            mentions[symbol]['recommendations'].append(recommendation)
                        
                        # Extract price targets
                        prices = self._extract_prices(context)
                        mentions[symbol]['prices'].extend(prices)
        
        # Convert to StockMention objects
        stock_mentions = []
        for symbol, data in mentions.items():
            if data['count'] > 0:
                # Calculate aggregate sentiment
                avg_sentiment = sum(data['sentiments']) / len(data['sentiments']) if data['sentiments'] else 0.0
                
                # Determine primary recommendation
                rec_counter = Counter(data['recommendations'])
                primary_rec = rec_counter.most_common(1)[0][0] if rec_counter else None
                
                # Get company info
                company_info = self.stock_universe.get(symbol, {})
                
                mention = StockMention(
                    symbol=symbol,
                    company_name=company_info.get('name', ''),
                    mentions_count=data['count'],
                    context_snippets=data['contexts'][:5],  # Limit to 5 examples
                    sentiment_score=avg_sentiment,
                    confidence=min(data['count'] / 10.0, 1.0),  # More mentions = higher confidence
                    recommendation=primary_rec,
                    price_target=max(data['prices']) if data['prices'] else None,
                    time_horizon=self._extract_time_horizon(text),
                    position_mentions=data['recommendations']
                )
                stock_mentions.append(mention)
        
        return sorted(stock_mentions, key=lambda x: x.mentions_count, reverse=True)
    
    def _find_sentence_index(self, sentences: List[str], position: int) -> int:
        """Find which sentence contains the character position"""
        char_count = 0
        for i, sentence in enumerate(sentences):
            char_count += len(sentence) + 1  # +1 for delimiter
            if char_count > position:
                return i
        return len(sentences) - 1
    
    def _analyze_sentiment(self, text: str, language: str = 'en') -> float:
        """Analyze sentiment of text snippet"""
        if language not in self.sentiment_keywords['positive']:
            language = 'en'  # Fallback to English
        
        text_lower = text.lower()
        
        positive_count = 0
        negative_count = 0
        
        # Count positive keywords
        for keyword in self.sentiment_keywords['positive'][language]:
            positive_count += len(re.findall(r'\b' + keyword + r'\b', text_lower))
        
        # Count negative keywords
        for keyword in self.sentiment_keywords['negative'][language]:
            negative_count += len(re.findall(r'\b' + keyword + r'\b', text_lower))
        
        # Calculate sentiment score
        total_count = positive_count + negative_count
        if total_count == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / total_count
        return max(-1.0, min(1.0, sentiment))
    
    def _extract_recommendation(self, text: str) -> Optional[str]:
        """Extract buy/sell/hold recommendation from text"""
        text_lower = text.lower()
        
        for rec_type, patterns in self.recommendation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return rec_type
        
        return None
    
    def _extract_prices(self, text: str) -> List[float]:
        """Extract price targets and values from text"""
        prices = []
        
        for pattern in self.price_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    price = float(match.group(1))
                    if 0.01 <= price <= 10000:  # Reasonable price range
                        prices.append(price)
                except (ValueError, IndexError):
                    continue
        
        return prices
    
    def _extract_time_horizon(self, text: str) -> Optional[str]:
        """Extract time horizon from text"""
        text_lower = text.lower()
        
        for horizon, patterns in self.time_horizon_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return horizon
        
        return None
    
    def extract_market_insights(self, text: str, language: str = 'en') -> List[MarketInsight]:
        """Extract general market insights and trends"""
        insights = []
        
        # Market trend keywords
        trend_keywords = {
            'bull_market': ['bull market', 'bullish trend', 'market rally', 'uptrend'],
            'bear_market': ['bear market', 'bearish trend', 'market decline', 'downtrend'],
            'volatility': ['volatile', 'volatility', 'uncertain', 'choppy'],
            'economic_outlook': ['economy', 'gdp', 'inflation', 'interest rates', 'fed', 'recession']
        }
        
        text_lower = text.lower()
        sentences = re.split(r'[.!?]+', text)
        
        for topic, keywords in trend_keywords.items():
            relevant_sentences = []
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(keyword in sentence_lower for keyword in keywords):
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                # Analyze overall sentiment for this topic
                combined_text = ' '.join(relevant_sentences)
                sentiment = self._analyze_sentiment(combined_text, language)
                
                insight = MarketInsight(
                    topic=topic.replace('_', ' ').title(),
                    sentiment=sentiment,
                    confidence=min(len(relevant_sentences) / 5.0, 1.0),
                    key_points=relevant_sentences[:3],
                    supporting_evidence=relevant_sentences,
                    analyst_view=self._summarize_analyst_view(relevant_sentences)
                )
                insights.append(insight)
        
        return insights
    
    def _summarize_analyst_view(self, sentences: List[str]) -> str:
        """Summarize analyst view from sentences"""
        if not sentences:
            return ""
        
        # Simple summarization - take key phrases
        combined = ' '.join(sentences)
        words = combined.split()
        
        # Return first 20 words as summary
        return ' '.join(words[:20]) + "..." if len(words) > 20 else combined
    
    def process_video_content(self, video: YouTubeVideo) -> Optional[ProcessedContent]:
        """Process a complete video for stock analysis insights"""
        start_time = datetime.now()
        
        # Check cache first
        cache_key = f"processed_content_{video.video_id}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            return ProcessedContent(**cached_result)
        
        # Validate input
        if not video.transcript:
            logger.warning(f"No transcript available for video {video.video_id}")
            return None
        
        try:
            # Extract stock mentions
            stock_mentions = self.extract_stock_mentions(
                video.transcript, 
                video.transcript_language or 'en'
            )
            
            # Extract market insights
            market_insights = self.extract_market_insights(
                video.transcript,
                video.transcript_language or 'en'
            )
            
            # Calculate overall sentiment
            overall_sentiment = self._analyze_sentiment(
                video.transcript,
                video.transcript_language or 'en'
            )
            
            # Calculate confidence score based on content quality
            confidence_score = self._calculate_confidence_score(
                video, stock_mentions, market_insights
            )
            
            # Extract keywords and topics
            keywords = self._extract_keywords(video.transcript)
            topics = self._identify_topics(video.transcript)
            
            # Create processed content object
            processed_content = ProcessedContent(
                video_id=video.video_id,
                video_title=video.title,
                channel_id=video.channel_id,
                channel_title=video.channel_title,
                published_at=video.published_at,
                processing_timestamp=datetime.now(),
                stock_mentions=stock_mentions,
                market_insights=market_insights,
                overall_sentiment=overall_sentiment,
                confidence_score=confidence_score,
                transcript_language=video.transcript_language or 'en',
                transcript_length=len(video.transcript),
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                keywords_found=keywords,
                topics_identified=topics
            )
            
            # Cache result for 24 hours
            self.cache_manager.set(cache_key, asdict(processed_content), expire_hours=24)
            
            logger.info(f"Processed video {video.video_id}: {len(stock_mentions)} stocks, {len(market_insights)} insights")
            
            return processed_content
            
        except Exception as e:
            logger.error(f"Error processing video {video.video_id}: {e}")
            return None
    
    def _calculate_confidence_score(self, video: YouTubeVideo, stock_mentions: List[StockMention], 
                                   market_insights: List[MarketInsight]) -> float:
        """Calculate confidence score for processed content"""
        score = 0.0
        
        # Video quality factors
        if video.view_count > 1000:
            score += 0.2
        if video.like_count > 50:
            score += 0.1
        
        # Content quality factors
        if len(stock_mentions) > 0:
            score += 0.3
        if len(market_insights) > 0:
            score += 0.2
        
        # Transcript quality
        if video.transcript and len(video.transcript) > 500:
            score += 0.2
        
        return min(score, 1.0)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key financial keywords from text"""
        financial_keywords = [
            'earnings', 'revenue', 'profit', 'loss', 'dividend', 'valuation',
            'growth', 'margin', 'debt', 'cash', 'buyback', 'merger', 'acquisition',
            'ipo', 'split', 'options', 'futures', 'volatility', 'risk'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in financial_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _identify_topics(self, text: str) -> List[str]:
        """Identify main topics discussed in the content"""
        topic_keywords = {
            'earnings': ['earnings', 'eps', 'quarterly results', 'revenue'],
            'technical_analysis': ['support', 'resistance', 'moving average', 'chart', 'pattern'],
            'market_outlook': ['outlook', 'forecast', 'prediction', 'expectation'],
            'sector_analysis': ['sector', 'industry', 'vertical', 'segment'],
            'economic_data': ['inflation', 'interest rates', 'gdp', 'unemployment']
        }
        
        identified_topics = []
        text_lower = text.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                identified_topics.append(topic)
        
        return identified_topics
    
    def process_channel_content(self, channel_id: str, days_back: int = 7) -> List[ProcessedContent]:
        """Process all recent content from a channel"""
        logger.info(f"Processing recent content for channel {channel_id}")
        
        # Get YouTube client and recent videos
        from ..data import get_youtube_client
        client = get_youtube_client()
        
        recent_videos = client.get_recent_videos(channel_id, days_back)
        
        processed_content = []
        for video in recent_videos:
            if video.transcript:  # Only process videos with transcripts
                processed = self.process_video_content(video)
                if processed:
                    processed_content.append(processed)
        
        logger.info(f"Processed {len(processed_content)} videos from channel {channel_id}")
        return processed_content
    
    def analyze_analyst_consensus(self, processed_contents: List[ProcessedContent], 
                                symbol: str) -> Dict[str, Any]:
        """Analyze consensus view on a specific stock from multiple analysts"""
        relevant_content = []
        
        # Find content mentioning the symbol
        for content in processed_contents:
            for mention in content.stock_mentions:
                if mention.symbol == symbol:
                    relevant_content.append((content, mention))
        
        if not relevant_content:
            return {}
        
        # Aggregate data
        sentiments = [mention.sentiment_score for _, mention in relevant_content]
        recommendations = [mention.recommendation for _, mention in relevant_content if mention.recommendation]
        price_targets = [mention.price_target for _, mention in relevant_content if mention.price_target]
        
        # Calculate consensus
        consensus = {
            'symbol': symbol,
            'analyst_count': len(relevant_content),
            'avg_sentiment': sum(sentiments) / len(sentiments) if sentiments else 0.0,
            'sentiment_range': [min(sentiments), max(sentiments)] if sentiments else [0.0, 0.0],
            'recommendation_distribution': dict(Counter(recommendations)),
            'price_targets': {
                'count': len(price_targets),
                'avg': sum(price_targets) / len(price_targets) if price_targets else None,
                'range': [min(price_targets), max(price_targets)] if price_targets else None
            },
            'recent_mentions': len(relevant_content),
            'channels_covering': len(set(content.channel_title for content, _ in relevant_content))
        }
        
        return consensus

# Convenience function for easy import
def get_content_processor() -> YouTubeContentProcessor:
    """Get configured YouTube content processor instance"""
    return YouTubeContentProcessor()