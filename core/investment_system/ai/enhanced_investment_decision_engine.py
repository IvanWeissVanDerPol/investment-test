"""
Enhanced AI Investment Decision Engine

Integrates YouTube market intelligence with existing AI analysis and ethics screening
to create the world's most comprehensive individual investment decision system.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import asdict

from .claude_client import ClaudeInvestmentClient
from ..integrations.ethics_integration import EthicsIntegratedAnalyzer
from ..analysis.youtube_market_intelligence import get_market_intelligence, MarketIntelligenceSignal
from ..utils.cache_manager import CacheManager
from ..utils.config_loader import ConfigurationManager

logger = logging.getLogger(__name__)

class EnhancedAIInvestmentDecisionEngine:
    """
    Next-generation AI investment decision engine that combines:
    - Global YouTube analyst intelligence (39+ channels)
    - Ethics screening and sustainability analysis
    - Claude AI market insights and analysis
    - Portfolio optimization recommendations
    - Multi-dimensional confidence scoring
    """
    
    def __init__(self, config_path: str = "config"):
        """Initialize the enhanced AI decision engine"""
        
        self.ethics_analyzer = EthicsIntegratedAnalyzer(config_path)
        self.claude_client = ClaudeInvestmentClient()
        self.youtube_intelligence = get_market_intelligence()
        self.cache_manager = CacheManager()
        self.config_manager = ConfigurationManager()
        
        # Enhanced decision weights with YouTube intelligence
        self.decision_weights = {
            "ethics_score": 0.30,           # 30% ethics/sustainability 
            "ai_analysis": 0.25,            # 25% Claude AI analysis
            "youtube_intelligence": 0.25,   # 25% YouTube analyst consensus
            "technical_analysis": 0.15,     # 15% technical factors
            "market_context": 0.05          # 5% general market conditions
        }
        
        # Signal confidence thresholds
        self.confidence_thresholds = {
            "very_high_confidence": 0.85,
            "high_confidence": 0.75,
            "medium_confidence": 0.60,
            "low_confidence": 0.45,
            "very_low_confidence": 0.30
        }
        
        # YouTube intelligence weights
        self.youtube_weights = {
            "signal_confidence": 0.40,      # YouTube signal confidence
            "analyst_quality": 0.30,        # Average analyst quality
            "consensus_strength": 0.20,     # How much analysts agree
            "data_freshness": 0.10          # How recent the data is
        }
        
        logger.info("Enhanced AI Investment Decision Engine initialized with YouTube intelligence")
    
    def analyze_investment_decision(self, symbol: str, portfolio_context: Dict, 
                                  decision_type: str = "buy") -> Dict[str, Any]:
        """
        Comprehensive AI-powered investment decision analysis with YouTube intelligence
        
        Args:
            symbol: Stock symbol to analyze
            portfolio_context: Current portfolio information
            decision_type: "buy", "sell", or "hold"
            
        Returns:
            Enhanced decision analysis with YouTube intelligence
        """
        logger.info(f"Running enhanced AI decision analysis for {symbol} ({decision_type})")
        
        # Check cache first
        cache_key = f"enhanced_ai_decision_{symbol}_{decision_type}_{datetime.now().strftime('%Y%m%d')}"
        cached_result = self.cache_manager.get_cached_data('ai_predictions', symbol, {'decision_type': decision_type})
        
        if cached_result:
            logger.debug(f"Using cached enhanced AI decision for {symbol}")
            return cached_result
        
        try:
            analysis_start = datetime.now()
            
            # Step 1: Ethics screening with portfolio context
            logger.debug(f"Running ethics analysis for {symbol}")
            ethics_result = self.ethics_analyzer.screen_investment_with_context(
                symbol, portfolio_context
            )
            
            # Step 2: YouTube market intelligence analysis
            logger.debug(f"Gathering YouTube intelligence for {symbol}")
            youtube_intelligence = self._get_youtube_intelligence(symbol)
            
            # Step 3: AI analysis if Claude is available
            ai_analysis = None
            if self.claude_client.is_available():
                logger.debug(f"Running Claude AI analysis for {symbol}")
                stock_data = self._prepare_enhanced_stock_data(
                    symbol, portfolio_context, youtube_intelligence
                )
                ai_analysis = self.claude_client.analyze_stock(symbol, stock_data, ethics_result)
            
            # Step 4: Market context analysis with YouTube insights
            market_context = None
            if self.claude_client.is_available():
                logger.debug("Analyzing market context with YouTube insights")
                market_context = self._analyze_enhanced_market_context(youtube_intelligence)
            
            # Step 5: Generate final enhanced decision
            final_decision = self._generate_enhanced_decision(
                symbol, ethics_result, ai_analysis, youtube_intelligence,
                market_context, portfolio_context, decision_type
            )
            
            # Add processing metadata
            final_decision['processing_time_seconds'] = (datetime.now() - analysis_start).total_seconds()
            final_decision['analysis_timestamp'] = datetime.now().isoformat()
            final_decision['engine_version'] = 'enhanced_v2.0'
            
            # Cache the result for 6 hours
            self.cache_manager.cache_data('ai_predictions', symbol, final_decision, {'decision_type': decision_type})
            
            logger.info(f"Enhanced decision analysis completed for {symbol} in {final_decision['processing_time_seconds']:.1f}s")
            
            return final_decision
            
        except Exception as e:
            logger.error(f"Error in enhanced AI decision analysis for {symbol}: {e}")
            return self._generate_error_response(symbol, str(e))
    
    def _get_youtube_intelligence(self, symbol: str) -> Dict[str, Any]:
        """Get YouTube market intelligence for a specific symbol"""
        try:
            # Try to get recent intelligence data from cache first
            cache_key = f"youtube_intelligence_{symbol}_daily"
            cached_intelligence = self.cache_manager.get_cached_data('youtube_intelligence', symbol)
            
            if cached_intelligence:
                return cached_intelligence
            
            # Generate fresh intelligence for this symbol
            processed_contents = self.youtube_intelligence.process_channel_batch(days_back=2)
            consensus = self.youtube_intelligence.build_stock_consensus(processed_contents, symbol)
            signal = self.youtube_intelligence.generate_investment_signal(consensus)
            
            intelligence_data = {
                'has_signal': signal is not None,
                'signal': asdict(signal) if signal else None,
                'consensus_data': consensus,
                'analyst_coverage': consensus.get('analysts_covering', 0),
                'total_mentions': consensus.get('total_mentions', 0),
                'avg_sentiment': consensus.get('avg_sentiment', 0.0),
                'quality_weighted_sentiment': consensus.get('quality_weighted_sentiment', 0.0),
                'data_freshness': consensus.get('data_freshness', 0.0),
                'regional_sentiment': dict(consensus.get('regional_sentiment', {})),
                'recommendation_distribution': consensus.get('recommendation_distribution', {}),
                'primary_recommendation': consensus.get('primary_recommendation'),
                'price_targets': {
                    'average': consensus.get('avg_price_target'),
                    'range': consensus.get('price_target_range'),
                    'count': len(consensus.get('price_targets', []))
                }
            }
            
            # Cache for 4 hours
            self.cache_manager.cache_data('youtube_intelligence', symbol, intelligence_data)
            
            return intelligence_data
            
        except Exception as e:
            logger.warning(f"Could not get YouTube intelligence for {symbol}: {e}")
            return {
                'has_signal': False,
                'signal': None,
                'analyst_coverage': 0,
                'total_mentions': 0,
                'avg_sentiment': 0.0,
                'error': str(e)
            }
    
    def _prepare_enhanced_stock_data(self, symbol: str, portfolio_context: Dict, 
                                   youtube_intelligence: Dict) -> Dict:
        """Prepare enhanced stock data including YouTube intelligence for Claude analysis"""
        stock_data = {
            'symbol': symbol,
            'portfolio_context': portfolio_context,
            'current_date': datetime.now().isoformat(),
            'youtube_intelligence': {
                'analyst_coverage': youtube_intelligence.get('analyst_coverage', 0),
                'total_mentions': youtube_intelligence.get('total_mentions', 0),
                'sentiment_score': youtube_intelligence.get('quality_weighted_sentiment', 0.0),
                'primary_recommendation': youtube_intelligence.get('primary_recommendation'),
                'price_target_consensus': youtube_intelligence.get('price_targets', {}).get('average'),
                'regional_consensus': youtube_intelligence.get('regional_sentiment', {}),
                'data_freshness': youtube_intelligence.get('data_freshness', 0.0)
            }
        }
        
        # Add signal details if available
        if youtube_intelligence.get('has_signal') and youtube_intelligence.get('signal'):
            signal = youtube_intelligence['signal']
            stock_data['youtube_intelligence']['signal_type'] = signal.get('signal_type')
            stock_data['youtube_intelligence']['signal_confidence'] = signal.get('confidence')
            stock_data['youtube_intelligence']['signal_strength'] = signal.get('signal_strength')
            stock_data['youtube_intelligence']['key_insights'] = signal.get('key_insights', [])
        
        return stock_data
    
    def _analyze_enhanced_market_context(self, youtube_intelligence: Dict) -> Dict:
        """Analyze market context with YouTube intelligence integration"""
        try:
            # Get general market overview from YouTube intelligence
            market_overview = self.youtube_intelligence.generate_market_overview({})
            
            market_context = {
                'overall_sentiment': market_overview.overall_market_sentiment,
                'market_uncertainty': market_overview.market_uncertainty,
                'analyst_consensus_strength': market_overview.analyst_consensus_strength,
                'trending_topics': market_overview.trending_topics[:5],
                'volatility_expectations': market_overview.volatility_expectations,
                'risk_sentiment': market_overview.risk_sentiment,
                'top_buy_signals_count': len(market_overview.top_buy_signals),
                'top_sell_signals_count': len(market_overview.top_sell_signals)
            }
            
            return market_context
            
        except Exception as e:
            logger.warning(f"Could not analyze enhanced market context: {e}")
            return {'error': str(e)}
    
    def _generate_enhanced_decision(self, symbol: str, ethics_result: Dict, ai_analysis: Dict,
                                  youtube_intelligence: Dict, market_context: Dict,
                                  portfolio_context: Dict, decision_type: str) -> Dict:
        """Generate final enhanced investment decision with all intelligence sources"""
        
        # Ensure we have valid data structures (defensive programming)
        ethics_result = ethics_result or {}
        ai_analysis = ai_analysis or {}
        youtube_intelligence = youtube_intelligence or {}
        market_context = market_context or {}
        portfolio_context = portfolio_context or {}
        
        # Calculate component scores
        ethics_score = self._calculate_ethics_score(ethics_result)
        ai_score = self._calculate_ai_score(ai_analysis)
        youtube_score = self._calculate_youtube_score(youtube_intelligence)
        technical_score = self._calculate_technical_score(symbol, market_context)
        market_score = self._calculate_market_score(market_context)
        
        # Calculate weighted overall score
        overall_score = (
            ethics_score * self.decision_weights['ethics_score'] +
            ai_score * self.decision_weights['ai_analysis'] +
            youtube_score * self.decision_weights['youtube_intelligence'] +
            technical_score * self.decision_weights['technical_analysis'] +
            market_score * self.decision_weights['market_context']
        )
        
        # Determine recommendation based on score and decision type
        recommendation = self._determine_enhanced_recommendation(
            overall_score, decision_type, youtube_intelligence, ethics_result
        )
        
        # Calculate confidence level
        confidence = self._calculate_enhanced_confidence(
            ethics_result, ai_analysis, youtube_intelligence, market_context
        )
        
        # Generate position sizing recommendation
        position_size = self._calculate_position_size(
            overall_score, confidence, portfolio_context, ethics_result
        )
        
        # Generate risk assessment
        risk_assessment = self._generate_risk_assessment(
            ethics_result, youtube_intelligence, market_context, confidence
        )
        
        # Compile final decision
        enhanced_decision = {
            'symbol': symbol,
            'decision_type': decision_type,
            'recommendation': recommendation,
            'overall_score': round(overall_score, 3),
            'confidence_level': confidence,
            'position_size_recommendation': position_size,
            
            # Component scores
            'component_scores': {
                'ethics_score': round(ethics_score, 3),
                'ai_analysis_score': round(ai_score, 3),
                'youtube_intelligence_score': round(youtube_score, 3),
                'technical_score': round(technical_score, 3),
                'market_context_score': round(market_score, 3)
            },
            
            # YouTube intelligence summary
            'youtube_intelligence_summary': {
                'has_coverage': youtube_intelligence.get('analyst_coverage', 0) > 0,
                'analyst_count': youtube_intelligence.get('analyst_coverage', 0),
                'total_mentions': youtube_intelligence.get('total_mentions', 0),
                'sentiment': youtube_intelligence.get('quality_weighted_sentiment', 0.0),
                'primary_recommendation': youtube_intelligence.get('primary_recommendation'),
                'signal_type': youtube_intelligence.get('signal', {}).get('signal_type') if youtube_intelligence.get('signal') else None,
                'signal_confidence': youtube_intelligence.get('signal', {}).get('confidence') if youtube_intelligence.get('signal') else None,
                'price_target': youtube_intelligence.get('price_targets', {}).get('average')
            },
            
            # Ethics summary
            'ethics_summary': {
                'is_green_investment': ethics_result.get('is_green_investment', False),
                'esg_score': ethics_result.get('esg_score', 0.0),
                'sustainability_rating': ethics_result.get('sustainability_rating', 'Unknown'),
                'ethics_recommendation': ethics_result.get('recommendation', 'Unknown')
            },
            
            # Risk assessment
            'risk_assessment': risk_assessment,
            
            # Key insights
            'key_insights': self._generate_key_insights(
                ethics_result, ai_analysis, youtube_intelligence, market_context
            ),
            
            # Action items
            'action_items': self._generate_action_items(
                recommendation, position_size, risk_assessment
            ),
            
            # Data sources
            'data_sources': {
                'ethics_screening': 'active',
                'claude_ai_analysis': 'active' if ai_analysis else 'unavailable',
                'youtube_intelligence': 'active' if youtube_intelligence.get('has_signal') else 'limited',
                'market_context': 'active' if market_context else 'unavailable'
            }
        }
        
        return enhanced_decision
    
    def _calculate_ethics_score(self, ethics_result: Dict) -> float:
        """Calculate normalized ethics score (0.0 to 1.0)"""
        if not ethics_result:
            return 0.5  # Neutral if no data
        
        # Base score from ESG rating
        esg_score = ethics_result.get('esg_score', 50) / 100.0  # Normalize to 0-1
        
        # Boost for green investments
        if ethics_result.get('is_green_investment', False):
            esg_score = min(1.0, esg_score + 0.2)
        
        # Penalty for blacklisted items
        if ethics_result.get('is_blacklisted', False):
            esg_score = max(0.0, esg_score - 0.5)
        
        return esg_score
    
    def _calculate_ai_score(self, ai_analysis: Dict) -> float:
        """Calculate normalized AI analysis score (0.0 to 1.0)"""
        if not ai_analysis:
            return 0.5  # Neutral if no AI analysis
        
        # Extract confidence from AI analysis
        confidence = ai_analysis.get('confidence', 0.5)
        recommendation = ai_analysis.get('recommendation', 'hold').lower()
        
        # Convert recommendation to score
        recommendation_scores = {
            'strong_buy': 0.9,
            'buy': 0.7,
            'hold': 0.5,
            'sell': 0.3,
            'strong_sell': 0.1
        }
        
        base_score = recommendation_scores.get(recommendation, 0.5)
        
        # Weight by confidence
        return base_score * confidence + 0.5 * (1 - confidence)
    
    def _calculate_youtube_score(self, youtube_intelligence: Dict) -> float:
        """Calculate normalized YouTube intelligence score (0.0 to 1.0)"""
        if not youtube_intelligence.get('has_signal'):
            return 0.5  # Neutral if no YouTube signal
        
        signal = youtube_intelligence.get('signal', {})
        if not signal:
            return 0.5
        
        # Base score from signal type
        signal_scores = {
            'strong_buy': 0.9,
            'buy': 0.7,
            'hold': 0.5,
            'sell': 0.3,
            'strong_sell': 0.1
        }
        
        base_score = signal_scores.get(signal.get('signal_type', 'hold'), 0.5)
        
        # Weight by signal confidence and quality factors
        signal_confidence = signal.get('confidence', 0.5)
        analyst_quality = signal.get('analyst_quality_score', 0.5)
        data_freshness = signal.get('data_freshness', 0.5)
        
        # Composite YouTube score
        youtube_score = (
            base_score * self.youtube_weights['signal_confidence'] * signal_confidence +
            base_score * self.youtube_weights['analyst_quality'] * analyst_quality +
            base_score * self.youtube_weights['data_freshness'] * data_freshness +
            base_score * self.youtube_weights['consensus_strength']  # Default consensus strength
        )
        
        return min(1.0, max(0.0, youtube_score))
    
    def _calculate_technical_score(self, symbol: str, market_context: Dict) -> float:
        """Calculate technical analysis score (simplified)"""
        # Simplified technical score based on market context
        if not market_context:
            return 0.5
        
        # Use market sentiment as proxy for technical score
        market_sentiment = market_context.get('overall_sentiment', 0.0)
        
        # Normalize market sentiment (-1 to 1) to score (0 to 1)
        technical_score = (market_sentiment + 1.0) / 2.0
        
        return min(1.0, max(0.0, technical_score))
    
    def _calculate_market_score(self, market_context: Dict) -> float:
        """Calculate market context score"""
        if not market_context:
            return 0.5
        
        # Factors: overall sentiment, uncertainty (inverted), consensus strength
        sentiment = market_context.get('overall_sentiment', 0.0)
        uncertainty = market_context.get('market_uncertainty', 0.5)
        consensus = market_context.get('analyst_consensus_strength', 0.5)
        
        # Normalize sentiment
        sentiment_score = (sentiment + 1.0) / 2.0
        
        # Invert uncertainty (lower uncertainty = higher score)
        uncertainty_score = 1.0 - uncertainty
        
        # Average the factors
        market_score = (sentiment_score + uncertainty_score + consensus) / 3.0
        
        return min(1.0, max(0.0, market_score))
    
    def _determine_enhanced_recommendation(self, overall_score: float, decision_type: str,
                                         youtube_intelligence: Dict, ethics_result: Dict) -> str:
        """Determine final recommendation based on enhanced analysis"""
        
        # Check for ethics red flags first
        if ethics_result.get('is_blacklisted', False):
            return 'avoid'
        
        # Use overall score to determine recommendation
        if overall_score >= 0.8:
            return 'strong_buy'
        elif overall_score >= 0.65:
            return 'buy'
        elif overall_score >= 0.45:
            return 'hold'
        elif overall_score >= 0.3:
            return 'sell'
        else:
            return 'strong_sell'
    
    def _calculate_enhanced_confidence(self, ethics_result: Dict, ai_analysis: Dict,
                                     youtube_intelligence: Dict, market_context: Dict) -> str:
        """Calculate enhanced confidence level"""
        
        confidence_factors = []
        
        # Ethics confidence
        if ethics_result:
            ethics_confidence = 0.8 if ethics_result.get('is_green_investment') else 0.6
            confidence_factors.append(ethics_confidence)
        
        # AI confidence
        if ai_analysis:
            ai_confidence = ai_analysis.get('confidence', 0.5)
            confidence_factors.append(ai_confidence)
        
        # YouTube confidence
        if youtube_intelligence.get('has_signal'):
            youtube_confidence = youtube_intelligence.get('signal', {}).get('confidence', 0.5)
            confidence_factors.append(youtube_confidence)
        
        # Market confidence (inverse of uncertainty)
        if market_context:
            market_confidence = 1.0 - market_context.get('market_uncertainty', 0.5)
            confidence_factors.append(market_confidence)
        
        # Calculate average confidence
        if confidence_factors:
            avg_confidence = sum(confidence_factors) / len(confidence_factors)
        else:
            avg_confidence = 0.5
        
        # Convert to confidence level
        if avg_confidence >= self.confidence_thresholds['very_high_confidence']:
            return 'very_high'
        elif avg_confidence >= self.confidence_thresholds['high_confidence']:
            return 'high'
        elif avg_confidence >= self.confidence_thresholds['medium_confidence']:
            return 'medium'
        elif avg_confidence >= self.confidence_thresholds['low_confidence']:
            return 'low'
        else:
            return 'very_low'
    
    def _calculate_position_size(self, overall_score: float, confidence: str,
                               portfolio_context: Dict, ethics_result: Dict) -> str:
        """Calculate recommended position size"""
        
        # Base position size on score and confidence
        if overall_score >= 0.8 and confidence in ['very_high', 'high']:
            if ethics_result.get('is_green_investment', False):
                return 'large (5-8% of portfolio)'
            else:
                return 'medium-large (4-6% of portfolio)'
        elif overall_score >= 0.65 and confidence in ['high', 'medium']:
            return 'medium (3-5% of portfolio)'
        elif overall_score >= 0.5:
            return 'small (1-3% of portfolio)'
        else:
            return 'avoid or minimal (<1% of portfolio)'
    
    def _generate_risk_assessment(self, ethics_result: Dict, youtube_intelligence: Dict,
                                market_context: Dict, confidence: str) -> Dict:
        """Generate comprehensive risk assessment"""
        
        risk_factors = []
        risk_level = 'medium'
        
        # Ethics risks
        if ethics_result.get('is_blacklisted', False):
            risk_factors.append('Investment conflicts with ethics criteria')
            risk_level = 'high'
        
        # YouTube intelligence risks
        if youtube_intelligence.get('analyst_coverage', 0) < 3:
            risk_factors.append('Limited analyst coverage - higher uncertainty')
        
        if youtube_intelligence.get('data_freshness', 1.0) < 0.5:
            risk_factors.append('YouTube intelligence data is not fresh')
        
        # Market risks
        if market_context.get('market_uncertainty', 0) > 0.7:
            risk_factors.append('High market uncertainty')
            risk_level = 'high'
        
        # Confidence risks
        if confidence in ['low', 'very_low']:
            risk_factors.append('Low confidence in analysis')
            risk_level = 'high'
        
        # Determine overall risk level
        if len(risk_factors) == 0:
            risk_level = 'low'
        elif len(risk_factors) <= 2 and risk_level != 'high':
            risk_level = 'medium'
        
        return {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'mitigation_strategies': self._generate_risk_mitigation(risk_factors)
        }
    
    def _generate_risk_mitigation(self, risk_factors: List[str]) -> List[str]:
        """Generate risk mitigation strategies"""
        mitigations = []
        
        if any('ethics' in factor.lower() for factor in risk_factors):
            mitigations.append('Review ethics criteria and consider alternative investments')
        
        if any('analyst coverage' in factor.lower() for factor in risk_factors):
            mitigations.append('Seek additional independent analysis and reduce position size')
        
        if any('uncertainty' in factor.lower() for factor in risk_factors):
            mitigations.append('Use smaller position sizes and consider dollar-cost averaging')
        
        if any('confidence' in factor.lower() for factor in risk_factors):
            mitigations.append('Wait for more data or seek additional confirmation')
        
        if not mitigations:
            mitigations.append('Maintain standard risk management practices')
        
        return mitigations
    
    def _generate_key_insights(self, ethics_result: Dict, ai_analysis: Dict,
                             youtube_intelligence: Dict, market_context: Dict) -> List[str]:
        """Generate key insights from all analysis components"""
        
        insights = []
        
        # Ethics insights
        if ethics_result.get('is_green_investment', False):
            insights.append(f"✅ Green investment aligned with sustainability goals")
        
        if ethics_result.get('esg_score', 0) > 75:
            insights.append(f"📊 Strong ESG score of {ethics_result.get('esg_score', 0)}")
        
        # YouTube insights
        if youtube_intelligence.get('has_signal'):
            signal = youtube_intelligence.get('signal', {})
            analyst_count = youtube_intelligence.get('analyst_coverage', 0)
            if analyst_count > 5:
                insights.append(f"🎬 Strong YouTube analyst coverage ({analyst_count} analysts)")
            
            if signal.get('confidence', 0) > 0.7:
                insights.append(f"📈 High-confidence YouTube signal: {signal.get('signal_type', 'unknown')}")
        
        # AI insights
        if ai_analysis and ai_analysis.get('confidence', 0) > 0.7:
            insights.append(f"🤖 Claude AI analysis shows {ai_analysis.get('recommendation', 'unknown')} with high confidence")
        
        # Market insights
        if market_context:
            sentiment = market_context.get('overall_sentiment', 0)
            if sentiment > 0.3:
                insights.append("🌍 Positive overall market sentiment from global analysts")
            elif sentiment < -0.3:
                insights.append("⚠️ Negative market sentiment requires caution")
        
        return insights[:5]  # Limit to top 5 insights
    
    def _generate_action_items(self, recommendation: str, position_size: str,
                             risk_assessment: Dict) -> List[str]:
        """Generate specific action items based on recommendation"""
        
        actions = []
        
        if recommendation in ['strong_buy', 'buy']:
            actions.append(f"Consider {recommendation.replace('_', ' ')} with {position_size}")
            actions.append("Monitor entry point for optimal timing")
            
            if risk_assessment['risk_level'] == 'high':
                actions.append("Implement strict stop-loss due to high risk")
            
        elif recommendation == 'hold':
            actions.append("Maintain current position if held")
            actions.append("Monitor for changes in analysis factors")
            
        elif recommendation in ['sell', 'strong_sell']:
            actions.append("Consider reducing or exiting position")
            actions.append("Review alternative investment opportunities")
            
        elif recommendation == 'avoid':
            actions.append("Do not invest - conflicts with ethics criteria")
            actions.append("Consider alternative investments in same sector")
        
        # Add risk-specific actions
        for mitigation in risk_assessment.get('mitigation_strategies', []):
            actions.append(f"Risk mitigation: {mitigation}")
        
        return actions
    
    def _generate_error_response(self, symbol: str, error_message: str) -> Dict:
        """Generate error response when analysis fails"""
        return {
            'symbol': symbol,
            'error': True,
            'error_message': error_message,
            'recommendation': 'hold',
            'confidence_level': 'very_low',
            'overall_score': 0.5,
            'position_size_recommendation': 'avoid or minimal (<1% of portfolio)',
            
            # Component scores (defaults for error state)
            'component_scores': {
                'ethics_score': 0.5,
                'ai_analysis_score': 0.5,
                'youtube_intelligence_score': 0.5,
                'technical_score': 0.5,
                'market_context_score': 0.5
            },
            
            # YouTube intelligence summary (defaults for error state)
            'youtube_intelligence_summary': {
                'has_coverage': False,
                'analyst_count': 0,
                'total_mentions': 0,
                'sentiment': 0.0,
                'primary_recommendation': None,
                'signal_type': None,
                'signal_confidence': None,
                'price_target': None
            },
            
            # Ethics summary (defaults for error state)
            'ethics_summary': {
                'is_green_investment': False,
                'esg_score': 0.0,
                'sustainability_rating': 'Unknown',
                'ethics_recommendation': 'Unknown'
            },
            
            # Risk assessment (defaults for error state)
            'risk_assessment': {
                'risk_level': 'very_high',
                'risk_factors': ['Analysis failed - data unreliable'],
                'mitigation_suggestions': ['Manual review required', 'Seek alternative analysis sources']
            },
            
            # Key insights and action items
            'key_insights': ['Analysis system encountered errors', 'Investment decision should be deferred'],
            'action_items': ['Analysis failed - seek manual review', 'Do not make investment decisions based on this result'],
            
            # Processing metadata
            'processing_time_seconds': 0.0,
            'analysis_timestamp': datetime.now().isoformat(),
            'engine_version': 'enhanced_v2.0',
            
            # Data sources (error state)
            'data_sources': {
                'ethics_screening': 'error',
                'claude_ai_analysis': 'error',
                'youtube_intelligence': 'error',
                'market_context': 'error'
            }
        }

# Convenience function for easy import
def get_enhanced_decision_engine() -> EnhancedAIInvestmentDecisionEngine:
    """Get configured enhanced AI investment decision engine instance"""
    return EnhancedAIInvestmentDecisionEngine()