"""
Smart Money Tracking Module
Monitors institutional investors, hedge funds, and insider movements
"""

import requests
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartMoneyTracker:
    def __init__(self, config_file: str = None):
        """Initialize with API keys and configuration"""
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Investment Research Tool 1.0'
        })
        
    def load_config(self, config_file: str) -> Dict:
        """Load API keys and settings from config file"""
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                logger.warning(f"Config file {config_file} not found, using defaults")
        
        # Default configuration structure
        return {
            "whalewisdom": {
                "api_key": "YOUR_WHALEWISDOM_API_KEY",
                "base_url": "https://api.whalewisdom.com"
            },
            "alpha_vantage": {
                "api_key": "YOUR_ALPHA_VANTAGE_API_KEY",
                "base_url": "https://www.alphavantage.co"
            },
            "target_funds": [
                "ARK Invest",
                "Tiger Global Management", 
                "Coatue Management",
                "Whale Rock Capital",
                "Berkshire Hathaway",
                "Bridgewater Associates",
                "Renaissance Technologies",
                "RA Capital",
                "Point72 Asset Management",
                "Citadel LLC"
            ],
            "target_stocks": [
                "NVDA", "MSFT", "TSLA", "DE", "TSM",
                "AMZN", "GOOGL", "META", "AAPL", "CRM"
            ],
            "ai_robotics_etfs": [
                "KROP", "BOTZ", "SOXX", "ARKQ", "ROBO"
            ]
        }
    
    def get_institutional_holdings(self, symbol: str) -> Dict:
        """Get institutional holdings for a specific stock"""
        try:
            # Using SEC EDGAR API (free alternative to WhaleWisdom)
            url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self.get_cik(symbol)}.json"
            
            headers = {
                'User-Agent': 'Investment Research ivan@example.com',
                'Accept-Encoding': 'gzip, deflate',
                'Host': 'data.sec.gov'
            }
            
            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching institutional data for {symbol}: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error in get_institutional_holdings for {symbol}: {e}")
            return {}
    
    def get_cik(self, symbol: str) -> str:
        """Get CIK number for stock symbol"""
        # This would typically query SEC company list
        # For now, using common CIKs for major stocks
        cik_mapping = {
            "NVDA": "0001045810",
            "MSFT": "0000789019", 
            "TSLA": "0001318605",
            "AAPL": "0000320193",
            "AMZN": "0001018724"
        }
        return cik_mapping.get(symbol, "0000000000")
    
    def scrape_whalewisdom_free(self, fund_name: str) -> Dict:
        """Scrape public WhaleWisdom data (free tier)"""
        try:
            # WhaleWisdom public pages
            base_url = "https://whalewisdom.com"
            search_url = f"{base_url}/filer_search"
            
            # Search for fund
            search_data = {
                'search_term': fund_name,
                'type': 'fund'
            }
            
            response = self.session.get(search_url, params=search_data)
            if response.status_code == 200:
                # Parse HTML response to extract fund data
                # This would require BeautifulSoup for proper parsing
                return {"status": "success", "data": "Fund data would be parsed here"}
            else:
                logger.error(f"Error searching for fund {fund_name}")
                return {}
                
        except Exception as e:
            logger.error(f"Error in scrape_whalewisdom_free: {e}")
            return {}
    
    def get_insider_trading(self, symbol: str) -> List[Dict]:
        """Get insider trading data from SEC filings"""
        try:
            # SEC EDGAR insider trading forms (Forms 3, 4, 5)
            url = f"https://data.sec.gov/submissions/CIK{self.get_cik(symbol)}.json"
            
            headers = {
                'User-Agent': 'Investment Research ivan@example.com',
                'Accept-Encoding': 'gzip, deflate',
                'Host': 'data.sec.gov'
            }
            
            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                # Filter for insider trading forms
                insider_filings = []
                recent_filings = data.get('filings', {}).get('recent', {})
                
                for i, form in enumerate(recent_filings.get('form', [])):
                    if form in ['3', '4', '5']:  # Insider trading forms
                        filing = {
                            'form': form,
                            'filing_date': recent_filings.get('filingDate', [])[i],
                            'accepted_date': recent_filings.get('acceptanceDateTime', [])[i],
                            'accession_number': recent_filings.get('accessionNumber', [])[i]
                        }
                        insider_filings.append(filing)
                
                return insider_filings[:10]  # Return most recent 10
            else:
                logger.error(f"Error fetching insider data for {symbol}")
                return []
                
        except Exception as e:
            logger.error(f"Error in get_insider_trading: {e}")
            return []
    
    def analyze_smart_money_moves(self, symbol: str) -> Dict:
        """Analyze recent smart money movements for a stock"""
        try:
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'institutional_holdings': self.get_institutional_holdings(symbol),
                'insider_trading': self.get_insider_trading(symbol),
                'fund_movements': {},
                'sentiment_score': 0,
                'buy_sell_ratio': 0,
                'confidence_level': 'low'
            }
            
            # Analyze institutional holdings changes
            institutional_data = analysis['institutional_holdings']
            if institutional_data:
                # Calculate sentiment based on recent institutional activity
                analysis['sentiment_score'] = self.calculate_institutional_sentiment(institutional_data)
            
            # Analyze insider trading patterns
            insider_data = analysis['insider_trading']
            if insider_data:
                analysis['buy_sell_ratio'] = self.calculate_insider_ratio(insider_data)
            
            # Determine confidence level
            analysis['confidence_level'] = self.determine_confidence(
                analysis['sentiment_score'], 
                analysis['buy_sell_ratio']
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in analyze_smart_money_moves: {e}")
            return {}
    
    def calculate_institutional_sentiment(self, data: Dict) -> float:
        """Calculate sentiment score from institutional data"""
        # Placeholder sentiment calculation
        # In real implementation, would analyze holdings changes
        return 0.0
    
    def calculate_insider_ratio(self, insider_data: List[Dict]) -> float:
        """Calculate buy/sell ratio from insider trading"""
        # Placeholder calculation
        # Would analyze actual transaction types and amounts
        return 1.0
    
    def determine_confidence(self, sentiment: float, ratio: float) -> str:
        """Determine confidence level based on multiple factors"""
        if sentiment > 0.7 and ratio > 1.5:
            return 'high'
        elif sentiment > 0.5 and ratio > 1.0:
            return 'medium'
        else:
            return 'low'
    
    def generate_smart_money_report(self, symbols: List[str]) -> Dict:
        """Generate comprehensive smart money report for multiple stocks"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'analysis_count': len(symbols),
            'stocks': {},
            'summary': {
                'high_confidence_buys': [],
                'medium_confidence_buys': [],
                'potential_sells': [],
                'trending_sectors': []
            }
        }
        
        for symbol in symbols:
            logger.info(f"Analyzing smart money for {symbol}")
            analysis = self.analyze_smart_money_moves(symbol)
            report['stocks'][symbol] = analysis
            
            # Categorize based on confidence and sentiment
            if analysis.get('confidence_level') == 'high':
                if analysis.get('sentiment_score', 0) > 0.6:
                    report['summary']['high_confidence_buys'].append(symbol)
            elif analysis.get('confidence_level') == 'medium':
                if analysis.get('sentiment_score', 0) > 0.5:
                    report['summary']['medium_confidence_buys'].append(symbol)
            
            if analysis.get('sentiment_score', 0) < 0.3:
                report['summary']['potential_sells'].append(symbol)
        
        return report
    
    def save_report(self, report: Dict, filename: str = None):
        """Save report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"smart_money_report_{timestamp}.json"
        
        filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
        
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")

def main():
    """Main execution function"""
    tracker = SmartMoneyTracker()
    
    # Load target stocks from config
    target_stocks = tracker.config.get('target_stocks', ['NVDA', 'MSFT', 'TSLA'])
    
    # Generate smart money report
    report = tracker.generate_smart_money_report(target_stocks)
    
    # Save report
    tracker.save_report(report)
    
    # Print summary
    print("\n=== SMART MONEY ANALYSIS SUMMARY ===")
    print(f"Generated: {report['generated_at']}")
    print(f"Stocks analyzed: {report['analysis_count']}")
    print(f"High confidence buys: {', '.join(report['summary']['high_confidence_buys'])}")
    print(f"Medium confidence buys: {', '.join(report['summary']['medium_confidence_buys'])}")
    print(f"Potential sells: {', '.join(report['summary']['potential_sells'])}")

if __name__ == "__main__":
    main()