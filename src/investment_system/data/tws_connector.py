"""
Interactive Brokers TWS API Connector
Alternative connector using ib_insync library for direct TWS/IB Gateway connection.
"""

try:
    from ib_insync import IB, Stock, Contract, util
    IB_INSYNC_AVAILABLE = True
except ImportError:
    IB_INSYNC_AVAILABLE = False

import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TWSConnector:
    """TWS API connector using ib_insync library"""
    
    def __init__(self, config_file: str = "config/config.json"):
        """Initialize TWS connector"""
        if not IB_INSYNC_AVAILABLE:
            raise ImportError("ib_insync library not installed. Run: pip install ib_insync")
        
        self.config = self.load_config(config_file)
        self.ib = IB()
        self.connected = False
        
        # Connection settings
        self.host = self.config.get('interactive_brokers', {}).get('host', '127.0.0.1')
        self.port = self.config.get('interactive_brokers', {}).get('port', 7497)  # TWS port
        self.client_id = self.config.get('interactive_brokers', {}).get('client_id', 1)
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration file"""
        try:
            config_path = Path(config_file)
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_file}")
            return {}
    
    def connect(self) -> bool:
        """Connect to TWS or IB Gateway"""
        try:
            if self.connected:
                return True
            
            # Try to connect
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = self.ib.isConnected()
            
            if self.connected:
                logger.info(f"✅ Connected to TWS/IB Gateway on {self.host}:{self.port}")
                return True
            else:
                logger.error("❌ Failed to connect to TWS/IB Gateway")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            logger.info("💡 Make sure TWS or IB Gateway is running")
            logger.info(f"💡 Check connection settings: {self.host}:{self.port}")
            return False
    
    def disconnect(self):
        """Disconnect from TWS"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("✅ Disconnected from TWS")
    
    def get_account_summary(self) -> Dict:
        """Get account summary with key financial metrics"""
        if not self.connected:
            if not self.connect():
                return {}
        
        try:
            # Get account summary
            account_summary = self.ib.accountSummary()
            
            summary_dict = {}
            for item in account_summary:
                summary_dict[item.tag] = {
                    'value': item.value,
                    'currency': item.currency,
                    'account': item.account
                }
            
            # Extract key metrics
            key_metrics = {
                'account_id': summary_dict.get('AccountCode', {}).get('value', ''),
                'net_liquidation': float(summary_dict.get('NetLiquidation', {}).get('value', 0)),
                'total_cash': float(summary_dict.get('TotalCashValue', {}).get('value', 0)),
                'buying_power': float(summary_dict.get('BuyingPower', {}).get('value', 0)),
                'excess_liquidity': float(summary_dict.get('ExcessLiquidity', {}).get('value', 0)),
                'maintenance_margin': float(summary_dict.get('MaintMarginReq', {}).get('value', 0)),
                'available_funds': float(summary_dict.get('AvailableFunds', {}).get('value', 0)),
                'currency': summary_dict.get('NetLiquidation', {}).get('currency', 'USD'),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Account summary retrieved: ${key_metrics['net_liquidation']:,.2f}")
            return key_metrics
            
        except Exception as e:
            logger.error(f"❌ Error getting account summary: {e}")
            return {}
    
    def get_portfolio_positions(self) -> List[Dict]:
        """Get current portfolio positions"""
        if not self.connected:
            if not self.connect():
                return []
        
        try:
            # Get portfolio positions
            positions = self.ib.positions()
            
            portfolio_positions = []
            for pos in positions:
                contract = pos.contract
                
                position_info = {
                    'symbol': contract.symbol,
                    'sec_type': contract.secType,
                    'exchange': contract.exchange,
                    'currency': contract.currency,
                    'position': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_price': 0,  # Will be updated with market data
                    'market_value': 0,  # Will be calculated
                    'unrealized_pnl': 0,
                    'contract': contract
                }
                
                # Only include actual positions
                if abs(position_info['position']) > 0:
                    portfolio_positions.append(position_info)
            
            # Get market data for positions
            self._update_position_market_data(portfolio_positions)
            
            logger.info(f"✅ Found {len(portfolio_positions)} positions")
            return portfolio_positions
            
        except Exception as e:
            logger.error(f"❌ Error getting positions: {e}")
            return []
    
    def _update_position_market_data(self, positions: List[Dict]):
        """Update positions with current market data"""
        try:
            contracts = [pos['contract'] for pos in positions]
            
            # Request market data for all contracts
            tickers = self.ib.reqTickers(*contracts)
            
            # Update positions with market data
            for i, ticker in enumerate(tickers):
                if i < len(positions):
                    pos = positions[i]
                    
                    # Get market price
                    market_price = ticker.marketPrice()
                    if market_price and not util.isNan(market_price):
                        pos['market_price'] = market_price
                        pos['market_value'] = pos['position'] * market_price
                        pos['unrealized_pnl'] = (market_price - pos['avg_cost']) * pos['position']
                    
                    # Remove contract object for JSON serialization
                    pos.pop('contract', None)
                    
        except Exception as e:
            logger.warning(f"⚠️  Could not update market data: {e}")
    
    def get_target_stock_data(self) -> Dict:
        """Get market data for target AI/Robotics stocks"""
        if not self.connected:
            if not self.connect():
                return {}
        
        try:
            target_stocks = self.config.get('target_stocks', [])[:10]  # Limit to first 10
            
            # Create stock contracts
            contracts = []
            for symbol in target_stocks:
                stock = Stock(symbol, 'SMART', 'USD')
                contracts.append(stock)
            
            # Get market data
            tickers = self.ib.reqTickers(*contracts)
            
            stock_data = {}
            for i, ticker in enumerate(tickers):
                symbol = target_stocks[i]
                
                stock_data[symbol] = {
                    'symbol': symbol,
                    'bid': ticker.bid if not util.isNan(ticker.bid) else 0,
                    'ask': ticker.ask if not util.isNan(ticker.ask) else 0,
                    'last': ticker.last if not util.isNan(ticker.last) else 0,
                    'close': ticker.close if not util.isNan(ticker.close) else 0,
                    'market_price': ticker.marketPrice() if ticker.marketPrice() and not util.isNan(ticker.marketPrice()) else 0,
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.info(f"✅ Retrieved market data for {len(stock_data)} target stocks")
            return stock_data
            
        except Exception as e:
            logger.error(f"❌ Error getting target stock data: {e}")
            return {}
    
    def get_comprehensive_portfolio_data(self) -> Dict:
        """Get comprehensive portfolio data combining account and positions"""
        try:
            # Get account summary
            account_summary = self.get_account_summary()
            
            # Get positions
            positions = self.get_portfolio_positions()
            
            # Get target stock data
            target_data = self.get_target_stock_data()
            
            # Calculate portfolio analytics
            total_market_value = sum(pos['market_value'] for pos in positions)
            total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in positions)
            
            # Analyze AI/Robotics exposure
            target_stocks = self.config.get('target_stocks', [])
            ai_etfs = self.config.get('ai_robotics_etfs', [])
            ai_symbols = set(target_stocks + ai_etfs)
            
            ai_positions = [pos for pos in positions if pos['symbol'] in ai_symbols]
            ai_market_value = sum(pos['market_value'] for pos in ai_positions)
            ai_allocation_pct = (ai_market_value / total_market_value * 100) if total_market_value > 0 else 0
            
            # Position size analysis
            position_sizes = [(pos['symbol'], pos['market_value'], 
                             pos['market_value']/total_market_value*100 if total_market_value > 0 else 0) 
                            for pos in positions]
            position_sizes.sort(key=lambda x: x[1], reverse=True)  # Sort by market value
            
            comprehensive_data = {
                'account_summary': account_summary,
                'positions': positions,
                'target_stock_data': target_data,
                'portfolio_analytics': {
                    'total_positions': len(positions),
                    'total_market_value': total_market_value,
                    'total_unrealized_pnl': total_unrealized_pnl,
                    'largest_position': position_sizes[0] if position_sizes else None,
                    'position_sizes': position_sizes
                },
                'ai_robotics_analysis': {
                    'ai_positions': ai_positions,
                    'ai_position_count': len(ai_positions),
                    'ai_market_value': ai_market_value,
                    'ai_allocation_percentage': ai_allocation_pct,
                    'target_allocation': 70  # Target AI/Robotics allocation from strategy
                },
                'risk_metrics': {
                    'concentration_risk': max([size[2] for size in position_sizes]) if position_sizes else 0,
                    'diversification_score': len(positions),
                    'cash_percentage': (account_summary.get('total_cash', 0) / account_summary.get('net_liquidation', 1)) * 100
                },
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("✅ Comprehensive portfolio data compiled")
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"❌ Error compiling comprehensive portfolio data: {e}")
            return {}
    
    def sync_with_analysis_system(self) -> bool:
        """Sync live portfolio data with the analysis system configuration"""
        try:
            portfolio_data = self.get_comprehensive_portfolio_data()
            
            if not portfolio_data:
                return False
            
            # Update configuration with live data
            account_summary = portfolio_data['account_summary']
            
            if 'user_profile' not in self.config:
                self.config['user_profile'] = {}
            
            # Update with live portfolio data
            self.config['user_profile'].update({
                'interactive_brokers_balance': account_summary.get('net_liquidation', 0),
                'buying_power': account_summary.get('buying_power', 0),
                'total_cash': account_summary.get('total_cash', 0),
                'last_sync_timestamp': datetime.now().isoformat(),
                'account_id': account_summary.get('account_id', '')
            })
            
            # Add live portfolio positions to config
            self.config['live_portfolio'] = {
                'positions': portfolio_data['positions'],
                'ai_allocation_current': portfolio_data['ai_robotics_analysis']['ai_allocation_percentage'],
                'concentration_risk': portfolio_data['risk_metrics']['concentration_risk'],
                'sync_timestamp': datetime.now().isoformat()
            }
            
            # Save updated configuration
            config_path = Path("config/config.json")
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"✅ Configuration synced with live portfolio data")
            logger.info(f"   Balance: ${account_summary.get('net_liquidation', 0):,.2f}")
            logger.info(f"   Positions: {len(portfolio_data['positions'])}")
            logger.info(f"   AI/Robotics Allocation: {portfolio_data['ai_robotics_analysis']['ai_allocation_percentage']:.1f}%")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error syncing with analysis system: {e}")
            return False


