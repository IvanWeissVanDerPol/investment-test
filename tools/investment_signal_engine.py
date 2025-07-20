"""
Investment Signal Engine
Combines all data sources to generate buy/sell signals and investment recommendations
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import math

# Import our custom modules
from smart_money_tracker import SmartMoneyTracker
from market_data_collector import MarketDataCollector
from government_spending_monitor import GovernmentSpendingMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InvestmentSignal:
    """Investment signal data structure"""
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL'
    confidence: float  # 0.0 to 1.0
    target_price: float
    stop_loss: float
    time_horizon: str  # 'short', 'medium', 'long'
    reasoning: List[str]
    risk_level: str  # 'low', 'medium', 'high'
    position_size: float  # Recommended position size as % of portfolio
    priority: int  # 1-10, 10 being highest priority

class InvestmentSignalEngine:
    def __init__(self, config_file: str = None):
        """Initialize the investment signal engine"""
        self.config = self.load_config(config_file)
        
        # Initialize data collectors
        self.smart_money = SmartMoneyTracker(config_file)
        self.market_data = MarketDataCollector(config_file)
        self.gov_monitor = GovernmentSpendingMonitor(config_file)
        
        # Signal weights
        self.weights = {
            'technical': 0.25,
            'smart_money': 0.30,
            'fundamental': 0.20,
            'government': 0.15,
            'sentiment': 0.10
        }
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                logger.warning(f"Config file {config_file} not found, using defaults")
        
        return {
            "target_stocks": [
                "NVDA", "MSFT", "TSLA", "DE", "TSM",
                "AMZN", "GOOGL", "META", "AAPL", "CRM"
            ],
            "ai_robotics_etfs": [
                "KROP", "BOTZ", "SOXX", "ARKQ", "ROBO"
            ],
            "risk_tolerance": "medium",  # low, medium, high
            "max_position_size": 0.15,  # 15% max per position
            "min_confidence": 0.6,  # Minimum confidence for signals
            "time_horizons": {
                "short": "1-3 months",
                "medium": "3-12 months", 
                "long": "1-3 years"
            }
        }
    
    def analyze_technical_signals(self, symbol: str) -> Dict:
        """Analyze technical indicators for buy/sell signals"""
        try:
            logger.info(f"Analyzing technical signals for {symbol}")
            
            # Get price data and technical indicators
            price_data = self.market_data.get_real_time_price(symbol)
            hist_data = self.market_data.get_historical_data(symbol, "6mo")
            
            if hist_data.empty or not price_data:
                return {'score': 0, 'signals': [], 'confidence': 0}
            
            latest = hist_data.iloc[-1]
            current_price = price_data.get('current_price', 0)
            
            signals = []
            score = 0
            
            # Moving Average Analysis
            sma_20 = latest.get('SMA_20', 0)
            sma_50 = latest.get('SMA_50', 0)
            sma_200 = latest.get('SMA_200', 0)
            
            if current_price > sma_20 > sma_50:
                signals.append("Price above short and medium-term averages")
                score += 2
            elif current_price > sma_20:
                signals.append("Price above short-term average")
                score += 1
            
            if sma_20 > sma_50 > sma_200:
                signals.append("All moving averages in bullish alignment")
                score += 2
            
            # RSI Analysis
            rsi = latest.get('RSI', 50)
            if 30 <= rsi <= 70:
                signals.append(f"RSI in neutral zone ({rsi:.1f})")
                score += 1
            elif rsi < 30:
                signals.append(f"RSI oversold ({rsi:.1f}) - potential buy signal")
                score += 2
            elif rsi > 70:
                signals.append(f"RSI overbought ({rsi:.1f}) - caution")
                score -= 1
            
            # MACD Analysis
            macd = latest.get('MACD', 0)
            macd_signal = latest.get('MACD_Signal', 0)
            if macd > macd_signal:
                signals.append("MACD bullish crossover")
                score += 1
            else:
                signals.append("MACD bearish signal")
                score -= 1
            
            # Volume Analysis
            volume_ratio = price_data.get('volume', 0) / max(price_data.get('avg_volume', 1), 1)
            if volume_ratio > 1.5:
                signals.append("High volume confirms price movement")
                score += 1
            elif volume_ratio < 0.7:
                signals.append("Low volume - weak conviction")
                score -= 0.5
            
            # Bollinger Bands
            bb_upper = latest.get('BB_Upper', 0)
            bb_lower = latest.get('BB_Lower', 0)
            if current_price < bb_lower:
                signals.append("Price below lower Bollinger Band - oversold")
                score += 1
            elif current_price > bb_upper:
                signals.append("Price above upper Bollinger Band - overbought")
                score -= 1
            
            # Calculate confidence
            max_score = 10
            confidence = max(0, min(1, (score + max_score/2) / max_score))
            
            return {
                'score': score,
                'signals': signals,
                'confidence': confidence,
                'current_price': current_price,
                'support_level': bb_lower,
                'resistance_level': bb_upper,
                'trend': 'bullish' if score > 0 else 'bearish' if score < -1 else 'neutral'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing technical signals for {symbol}: {e}")
            return {'score': 0, 'signals': [], 'confidence': 0}
    
    def analyze_smart_money_signals(self, symbol: str) -> Dict:
        """Analyze smart money and institutional activity"""
        try:
            logger.info(f"Analyzing smart money signals for {symbol}")
            
            # Get smart money analysis
            smart_analysis = self.smart_money.analyze_smart_money_moves(symbol)
            
            signals = []
            score = 0
            
            if smart_analysis:
                sentiment_score = smart_analysis.get('sentiment_score', 0)
                buy_sell_ratio = smart_analysis.get('buy_sell_ratio', 1)
                confidence_level = smart_analysis.get('confidence_level', 'low')
                
                # Institutional sentiment
                if sentiment_score > 0.7:
                    signals.append("Strong positive institutional sentiment")
                    score += 3
                elif sentiment_score > 0.5:
                    signals.append("Positive institutional sentiment")
                    score += 2
                elif sentiment_score < 0.3:
                    signals.append("Negative institutional sentiment")
                    score -= 2
                
                # Insider trading activity
                if buy_sell_ratio > 1.5:
                    signals.append("Insider buying exceeds selling")
                    score += 2
                elif buy_sell_ratio < 0.7:
                    signals.append("Insider selling exceeds buying")
                    score -= 2
                
                # Confidence weighting
                if confidence_level == 'high':
                    score *= 1.2
                elif confidence_level == 'low':
                    score *= 0.8
                
                # Recent insider filings
                insider_data = smart_analysis.get('insider_trading', [])
                if len(insider_data) > 5:  # High insider activity
                    signals.append("High insider trading activity")
                    score += 1
            
            confidence = max(0, min(1, (score + 5) / 10))
            
            return {
                'score': score,
                'signals': signals,
                'confidence': confidence,
                'institutional_sentiment': smart_analysis.get('sentiment_score', 0),
                'insider_ratio': smart_analysis.get('buy_sell_ratio', 1)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing smart money signals for {symbol}: {e}")
            return {'score': 0, 'signals': [], 'confidence': 0}
    
    def analyze_government_signals(self, symbol: str) -> Dict:
        """Analyze government spending and contract signals"""
        try:
            logger.info(f"Analyzing government signals for {symbol}")
            
            # Get government intelligence
            gov_report = self.gov_monitor.generate_government_intelligence_report()
            
            signals = []
            score = 0
            
            # Check for recent AI contracts
            contracts = gov_report.get('ai_contracts', [])
            relevant_contracts = []
            
            for contract in contracts:
                relevance = contract.get('investment_relevance', {})
                companies = relevance.get('publicly_traded_companies', [])
                
                # Check if symbol matches any company names (simplified matching)
                symbol_mapping = {
                    'NVDA': ['nvidia'],
                    'MSFT': ['microsoft'],
                    'GOOGL': ['google'],
                    'AMZN': ['amazon'],
                    'META': ['meta', 'facebook'],
                    'PLTR': ['palantir'],
                    'TSM': ['taiwan semiconductor']
                }
                
                keywords = symbol_mapping.get(symbol, [symbol.lower()])
                for company in companies:
                    if any(keyword in company.lower() for keyword in keywords):
                        relevant_contracts.append(contract)
                        break
            
            if relevant_contracts:
                total_value = sum(c.get('award_amount', 0) for c in relevant_contracts)
                signals.append(f"Recent government contracts worth ${total_value:,.0f}")
                
                # Score based on contract value
                if total_value > 100_000_000:  # $100M+
                    score += 3
                elif total_value > 10_000_000:  # $10M+
                    score += 2
                elif total_value > 1_000_000:  # $1M+
                    score += 1
            
            # Check defense budget alignment
            defense_budget = gov_report.get('defense_budget', {})
            investment_recs = defense_budget.get('investment_recommendations', [])
            
            for rec in investment_recs:
                if symbol in rec.get('stocks', []):
                    signals.append(f"Aligned with defense spending in {rec.get('category', 'unknown category')}")
                    if rec.get('confidence') == 'High':
                        score += 2
                    else:
                        score += 1
            
            # DARPA program alignment
            darpa_programs = gov_report.get('darpa_programs', [])
            for program in darpa_programs:
                program_recs = program.get('investment_recommendations', [])
                if symbol in program_recs:
                    signals.append(f"Benefits from DARPA {program.get('program_name', 'program')}")
                    score += 1
            
            confidence = max(0, min(1, score / 5))
            
            return {
                'score': score,
                'signals': signals,
                'confidence': confidence,
                'contract_value': sum(c.get('award_amount', 0) for c in relevant_contracts),
                'contract_count': len(relevant_contracts)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing government signals for {symbol}: {e}")
            return {'score': 0, 'signals': [], 'confidence': 0}
    
    def calculate_fundamental_score(self, symbol: str) -> Dict:
        """Calculate fundamental analysis score"""
        try:
            logger.info(f"Analyzing fundamentals for {symbol}")
            
            price_data = self.market_data.get_real_time_price(symbol)
            
            signals = []
            score = 0
            
            if price_data:
                # P/E ratio analysis
                pe_ratio = price_data.get('pe_ratio', 0)
                if 0 < pe_ratio < 25:
                    signals.append(f"Reasonable P/E ratio ({pe_ratio:.1f})")
                    score += 1
                elif pe_ratio > 50:
                    signals.append(f"High P/E ratio ({pe_ratio:.1f}) - growth expectations")
                    score -= 0.5
                
                # Market cap consideration
                market_cap = price_data.get('market_cap', 0)
                if market_cap > 100_000_000_000:  # $100B+
                    signals.append("Large cap stability")
                    score += 0.5
                elif market_cap > 10_000_000_000:  # $10B+
                    signals.append("Mid-large cap with growth potential")
                    score += 1
                
                # 52-week performance
                current_price = price_data.get('current_price', 0)
                week_52_high = price_data.get('52_week_high', 0)
                week_52_low = price_data.get('52_week_low', 0)
                
                if week_52_high and week_52_low:
                    price_position = (current_price - week_52_low) / (week_52_high - week_52_low)
                    
                    if price_position < 0.3:
                        signals.append("Near 52-week lows - potential value")
                        score += 1
                    elif price_position > 0.8:
                        signals.append("Near 52-week highs - momentum")
                        score += 0.5
            
            confidence = max(0, min(1, (score + 2) / 4))
            
            return {
                'score': score,
                'signals': signals,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error analyzing fundamentals for {symbol}: {e}")
            return {'score': 0, 'signals': [], 'confidence': 0}
    
    def generate_investment_signal(self, symbol: str) -> InvestmentSignal:
        """Generate comprehensive investment signal for a symbol"""
        try:
            logger.info(f"Generating investment signal for {symbol}")
            
            # Collect all analysis
            technical = self.analyze_technical_signals(symbol)
            smart_money = self.analyze_smart_money_signals(symbol)
            government = self.analyze_government_signals(symbol)
            fundamental = self.calculate_fundamental_score(symbol)
            
            # Calculate weighted score
            total_score = (
                technical['score'] * self.weights['technical'] +
                smart_money['score'] * self.weights['smart_money'] +
                government['score'] * self.weights['government'] +
                fundamental['score'] * self.weights['fundamental']
            )
            
            # Calculate confidence
            confidence = (
                technical['confidence'] * self.weights['technical'] +
                smart_money['confidence'] * self.weights['smart_money'] +
                government['confidence'] * self.weights['government'] +
                fundamental['confidence'] * self.weights['fundamental']
            )
            
            # Determine signal type
            if total_score >= 3 and confidence >= 0.7:
                signal_type = "STRONG_BUY"
                priority = 9
            elif total_score >= 2 and confidence >= 0.6:
                signal_type = "BUY"
                priority = 7
            elif total_score >= 1:
                signal_type = "HOLD"
                priority = 5
            elif total_score <= -2:
                signal_type = "SELL"
                priority = 3
            elif total_score <= -3:
                signal_type = "STRONG_SELL"
                priority = 1
            else:
                signal_type = "HOLD"
                priority = 4
            
            # Calculate target price and stop loss
            current_price = technical.get('current_price', 0)
            if current_price > 0:
                if signal_type in ['BUY', 'STRONG_BUY']:
                    target_price = current_price * (1 + 0.15 * (total_score / 3))  # 15% upside potential
                    stop_loss = current_price * 0.92  # 8% stop loss
                else:
                    target_price = current_price * 0.95  # Conservative target
                    stop_loss = current_price * 0.88  # Wider stop loss for sells
            else:
                target_price = 0
                stop_loss = 0
            
            # Determine time horizon
            if government['score'] > 2:
                time_horizon = "long"  # Government contracts are long-term
            elif technical['score'] > 2:
                time_horizon = "short"  # Technical signals are shorter-term
            else:
                time_horizon = "medium"
            
            # Calculate position size
            risk_level = self.assess_risk_level(symbol, technical, smart_money, government)
            position_size = self.calculate_position_size(confidence, risk_level)
            
            # Compile reasoning
            reasoning = []
            reasoning.extend(technical.get('signals', []))
            reasoning.extend(smart_money.get('signals', []))
            reasoning.extend(government.get('signals', []))
            reasoning.extend(fundamental.get('signals', []))
            
            return InvestmentSignal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                target_price=target_price,
                stop_loss=stop_loss,
                time_horizon=time_horizon,
                reasoning=reasoning,
                risk_level=risk_level,
                position_size=position_size,
                priority=priority
            )
            
        except Exception as e:
            logger.error(f"Error generating investment signal for {symbol}: {e}")
            return InvestmentSignal(
                symbol=symbol,
                signal_type="HOLD",
                confidence=0.0,
                target_price=0.0,
                stop_loss=0.0,
                time_horizon="medium",
                reasoning=["Error in analysis"],
                risk_level="high",
                position_size=0.0,
                priority=1
            )
    
    def assess_risk_level(self, symbol: str, technical: Dict, smart_money: Dict, government: Dict) -> str:
        """Assess overall risk level for the investment"""
        risk_factors = 0
        
        # Technical risk
        if technical.get('confidence', 0) < 0.5:
            risk_factors += 1
        
        # Smart money uncertainty
        if smart_money.get('confidence', 0) < 0.5:
            risk_factors += 1
        
        # Government dependency
        if government.get('score', 0) > 2:  # High government dependency
            risk_factors += 1
        
        # Volatility (would need historical data)
        # For now, assume moderate risk for all
        
        if risk_factors >= 2:
            return "high"
        elif risk_factors == 1:
            return "medium"
        else:
            return "low"
    
    def calculate_position_size(self, confidence: float, risk_level: str) -> float:
        """Calculate recommended position size"""
        base_size = 0.05  # 5% base position
        max_size = self.config.get('max_position_size', 0.15)
        
        # Adjust for confidence
        size = base_size * (1 + confidence)
        
        # Adjust for risk
        risk_multipliers = {
            'low': 1.5,
            'medium': 1.0,
            'high': 0.7
        }
        size *= risk_multipliers.get(risk_level, 1.0)
        
        return min(size, max_size)
    
    def generate_portfolio_signals(self, symbols: List[str] = None) -> List[InvestmentSignal]:
        """Generate signals for entire portfolio"""
        if not symbols:
            symbols = self.config.get('target_stocks', [])
            symbols.extend(self.config.get('ai_robotics_etfs', []))
        
        signals = []
        for symbol in symbols:
            try:
                signal = self.generate_investment_signal(symbol)
                if signal.confidence >= self.config.get('min_confidence', 0.6):
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
        
        # Sort by priority
        signals.sort(key=lambda x: x.priority, reverse=True)
        
        return signals
    
    def create_investment_report(self, signals: List[InvestmentSignal]) -> Dict:
        """Create comprehensive investment report"""
        try:
            # Categorize signals
            strong_buys = [s for s in signals if s.signal_type == "STRONG_BUY"]
            buys = [s for s in signals if s.signal_type == "BUY"]
            sells = [s for s in signals if s.signal_type in ["SELL", "STRONG_SELL"]]
            holds = [s for s in signals if s.signal_type == "HOLD"]
            
            # Calculate portfolio allocation
            total_allocation = sum(s.position_size for s in strong_buys + buys)
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'total_signals': len(signals),
                'summary': {
                    'strong_buys': len(strong_buys),
                    'buys': len(buys),
                    'holds': len(holds),
                    'sells': len(sells),
                    'total_buy_allocation': total_allocation
                },
                'top_recommendations': {
                    'strong_buys': [
                        {
                            'symbol': s.symbol,
                            'confidence': s.confidence,
                            'target_price': s.target_price,
                            'position_size': s.position_size,
                            'time_horizon': s.time_horizon,
                            'key_reasons': s.reasoning[:3]  # Top 3 reasons
                        }
                        for s in strong_buys[:5]  # Top 5
                    ],
                    'buys': [
                        {
                            'symbol': s.symbol,
                            'confidence': s.confidence,
                            'target_price': s.target_price,
                            'position_size': s.position_size,
                            'time_horizon': s.time_horizon,
                            'key_reasons': s.reasoning[:3]
                        }
                        for s in buys[:5]
                    ]
                },
                'risk_analysis': {
                    'high_risk_positions': len([s for s in signals if s.risk_level == "high"]),
                    'medium_risk_positions': len([s for s in signals if s.risk_level == "medium"]),
                    'low_risk_positions': len([s for s in signals if s.risk_level == "low"]),
                    'avg_confidence': np.mean([s.confidence for s in signals]) if signals else 0
                },
                'action_items': self.generate_action_items(signals),
                'detailed_signals': [
                    {
                        'symbol': s.symbol,
                        'signal_type': s.signal_type,
                        'confidence': s.confidence,
                        'target_price': s.target_price,
                        'stop_loss': s.stop_loss,
                        'time_horizon': s.time_horizon,
                        'risk_level': s.risk_level,
                        'position_size': s.position_size,
                        'priority': s.priority,
                        'reasoning': s.reasoning
                    }
                    for s in signals
                ]
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error creating investment report: {e}")
            return {}
    
    def generate_action_items(self, signals: List[InvestmentSignal]) -> List[Dict]:
        """Generate actionable items from signals"""
        actions = []
        
        # Immediate buy opportunities
        strong_buys = [s for s in signals if s.signal_type == "STRONG_BUY"]
        if strong_buys:
            actions.append({
                'priority': 'High',
                'action': 'Execute Strong Buy Orders',
                'description': f'Place orders for {len(strong_buys)} strong buy signals',
                'symbols': [s.symbol for s in strong_buys[:3]],
                'timeline': 'Within 24 hours'
            })
        
        # Research high-confidence opportunities
        high_conf_buys = [s for s in signals if s.signal_type == "BUY" and s.confidence > 0.8]
        if high_conf_buys:
            actions.append({
                'priority': 'Medium',
                'action': 'Research High-Confidence Buys',
                'description': f'Detailed analysis of {len(high_conf_buys)} high-confidence opportunities',
                'symbols': [s.symbol for s in high_conf_buys],
                'timeline': 'Within 3 days'
            })
        
        # Monitor sell signals
        sells = [s for s in signals if s.signal_type in ["SELL", "STRONG_SELL"]]
        if sells:
            actions.append({
                'priority': 'High',
                'action': 'Review Sell Signals',
                'description': f'Consider exiting positions in {len(sells)} securities',
                'symbols': [s.symbol for s in sells],
                'timeline': 'Within 48 hours'
            })
        
        return actions
    
    def save_investment_report(self, report: Dict, filename: str = None):
        """Save investment report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"investment_signals_{timestamp}.json"
        
        filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
        
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Investment report saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving investment report: {e}")

