"""
Market Data Collection Module
Real-time market data, technical indicators, and price tracking
"""

import requests
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import yfinance as yf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataCollector:
    def __init__(self, config_file: str = None):
        """Initialize with API keys and configuration"""
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration and API keys"""
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                logger.warning(f"Config file {config_file} not found, using defaults")
        
        return {
            "alpha_vantage": {
                "api_key": "YOUR_ALPHA_VANTAGE_API_KEY",
                "base_url": "https://www.alphavantage.co/query"
            },
            "polygon": {
                "api_key": "YOUR_POLYGON_API_KEY",
                "base_url": "https://api.polygon.io"
            },
            "target_stocks": [
                "NVDA", "MSFT", "TSLA", "DE", "TSM",
                "AMZN", "GOOGL", "META", "AAPL", "CRM"
            ],
            "ai_robotics_etfs": [
                "KROP", "BOTZ", "SOXX", "ARKQ", "ROBO", "IRBO", "UBOT"
            ],
            "sectors": {
                "AI_Software": ["NVDA", "MSFT", "GOOGL", "META", "CRM"],
                "AI_Hardware": ["NVDA", "TSM", "AMD", "INTC", "QCOM"],
                "Robotics": ["DE", "ABB", "FANUY", "KUKA.DE", "IRobot"],
                "Agriculture_Tech": ["DE", "CNH", "AGCO", "TTI"]
            }
        }
    
    def get_real_time_price(self, symbol: str) -> Dict:
        """Get real-time price data using yfinance (free)"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price data
            data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'current_price': info.get('currentPrice', 0),
                'previous_close': info.get('previousClose', 0),
                'day_change': 0,
                'day_change_percent': 0,
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                '52_week_low': info.get('fiftyTwoWeekLow', 0)
            }
            
            # Calculate day change
            if data['current_price'] and data['previous_close']:
                data['day_change'] = data['current_price'] - data['previous_close']
                data['day_change_percent'] = (data['day_change'] / data['previous_close']) * 100
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting real-time price for {symbol}: {e}")
            return {}
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Get historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            # Add technical indicators
            hist = self.add_technical_indicators(hist)
            
            return hist
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to price data"""
        try:
            # Simple Moving Averages
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # Exponential Moving Averages
            df['EMA_12'] = df['Close'].ewm(span=12).mean()
            df['EMA_26'] = df['Close'].ewm(span=26).mean()
            
            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            
            # Volume indicators
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {e}")
            return df
    
    def analyze_sector_performance(self) -> Dict:
        """Analyze performance across AI/robotics sectors"""
        try:
            sectors = self.config.get('sectors', {})
            sector_analysis = {
                'timestamp': datetime.now().isoformat(),
                'sectors': {}
            }
            
            for sector_name, symbols in sectors.items():
                logger.info(f"Analyzing sector: {sector_name}")
                
                sector_data = {
                    'symbols': symbols,
                    'performance': [],
                    'avg_change': 0,
                    'total_volume': 0,
                    'momentum_score': 0,
                    'strength_rating': 'Neutral'
                }
                
                daily_changes = []
                total_volume = 0
                
                for symbol in symbols:
                    price_data = self.get_real_time_price(symbol)
                    if price_data:
                        sector_data['performance'].append({
                            'symbol': symbol,
                            'change_percent': price_data.get('day_change_percent', 0),
                            'volume_ratio': price_data.get('volume', 0) / max(price_data.get('avg_volume', 1), 1)
                        })
                        daily_changes.append(price_data.get('day_change_percent', 0))
                        total_volume += price_data.get('volume', 0)
                
                # Calculate sector metrics
                if daily_changes:
                    sector_data['avg_change'] = np.mean(daily_changes)
                    sector_data['total_volume'] = total_volume
                    sector_data['momentum_score'] = self.calculate_momentum_score(daily_changes)
                    sector_data['strength_rating'] = self.rate_sector_strength(sector_data['avg_change'], sector_data['momentum_score'])
                
                sector_analysis['sectors'][sector_name] = sector_data
            
            return sector_analysis
            
        except Exception as e:
            logger.error(f"Error in sector analysis: {e}")
            return {}
    
    def calculate_momentum_score(self, changes: List[float]) -> float:
        """Calculate momentum score for a list of price changes"""
        if not changes:
            return 0.0
        
        # Weight recent performance higher
        positive_count = sum(1 for change in changes if change > 0)
        total_count = len(changes)
        
        # Momentum based on % of stocks moving up and average magnitude
        momentum = (positive_count / total_count) * (1 + abs(np.mean(changes)) / 100)
        
        return min(momentum, 2.0)  # Cap at 2.0
    
    def rate_sector_strength(self, avg_change: float, momentum: float) -> str:
        """Rate sector strength based on performance metrics"""
        if avg_change > 2.0 and momentum > 1.5:
            return "Very Strong"
        elif avg_change > 1.0 and momentum > 1.2:
            return "Strong"
        elif avg_change > 0 and momentum > 1.0:
            return "Bullish"
        elif avg_change > -1.0 and momentum > 0.8:
            return "Neutral"
        elif avg_change > -2.0:
            return "Weak"
        else:
            return "Very Weak"
    
    def get_etf_analysis(self) -> Dict:
        """Analyze AI/robotics ETF performance"""
        try:
            etfs = self.config.get('ai_robotics_etfs', [])
            etf_analysis = {
                'timestamp': datetime.now().isoformat(),
                'etfs': {},
                'recommendations': []
            }
            
            for etf in etfs:
                logger.info(f"Analyzing ETF: {etf}")
                
                # Get current data
                price_data = self.get_real_time_price(etf)
                hist_data = self.get_historical_data(etf, "3mo")
                
                if not hist_data.empty:
                    latest = hist_data.iloc[-1]
                    
                    etf_data = {
                        'symbol': etf,
                        'current_price': price_data.get('current_price', 0),
                        'day_change_percent': price_data.get('day_change_percent', 0),
                        'volume_ratio': price_data.get('volume', 0) / max(price_data.get('avg_volume', 1), 1),
                        'rsi': latest.get('RSI', 50),
                        'above_sma20': price_data.get('current_price', 0) > latest.get('SMA_20', 0),
                        'above_sma50': price_data.get('current_price', 0) > latest.get('SMA_50', 0),
                        'macd_signal': 'Buy' if latest.get('MACD', 0) > latest.get('MACD_Signal', 0) else 'Sell',
                        'recommendation': self.get_etf_recommendation(price_data, latest)
                    }
                    
                    etf_analysis['etfs'][etf] = etf_data
                    
                    # Add to recommendations if strong signal
                    if etf_data['recommendation'] in ['Strong Buy', 'Buy']:
                        etf_analysis['recommendations'].append({
                            'symbol': etf,
                            'action': etf_data['recommendation'],
                            'reason': self.get_recommendation_reason(etf_data)
                        })
            
            return etf_analysis
            
        except Exception as e:
            logger.error(f"Error in ETF analysis: {e}")
            return {}
    
    def get_etf_recommendation(self, price_data: Dict, technical_data: pd.Series) -> str:
        """Generate buy/sell recommendation for ETF"""
        score = 0
        
        # Technical factors
        if price_data.get('day_change_percent', 0) > 1:
            score += 1
        if technical_data.get('RSI', 50) < 70:  # Not overbought
            score += 1
        if technical_data.get('MACD', 0) > technical_data.get('MACD_Signal', 0):
            score += 1
        if price_data.get('current_price', 0) > technical_data.get('SMA_20', 0):
            score += 1
        if price_data.get('volume', 0) > price_data.get('avg_volume', 1):
            score += 1
        
        # Convert score to recommendation
        if score >= 4:
            return "Strong Buy"
        elif score >= 3:
            return "Buy"
        elif score >= 2:
            return "Hold"
        else:
            return "Caution"
    
    def get_recommendation_reason(self, etf_data: Dict) -> str:
        """Generate reason for recommendation"""
        reasons = []
        
        if etf_data['day_change_percent'] > 1:
            reasons.append("strong daily performance")
        if etf_data['above_sma20']:
            reasons.append("above 20-day average")
        if etf_data['macd_signal'] == 'Buy':
            reasons.append("positive MACD signal")
        if etf_data['volume_ratio'] > 1.2:
            reasons.append("high volume")
        
        return ", ".join(reasons) if reasons else "mixed signals"
    
    def generate_market_report(self) -> Dict:
        """Generate comprehensive market analysis report"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'market_overview': {},
                'sector_analysis': self.analyze_sector_performance(),
                'etf_analysis': self.get_etf_analysis(),
                'individual_stocks': {},
                'alerts': [],
                'recommendations': {
                    'buy_signals': [],
                    'sell_signals': [],
                    'watch_list': []
                }
            }
            
            # Analyze individual target stocks
            target_stocks = self.config.get('target_stocks', [])
            for symbol in target_stocks:
                logger.info(f"Analyzing stock: {symbol}")
                
                price_data = self.get_real_time_price(symbol)
                hist_data = self.get_historical_data(symbol, "3mo")
                
                if price_data and not hist_data.empty:
                    latest = hist_data.iloc[-1]
                    
                    stock_analysis = {
                        'price_data': price_data,
                        'technical_indicators': {
                            'rsi': latest.get('RSI', 50),
                            'macd_signal': 'Buy' if latest.get('MACD', 0) > latest.get('MACD_Signal', 0) else 'Sell',
                            'sma_20': latest.get('SMA_20', 0),
                            'sma_50': latest.get('SMA_50', 0),
                            'volume_trend': 'High' if price_data.get('volume', 0) > price_data.get('avg_volume', 1) * 1.5 else 'Normal'
                        },
                        'recommendation': self.get_stock_recommendation(price_data, latest),
                        'risk_level': self.assess_risk_level(price_data, hist_data)
                    }
                    
                    report['individual_stocks'][symbol] = stock_analysis
                    
                    # Generate alerts and recommendations
                    self.process_stock_signals(symbol, stock_analysis, report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating market report: {e}")
            return {}
    
    def get_stock_recommendation(self, price_data: Dict, technical_data: pd.Series) -> str:
        """Generate stock recommendation based on multiple factors"""
        score = 0
        
        # Price momentum
        if price_data.get('day_change_percent', 0) > 2:
            score += 2
        elif price_data.get('day_change_percent', 0) > 0:
            score += 1
        
        # Technical indicators
        rsi = technical_data.get('RSI', 50)
        if 30 < rsi < 70:  # Not oversold or overbought
            score += 1
        elif rsi < 30:  # Oversold - potential buy
            score += 2
        
        # Moving average trends
        current_price = price_data.get('current_price', 0)
        if current_price > technical_data.get('SMA_20', 0):
            score += 1
        if current_price > technical_data.get('SMA_50', 0):
            score += 1
        
        # MACD signal
        if technical_data.get('MACD', 0) > technical_data.get('MACD_Signal', 0):
            score += 1
        
        # Volume confirmation
        if price_data.get('volume', 0) > price_data.get('avg_volume', 1) * 1.2:
            score += 1
        
        # Convert to recommendation
        if score >= 6:
            return "Strong Buy"
        elif score >= 4:
            return "Buy"
        elif score >= 2:
            return "Hold"
        else:
            return "Caution"
    
    def assess_risk_level(self, price_data: Dict, hist_data: pd.DataFrame) -> str:
        """Assess risk level based on volatility and other factors"""
        try:
            if hist_data.empty:
                return "Unknown"
            
            # Calculate volatility
            returns = hist_data['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            
            # Assess based on volatility and other factors
            if volatility > 0.4:
                return "High"
            elif volatility > 0.25:
                return "Medium"
            else:
                return "Low"
                
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return "Unknown"
    
    def process_stock_signals(self, symbol: str, analysis: Dict, report: Dict):
        """Process stock analysis to generate signals and alerts"""
        recommendation = analysis.get('recommendation', 'Hold')
        price_data = analysis.get('price_data', {})
        
        # Buy signals
        if recommendation in ['Strong Buy', 'Buy']:
            report['recommendations']['buy_signals'].append({
                'symbol': symbol,
                'recommendation': recommendation,
                'current_price': price_data.get('current_price', 0),
                'reason': self.get_recommendation_reason(analysis)
            })
        
        # Sell signals (for existing positions)
        elif recommendation == 'Caution':
            report['recommendations']['sell_signals'].append({
                'symbol': symbol,
                'recommendation': 'Consider Selling',
                'current_price': price_data.get('current_price', 0),
                'reason': 'Weak technical signals'
            })
        
        # Alerts for significant movements
        day_change = price_data.get('day_change_percent', 0)
        if abs(day_change) > 5:
            report['alerts'].append({
                'type': 'Price Movement',
                'symbol': symbol,
                'change': day_change,
                'message': f"{symbol} moved {day_change:.2f}% today"
            })
    
    def save_market_report(self, report: Dict, filename: str = None):
        """Save market report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"market_report_{timestamp}.json"
        
        filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
        
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Market report saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving market report: {e}")

def main():
    """Main execution function"""
    collector = MarketDataCollector()
    
    # Generate comprehensive market report
    report = collector.generate_market_report()
    
    # Save report
    collector.save_market_report(report)
    
    # Print summary
    print("\n=== MARKET ANALYSIS SUMMARY ===")
    print(f"Generated: {report['generated_at']}")
    
    # Buy signals
    buy_signals = report.get('recommendations', {}).get('buy_signals', [])
    if buy_signals:
        print("\n🟢 BUY SIGNALS:")
        for signal in buy_signals:
            print(f"  {signal['symbol']}: {signal['recommendation']} at ${signal['current_price']:.2f}")
    
    # Sell signals
    sell_signals = report.get('recommendations', {}).get('sell_signals', [])
    if sell_signals:
        print("\n🔴 SELL SIGNALS:")
        for signal in sell_signals:
            print(f"  {signal['symbol']}: {signal['recommendation']} at ${signal['current_price']:.2f}")
    
    # Alerts
    alerts = report.get('alerts', [])
    if alerts:
        print("\n⚠️ ALERTS:")
        for alert in alerts:
            print(f"  {alert['message']}")
    
    # Sector performance
    sectors = report.get('sector_analysis', {}).get('sectors', {})
    print("\n📊 SECTOR PERFORMANCE:")
    for sector, data in sectors.items():
        print(f"  {sector}: {data.get('avg_change', 0):.2f}% ({data.get('strength_rating', 'Unknown')})")

if __name__ == "__main__":
    main()