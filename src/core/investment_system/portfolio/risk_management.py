"""
Advanced Risk Management System
Value at Risk (VaR), stress testing, correlation analysis, and portfolio risk metrics
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import yfinance as yf
from scipy.stats import norm
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, config_file: str = "config.json"):
        """Initialize risk management system"""
        self.config = self.load_config(config_file)
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'confidence_level': 0.05,  # 95% VaR
                'holding_period': 1,  # 1 day
                'stress_scenarios': {
                    'market_crash': -0.20,  # 20% market drop
                    'volatility_spike': 2.0,  # 2x volatility
                    'interest_rate_shock': 0.02  # 2% rate increase
                }
            }
    
    def get_portfolio_data(self, symbols: List[str], weights: List[float], period: str = "1y") -> pd.DataFrame:
        """Get portfolio data for risk analysis"""
        try:
            logger.info(f"Fetching portfolio data for {len(symbols)} assets")
            
            # Get historical data
            data = {}
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                if not hist.empty:
                    data[symbol] = hist['Close']
            
            if not data:
                raise ValueError("No data available for any symbols")
            
            # Create DataFrame
            prices_df = pd.DataFrame(data)
            prices_df.dropna(inplace=True)
            
            # Calculate returns
            returns_df = prices_df.pct_change().dropna()
            
            # Calculate portfolio returns
            weights_array = np.array(weights[:len(returns_df.columns)])
            weights_array = weights_array / weights_array.sum()  # Normalize weights
            
            portfolio_returns = (returns_df * weights_array).sum(axis=1)
            
            return {
                'prices': prices_df,
                'returns': returns_df,
                'portfolio_returns': portfolio_returns,
                'weights': weights_array
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio data: {e}")
            return {}
    
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.05, method: str = "historical") -> Dict:
        """Calculate Value at Risk using different methods"""
        try:
            if len(returns) < 30:
                return {'error': 'Insufficient data for VaR calculation'}
            
            results = {
                'confidence_level': confidence_level,
                'holding_period': self.config.get('holding_period', 1),
                'sample_size': len(returns)
            }
            
            # Historical VaR
            if method in ["historical", "all"]:
                historical_var = returns.quantile(confidence_level)
                results['historical_var'] = {
                    'value': historical_var,
                    'percentage': historical_var * 100
                }
            
            # Parametric VaR (assumes normal distribution)
            if method in ["parametric", "all"]:
                mean_return = returns.mean()
                std_return = returns.std()
                z_score = norm.ppf(confidence_level)
                parametric_var = mean_return + z_score * std_return
                
                results['parametric_var'] = {
                    'value': parametric_var,
                    'percentage': parametric_var * 100,
                    'mean_return': mean_return,
                    'volatility': std_return
                }
            
            # Monte Carlo VaR
            if method in ["monte_carlo", "all"]:
                mc_var = self.monte_carlo_var(returns, confidence_level)
                results['monte_carlo_var'] = mc_var
            
            # Expected Shortfall (Conditional VaR)
            var_threshold = results.get('historical_var', {}).get('value', returns.quantile(confidence_level))
            tail_losses = returns[returns <= var_threshold]
            if len(tail_losses) > 0:
                expected_shortfall = tail_losses.mean()
                results['expected_shortfall'] = {
                    'value': expected_shortfall,
                    'percentage': expected_shortfall * 100
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return {'error': str(e)}
    
    def monte_carlo_var(self, returns: pd.Series, confidence_level: float, num_simulations: int = 10000) -> Dict:
        """Calculate VaR using Monte Carlo simulation"""
        try:
            mean_return = returns.mean()
            std_return = returns.std()
            
            # Generate random scenarios
            random_returns = np.random.normal(mean_return, std_return, num_simulations)
            
            # Calculate VaR
            mc_var = np.percentile(random_returns, confidence_level * 100)
            
            return {
                'value': mc_var,
                'percentage': mc_var * 100,
                'simulations': num_simulations,
                'mean_simulated': np.mean(random_returns),
                'std_simulated': np.std(random_returns)
            }
            
        except Exception as e:
            logger.error(f"Error in Monte Carlo VaR: {e}")
            return {'error': str(e)}
    
    def stress_testing(self, portfolio_data: Dict, scenarios: Dict = None) -> Dict:
        """Perform stress testing on portfolio"""
        try:
            if not portfolio_data or 'returns' not in portfolio_data:
                return {'error': 'Invalid portfolio data'}
            
            returns_df = portfolio_data['returns']
            weights = portfolio_data['weights']
            
            if scenarios is None:
                scenarios = self.config.get('stress_scenarios', {})
            
            stress_results = {}
            
            for scenario_name, scenario_params in scenarios.items():
                logger.debug(f"Running stress test: {scenario_name}")
                
                if scenario_name == 'market_crash':
                    # Apply uniform market drop
                    shocked_returns = returns_df + scenario_params
                    
                elif scenario_name == 'volatility_spike':
                    # Increase volatility
                    mean_returns = returns_df.mean()
                    shocked_returns = returns_df + (returns_df - mean_returns) * (scenario_params - 1)
                    
                elif scenario_name == 'interest_rate_shock':
                    # Interest rate sensitive stocks affected more
                    # Tech stocks typically more sensitive to rates
                    tech_symbols = ['NVDA', 'MSFT', 'GOOGL', 'META', 'CRM', 'TSLA']
                    shocked_returns = returns_df.copy()
                    
                    for col in shocked_returns.columns:
                        if col in tech_symbols:
                            shocked_returns[col] += scenario_params * -0.5  # Negative impact
                        else:
                            shocked_returns[col] += scenario_params * -0.2  # Less impact
                
                else:
                    # Custom scenario - apply directly
                    shocked_returns = returns_df + scenario_params
                
                # Calculate portfolio impact
                portfolio_shocked = (shocked_returns * weights).sum(axis=1)
                portfolio_normal = (returns_df * weights).sum(axis=1)
                
                impact = portfolio_shocked.mean() - portfolio_normal.mean()
                
                stress_results[scenario_name] = {
                    'scenario_parameter': scenario_params,
                    'portfolio_impact': impact,
                    'portfolio_impact_pct': impact * 100,
                    'volatility_change': portfolio_shocked.std() / portfolio_normal.std() - 1,
                    'worst_case_loss': portfolio_shocked.min(),
                    'expected_loss': portfolio_shocked.mean()
                }
            
            return {
                'scenarios_tested': len(stress_results),
                'results': stress_results,
                'summary': self.summarize_stress_tests(stress_results)
            }
            
        except Exception as e:
            logger.error(f"Error in stress testing: {e}")
            return {'error': str(e)}
    
    def summarize_stress_tests(self, stress_results: Dict) -> Dict:
        """Summarize stress test results"""
        try:
            impacts = [result['portfolio_impact_pct'] for result in stress_results.values()]
            worst_losses = [result['worst_case_loss'] for result in stress_results.values()]
            
            return {
                'worst_scenario': min(impacts),
                'average_impact': np.mean(impacts),
                'most_severe_loss': min(worst_losses),
                'scenarios_with_major_loss': len([i for i in impacts if i < -5]),  # >5% loss
                'risk_level': 'HIGH' if min(impacts) < -10 else 'MEDIUM' if min(impacts) < -5 else 'LOW'
            }
            
        except Exception as e:
            logger.warning(f"Error summarizing stress tests: {e}")
            return {}
    
    def calculate_correlation_matrix(self, returns_df: pd.DataFrame) -> Dict:
        """Calculate correlation matrix and identify concentration risks"""
        try:
            correlation_matrix = returns_df.corr()
            
            # Find highly correlated pairs
            high_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # High correlation threshold
                        high_correlations.append({
                            'asset1': correlation_matrix.columns[i],
                            'asset2': correlation_matrix.columns[j],
                            'correlation': corr_value
                        })
            
            # Calculate average correlations
            avg_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
            
            return {
                'correlation_matrix': correlation_matrix.to_dict(),
                'average_correlation': avg_correlation,
                'high_correlations': high_correlations,
                'diversification_ratio': 1 - avg_correlation,
                'concentration_risk': 'HIGH' if avg_correlation > 0.7 else 'MEDIUM' if avg_correlation > 0.5 else 'LOW'
            }
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return {'error': str(e)}
    
    def calculate_portfolio_metrics(self, portfolio_data: Dict, portfolio_value: float = 100000) -> Dict:
        """Calculate comprehensive portfolio risk metrics"""
        try:
            returns = portfolio_data['portfolio_returns']
            
            # Basic metrics
            annual_return = returns.mean() * 252
            annual_volatility = returns.std() * np.sqrt(252)
            sharpe_ratio = (annual_return - 0.02) / annual_volatility if annual_volatility > 0 else 0
            
            # Drawdown analysis
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdowns = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdowns.min()
            
            # Calculate current drawdown
            current_drawdown = drawdowns.iloc[-1]
            
            # Downside metrics
            downside_returns = returns[returns < 0]
            downside_volatility = downside_returns.std() * np.sqrt(252)
            sortino_ratio = (annual_return - 0.02) / downside_volatility if downside_volatility > 0 else 0
            
            # VaR calculations
            var_results = self.calculate_var(returns, method="all")
            
            # Position sizing recommendations
            kelly_criterion = self.calculate_kelly_criterion(returns)
            
            return {
                'performance_metrics': {
                    'annual_return': annual_return,
                    'annual_volatility': annual_volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'sortino_ratio': sortino_ratio,
                    'max_drawdown': max_drawdown,
                    'current_drawdown': current_drawdown
                },
                'risk_metrics': var_results,
                'portfolio_value': portfolio_value,
                'daily_var_dollar': var_results.get('historical_var', {}).get('value', 0) * portfolio_value,
                'position_sizing': {
                    'kelly_criterion': kelly_criterion,
                    'recommended_position_size': min(kelly_criterion, 0.25),  # Cap at 25%
                    'risk_per_trade': 0.02  # 2% risk per trade
                },
                'risk_rating': self.get_risk_rating(annual_volatility, max_drawdown, sharpe_ratio)
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return {'error': str(e)}
    
    def calculate_kelly_criterion(self, returns: pd.Series) -> float:
        """Calculate Kelly Criterion for optimal position sizing"""
        try:
            if len(returns) < 30:
                return 0.1  # Conservative default
            
            win_rate = len(returns[returns > 0]) / len(returns)
            avg_win = returns[returns > 0].mean() if len(returns[returns > 0]) > 0 else 0
            avg_loss = abs(returns[returns < 0].mean()) if len(returns[returns < 0]) > 0 else 0.01
            
            if avg_loss == 0:
                return 0.1
            
            # Kelly formula: f = (bp - q) / b
            # where b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
            b = avg_win / avg_loss
            kelly = (b * win_rate - (1 - win_rate)) / b
            
            # Cap Kelly between 0 and 0.25 (25%)
            return max(0, min(kelly, 0.25))
            
        except Exception as e:
            logger.warning(f"Error calculating Kelly criterion: {e}")
            return 0.1
    
    def get_risk_rating(self, volatility: float, max_drawdown: float, sharpe_ratio: float) -> str:
        """Get overall risk rating for portfolio"""
        risk_score = 0
        
        # Volatility component
        if volatility > 0.30:  # >30% annual volatility
            risk_score += 3
        elif volatility > 0.20:
            risk_score += 2
        elif volatility > 0.15:
            risk_score += 1
        
        # Drawdown component
        if abs(max_drawdown) > 0.30:  # >30% max drawdown
            risk_score += 3
        elif abs(max_drawdown) > 0.20:
            risk_score += 2
        elif abs(max_drawdown) > 0.10:
            risk_score += 1
        
        # Sharpe ratio component (inverse)
        if sharpe_ratio < 0.5:
            risk_score += 2
        elif sharpe_ratio < 1.0:
            risk_score += 1
        
        # Determine rating
        if risk_score >= 6:
            return "HIGH RISK"
        elif risk_score >= 4:
            return "MEDIUM-HIGH RISK"
        elif risk_score >= 2:
            return "MEDIUM RISK"
        else:
            return "LOW-MEDIUM RISK"
    
    def generate_risk_report(self, symbols: List[str], weights: List[float], portfolio_value: float = 100000) -> Dict:
        """Generate comprehensive risk report"""
        try:
            logger.info("Generating comprehensive risk report")
            
            # Get portfolio data
            portfolio_data = self.get_portfolio_data(symbols, weights)
            
            if not portfolio_data:
                return {'error': 'Could not retrieve portfolio data'}
            
            # Calculate all risk metrics
            portfolio_metrics = self.calculate_portfolio_metrics(portfolio_data, portfolio_value)
            correlation_analysis = self.calculate_correlation_matrix(portfolio_data['returns'])
            stress_test_results = self.stress_testing(portfolio_data)
            
            # Risk recommendations
            recommendations = self.generate_risk_recommendations(
                portfolio_metrics, correlation_analysis, stress_test_results
            )
            
            return {
                'generated_at': datetime.now().isoformat(),
                'portfolio': {
                    'symbols': symbols,
                    'weights': weights.tolist() if hasattr(weights, 'tolist') else weights,
                    'value': portfolio_value
                },
                'portfolio_metrics': portfolio_metrics,
                'correlation_analysis': correlation_analysis,
                'stress_testing': stress_test_results,
                'recommendations': recommendations,
                'summary': {
                    'overall_risk_level': portfolio_metrics.get('risk_rating', 'UNKNOWN'),
                    'daily_var_95': portfolio_metrics.get('daily_var_dollar', 0),
                    'max_expected_loss': stress_test_results.get('summary', {}).get('most_severe_loss', 0) * portfolio_value,
                    'diversification_level': correlation_analysis.get('concentration_risk', 'UNKNOWN')
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating risk report: {e}")
            return {'error': str(e)}
    
    def generate_risk_recommendations(self, portfolio_metrics: Dict, correlation_analysis: Dict, stress_results: Dict) -> List[str]:
        """Generate actionable risk management recommendations"""
        recommendations = []
        
        try:
            # VaR recommendations
            var_pct = portfolio_metrics.get('risk_metrics', {}).get('historical_var', {}).get('percentage', 0)
            if abs(var_pct) > 5:  # >5% daily VaR
                recommendations.append(f"Daily VaR of {abs(var_pct):.1f}% is high - consider reducing position sizes")
            
            # Correlation recommendations
            avg_corr = correlation_analysis.get('average_correlation', 0)
            if avg_corr > 0.7:
                recommendations.append("High correlation between assets reduces diversification benefits")
            
            # Stress test recommendations
            stress_summary = stress_results.get('summary', {})
            if stress_summary.get('risk_level') == 'HIGH':
                recommendations.append("Portfolio vulnerable to stress scenarios - implement hedging strategies")
            
            # Sharpe ratio recommendations
            sharpe = portfolio_metrics.get('performance_metrics', {}).get('sharpe_ratio', 0)
            if sharpe < 1.0:
                recommendations.append("Low risk-adjusted returns - consider strategy optimization")
            
            # Drawdown recommendations
            max_dd = portfolio_metrics.get('performance_metrics', {}).get('max_drawdown', 0)
            if abs(max_dd) > 0.20:
                recommendations.append("High maximum drawdown - implement stop-loss rules")
            
            # Position sizing recommendations
            kelly = portfolio_metrics.get('position_sizing', {}).get('kelly_criterion', 0)
            if kelly < 0.05:
                recommendations.append("Kelly criterion suggests very conservative position sizing")
            
            # Default recommendations if none found
            if not recommendations:
                recommendations.append("Risk levels appear manageable with current portfolio allocation")
                recommendations.append("Continue monitoring market conditions and rebalance monthly")
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            return ["Error generating recommendations - manual review advised"]
    
    def save_risk_report(self, risk_report: Dict, filename: str = None):
        """Save risk report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"risk_report_{timestamp}.json"
        
        filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(risk_report, f, indent=2, default=str)
            logger.info(f"Risk report saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving risk report: {e}")

