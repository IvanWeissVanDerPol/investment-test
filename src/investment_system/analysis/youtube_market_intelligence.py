"""
YouTube Market Intelligence Engine

Aggregates insights from multiple YouTube stock analysis channels to generate
investment signals, track analyst performance, and provide market intelligence
for the AI investment decision engine.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import statistics
import json
from pathlib import Path

from .youtube_content_processor import ProcessedContent, StockMention, MarketInsight, get_content_processor
from ..data import get_youtube_client, YouTubeStockChannelsDatabase
from ..utils.cache_manager import CacheManager
from ..utils.config_loader import ConfigurationManager

logger = logging.getLogger(__name__)

@dataclass
class AnalystPerformance:
    """Track individual analyst/channel performance"""
    channel_id: str
    channel_name: str
    region: str
    language: str
    
    # Performance metrics
    total_predictions: int
    correct_predictions: int
    accuracy_rate: float
    
    # Content metrics
    videos_processed: int
    avg_stocks_per_video: float
    avg_sentiment_accuracy: float
    
    # Specialty tracking
    best_performing_stocks: List[str]
    preferred_sectors: List[str]
    avg_processing_time: float
    
    # Reliability indicators
    consistency_score: float  # How consistent are their predictions
    confidence_calibration: float  # How well confidence matches accuracy
    bias_score: float  # Tendency toward bullish/bearish
    
    # Recent performance
    last_30_days_accuracy: float
    recent_stock_calls: List[Dict]
    
    @property
    def reliability_grade(self) -> str:
        """Calculate overall reliability grade A-F"""
        if self.accuracy_rate >= 0.75 and self.consistency_score >= 0.7:
            return "A"
        elif self.accuracy_rate >= 0.65 and self.consistency_score >= 0.6:
            return "B"
        elif self.accuracy_rate >= 0.55 and self.consistency_score >= 0.5:
            return "C"
        elif self.accuracy_rate >= 0.45:
            return "D"
        else:
            return "F"

@dataclass
class MarketIntelligenceSignal:
    """Investment signal generated from YouTube intelligence"""
    symbol: str
    company_name: str
    signal_type: str  # strong_buy, buy, hold, sell, strong_sell
    confidence: float  # 0.0 to 1.0
    
    # Signal components
    analyst_consensus: Dict[str, int]  # recommendation distribution
    sentiment_score: float  # aggregate sentiment
    price_target_consensus: Optional[float]
    price_target_range: Optional[Tuple[float, float]]
    
    # Supporting data
    analysts_covering: int
    total_mentions: int
    mention_frequency_trend: str  # increasing, stable, decreasing
    geographic_consensus: Dict[str, float]  # sentiment by region
    
    # Quality indicators
    signal_strength: float  # How strong is this signal
    data_freshness: float  # How recent is the data
    analyst_quality_score: float  # Average quality of contributing analysts
    
    # Metadata
    generated_at: datetime
    valid_until: datetime
    supporting_channels: List[str]
    key_insights: List[str]

@dataclass
class MarketOverview:
    """Overall market intelligence summary"""
    timestamp: datetime
    
    # Market sentiment
    overall_market_sentiment: float
    sector_sentiments: Dict[str, float]
    sentiment_momentum: str  # improving, stable, declining
    
    # Top signals
    top_buy_signals: List[MarketIntelligenceSignal]
    top_sell_signals: List[MarketIntelligenceSignal]
    emerging_opportunities: List[MarketIntelligenceSignal]
    
    # Market themes
    trending_topics: List[str]
    most_discussed_stocks: List[str]
    analyst_consensus_strength: float
    
    # Risk indicators
    market_uncertainty: float
    volatility_expectations: str
    risk_sentiment: float

class YouTubeMarketIntelligence:
    """
    Aggregates YouTube stock analysis to generate market intelligence and investment signals
    
    Features:
    - Multi-analyst consensus building
    - Signal generation with confidence scoring
    - Analyst performance tracking
    - Market trend identification
    - Geographic sentiment analysis
    - Automated investment recommendations
    """
    
    def __init__(self, config_manager: ConfigurationManager = None):
        """Initialize the market intelligence engine"""
        self.config_manager = config_manager or ConfigurationManager()
        self.cache_manager = CacheManager()
        self.content_processor = get_content_processor()
        
        # Load channels and create analyst mapping
        self.channels_db = YouTubeStockChannelsDatabase()
        self.channels = list(self.channels_db.channels.values())
        self.channel_map = {ch.channel_id: ch for ch in self.channels}
        
        # Signal generation parameters
        self.signal_config = {
            'min_analysts_for_signal': 3,
            'min_mentions_for_signal': 5,
            'confidence_threshold': 0.6,
            'signal_validity_hours': 24,
            'sentiment_threshold_buy': 0.3,
            'sentiment_threshold_sell': -0.3,
            'price_target_weight': 0.3,
            'analyst_quality_weight': 0.4,
            'recency_weight': 0.3
        }
        
        # Performance tracking
        self.analyst_performance = {}
        self._load_analyst_performance()
        
        logger.info("YouTube Market Intelligence Engine initialized")
    
    def _load_analyst_performance(self):
        """Load historical analyst performance data"""
        try:
            cache_key = "analyst_performance_history"
            cached_data = self.cache_manager.get(cache_key)
            
            if cached_data:
                self.analyst_performance = {
                    ch_id: AnalystPerformance(**data) 
                    for ch_id, data in cached_data.items()
                }
                logger.info(f"Loaded performance data for {len(self.analyst_performance)} analysts")
            else:
                # Initialize default performance for all channels
                self._initialize_analyst_performance()
                
        except Exception as e:
            logger.warning(f"Could not load analyst performance: {e}")
            self._initialize_analyst_performance()
    
    def _initialize_analyst_performance(self):
        """Initialize default performance metrics for all analysts"""
        for channel in self.channels:
            self.analyst_performance[channel.channel_id] = AnalystPerformance(
                channel_id=channel.channel_id,
                channel_name=channel.channel_name,
                region=channel.region.value,
                language=channel.language.value,
                total_predictions=0,
                correct_predictions=0,
                accuracy_rate=0.5,  # Start neutral
                videos_processed=0,
                avg_stocks_per_video=0.0,
                avg_sentiment_accuracy=0.5,
                best_performing_stocks=[],
                preferred_sectors=[],
                avg_processing_time=0.0,
                consistency_score=0.5,
                confidence_calibration=0.5,
                bias_score=0.0,
                last_30_days_accuracy=0.5,
                recent_stock_calls=[]
            )
        
        logger.info(f"Initialized performance tracking for {len(self.analyst_performance)} analysts")
    
    def _save_analyst_performance(self):
        """Save analyst performance data to cache"""
        try:
            cache_key = "analyst_performance_history"
            cache_data = {
                ch_id: asdict(perf) 
                for ch_id, perf in self.analyst_performance.items()
            }
            # Cache for 30 days
            self.cache_manager.set(cache_key, cache_data, expire_hours=24*30)
            logger.debug("Saved analyst performance data")
        except Exception as e:
            logger.error(f"Could not save analyst performance: {e}")
    
    def process_channel_batch(self, days_back: int = 1) -> Dict[str, List[ProcessedContent]]:
        """
        Process recent content from all channels
        
        Args:
            days_back: Number of days to look back for content
            
        Returns:
            Dictionary mapping channel_id to list of processed content
        """
        logger.info(f"Processing content from {len(self.channels)} channels ({days_back} days back)")
        
        youtube_client = get_youtube_client()
        all_processed = {}
        
        for i, channel in enumerate(self.channels, 1):
            logger.info(f"Processing channel {i}/{len(self.channels)}: {channel.channel_name}")
            
            try:
                # Get recent videos with transcripts
                recent_videos = youtube_client.get_recent_videos(channel.channel_id, days_back)
                videos_with_transcripts = [v for v in recent_videos if v.transcript]
                
                # Process each video
                processed_content = []
                for video in videos_with_transcripts:
                    processed = self.content_processor.process_video_content(video)
                    if processed and processed.stock_mentions:
                        processed_content.append(processed)
                
                all_processed[channel.channel_id] = processed_content
                
                # Update analyst performance
                if channel.channel_id in self.analyst_performance:
                    perf = self.analyst_performance[channel.channel_id]
                    perf.videos_processed += len(processed_content)
                    if processed_content:
                        avg_stocks = sum(len(p.stock_mentions) for p in processed_content) / len(processed_content)
                        perf.avg_stocks_per_video = (perf.avg_stocks_per_video + avg_stocks) / 2
                
                logger.debug(f"Processed {len(processed_content)} videos from {channel.channel_name}")
                
            except Exception as e:
                logger.error(f"Error processing channel {channel.channel_name}: {e}")
                all_processed[channel.channel_id] = []
        
        self._save_analyst_performance()
        return all_processed
    
    def build_stock_consensus(self, processed_contents: Dict[str, List[ProcessedContent]], 
                            symbol: str) -> Dict[str, Any]:
        """
        Build consensus view on a specific stock from all analysts
        
        Args:
            processed_contents: Channel processing results
            symbol: Stock symbol to analyze
            
        Returns:
            Comprehensive consensus analysis
        """
        consensus_data = {
            'symbol': symbol,
            'analysts_covering': 0,
            'total_mentions': 0,
            'channels_mentioning': [],
            'sentiment_scores': [],
            'recommendations': [],
            'price_targets': [],
            'regional_sentiment': defaultdict(list),
            'language_sentiment': defaultdict(list),
            'channel_quality_scores': [],
            'mention_contexts': [],
            'latest_mentions': []
        }
        
        # Aggregate data from all channels
        for channel_id, contents in processed_contents.items():
            channel = self.channel_map.get(channel_id)
            if not channel:
                continue
            
            channel_mentions = []
            for content in contents:
                for mention in content.stock_mentions:
                    if mention.symbol == symbol:
                        channel_mentions.append(mention)
                        
                        # Aggregate data
                        consensus_data['sentiment_scores'].append(mention.sentiment_score)
                        consensus_data['regional_sentiment'][channel.region.value].append(mention.sentiment_score)
                        consensus_data['language_sentiment'][channel.language.value].append(mention.sentiment_score)
                        consensus_data['mention_contexts'].extend(mention.context_snippets[:2])
                        
                        if mention.recommendation:
                            consensus_data['recommendations'].append(mention.recommendation)
                        if mention.price_target:
                            consensus_data['price_targets'].append(mention.price_target)
                        
                        consensus_data['latest_mentions'].append({
                            'channel': channel.channel_name,
                            'published': content.published_at,
                            'sentiment': mention.sentiment_score,
                            'recommendation': mention.recommendation,
                            'context': mention.context_snippets[0] if mention.context_snippets else ""
                        })
            
            if channel_mentions:
                consensus_data['analysts_covering'] += 1
                consensus_data['channels_mentioning'].append(channel.channel_name)
                consensus_data['total_mentions'] += sum(m.mentions_count for m in channel_mentions)
                
                # Add channel quality score
                if channel_id in self.analyst_performance:
                    quality = self.analyst_performance[channel_id].accuracy_rate
                    consensus_data['channel_quality_scores'].append(quality)
        
        # Calculate consensus metrics
        if consensus_data['sentiment_scores']:
            consensus_data['avg_sentiment'] = statistics.mean(consensus_data['sentiment_scores'])
            consensus_data['sentiment_std'] = statistics.stdev(consensus_data['sentiment_scores']) if len(consensus_data['sentiment_scores']) > 1 else 0.0
            consensus_data['sentiment_range'] = [min(consensus_data['sentiment_scores']), max(consensus_data['sentiment_scores'])]
        else:
            consensus_data['avg_sentiment'] = 0.0
            consensus_data['sentiment_std'] = 0.0
            consensus_data['sentiment_range'] = [0.0, 0.0]
        
        # Recommendation consensus
        if consensus_data['recommendations']:
            rec_counts = Counter(consensus_data['recommendations'])
            consensus_data['recommendation_distribution'] = dict(rec_counts)
            consensus_data['primary_recommendation'] = rec_counts.most_common(1)[0][0]
        else:
            consensus_data['recommendation_distribution'] = {}
            consensus_data['primary_recommendation'] = None
        
        # Price target consensus
        if consensus_data['price_targets']:
            consensus_data['avg_price_target'] = statistics.mean(consensus_data['price_targets'])
            consensus_data['price_target_range'] = [min(consensus_data['price_targets']), max(consensus_data['price_targets'])]
            consensus_data['price_target_std'] = statistics.stdev(consensus_data['price_targets']) if len(consensus_data['price_targets']) > 1 else 0.0
        else:
            consensus_data['avg_price_target'] = None
            consensus_data['price_target_range'] = None
            consensus_data['price_target_std'] = 0.0
        
        # Regional consensus
        for region, sentiments in consensus_data['regional_sentiment'].items():
            consensus_data['regional_sentiment'][region] = statistics.mean(sentiments)
        
        # Quality-weighted sentiment
        if consensus_data['channel_quality_scores'] and consensus_data['sentiment_scores']:
            weighted_sentiment = sum(
                sent * quality for sent, quality in 
                zip(consensus_data['sentiment_scores'], consensus_data['channel_quality_scores'])
            ) / sum(consensus_data['channel_quality_scores'])
            consensus_data['quality_weighted_sentiment'] = weighted_sentiment
        else:
            consensus_data['quality_weighted_sentiment'] = consensus_data['avg_sentiment']
        
        # Data freshness
        if consensus_data['latest_mentions']:
            latest_time = max(m['published'] for m in consensus_data['latest_mentions'])
            hours_ago = (datetime.now() - latest_time).total_seconds() / 3600
            consensus_data['data_freshness'] = max(0.0, 1.0 - (hours_ago / 24))  # 1.0 = very fresh, 0.0 = 24h+ old
        else:
            consensus_data['data_freshness'] = 0.0
        
        return dict(consensus_data)
    
    def generate_investment_signal(self, consensus_data: Dict[str, Any]) -> Optional[MarketIntelligenceSignal]:
        """
        Generate investment signal from consensus data
        
        Args:
            consensus_data: Stock consensus analysis
            
        Returns:
            Investment signal or None if insufficient data
        """
        symbol = consensus_data['symbol']
        
        # Check minimum requirements
        if (consensus_data['analysts_covering'] < self.signal_config['min_analysts_for_signal'] or
            consensus_data['total_mentions'] < self.signal_config['min_mentions_for_signal']):
            return None
        
        # Calculate signal components
        sentiment_score = consensus_data['quality_weighted_sentiment']
        data_freshness = consensus_data['data_freshness']
        
        # Determine signal type based on sentiment and recommendations
        signal_type = self._determine_signal_type(consensus_data)
        
        # Calculate confidence
        confidence = self._calculate_signal_confidence(consensus_data)
        
        if confidence < self.signal_config['confidence_threshold']:
            return None
        
        # Calculate signal strength
        signal_strength = self._calculate_signal_strength(consensus_data)
        
        # Geographic consensus
        geographic_consensus = dict(consensus_data['regional_sentiment'])
        
        # Analyst quality score
        avg_analyst_quality = (
            statistics.mean(consensus_data['channel_quality_scores']) 
            if consensus_data['channel_quality_scores'] else 0.5
        )
        
        # Mention frequency trend (simplified - would need historical data for full implementation)
        mention_frequency_trend = "stable"  # TODO: Implement trend analysis
        
        # Generate key insights
        key_insights = self._generate_key_insights(consensus_data)
        
        signal = MarketIntelligenceSignal(
            symbol=symbol,
            company_name=consensus_data.get('company_name', ''),
            signal_type=signal_type,
            confidence=confidence,
            analyst_consensus=consensus_data['recommendation_distribution'],
            sentiment_score=sentiment_score,
            price_target_consensus=consensus_data['avg_price_target'],
            price_target_range=(
                tuple(consensus_data['price_target_range']) 
                if consensus_data['price_target_range'] else None
            ),
            analysts_covering=consensus_data['analysts_covering'],
            total_mentions=consensus_data['total_mentions'],
            mention_frequency_trend=mention_frequency_trend,
            geographic_consensus=geographic_consensus,
            signal_strength=signal_strength,
            data_freshness=data_freshness,
            analyst_quality_score=avg_analyst_quality,
            generated_at=datetime.now(),
            valid_until=datetime.now() + timedelta(hours=self.signal_config['signal_validity_hours']),
            supporting_channels=consensus_data['channels_mentioning'],
            key_insights=key_insights
        )
        
        return signal
    
    def _determine_signal_type(self, consensus_data: Dict[str, Any]) -> str:
        """Determine investment signal type from consensus data"""
        sentiment = consensus_data['quality_weighted_sentiment']
        primary_rec = consensus_data['primary_recommendation']
        
        # Strong signals based on both sentiment and recommendations
        if sentiment >= 0.5 and primary_rec == 'buy':
            return 'strong_buy'
        elif sentiment <= -0.5 and primary_rec == 'sell':
            return 'strong_sell'
        elif sentiment >= self.signal_config['sentiment_threshold_buy']:
            return 'buy'
        elif sentiment <= self.signal_config['sentiment_threshold_sell']:
            return 'sell'
        else:
            return 'hold'
    
    def _calculate_signal_confidence(self, consensus_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the signal"""
        confidence_factors = []
        
        # Analyst agreement (lower std deviation = higher confidence)
        if consensus_data['sentiment_scores']:
            agreement = 1.0 - min(1.0, consensus_data['sentiment_std'])
            confidence_factors.append(agreement * 0.3)
        
        # Number of analysts (more analysts = higher confidence)
        analyst_factor = min(1.0, consensus_data['analysts_covering'] / 10.0)
        confidence_factors.append(analyst_factor * 0.2)
        
        # Data freshness
        confidence_factors.append(consensus_data['data_freshness'] * 0.2)
        
        # Analyst quality
        if consensus_data['channel_quality_scores']:
            avg_quality = statistics.mean(consensus_data['channel_quality_scores'])
            confidence_factors.append(avg_quality * 0.3)
        
        return sum(confidence_factors)
    
    def _calculate_signal_strength(self, consensus_data: Dict[str, Any]) -> float:
        """Calculate overall signal strength"""
        strength_factors = []
        
        # Sentiment magnitude
        sentiment_strength = abs(consensus_data['quality_weighted_sentiment'])
        strength_factors.append(sentiment_strength * 0.4)
        
        # Mention volume
        mention_strength = min(1.0, consensus_data['total_mentions'] / 20.0)
        strength_factors.append(mention_strength * 0.3)
        
        # Recommendation clarity
        if consensus_data['recommendation_distribution']:
            max_rec_count = max(consensus_data['recommendation_distribution'].values())
            total_recs = sum(consensus_data['recommendation_distribution'].values())
            rec_clarity = max_rec_count / total_recs if total_recs > 0 else 0.0
            strength_factors.append(rec_clarity * 0.3)
        
        return sum(strength_factors)
    
    def _generate_key_insights(self, consensus_data: Dict[str, Any]) -> List[str]:
        """Generate key insights from consensus data"""
        insights = []
        
        # Analyst coverage insight
        insights.append(f"{consensus_data['analysts_covering']} analysts covering with {consensus_data['total_mentions']} total mentions")
        
        # Sentiment insight
        sentiment = consensus_data['quality_weighted_sentiment']
        if sentiment > 0.3:
            insights.append(f"Strong positive sentiment ({sentiment:.2f}) across analysts")
        elif sentiment < -0.3:
            insights.append(f"Negative sentiment ({sentiment:.2f}) indicating caution")
        else:
            insights.append(f"Neutral sentiment ({sentiment:.2f}) with mixed views")
        
        # Recommendation insight
        if consensus_data['primary_recommendation']:
            rec_dist = consensus_data['recommendation_distribution']
            total_recs = sum(rec_dist.values())
            primary_pct = rec_dist[consensus_data['primary_recommendation']] / total_recs * 100
            insights.append(f"{primary_pct:.0f}% recommend {consensus_data['primary_recommendation']}")
        
        # Price target insight
        if consensus_data['avg_price_target']:
            insights.append(f"Average price target: ${consensus_data['avg_price_target']:.2f}")
        
        # Regional consensus
        if len(consensus_data['regional_sentiment']) > 1:
            regions = list(consensus_data['regional_sentiment'].keys())
            insights.append(f"Global coverage across {len(regions)} regions")
        
        return insights
    
    def generate_market_overview(self, processed_contents: Dict[str, List[ProcessedContent]]) -> MarketOverview:
        """Generate comprehensive market overview from all processed content"""
        logger.info("Generating market overview from all channels")
        
        # Collect all stock mentions and market insights
        all_mentions = []
        all_market_insights = []
        stock_mention_counts = Counter()
        
        for contents in processed_contents.values():
            for content in contents:
                all_mentions.extend(content.stock_mentions)
                all_market_insights.extend(content.market_insights)
                for mention in content.stock_mentions:
                    stock_mention_counts[mention.symbol] += mention.mentions_count
        
        # Calculate overall market sentiment
        if all_mentions:
            overall_sentiment = statistics.mean([m.sentiment_score for m in all_mentions])
        else:
            overall_sentiment = 0.0
        
        # Calculate sector sentiments (simplified - would need sector mapping)
        sector_sentiments = {}  # TODO: Implement sector mapping
        
        # Find most discussed stocks
        most_discussed = [symbol for symbol, count in stock_mention_counts.most_common(10)]
        
        # Generate signals for top stocks
        top_signals = []
        for symbol in most_discussed[:20]:  # Check top 20 stocks
            consensus = self.build_stock_consensus(processed_contents, symbol)
            signal = self.generate_investment_signal(consensus)
            if signal:
                top_signals.append(signal)
        
        # Separate by signal type
        buy_signals = [s for s in top_signals if s.signal_type in ['buy', 'strong_buy']]
        sell_signals = [s for s in top_signals if s.signal_type in ['sell', 'strong_sell']]
        
        # Sort by confidence
        buy_signals.sort(key=lambda x: x.confidence, reverse=True)
        sell_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        # Extract trending topics
        trending_topics = self._extract_trending_topics(all_market_insights)
        
        # Calculate market uncertainty
        sentiment_std = statistics.stdev([m.sentiment_score for m in all_mentions]) if len(all_mentions) > 1 else 0.0
        market_uncertainty = min(1.0, sentiment_std * 2)  # Normalize to 0-1
        
        # Sentiment momentum (simplified)
        sentiment_momentum = "stable"  # TODO: Implement trend analysis
        
        # Analyst consensus strength
        if all_mentions:
            # Calculate how much analysts agree
            symbol_sentiments = defaultdict(list)
            for mention in all_mentions:
                symbol_sentiments[mention.symbol].append(mention.sentiment_score)
            
            agreement_scores = []
            for sentiments in symbol_sentiments.values():
                if len(sentiments) > 1:
                    std = statistics.stdev(sentiments)
                    agreement = 1.0 - min(1.0, std)
                    agreement_scores.append(agreement)
            
            consensus_strength = statistics.mean(agreement_scores) if agreement_scores else 0.5
        else:
            consensus_strength = 0.0
        
        overview = MarketOverview(
            timestamp=datetime.now(),
            overall_market_sentiment=overall_sentiment,
            sector_sentiments=sector_sentiments,
            sentiment_momentum=sentiment_momentum,
            top_buy_signals=buy_signals[:5],
            top_sell_signals=sell_signals[:5],
            emerging_opportunities=buy_signals[5:10] if len(buy_signals) > 5 else [],
            trending_topics=trending_topics,
            most_discussed_stocks=most_discussed[:10],
            analyst_consensus_strength=consensus_strength,
            market_uncertainty=market_uncertainty,
            volatility_expectations="moderate",  # TODO: Implement volatility analysis
            risk_sentiment=overall_sentiment  # Simplified - negative sentiment = higher risk
        )
        
        return overview
    
    def _extract_trending_topics(self, market_insights: List[MarketInsight]) -> List[str]:
        """Extract trending topics from market insights"""
        topic_counts = Counter()
        
        for insight in market_insights:
            topic_counts[insight.topic] += 1
            # Also count key words from key points
            for point in insight.key_points:
                words = point.lower().split()
                for word in words:
                    if len(word) > 4 and word not in ['stock', 'market', 'price', 'trading']:
                        topic_counts[word] += 1
        
        return [topic for topic, count in topic_counts.most_common(10)]
    
    def run_full_intelligence_cycle(self, days_back: int = 1) -> Dict[str, Any]:
        """
        Run complete intelligence cycle: process channels, generate signals, create overview
        
        Args:
            days_back: Days to look back for content
            
        Returns:
            Complete intelligence report
        """
        logger.info(f"Running full intelligence cycle ({days_back} days)")
        start_time = datetime.now()
        
        # Process all channels
        processed_contents = self.process_channel_batch(days_back)
        
        # Generate signals for all mentioned stocks
        signals = {}
        stock_symbols = set()
        
        # Collect all mentioned stocks
        for contents in processed_contents.values():
            for content in contents:
                for mention in content.stock_mentions:
                    stock_symbols.add(mention.symbol)
        
        logger.info(f"Generating signals for {len(stock_symbols)} stocks")
        
        # Generate signal for each stock
        for symbol in stock_symbols:
            consensus = self.build_stock_consensus(processed_contents, symbol)
            signal = self.generate_investment_signal(consensus)
            if signal:
                signals[symbol] = signal
        
        # Generate market overview
        market_overview = self.generate_market_overview(processed_contents)
        
        # Compile full report
        intelligence_report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'processing_time_seconds': (datetime.now() - start_time).total_seconds(),
                'days_analyzed': days_back,
                'channels_processed': len(processed_contents),
                'total_videos': sum(len(contents) for contents in processed_contents.values()),
                'stocks_analyzed': len(stock_symbols),
                'signals_generated': len(signals)
            },
            'market_overview': asdict(market_overview),
            'investment_signals': {symbol: asdict(signal) for symbol, signal in signals.items()},
            'analyst_performance': {
                ch_id: asdict(perf) for ch_id, perf in self.analyst_performance.items()
                if perf.videos_processed > 0
            },
            'raw_data': {
                'processed_contents_summary': {
                    ch_id: len(contents) for ch_id, contents in processed_contents.items()
                }
            }
        }
        
        logger.info(f"Intelligence cycle completed in {intelligence_report['metadata']['processing_time_seconds']:.1f}s")
        logger.info(f"Generated {len(signals)} investment signals from {len(stock_symbols)} stocks")
        
        return intelligence_report

# Convenience function for easy import
def get_market_intelligence() -> YouTubeMarketIntelligence:
    """Get configured YouTube market intelligence engine instance"""
    return YouTubeMarketIntelligence()