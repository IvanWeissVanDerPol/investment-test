"""
Enhanced News Sentiment Analyzer
Complete integration with advanced sentiment analysis and market intelligence
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from analysis.news_sentiment_analyzer import NewsSentimentAnalyzer

logger = logging.getLogger(__name__)

class EnhancedNewsSentiment:
    """Enhanced news sentiment analyzer with complete integration"""
    
    def __init__(self):
        self.analyzer = NewsSentimentAnalyzer()
        self.report_dir = Path("reports/news_analysis")
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def run_comprehensive_analysis(self, symbols: List[str] = None) -> Dict:
        """Run comprehensive news sentiment analysis for all symbols"""
        
        if symbols is None:
            symbols = [
                'NVDA', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMZN', 'AAPL', 'CRM',
                'DE', 'TSM', 'AMD', 'INTC', 'QCOM', 'PLTR', 'SNOW'
            ]
        
        logger.info(f"Starting comprehensive news analysis for {len(symbols)} symbols")
        
        analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'comprehensive_news_sentiment',
            'symbols_analyzed': len(symbols),
            'symbol_results': {},
            'market_overview': {},
            'alerts': [],
            'recommendations': []
        }
        
        all_sentiments = []
        
        for symbol in symbols:
            try:
                logger.info(f"Analyzing {symbol}...")
                
                # Get news sentiment analysis
                news_data = self.analyzer.analyze_stock_sentiment(symbol)
                
                # Process and enhance data
                enhanced_data = self._enhance_news_data(symbol, news_data)
                analysis_results['symbol_results'][symbol] = enhanced_data
                
                # Collect for market overview
                if enhanced_data.get('sentiment_score') is not None:
                    all_sentiments.append(enhanced_data['sentiment_score'])
                
                # Generate alerts for strong sentiment
                if abs(enhanced_data.get('sentiment_score', 0)) > 0.4 and enhanced_data.get('confidence', 0) > 0.7:
                    analysis_results['alerts'].append({
                        'symbol': symbol,
                        'sentiment_score': enhanced_data['sentiment_score'],
                        'confidence': enhanced_data['confidence'],
                        'type': 'positive' if enhanced_data['sentiment_score'] > 0 else 'negative',
                        'message': f"Strong news sentiment detected for {symbol}"
                    })
            
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                analysis_results['symbol_results'][symbol] = {
                    'error': str(e),
                    'symbol': symbol
                }
        
        # Generate market overview
        if all_sentiments:
            analysis_results['market_overview'] = {
                'average_sentiment': sum(all_sentiments) / len(all_sentiments),
                'sentiment_distribution': {
                    'positive': len([s for s in all_sentiments if s > 0.1]),
                    'negative': len([s for s in all_sentiments if s < -0.1]),
                    'neutral': len([s for s in all_sentiments if -0.1 <= s <= 0.1])
                },
                'total_alerts': len(analysis_results['alerts'])
            }
        
        # Generate recommendations
        analysis_results['recommendations'] = self._generate_recommendations(analysis_results)
        
        # Save results
        self._save_analysis_results(analysis_results)
        
        logger.info("Comprehensive news analysis completed")
        return analysis_results
    
    def _enhance_news_data(self, symbol: str, news_data: Dict) -> Dict:
        """Enhance news data with additional insights"""
        
        if not news_data or 'error' in news_data:
            return news_data
        
        enhanced = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'raw_data': news_data
        }
        
        # Extract sentiment statistics
        if news_data.get('sentiment_stats'):
            stats = news_data['sentiment_stats']
            enhanced.update({
                'sentiment_score': stats.get('avg_sentiment', 0),
                'confidence': stats.get('avg_confidence', 0),
                'strong_signals': stats.get('strong_signals', 0),
                'ai_relevance': news_data.get('ai_relevance', 'low')
            })
        
        # Count articles
        enhanced['total_articles'] = len(news_data.get('articles', []))
        
        # Generate quick summary
        if enhanced.get('sentiment_score') is not None:
            score = enhanced['sentiment_score']
            if score > 0.3:
                enhanced['summary'] = f"Positive news sentiment ({score:.2f}) for {symbol}"
            elif score < -0.3:
                enhanced['summary'] = f"Negative news sentiment ({score:.2f}) for {symbol}"
            else:
                enhanced['summary'] = f"Neutral news sentiment ({score:.2f}) for {symbol}"
        
        return enhanced
    
    def _generate_recommendations(self, analysis_results: Dict) -> List[Dict]:
        """Generate investment recommendations based on news sentiment"""
        
        recommendations = []
        
        # Market-level recommendations
        market_sentiment = analysis_results['market_overview'].get('average_sentiment', 0)
        
        if market_sentiment > 0.2:
            recommendations.append({
                'type': 'market_sentiment',
                'message': "Overall positive news sentiment across AI/tech stocks",
                'confidence': min(abs(market_sentiment), 0.8),
                'action': 'consider_bullish_positions'
            })
        elif market_sentiment < -0.2:
            recommendations.append({
                'type': 'market_sentiment',
                'message': "Overall negative news sentiment - exercise caution",
                'confidence': min(abs(market_sentiment), 0.8),
                'action': 'consider_defensive_positions'
            })
        
        # Symbol-specific recommendations
        for symbol, data in analysis_results['symbol_results'].items():
            if 'error' in data:
                continue
            
            sentiment_score = data.get('sentiment_score', 0)
            confidence = data.get('confidence', 0)
            
            if abs(sentiment_score) > 0.4 and confidence > 0.7:
                if sentiment_score > 0:
                    recommendations.append({
                        'type': 'symbol_sentiment',
                        'symbol': symbol,
                        'message': f"Strong positive news sentiment for {symbol}",
                        'confidence': confidence,
                        'action': 'research_buy_opportunity',
                        'sentiment_score': sentiment_score
                    })
                else:
                    recommendations.append({
                        'type': 'symbol_sentiment',
                        'symbol': symbol,
                        'message': f"Strong negative news sentiment for {symbol}",
                        'confidence': confidence,
                        'action': 'review_holdings',
                        'sentiment_score': sentiment_score
                    })
        
        return recommendations
    
    def _save_analysis_results(self, results: Dict):
        """Save analysis results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_sentiment_analysis_{timestamp}.json"
            filepath = self.report_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Analysis results saved to {filepath}")
            
            # Also save latest summary
            latest_file = self.report_dir / "latest_news_summary.json"
            with open(latest_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
    
    def generate_daily_report(self) -> Dict:
        """Generate daily news sentiment report"""
        
        logger.info("Generating daily news sentiment report...")
        
        # Load configuration
        try:
            with open('config/config.json', 'r') as f:
                config = json.load(f)
            symbols = config.get('target_stocks', [])
        except:
            symbols = ['NVDA', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMZN', 'AAPL', 'CRM']
        
        # Run comprehensive analysis
        results = self.run_comprehensive_analysis(symbols)
        
        # Generate human-readable summary
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'summary': f"Analyzed {len(symbols)} stocks for news sentiment",
            'key_findings': [],
            'alerts': len(results.get('alerts', [])),
            'recommendations': len(results.get('recommendations', []))
        }
        
        # Add key findings
        if results.get('market_overview'):
            avg_sentiment = results['market_overview']['average_sentiment']
            sentiment_desc = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"
            report['key_findings'].append(f"Market sentiment is {sentiment_desc} ({avg_sentiment:.2f})")
        
        # Add alerts summary
        if results.get('alerts'):
            positive_alerts = [a for a in results['alerts'] if a['type'] == 'positive']
            negative_alerts = [a for a in results['alerts'] if a['type'] == 'negative']
            report['key_findings'].append(f"{len(positive_alerts)} positive alerts, {len(negative_alerts)} negative alerts")
        
        # Save human-readable report
        try:
            summary_file = self.report_dir / "daily_summary.txt"
            with open(summary_file, 'w') as f:
                f.write(f"Daily News Sentiment Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for finding in report['key_findings']:
                    f.write(f"• {finding}\n")
                
                f.write(f"\nAlerts: {report['alerts']}\n")
                f.write(f"Recommendations: {report['recommendations']}\n")
            
            logger.info("Daily summary saved to daily_summary.txt")
            
        except Exception as e:
            logger.error(f"Error saving daily summary: {e}")
        
        return report


def main():
    """Main function for standalone execution"""
    
    from datetime import datetime
    
    print("🚀 Enhanced News Sentiment Analysis")
    print("=" * 50)
    
    enhancer = EnhancedNewsSentiment()
    
    # Run comprehensive analysis
    results = enhancer.generate_daily_report()
    
    print(f"\n📊 Daily News Report Generated")
    print(f"Date: {results['date']}")
    print(f"Symbols Analyzed: {results.get('summary', '').split()[0]}")
    
    print("\n🔍 Key Findings:")
    for finding in results['key_findings']:
        print(f"  • {finding}")
    
    print(f"\n📈 Alerts: {results['alerts']}")
    print(f"💡 Recommendations: {results['recommendations']}")
    
    # Show detailed results
    try:
        import json
        with open('reports/news_analysis/latest_news_summary.json', 'r') as f:
            detailed = json.load(f)
        
        if 'urgent_alerts' in detailed and detailed['urgent_alerts']:
            print("\n🚨 Urgent Alerts:")
            for alert in detailed['urgent_alerts']:
                print(f"  {alert['symbol']}: {alert['sentiment']:.2f} ({alert['confidence']:.1%})")
        
    except Exception as e:
        print(f"Could not load detailed results: {e}")


if __name__ == "__main__":
    main()