def main():
    """Test TWS connection and portfolio data retrieval"""
    print("=== Interactive Brokers TWS Connection Test ===")
    
    if not IB_INSYNC_AVAILABLE:
        print("❌ ib_insync library not installed")
        print("💡 Install with: pip install ib_insync")
        return
    
    # Initialize connector
    tws = TWSConnector()
    
    try:
        # Test connection
        if tws.connect():
            print("✅ Connected to TWS/IB Gateway")
            
            # Get comprehensive portfolio data
            portfolio_data = tws.get_comprehensive_portfolio_data()
            
            if portfolio_data:
                account = portfolio_data['account_summary']
                analytics = portfolio_data['portfolio_analytics']
                ai_analysis = portfolio_data['ai_robotics_analysis']
                
                print(f"\n📊 Account Summary:")
                print(f"   Net Liquidation: ${account.get('net_liquidation', 0):,.2f}")
                print(f"   Buying Power: ${account.get('buying_power', 0):,.2f}")
                print(f"   Total Cash: ${account.get('total_cash', 0):,.2f}")
                
                print(f"\n📈 Portfolio Analytics:")
                print(f"   Total Positions: {analytics['total_positions']}")
                print(f"   Market Value: ${analytics['total_market_value']:,.2f}")
                print(f"   Unrealized P&L: ${analytics['total_unrealized_pnl']:,.2f}")
                
                print(f"\n🤖 AI/Robotics Analysis:")
                print(f"   AI Positions: {ai_analysis['ai_position_count']}")
                print(f"   AI Market Value: ${ai_analysis['ai_market_value']:,.2f}")
                print(f"   AI Allocation: {ai_analysis['ai_allocation_percentage']:.1f}%")
                print(f"   Target Allocation: {ai_analysis['target_allocation']}%")
                
                # Show top positions
                if analytics['position_sizes']:
                    print(f"\n📋 Top Positions:")
                    for symbol, value, pct in analytics['position_sizes'][:5]:
                        print(f"   {symbol}: ${value:,.2f} ({pct:.1f}%)")
                
                # Sync with analysis system
                if tws.sync_with_analysis_system():
                    print("\n✅ Portfolio data synced with analysis system")
                
            else:
                print("❌ Failed to retrieve portfolio data")
        else:
            print("❌ Failed to connect to TWS/IB Gateway")
            print("💡 Make sure TWS or IB Gateway is running with API enabled")
    
    finally:
        tws.disconnect()


if __name__ == "__main__":
    main()