"""
Live Portfolio Manager
Unified interface for connecting to Interactive Brokers and managing live portfolio data.
"""

import json
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data.interactive_brokers_connector import IBKRConnector
try:
    from data.tws_connector import TWSConnector
    TWS_AVAILABLE = True
except ImportError:
    TWS_AVAILABLE = False

logger = logging.getLogger(__name__)


class LivePortfolioManager:
    """Unified portfolio manager for Interactive Brokers integration"""
    
    def __init__(self, config_file: str = "config/config.json", connection_type: str = "auto"):
        """
        Initialize portfolio manager
        
        Args:
            config_file: Path to configuration file
            connection_type: "tws", "gateway", or "auto" (try TWS first, fallback to Gateway)
        """
        self.config_file = config_file
        self.config = self.load_config(config_file)
        self.connection_type = connection_type
        
        # Initialize connectors
        self.tws_connector = None
        self.ibkr_connector = None
        self.active_connector = None
        
        # Portfolio data cache
        self.last_update = None
        self.cached_portfolio = None
        self.cache_duration = 300  # 5 minutes
        
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
        """Connect to Interactive Brokers using best available method"""
        
        if self.connection_type in ["tws", "auto"]:
            # Try TWS connection first
            if TWS_AVAILABLE:
                try:
                    self.tws_connector = TWSConnector(self.config_file)
                    if self.tws_connector.connect():
                        self.active_connector = self.tws_connector
                        logger.info("✅ Connected via TWS API")
                        return True
                except Exception as e:
                    logger.warning(f"⚠️  TWS connection failed: {e}")
        
        if self.connection_type in ["gateway", "auto"]:
            # Try Gateway API connection
            try:
                self.ibkr_connector = IBKRConnector(self.config_file)
                if self.ibkr_connector.authenticate():
                    self.active_connector = self.ibkr_connector
                    logger.info("✅ Connected via IB Gateway API")
                    return True
            except Exception as e:
                logger.warning(f"⚠️  Gateway connection failed: {e}")
        
        logger.error("❌ Failed to connect to Interactive Brokers")
        logger.info("💡 Please ensure TWS or IB Gateway is running with API enabled")
        return False
    
    def disconnect(self):
        """Disconnect from Interactive Brokers"""
        if self.tws_connector:
            self.tws_connector.disconnect()
        self.active_connector = None
        logger.info("✅ Disconnected from Interactive Brokers")
    
    def is_connected(self) -> bool:
        """Check if connected to Interactive Brokers"""
        if self.active_connector is None:
            return False
        
        if hasattr(self.active_connector, 'is_connected'):
            return self.active_connector.is_connected()
        elif hasattr(self.active_connector, 'connected'):
            return self.active_connector.connected
        else:
            return True  # Assume connected if we have an active connector
    
    def get_account_balance(self) -> Dict:
        """Get current account balance and buying power"""
        if not self.active_connector:
            if not self.connect():
                return {}
        
        try:
            if hasattr(self.active_connector, 'get_account_summary'):
                # TWS connector
                return self.active_connector.get_account_summary()
            else:
                # Gateway connector
                return self.active_connector.get_account_balance()
        except Exception as e:
            logger.error(f"❌ Error getting account balance: {e}")
            return {}
    
    def get_positions(self) -> List[Dict]:
        """Get current portfolio positions"""
        if not self.active_connector:
            if not self.connect():
                return []
        
        try:
            if hasattr(self.active_connector, 'get_portfolio_positions'):
                # TWS connector
                return self.active_connector.get_portfolio_positions()
            else:
                # Gateway connector
                return self.active_connector.get_positions()
        except Exception as e:
            logger.error(f"❌ Error getting positions: {e}")
            return []
    
    def get_live_portfolio_data(self, force_refresh: bool = False) -> Dict:
        """Get comprehensive live portfolio data with caching"""
        
        # Check cache
        if not force_refresh and self.cached_portfolio and self.last_update:
            if datetime.now() - self.last_update < timedelta(seconds=self.cache_duration):
                logger.info("📋 Using cached portfolio data")
                return self.cached_portfolio
        
        if not self.active_connector:
            if not self.connect():
                return {}
        
        try:
            # Get data using appropriate connector
            if hasattr(self.active_connector, 'get_comprehensive_portfolio_data'):
                # TWS connector
                portfolio_data = self.active_connector.get_comprehensive_portfolio_data()
            else:
                # Gateway connector - build comprehensive data
                balance = self.get_account_balance()
                positions = self.get_positions()
                portfolio_data = self._build_comprehensive_data(balance, positions)
            
            # Cache the data
            self.cached_portfolio = portfolio_data
            self.last_update = datetime.now()
            
            logger.info("✅ Live portfolio data retrieved")
            return portfolio_data
            
        except Exception as e:
            logger.error(f"❌ Error getting live portfolio data: {e}")
            return {}
    
    def _build_comprehensive_data(self, balance: Dict, positions: List[Dict]) -> Dict:
        """Build comprehensive portfolio data from basic components"""
        try:
            # Calculate analytics
            total_market_value = sum(pos.get('market_value', 0) for pos in positions)
            total_unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions)
            
            # AI/Robotics analysis
            target_stocks = self.config.get('target_stocks', [])
            ai_etfs = self.config.get('ai_robotics_etfs', [])
            ai_symbols = set(target_stocks + ai_etfs)
            
            ai_positions = [pos for pos in positions if pos.get('symbol', '') in ai_symbols]
            ai_market_value = sum(pos.get('market_value', 0) for pos in ai_positions)
            ai_allocation_pct = (ai_market_value / total_market_value * 100) if total_market_value > 0 else 0
            
            # Position analysis
            position_sizes = []
            for pos in positions:
                symbol = pos.get('symbol', '')
                market_value = pos.get('market_value', 0)
                percentage = (market_value / total_market_value * 100) if total_market_value > 0 else 0
                position_sizes.append((symbol, market_value, percentage))
            
            position_sizes.sort(key=lambda x: x[1], reverse=True)
            
            return {
                'account_summary': balance,
                'positions': positions,
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
                    'target_allocation': 70  # From investment strategy
                },
                'risk_metrics': {
                    'concentration_risk': max([size[2] for size in position_sizes]) if position_sizes else 0,
                    'diversification_score': len(positions),
                    'cash_percentage': (balance.get('total_cash', 0) / balance.get('net_liquidation', 1)) * 100
                },
                'timestamp': datetime.now().isoformat(),
                'connection_type': 'gateway'
            }
            
        except Exception as e:
            logger.error(f"❌ Error building comprehensive data: {e}")
            return {}
    
    def sync_with_analysis_system(self) -> bool:
        """Synchronize live portfolio data with the analysis system"""
        try:
            portfolio_data = self.get_live_portfolio_data(force_refresh=True)
            
            if not portfolio_data:
                logger.error("❌ No portfolio data to sync")
                return False
            
            account_summary = portfolio_data.get('account_summary', {})
            
            # Update user profile
            if 'user_profile' not in self.config:
                self.config['user_profile'] = {}
            
            # Update with live data
            live_balance = account_summary.get('net_liquidation', 0)
            if live_balance > 0:
                self.config['user_profile'].update({
                    'interactive_brokers_balance': live_balance,
                    'buying_power': account_summary.get('buying_power', 0),
                    'total_cash': account_summary.get('total_cash', 0),
                    'last_sync_timestamp': datetime.now().isoformat(),
                    'account_id': account_summary.get('account_id', ''),
                    'connection_type': portfolio_data.get('connection_type', 'unknown')
                })
                
                # Add live portfolio snapshot
                self.config['live_portfolio'] = {
                    'positions': portfolio_data.get('positions', []),
                    'ai_allocation_current': portfolio_data.get('ai_robotics_analysis', {}).get('ai_allocation_percentage', 0),
                    'concentration_risk': portfolio_data.get('risk_metrics', {}).get('concentration_risk', 0),
                    'total_market_value': portfolio_data.get('portfolio_analytics', {}).get('total_market_value', 0),
                    'sync_timestamp': datetime.now().isoformat()
                }
                
                # Save updated configuration
                config_path = Path(self.config_file)
                with open(config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                
                logger.info(f"✅ Configuration synced with live portfolio")
                logger.info(f"   Live Balance: ${live_balance:,.2f}")
                logger.info(f"   Positions: {len(portfolio_data.get('positions', []))}")
                logger.info(f"   AI Allocation: {portfolio_data.get('ai_robotics_analysis', {}).get('ai_allocation_percentage', 0):.1f}%")
                
                return True
            else:
                logger.warning("⚠️  Invalid balance data received")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error syncing with analysis system: {e}")
            return False
    
    def get_portfolio_summary_for_analysis(self) -> Dict:
        """Get portfolio summary formatted for analysis system"""
        try:
            portfolio_data = self.get_live_portfolio_data()
            
            if not portfolio_data:
                return {}
            
            account = portfolio_data.get('account_summary', {})
            analytics = portfolio_data.get('portfolio_analytics', {})
            ai_analysis = portfolio_data.get('ai_robotics_analysis', {})
            risk_metrics = portfolio_data.get('risk_metrics', {})
            
            summary = {
                'account_info': {
                    'balance': account.get('net_liquidation', 0),
                    'buying_power': account.get('buying_power', 0),
                    'cash': account.get('total_cash', 0),
                    'currency': account.get('currency', 'USD')
                },
                'portfolio_metrics': {
                    'total_positions': analytics.get('total_positions', 0),
                    'market_value': analytics.get('total_market_value', 0),
                    'unrealized_pnl': analytics.get('total_unrealized_pnl', 0),
                    'largest_position_pct': risk_metrics.get('concentration_risk', 0)
                },
                'ai_robotics_focus': {
                    'current_allocation_pct': ai_analysis.get('ai_allocation_percentage', 0),
                    'target_allocation_pct': ai_analysis.get('target_allocation', 70),
                    'ai_positions_count': ai_analysis.get('ai_position_count', 0),
                    'ai_market_value': ai_analysis.get('ai_market_value', 0)
                },
                'risk_assessment': {
                    'concentration_risk': risk_metrics.get('concentration_risk', 0),
                    'diversification_score': risk_metrics.get('diversification_score', 0),
                    'cash_percentage': risk_metrics.get('cash_percentage', 0)
                },
                'positions': portfolio_data.get('positions', []),
                'last_updated': portfolio_data.get('timestamp'),
                'data_source': 'interactive_brokers_live'
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating portfolio summary: {e}")
            return {}
    
    def check_rebalancing_needs(self) -> Dict:
        """Check if portfolio needs rebalancing based on targets"""
        try:
            portfolio_summary = self.get_portfolio_summary_for_analysis()
            
            if not portfolio_summary:
                return {}
            
            ai_focus = portfolio_summary['ai_robotics_focus']
            risk_assessment = portfolio_summary['risk_assessment']
            
            rebalancing_needs = {
                'needs_rebalancing': False,
                'recommendations': [],
                'risk_warnings': [],
                'analysis_date': datetime.now().isoformat()
            }
            
            # Check AI allocation
            current_ai_pct = ai_focus['current_allocation_pct']
            target_ai_pct = ai_focus['target_allocation_pct']
            
            if abs(current_ai_pct - target_ai_pct) > 10:  # More than 10% deviation
                rebalancing_needs['needs_rebalancing'] = True
                if current_ai_pct < target_ai_pct:
                    rebalancing_needs['recommendations'].append(
                        f"Increase AI/Robotics allocation from {current_ai_pct:.1f}% to {target_ai_pct}%"
                    )
                else:
                    rebalancing_needs['recommendations'].append(
                        f"Reduce AI/Robotics allocation from {current_ai_pct:.1f}% to {target_ai_pct}%"
                    )
            
            # Check concentration risk
            max_position_pct = risk_assessment['concentration_risk']
            if max_position_pct > 25:  # Medium risk tolerance limit
                rebalancing_needs['risk_warnings'].append(
                    f"High concentration risk: largest position is {max_position_pct:.1f}% (limit: 25%)"
                )
                rebalancing_needs['needs_rebalancing'] = True
            
            # Check diversification
            diversification_score = risk_assessment['diversification_score']
            if diversification_score < 6:  # Minimum positions for medium risk
                rebalancing_needs['recommendations'].append(
                    f"Increase diversification: currently {diversification_score} positions (target: 6-8)"
                )
            
            # Check cash percentage
            cash_pct = risk_assessment['cash_percentage']
            if cash_pct > 10:  # Too much cash sitting idle
                rebalancing_needs['recommendations'].append(
                    f"Deploy excess cash: {cash_pct:.1f}% cash (target: <10%)"
                )
            
            return rebalancing_needs
            
        except Exception as e:
            logger.error(f"❌ Error checking rebalancing needs: {e}")
            return {}


def main():
    """Test live portfolio manager functionality"""
    print("=== Live Portfolio Manager Test ===")
    
    # Initialize manager
    portfolio_manager = LivePortfolioManager()
    
    try:
        # Test connection
        if portfolio_manager.connect():
            print("✅ Connected to Interactive Brokers")
            
            # Get portfolio summary
            summary = portfolio_manager.get_portfolio_summary_for_analysis()
            
            if summary:
                account = summary['account_info']
                metrics = summary['portfolio_metrics']
                ai_focus = summary['ai_robotics_focus']
                
                print(f"\n💰 Account Information:")
                print(f"   Balance: ${account['balance']:,.2f}")
                print(f"   Buying Power: ${account['buying_power']:,.2f}")
                print(f"   Cash: ${account['cash']:,.2f}")
                
                print(f"\n📊 Portfolio Metrics:")
                print(f"   Positions: {metrics['total_positions']}")
                print(f"   Market Value: ${metrics['market_value']:,.2f}")
                print(f"   Unrealized P&L: ${metrics['unrealized_pnl']:,.2f}")
                
                print(f"\n🤖 AI/Robotics Focus:")
                print(f"   Current Allocation: {ai_focus['current_allocation_pct']:.1f}%")
                print(f"   Target Allocation: {ai_focus['target_allocation_pct']}%")
                print(f"   AI Positions: {ai_focus['ai_positions_count']}")
                
                # Check rebalancing needs
                rebalancing = portfolio_manager.check_rebalancing_needs()
                if rebalancing.get('needs_rebalancing'):
                    print(f"\n⚠️  Rebalancing Recommended:")
                    for rec in rebalancing.get('recommendations', []):
                        print(f"   • {rec}")
                    for warning in rebalancing.get('risk_warnings', []):
                        print(f"   ⚠️  {warning}")
                else:
                    print(f"\n✅ Portfolio is well-balanced")
                
                # Sync with analysis system
                if portfolio_manager.sync_with_analysis_system():
                    print(f"\n✅ Portfolio data synced with analysis system")
                
            else:
                print("❌ Failed to get portfolio summary")
        else:
            print("❌ Failed to connect to Interactive Brokers")
    
    finally:
        portfolio_manager.disconnect()


if __name__ == "__main__":
    main()