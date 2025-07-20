"""
News Sentiment Analyzer
Searches and analyzes news for target stocks and companies
"""

import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import re
from urllib.parse import quote
import concurrent.futures
from cache_manager import cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsSentimentAnalyzer:
    def __init__(self, config_file: str = "config.json"):
        """Initialize news sentiment analyzer"""
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Investment Research Tool 1.0'
        })
        
        # Company name mappings for better news search
        self.company_mappings = {
            'NVDA': ['NVIDIA', 'NVIDIA Corporation', 'Jensen Huang'],
            'MSFT': ['Microsoft', 'Microsoft Corporation', 'Satya Nadella'],
            'TSLA': ['Tesla', 'Tesla Inc', 'Elon Musk'],
            'GOOGL': ['Google', 'Alphabet', 'Alphabet Inc', 'Sundar Pichai'],
            'META': ['Meta', 'Facebook', 'Meta Platforms', 'Mark Zuckerberg'],
            'AMZN': ['Amazon', 'Amazon.com', 'Jeff Bezos', 'Andy Jassy'],
            'AAPL': ['Apple', 'Apple Inc', 'Tim Cook'],
            'CRM': ['Salesforce', 'Salesforce.com', 'Marc Benioff'],
            'DE': ['John Deere', 'Deere & Company', 'Deere Company'],
            'TSM': ['Taiwan Semiconductor', 'TSMC', 'Taiwan Semi'],
            'AMD': ['AMD', 'Advanced Micro Devices'],
            'INTC': ['Intel', 'Intel Corporation'],
            'QCOM': ['Qualcomm', 'Qualcomm Inc'],
            'PLTR': ['Palantir', 'Palantir Technologies'],
            'SNOW': ['Snowflake', 'Snowflake Inc']
        }
        
        # AI/Tech keywords for relevance scoring
        self.ai_keywords = [
            'artificial intelligence', 'AI', 'machine learning', 'ML',
            'neural network', 'deep learning', 'automation', 'robotics',
            'autonomous', 'computer vision', 'natural language',
            'chatgpt', 'generative ai', 'llm', 'algorithm', 'data science'
        ]
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return {}
    
    def search_google_news(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search Google News for a query"""
        try:
            # Use Google News RSS feed (free, no API key required)
            encoded_query = quote(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Google News search failed for {query}: {response.status_code}")
                return []
            
            # Parse RSS feed
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            articles = []
            for item in root.findall('.//item')[:max_results]:
                try:
                    title = item.find('title').text if item.find('title') is not None else ''
                    link = item.find('link').text if item.find('link') is not None else ''
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                    description = item.find('description').text if item.find('description') is not None else ''
                    
                    # Clean up description (remove HTML tags)
                    if description:
                        description = re.sub(r'<[^>]+>', '', description)
                    
                    articles.append({
                        'title': title,
                        'url': link,
                        'published_date': pub_date,
                        'description': description,
                        'source': 'Google News',
                        'query': query
                    })
                except Exception as e:
                    logger.warning(f"Error parsing news item: {e}")
                    continue
                    
            return articles
            
        except Exception as e:
            logger.error(f"Error searching Google News for {query}: {e}")
            return []
    
    def search_bing_news(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search Bing News (backup method)"""
        try:
            # Bing News search (no API key version)
            url = f"https://www.bing.com/news/search"
            params = {
                'q': query,
                'format': 'rss',
                'count': max_results
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return []
            
            # Parse RSS if available
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                articles = []
                for item in root.findall('.//item')[:max_results]:
                    title = item.find('title').text if item.find('title') is not None else ''
                    link = item.find('link').text if item.find('link') is not None else ''
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                    description = item.find('description').text if item.find('description') is not None else ''
                    
                    articles.append({
                        'title': title,
                        'url': link,
                        'published_date': pub_date,
                        'description': description,
                        'source': 'Bing News',
                        'query': query
                    })
                    
                return articles
            except:
                return []
                
        except Exception as e:
            logger.error(f"Error searching Bing News for {query}: {e}")
            return []
    
    def fetch_article_content(self, url: str) -> str:
        """Fetch full article content using MCP browser tools"""
        try:
            # Try to get article content
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                # Basic text extraction (could be enhanced with MCP tools)
                content = response.text
                
                # Simple text extraction from HTML
                import re
                # Remove script and style elements
                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
                # Remove HTML tags
                content = re.sub(r'<[^>]+>', ' ', content)
                # Clean up whitespace
                content = re.sub(r'\s+', ' ', content).strip()
                
                # Return first 1000 characters
                return content[:1000]
            else:
                return ""
                
        except Exception as e:
            logger.warning(f"Could not fetch content from {url}: {e}")
            return ""
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of news text"""
        try:
            text_lower = text.lower()
            
            # Positive indicators
            positive_words = [
                'beat', 'exceeds', 'strong', 'growth', 'up', 'gain', 'rise', 'surge',
                'breakthrough', 'success', 'win', 'partnership', 'deal', 'expansion',
                'innovation', 'launch', 'positive', 'bullish', 'outperform', 'upgrade',
                'revenue', 'profit', 'earnings beat', 'milestone', 'record'
            ]
            
            # Negative indicators
            negative_words = [
                'decline', 'fall', 'drop', 'loss', 'weak', 'miss', 'disappointing',
                'concern', 'risk', 'problem', 'issue', 'lawsuit', 'investigation',
                'downgrade', 'bearish', 'underperform', 'cut', 'reduce', 'layoff',
                'challenge', 'struggle', 'warning', 'caution'
            ]
            
            # AI/Tech specific positive indicators
            ai_positive = [
                'ai breakthrough', 'artificial intelligence', 'machine learning advance',
                'automation', 'robotics', 'innovation', 'technology leadership',
                'digital transformation', 'cloud growth', 'ai adoption'
            ]
            
            # Count sentiment indicators
            positive_score = sum(1 for word in positive_words if word in text_lower)
            negative_score = sum(1 for word in negative_words if word in text_lower)
            ai_relevance = sum(1 for phrase in ai_positive if phrase in text_lower)
            
            # Calculate overall sentiment
            if positive_score > negative_score:
                sentiment = 'positive'
                confidence = min((positive_score - negative_score) / 10, 1.0)
            elif negative_score > positive_score:
                sentiment = 'negative'
                confidence = min((negative_score - positive_score) / 10, 1.0)
            else:
                sentiment = 'neutral'
                confidence = 0.5
            
            # Boost confidence for AI-relevant news
            if ai_relevance > 0:
                confidence = min(confidence + 0.2, 1.0)
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'positive_indicators': positive_score,
                'negative_indicators': negative_score,
                'ai_relevance': ai_relevance,
                'score': (positive_score - negative_score) + ai_relevance
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'positive_indicators': 0,
                'negative_indicators': 0,
                'ai_relevance': 0,
                'score': 0
            }
    
    def search_stock_news(self, symbol: str, max_articles: int = 15) -> List[Dict]:
        """Search news for a specific stock symbol with caching"""
        try:
            logger.info(f"Searching news for {symbol}")
            
            # Check cache first
            cached_articles = cache_manager.get_cached_data('news', symbol)
            if cached_articles:
                logger.debug(f"Using cached news for {symbol}")
                return cached_articles['data'][:max_articles]
            
            company_names = self.company_mappings.get(symbol, [symbol])
            all_articles = []
            
            # Search for each company name variation
            for company_name in company_names[:2]:  # Limit to 2 main variations
                # Primary search query
                query = f'"{company_name}" stock earnings revenue'
                articles = self.search_google_news(query, max_results=5)
                all_articles.extend(articles)
                
                # AI-specific search if relevant
                if symbol in ['NVDA', 'MSFT', 'GOOGL', 'META', 'CRM', 'PLTR']:
                    ai_query = f'"{company_name}" artificial intelligence AI'
                    ai_articles = self.search_google_news(ai_query, max_results=3)
                    all_articles.extend(ai_articles)
                
                time.sleep(0.5)  # Reduced rate limiting
            
            # Remove duplicates based on title similarity
            unique_articles = []
            seen_titles = set()
            
            for article in all_articles:
                title_key = article['title'][:50].lower()  # First 50 chars
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    
                    # Analyze sentiment
                    full_text = f"{article['title']} {article['description']}"
                    sentiment_analysis = self.analyze_sentiment(full_text)
                    
                    # Add analysis to article
                    article.update({
                        'symbol': symbol,
                        'sentiment_analysis': sentiment_analysis,
                        'relevance_score': self.calculate_relevance_score(article, symbol),
                        'analyzed_at': datetime.now().isoformat()
                    })
                    
                    unique_articles.append(article)
            
            # Sort by relevance score
            unique_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Cache the results
            if unique_articles:
                cache_manager.cache_data('news', symbol, unique_articles[:max_articles])
            
            return unique_articles[:max_articles]
            
        except Exception as e:
            logger.error(f"Error searching news for {symbol}: {e}")
            return []
    
    def calculate_relevance_score(self, article: Dict, symbol: str) -> float:
        """Calculate how relevant an article is to the stock"""
        try:
            score = 0.0
            text = f"{article['title']} {article['description']}".lower()
            
            # Symbol/company name mentions
            company_names = self.company_mappings.get(symbol, [symbol])
            for name in company_names:
                if name.lower() in text:
                    score += 2.0
            
            # Financial keywords
            financial_keywords = [
                'earnings', 'revenue', 'profit', 'stock', 'shares', 'quarter',
                'guidance', 'outlook', 'analyst', 'rating', 'price target'
            ]
            score += sum(0.5 for keyword in financial_keywords if keyword in text)
            
            # AI/Tech relevance (bonus for our focus)
            ai_score = sum(0.3 for keyword in self.ai_keywords if keyword.lower() in text)
            score += ai_score
            
            # Recent news gets higher score
            try:
                # Boost score for recent articles (simple heuristic)
                if 'hour' in article.get('published_date', '').lower():
                    score += 1.0
                elif 'day' in article.get('published_date', '').lower():
                    score += 0.5
            except:
                pass
            
            return min(score, 10.0)  # Cap at 10
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.0
    
    def generate_news_summary(self, symbol: str, articles: List[Dict]) -> Dict:
        """Generate news summary for a stock"""
        try:
            if not articles:
                return {
                    'symbol': symbol,
                    'total_articles': 0,
                    'overall_sentiment': 'neutral',
                    'sentiment_score': 0.0,
                    'key_themes': [],
                    'top_headlines': [],
                    'ai_relevance': 'low'
                }
            
            # Calculate overall sentiment
            sentiment_scores = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            ai_mentions = 0
            
            for article in articles:
                sentiment = article.get('sentiment_analysis', {})
                sentiment_type = sentiment.get('sentiment', 'neutral')
                score = sentiment.get('score', 0)
                
                sentiment_scores.append(score)
                
                if sentiment_type == 'positive':
                    positive_count += 1
                elif sentiment_type == 'negative':
                    negative_count += 1
                else:
                    neutral_count += 1
                
                if sentiment.get('ai_relevance', 0) > 0:
                    ai_mentions += 1
            
            # Overall sentiment calculation
            avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            if avg_score > 1:
                overall_sentiment = 'positive'
            elif avg_score < -1:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            # Extract key themes from headlines
            all_text = ' '.join([article['title'] for article in articles])
            key_themes = self.extract_key_themes(all_text)
            
            # Top headlines (highest relevance)
            top_headlines = [
                {
                    'title': article['title'],
                    'sentiment': article['sentiment_analysis']['sentiment'],
                    'relevance': article['relevance_score'],
                    'url': article['url']
                }
                for article in sorted(articles, key=lambda x: x['relevance_score'], reverse=True)[:5]
            ]
            
            # AI relevance assessment
            ai_percentage = (ai_mentions / len(articles)) * 100 if articles else 0
            if ai_percentage > 30:
                ai_relevance = 'high'
            elif ai_percentage > 10:
                ai_relevance = 'medium'
            else:
                ai_relevance = 'low'
            
            return {
                'symbol': symbol,
                'total_articles': len(articles),
                'overall_sentiment': overall_sentiment,
                'sentiment_score': round(avg_score, 2),
                'sentiment_breakdown': {
                    'positive': positive_count,
                    'negative': negative_count,
                    'neutral': neutral_count
                },
                'key_themes': key_themes,
                'top_headlines': top_headlines,
                'ai_relevance': ai_relevance,
                'ai_mention_percentage': round(ai_percentage, 1),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating news summary for {symbol}: {e}")
            return {}
    
    def extract_key_themes(self, text: str) -> List[str]:
        """Extract key themes from news text"""
        try:
            text_lower = text.lower()
            themes = []
            
            # Define theme patterns
            theme_patterns = {
                'Earnings & Revenue': ['earnings', 'revenue', 'profit', 'quarterly results'],
                'AI & Technology': ['artificial intelligence', 'ai', 'machine learning', 'automation'],
                'Product Launch': ['launch', 'new product', 'release', 'unveil'],
                'Partnership & Deals': ['partnership', 'deal', 'acquisition', 'merger'],
                'Market Performance': ['stock', 'market', 'price', 'shares'],
                'Regulatory': ['regulation', 'lawsuit', 'investigation', 'compliance'],
                'Leadership': ['ceo', 'executive', 'management', 'leadership'],
                'Growth & Expansion': ['growth', 'expansion', 'expansion', 'investment']
            }
            
            for theme, keywords in theme_patterns.items():
                if any(keyword in text_lower for keyword in keywords):
                    themes.append(theme)
            
            return themes[:5]  # Return top 5 themes
            
        except Exception as e:
            logger.error(f"Error extracting themes: {e}")
            return []
    
    def analyze_portfolio_news(self, symbols: List[str]) -> Dict:
        """Analyze news for entire portfolio"""
        try:
            logger.info(f"Analyzing news for {len(symbols)} symbols")
            
            portfolio_analysis = {
                'generated_at': datetime.now().isoformat(),
                'total_symbols': len(symbols),
                'stock_analysis': {},
                'portfolio_summary': {
                    'overall_sentiment': 'neutral',
                    'positive_stocks': [],
                    'negative_stocks': [],
                    'high_ai_relevance': [],
                    'major_news_alerts': []
                }
            }
            
            positive_count = 0
            negative_count = 0
            sentiment_scores = []
            
            for symbol in symbols:
                print(f"   Analyzing news for {symbol}...")
                
                # Get news articles
                articles = self.search_stock_news(symbol, max_articles=10)
                
                # Generate summary
                summary = self.generate_news_summary(symbol, articles)
                
                # Store analysis
                portfolio_analysis['stock_analysis'][symbol] = {
                    'summary': summary,
                    'articles': articles[:5]  # Store top 5 articles
                }
                
                # Aggregate portfolio data
                if summary:
                    sentiment = summary.get('overall_sentiment', 'neutral')
                    sentiment_score = summary.get('sentiment_score', 0)
                    
                    sentiment_scores.append(sentiment_score)
                    
                    if sentiment == 'positive':
                        positive_count += 1
                        portfolio_analysis['portfolio_summary']['positive_stocks'].append({
                            'symbol': symbol,
                            'sentiment_score': sentiment_score
                        })
                    elif sentiment == 'negative':
                        negative_count += 1
                        portfolio_analysis['portfolio_summary']['negative_stocks'].append({
                            'symbol': symbol,
                            'sentiment_score': sentiment_score
                        })
                    
                    # High AI relevance
                    if summary.get('ai_relevance') == 'high':
                        portfolio_analysis['portfolio_summary']['high_ai_relevance'].append(symbol)
                    
                    # Major news alerts (high relevance + strong sentiment)
                    if abs(sentiment_score) > 2 and summary.get('total_articles', 0) > 3:
                        portfolio_analysis['portfolio_summary']['major_news_alerts'].append({
                            'symbol': symbol,
                            'alert_type': 'High news activity with strong sentiment',
                            'sentiment': sentiment,
                            'article_count': summary.get('total_articles', 0)
                        })
                
                time.sleep(1)  # Rate limiting
            
            # Calculate overall portfolio sentiment
            if sentiment_scores:
                avg_portfolio_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                if avg_portfolio_sentiment > 0.5:
                    portfolio_analysis['portfolio_summary']['overall_sentiment'] = 'positive'
                elif avg_portfolio_sentiment < -0.5:
                    portfolio_analysis['portfolio_summary']['overall_sentiment'] = 'negative'
                else:
                    portfolio_analysis['portfolio_summary']['overall_sentiment'] = 'neutral'
            
            return portfolio_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio news: {e}")
            return {}
    
    def save_news_analysis(self, analysis: Dict, filename: str = None):
        """Save news analysis to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_analysis_{timestamp}.json"
        
        filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, default=str)
            logger.info(f"News analysis saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving news analysis: {e}")

def main():
    """Main execution function"""
    analyzer = NewsSentimentAnalyzer()
    
    # Target stocks for news analysis
    target_stocks = [
        "NVDA", "MSFT", "TSLA", "DE", "TSM",
        "AMZN", "GOOGL", "META", "AAPL", "CRM"
    ]
    
    print("Starting comprehensive news analysis...")
    print(f"Analyzing {len(target_stocks)} stocks...")
    
    # Analyze portfolio news
    analysis = analyzer.analyze_portfolio_news(target_stocks)
    
    # Save analysis
    analyzer.save_news_analysis(analysis)
    
    # Print summary
    print("\n=== NEWS ANALYSIS SUMMARY ===")
    summary = analysis.get('portfolio_summary', {})
    
    print(f"Overall Portfolio Sentiment: {summary.get('overall_sentiment', 'unknown').upper()}")
    
    positive_stocks = summary.get('positive_stocks', [])
    if positive_stocks:
        print(f"\nPOSITIVE NEWS SENTIMENT:")
        for stock in positive_stocks:
            print(f"  {stock['symbol']}: Score {stock['sentiment_score']}")
    
    negative_stocks = summary.get('negative_stocks', [])
    if negative_stocks:
        print(f"\nNEGATIVE NEWS SENTIMENT:")
        for stock in negative_stocks:
            print(f"  {stock['symbol']}: Score {stock['sentiment_score']}")
    
    ai_relevant = summary.get('high_ai_relevance', [])
    if ai_relevant:
        print(f"\nHIGH AI RELEVANCE: {', '.join(ai_relevant)}")
    
    alerts = summary.get('major_news_alerts', [])
    if alerts:
        print(f"\nMAJOR NEWS ALERTS:")
        for alert in alerts:
            print(f"  {alert['symbol']}: {alert['alert_type']} ({alert['sentiment']})")

if __name__ == "__main__":
    main()