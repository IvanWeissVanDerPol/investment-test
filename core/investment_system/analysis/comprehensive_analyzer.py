"""
Comprehensive Investment Analyzer
Integrates all advanced features: Options flow, AI predictions, social sentiment, etc.
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import logging
import time
from pathlib import Path

# Import all our advanced modules (with error handling)
try:
    from advanced_market_analyzer import AdvancedMarketAnalyzer
except ImportError:
    AdvancedMarketAnalyzer = None

try:
    from ai_prediction_engine import AIPredictionEngine
except ImportError:
    AIPredictionEngine = None

try:
    from social_sentiment_analyzer import SocialSentimentAnalyzer
except ImportError:
    SocialSentimentAnalyzer = None

try:
    from news_sentiment_analyzer import NewsSentimentAnalyzer
except ImportError:
    NewsSentimentAnalyzer = None

try:
    from quick_analysis import get_stock_analysis
except ImportError:
    get_stock_analysis = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveAnalyzer:
    def __init__(self, config_file: str = "config.json"):
        """Initialize comprehensive analyzer with all modules"""
        self.config = self.load_config(config_file)
        
        # Initialize all analyzers
        self.market_analyzer = AdvancedMarketAnalyzer(config_file)
        self.ai_engine = AIPredictionEngine(config_file)
        self.social_analyzer = SocialSentimentAnalyzer(config_file)
        self.news_analyzer = NewsSentimentAnalyzer(config_file)
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return {}
    
    def generate_comprehensive_analysis(self, symbols: List[str]) -> Dict:
        """Generate the most comprehensive investment analysis possible"""
        try:
            logger.info(f"Starting comprehensive analysis for {len(symbols)} symbols")
            
            comprehensive_report = {
                'generated_at': datetime.now().isoformat(),
                'analysis_type': 'comprehensive_enterprise_grade',
                'symbols_analyzed': symbols,
                'user_profile': {
                    'dukascopy_balance': 900,
                    'available_for_investment': 700,
                    'investment_focus': 'AI/Robotics with comprehensive market intelligence'
                },
                
                # Core Analysis Modules
                'technical_analysis': {},
                'news_sentiment': {},
                'advanced_market_analysis': {},
                'ai_predictions': {},
                'social_sentiment': {},
                
                # Integrated Insights
                'master_recommendations': {},
                'risk_assessment': {},
                'portfolio_optimization': {},
                'alerts_and_warnings': [],
                'investment_thesis': {},
                'execution_plan': {}
            }
            
            print("Phase 1: Technical Analysis...")
            # Technical analysis for all symbols
            for symbol in symbols:
                print(f"   Technical analysis: {symbol}")
                try:
                    comprehensive_report['technical_analysis'][symbol] = get_stock_analysis(symbol)
                except Exception as e:
                    logger.warning(f"Technical analysis failed for {symbol}: {e}")
            
            print("Phase 2: News Sentiment Analysis...")
            # News sentiment analysis
            try:
                news_analysis = self.news_analyzer.analyze_portfolio_news(symbols[:5])  # Top 5 for performance
                comprehensive_report['news_sentiment'] = news_analysis
            except Exception as e:
                logger.warning(f"News analysis failed: {e}")
            
            print("Phase 3: Advanced Market Analysis...")
            # Advanced market analysis (Options, Forex, Bonds, Sector Rotation)
            try:
                advanced_analysis = self.market_analyzer.generate_comprehensive_analysis(symbols[:5])
                comprehensive_report['advanced_market_analysis'] = advanced_analysis
            except Exception as e:
                logger.warning(f"Advanced market analysis failed: {e}")
            
            print("Phase 4: AI Predictions...")
            # AI predictions and pattern recognition
            try:
                ai_analysis = self.ai_engine.generate_ai_analysis(symbols[:3])  # Top 3 for ML performance
                comprehensive_report['ai_predictions'] = ai_analysis
            except Exception as e:
                logger.warning(f"AI predictions failed: {e}")
            
            print("Phase 5: Social Sentiment Analysis...")
            # Social media sentiment
            try:
                social_analysis = self.social_analyzer.generate_social_sentiment_report(symbols[:3])
                comprehensive_report['social_sentiment'] = social_analysis
            except Exception as e:
                logger.warning(f"Social sentiment analysis failed: {e}")
            
            print("Phase 6: Master Integration...")
            # Generate master recommendations by combining all data
            comprehensive_report['master_recommendations'] = self.generate_master_recommendations(comprehensive_report)
            
            # Generate integrated risk assessment
            comprehensive_report['risk_assessment'] = self.generate_integrated_risk_assessment(comprehensive_report)
            
            # Generate portfolio optimization
            comprehensive_report['portfolio_optimization'] = self.generate_portfolio_optimization(comprehensive_report)
            
            # Generate alerts and warnings
            comprehensive_report['alerts_and_warnings'] = self.generate_integrated_alerts(comprehensive_report)
            
            # Generate investment thesis
            comprehensive_report['investment_thesis'] = self.generate_investment_thesis(comprehensive_report)
            
            # Generate execution plan
            comprehensive_report['execution_plan'] = self.generate_execution_plan(comprehensive_report)
            
            return comprehensive_report
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {'error': str(e)}
    
    def generate_master_recommendations(self, report: Dict) -> Dict:
        """Generate master recommendations by integrating all analysis modules"""
        try:
            master_recs = {
                'top_opportunities': [],
                'avoid_list': [],
                'confidence_scores': {},
                'multi_factor_analysis': {},
                'recommendation_basis': {}
            }
            
            symbols = report.get('symbols_analyzed', [])
            
            for symbol in symbols:
                # Collect scores from different modules
                scores = {
                    'technical': 0,
                    'news': 0,
                    'advanced_market': 0,
                    'ai_prediction': 0,
                    'social_sentiment': 0
                }
                
                confidence_factors = []
                
                # Technical Analysis Score
                tech_data = report.get('technical_analysis', {}).get(symbol, {})
                if tech_data.get('recommendation') == 'STRONG BUY':
                    scores['technical'] = 10
                    confidence_factors.append("Strong technical signals")
                elif tech_data.get('recommendation') == 'BUY':
                    scores['technical'] = 7
                    confidence_factors.append("Positive technical signals")
                elif tech_data.get('recommendation') == 'HOLD':
                    scores['technical'] = 5
                elif tech_data.get('recommendation') == 'CAUTION':
                    scores['technical'] = 2
                
                # News Sentiment Score
                news_data = report.get('news_sentiment', {}).get('stock_analysis', {}).get(symbol, {})
                if news_data:
                    news_summary = news_data.get('summary', {})
                    sentiment = news_summary.get('overall_sentiment', 'neutral')
                    if sentiment == 'positive':
                        scores['news'] = 8
                        confidence_factors.append("Positive news sentiment")
                    elif sentiment == 'neutral':
                        scores['news'] = 5
                    else:
                        scores['news'] = 2
                        confidence_factors.append("Negative news sentiment")
                
                # Advanced Market Score
                advanced_data = report.get('advanced_market_analysis', {})
                
                # Options flow
                options_data = advanced_data.get('options_flow', {}).get(symbol, {})
                if options_data.get('sentiment') == 'bullish':
                    scores['advanced_market'] += 3
                    confidence_factors.append("Bullish options flow")
                elif options_data.get('sentiment') == 'bearish':
                    scores['advanced_market'] -= 2
                
                # Bond yield impact
                bond_impact = advanced_data.get('bond_yield_impact', {}).get('stock_impacts', {}).get(symbol, {})
                if bond_impact.get('expected_impact_pct', 0) > 1:
                    scores['advanced_market'] += 2
                elif bond_impact.get('expected_impact_pct', 0) < -2:
                    scores['advanced_market'] -= 2
                
                # AI Predictions Score
                ai_data = report.get('ai_predictions', {})
                ai_predictions = ai_data.get('price_predictions', {}).get(symbol, {})
                if ai_predictions.get('prediction_trend', {}).get('trend') in ['bullish', 'strongly_bullish']:
                    scores['ai_prediction'] = 8
                    confidence_factors.append("AI models predict upward trend")
                elif ai_predictions.get('prediction_trend', {}).get('trend') in ['bearish', 'strongly_bearish']:
                    scores['ai_prediction'] = 2
                else:
                    scores['ai_prediction'] = 5
                
                # Pattern recognition
                patterns = ai_data.get('pattern_analysis', {}).get(symbol, {})
                if patterns.get('bullish_patterns', 0) > patterns.get('bearish_patterns', 0):
                    scores['ai_prediction'] += 2
                    confidence_factors.append("Bullish technical patterns detected")
                
                # Social Sentiment Score
                social_data = report.get('social_sentiment', {})
                wsb_data = social_data.get('wsb_analysis', {}).get(symbol, {})
                if wsb_data.get('overall_sentiment') in ['bullish', 'very_bullish']:
                    scores['social_sentiment'] = 7
                    confidence_factors.append("Positive social media sentiment")
                elif wsb_data.get('overall_sentiment') == 'bearish':
                    scores['social_sentiment'] = 3
                else:
                    scores['social_sentiment'] = 5
                
                # Calculate overall score (weighted average)
                weights = {
                    'technical': 0.30,
                    'news': 0.20,
                    'advanced_market': 0.20,
                    'ai_prediction': 0.20,
                    'social_sentiment': 0.10
                }
                
                overall_score = sum(scores[factor] * weights[factor] for factor in scores)
                
                # Calculate confidence based on consistency and number of positive factors
                confidence = len(confidence_factors) / 8.0  # Max 8 possible factors
                consistency_score = 1 - (max(scores.values()) - min(scores.values())) / 10.0  # Penalty for inconsistency
                final_confidence = (confidence + consistency_score) / 2.0
                
                master_recs['confidence_scores'][symbol] = {
                    'overall_score': round(overall_score, 2),
                    'confidence': round(final_confidence, 2),
                    'individual_scores': scores,
                    'confidence_factors': confidence_factors
                }
                
                master_recs['multi_factor_analysis'][symbol] = {
                    'recommendation': self.score_to_recommendation(overall_score),
                    'strength': 'high' if final_confidence > 0.7 else 'medium' if final_confidence > 0.5 else 'low',
                    'consensus': len(confidence_factors) >= 4  # Consensus if 4+ positive factors
                }
                
                # Categorize recommendations
                if overall_score >= 8 and final_confidence > 0.6:
                    master_recs['top_opportunities'].append({
                        'symbol': symbol,
                        'score': round(overall_score, 2),
                        'confidence': round(final_confidence, 2),
                        'key_factors': confidence_factors[:3]  # Top 3 factors
                    })
                elif overall_score <= 3 or final_confidence < 0.3:
                    master_recs['avoid_list'].append({
                        'symbol': symbol,
                        'score': round(overall_score, 2),
                        'reasons': self.get_avoid_reasons(scores, symbol, report)
                    })
            
            # Sort opportunities by score
            master_recs['top_opportunities'].sort(key=lambda x: x['score'], reverse=True)
            
            return master_recs
            
        except Exception as e:
            logger.error(f"Error generating master recommendations: {e}")
            return {}
    
    def score_to_recommendation(self, score: float) -> str:
        """Convert numeric score to recommendation"""
        if score >= 8.5:
            return "STRONG BUY"
        elif score >= 7:
            return "BUY"
        elif score >= 6:
            return "MODERATE BUY"
        elif score >= 4:
            return "HOLD"
        elif score >= 3:
            return "WEAK HOLD"
        else:
            return "AVOID"
    
    def get_avoid_reasons(self, scores: Dict, symbol: str, report: Dict) -> List[str]:
        """Get reasons to avoid a stock"""
        reasons = []
        
        if scores['technical'] <= 3:
            reasons.append("Weak technical indicators")
        if scores['news'] <= 3:
            reasons.append("Negative news sentiment")
        if scores['ai_prediction'] <= 3:
            reasons.append("AI models predict downward trend")
        if scores['social_sentiment'] <= 3:
            reasons.append("Bearish social media sentiment")
        
        return reasons
    
    def generate_integrated_risk_assessment(self, report: Dict) -> Dict:
        """Generate comprehensive risk assessment"""
        try:
            risk_assessment = {
                'overall_portfolio_risk': 'medium',
                'individual_stock_risks': {},
                'market_environment_risks': [],
                'systematic_risks': [],
                'idiosyncratic_risks': {},
                'risk_mitigation_strategies': []
            }
            
            # Market environment risks
            advanced_data = report.get('advanced_market_analysis', {})
            
            # Bond yield risk
            bond_data = advanced_data.get('bond_yield_impact', {})
            if bond_data.get('yield_trend') in ['rising', 'rapidly_rising']:
                risk_assessment['market_environment_risks'].append({
                    'type': 'Rising Interest Rates',
                    'impact': 'High on growth stocks',
                    'current_level': f"{bond_data.get('current_10y_yield', 0):.2f}%"
                })
            
            # USD strength risk
            forex_data = advanced_data.get('forex_impact', {})
            if forex_data.get('usd_trend') == 'strengthening':
                risk_assessment['systematic_risks'].append({
                    'type': 'USD Strength',
                    'impact': 'Negative for international stocks',
                    'affected_stocks': list(forex_data.get('stock_impacts', {}).keys())
                })
            
            # Individual stock risks
            symbols = report.get('symbols_analyzed', [])
            for symbol in symbols:
                stock_risks = []
                
                # Volatility risk
                ai_data = report.get('ai_predictions', {})
                vol_forecast = ai_data.get('volatility_forecasts', {}).get(symbol, {})
                if vol_forecast.get('volatility_regime') == 'high_volatility':
                    stock_risks.append("High volatility expected")
                
                # Anomaly risk
                anomaly_data = ai_data.get('anomaly_detection', {}).get(symbol, {})
                if anomaly_data.get('anomaly_level') in ['high', 'medium']:
                    stock_risks.append("Unusual trading patterns detected")
                
                # News risk
                news_data = report.get('news_sentiment', {})
                stock_news = news_data.get('stock_analysis', {}).get(symbol, {})
                if stock_news.get('summary', {}).get('overall_sentiment') == 'negative':
                    stock_risks.append("Negative news sentiment")
                
                if stock_risks:
                    risk_assessment['individual_stock_risks'][symbol] = stock_risks
            
            # Risk mitigation strategies
            risk_assessment['risk_mitigation_strategies'] = [
                "Diversify across multiple sectors and asset classes",
                "Use position sizing based on volatility and confidence levels",
                "Monitor daily for changes in risk factors",
                "Maintain cash reserves for opportunities and protection",
                "Set stop-loss orders for all positions"
            ]
            
            # Overall portfolio risk
            high_risk_count = len([s for s in symbols if s in risk_assessment['individual_stock_risks']])
            risk_ratio = high_risk_count / len(symbols) if symbols else 0
            
            if risk_ratio > 0.6:
                risk_assessment['overall_portfolio_risk'] = 'high'
            elif risk_ratio > 0.3:
                risk_assessment['overall_portfolio_risk'] = 'medium'
            else:
                risk_assessment['overall_portfolio_risk'] = 'low'
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Error generating risk assessment: {e}")
            return {}
    
    def generate_portfolio_optimization(self, report: Dict) -> Dict:
        """Generate AI-optimized portfolio allocation"""
        try:
            optimization = {
                'recommended_allocation': {},
                'allocation_rationale': {},
                'rebalancing_triggers': [],
                'performance_expectations': {},
                'diversification_analysis': {}
            }
            
            available_capital = 700
            master_recs = report.get('master_recommendations', {})
            top_opportunities = master_recs.get('top_opportunities', [])
            
            if not top_opportunities:
                # Fallback: use technical analysis recommendations
                logger.warning("No master recommendations found, falling back to technical analysis")
                return self.generate_fallback_portfolio(report, available_capital)
            
            # Calculate allocations based on scores and confidence
            total_score = sum(opp['score'] * opp['confidence'] for opp in top_opportunities)
            
            if total_score == 0:
                # Handle zero total score
                logger.warning("Zero total score in opportunities, using equal weighting")
                total_score = len(top_opportunities)
                for opp in top_opportunities:
                    opp['score'] = 1.0
                    opp['confidence'] = 1.0
            
            for opp in top_opportunities[:5]:  # Top 5 opportunities
                symbol = opp['symbol']
                weighted_score = opp['score'] * opp['confidence']
                base_allocation = (weighted_score / total_score) * 0.6  # Use 60% of capital for top picks
                
                # Adjust for risk
                risk_data = report.get('risk_assessment', {}).get('individual_stock_risks', {})
                risk_adjustment = 1.0
                if symbol in risk_data:
                    risk_count = len(risk_data[symbol])
                    risk_adjustment = max(0.5, 1.0 - (risk_count * 0.1))  # Reduce allocation for risky stocks
                
                final_allocation = base_allocation * risk_adjustment * available_capital
                final_allocation = min(final_allocation, available_capital * 0.25)  # Max 25% per position
                final_allocation = max(final_allocation, available_capital * 0.05)  # Min 5% per position
                
                optimization['recommended_allocation'][symbol] = {
                    'amount': round(final_allocation, 2),
                    'percentage': round((final_allocation / available_capital) * 100, 1),
                    'rationale': f"Score: {opp['score']}, Confidence: {opp['confidence']:.1%}"
                }
                
                optimization['allocation_rationale'][symbol] = {
                    'base_score': opp['score'],
                    'confidence_level': opp['confidence'],
                    'risk_adjustment': risk_adjustment,
                    'key_factors': opp.get('key_factors', [])
                }
            
            # Calculate remaining cash allocation
            total_allocated = sum(alloc['amount'] for alloc in optimization['recommended_allocation'].values())
            remaining_cash = available_capital - total_allocated
            
            optimization['recommended_allocation']['CASH'] = {
                'amount': round(remaining_cash, 2),
                'percentage': round((remaining_cash / available_capital) * 100, 1),
                'rationale': 'Opportunity buffer and risk management'
            }
            
            # Performance expectations
            expected_returns = []
            for symbol, alloc in optimization['recommended_allocation'].items():
                if symbol != 'CASH':
                    # Simple expected return based on score (simplified)
                    score = optimization['allocation_rationale'][symbol]['base_score']
                    expected_annual_return = (score - 5) * 0.05  # Score of 10 = 25% expected return
                    expected_returns.append(expected_annual_return * (alloc['percentage'] / 100))
            
            optimization['performance_expectations'] = {
                'expected_annual_return': f"{sum(expected_returns) * 100:.1f}%",
                'risk_level': report.get('risk_assessment', {}).get('overall_portfolio_risk', 'medium'),
                'diversification_score': min(len(optimization['recommended_allocation']) - 1, 5) / 5.0  # Exclude cash
            }
            
            # Add rebalancing triggers
            optimization['rebalancing_triggers'] = [
                "Weekly review of AI predictions and sentiment changes",
                "Monthly portfolio performance review",
                "Significant news events or earnings announcements",
                "Risk level changes or volatility spikes",
                "New high-confidence opportunities emerge"
            ]
            
            # Add diversification analysis
            optimization['diversification_analysis'] = {
                'sector_concentration': self.analyze_sector_concentration(optimization['recommended_allocation']),
                'position_sizes': [alloc['percentage'] for symbol, alloc in optimization['recommended_allocation'].items() if symbol != 'CASH'],
                'max_position_size': max([alloc['percentage'] for symbol, alloc in optimization['recommended_allocation'].items() if symbol != 'CASH'], default=0),
                'cash_percentage': optimization['recommended_allocation'].get('CASH', {}).get('percentage', 0)
            }
            
            return optimization
            
        except Exception as e:
            logger.error(f"Error generating portfolio optimization: {e}")
            return {}
    
    def generate_fallback_portfolio(self, report: Dict, available_capital: float) -> Dict:
        """Generate portfolio when master recommendations fail"""
        try:
            fallback_optimization = {
                'recommended_allocation': {},
                'allocation_rationale': {},
                'rebalancing_triggers': [],
                'performance_expectations': {},
                'diversification_analysis': {},
                'note': 'Generated using technical analysis fallback'
            }
            
            # Use technical analysis data
            technical_data = report.get('technical_analysis', {})
            
            # Find stocks with buy recommendations
            buy_candidates = []
            for symbol, data in technical_data.items():
                if data.get('recommendation') in ['BUY', 'STRONG BUY']:
                    buy_candidates.append({
                        'symbol': symbol,
                        'score': data.get('score', 1),
                        'confidence': data.get('confidence', 0.5),
                        'recommendation': data.get('recommendation')
                    })
            
            if not buy_candidates:
                # Last resort: equal allocation to top 3 symbols
                symbols = list(technical_data.keys())[:3]
                for symbol in symbols:
                    fallback_optimization['recommended_allocation'][symbol] = {
                        'amount': round(available_capital * 0.2, 2),
                        'percentage': 20.0,
                        'rationale': 'Equal weight fallback allocation'
                    }
                
                fallback_optimization['recommended_allocation']['CASH'] = {
                    'amount': round(available_capital * 0.4, 2),
                    'percentage': 40.0,
                    'rationale': 'Conservative cash allocation due to limited opportunities'
                }
                
                return fallback_optimization
            
            # Sort by score and confidence
            buy_candidates.sort(key=lambda x: x['score'] * x['confidence'], reverse=True)
            
            # Allocate based on technical scores
            total_weight = sum(candidate['score'] * candidate['confidence'] for candidate in buy_candidates[:4])
            
            for candidate in buy_candidates[:4]:  # Top 4 technical picks
                symbol = candidate['symbol']
                weight = (candidate['score'] * candidate['confidence']) / total_weight
                allocation = weight * available_capital * 0.7  # Use 70% of capital
                
                fallback_optimization['recommended_allocation'][symbol] = {
                    'amount': round(allocation, 2),
                    'percentage': round((allocation / available_capital) * 100, 1),
                    'rationale': f"Technical analysis: {candidate['recommendation']}"
                }
                
                fallback_optimization['allocation_rationale'][symbol] = {
                    'base_score': candidate['score'],
                    'confidence_level': candidate['confidence'],
                    'source': 'technical_analysis'
                }
            
            # Add cash allocation
            allocated_amount = sum(alloc['amount'] for alloc in fallback_optimization['recommended_allocation'].values())
            cash_amount = available_capital - allocated_amount
            
            fallback_optimization['recommended_allocation']['CASH'] = {
                'amount': round(cash_amount, 2),
                'percentage': round((cash_amount / available_capital) * 100, 1),
                'rationale': 'Conservative cash buffer'
            }
            
            return fallback_optimization
            
        except Exception as e:
            logger.error(f"Error generating fallback portfolio: {e}")
            return {'error': 'Portfolio generation failed'}
    
    def analyze_sector_concentration(self, allocations: Dict) -> Dict:
        """Analyze sector concentration in portfolio"""
        try:
            # Simple sector mapping (in practice, you'd use a more comprehensive mapping)
            sector_mapping = {
                'NVDA': 'Technology',
                'MSFT': 'Technology', 
                'GOOGL': 'Technology',
                'META': 'Technology',
                'CRM': 'Technology',
                'TSLA': 'Consumer Discretionary',
                'AMZN': 'Consumer Discretionary',
                'AAPL': 'Technology',
                'TSM': 'Technology',
                'DE': 'Industrials'
            }
            
            sector_allocations = {}
            for symbol, alloc in allocations.items():
                if symbol != 'CASH':
                    sector = sector_mapping.get(symbol, 'Other')
                    if sector not in sector_allocations:
                        sector_allocations[sector] = 0
                    sector_allocations[sector] += alloc.get('percentage', 0)
            
            return {
                'by_sector': sector_allocations,
                'max_sector_concentration': max(sector_allocations.values()) if sector_allocations else 0,
                'sector_count': len(sector_allocations)
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing sector concentration: {e}")
            return {}
    
    def generate_integrated_alerts(self, report: Dict) -> List[Dict]:
        """Generate integrated alerts from all analysis modules"""
        alerts = []
        
        try:
            # Market environment alerts
            advanced_data = report.get('advanced_market_analysis', {})
            market_summary = advanced_data.get('market_summary', {})
            
            if market_summary.get('market_environment') == 'challenging':
                alerts.append({
                    'type': 'market_environment',
                    'priority': 'high',
                    'message': 'Challenging market environment detected',
                    'action': 'Consider reducing position sizes and increasing cash allocation'
                })
            
            # AI prediction alerts
            ai_data = report.get('ai_predictions', {})
            ai_summary = ai_data.get('ai_summary', {})
            
            if ai_summary.get('volatility_warnings'):
                for warning in ai_summary['volatility_warnings']:
                    alerts.append({
                        'type': 'volatility_warning',
                        'priority': 'medium',
                        'symbol': warning['symbol'],
                        'message': f"High volatility expected in {warning['symbol']}",
                        'action': 'Reduce position size or use wider stop losses'
                    })
            
            # Social sentiment alerts
            social_data = report.get('social_sentiment', {})
            social_alerts = social_data.get('sentiment_alerts', [])
            
            for social_alert in social_alerts:
                if social_alert.get('priority') == 'high':
                    alerts.append({
                        'type': 'social_sentiment',
                        'priority': social_alert['priority'],
                        'symbol': social_alert['symbol'],
                        'message': social_alert['message'],
                        'action': 'Monitor for unusual price movements'
                    })
            
            # News sentiment alerts
            news_data = report.get('news_sentiment', {})
            portfolio_summary = news_data.get('portfolio_summary', {})
            
            major_alerts = portfolio_summary.get('major_news_alerts', [])
            for news_alert in major_alerts:
                alerts.append({
                    'type': 'news_event',
                    'priority': 'medium',
                    'symbol': news_alert['symbol'],
                    'message': news_alert['alert_type'],
                    'action': 'Review news impact on investment thesis'
                })
            
            # Master recommendation alerts
            master_recs = report.get('master_recommendations', {})
            top_opportunities = master_recs.get('top_opportunities', [])
            
            for opp in top_opportunities:
                if opp['confidence'] > 0.8 and opp['score'] > 8.5:
                    alerts.append({
                        'type': 'strong_opportunity',
                        'priority': 'high',
                        'symbol': opp['symbol'],
                        'message': f"Strong investment opportunity: {opp['symbol']} (Score: {opp['score']}, Confidence: {opp['confidence']:.1%})",
                        'action': 'Consider immediate position entry'
                    })
        
        except Exception as e:
            logger.error(f"Error generating integrated alerts: {e}")
        
        return alerts
    
    def generate_investment_thesis(self, report: Dict) -> Dict:
        """Generate comprehensive investment thesis"""
        try:
            thesis = {
                'market_outlook': '',
                'key_themes': [],
                'investment_rationale': {},
                'risk_factors': [],
                'expected_outcomes': {},
                'time_horizon': 'medium_term'
            }
            
            # Market outlook
            advanced_data = report.get('advanced_market_analysis', {})
            market_env = advanced_data.get('market_summary', {}).get('market_environment', 'neutral')
            
            if market_env == 'favorable':
                thesis['market_outlook'] = "Favorable market conditions with multiple tailwinds supporting AI/robotics investments"
            elif market_env == 'challenging':
                thesis['market_outlook'] = "Challenging market environment requiring careful stock selection and risk management"
            else:
                thesis['market_outlook'] = "Neutral market environment with mixed signals requiring selective approach"
            
            # Key themes
            ai_data = report.get('ai_predictions', {})
            if ai_data.get('ai_summary', {}).get('overall_sentiment') == 'bullish':
                thesis['key_themes'].append("AI revolution driving long-term growth")
            
            social_data = report.get('social_sentiment', {})
            if social_data.get('overall_social_sentiment', {}).get('ai_buzz_level') == 'high':
                thesis['key_themes'].append("High retail investor interest in AI/tech stocks")
            
            news_data = report.get('news_sentiment', {})
            positive_stocks = news_data.get('portfolio_summary', {}).get('positive_stocks', [])
            if len(positive_stocks) > 3:
                thesis['key_themes'].append("Positive news flow supporting sector momentum")
            
            # Investment rationale for top picks
            master_recs = report.get('master_recommendations', {})
            for opp in master_recs.get('top_opportunities', [])[:3]:
                symbol = opp['symbol']
                thesis['investment_rationale'][symbol] = {
                    'core_thesis': f"Multi-factor analysis shows strong conviction for {symbol}",
                    'key_factors': opp.get('key_factors', []),
                    'confidence_level': opp['confidence'],
                    'expected_catalyst': 'Continued AI adoption and market expansion'
                }
            
            return thesis
            
        except Exception as e:
            logger.error(f"Error generating investment thesis: {e}")
            return {}
    
    def generate_execution_plan(self, report: Dict) -> Dict:
        """Generate detailed execution plan"""
        try:
            execution_plan = {
                'immediate_actions': [],
                'weekly_monitoring': [],
                'monthly_reviews': [],
                'rebalancing_triggers': [],
                'exit_strategies': {}
            }
            
            # Immediate actions
            master_recs = report.get('master_recommendations', {})
            top_opportunities = master_recs.get('top_opportunities', [])
            
            for opp in top_opportunities[:3]:  # Top 3 for immediate action
                execution_plan['immediate_actions'].append({
                    'action': f"Execute buy order for {opp['symbol']}",
                    'rationale': f"High conviction opportunity (Score: {opp['score']}, Confidence: {opp['confidence']:.1%})",
                    'timeline': 'Within 24-48 hours',
                    'position_size': f"As per portfolio optimization recommendations"
                })
            
            # Weekly monitoring
            execution_plan['weekly_monitoring'] = [
                "Review all AI/ML prediction updates",
                "Monitor social media sentiment changes",
                "Track news sentiment and major announcements",
                "Check for new options flow anomalies",
                "Assess sector rotation patterns"
            ]
            
            # Monthly reviews
            execution_plan['monthly_reviews'] = [
                "Comprehensive performance attribution analysis",
                "Risk assessment update and adjustment",
                "Portfolio rebalancing if needed",
                "Investment thesis validation",
                "Strategy refinement based on results"
            ]
            
            return execution_plan
            
        except Exception as e:
            logger.error(f"Error generating execution plan: {e}")
            return {}
    
    def create_executive_summary(self, report: Dict) -> str:
        """Create executive summary of comprehensive analysis"""
        try:
            master_recs = report.get('master_recommendations', {})
            risk_assessment = report.get('risk_assessment', {})
            portfolio_opt = report.get('portfolio_optimization', {})
            
            top_opportunities = master_recs.get('top_opportunities', [])
            top_3 = top_opportunities[:3] if len(top_opportunities) >= 3 else top_opportunities
            
            summary = f"""
