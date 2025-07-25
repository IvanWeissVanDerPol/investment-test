import os
from dotenv import load_dotenv
import requests
import finnhub
import yfinance as yf
import json
from datetime import datetime
import pandas as pd

load_dotenv()

TRACKING_DIR = os.path.join(os.path.dirname(__file__), '../tracking/sector_data/')
os.makedirs(TRACKING_DIR, exist_ok=True)

def timestamp():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def save_to_json(data, prefix):
    filename = os.path.join(TRACKING_DIR, f"{prefix}_{timestamp()}.json")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved JSON: {filename}")

def save_to_csv(items, prefix):
    filename = os.path.join(TRACKING_DIR, f"{prefix}_{timestamp()}.csv")
    df = pd.DataFrame(items)
    df.to_csv(filename, index=False)
    print(f"Saved CSV: {filename}")

# NewsAPI
def fetch_newsapi_news(query, language='en'):
    api_key = os.getenv('NEWSAPI_KEY')
    url = f'https://newsapi.org/v2/everything?q={query}&language={language}&apiKey={api_key}'
    resp = requests.get(url)
    return resp.json()

# Finnhub News
finnhub_client = finnhub.Client(api_key=os.getenv('FINNHUB_API_KEY'))
def fetch_finnhub_company_news(symbol):
    today = datetime.now().strftime('%Y-%m-%d')
    last_week = (datetime.now() - pd.Timedelta(days=7)).strftime('%Y-%m-%d')
    return finnhub_client.company_news(symbol, _from=last_week, to=today)

# yfinance news (basic headlines, if available)
def fetch_yfinance_news(symbol):
    ticker = yf.Ticker(symbol)
    return ticker.news

class NewsFeed:
    """News feed collector for AI/Robotics investment analysis"""
    
    def __init__(self):
        load_dotenv()
        self.tracking_dir = TRACKING_DIR
        self.finnhub_client = finnhub_client
    
    def get_sector_news(self, keywords=None):
        """Get news for AI/Robotics sectors"""
        if keywords is None:
            keywords = ['artificial intelligence', 'robotics', 'semiconductors', 'AI hardware']
        
        all_news = {}
        for query in keywords:
            newsapi_data = fetch_newsapi_news(query)
            all_news[query] = newsapi_data
        
        return all_news
    
    def get_company_news(self, symbols=None):
        """Get news for specific companies"""
        if symbols is None:
            symbols = ['NVDA', 'MSFT', 'GOOGL', 'TSLA', 'DE']
        
        company_news = {}
        for symbol in symbols:
            try:
                finnhub_news = fetch_finnhub_company_news(symbol)
                yfinance_news = fetch_yfinance_news(symbol)
                company_news[symbol] = {
                    'finnhub': finnhub_news,
                    'yfinance': yfinance_news
                }
            except Exception as e:
                print(f"Error fetching news for {symbol}: {e}")
                company_news[symbol] = {'finnhub': [], 'yfinance': []}
        
        return company_news
    
    def save_news_data(self, data, prefix):
        """Save news data to files"""
        save_to_json(data, prefix)
        return True


if __name__ == "__main__":
    keywords = ['agriculture technology', 'robotics', 'semiconductors', 'AI hardware']
    symbols = ['SOXX', 'BOTZ', 'MOO', 'NVDA', 'MSFT', 'GOOGL', 'TSLA']
    # NewsAPI for sector keywords
    for query in keywords:
        newsapi_data = fetch_newsapi_news(query)
        save_to_json(newsapi_data, f'newsapi_{query.replace(" ", "_")}')
        if 'articles' in newsapi_data:
            save_to_csv(newsapi_data['articles'], f'newsapi_{query.replace(" ", "_")}')
    # Finnhub and yfinance news for each symbol
    for symbol in symbols:
        finnhub_news = fetch_finnhub_company_news(symbol)
        save_to_json(finnhub_news, f'finnhub_news_{symbol}')
        save_to_csv(finnhub_news, f'finnhub_news_{symbol}')
        yfinance_news = fetch_yfinance_news(symbol)
        save_to_json(yfinance_news, f'yfinance_news_{symbol}')
        save_to_csv(yfinance_news, f'yfinance_news_{symbol}')
