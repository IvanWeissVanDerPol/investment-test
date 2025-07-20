"""
Advanced Market Analyzer
Implements options flow, forex impact, sector rotation, bond yields, and earnings calendar
"""

import json
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedMarketAnalyzer:
    def __init__(self, config_file: str = "config.json"):
        """Initialize advanced market analyzer"""
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Investment Research Tool 1.0'
        })
        
        # Market tickers for analysis
        self.forex_tickers = {
            'DXY': 'UUP',      # USD ETF (more reliable than ^DXY)
            'EURUSD': 'FXE',   # Euro ETF
            'JPYUSD': 'FXY',   # Yen ETF
            'GBPUSD': 'FXB'    # British Pound ETF
        }
        
        self.bond_tickers = {
            '10Y_Treasury': '^TNX',
            '2Y_Treasury': '^IRX',
            '30Y_Treasury': '^TYX'
        }
        
        self.sector_etfs = {
            'Technology': 'XLK',
            'Healthcare': 'XLV', 
            'Financials': 'XLF',
            'Energy': 'XLE',
            'Consumer_Discretionary': 'XLY',
            'Industrials': 'XLI',
            'Materials': 'XLB',
            'Utilities': 'XLU',
            'Real_Estate': 'XLRE',
            'Consumer_Staples': 'XLP',
            'Communications': 'XLC'
        }
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return {}
    
    def analyze_options_flow(self, symbol: str) -> Dict:
        """Analyze unusual options activity - simplified version using volume data"""
        try:
            logger.info(f"Analyzing options flow for {symbol}")
            
            ticker = yf.Ticker(symbol)
            options_dates = ticker.options
            
            if not options_dates:
                return {'symbol': symbol, 'unusual_activity': False, 'analysis': 'No options data available'}
            
            # Get nearest expiration options
            nearest_exp = options_dates[0]
            calls = ticker.option_chain(nearest_exp).calls
            puts = ticker.option_chain(nearest_exp).puts
            
            if calls.empty or puts.empty:
                return {'symbol': symbol, 'unusual_activity': False, 'analysis': 'No options data available'}
            
            # Calculate call/put volume ratio
            total_call_volume = calls['volume'].fillna(0).sum()
            total_put_volume = puts['volume'].fillna(0).sum()
            
            call_put_ratio = total_call_volume / max(total_put_volume, 1)
            
            # Calculate open interest
            total_call_oi = calls['openInterest'].fillna(0).sum()
            total_put_oi = puts['openInterest'].fillna(0).sum()
            
            # Identify unusual activity patterns
            unusual_activity = False
            signals = []
            
            if call_put_ratio > 2.0:
                unusual_activity = True
                signals.append("High call volume - bullish sentiment")
            elif call_put_ratio < 0.5:
                unusual_activity = True
                signals.append("High put volume - bearish sentiment")
            
            # Check for large volume compared to open interest
            if total_call_volume > total_call_oi * 0.5:
                unusual_activity = True
                signals.append("High call volume vs open interest")
            
            if total_put_volume > total_put_oi * 0.5:
                unusual_activity = True
                signals.append("High put volume vs open interest")
            
            return {
                'symbol': symbol,
                'expiration': nearest_exp,
                'call_put_volume_ratio': round(call_put_ratio, 2),
                'total_call_volume': int(total_call_volume),
                'total_put_volume': int(total_put_volume),
                'total_call_oi': int(total_call_oi),
                'total_put_oi': int(total_put_oi),
                'unusual_activity': unusual_activity,
                'signals': signals,
                'sentiment': 'bullish' if call_put_ratio > 1.2 else 'bearish' if call_put_ratio < 0.8 else 'neutral'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing options flow for {symbol}: {e}")
            return {'symbol': symbol, 'unusual_activity': False, 'error': str(e)}
    
    def analyze_forex_impact(self, symbols: List[str]) -> Dict:
        """Analyze USD strength effects on international stocks"""
        try:
            logger.info("Analyzing forex impact on portfolio")
            
            # Get USD ETF data (more reliable than index)
            usd_etf = yf.Ticker(self.forex_tickers['DXY'])
            usd_hist = usd_etf.history(period="1mo")
            
            if usd_hist.empty:
                # Fallback: use TLT inverse as USD proxy
                logger.warning("USD ETF failed, using TLT inverse as proxy")
                tlt_ticker = yf.Ticker('TLT')
                tlt_hist = tlt_ticker.history(period="1mo")
                if not tlt_hist.empty:
                    # Use inverse of TLT as USD strength proxy
                    usd_hist = tlt_hist.copy()
                    base_price = tlt_hist['Close'].iloc[0]
                    usd_hist['Close'] = base_price * 2 - tlt_hist['Close']  # Inverse relationship
                else:
                    return {'error': 'Could not fetch any USD proxy data'}
            
            # Calculate USD strength trend
            usd_current = usd_hist['Close'].iloc[-1]
            usd_30d_avg = usd_hist['Close'].mean()
            usd_strength = (usd_current - usd_30d_avg) / usd_30d_avg * 100
            
            # Analyze impact on different stock categories
            forex_analysis = {
                'usd_proxy_current': round(usd_current, 2),
                'usd_strength_vs_30d': round(usd_strength, 2),
                'usd_trend': 'strengthening' if usd_strength > 1 else 'weakening' if usd_strength < -1 else 'stable',
                'stock_impacts': {}
            }
            
            # Define international exposure for common stocks
            international_exposure = {
                'TSM': {'region': 'Asia', 'currency_sensitivity': 'high'},
                'NVDA': {'region': 'Global', 'currency_sensitivity': 'medium'},
                'MSFT': {'region': 'Global', 'currency_sensitivity': 'low'},
                'AAPL': {'region': 'Global', 'currency_sensitivity': 'medium'},
                'GOOGL': {'region': 'Global', 'currency_sensitivity': 'low'},
                'TSLA': {'region': 'Global', 'currency_sensitivity': 'medium'},
                'META': {'region': 'Global', 'currency_sensitivity': 'low'}
            }
            
            for symbol in symbols:
                if symbol in international_exposure:
                    exposure = international_exposure[symbol]
                    sensitivity = exposure['currency_sensitivity']
                    
                    # Calculate expected impact
                    if sensitivity == 'high':
                        impact_factor = 0.8
                    elif sensitivity == 'medium':
                        impact_factor = 0.4
                    else:
                        impact_factor = 0.1
                    
                    expected_impact = -usd_strength * impact_factor  # Negative because strong USD hurts international stocks
                    
                    forex_analysis['stock_impacts'][symbol] = {
                        'region': exposure['region'],
                        'currency_sensitivity': sensitivity,
                        'expected_impact_pct': round(expected_impact, 2),
                        'recommendation': self.get_forex_recommendation(expected_impact)
                    }
            
            return forex_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing forex impact: {e}")
            return {'error': str(e)}
    
    def get_forex_recommendation(self, expected_impact: float) -> str:
        """Get forex-based recommendation"""
        if expected_impact > 2:
            return "Strong positive forex tailwind"
        elif expected_impact > 0.5:
            return "Moderate positive forex impact"
        elif expected_impact > -0.5:
            return "Neutral forex impact"
        elif expected_impact > -2:
            return "Moderate negative forex headwind"
        else:
            return "Strong negative forex headwind"
    
    def detect_sector_rotation(self) -> Dict:
        """Identify when money flows between sectors"""
        try:
            logger.info("Detecting sector rotation patterns")
            
            rotation_analysis = {
                'analysis_date': datetime.now().isoformat(),
                'sector_performance': {},
                'rotation_signals': [],
                'top_performers': [],
                'underperformers': [],
                'rotation_strength': 'low'
            }
            
            # Get sector ETF performance
            for sector, etf in self.sector_etfs.items():
                try:
                    ticker = yf.Ticker(etf)
                    hist = ticker.history(period="1mo")
                    
                    if not hist.empty:
                        # Calculate performance metrics
                        current_price = hist['Close'].iloc[-1]
                        price_1w_ago = hist['Close'].iloc[-5] if len(hist) >= 5 else hist['Close'].iloc[0]
                        price_1m_ago = hist['Close'].iloc[0]
                        
                        weekly_return = (current_price - price_1w_ago) / price_1w_ago * 100
                        monthly_return = (current_price - price_1m_ago) / price_1m_ago * 100
                        
                        # Volume analysis
                        avg_volume = hist['Volume'].mean()
                        recent_volume = hist['Volume'].tail(5).mean()
                        volume_ratio = recent_volume / avg_volume
                        
                        rotation_analysis['sector_performance'][sector] = {
                            'etf': etf,
                            'weekly_return': round(weekly_return, 2),
                            'monthly_return': round(monthly_return, 2),
                            'volume_ratio': round(volume_ratio, 2),
                            'current_price': round(current_price, 2)
                        }
                        
                except Exception as e:
                    logger.warning(f"Could not analyze sector {sector}: {e}")
                    continue
            
            # Identify rotation patterns
            if rotation_analysis['sector_performance']:
                # Sort by weekly performance
                weekly_performers = sorted(
                    rotation_analysis['sector_performance'].items(),
                    key=lambda x: x[1]['weekly_return'],
                    reverse=True
                )
                
                # Top and bottom performers
                rotation_analysis['top_performers'] = weekly_performers[:3]
                rotation_analysis['underperformers'] = weekly_performers[-3:]
                
                # Calculate rotation strength
                top_return = weekly_performers[0][1]['weekly_return']
                bottom_return = weekly_performers[-1][1]['weekly_return']
                performance_spread = top_return - bottom_return
                
                if performance_spread > 5:
                    rotation_analysis['rotation_strength'] = 'high'
                elif performance_spread > 2:
                    rotation_analysis['rotation_strength'] = 'medium'
                else:
                    rotation_analysis['rotation_strength'] = 'low'
                
                # Generate rotation signals
                for sector, data in weekly_performers[:2]:  # Top 2 performers
                    if data['weekly_return'] > 3 and data['volume_ratio'] > 1.2:
                        rotation_analysis['rotation_signals'].append(
                            f"Money flowing INTO {sector} - strong performance with high volume"
                        )
                
                for sector, data in weekly_performers[-2:]:  # Bottom 2 performers
                    if data['weekly_return'] < -3 and data['volume_ratio'] > 1.2:
                        rotation_analysis['rotation_signals'].append(
                            f"Money flowing OUT OF {sector} - weak performance with high volume"
                        )
            
            return rotation_analysis
            
        except Exception as e:
            logger.error(f"Error detecting sector rotation: {e}")
            return {'error': str(e)}
    
    def get_earnings_calendar(self, symbols: List[str]) -> Dict:
        """Get earnings calendar for target stocks"""
        try:
            logger.info("Fetching earnings calendar")
            
            earnings_calendar = {
                'generated_at': datetime.now().isoformat(),
                'upcoming_earnings': {},
                'recent_earnings': {},
                'earnings_alerts': []
            }
            
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    # Get earnings dates (if available)
                    earnings_date = info.get('earningsDate')
                    last_earnings = info.get('lastEarningsDate')
                    
                    earnings_info = {
                        'symbol': symbol,
                        'next_earnings': earnings_date,
                        'last_earnings': last_earnings,
                        'earnings_time': info.get('earningsTime', 'Unknown'),
                        'estimate_eps': info.get('forwardEps'),
                        'trailing_eps': info.get('trailingEps'),
                        'pe_ratio': info.get('trailingPE'),
                        'forward_pe': info.get('forwardPE')
                    }
                    
                    # Check if earnings are upcoming (within next 30 days)
                    if earnings_date:
                        try:
                            if isinstance(earnings_date, list) and earnings_date:
                                earnings_dt = earnings_date[0] if hasattr(earnings_date[0], 'date') else None
                            else:
                                earnings_dt = earnings_date if hasattr(earnings_date, 'date') else None
                            
                            if earnings_dt:
                                days_to_earnings = (earnings_dt.date() - datetime.now().date()).days
                                earnings_info['days_until_earnings'] = days_to_earnings
                                
                                if 0 <= days_to_earnings <= 30:
                                    earnings_calendar['upcoming_earnings'][symbol] = earnings_info
                                    
                                    # Generate alerts for upcoming earnings
                                    if days_to_earnings <= 7:
                                        earnings_calendar['earnings_alerts'].append({
                                            'symbol': symbol,
                                            'type': 'upcoming_earnings',
                                            'days_until': days_to_earnings,
                                            'message': f"{symbol} reports earnings in {days_to_earnings} days"
                                        })
                        except:
                            pass
                    
                    # Check for recent earnings (within last 30 days)
                    if last_earnings:
                        try:
                            if hasattr(last_earnings, 'date'):
                                days_since_earnings = (datetime.now().date() - last_earnings.date()).days
                                if 0 <= days_since_earnings <= 30:
                                    earnings_calendar['recent_earnings'][symbol] = earnings_info
                        except:
                            pass
                
                except Exception as e:
                    logger.warning(f"Could not get earnings info for {symbol}: {e}")
                    continue
            
            return earnings_calendar
            
        except Exception as e:
            logger.error(f"Error fetching earnings calendar: {e}")
            return {'error': str(e)}
    
    def analyze_bond_yield_impact(self, symbols: List[str]) -> Dict:
        """Analyze 10-year treasury effects on growth stocks"""
        try:
            logger.info("Analyzing bond yield impact")
            
            # Get 10-year treasury data
            tnx = yf.Ticker(self.bond_tickers['10Y_Treasury'])
            tnx_hist = tnx.history(period="3mo")
            
            if tnx_hist.empty:
                return {'error': 'Could not fetch treasury data'}
            
            # Calculate yield metrics
            current_yield = tnx_hist['Close'].iloc[-1]
            yield_30d_ago = tnx_hist['Close'].iloc[-20] if len(tnx_hist) >= 20 else tnx_hist['Close'].iloc[0]
            yield_change = current_yield - yield_30d_ago
            yield_change_pct = (yield_change / yield_30d_ago) * 100
            
            bond_analysis = {
                'current_10y_yield': round(current_yield, 2),
                'yield_change_30d': round(yield_change, 2),
                'yield_change_pct_30d': round(yield_change_pct, 2),
                'yield_trend': self.classify_yield_trend(yield_change_pct),
                'stock_impacts': {}
            }
            
            # Define growth stock sensitivity to yield changes
            growth_sensitivity = {
                'NVDA': 'high',
                'TSLA': 'high', 
                'META': 'high',
                'GOOGL': 'medium',
                'MSFT': 'medium',
                'AAPL': 'low',
                'CRM': 'high',
                'PLTR': 'high',
                'SNOW': 'high'
            }
            
            for symbol in symbols:
                if symbol in growth_sensitivity:
                    sensitivity = growth_sensitivity[symbol]
                    
                    # Calculate expected impact
                    if sensitivity == 'high':
                        impact_factor = -1.5  # High sensitivity to yield changes
                    elif sensitivity == 'medium':
                        impact_factor = -0.8
                    else:
                        impact_factor = -0.3
                    
                    expected_impact = yield_change_pct * impact_factor
                    
                    bond_analysis['stock_impacts'][symbol] = {
                        'yield_sensitivity': sensitivity,
                        'expected_impact_pct': round(expected_impact, 2),
                        'recommendation': self.get_yield_recommendation(expected_impact, yield_change_pct)
                    }
            
            return bond_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing bond yield impact: {e}")
            return {'error': str(e)}
    
    def classify_yield_trend(self, yield_change_pct: float) -> str:
        """Classify yield trend"""
        if yield_change_pct > 10:
            return "rapidly_rising"
        elif yield_change_pct > 5:
            return "rising"
        elif yield_change_pct > -5:
            return "stable"
        elif yield_change_pct > -10:
            return "falling"
        else:
            return "rapidly_falling"
    
    def get_yield_recommendation(self, expected_impact: float, yield_change: float) -> str:
        """Get yield-based recommendation"""
        if yield_change > 5:  # Rising yields
            return "Caution: Rising yields pressure growth stocks"
        elif yield_change < -5:  # Falling yields
            return "Positive: Falling yields support growth stocks"
        else:
            return "Neutral: Stable yield environment"
    
    def generate_comprehensive_analysis(self, symbols: List[str]) -> Dict:
        """Generate comprehensive advanced market analysis"""
        try:
            logger.info("Generating comprehensive advanced analysis")
            
            analysis = {
                'generated_at': datetime.now().isoformat(),
                'symbols_analyzed': symbols,
                'options_flow': {},
                'forex_impact': self.analyze_forex_impact(symbols),
                'sector_rotation': self.detect_sector_rotation(),
                'earnings_calendar': self.get_earnings_calendar(symbols),
                'bond_yield_impact': self.analyze_bond_yield_impact(symbols),
                'market_summary': {},
                'investment_implications': []
            }
            
            # Analyze options flow for key stocks
            key_stocks = symbols[:5]  # Limit to top 5 for performance
            for symbol in key_stocks:
                print(f"   Analyzing options flow for {symbol}...")
                analysis['options_flow'][symbol] = self.analyze_options_flow(symbol)
                time.sleep(0.5)  # Rate limiting
            
            # Generate market summary
            analysis['market_summary'] = self.create_market_summary(analysis)
            
            # Generate investment implications
            analysis['investment_implications'] = self.generate_investment_implications(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating comprehensive analysis: {e}")
            return {'error': str(e)}
    
    def create_market_summary(self, analysis: Dict) -> Dict:
        """Create overall market environment summary"""
        summary = {
            'market_environment': 'neutral',
            'key_factors': [],
            'risk_level': 'medium',
            'opportunities': [],
            'threats': []
        }
        
        try:
            # Analyze forex impact
            forex = analysis.get('forex_impact', {})
            if forex.get('usd_trend') == 'strengthening':
                summary['key_factors'].append("Strong USD pressuring international stocks")
                summary['threats'].append("USD strength")
            elif forex.get('usd_trend') == 'weakening':
                summary['key_factors'].append("Weak USD supporting international stocks")
                summary['opportunities'].append("USD weakness")
            
            # Analyze sector rotation
            rotation = analysis.get('sector_rotation', {})
            if rotation.get('rotation_strength') == 'high':
                summary['key_factors'].append("High sector rotation activity")
                top_sector = rotation.get('top_performers', [])
                if top_sector:
                    summary['opportunities'].append(f"Strong performance in {top_sector[0][0]}")
            
            # Analyze bond yields
            bonds = analysis.get('bond_yield_impact', {})
            yield_trend = bonds.get('yield_trend', 'stable')
            if yield_trend in ['rising', 'rapidly_rising']:
                summary['key_factors'].append("Rising bond yields pressuring growth stocks")
                summary['threats'].append("Rising yields")
                summary['risk_level'] = 'high'
            elif yield_trend in ['falling', 'rapidly_falling']:
                summary['opportunities'].append("Falling yields supporting growth stocks")
            
            # Analyze earnings calendar
            earnings = analysis.get('earnings_calendar', {})
            upcoming_count = len(earnings.get('upcoming_earnings', {}))
            if upcoming_count > 3:
                summary['key_factors'].append(f"{upcoming_count} companies reporting earnings soon")
                summary['opportunities'].append("Multiple earnings catalysts")
            
            # Overall environment assessment
            threat_count = len(summary['threats'])
            opportunity_count = len(summary['opportunities'])
            
            if opportunity_count > threat_count + 1:
                summary['market_environment'] = 'favorable'
            elif threat_count > opportunity_count + 1:
                summary['market_environment'] = 'challenging'
            else:
                summary['market_environment'] = 'neutral'
                
        except Exception as e:
            logger.error(f"Error creating market summary: {e}")
        
        return summary
    
    def generate_investment_implications(self, analysis: Dict) -> List[Dict]:
        """Generate actionable investment implications"""
        implications = []
        
        try:
            # Options flow implications
            options_data = analysis.get('options_flow', {})
            for symbol, data in options_data.items():
                if data.get('unusual_activity'):
                    sentiment = data.get('sentiment', 'neutral')
                    implications.append({
                        'type': 'options_activity',
                        'symbol': symbol,
                        'action': f"Monitor {symbol} for {sentiment} momentum",
                        'reason': f"Unusual options activity detected - {sentiment} sentiment",
                        'priority': 'medium'
                    })
            
            # Forex implications
            forex = analysis.get('forex_impact', {})
            stock_impacts = forex.get('stock_impacts', {})
            for symbol, impact in stock_impacts.items():
                if abs(impact.get('expected_impact_pct', 0)) > 1:
                    implications.append({
                        'type': 'forex_impact',
                        'symbol': symbol,
                        'action': impact.get('recommendation', ''),
                        'reason': f"USD impact: {impact.get('expected_impact_pct', 0)}%",
                        'priority': 'low'
                    })
            
            # Sector rotation implications
            rotation = analysis.get('sector_rotation', {})
            if rotation.get('rotation_strength') in ['medium', 'high']:
                top_performers = rotation.get('top_performers', [])
                for sector, data in top_performers[:2]:
                    implications.append({
                        'type': 'sector_rotation',
                        'symbol': data.get('etf'),
                        'action': f"Consider {sector} exposure",
                        'reason': f"Strong sector performance: {data.get('weekly_return', 0)}% weekly",
                        'priority': 'medium'
                    })
            
            # Earnings implications
            earnings = analysis.get('earnings_calendar', {})
            for alert in earnings.get('earnings_alerts', []):
                implications.append({
                    'type': 'earnings_event',
                    'symbol': alert.get('symbol'),
                    'action': f"Prepare for earnings volatility",
                    'reason': alert.get('message', ''),
                    'priority': 'high' if alert.get('days_until', 30) <= 3 else 'medium'
                })
            
            # Bond yield implications
            bonds = analysis.get('bond_yield_impact', {})
            yield_trend = bonds.get('yield_trend', 'stable')
            if yield_trend in ['rising', 'rapidly_rising']:
                implications.append({
                    'type': 'yield_environment',
                    'symbol': 'GROWTH_STOCKS',
                    'action': 'Reduce growth stock exposure',
                    'reason': f"Rising yields ({bonds.get('current_10y_yield', 0)}%) pressure growth stocks",
                    'priority': 'high'
                })
            elif yield_trend in ['falling', 'rapidly_falling']:
                implications.append({
                    'type': 'yield_environment',
                    'symbol': 'GROWTH_STOCKS',
                    'action': 'Increase growth stock exposure',
                    'reason': f"Falling yields ({bonds.get('current_10y_yield', 0)}%) support growth stocks",
                    'priority': 'medium'
                })
        
        except Exception as e:
            logger.error(f"Error generating investment implications: {e}")
        
        return implications
    
    def save_advanced_analysis(self, analysis: Dict, filename: str = None):
        """Save advanced analysis to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"advanced_market_analysis_{timestamp}.json"
        
        filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, default=str)
            logger.info(f"Advanced analysis saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving advanced analysis: {e}")

def main():
    """Main execution function"""
    analyzer = AdvancedMarketAnalyzer()
    
    # Target stocks for advanced analysis
    target_stocks = [
        "NVDA", "MSFT", "TSLA", "DE", "TSM",
        "AMZN", "GOOGL", "META", "AAPL", "CRM"
    ]
    
    print("Starting Advanced Market Analysis...")
    print("This includes: Options Flow, Forex Impact, Sector Rotation, Bond Yields, Earnings Calendar")
    
    # Generate comprehensive analysis
    analysis = analyzer.generate_comprehensive_analysis(target_stocks)
    
    # Save analysis
    analyzer.save_advanced_analysis(analysis)
    
    # Print summary
    print("\n=== ADVANCED MARKET ANALYSIS SUMMARY ===")
    
    market_summary = analysis.get('market_summary', {})
    print(f"Market Environment: {market_summary.get('market_environment', 'unknown').upper()}")
    print(f"Risk Level: {market_summary.get('risk_level', 'unknown').upper()}")
    
    # Key factors
    key_factors = market_summary.get('key_factors', [])
    if key_factors:
        print(f"\nKey Market Factors:")
        for factor in key_factors:
            print(f"  • {factor}")
    
    # Investment implications
    implications = analysis.get('investment_implications', [])
    if implications:
        print(f"\nInvestment Implications:")
        for impl in implications[:5]:  # Top 5
            print(f"  {impl.get('priority', 'medium').upper()}: {impl.get('action', '')} ({impl.get('symbol', '')})")
    
    # Forex impact
    forex = analysis.get('forex_impact', {})
    if forex:
        print(f"\nUSD Impact: {forex.get('usd_trend', 'unknown')} ({forex.get('usd_strength_vs_30d', 0):.1f}%)")
    
    # Sector rotation
    rotation = analysis.get('sector_rotation', {})
    if rotation.get('top_performers'):
        top_sector = rotation['top_performers'][0]
        print(f"Top Performing Sector: {top_sector[0]} ({top_sector[1].get('weekly_return', 0):.1f}% weekly)")
    
    # Bond yields
    bonds = analysis.get('bond_yield_impact', {})
    if bonds:
        print(f"10Y Treasury: {bonds.get('current_10y_yield', 0):.2f}% ({bonds.get('yield_trend', 'stable')})")

if __name__ == "__main__":
    main()