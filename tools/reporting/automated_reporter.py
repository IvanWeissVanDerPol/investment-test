"""
Automated Investment Reporting System
Orchestrates all modules and generates comprehensive investment reports
"""

import schedule
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import os
# Email imports commented out for now
# import smtplib
# from email.mime.text import MimeText
# from email.mime.multipart import MimeMultipart
# from email.mime.base import MimeBase
# from email import encoders

# Import our modules
from smart_money_tracker import SmartMoneyTracker
from market_data_collector import MarketDataCollector
from government_spending_monitor import GovernmentSpendingMonitor
from investment_signal_engine import InvestmentSignalEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedReporter:
    def __init__(self, config_file: str = "config.json"):
        """Initialize the automated reporting system"""
        self.config = self.load_config(config_file)
        
        # Initialize all modules
        self.smart_money = SmartMoneyTracker(config_file)
        self.market_data = MarketDataCollector(config_file)
        self.gov_monitor = GovernmentSpendingMonitor(config_file)
        self.signal_engine = InvestmentSignalEngine(config_file)
        
        # Ensure reports directory exists
        os.makedirs("C:\\Users\\jandr\\Documents\\ivan\\reports", exist_ok=True)
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration for reporting system"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            
        return {
            "email_settings": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "your_email@gmail.com",
                "password": "your_app_password",
                "recipient": "recipient@gmail.com"
            },
            "report_schedule": {
                "daily_report_time": "08:00",
                "weekly_report_day": "monday",
                "monthly_report_day": 1
            },
            "alert_thresholds": {
                "strong_buy_confidence": 0.8,
                "price_movement_alert": 0.05,  # 5%
                "volume_spike_threshold": 2.0,  # 2x average
                "contract_value_alert": 50_000_000  # $50M
            },
            "target_stocks": [
                "NVDA", "MSFT", "TSLA", "DE", "TSM",
                "AMZN", "GOOGL", "META", "AAPL", "CRM"
            ],
            "ai_robotics_etfs": [
                "KROP", "BOTZ", "SOXX", "ARKQ", "ROBO"
            ]
        }
    
    def generate_daily_report(self) -> Dict:
        """Generate comprehensive daily investment report"""
        try:
            logger.info("Generating daily investment report")
            
            # Collect data from all modules
            market_report = self.market_data.generate_market_report()
            smart_money_report = self.smart_money.generate_smart_money_report(
                self.config.get('target_stocks', [])
            )
            gov_intel = self.gov_monitor.generate_government_intelligence_report()
            
            # Generate investment signals
            signals = self.signal_engine.generate_portfolio_signals()
            signal_report = self.signal_engine.create_investment_report(signals)
            
            # Create comprehensive daily report
            daily_report = {
                'report_type': 'daily',
                'generated_at': datetime.now().isoformat(),
                'executive_summary': self.create_executive_summary(
                    market_report, smart_money_report, gov_intel, signal_report
                ),
                'market_analysis': market_report,
                'smart_money_intelligence': smart_money_report,
                'government_intelligence': gov_intel,
                'investment_signals': signal_report,
                'alerts': self.generate_alerts(market_report, smart_money_report, gov_intel, signal_report),
                'recommendations': self.compile_recommendations(signal_report),
                'risk_assessment': self.create_risk_assessment(market_report, signal_report),
                'portfolio_allocation': self.calculate_portfolio_allocation(signals),
                'next_actions': self.generate_next_actions(signal_report)
            }
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"daily_investment_report_{timestamp}.json"
            self.save_report(daily_report, filename)
            
            # Generate human-readable summary
            summary_report = self.create_human_readable_report(daily_report)
            summary_filename = f"daily_summary_{timestamp}.txt"
            self.save_text_report(summary_report, summary_filename)
            
            return daily_report
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return {}
    
    def create_executive_summary(self, market_report: Dict, smart_money: Dict, 
                               gov_intel: Dict, signals: Dict) -> Dict:
        """Create executive summary of all data"""
        summary = {
            'market_sentiment': 'neutral',
            'top_opportunities': [],
            'major_alerts': [],
            'portfolio_changes_needed': False,
            'overall_confidence': 0.0,
            'key_themes': []
        }
        
        try:
            # Analyze market sentiment
            sector_data = market_report.get('sector_analysis', {}).get('sectors', {})
            positive_sectors = sum(1 for sector, data in sector_data.items() 
                                 if data.get('avg_change', 0) > 0)
            total_sectors = len(sector_data)
            
            if total_sectors > 0:
                if positive_sectors / total_sectors > 0.7:
                    summary['market_sentiment'] = 'bullish'
                elif positive_sectors / total_sectors < 0.3:
                    summary['market_sentiment'] = 'bearish'
            
            # Top opportunities from signals
            strong_buys = signals.get('top_recommendations', {}).get('strong_buys', [])
            summary['top_opportunities'] = [
                {
                    'symbol': rec['symbol'],
                    'confidence': rec['confidence'],
                    'target_upside': ((rec['target_price'] / rec.get('current_price', rec['target_price'])) - 1) * 100
                        if rec.get('current_price', 0) > 0 else 0
                }
                for rec in strong_buys[:3]
            ]
            
            # Major alerts
            all_alerts = []
            all_alerts.extend(market_report.get('alerts', []))
            
            # Government contract alerts
            contracts = gov_intel.get('ai_contracts', [])
            large_contracts = [c for c in contracts if c.get('award_amount', 0) > 50_000_000]
            for contract in large_contracts:
                all_alerts.append({
                    'type': 'Government Contract',
                    'message': f"${contract.get('award_amount', 0):,.0f} AI contract to {contract.get('recipient_name', 'Unknown')}"
                })
            
            summary['major_alerts'] = all_alerts[:5]  # Top 5 alerts
            
            # Portfolio changes needed
            signal_summary = signals.get('summary', {})
            if signal_summary.get('strong_buys', 0) > 0 or signal_summary.get('sells', 0) > 0:
                summary['portfolio_changes_needed'] = True
            
            # Overall confidence
            risk_analysis = signals.get('risk_analysis', {})
            summary['overall_confidence'] = risk_analysis.get('avg_confidence', 0.0)
            
            # Key themes
            themes = []
            if signal_summary.get('strong_buys', 0) > 2:
                themes.append("Multiple strong buy opportunities identified")
            if len(large_contracts) > 0:
                themes.append("Significant government AI contract activity")
            if summary['market_sentiment'] == 'bullish':
                themes.append("Broad market showing positive momentum")
            
            summary['key_themes'] = themes
            
        except Exception as e:
            logger.error(f"Error creating executive summary: {e}")
        
        return summary
    
    def generate_alerts(self, market_report: Dict, smart_money: Dict, 
                       gov_intel: Dict, signals: Dict) -> List[Dict]:
        """Generate alerts based on configured thresholds"""
        alerts = []
        thresholds = self.config.get('alert_thresholds', {})
        
        try:
            # Strong buy signals alert
            strong_buys = signals.get('top_recommendations', {}).get('strong_buys', [])
            high_confidence_buys = [
                s for s in strong_buys 
                if s.get('confidence', 0) > thresholds.get('strong_buy_confidence', 0.8)
            ]
            
            if high_confidence_buys:
                alerts.append({
                    'type': 'Strong Buy Alert',
                    'priority': 'High',
                    'message': f"{len(high_confidence_buys)} high-confidence buy signals detected",
                    'symbols': [s['symbol'] for s in high_confidence_buys],
                    'action_required': True
                })
            
            # Price movement alerts
            market_alerts = market_report.get('alerts', [])
            significant_moves = [
                alert for alert in market_alerts
                if 'moved' in alert.get('message', '') and 
                abs(alert.get('change', 0)) > thresholds.get('price_movement_alert', 0.05) * 100
            ]
            
            for move in significant_moves:
                alerts.append({
                    'type': 'Price Movement',
                    'priority': 'Medium',
                    'message': move.get('message', ''),
                    'symbol': move.get('symbol', ''),
                    'action_required': False
                })
            
            # Government contract alerts
            contracts = gov_intel.get('ai_contracts', [])
            large_contracts = [
                c for c in contracts 
                if c.get('award_amount', 0) > thresholds.get('contract_value_alert', 50_000_000)
            ]
            
            for contract in large_contracts:
                relevance = contract.get('investment_relevance', {})
                if relevance.get('publicly_traded_companies'):
                    alerts.append({
                        'type': 'Government Contract',
                        'priority': 'High',
                        'message': f"${contract.get('award_amount', 0):,.0f} contract affects public companies",
                        'companies': relevance.get('publicly_traded_companies', []),
                        'action_required': True
                    })
            
            # Smart money alerts
            smart_money_summary = smart_money.get('summary', {})
            if smart_money_summary.get('high_confidence_buys'):
                alerts.append({
                    'type': 'Smart Money Activity',
                    'priority': 'Medium',
                    'message': 'Institutional buying activity detected',
                    'symbols': smart_money_summary.get('high_confidence_buys', []),
                    'action_required': False
                })
        
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
        
        return alerts
    
    def compile_recommendations(self, signal_report: Dict) -> Dict:
        """Compile actionable investment recommendations"""
        recommendations = {
            'immediate_actions': [],
            'research_targets': [],
            'portfolio_rebalancing': [],
            'risk_management': []
        }
        
        try:
            # Immediate buy/sell actions
            strong_buys = signal_report.get('top_recommendations', {}).get('strong_buys', [])
            for rec in strong_buys:
                recommendations['immediate_actions'].append({
                    'action': 'BUY',
                    'symbol': rec['symbol'],
                    'confidence': rec['confidence'],
                    'position_size': rec['position_size'],
                    'rationale': rec['key_reasons'][:2]  # Top 2 reasons
                })
            
            # Research targets (medium confidence buys)
            buys = signal_report.get('top_recommendations', {}).get('buys', [])
            for rec in buys:
                if rec['confidence'] > 0.6:
                    recommendations['research_targets'].append({
                        'symbol': rec['symbol'],
                        'confidence': rec['confidence'],
                        'potential_upside': 'TBD',
                        'key_factors': rec['key_reasons'][:3]
                    })
            
            # Portfolio rebalancing
            detailed_signals = signal_report.get('detailed_signals', [])
            sells = [s for s in detailed_signals if s['signal_type'] in ['SELL', 'STRONG_SELL']]
            
            if sells:
                recommendations['portfolio_rebalancing'].append({
                    'action': 'Consider reducing/exiting positions',
                    'symbols': [s['symbol'] for s in sells],
                    'reason': 'Negative technical/fundamental signals'
                })
            
            # Risk management
            risk_analysis = signal_report.get('risk_analysis', {})
            high_risk_count = risk_analysis.get('high_risk_positions', 0)
            
            if high_risk_count > 3:
                recommendations['risk_management'].append({
                    'concern': 'High concentration of risky positions',
                    'action': 'Consider diversification or position sizing reduction',
                    'priority': 'Medium'
                })
        
        except Exception as e:
            logger.error(f"Error compiling recommendations: {e}")
        
        return recommendations
    
    def create_risk_assessment(self, market_report: Dict, signal_report: Dict) -> Dict:
        """Create comprehensive risk assessment"""
        risk_assessment = {
            'overall_risk_level': 'medium',
            'key_risks': [],
            'risk_mitigation': [],
            'portfolio_risk_score': 0.5
        }
        
        try:
            # Market risk factors
            sector_analysis = market_report.get('sector_analysis', {}).get('sectors', {})
            weak_sectors = [
                name for name, data in sector_analysis.items()
                if data.get('strength_rating', '') in ['Weak', 'Very Weak']
            ]
            
            if len(weak_sectors) > 2:
                risk_assessment['key_risks'].append({
                    'type': 'Market Risk',
                    'description': f"Multiple sectors showing weakness: {', '.join(weak_sectors)}",
                    'impact': 'Medium'
                })
            
            # Concentration risk
            signal_summary = signal_report.get('summary', {})
            total_allocation = signal_summary.get('total_buy_allocation', 0)
            
            if total_allocation > 0.8:  # More than 80% allocated
                risk_assessment['key_risks'].append({
                    'type': 'Concentration Risk',
                    'description': 'High portfolio concentration in recommended positions',
                    'impact': 'High'
                })
            
            # Technical risk
            risk_analysis = signal_report.get('risk_analysis', {})
            avg_confidence = risk_analysis.get('avg_confidence', 0)
            
            if avg_confidence < 0.6:
                risk_assessment['key_risks'].append({
                    'type': 'Signal Quality Risk',
                    'description': 'Below-average confidence in investment signals',
                    'impact': 'Medium'
                })
            
            # Risk mitigation strategies
            risk_assessment['risk_mitigation'] = [
                {
                    'strategy': 'Position Sizing',
                    'description': 'Limit individual positions to maximum allocation limits'
                },
                {
                    'strategy': 'Diversification',
                    'description': 'Maintain exposure across multiple sectors and asset classes'
                },
                {
                    'strategy': 'Stop Losses',
                    'description': 'Implement systematic stop-loss orders for all positions'
                }
            ]
            
            # Calculate overall portfolio risk score
            risk_factors = len(risk_assessment['key_risks'])
            high_risk_positions = risk_analysis.get('high_risk_positions', 0)
            
            portfolio_risk_score = min(1.0, (risk_factors * 0.2) + (high_risk_positions * 0.1))
            risk_assessment['portfolio_risk_score'] = portfolio_risk_score
            
            # Determine overall risk level
            if portfolio_risk_score > 0.7:
                risk_assessment['overall_risk_level'] = 'high'
            elif portfolio_risk_score < 0.3:
                risk_assessment['overall_risk_level'] = 'low'
            else:
                risk_assessment['overall_risk_level'] = 'medium'
        
        except Exception as e:
            logger.error(f"Error creating risk assessment: {e}")
        
        return risk_assessment
    
    def calculate_portfolio_allocation(self, signals: List) -> Dict:
        """Calculate recommended portfolio allocation"""
        allocation = {
            'total_equity_allocation': 0.0,
            'by_sector': {},
            'by_risk_level': {},
            'cash_allocation': 1.0,
            'allocation_details': []
        }
        
        try:
            total_allocation = 0.0
            sector_allocation = {}
            risk_allocation = {'low': 0, 'medium': 0, 'high': 0}
            
            for signal in signals:
                if signal.signal_type in ['BUY', 'STRONG_BUY']:
                    position_size = signal.position_size
                    total_allocation += position_size
                    
                    # Sector allocation (simplified mapping)
                    sector = self.map_symbol_to_sector(signal.symbol)
                    sector_allocation[sector] = sector_allocation.get(sector, 0) + position_size
                    
                    # Risk allocation
                    risk_allocation[signal.risk_level] += position_size
                    
                    # Detailed allocation
                    allocation['allocation_details'].append({
                        'symbol': signal.symbol,
                        'allocation': position_size,
                        'sector': sector,
                        'risk_level': signal.risk_level,
                        'confidence': signal.confidence
                    })
            
            allocation['total_equity_allocation'] = min(total_allocation, 0.95)  # Max 95% equity
            allocation['cash_allocation'] = 1.0 - allocation['total_equity_allocation']
            allocation['by_sector'] = sector_allocation
            allocation['by_risk_level'] = risk_allocation
        
        except Exception as e:
            logger.error(f"Error calculating portfolio allocation: {e}")
        
        return allocation
    
    def map_symbol_to_sector(self, symbol: str) -> str:
        """Map stock symbol to sector"""
        sector_mapping = {
            'NVDA': 'AI Hardware',
            'AMD': 'AI Hardware',
            'INTC': 'AI Hardware',
            'TSM': 'AI Hardware',
            'MSFT': 'AI Software',
            'GOOGL': 'AI Software',
            'META': 'AI Software',
            'CRM': 'AI Software',
            'DE': 'Agriculture Tech',
            'CNH': 'Agriculture Tech',
            'AGCO': 'Agriculture Tech',
            'KROP': 'AI/Robotics ETF',
            'BOTZ': 'AI/Robotics ETF',
            'SOXX': 'AI/Robotics ETF'
        }
        
        return sector_mapping.get(symbol, 'Other')
    
    def generate_next_actions(self, signal_report: Dict) -> List[Dict]:
        """Generate specific next actions for the investor"""
        actions = []
        
        try:
            # From signal report action items
            signal_actions = signal_report.get('action_items', [])
            for action in signal_actions:
                actions.append({
                    'priority': action.get('priority', 'Medium'),
                    'action': action.get('action', ''),
                    'timeline': action.get('timeline', 'TBD'),
                    'symbols': action.get('symbols', []),
                    'category': 'Trading'
                })
            
            # Research actions
            buys = signal_report.get('top_recommendations', {}).get('buys', [])
            if buys:
                actions.append({
                    'priority': 'Medium',
                    'action': f'Conduct detailed research on {len(buys)} buy candidates',
                    'timeline': 'Within 1 week',
                    'symbols': [b['symbol'] for b in buys],
                    'category': 'Research'
                })
            
            # Monitoring actions
            actions.append({
                'priority': 'Low',
                'action': 'Monitor daily market movements and news',
                'timeline': 'Daily',
                'symbols': [],
                'category': 'Monitoring'
            })
            
            # Review actions
            actions.append({
                'priority': 'Medium',
                'action': 'Review and update investment thesis',
                'timeline': 'Monthly',
                'symbols': [],
                'category': 'Strategy'
            })
        
        except Exception as e:
            logger.error(f"Error generating next actions: {e}")
        
        return actions
    
    def create_human_readable_report(self, report: Dict) -> str:
        """Create human-readable text summary"""
        try:
            summary = report.get('executive_summary', {})
            signals = report.get('investment_signals', {})
            alerts = report.get('alerts', [])
            
            readable_report = f"""
DAILY INVESTMENT REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

=== EXECUTIVE SUMMARY ===
Market Sentiment: {summary.get('market_sentiment', 'Unknown').upper()}
Overall Confidence: {summary.get('overall_confidence', 0):.1%}
Portfolio Changes Needed: {'YES' if summary.get('portfolio_changes_needed') else 'NO'}

Top Opportunities:
"""
            
            for opp in summary.get('top_opportunities', []):
                readable_report += f"  • {opp['symbol']}: {opp['confidence']:.1%} confidence\n"
            
            readable_report += f"\n=== INVESTMENT SIGNALS ===\n"
            signal_summary = signals.get('summary', {})
            readable_report += f"Strong Buys: {signal_summary.get('strong_buys', 0)}\n"
            readable_report += f"Buys: {signal_summary.get('buys', 0)}\n"
            readable_report += f"Holds: {signal_summary.get('holds', 0)}\n"
            readable_report += f"Sells: {signal_summary.get('sells', 0)}\n"
            
            strong_buys = signals.get('top_recommendations', {}).get('strong_buys', [])
            if strong_buys:
                readable_report += f"\nTOP STRONG BUY RECOMMENDATIONS:\n"
                for rec in strong_buys:
                    readable_report += f"  • {rec['symbol']}: {rec['confidence']:.1%} confidence, ${rec['target_price']:.2f} target\n"
            
            if alerts:
                readable_report += f"\n=== ALERTS ===\n"
                for alert in alerts[:5]:  # Top 5 alerts
                    readable_report += f"  • {alert.get('type', 'Alert')}: {alert.get('message', '')}\n"
            
            readable_report += f"\n=== NEXT ACTIONS ===\n"
            actions = report.get('next_actions', [])
            for action in actions[:5]:  # Top 5 actions
                readable_report += f"  • {action.get('priority', 'Medium')}: {action.get('action', '')} ({action.get('timeline', 'TBD')})\n"
            
            return readable_report
            
        except Exception as e:
            logger.error(f"Error creating human-readable report: {e}")
            return "Error generating readable report"
    
    def save_report(self, report: Dict, filename: str):
        """Save JSON report to file"""
        try:
            filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Report saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")
    
    def save_text_report(self, report_text: str, filename: str):
        """Save text report to file"""
        try:
            filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
            with open(filepath, 'w') as f:
                f.write(report_text)
            logger.info(f"Text report saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving text report: {e}")
    
    def send_email_report(self, report: Dict):
        """Send email report if configured"""
        email_config = self.config.get('email_settings', {})
        if not email_config.get('enabled', False):
            logger.info("Email notifications disabled")
            return
        
        logger.info("Email functionality temporarily disabled for initial setup")
        # Email functionality can be enabled later with proper email library setup
    
    def run_daily_automation(self):
        """Run the daily automated reporting process"""
        logger.info("Starting daily automation process")
        
        try:
            # Generate daily report
            report = self.generate_daily_report()
            
            # Send email if configured
            self.send_email_report(report)
            
            # Print summary to console
            summary = report.get('executive_summary', {})
            print(f"\n=== DAILY REPORT COMPLETE ===")
            print(f"Market Sentiment: {summary.get('market_sentiment', 'Unknown')}")
            print(f"Strong Buys: {len(summary.get('top_opportunities', []))}")
            print(f"Major Alerts: {len(report.get('alerts', []))}")
            print(f"Portfolio Changes Needed: {'Yes' if summary.get('portfolio_changes_needed') else 'No'}")
            
        except Exception as e:
            logger.error(f"Error in daily automation: {e}")
    
    def schedule_reports(self):
        """Schedule automated report generation"""
        schedule_config = self.config.get('report_schedule', {})
        
        # Daily report
        daily_time = schedule_config.get('daily_report_time', '08:00')
        schedule.every().day.at(daily_time).do(self.run_daily_automation)
        
        # Weekly report (more comprehensive)
        weekly_day = schedule_config.get('weekly_report_day', 'monday')
        schedule.every().week.on(weekly_day).at(daily_time).do(self.run_weekly_automation)
        
        logger.info(f"Reports scheduled: Daily at {daily_time}, Weekly on {weekly_day}")
    
    def run_weekly_automation(self):
        """Run weekly comprehensive analysis"""
        logger.info("Starting weekly automation process")
        # Weekly reports would include trend analysis, performance review, etc.
        # For now, just run daily report
        self.run_daily_automation()
    
    def start_automation(self):
        """Start the automated reporting system"""
        logger.info("Starting automated investment reporting system")
        
        # Schedule reports
        self.schedule_reports()
        
        # Run immediate report
        self.run_daily_automation()
        
        # Keep running
        print("Automated reporting system started. Press Ctrl+C to stop.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Automated reporting system stopped")

def main():
    """Main execution function"""
    reporter = AutomatedReporter()
    
    # For immediate execution (not scheduled)
    if len(os.sys.argv) > 1 and os.sys.argv[1] == '--schedule':
        reporter.start_automation()
    else:
        # Run once
        reporter.run_daily_automation()

if __name__ == "__main__":
    main()