def generate_portfolio_risk_analysis():
    """Generate risk analysis for current portfolio recommendations"""
    print("Generating Portfolio Risk Analysis...")
    
    # Sample portfolio (would normally come from portfolio optimizer)
    symbols = ['NVDA', 'MSFT', 'TSLA', 'AMZN', 'GOOGL']
    weights = [0.25, 0.20, 0.20, 0.15, 0.20]  # Equal-ish weights
    portfolio_value = 100000  # $100k portfolio
    
    # Initialize risk manager
    risk_manager = RiskManager()
    
    # Generate comprehensive risk report
    risk_report = risk_manager.generate_risk_report(symbols, weights, portfolio_value)
    
    # Save report
    risk_manager.save_risk_report(risk_report)
    
    # Print summary
    if 'error' not in risk_report:
        print(f"\n=== PORTFOLIO RISK ANALYSIS ===")
        print(f"Portfolio Value: ${portfolio_value:,}")
        
        summary = risk_report.get('summary', {})
        print(f"Overall Risk Level: {summary.get('overall_risk_level', 'Unknown')}")
        print(f"Daily VaR (95%): ${abs(summary.get('daily_var_95', 0)):,.0f}")
        print(f"Worst Stress Loss: ${abs(summary.get('max_expected_loss', 0)):,.0f}")
        print(f"Diversification: {summary.get('diversification_level', 'Unknown')}")
        
        # Performance metrics
        perf = risk_report.get('portfolio_metrics', {}).get('performance_metrics', {})
        print(f"\nPerformance Metrics:")
        print(f"Annual Return: {perf.get('annual_return', 0):.1%}")
        print(f"Volatility: {perf.get('annual_volatility', 0):.1%}")
        print(f"Sharpe Ratio: {perf.get('sharpe_ratio', 0):.2f}")
        print(f"Max Drawdown: {perf.get('max_drawdown', 0):.1%}")
        
        # Recommendations
        recommendations = risk_report.get('recommendations', [])
        if recommendations:
            print(f"\nRisk Management Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
    else:
        print(f"Risk analysis failed: {risk_report['error']}")

if __name__ == "__main__":
    generate_portfolio_risk_analysis()