def main():
    """Main execution function"""
    engine = InvestmentSignalEngine()
    
    # Generate signals for all target stocks
    signals = engine.generate_portfolio_signals()
    
    # Create comprehensive report
    report = engine.create_investment_report(signals)
    
    # Save report
    engine.save_investment_report(report)
    
    # Print summary
    print("\n=== INVESTMENT SIGNALS SUMMARY ===")
    print(f"Generated: {report['generated_at']}")
    print(f"Total signals analyzed: {report['total_signals']}")
    
    summary = report.get('summary', {})
    print(f"\n📊 SIGNAL BREAKDOWN:")
    print(f"  🟢 Strong Buys: {summary.get('strong_buys', 0)}")
    print(f"  🔵 Buys: {summary.get('buys', 0)}")
    print(f"  ⚪ Holds: {summary.get('holds', 0)}")
    print(f"  🔴 Sells: {summary.get('sells', 0)}")
    print(f"  💰 Total Buy Allocation: {summary.get('total_buy_allocation', 0):.1%}")
    
    # Top recommendations
    strong_buys = report.get('top_recommendations', {}).get('strong_buys', [])
    if strong_buys:
        print(f"\n🎯 TOP STRONG BUY SIGNALS:")
        for rec in strong_buys:
            print(f"  {rec['symbol']}: {rec['confidence']:.1%} confidence, ${rec['target_price']:.2f} target")
    
    # Action items
    actions = report.get('action_items', [])
    if actions:
        print(f"\n📋 IMMEDIATE ACTIONS:")
        for action in actions:
            print(f"  {action['priority']}: {action['action']} ({action['timeline']})")

if __name__ == "__main__":
    main()