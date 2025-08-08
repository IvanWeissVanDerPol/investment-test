from config.settings import get_settings
import requests
import pandas as pd
import yfinance as yf
import finnhub
try:
    from alpaca_trade_api.rest import REST, TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
import json
from datetime import datetime

settings = get_settings()

import os
TRACKING_DIR = os.path.join(os.path.dirname(__file__), '../tracking/sector_data/')
os.makedirs(TRACKING_DIR, exist_ok=True)

def timestamp():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def save_to_csv(df, prefix):
    filename = os.path.join(TRACKING_DIR, f"{prefix}_{timestamp()}.csv")
    df.to_csv(filename)
    print(f"Saved CSV: {filename}")

def save_to_json(data, prefix):
    filename = os.path.join(TRACKING_DIR, f"{prefix}_{timestamp()}.json")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved JSON: {filename}")

# Twelve Data
def fetch_twelvedata_price(symbol):
    api_key = settings.apis.twelvedata_api_key
    url = f'https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&apikey={api_key}'
    resp = requests.get(url)
    return resp.json()

# yfinance
def fetch_yfinance_price(symbol):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="5d")
    return hist

# Finnhub
finnhub_client = finnhub.Client(api_key=settings.apis.finnhub_api_key)
def fetch_finnhub_quote(symbol):
    return finnhub_client.quote(symbol)

def fetch_finnhub_company_news(symbol):
    today = datetime.now().strftime('%Y-%m-%d')
    last_week = (datetime.now() - pd.Timedelta(days=7)).strftime('%Y-%m-%d')
    return finnhub_client.company_news(symbol, _from=last_week, to=today)

# Alpaca
if ALPACA_AVAILABLE:
    ALPACA_API_KEY = settings.apis.alpaca_api_key
    ALPACA_API_SECRET = settings.apis.alpaca_api_secret
    ALPACA_PAPER_BASE_URL = 'https://paper-api.alpaca.markets'
    try:
        alpaca = REST(ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_PAPER_BASE_URL)
    except:
        alpaca = None
        ALPACA_AVAILABLE = False
else:
    alpaca = None

def fetch_alpaca_price(symbol):
    if ALPACA_AVAILABLE and alpaca:
        try:
            barset = alpaca.get_bars(symbol, TimeFrame.Day, limit=5)
            return barset.df if hasattr(barset, 'df') else barset
        except:
            return None
    return None

class DataIngestion:
    """Data ingestion manager for multiple market data sources"""
    
    def __init__(self):
        load_dotenv()
        self.tracking_dir = TRACKING_DIR
        self.finnhub_client = finnhub_client
        self.alpaca_available = ALPACA_AVAILABLE
        self.alpaca = alpaca if ALPACA_AVAILABLE else None
    
    def get_multi_source_data(self, symbols):
        """Get data from multiple sources for given symbols"""
        results = {}
        
        for symbol in symbols:
            symbol_data = {}
            
            # Twelve Data
            try:
                symbol_data['twelvedata'] = fetch_twelvedata_price(symbol)
            except Exception as e:
                symbol_data['twelvedata'] = None
            
            # yfinance
            try:
                symbol_data['yfinance'] = fetch_yfinance_price(symbol)
            except Exception as e:
                symbol_data['yfinance'] = None
            
            # Finnhub
            try:
                symbol_data['finnhub_quote'] = fetch_finnhub_quote(symbol)
                symbol_data['finnhub_news'] = fetch_finnhub_company_news(symbol)
            except Exception as e:
                symbol_data['finnhub_quote'] = None
                symbol_data['finnhub_news'] = None
            
            # Alpaca
            if self.alpaca_available:
                try:
                    symbol_data['alpaca'] = fetch_alpaca_price(symbol)
                except Exception as e:
                    symbol_data['alpaca'] = None
            else:
                symbol_data['alpaca'] = None
            
            results[symbol] = symbol_data
        
        return results
    
    def save_data(self, data, prefix):
        """Save data to files"""
        save_to_json(data, prefix)
        return True


if __name__ == "__main__":
    tickers = ['SOXX', 'BOTZ', 'MOO', 'NVDA', 'MSFT', 'GOOGL', 'TSLA']
    for symbol in tickers:
        # Twelve Data
        td_data = fetch_twelvedata_price(symbol)
        save_to_json(td_data, f'twelvedata_{symbol}')
        # yfinance
        yf_data = fetch_yfinance_price(symbol)
        save_to_csv(yf_data, f'yfinance_{symbol}')
        # Finnhub
        fh_quote = fetch_finnhub_quote(symbol)
        save_to_json(fh_quote, f'finnhub_quote_{symbol}')
        fh_news = fetch_finnhub_company_news(symbol)
        save_to_json(fh_news, f'finnhub_news_{symbol}')
        # Alpaca
        alpaca_data = fetch_alpaca_price(symbol)
        if isinstance(alpaca_data, pd.DataFrame):
            save_to_csv(alpaca_data, f'alpaca_{symbol}')
        else:
            save_to_json(alpaca_data, f'alpaca_{symbol}')
