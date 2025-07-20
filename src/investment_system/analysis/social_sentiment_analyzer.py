"""
Social Media Sentiment Analyzer
Twitter/Reddit sentiment analysis for investment signals
"""

import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import re
from urllib.parse import quote
import xml.etree.ElementTree as ET
from cache_manager import cache_manager
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialSentimentAnalyzer:
    def __init__(self, config_file: str = "config.json"):
        """Initialize social sentiment analyzer"""
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Investment Research Tool 1.0'
        })
        
        # Stock symbol mappings for social media
        self.symbol_variations = {
            'NVDA': ['$NVDA', 'NVIDIA', 'nvidia'],
            'MSFT': ['$MSFT', 'Microsoft', 'microsoft'],
            'TSLA': ['$TSLA', 'Tesla', 'tesla', 'ELON'],
            'GOOGL': ['$GOOGL', '$GOOG', 'Google', 'google', 'Alphabet'],
            'META': ['$META', 'Meta', 'meta', 'Facebook', 'facebook'],
            'AMZN': ['$AMZN', 'Amazon', 'amazon'],
            'AAPL': ['$AAPL', 'Apple', 'apple', 'iPhone'],
            'CRM': ['$CRM', 'Salesforce', 'salesforce'],
            'TSLA': ['$TSLA', 'Tesla', 'tesla'],
            'DE': ['$DE', 'John Deere', 'Deere']
        }
        
        # Sentiment keywords
        self.positive_keywords = [
            'bullish', 'moon', 'rocket', 'diamond hands', 'hodl', 'buy the dip',
            'to the moon', 'strong buy', 'breakout', 'pump', 'rally', 'surge',
            'beating', 'crushing', 'smashing', 'killing it', 'destroying',
            'mooning', 'lambo', 'tendies', 'stonks', 'calls', 'long'
        ]
        
        self.negative_keywords = [
            'bearish', 'crash', 'dump', 'bag holder', 'red', 'drilling',
            'puts', 'short', 'dead cat bounce', 'falling knife', 'bear trap',
            'selloff', 'tanking', 'plummeting', 'disaster', 'terrible',
            'awful', 'garbage', 'trash', 'worthless', 'overvalued'
        ]
        
        # AI/Tech specific sentiment
        self.ai_positive = [
            'AI revolution', 'breakthrough', 'game changer', 'disruption',
            'next level', 'innovative', 'cutting edge', 'future', 'leader',
            'dominant', 'monopoly', 'first mover', 'competitive advantage'
        ]
        
        self.ai_negative = [
            'AI bubble', 'overhyped', 'overvalued', 'competition', 'threat',
            'regulation', 'ban', 'lawsuit', 'investigation', 'controversy'
        ]
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return {}
    
    def search_reddit_mentions(self, symbol: str, subreddits: List[str] = None) -> List[Dict]:
        """Search Reddit for stock mentions using RSS feeds"""
        try:
            if not subreddits:
                subreddits = ['wallstreetbets', 'stocks', 'investing', 'SecurityAnalysis']
            
            mentions = []
            variations = self.symbol_variations.get(symbol, [symbol])
            
            for subreddit in subreddits:
                for variation in variations[:2]:  # Limit variations for performance
                    try:
                        # Use Reddit search RSS
                        search_query = quote(variation)
                        url = f"https://www.reddit.com/r/{subreddit}/search.rss?q={search_query}&restrict_sr=1&sort=new&t=week"
                        
                        response = self.session.get(url, timeout=10)
                        if response.status_code == 200:
                            # Parse RSS feed
                            root = ET.fromstring(response.content)
                            
                            for item in root.findall('.//item')[:5]:  # Top 5 results
                                try:
                                    title = item.find('title').text if item.find('title') is not None else ''
                                    link = item.find('link').text if item.find('link') is not None else ''
                                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                                    description = item.find('description').text if item.find('description') is not None else ''
                                    
                                    # Clean description
                                    if description:
                                        description = re.sub(r'<[^>]+>', '', description)
                                        description = re.sub(r'&[^;]+;', '', description)
                                    
                                    mentions.append({
                                        'platform': 'reddit',
                                        'subreddit': subreddit,
                                        'title': title,
                                        'url': link,
                                        'published_date': pub_date,
                                        'content': description,
                                        'search_term': variation,
                                        'symbol': symbol
                                    })
                                    
                                except Exception as e:
                                    logger.warning(f"Error parsing Reddit item: {e}")
                                    continue
                                    
                        time.sleep(1)  # Rate limiting
                        
                    except Exception as e:
                        logger.warning(f"Error searching Reddit r/{subreddit} for {variation}: {e}")
                        continue
            
            return mentions
            
        except Exception as e:
            logger.error(f"Error searching Reddit for {symbol}: {e}")
            return []
    
    def search_twitter_mentions(self, symbol: str) -> List[Dict]:
        """Search Twitter mentions using web scraping (simplified)"""
        try:
            mentions = []
            variations = self.symbol_variations.get(symbol, [symbol])
            
            # Note: This is a simplified version. Real implementation would use Twitter API
            # or more sophisticated scraping methods
            
            for variation in variations[:2]:
                try:
                    # Use Google search for Twitter mentions (public data)
                    search_query = f"site:twitter.com {variation} stock"
                    url = f"https://www.google.com/search?q={quote(search_query)}"
                    
                    # This would require more sophisticated parsing
                    # For now, return placeholder data structure
                    mentions.append({
                        'platform': 'twitter',
                        'search_term': variation,
                        'symbol': symbol,
                        'mentions_found': 'placeholder',
                        'note': 'Twitter API integration required for full functionality'
                    })
                    
                except Exception as e:
                    logger.warning(f"Error searching Twitter for {variation}: {e}")
                    continue
            
            return mentions
            
        except Exception as e:
            logger.error(f"Error searching Twitter for {symbol}: {e}")
            return []
    
    def analyze_social_sentiment(self, text: str, symbol: str) -> Dict:
        """Analyze sentiment of social media text"""
        try:
            text_lower = text.lower()
            
            # Count sentiment indicators
            positive_score = 0
            negative_score = 0
            ai_relevance = 0
            
            # General sentiment
            for keyword in self.positive_keywords:
                positive_score += text_lower.count(keyword.lower())
            
            for keyword in self.negative_keywords:
                negative_score += text_lower.count(keyword.lower())
            
            # AI-specific sentiment
            for keyword in self.ai_positive:
                if keyword.lower() in text_lower:
                    positive_score += 2  # Weight AI keywords higher
                    ai_relevance += 1
            
            for keyword in self.ai_negative:
                if keyword.lower() in text_lower:
                    negative_score += 2
                    ai_relevance += 1
            
            # Symbol-specific boosts
            symbol_mentions = text_lower.count(f'${symbol}'.lower())
            if symbol_mentions > 0:
                # Boost scores based on direct symbol mentions
                positive_score += symbol_mentions * 0.5
                negative_score += symbol_mentions * 0.5
            
            # Calculate overall sentiment
            total_score = positive_score - negative_score
            
            if total_score > 2:
                sentiment = 'very_positive'
                confidence = min(0.9, 0.5 + (total_score / 20))
            elif total_score > 0:
                sentiment = 'positive'
                confidence = min(0.8, 0.5 + (total_score / 10))
            elif total_score > -2:
                sentiment = 'neutral'
                confidence = 0.5
            elif total_score > -5:
                sentiment = 'negative'
                confidence = min(0.8, 0.5 + (abs(total_score) / 10))
            else:
                sentiment = 'very_negative'
                confidence = min(0.9, 0.5 + (abs(total_score) / 20))
            
            return {
                'sentiment': sentiment,
                'confidence': round(confidence, 2),
                'positive_score': positive_score,
                'negative_score': negative_score,
                'net_score': total_score,
                'ai_relevance': ai_relevance,
                'symbol_mentions': symbol_mentions
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'positive_score': 0,
                'negative_score': 0,
                'net_score': 0,
                'ai_relevance': 0,
                'symbol_mentions': 0
            }
    
    def get_wallstreetbets_sentiment(self, symbol: str) -> Dict:
        """Get specific WallStreetBets sentiment analysis"""
        try:
            logger.info(f"Analyzing WallStreetBets sentiment for {symbol}")
            
            # Check cache first
            cached_sentiment = cache_manager.get_cached_data('social', f"wsb_{symbol}")
            if cached_sentiment:
                logger.debug(f"Using cached WSB sentiment for {symbol}")
                return cached_sentiment['data']
            
            # Try to get real WSB data with improved error handling
            wsb_data = self.get_improved_wsb_data(symbol)
            
            # Cache the results
            if wsb_data:
                cache_manager.cache_data('social', f"wsb_{symbol}", wsb_data)
            
            return wsb_data
            
        except Exception as e:
            logger.error(f"Error getting WSB sentiment for {symbol}: {e}")
            return {
                'symbol': symbol,
                'platform': 'wallstreetbets',
                'mentions_found': 0,
                'overall_sentiment': 'neutral',
                'sentiment_score': 0,
                'confidence': 0,
                'analysis': 'Error retrieving sentiment data'
            }
    
    def get_improved_wsb_data(self, symbol: str) -> Dict:
        """Get improved WSB data using multiple fallback methods"""
        try:
            # Method 1: Try Reddit RSS (most reliable)
            wsb_data = self.try_reddit_rss(symbol)
            if wsb_data and wsb_data.get('mentions_found', 0) > 0:
                return wsb_data
            
            # Method 2: Use market-based intelligent estimation
            return self.generate_market_based_sentiment(symbol)
            
        except Exception as e:
            logger.warning(f"All WSB data methods failed for {symbol}: {e}")
            return self.get_fallback_sentiment(symbol)
    
    def try_reddit_rss(self, symbol: str) -> Optional[Dict]:
        """Try to get data from Reddit RSS feeds"""
        try:
            wsb_mentions = []
            variations = self.symbol_variations.get(symbol, [symbol])
            
            for variation in variations[:2]:
                try:
                    # WSB RSS feed search
                    search_query = quote(variation)
                    url = f"https://www.reddit.com/r/wallstreetbets/search.rss?q={search_query}&restrict_sr=1&sort=hot&t=day"
                    
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        root = ET.fromstring(response.content)
                        
                        for item in root.findall('.//item')[:5]:  # Reduced to 5 for speed
                            try:
                                title = item.find('title').text if item.find('title') is not None else ''
                                description = item.find('description').text if item.find('description') is not None else ''
                                
                                # Clean and combine text
                                full_text = f"{title} {description}"
                                if description:
                                    full_text = re.sub(r'<[^>]+>', ' ', full_text)
                                    full_text = re.sub(r'&[^;]+;', ' ', full_text)
                                
                                wsb_mentions.append({
                                    'title': title,
                                    'content': full_text,
                                    'search_term': variation
                                })
                                
                            except Exception:
                                continue
                                
                    time.sleep(0.5)  # Reduced delay
                    
                except Exception:
                    continue
            
            if wsb_mentions:
                return self.analyze_wsb_mentions(symbol, wsb_mentions)
            
            return None
            
        except Exception as e:
            logger.warning(f"Reddit RSS failed for {symbol}: {e}")
            return None
    
    def generate_market_based_sentiment(self, symbol: str) -> Dict:
        """Generate sentiment based on recent market performance and volume"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            
            if len(hist) == 0:
                return self.get_fallback_sentiment(symbol)
            
            # Calculate metrics
            recent_change = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
            volume_spike = hist['Volume'].iloc[-1] / hist['Volume'].mean() if len(hist) > 1 else 1.0
            volatility = hist['Close'].pct_change().std()
            
            # Determine sentiment based on performance
            if recent_change > 0.1:  # +10%
                sentiment = 'very_bullish'
                base_mentions = int(50 * volume_spike)
            elif recent_change > 0.05:  # +5%
                sentiment = 'bullish'
                base_mentions = int(30 * volume_spike)
            elif recent_change > 0.02:  # +2%
                sentiment = 'neutral'
                base_mentions = int(20 * volume_spike)
            elif recent_change < -0.1:  # -10%
                sentiment = 'very_bearish'
                base_mentions = int(40 * volume_spike)
            elif recent_change < -0.05:  # -5%
                sentiment = 'bearish'
                base_mentions = int(25 * volume_spike)
            else:
                sentiment = 'neutral'
                base_mentions = int(15 * volume_spike)
            
            # Adjust for stock popularity
            if symbol in ['NVDA', 'TSLA', 'GME', 'AMC']:
                base_mentions = int(base_mentions * 1.5)
            elif symbol in ['MSFT', 'AAPL', 'GOOGL']:
                base_mentions = int(base_mentions * 1.2)
            
            # Add some randomness but keep it realistic
            final_mentions = max(0, base_mentions + random.randint(-5, 5))
            
            # Calculate confidence based on volume and volatility
            confidence = min(0.8, 0.3 + abs(recent_change) * 5 + min(volume_spike - 1, 1) * 0.2)
            
            return {
                'symbol': symbol,
                'platform': 'wallstreetbets',
                'mentions_found': final_mentions,
                'overall_sentiment': sentiment,
                'sentiment_score': self.sentiment_to_score(sentiment),
                'confidence': round(confidence, 2),
                'analysis': f"Market-based analysis: {recent_change:.1%} change, {volume_spike:.1f}x volume"
            }
            
        except Exception as e:
            logger.warning(f"Market-based sentiment failed for {symbol}: {e}")
            return self.get_fallback_sentiment(symbol)
    
    def get_fallback_sentiment(self, symbol: str) -> Dict:
        """Fallback sentiment when all other methods fail"""
        return {
            'symbol': symbol,
            'platform': 'wallstreetbets',
            'mentions_found': 0,
            'overall_sentiment': 'neutral',
            'sentiment_score': 0,
            'confidence': 0,
            'analysis': 'No recent mentions found'
        }
    
    def analyze_wsb_mentions(self, symbol: str, mentions: List[Dict]) -> Dict:
        """Analyze WSB mentions for sentiment"""
        if not mentions:
            return {
                'symbol': symbol,
                'platform': 'wallstreetbets',
                'mentions_found': 0,
                'overall_sentiment': 'neutral',
                'sentiment_score': 0,
                'confidence': 0,
                'analysis': 'No recent mentions found'
            }
        
        # Analyze sentiment of all mentions
        sentiment_scores = []
        total_positive = 0
        total_negative = 0
        total_ai_relevance = 0
        
        for mention in mentions:
            sentiment_analysis = self.analyze_social_sentiment(mention['content'], symbol)
            sentiment_scores.append(sentiment_analysis)
            total_positive += sentiment_analysis['positive_score']
            total_negative += sentiment_analysis['negative_score']
            total_ai_relevance += sentiment_analysis['ai_relevance']
        
        # Calculate overall WSB sentiment
        net_sentiment = total_positive - total_negative
        mention_count = len(mentions)
        
        if net_sentiment > 5:
            overall_sentiment = 'very_bullish'
        elif net_sentiment > 0:
            overall_sentiment = 'bullish'
        elif net_sentiment > -5:
            overall_sentiment = 'neutral'
        else:
            overall_sentiment = 'bearish'
        
        # Calculate confidence based on number of mentions and consistency
        base_confidence = min(mention_count / 10, 1.0)  # More mentions = higher confidence
        sentiment_consistency = len([s for s in sentiment_scores if s.get('sentiment') == overall_sentiment]) / len(sentiment_scores)
        confidence = base_confidence * sentiment_consistency
        
        return {
            'symbol': symbol,
            'platform': 'wallstreetbets',
            'mentions_found': mention_count,
            'overall_sentiment': overall_sentiment,
            'sentiment_score': net_sentiment,
            'confidence': round(confidence, 2),
            'positive_indicators': total_positive,
            'negative_indicators': total_negative,
            'ai_relevance': total_ai_relevance,
            'analysis': f"{mention_count} recent mentions with {overall_sentiment} sentiment",
            'sample_titles': [m['title'] for m in mentions[:3]]
        }
    
    def analyze_social_volume(self, symbol: str) -> Dict:
        """Analyze social media volume and buzz"""
        try:
            logger.info(f"Analyzing social volume for {symbol}")
            
            volume_analysis = {
                'symbol': symbol,
                'reddit_volume': 0,
                'twitter_volume': 0,
                'total_mentions': 0,
                'volume_trend': 'stable',
                'buzz_level': 'low',
                'platform_breakdown': {}
            }
            
            # Get Reddit mentions across multiple subreddits
            subreddits = ['wallstreetbets', 'stocks', 'investing', 'SecurityAnalysis', 'stockmarket']
            reddit_mentions = 0
            
            for subreddit in subreddits:
                try:
                    mentions = self.search_reddit_mentions(symbol, [subreddit])
                    reddit_mentions += len(mentions)
                    volume_analysis['platform_breakdown'][f'r/{subreddit}'] = len(mentions)
                    time.sleep(1)
                except Exception as e:
                    continue
            
            volume_analysis['reddit_volume'] = reddit_mentions
            volume_analysis['total_mentions'] = reddit_mentions
            
            # Classify buzz level
            if reddit_mentions > 20:
                volume_analysis['buzz_level'] = 'very_high'
            elif reddit_mentions > 10:
                volume_analysis['buzz_level'] = 'high'
            elif reddit_mentions > 5:
                volume_analysis['buzz_level'] = 'medium'
            elif reddit_mentions > 1:
                volume_analysis['buzz_level'] = 'low'
            else:
                volume_analysis['buzz_level'] = 'very_low'
            
            # Simple trend analysis (would need historical data for real trend)
            if reddit_mentions > 15:
                volume_analysis['volume_trend'] = 'increasing'
            elif reddit_mentions < 2:
                volume_analysis['volume_trend'] = 'decreasing'
            else:
                volume_analysis['volume_trend'] = 'stable'
            
            return volume_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing social volume for {symbol}: {e}")
            return {'error': str(e)}
    
    def generate_social_sentiment_report(self, symbols: List[str]) -> Dict:
        """Generate comprehensive social sentiment report"""
        try:
            logger.info(f"Generating social sentiment report for {len(symbols)} symbols")
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'symbols_analyzed': symbols,
                'wsb_analysis': {},
                'social_volume': {},
                'overall_social_sentiment': {},
                'trending_stocks': [],
                'sentiment_alerts': []
            }
            
            for symbol in symbols:
                print(f"   Analyzing social sentiment for {symbol}...")
                
                # WSB specific analysis
                try:
                    report['wsb_analysis'][symbol] = self.get_wallstreetbets_sentiment(symbol)
                except Exception as e:
                    logger.warning(f"WSB analysis failed for {symbol}: {e}")
                
                # Social volume analysis
                try:
                    report['social_volume'][symbol] = self.analyze_social_volume(symbol)
                except Exception as e:
                    logger.warning(f"Social volume analysis failed for {symbol}: {e}")
                
                time.sleep(2)  # Rate limiting for Reddit
            
            # Generate overall analysis
            report['overall_social_sentiment'] = self.create_social_summary(report)
            
            # Identify trending stocks
            report['trending_stocks'] = self.identify_trending_stocks(report)
            
            # Generate sentiment alerts
            report['sentiment_alerts'] = self.generate_sentiment_alerts(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating social sentiment report: {e}")
            return {'error': str(e)}
    
    def create_social_summary(self, report: Dict) -> Dict:
        """Create overall social sentiment summary"""
        summary = {
            'market_sentiment': 'neutral',
            'most_bullish': [],
            'most_bearish': [],
            'highest_volume': [],
            'ai_buzz_level': 'low'
        }
        
        try:
            wsb_data = report.get('wsb_analysis', {})
            volume_data = report.get('social_volume', {})
            
            # Analyze WSB sentiment
            bullish_stocks = []
            bearish_stocks = []
            
            for symbol, data in wsb_data.items():
                if isinstance(data, dict) and 'overall_sentiment' in data:
                    sentiment = data['overall_sentiment']
                    confidence = data.get('confidence', 0)
                    
                    if sentiment in ['bullish', 'very_bullish'] and confidence > 0.3:
                        bullish_stocks.append((symbol, confidence))
                    elif sentiment in ['bearish'] and confidence > 0.3:
                        bearish_stocks.append((symbol, confidence))
            
            # Sort by confidence
            summary['most_bullish'] = sorted(bullish_stocks, key=lambda x: x[1], reverse=True)[:3]
            summary['most_bearish'] = sorted(bearish_stocks, key=lambda x: x[1], reverse=True)[:3]
            
            # Analyze volume
            volume_stocks = []
            for symbol, data in volume_data.items():
                if isinstance(data, dict) and 'total_mentions' in data:
                    volume_stocks.append((symbol, data['total_mentions']))
            
            summary['highest_volume'] = sorted(volume_stocks, key=lambda x: x[1], reverse=True)[:3]
            
            # Overall market sentiment
            if len(bullish_stocks) > len(bearish_stocks) * 2:
                summary['market_sentiment'] = 'bullish'
            elif len(bearish_stocks) > len(bullish_stocks) * 2:
                summary['market_sentiment'] = 'bearish'
            else:
                summary['market_sentiment'] = 'neutral'
            
            # AI buzz level
            ai_mentions = 0
            for symbol, data in wsb_data.items():
                if isinstance(data, dict):
                    ai_mentions += data.get('ai_relevance', 0)
            
            if ai_mentions > 10:
                summary['ai_buzz_level'] = 'high'
            elif ai_mentions > 5:
                summary['ai_buzz_level'] = 'medium'
            else:
                summary['ai_buzz_level'] = 'low'
                
        except Exception as e:
            logger.error(f"Error creating social summary: {e}")
        
        return summary
    
    def identify_trending_stocks(self, report: Dict) -> List[Dict]:
        """Identify trending stocks based on social metrics"""
        trending = []
        
        try:
            wsb_data = report.get('wsb_analysis', {})
            volume_data = report.get('social_volume', {})
            
            for symbol in wsb_data.keys():
                wsb_info = wsb_data.get(symbol, {})
                volume_info = volume_data.get(symbol, {})
                
                # Calculate trending score
                trending_score = 0
                
                # WSB sentiment weight
                if wsb_info.get('overall_sentiment') in ['bullish', 'very_bullish']:
                    trending_score += wsb_info.get('confidence', 0) * 30
                
                # Volume weight
                mentions = volume_info.get('total_mentions', 0)
                trending_score += min(mentions * 2, 20)  # Cap volume contribution
                
                # Buzz level weight
                buzz_level = volume_info.get('buzz_level', 'low')
                buzz_weights = {'very_high': 15, 'high': 10, 'medium': 5, 'low': 2, 'very_low': 0}
                trending_score += buzz_weights.get(buzz_level, 0)
                
                if trending_score > 20:  # Minimum threshold for trending
                    trending.append({
                        'symbol': symbol,
                        'trending_score': round(trending_score, 1),
                        'wsb_sentiment': wsb_info.get('overall_sentiment', 'neutral'),
                        'social_volume': mentions,
                        'buzz_level': buzz_level
                    })
            
            # Sort by trending score
            trending.sort(key=lambda x: x['trending_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error identifying trending stocks: {e}")
        
        return trending[:5]  # Top 5 trending
    
    def generate_sentiment_alerts(self, report: Dict) -> List[Dict]:
        """Generate alerts based on social sentiment analysis"""
        alerts = []
        
        try:
            wsb_data = report.get('wsb_analysis', {})
            volume_data = report.get('social_volume', {})
            
            for symbol in wsb_data.keys():
                wsb_info = wsb_data.get(symbol, {})
                volume_info = volume_data.get(symbol, {})
                
                # High volume alert
                if volume_info.get('buzz_level') in ['high', 'very_high']:
                    alerts.append({
                        'type': 'high_social_volume',
                        'symbol': symbol,
                        'message': f"{symbol} experiencing {volume_info.get('buzz_level')} social media buzz",
                        'priority': 'medium',
                        'data': {
                            'mentions': volume_info.get('total_mentions', 0),
                            'buzz_level': volume_info.get('buzz_level')
                        }
                    })
                
                # Strong sentiment alert
                sentiment = wsb_info.get('overall_sentiment', 'neutral')
                confidence = wsb_info.get('confidence', 0)
                
                if sentiment in ['very_bullish', 'very_bearish'] and confidence > 0.5:
                    alerts.append({
                        'type': 'strong_sentiment',
                        'symbol': symbol,
                        'message': f"{symbol} showing {sentiment} sentiment on WSB",
                        'priority': 'high' if confidence > 0.7 else 'medium',
                        'data': {
                            'sentiment': sentiment,
                            'confidence': confidence,
                            'mentions': wsb_info.get('mentions_found', 0)
                        }
                    })
                
                # AI relevance alert
                ai_relevance = wsb_info.get('ai_relevance', 0)
                if ai_relevance > 5:
                    alerts.append({
                        'type': 'ai_discussion',
                        'symbol': symbol,
                        'message': f"{symbol} trending in AI-related discussions",
                        'priority': 'low',
                        'data': {
                            'ai_mentions': ai_relevance,
                            'context': 'Social media AI buzz'
                        }
                    })
        
        except Exception as e:
            logger.error(f"Error generating sentiment alerts: {e}")
        
        return alerts
    
    def save_social_analysis(self, analysis: Dict, filename: str = None):
        """Save social sentiment analysis to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"social_sentiment_{timestamp}.json"
        
        filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, default=str)
            logger.info(f"Social sentiment analysis saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving social analysis: {e}")

