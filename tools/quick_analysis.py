"""
Quick Investment Analysis - Simplified version for immediate results
"""

import json
import yfinance as yf
import pandas as pd
from datetime import datetime
import logging
from news_sentiment_analyzer import NewsSentimentAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_stock_analysis(symbol):
    """Get quick analysis for a stock"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="3mo")
        
        if hist.empty:
            return None
            
        current_price = info.get('currentPrice', hist['Close'].iloc[-1])
        prev_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
        
        # Calculate simple metrics
        day_change = current_price - prev_close
        day_change_pct = (day_change / prev_close) * 100 if prev_close > 0 else 0
        
        # Simple moving averages
        sma_20 = hist['Close'].rolling(20).mean().iloc[-1] if len(hist) >= 20 else current_price
        sma_50 = hist['Close'].rolling(50).mean().iloc[-1] if len(hist) >= 50 else current_price
        
        # Volume analysis
        avg_volume = hist['Volume'].mean()
        current_volume = hist['Volume'].iloc[-1] if not hist.empty else 0
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Simple signal generation
        signals = []
        score = 0
        
        if current_price > sma_20:
            signals.append("Above 20-day average")
            score += 1
        if current_price > sma_50:
            signals.append("Above 50-day average") 
            score += 1
        if day_change_pct > 2:
            signals.append("Strong daily gain")
            score += 2
        elif day_change_pct > 0:
            signals.append("Positive daily move")
            score += 1
        if volume_ratio > 1.5:
            signals.append("High volume")
            score += 1
            
        # Generate recommendation
        if score >= 4:
            recommendation = "STRONG BUY"
        elif score >= 2:
            recommendation = "BUY"
        elif score >= 0:
            recommendation = "HOLD"
        else:
            recommendation = "CAUTION"
            
        return {
            'symbol': symbol,
            'current_price': round(current_price, 2),
            'day_change': round(day_change, 2),
            'day_change_pct': round(day_change_pct, 2),
            'volume_ratio': round(volume_ratio, 2),
            'sma_20': round(sma_20, 2),
            'sma_50': round(sma_50, 2),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'signals': signals,
            'score': score,
            'recommendation': recommendation,
            'confidence': min(score / 5, 1.0)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return None

def generate_quick_report():
    """Generate quick investment report"""
    # Your investment targets
    stocks = [
        "NVDA", "MSFT", "TSLA", "DE", "TSM",
        "AMZN", "GOOGL", "META", "AAPL", "CRM"
    ]
    
    etfs = ["KROP", "BOTZ", "SOXX", "ARKQ", "ROBO"]
    
    # Initialize news analyzer
    news_analyzer = NewsSentimentAnalyzer()
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'user_profile': {
            'dukascopy_balance': 900,
            'available_for_investment': 700,  # Keeping $200 as cash buffer
            'investment_focus': 'AI/Robotics with government contract exposure'
        },
        'stock_analysis': {},
        'etf_analysis': {},
        'news_analysis': {},
        'recommendations': {
            'strong_buys': [],
            'buys': [],
            'top_opportunities': []
        },
        'portfolio_suggestions': {
            'allocation': {},
            'total_recommended_investment': 0
        }
    }
    
    print("Analyzing stocks...")
    
    # Analyze stocks
    for symbol in stocks:
        print(f"   Analyzing {symbol}...")
        analysis = get_stock_analysis(symbol)
        if analysis:
            report['stock_analysis'][symbol] = analysis
            
            # Categorize recommendations
            if analysis['recommendation'] == 'STRONG BUY':
                report['recommendations']['strong_buys'].append(analysis)
            elif analysis['recommendation'] == 'BUY':
                report['recommendations']['buys'].append(analysis)
    
    print("Analyzing ETFs...")
    
    # Analyze ETFs
    for symbol in etfs:
        print(f"   Analyzing {symbol}...")
        analysis = get_stock_analysis(symbol)
        if analysis:
            report['etf_analysis'][symbol] = analysis
            
            if analysis['recommendation'] in ['STRONG BUY', 'BUY']:
                report['recommendations']['top_opportunities'].append(analysis)
    
    print("Analyzing news sentiment...")
    
    # Analyze news for top stocks only (to save time)
    top_stocks = stocks[:5]  # Top 5 stocks for news analysis
    for symbol in top_stocks:
        print(f"   Getting news for {symbol}...")
        try:
            articles = news_analyzer.search_stock_news(symbol, max_articles=5)
            news_summary = news_analyzer.generate_news_summary(symbol, articles)
            
            report['news_analysis'][symbol] = {
                'summary': news_summary,
                'recent_headlines': [
                    {
                        'title': article['title'][:100] + '...' if len(article['title']) > 100 else article['title'],
                        'sentiment': article.get('sentiment_analysis', {}).get('sentiment', 'neutral'),
                        'url': article['url']
                    }
                    for article in articles[:3]  # Top 3 headlines
                ]
            }
        except Exception as e:
            logger.warning(f"Could not get news for {symbol}: {e}")
            report['news_analysis'][symbol] = {
                'summary': {'overall_sentiment': 'neutral', 'total_articles': 0},
                'recent_headlines': []
            }
    
    # Sort recommendations by confidence
    report['recommendations']['strong_buys'].sort(key=lambda x: x['confidence'], reverse=True)
    report['recommendations']['buys'].sort(key=lambda x: x['confidence'], reverse=True)
    report['recommendations']['top_opportunities'].sort(key=lambda x: x['confidence'], reverse=True)
    
    # Generate portfolio allocation suggestions
    total_investment = 0
    allocations = {}
    
    # Strong buys get larger allocation
    for stock in report['recommendations']['strong_buys'][:3]:  # Top 3
        allocation = min(150, 700 * 0.2)  # Max $150 or 20% of available
        allocations[stock['symbol']] = allocation
        total_investment += allocation
    
    # Regular buys get smaller allocation  
    for stock in report['recommendations']['buys'][:2]:  # Top 2
        allocation = min(100, 700 * 0.15)  # Max $100 or 15% of available
        allocations[stock['symbol']] = allocation
        total_investment += allocation
        
    # ETF allocation
    for etf in report['recommendations']['top_opportunities'][:1]:  # Top 1 ETF
        allocation = min(100, 700 * 0.15)
        allocations[etf['symbol']] = allocation
        total_investment += allocation
    
    report['portfolio_suggestions']['allocation'] = allocations
    report['portfolio_suggestions']['total_recommended_investment'] = total_investment
    report['portfolio_suggestions']['remaining_cash'] = 700 - total_investment
    
    return report

def create_readable_summary(report):
    """Create human-readable summary"""
    summary = f"""