=== COMPREHENSIVE INVESTMENT ANALYSIS EXECUTIVE SUMMARY ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

INVESTMENT PROFILE:
• Dukascopy Balance: $900
• Available Capital: $700
• Strategy: AI/Robotics Multi-Factor Analysis

TOP OPPORTUNITIES IDENTIFIED:
"""
            
            for i, opp in enumerate(top_3, 1):
                summary += f"""
{i}. {opp['symbol']} - Score: {opp['score']}/10 (Confidence: {opp['confidence']:.1%})
   Key Factors: {', '.join(opp['key_factors'][:2])}"""
            
            # Portfolio allocation
            allocations = portfolio_opt.get('recommended_allocation', {})
            if allocations:
                summary += f"\n\nRECOMMENDED ALLOCATION:"
                for symbol, alloc in allocations.items():
                    if symbol != 'CASH':
                        summary += f"\n• {symbol}: ${alloc['amount']} ({alloc['percentage']}%)"
                
                cash_alloc = allocations.get('CASH', {})
                summary += f"\n• Cash Buffer: ${cash_alloc.get('amount', 0)} ({cash_alloc.get('percentage', 0)}%)"
            
            # Risk assessment
            overall_risk = risk_assessment.get('overall_portfolio_risk', 'medium')
            summary += f"\n\nRISK ASSESSMENT: {overall_risk.upper()}"
            
            # Expected performance
            performance = portfolio_opt.get('performance_expectations', {})
            expected_return = performance.get('expected_annual_return', 'TBD')
            summary += f"\nExpected Annual Return: {expected_return}"
            
            # Key alerts
            alerts = report.get('alerts_and_warnings', [])
            high_priority_alerts = [a for a in alerts if a.get('priority') == 'high']
            if high_priority_alerts:
                summary += f"\n\nHIGH PRIORITY ALERTS:"
                for alert in high_priority_alerts[:3]:
                    summary += f"\nWARNING: {alert.get('message', '')}"
            
            summary += f"\n\nNEXT ACTIONS:"
            summary += f"\n1. Review detailed analysis and recommendations"
            summary += f"\n2. Execute top opportunity trades in Dukascopy"
            summary += f"\n3. Set up monitoring for weekly updates"
            summary += f"\n4. Implement risk management strategies"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating executive summary: {e}")
            return "Error generating executive summary"
    
    def save_comprehensive_report(self, report: Dict, filename: str = None):
        """Save comprehensive report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_analysis_{timestamp}.json"
        
        # Ensure comprehensive reports directory exists
        reports_dir = Path("reports/comprehensive")
        reports_dir.mkdir(parents=True, exist_ok=True)
        filepath = reports_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Comprehensive report saved to {filepath}")
            
            # Also save executive summary
            summary = self.create_executive_summary(report)
            summary_filename = filename.replace('.json', '_summary.txt')
            summary_filepath = reports_dir / summary_filename
            
            with open(summary_filepath, 'w', encoding='utf-8') as f:
                f.write(summary)
            logger.info(f"Executive summary saved to {summary_filepath}")
            
        except Exception as e:
            logger.error(f"Error saving comprehensive report: {e}")

