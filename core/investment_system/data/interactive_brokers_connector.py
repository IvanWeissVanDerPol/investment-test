"""
Interactive Brokers API Connector
Connects to Interactive Brokers to fetch real account data, positions, and balances.
"""

import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class IBKRConnector:
    """Interactive Brokers API connector for real-time account data"""
    
    def __init__(self, config_file: str = "config/config.json"):
        """Initialize IBKR connector with configuration"""
        self.config = self.load_config(config_file)
        self.base_url = "https://localhost:5000/v1/api"  # Default IB Gateway URL
        self.session = requests.Session()
        self.account_id = None
        self.authenticated = False
        
        # Load IBKR specific config
        self.ibkr_config = self.config.get('interactive_brokers', {})
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration file"""
        try:
            config_path = Path(config_file)
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_file}")
            return {}
    
    def authenticate(self) -> bool:
        """Authenticate with Interactive Brokers Gateway"""
        try:
            # Check if IB Gateway is running
            response = self.session.get(f"{self.base_url}/portal/iserver/auth/status")
            
            if response.status_code == 200:
                auth_data = response.json()
                if auth_data.get('authenticated', False):
                    self.authenticated = True
                    logger.info("✅ Already authenticated with IB Gateway")
                    return True
                else:
                    logger.warning("⚠️  IB Gateway running but not authenticated")
                    return self._perform_authentication()
            else:
                logger.error("❌ IB Gateway not accessible. Please start IB Gateway or TWS.")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to IB Gateway. Please ensure it's running on localhost:5000")
            return False
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def _perform_authentication(self) -> bool:
        """Perform authentication flow with IB Gateway"""
        try:
            # Trigger authentication
            auth_response = self.session.post(f"{self.base_url}/portal/iserver/auth/ssodh/init")
            
            if auth_response.status_code == 200:
                print("🔐 Please complete authentication in your browser or TWS/IB Gateway")
                print("   Waiting for authentication completion...")
                
                # Poll for authentication completion
                for attempt in range(30):  # Wait up to 30 seconds
                    time.sleep(1)
                    status_response = self.session.get(f"{self.base_url}/portal/iserver/auth/status")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('authenticated', False):
                            self.authenticated = True
                            logger.info("✅ Authentication successful")
                            return True
                
                logger.error("❌ Authentication timeout. Please try again.")
                return False
            else:
                logger.error(f"❌ Authentication failed: {auth_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def get_accounts(self) -> List[Dict]:
        """Get list of available accounts"""
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            response = self.session.get(f"{self.base_url}/portal/iserver/accounts")
            
            if response.status_code == 200:
                accounts = response.json()
                logger.info(f"✅ Found {len(accounts)} account(s)")
                
                # Set primary account
                if accounts and not self.account_id:
                    self.account_id = accounts[0].get('id') or accounts[0].get('accountId')
                    logger.info(f"Using account: {self.account_id}")
                
                return accounts
            else:
                logger.error(f"❌ Failed to get accounts: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting accounts: {e}")
            return []
    
    def get_account_balance(self, account_id: Optional[str] = None) -> Dict:
        """Get account balance and buying power"""
        if not self.authenticated:
            if not self.authenticate():
                return {}
        
        account_id = account_id or self.account_id
        if not account_id:
            accounts = self.get_accounts()
            if not accounts:
                return {}
            account_id = accounts[0].get('id') or accounts[0].get('accountId')
        
        try:
            response = self.session.get(f"{self.base_url}/portal/iserver/account/{account_id}/summary")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Extract key balance information
                balance_info = {}
                
                for item in summary.get('summary', []):
                    currency = item.get('currency', 'USD')
                    amount = item.get('amount', {})
                    
                    if currency == 'USD':  # Focus on USD balances
                        balance_info.update({
                            'total_cash': amount.get('totalcash', 0),
                            'net_liquidation': amount.get('netliquidation', 0),
                            'buying_power': amount.get('buypower', 0),
                            'excess_liquidity': amount.get('excessliquidity', 0),
                            'currency': currency
                        })
                
                logger.info(f"✅ Account balance retrieved for {account_id}")
                return balance_info
            else:
                logger.error(f"❌ Failed to get balance: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error getting balance: {e}")
            return {}
    
    def get_positions(self, account_id: Optional[str] = None) -> List[Dict]:
        """Get current portfolio positions"""
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        account_id = account_id or self.account_id
        if not account_id:
            accounts = self.get_accounts()
            if not accounts:
                return []
            account_id = accounts[0].get('id') or accounts[0].get('accountId')
        
        try:
            response = self.session.get(f"{self.base_url}/portal/iserver/account/positions/{account_id}")
            
            if response.status_code == 200:
                positions_data = response.json()
                positions = []
                
                for position in positions_data:
                    pos_info = {
                        'symbol': position.get('ticker', ''),
                        'position': position.get('position', 0),
                        'market_price': position.get('mktPrice', 0),
                        'market_value': position.get('mktValue', 0),
                        'avg_cost': position.get('avgCost', 0),
                        'unrealized_pnl': position.get('unrealizedPnl', 0),
                        'realized_pnl': position.get('realizedPnl', 0),
                        'asset_class': position.get('assetClass', ''),
                        'currency': position.get('currency', 'USD')
                    }
                    
                    # Only include actual positions (not zero positions)
                    if abs(pos_info['position']) > 0:
                        positions.append(pos_info)
                
                logger.info(f"✅ Found {len(positions)} positions")
                return positions
            else:
                logger.error(f"❌ Failed to get positions: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting positions: {e}")
            return []
    
    def get_portfolio_summary(self, account_id: Optional[str] = None) -> Dict:
        """Get comprehensive portfolio summary"""
        try:
            # Get account balance
            balance = self.get_account_balance(account_id)
            
            # Get positions
            positions = self.get_positions(account_id)
            
            # Calculate portfolio metrics
            total_market_value = sum(pos['market_value'] for pos in positions)
            total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in positions)
            total_realized_pnl = sum(pos['realized_pnl'] for pos in positions)
            
            # Count positions by asset class
            asset_classes = {}
            for pos in positions:
                asset_class = pos['asset_class']
                if asset_class not in asset_classes:
                    asset_classes[asset_class] = {'count': 0, 'value': 0}
                asset_classes[asset_class]['count'] += 1
                asset_classes[asset_class]['value'] += pos['market_value']
            
            # Get AI/Robotics focused positions
            target_stocks = self.config.get('target_stocks', [])
            ai_etfs = self.config.get('ai_robotics_etfs', [])
            ai_positions = [pos for pos in positions if pos['symbol'] in target_stocks + ai_etfs]
            
            portfolio_summary = {
                'account_id': account_id or self.account_id,
                'timestamp': datetime.now().isoformat(),
                'balance': balance,
                'positions': positions,
                'metrics': {
                    'total_positions': len(positions),
                    'total_market_value': total_market_value,
                    'total_unrealized_pnl': total_unrealized_pnl,
                    'total_realized_pnl': total_realized_pnl,
                    'asset_classes': asset_classes
                },
                'ai_robotics_focus': {
                    'ai_positions': ai_positions,
                    'ai_position_count': len(ai_positions),
                    'ai_market_value': sum(pos['market_value'] for pos in ai_positions),
                    'ai_allocation_pct': (sum(pos['market_value'] for pos in ai_positions) / total_market_value * 100) if total_market_value > 0 else 0
                }
            }
            
            logger.info("✅ Portfolio summary generated")
            return portfolio_summary
            
        except Exception as e:
            logger.error(f"❌ Error generating portfolio summary: {e}")
            return {}
    
    def sync_with_config(self) -> bool:
        """Synchronize live portfolio data with system configuration"""
        try:
            portfolio = self.get_portfolio_summary()
            
            if not portfolio:
                return False
            
            # Update configuration with live data
            balance = portfolio['balance']
            
            # Update user profile with live balance
            if 'user_profile' not in self.config:
                self.config['user_profile'] = {}
            
            # Update balance from live data
            live_balance = balance.get('net_liquidation', 0)
            if live_balance > 0:
                self.config['user_profile']['interactive_brokers_balance'] = live_balance
                self.config['user_profile']['last_sync'] = datetime.now().isoformat()
                
                # Save updated config
                config_path = Path("config/config.json")
                with open(config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                
                logger.info(f"✅ Config updated with live balance: ${live_balance:,.2f}")
                return True
            else:
                logger.warning("⚠️  No valid balance data received")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error syncing with config: {e}")
            return False
    
    def get_market_data(self, symbol: str) -> Dict:
        """Get real-time market data for a symbol"""
        if not self.authenticated:
            if not self.authenticate():
                return {}
        
        try:
            # First get contract ID for symbol
            search_response = self.session.get(
                f"{self.base_url}/portal/iserver/secdef/search",
                params={'symbol': symbol}
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data:
                    contract_id = search_data[0].get('conid')
                    
                    # Get market data
                    market_response = self.session.get(
                        f"{self.base_url}/portal/iserver/marketdata/snapshot",
                        params={'conids': contract_id, 'fields': '31,84,86,87,88'}  # Last, bid, ask, high, low
                    )
                    
                    if market_response.status_code == 200:
                        market_data = market_response.json()
                        if market_data:
                            data = market_data[0]
                            return {
                                'symbol': symbol,
                                'last_price': data.get('31', 0),
                                'bid': data.get('84', 0),
                                'ask': data.get('86', 0),
                                'high': data.get('87', 0),
                                'low': data.get('88', 0),
                                'timestamp': datetime.now().isoformat()
                            }
            
            logger.warning(f"⚠️  No market data found for {symbol}")
            return {}
            
        except Exception as e:
            logger.error(f"❌ Error getting market data for {symbol}: {e}")
            return {}
    
    def is_connected(self) -> bool:
        """Check if connected to IB Gateway"""
        try:
            response = self.session.get(f"{self.base_url}/portal/iserver/auth/status", timeout=5)
            return response.status_code == 200 and response.json().get('authenticated', False)
        except:
            return False


def main():
    """Test Interactive Brokers connection"""
    print("=== Interactive Brokers Connection Test ===")
    
    # Initialize connector
    ibkr = IBKRConnector()
    
    # Test connection
    if ibkr.authenticate():
        print("✅ Connected to Interactive Brokers")
        
        # Get accounts
        accounts = ibkr.get_accounts()
        print(f"📊 Accounts: {len(accounts)}")
        
        # Get portfolio summary
        portfolio = ibkr.get_portfolio_summary()
        if portfolio:
            balance = portfolio['balance']
            positions = portfolio['positions']
            
            print(f"💰 Net Liquidation: ${balance.get('net_liquidation', 0):,.2f}")
            print(f"💵 Buying Power: ${balance.get('buying_power', 0):,.2f}")
            print(f"📈 Positions: {len(positions)}")
            
            # Show AI/Robotics positions
            ai_focus = portfolio['ai_robotics_focus']
            print(f"🤖 AI/Robotics Positions: {ai_focus['ai_position_count']}")
            print(f"🎯 AI Allocation: {ai_focus['ai_allocation_pct']:.1f}%")
            
            # Sync with config
            ibkr.sync_with_config()
            
        else:
            print("❌ Failed to get portfolio data")
    else:
        print("❌ Failed to connect to Interactive Brokers")
        print("💡 Make sure IB Gateway or TWS is running and authenticated")


if __name__ == "__main__":
    main()