=== AUTOMATED INVESTMENT ANALYSIS REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

YOUR INVESTMENT PROFILE:
• Dukascopy Balance: ${report['user_profile']['dukascopy_balance']}
• Available for Investment: ${report['user_profile']['available_for_investment']}
• Focus: {report['user_profile']['investment_focus']}

TOP INVESTMENT OPPORTUNITIES:

STRONG BUY SIGNALS:"""
    
    strong_buys = report['recommendations']['strong_buys']
    if strong_buys:
        for stock in strong_buys:
            summary += f"\n  + {stock['symbol']}: ${stock['current_price']} ({stock['day_change_pct']:+.1f}%)"
            summary += f"\n     Confidence: {stock['confidence']:.1%} | Signals: {', '.join(stock['signals'][:2])}"
    else:
        summary += "\n  No strong buy signals detected"
    
    summary += "\n\nBUY SIGNALS:"
    buys = report['recommendations']['buys']
    if buys:
        for stock in buys:
            summary += f"\n  * {stock['symbol']}: ${stock['current_price']} ({stock['day_change_pct']:+.1f}%)"
            summary += f"\n     Confidence: {stock['confidence']:.1%} | Signals: {', '.join(stock['signals'][:2])}"
    else:
        summary += "\n  No buy signals detected"
    
    summary += "\n\nETF OPPORTUNITIES:"
    etfs = report['recommendations']['top_opportunities']
    if etfs:
        for etf in etfs:
            summary += f"\n  > {etf['symbol']}: ${etf['current_price']} ({etf['day_change_pct']:+.1f}%)"
            summary += f"\n     Recommendation: {etf['recommendation']} | Confidence: {etf['confidence']:.1%}"
    else:
        summary += "\n  No ETF opportunities detected"
    
    summary += f"\n\nRECOMMENDED PORTFOLIO ALLOCATION:"
    allocations = report['portfolio_suggestions']['allocation']
    if allocations:
        for symbol, amount in allocations.items():
            percentage = (amount / 700) * 100
            summary += f"\n  • {symbol}: ${amount} ({percentage:.1f}%)"
        
        total_inv = report['portfolio_suggestions']['total_recommended_investment']
        remaining = report['portfolio_suggestions']['remaining_cash']
        summary += f"\n\nTotal Investment: ${total_inv}"
        summary += f"\nRemaining Cash: ${remaining}"
        summary += f"\nCash Allocation: {(remaining/700)*100:.1f}%"
    else:
        summary += "\n  No specific allocations recommended - consider keeping cash for better opportunities"
    
    # Add news sentiment section
    news_data = report.get('news_analysis', {})
    if news_data:
        summary += f"\n\nNEWS SENTIMENT ANALYSIS:"
        for symbol, news_info in news_data.items():
            news_summary = news_info.get('summary', {})
            sentiment = news_summary.get('overall_sentiment', 'neutral')
            article_count = news_summary.get('total_articles', 0)
            
            summary += f"\n  {symbol}: {sentiment.upper()} sentiment ({article_count} articles)"
            
            # Add top headlines
            headlines = news_info.get('recent_headlines', [])
            if headlines:
                summary += f"\n     Recent: {headlines[0]['title']}"
    
    summary += f"\n\nNEXT ACTIONS:"
    summary += f"\n  1. Review the strong buy recommendations above"
    summary += f"\n  2. Check your Dukascopy account for available funds"
    summary += f"\n  3. Consider starting with smaller position sizes"
    summary += f"\n  4. Monitor daily for changes in recommendations"
    summary += f"\n  5. Keep 20-30% in cash for opportunities"
    
    return summary

def main():
    """Main execution"""
    print("Starting Automated Investment Analysis...")
    print("   This may take 2-3 minutes to collect data...")
    
    # Generate report
    report = generate_quick_report()
    
    # Save JSON report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\investment_analysis_{timestamp}.json"
    
    with open(json_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Create and save human-readable summary
    summary = create_readable_summary(report)
    txt_filename = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\investment_summary_{timestamp}.txt"
    
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    # Print summary to console
    print(summary)
    
    print(f"\nReports saved:")
    print(f"   JSON: {json_filename}")
    print(f"   Summary: {txt_filename}")
    
    # Quick stats
    strong_buys = len(report['recommendations']['strong_buys'])
    buys = len(report['recommendations']['buys']) 
    total_investment = report['portfolio_suggestions']['total_recommended_investment']
    
    print(f"\nANALYSIS COMPLETE:")
    print(f"   Strong Buys: {strong_buys}")
    print(f"   Buys: {buys}")
    print(f"   Recommended Investment: ${total_investment}")

if __name__ == "__main__":
    main()