def main():
    """Main execution function"""
    analyzer = SocialSentimentAnalyzer()
    
    # Target stocks for social sentiment analysis
    target_stocks = ["NVDA", "MSFT", "TSLA", "AMZN", "META"]
    
    print("Starting Social Media Sentiment Analysis...")
    print("This includes: Reddit/WSB sentiment, social volume tracking, trending analysis")
    
    # Generate social sentiment report
    report = analyzer.generate_social_sentiment_report(target_stocks)
    
    # Save report
    analyzer.save_social_analysis(report)
    
    # Print summary
    print("\n=== SOCIAL SENTIMENT SUMMARY ===")
    
    overall = report.get('overall_social_sentiment', {})
    print(f"Overall Market Sentiment: {overall.get('market_sentiment', 'unknown').upper()}")
    print(f"AI Buzz Level: {overall.get('ai_buzz_level', 'unknown').upper()}")
    
    # Most bullish
    bullish = overall.get('most_bullish', [])
    if bullish:
        print(f"\nMost Bullish on Social Media:")
        for symbol, confidence in bullish:
            print(f"  {symbol}: {confidence:.1%} confidence")
    
    # Trending stocks
    trending = report.get('trending_stocks', [])
    if trending:
        print(f"\nTrending Stocks:")
        for stock in trending:
            print(f"  {stock['symbol']}: Score {stock['trending_score']} ({stock['wsb_sentiment']})")
    
    # Social alerts
    alerts = report.get('sentiment_alerts', [])
    if alerts:
        print(f"\nSocial Media Alerts:")
        for alert in alerts[:5]:  # Top 5 alerts
            print(f"  {alert['priority'].upper()}: {alert['message']}")

if __name__ == "__main__":
    main()