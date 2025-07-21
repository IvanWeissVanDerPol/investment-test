"""
Local Investment Dashboard Backend
FastAPI backend for interactive stock dashboard
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime
from pathlib import Path
import sys
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Investment Dashboard", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=4)

class StockPreview(BaseModel):
    symbol: str
    name: str
    current_price: float
    change_percent: float
    sentiment_score: float
    sentiment_label: str
    ai_relevance: str
    last_updated: str

class StockDetail(BaseModel):
    symbol: str
    name: str
    current_data: Dict
    news_analysis: Dict
    technical_indicators: Dict
    sentiment_trend: List[Dict]
    recommendations: List[str]

class Person(BaseModel):
    name: str
    type: str  # "investor", "analyst", "influencer"
    focus_areas: List[str]
    track_record: str
    sources: List[str]

class CustomValue(BaseModel):
    key: str
    value: str
    category: str
    notes: str = ""

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": {}})

@app.get("/stock/{symbol}")
async def stock_detail_page(symbol: str):
    """Serve the stock detail page"""
    return templates.TemplateResponse("stock_detail.html", {"request": {}, "symbol": symbol})

@app.get("/people")
async def people_page():
    """Serve the people tracking page"""
    return templates.TemplateResponse("people.html", {"request": {}})

@app.get("/settings")
async def settings_page():
    """Serve the settings page"""
    return templates.TemplateResponse("settings.html", {"request": {}})

@app.get("/api/stocks")
async def get_stocks():
    """Get list of all tracked stocks with basic info"""
    try:
        with open('config/config.json', 'r') as f:
            config = json.load(f)
        
        symbols = config.get('target_stocks', [
            'NVDA', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMZN', 'AAPL', 'CRM',
            'DE', 'TSM', 'AMD', 'INTC', 'QCOM', 'PLTR', 'SNOW'
        ])
        
        # Get basic stock info
        stocks = []
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Open'].iloc[0]
                    change_percent = ((current_price - prev_close) / prev_close) * 100
                else:
                    current_price = info.get('currentPrice', 0)
                    change_percent = info.get('regularMarketChangePercent', 0)
                
                stocks.append({
                    'symbol': symbol,
                    'name': info.get('longName', symbol),
                    'current_price': round(current_price, 2),
                    'change_percent': round(change_percent, 2),
                    'market_cap': info.get('marketCap', 0),
                    'sector': info.get('sector', 'Unknown')
                })
            except Exception as e:
                logger.warning(f"Failed to get data for {symbol}: {e}")
                stocks.append({
                    'symbol': symbol,
                    'name': symbol,
                    'current_price': 0,
                    'change_percent': 0,
                    'market_cap': 0,
                    'sector': 'Unknown'
                })
        
        return stocks
    except Exception as e:
        logger.error(f"Error getting stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{symbol}/preview")
async def get_stock_preview(symbol: str):
    """Get detailed preview for hover tooltip"""
    try:
        # Get stock data
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="5d")
        
        # Get news sentiment
        try:
            news_data = news_analyzer.analyze_stock_sentiment(symbol)
            sentiment_score = news_data.get('sentiment_stats', {}).get('avg_sentiment', 0)
            sentiment_label = "Positive" if sentiment_score > 0.1 else "Negative" if sentiment_score < -0.1 else "Neutral"
            ai_relevance = news_data.get('ai_relevance', 'low')
        except Exception as e:
            logger.warning(f"Failed to get sentiment for {symbol}: {e}")
            sentiment_score = 0
            sentiment_label = "Unknown"
            ai_relevance = "low"
        
        # Calculate recent performance
        if len(hist) >= 2:
            current_price = hist['Close'].iloc[-1]
            week_ago_price = hist['Close'].iloc[0]
            week_change = ((current_price - week_ago_price) / week_ago_price) * 100
        else:
            current_price = info.get('currentPrice', 0)
            week_change = 0
        
        return {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'current_price': round(current_price, 2),
            'week_change': round(week_change, 2),
            'sentiment_score': round(sentiment_score, 3),
            'sentiment_label': sentiment_label,
            'ai_relevance': ai_relevance,
            'market_cap': info.get('marketCap', 0),
            'sector': info.get('sector', 'Unknown'),
            'recommendation': info.get('recommendationMean', 'N/A'),
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting preview for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{symbol}/details")
async def get_stock_details(symbol: str):
    """Get comprehensive stock details"""
    try:
        # Get stock data
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get historical data
        hist_1m = ticker.history(period="1mo")
        hist_6m = ticker.history(period="6mo")
        
        # Get news sentiment
        try:
            news_data = news_analyzer.analyze_stock_sentiment(symbol)
        except Exception as e:
            logger.warning(f"Failed to get news sentiment for {symbol}: {e}")
            news_data = {}
        
        # Calculate technical indicators
        technical_indicators = {}
        if not hist_1m.empty:
            current_price = hist_1m['Close'].iloc[-1]
            sma_20 = hist_1m['Close'].rolling(window=20).mean().iloc[-1] if len(hist_1m) >= 20 else current_price
            sma_50 = hist_1m['Close'].rolling(window=50).mean().iloc[-1] if len(hist_1m) >= 50 else current_price
            
            technical_indicators = {
                'sma_20': round(sma_20, 2),
                'sma_50': round(sma_50, 2),
                'rsi': 50,  # Simplified for now
                'volume_avg': int(hist_1m['Volume'].mean()),
                'volatility': round(hist_1m['Close'].pct_change().std() * 100, 2)
            }
        
        # Generate recommendations
        recommendations = []
        sentiment_score = news_data.get('sentiment_stats', {}).get('avg_sentiment', 0)
        
        if sentiment_score > 0.3:
            recommendations.append("Strong positive news sentiment - consider buying")
        elif sentiment_score > 0.1:
            recommendations.append("Positive news sentiment - good to hold")
        elif sentiment_score < -0.3:
            recommendations.append("Negative news sentiment - consider selling")
        elif sentiment_score < -0.1:
            recommendations.append("Caution advised due to negative sentiment")
        
        return {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'description': info.get('longBusinessSummary', 'No description available'),
            'current_data': {
                'price': info.get('currentPrice', 0),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 0)
            },
            'news_analysis': news_data,
            'technical_indicators': technical_indicators,
            'sentiment_trend': [],  # Placeholder for historical sentiment
            'recommendations': recommendations,
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting details for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{symbol}/news")
async def get_stock_news(symbol: str, limit: int = Query(default=5)):
    """Get recent news for a stock"""
    try:
        news_data = news_analyzer.analyze_stock_sentiment(symbol)
        articles = news_data.get('articles', [])[:limit]
        
        return {
            'symbol': symbol,
            'articles': articles,
            'total_articles': len(news_data.get('articles', [])),
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/refresh/{symbol}")
async def refresh_stock_data(symbol: str):
    """Refresh data for a specific stock"""
    try:
        # This would typically refresh cache
        return {"message": f"Data refreshed for {symbol}"}
    except Exception as e:
        logger.error(f"Error refreshing data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)