def main():
    """Main execution function"""
    analyzer = ComprehensiveAnalyzer()
    
    # Target stocks for comprehensive analysis
    target_stocks = [
        "NVDA", "MSFT", "TSLA", "DE", "TSM",
        "AMZN", "GOOGL", "META", "AAPL", "CRM"
    ]
    
    print("STARTING COMPREHENSIVE ENTERPRISE-GRADE ANALYSIS")
    print("=" * 60)
    print("This includes ALL advanced features:")
    print("• Technical Analysis")
    print("• News Sentiment Analysis") 
    print("• Options Flow & Market Analysis")
    print("• AI/ML Predictions & Pattern Recognition")
    print("• Social Media Sentiment")
    print("• Master Integration & Portfolio Optimization")
    print("=" * 60)
    
    # Generate comprehensive analysis
    report = analyzer.generate_comprehensive_analysis(target_stocks)
    
    # Save report
    analyzer.save_comprehensive_report(report)
    
    # Print executive summary
    summary = analyzer.create_executive_summary(report)
    print(summary)
    
    print(f"\n" + "=" * 60)
    print("COMPREHENSIVE ANALYSIS COMPLETE")
    print("Full report saved to reports/ directory")
    print("Executive summary saved separately")
    print("=" * 60)

if __name__ == "__main__":
    main()