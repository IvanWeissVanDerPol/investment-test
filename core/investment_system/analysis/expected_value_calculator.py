"""
Expected Value Calculator
Advanced expected value calculation for investment opportunities
Inspired by money-machine project's sophisticated EV optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from scipy import stats
import math

from ..data.market_data_collector import MarketDataCollector
from ..ai.ml_prediction_engine import get_ml_engine
from ..utils.cache_manager import CacheManager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

logger = logging.getLogger(__name__)


@dataclass
class EVScenario:
    """Expected value scenario"""
    name: str
    probability: float
    outcome: float  # Return percentage
    description: str


@dataclass
class EVAnalysis:
    """Complete expected value analysis"""
    symbol: str
    expected_value: float
    scenarios: List[EVScenario]
    confidence_level: float
    risk_adjusted_ev: float
    downside_risk: float
    upside_potential: float
    probability_of_loss: float
    maximum_loss: float
    maximum_gain: float
    sharpe_ratio: float
    sortino_ratio: float
    var_95: float  # Value at Risk
    cvar_95: float  # Conditional Value at Risk
    recommendation: str
    time_horizon: str


@dataclass
class OpportunityRanking:
    """Opportunity ranking result"""
    symbol: str
    ev_score: float
    risk_score: float
    opportunity_score: float  # Combined EV and risk
    rank: int
    tier: str  # 'premium', 'good', 'average', 'poor'


class ExpectedValueCalculator:
    """
    Advanced expected value calculator with multi-scenario analysis
    """
    
    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize EV calculator
        
        Args:
            confidence_threshold: Minimum confidence level for predictions
        """
        self.confidence_threshold = confidence_threshold
        
        self.data_collector = MarketDataCollector()
        self.ml_engine = get_ml_engine()
        self.cache_manager = CacheManager()
        self.audit_logger = get_audit_logger()
        
        # EV calculation parameters
        self.scenario_weights = {
            'bull_market': 0.25,      # Strong positive market
            'normal_up': 0.35,        # Normal positive conditions
            'sideways': 0.20,         # Range-bound market
            'normal_down': 0.15,      # Normal negative conditions
            'bear_market': 0.05       # Strong negative market
        }
        
        # Risk-free rate for calculations
        self.risk_free_rate = 0.02  # 2% annual
        
        logger.info("Expected Value Calculator initialized")
    
    def calculate_expected_value(self, symbol: str, time_horizon: int = 30,
                               use_ml: bool = True) -> EVAnalysis:
        """
        Calculate comprehensive expected value analysis
        
        Args:
            symbol: Stock symbol to analyze
            time_horizon: Analysis time horizon in days
            use_ml: Whether to use ML predictions
        """
        try:
            logger.info(f"Calculating EV for {symbol} with {time_horizon}d horizon")
            
            # Get historical data
            historical_data = self._get_historical_data(symbol, days=252*2)  # 2 years
            if historical_data is None or len(historical_data) < 100:
                raise ValueError(f"Insufficient data for {symbol}")
            
            # Calculate base scenarios from historical data
            base_scenarios = self._calculate_base_scenarios(historical_data, time_horizon)
            
            # Enhance with ML predictions if enabled
            if use_ml:
                enhanced_scenarios = self._enhance_with_ml(symbol, base_scenarios, time_horizon)
            else:
                enhanced_scenarios = base_scenarios
            
            # Calculate expected value
            expected_value = sum(
                scenario.probability * scenario.outcome 
                for scenario in enhanced_scenarios
            )
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(enhanced_scenarios, historical_data)
            
            # Generate recommendation
            recommendation = self._generate_ev_recommendation(
                expected_value, risk_metrics, enhanced_scenarios
            )
            
            # Determine time horizon category
            time_horizon_str = self._categorize_time_horizon(time_horizon)
            
            analysis = EVAnalysis(
                symbol=symbol,
                expected_value=expected_value,
                scenarios=enhanced_scenarios,
                confidence_level=risk_metrics['confidence_level'],
                risk_adjusted_ev=risk_metrics['risk_adjusted_ev'],
                downside_risk=risk_metrics['downside_risk'],
                upside_potential=risk_metrics['upside_potential'],
                probability_of_loss=risk_metrics['probability_of_loss'],
                maximum_loss=risk_metrics['maximum_loss'],
                maximum_gain=risk_metrics['maximum_gain'],
                sharpe_ratio=risk_metrics['sharpe_ratio'],
                sortino_ratio=risk_metrics['sortino_ratio'],
                var_95=risk_metrics['var_95'],
                cvar_95=risk_metrics['cvar_95'],
                recommendation=recommendation,
                time_horizon=time_horizon_str
            )
            
            # Cache results
            cache_key = f"ev_analysis_{symbol}_{time_horizon}d"
            self.cache_manager.set(cache_key, analysis, ttl=1800)  # 30 minutes
            
            return analysis
            
        except Exception as e:
            logger.error(f"EV calculation failed for {symbol}: {e}")
            # Return neutral analysis
            return self._create_neutral_analysis(symbol, time_horizon)
    
    def rank_opportunities(self, symbols: List[str], max_risk_level: str = 'medium',
                          min_expected_return: float = 0.05) -> List[OpportunityRanking]:
        """
        Rank investment opportunities by expected value
        
        Args:
            symbols: List of symbols to analyze
            max_risk_level: Maximum acceptable risk ('low', 'medium', 'high')
            min_expected_return: Minimum expected return threshold
        """
        logger.info(f"Ranking {len(symbols)} investment opportunities")
        
        opportunities = []
        
        for symbol in symbols:
            try:
                analysis = self.calculate_expected_value(symbol)
                
                # Apply filters
                if analysis.expected_value < min_expected_return:
                    continue
                    
                risk_level = self._assess_risk_level(analysis)
                if not self._is_risk_acceptable(risk_level, max_risk_level):
                    continue
                
                # Calculate scores
                ev_score = self._calculate_ev_score(analysis)
                risk_score = self._calculate_risk_score(analysis)
                opportunity_score = self._calculate_opportunity_score(ev_score, risk_score)
                
                ranking = OpportunityRanking(
                    symbol=symbol,
                    ev_score=ev_score,
                    risk_score=risk_score,
                    opportunity_score=opportunity_score,
                    rank=0,  # Will be assigned after sorting
                    tier='average'  # Will be assigned after sorting
                )
                
                opportunities.append(ranking)
                
            except Exception as e:
                logger.error(f"Failed to rank {symbol}: {e}")
                continue
        
        # Sort by opportunity score (descending)
        opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        # Assign ranks and tiers
        for i, opp in enumerate(opportunities):
            opp.rank = i + 1
            
            # Assign tiers
            if i < len(opportunities) * 0.2:  # Top 20%
                opp.tier = 'premium'
            elif i < len(opportunities) * 0.5:  # Top 50%
                opp.tier = 'good'
            elif i < len(opportunities) * 0.8:  # Top 80%
                opp.tier = 'average'
            else:
                opp.tier = 'poor'
        
        logger.info(f"Ranked {len(opportunities)} opportunities")
        return opportunities
    
    def calculate_portfolio_ev(self, positions: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate portfolio-level expected value
        
        Args:
            positions: Dict of {symbol: weight} for portfolio positions
        """
        try:
            portfolio_ev = 0.0
            portfolio_risk = 0.0
            portfolio_scenarios = []
            
            symbol_analyses = {}
            
            # Calculate EV for each position
            for symbol, weight in positions.items():
                if weight <= 0:
                    continue
                    
                analysis = self.calculate_expected_value(symbol)
                symbol_analyses[symbol] = analysis
                
                # Weight the EV by position size
                weighted_ev = analysis.expected_value * weight
                portfolio_ev += weighted_ev
                
                # Add to portfolio risk (simplified - not considering correlations)
                portfolio_risk += (analysis.downside_risk * weight) ** 2
            
            portfolio_risk = math.sqrt(portfolio_risk)
            
            # Calculate portfolio Sharpe ratio
            portfolio_sharpe = (portfolio_ev - self.risk_free_rate) / portfolio_risk if portfolio_risk > 0 else 0
            
            # Generate portfolio scenarios (simplified)
            portfolio_scenarios = self._generate_portfolio_scenarios(symbol_analyses, positions)
            
            return {
                'expected_return': portfolio_ev,
                'risk': portfolio_risk,
                'sharpe_ratio': portfolio_sharpe,
                'num_positions': len([w for w in positions.values() if w > 0]),
                'scenarios': portfolio_scenarios,
                'individual_analyses': symbol_analyses,
                'diversification_benefit': self._calculate_diversification_benefit(positions),
                'concentration_risk': max(positions.values()) if positions else 0
            }
            
        except Exception as e:
            logger.error(f"Portfolio EV calculation failed: {e}")
            return {'error': str(e)}
    
    def _get_historical_data(self, symbol: str, days: int = 252) -> Optional[pd.DataFrame]:
        """Get historical data for analysis"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 50)  # Extra buffer
            
            return self.data_collector.get_historical_data(
                symbol,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return None
    
    def _calculate_base_scenarios(self, data: pd.DataFrame, horizon: int) -> List[EVScenario]:
        """Calculate base scenarios from historical data"""
        try:
            returns = data['Close'].pct_change(periods=horizon).dropna()
            
            if len(returns) < 50:
                raise ValueError("Insufficient return data")
            
            # Calculate percentiles for different market conditions
            percentiles = {
                'bear_market': 5,      # 5th percentile (worst 5%)
                'normal_down': 25,     # 25th percentile
                'sideways': 50,        # Median
                'normal_up': 75,       # 75th percentile
                'bull_market': 95      # 95th percentile (best 5%)
            }
            
            scenarios = []
            for scenario_name, percentile in percentiles.items():
                outcome = np.percentile(returns, percentile)
                probability = self.scenario_weights[scenario_name]
                
                scenarios.append(EVScenario(
                    name=scenario_name,
                    probability=probability,
                    outcome=outcome,
                    description=f"{scenario_name.replace('_', ' ').title()} scenario ({percentile}th percentile)"
                ))
            
            return scenarios
            
        except Exception as e:
            logger.error(f"Base scenario calculation failed: {e}")
            return self._create_default_scenarios()
    
    def _enhance_with_ml(self, symbol: str, base_scenarios: List[EVScenario],
                        horizon: int) -> List[EVScenario]:
        """Enhance scenarios with ML predictions"""
        try:
            # Get ML predictions
            price_pred = self.ml_engine.predict_price(symbol, horizon=horizon, model_type='ensemble')
            direction_pred = self.ml_engine.predict_direction(symbol, horizon=horizon)
            
            # Only use ML if confidence is high enough
            if (price_pred.confidence < self.confidence_threshold or 
                direction_pred.confidence < self.confidence_threshold):
                return base_scenarios
            
            # Adjust scenarios based on ML predictions
            enhanced_scenarios = []
            
            for scenario in base_scenarios:
                adjusted_outcome = scenario.outcome
                
                # Adjust based on direction prediction
                if direction_pred.predicted_value > 0.6:  # Strong upward prediction
                    if scenario.name in ['bull_market', 'normal_up']:
                        adjusted_outcome *= 1.2  # Increase positive outcomes
                    elif scenario.name in ['bear_market', 'normal_down']:
                        adjusted_outcome *= 0.8  # Reduce negative outcomes
                
                elif direction_pred.predicted_value < 0.4:  # Strong downward prediction
                    if scenario.name in ['bull_market', 'normal_up']:
                        adjusted_outcome *= 0.8  # Reduce positive outcomes
                    elif scenario.name in ['bear_market', 'normal_down']:
                        adjusted_outcome *= 1.2  # Increase negative outcomes
                
                enhanced_scenarios.append(EVScenario(
                    name=scenario.name,
                    probability=scenario.probability,
                    outcome=adjusted_outcome,
                    description=f"{scenario.description} (ML-enhanced)"
                ))
            
            return enhanced_scenarios
            
        except Exception as e:
            logger.warning(f"ML enhancement failed for {symbol}: {e}")
            return base_scenarios
    
    def _calculate_risk_metrics(self, scenarios: List[EVScenario], 
                               historical_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate comprehensive risk metrics"""
        try:
            # Extract outcomes and probabilities
            outcomes = np.array([s.outcome for s in scenarios])
            probabilities = np.array([s.probability for s in scenarios])
            
            # Expected value
            ev = np.sum(outcomes * probabilities)
            
            # Variance and standard deviation
            variance = np.sum(probabilities * (outcomes - ev) ** 2)
            std_dev = math.sqrt(variance)
            
            # Risk-adjusted EV (penalize volatility)
            risk_adjusted_ev = ev - (0.5 * variance)  # Simple risk adjustment
            
            # Downside risk (negative outcomes only)
            downside_outcomes = outcomes[outcomes < 0]
            downside_probs = probabilities[outcomes < 0]
            
            if len(downside_outcomes) > 0:
                downside_risk = math.sqrt(np.sum(downside_probs * (downside_outcomes ** 2)))
                probability_of_loss = np.sum(downside_probs)
                maximum_loss = np.min(outcomes)
            else:
                downside_risk = 0.0
                probability_of_loss = 0.0
                maximum_loss = 0.0
            
            # Upside potential
            upside_outcomes = outcomes[outcomes > 0]
            upside_potential = np.max(outcomes) if len(upside_outcomes) > 0 else 0.0
            maximum_gain = upside_potential
            
            # Sharpe ratio (assuming risk-free rate)
            daily_risk_free = self.risk_free_rate / 252  # Daily risk-free rate
            sharpe_ratio = (ev - daily_risk_free) / std_dev if std_dev > 0 else 0
            
            # Sortino ratio (downside deviation)
            sortino_ratio = (ev - daily_risk_free) / downside_risk if downside_risk > 0 else 0
            
            # Value at Risk (95% confidence)
            var_95 = np.percentile(outcomes, 5) if len(outcomes) > 0 else 0
            
            # Conditional Value at Risk (expected loss beyond VaR)
            tail_outcomes = outcomes[outcomes <= var_95]
            cvar_95 = np.mean(tail_outcomes) if len(tail_outcomes) > 0 else var_95
            
            # Confidence level (based on consistency of scenarios)
            confidence_level = 1.0 - (std_dev / abs(ev)) if ev != 0 else 0.5
            confidence_level = max(0.1, min(0.95, confidence_level))
            
            return {
                'risk_adjusted_ev': risk_adjusted_ev,
                'downside_risk': downside_risk,
                'upside_potential': upside_potential,
                'probability_of_loss': probability_of_loss,
                'maximum_loss': maximum_loss,
                'maximum_gain': maximum_gain,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'var_95': var_95,
                'cvar_95': cvar_95,
                'confidence_level': confidence_level
            }
            
        except Exception as e:
            logger.error(f"Risk metrics calculation failed: {e}")
            return self._create_default_risk_metrics()
    
    def _generate_ev_recommendation(self, expected_value: float, 
                                  risk_metrics: Dict[str, float],
                                  scenarios: List[EVScenario]) -> str:
        """Generate investment recommendation based on EV analysis"""
        try:
            sharpe_ratio = risk_metrics.get('sharpe_ratio', 0)
            probability_of_loss = risk_metrics.get('probability_of_loss', 0.5)
            confidence_level = risk_metrics.get('confidence_level', 0.5)
            
            # Strong positive EV with good risk metrics
            if (expected_value > 0.1 and sharpe_ratio > 1.5 and 
                probability_of_loss < 0.3 and confidence_level > 0.7):
                return 'strong_buy'
            
            # Positive EV with acceptable risk
            elif (expected_value > 0.05 and sharpe_ratio > 1.0 and 
                  probability_of_loss < 0.4 and confidence_level > 0.6):
                return 'buy'
            
            # Marginal positive EV
            elif (expected_value > 0.02 and sharpe_ratio > 0.5 and 
                  probability_of_loss < 0.5):
                return 'hold'
            
            # Negative or very low EV
            elif expected_value < 0 or sharpe_ratio < 0:
                return 'sell'
            
            # Uncertain or risky
            else:
                return 'hold'
                
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return 'hold'
    
    def _categorize_time_horizon(self, days: int) -> str:
        """Categorize time horizon"""
        if days <= 7:
            return 'very_short'
        elif days <= 30:
            return 'short'
        elif days <= 90:
            return 'medium'
        elif days <= 365:
            return 'long'
        else:
            return 'very_long'
    
    def _calculate_ev_score(self, analysis: EVAnalysis) -> float:
        """Calculate EV score (0-100)"""
        # Base score from expected value
        ev_score = min(100, max(0, analysis.expected_value * 1000))  # Scale to 0-100
        
        # Adjust for confidence
        ev_score *= analysis.confidence_level
        
        # Adjust for Sharpe ratio
        if analysis.sharpe_ratio > 0:
            ev_score *= (1 + min(1, analysis.sharpe_ratio / 2))
        
        return ev_score
    
    def _calculate_risk_score(self, analysis: EVAnalysis) -> float:
        """Calculate risk score (0-100, lower is better)"""
        # Base risk from probability of loss
        risk_score = analysis.probability_of_loss * 100
        
        # Adjust for maximum loss potential
        risk_score += abs(analysis.maximum_loss) * 500  # Scale factor
        
        # Adjust for downside risk
        risk_score += analysis.downside_risk * 1000
        
        return min(100, risk_score)
    
    def _calculate_opportunity_score(self, ev_score: float, risk_score: float) -> float:
        """Calculate combined opportunity score"""
        # Reward high EV and penalize high risk
        return ev_score * (100 - risk_score) / 100
    
    def _assess_risk_level(self, analysis: EVAnalysis) -> str:
        """Assess overall risk level"""
        if analysis.probability_of_loss > 0.6 or abs(analysis.maximum_loss) > 0.2:
            return 'high'
        elif analysis.probability_of_loss > 0.4 or abs(analysis.maximum_loss) > 0.1:
            return 'medium'
        else:
            return 'low'
    
    def _is_risk_acceptable(self, risk_level: str, max_risk_level: str) -> bool:
        """Check if risk level is acceptable"""
        risk_hierarchy = {'low': 0, 'medium': 1, 'high': 2}
        return risk_hierarchy[risk_level] <= risk_hierarchy[max_risk_level]
    
    def _create_neutral_analysis(self, symbol: str, horizon: int) -> EVAnalysis:
        """Create neutral analysis for error cases"""
        neutral_scenarios = [
            EVScenario('neutral', 1.0, 0.0, 'Neutral scenario due to analysis error')
        ]
        
        return EVAnalysis(
            symbol=symbol,
            expected_value=0.0,
            scenarios=neutral_scenarios,
            confidence_level=0.1,
            risk_adjusted_ev=0.0,
            downside_risk=0.1,
            upside_potential=0.1,
            probability_of_loss=0.5,
            maximum_loss=-0.1,
            maximum_gain=0.1,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            var_95=-0.05,
            cvar_95=-0.07,
            recommendation='hold',
            time_horizon=self._categorize_time_horizon(horizon)
        )
    
    def _create_default_scenarios(self) -> List[EVScenario]:
        """Create default scenarios"""
        return [
            EVScenario('bear_market', 0.05, -0.2, 'Default bear market scenario'),
            EVScenario('normal_down', 0.15, -0.05, 'Default normal down scenario'),
            EVScenario('sideways', 0.6, 0.0, 'Default sideways scenario'),
            EVScenario('normal_up', 0.15, 0.05, 'Default normal up scenario'),
            EVScenario('bull_market', 0.05, 0.2, 'Default bull market scenario')
        ]
    
    def _create_default_risk_metrics(self) -> Dict[str, float]:
        """Create default risk metrics"""
        return {
            'risk_adjusted_ev': 0.0,
            'downside_risk': 0.1,
            'upside_potential': 0.1,
            'probability_of_loss': 0.5,
            'maximum_loss': -0.1,
            'maximum_gain': 0.1,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'var_95': -0.05,
            'cvar_95': -0.07,
            'confidence_level': 0.1
        }
    
    def _generate_portfolio_scenarios(self, analyses: Dict[str, EVAnalysis], 
                                    positions: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate portfolio-level scenarios"""
        # Simplified portfolio scenario generation
        scenarios = []
        
        scenario_names = ['bear_market', 'normal_down', 'sideways', 'normal_up', 'bull_market']
        
        for scenario_name in scenario_names:
            portfolio_return = 0.0
            total_weight = 0.0
            
            for symbol, weight in positions.items():
                if weight <= 0 or symbol not in analyses:
                    continue
                    
                analysis = analyses[symbol]
                # Find matching scenario
                symbol_scenario = next(
                    (s for s in analysis.scenarios if s.name == scenario_name), 
                    None
                )
                
                if symbol_scenario:
                    portfolio_return += weight * symbol_scenario.outcome
                    total_weight += weight
            
            if total_weight > 0:
                scenarios.append({
                    'name': scenario_name,
                    'return': portfolio_return,
                    'probability': self.scenario_weights.get(scenario_name, 0.2)
                })
        
        return scenarios
    
    def _calculate_diversification_benefit(self, positions: Dict[str, float]) -> float:
        """Calculate diversification benefit (simplified)"""
        if len(positions) <= 1:
            return 0.0
        
        # Simple diversification score based on position concentration
        max_weight = max(positions.values()) if positions else 1.0
        num_positions = len([w for w in positions.values() if w > 0.01])  # At least 1%
        
        # Higher diversification when positions are more equal and numerous
        diversification = (1 - max_weight) * min(1.0, num_positions / 10)
        
        return diversification


# Global EV calculator instance
_ev_calculator: Optional[ExpectedValueCalculator] = None


def get_ev_calculator() -> ExpectedValueCalculator:
    """Get the global Expected Value calculator instance"""
    global _ev_calculator
    if _ev_calculator is None:
        _ev_calculator = ExpectedValueCalculator()
    return _ev_calculator


if __name__ == "__main__":
    # Test Expected Value calculator
    calculator = ExpectedValueCalculator()
    
    try:
        # Test single symbol EV analysis
        print("Testing EV analysis for NVDA...")
        analysis = calculator.calculate_expected_value("NVDA", time_horizon=30)
        
        print(f"EV Analysis Results:")
        print(f"  Expected Value: {analysis.expected_value:.4f}")
        print(f"  Risk-Adjusted EV: {analysis.risk_adjusted_ev:.4f}")
        print(f"  Probability of Loss: {analysis.probability_of_loss:.2%}")
        print(f"  Sharpe Ratio: {analysis.sharpe_ratio:.3f}")
        print(f"  Recommendation: {analysis.recommendation}")
        
        print(f"\nScenarios:")
        for scenario in analysis.scenarios:
            print(f"  {scenario.name}: {scenario.outcome:.2%} (p={scenario.probability:.2%})")
        
        # Test opportunity ranking
        print(f"\nTesting opportunity ranking...")
        symbols = ["NVDA", "MSFT", "GOOGL", "TSLA", "AMZN"]
        rankings = calculator.rank_opportunities(symbols, max_risk_level='medium')
        
        print(f"Opportunity Rankings:")
        for ranking in rankings:
            print(f"  #{ranking.rank} {ranking.symbol}: Score {ranking.opportunity_score:.1f} "
                  f"({ranking.tier})")
        
        # Test portfolio EV
        print(f"\nTesting portfolio EV...")
        positions = {"NVDA": 0.3, "MSFT": 0.25, "GOOGL": 0.25, "TSLA": 0.2}
        portfolio_ev = calculator.calculate_portfolio_ev(positions)
        
        print(f"Portfolio EV Results:")
        print(f"  Expected Return: {portfolio_ev['expected_return']:.4f}")
        print(f"  Risk: {portfolio_ev['risk']:.4f}")
        print(f"  Sharpe Ratio: {portfolio_ev['sharpe_ratio']:.3f}")
        print(f"  Diversification Benefit: {portfolio_ev['diversification_benefit']:.3f}")
        
    except Exception as e:
        print(f"Test failed: {e}")