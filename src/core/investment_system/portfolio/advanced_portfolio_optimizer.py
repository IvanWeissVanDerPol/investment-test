"""
Advanced Portfolio Optimization Engine
Modern Portfolio Theory, Black-Litterman, Risk Parity, and ML-based optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from scipy import optimize, linalg
from sklearn.covariance import LedoitWolf, OAS, ShrunkCovariance
from sklearn.preprocessing import StandardScaler
import cvxpy as cp

from ..data.market_data_collector import MarketDataCollector
from ..analysis.enhanced_market_analyzer import EnhancedMarketAnalyzer
from ..ai.ml_prediction_engine import get_ml_engine
from ..utils.cache_manager import CacheManager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

logger = logging.getLogger(__name__)


@dataclass
class PortfolioConstraints:
    """Portfolio optimization constraints"""
    max_weight: float = 0.15  # Maximum weight per asset (15%)
    min_weight: float = 0.0   # Minimum weight per asset
    target_return: Optional[float] = None  # Target return constraint
    max_volatility: Optional[float] = None  # Maximum portfolio volatility
    max_sector_weight: float = 0.4  # Maximum sector concentration (40%)
    min_positions: int = 5  # Minimum number of positions
    max_positions: int = 20  # Maximum number of positions
    turnover_limit: Optional[float] = None  # Maximum turnover
    leverage_limit: float = 1.0  # Maximum leverage (1.0 = no leverage)


@dataclass
class OptimizationResult:
    """Portfolio optimization result"""
    weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    optimization_method: str
    constraints_satisfied: bool
    optimization_score: float
    sector_allocations: Dict[str, float]
    risk_contributions: Dict[str, float]
    timestamp: datetime
    convergence_info: Dict[str, Any]


class AdvancedPortfolioOptimizer:
    """
    Advanced portfolio optimization with multiple methodologies:
    - Modern Portfolio Theory (Markowitz)
    - Black-Litterman Model
    - Risk Parity
    - Hierarchical Risk Parity
    - ML-Enhanced Optimization
    - ESG-Constrained Optimization
    """
    
    def __init__(self):
        """Initialize advanced portfolio optimizer"""
        self.data_collector = MarketDataCollector()
        self.market_analyzer = EnhancedMarketAnalyzer()
        self.ml_engine = get_ml_engine()
        self.cache_manager = CacheManager()
        self.audit_logger = get_audit_logger()
        
        # Risk-free rate (can be updated dynamically)
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        
        # Optimization parameters
        self.lookback_period = 252  # 1 year of daily data
        self.rebalancing_frequency = 'monthly'
        
        # Covariance estimation methods
        self.covariance_estimators = {
            'sample': lambda X: np.cov(X.T),
            'ledoit_wolf': lambda X: LedoitWolf().fit(X).covariance_,
            'oas': lambda X: OAS().fit(X).covariance_,
            'shrunk': lambda X: ShrunkCovariance().fit(X).covariance_
        }
        
        # Sector mappings (should be loaded from config)
        self.sector_mapping = {
            'NVDA': 'Technology', 'MSFT': 'Technology', 'AAPL': 'Technology',
            'GOOGL': 'Technology', 'META': 'Technology', 'TSLA': 'Consumer Discretionary',
            'DE': 'Industrials', 'TSM': 'Technology', 'AMD': 'Technology',
            'INTC': 'Technology', 'CRM': 'Technology', 'PLTR': 'Technology'
        }
        
        logger.info("Advanced Portfolio Optimizer initialized")
    
    def optimize_portfolio(self, symbols: List[str], method: str = 'markowitz',
                          constraints: PortfolioConstraints = None,
                          current_weights: Optional[Dict[str, float]] = None) -> OptimizationResult:
        """
        Optimize portfolio using specified method
        
        Args:
            symbols: List of stock symbols
            method: Optimization method ('markowitz', 'black_litterman', 'risk_parity', 'ml_enhanced')
            constraints: Portfolio constraints
            current_weights: Current portfolio weights for turnover calculation
        """
        try:
            if constraints is None:
                constraints = PortfolioConstraints()
            
            # Get market data and expected returns
            market_data = self._get_market_data(symbols)
            expected_returns = self._calculate_expected_returns(symbols, method)
            covariance_matrix = self._estimate_covariance_matrix(market_data, method='ledoit_wolf')
            
            # Validate inputs
            if len(expected_returns) != len(symbols) or covariance_matrix.shape[0] != len(symbols):
                raise ValueError("Dimension mismatch in optimization inputs")
            
            # Select optimization method
            if method == 'markowitz':
                result = self._markowitz_optimization(expected_returns, covariance_matrix, constraints, symbols)
            elif method == 'black_litterman':
                result = self._black_litterman_optimization(expected_returns, covariance_matrix, constraints, symbols)
            elif method == 'risk_parity':
                result = self._risk_parity_optimization(covariance_matrix, constraints, symbols)
            elif method == 'hierarchical_risk_parity':
                result = self._hierarchical_risk_parity_optimization(market_data, constraints, symbols)
            elif method == 'ml_enhanced':
                result = self._ml_enhanced_optimization(symbols, constraints, current_weights)
            elif method == 'equal_weight':
                result = self._equal_weight_optimization(symbols, constraints)
            else:
                raise ValueError(f"Unknown optimization method: {method}")
            
            # Validate and adjust result
            result = self._validate_and_adjust_weights(result, constraints)
            
            # Calculate additional metrics
            result = self._calculate_additional_metrics(result, expected_returns, covariance_matrix, symbols)
            
            # Cache result
            self._cache_optimization_result(result, symbols, method)
            
            # Audit log
            self.audit_logger.log_event(
                EventType.ANALYSIS_COMPLETED,
                SeverityLevel.LOW,
                resource='portfolio_optimizer',
                details={
                    'method': method,
                    'symbols': symbols,
                    'expected_return': result.expected_return,
                    'volatility': result.expected_volatility,
                    'sharpe_ratio': result.sharpe_ratio
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Portfolio optimization error: {e}")
            self.audit_logger.log_event(
                EventType.ERROR_OCCURRED,
                SeverityLevel.HIGH,
                resource='portfolio_optimizer',
                error_message=str(e)
            )
            raise
    
    def _markowitz_optimization(self, expected_returns: np.ndarray, cov_matrix: np.ndarray,
                               constraints: PortfolioConstraints, symbols: List[str]) -> OptimizationResult:
        """Modern Portfolio Theory optimization"""
        try:
            n = len(symbols)
            
            # Decision variables
            w = cp.Variable(n)
            
            # Objective: Maximize Sharpe ratio (equivalent to minimizing -Sharpe)
            portfolio_return = expected_returns.T @ w
            portfolio_variance = cp.quad_form(w, cov_matrix)
            
            # Constraints
            constraints_list = [
                cp.sum(w) == 1,  # Weights sum to 1
                w >= constraints.min_weight,  # Minimum weights
                w <= constraints.max_weight   # Maximum weights
            ]
            
            # Target return constraint
            if constraints.target_return is not None:
                constraints_list.append(portfolio_return >= constraints.target_return)
            
            # Maximum volatility constraint
            if constraints.max_volatility is not None:
                constraints_list.append(cp.sqrt(portfolio_variance) <= constraints.max_volatility)
            
            # Sector constraints
            sector_constraints = self._get_sector_constraints(symbols, w, constraints)
            constraints_list.extend(sector_constraints)
            
            # Optimization problems
            if constraints.target_return is not None:
                # Minimize risk for target return
                problem = cp.Problem(cp.Minimize(portfolio_variance), constraints_list)
            else:
                # Maximize Sharpe ratio
                # Use auxiliary variable for Sharpe ratio maximization
                kappa = cp.Variable()
                y = cp.Variable(n)
                
                constraints_aux = [
                    expected_returns.T @ y == 1,
                    cp.quad_form(y, cov_matrix) <= kappa,
                    y >= 0,
                    cp.sum(y) <= 1 / constraints.min_weight if constraints.min_weight > 0 else cp.sum(y) >= 0
                ]
                
                problem = cp.Problem(cp.Minimize(kappa), constraints_aux)
                
            # Solve optimization
            problem.solve(solver=cp.OSQP, verbose=False)
            
            if problem.status not in ["infeasible", "unbounded"]:
                if constraints.target_return is not None:
                    weights = w.value
                else:
                    # Convert auxiliary variables back to weights
                    weights = y.value / np.sum(y.value)
                
                # Normalize weights
                weights = weights / np.sum(weights)
                
                # Create weight dictionary
                weight_dict = dict(zip(symbols, weights))
                
                # Calculate portfolio metrics
                port_return = np.dot(weights, expected_returns)
                port_variance = np.dot(weights, np.dot(cov_matrix, weights))
                port_volatility = np.sqrt(port_variance)
                sharpe_ratio = (port_return - self.risk_free_rate) / port_volatility if port_volatility > 0 else 0
                
                return OptimizationResult(
                    weights=weight_dict,
                    expected_return=port_return,
                    expected_volatility=port_volatility,
                    sharpe_ratio=sharpe_ratio,
                    optimization_method='markowitz',
                    constraints_satisfied=True,
                    optimization_score=sharpe_ratio,
                    sector_allocations=self._calculate_sector_allocations(weight_dict),
                    risk_contributions=self._calculate_risk_contributions(weights, cov_matrix, symbols),
                    timestamp=datetime.utcnow(),
                    convergence_info={'status': problem.status, 'optimal_value': problem.value}
                )
            else:
                # Fallback to equal weights if optimization fails
                return self._equal_weight_optimization(symbols, constraints)
                
        except Exception as e:
            logger.error(f"Markowitz optimization error: {e}")
            return self._equal_weight_optimization(symbols, constraints)
    
    def _black_litterman_optimization(self, expected_returns: np.ndarray, cov_matrix: np.ndarray,
                                    constraints: PortfolioConstraints, symbols: List[str]) -> OptimizationResult:
        """Black-Litterman model optimization"""
        try:
            # Market capitalization weights (proxy with equal weights for simplicity)
            market_weights = np.ones(len(symbols)) / len(symbols)
            
            # Risk aversion parameter
            risk_aversion = 3.0
            
            # Implied equilibrium returns
            implied_returns = risk_aversion * np.dot(cov_matrix, market_weights)
            
            # Views and confidence (example views - in practice, these would come from analyst inputs)
            views_matrix, views_returns, omega = self._generate_views(symbols, expected_returns)
            
            # Black-Litterman formula
            if views_matrix is not None:
                # Calculate tau (scaling factor)
                tau = 1 / len(expected_returns)
                
                # Adjusted covariance matrix
                M1 = linalg.inv(tau * cov_matrix)
                M2 = np.dot(views_matrix.T, np.dot(linalg.inv(omega), views_matrix))
                M3 = np.dot(linalg.inv(tau * cov_matrix), implied_returns)
                M4 = np.dot(views_matrix.T, np.dot(linalg.inv(omega), views_returns))
                
                # New expected returns
                bl_returns = np.dot(linalg.inv(M1 + M2), M3 + M4)
                
                # New covariance matrix
                bl_cov = linalg.inv(M1 + M2)
            else:
                bl_returns = implied_returns
                bl_cov = cov_matrix
            
            # Optimize with Black-Litterman inputs
            return self._markowitz_optimization(bl_returns, bl_cov, constraints, symbols)
            
        except Exception as e:
            logger.error(f"Black-Litterman optimization error: {e}")
            return self._markowitz_optimization(expected_returns, cov_matrix, constraints, symbols)
    
    def _risk_parity_optimization(self, cov_matrix: np.ndarray, constraints: PortfolioConstraints,
                                symbols: List[str]) -> OptimizationResult:
        """Risk parity optimization"""
        try:
            n = len(symbols)
            
            # Objective function: minimize sum of squared risk contribution deviations
            def risk_parity_objective(weights):
                weights = np.array(weights)
                portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                
                # Risk contributions
                marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
                contrib = weights * marginal_contrib
                
                # Target: equal risk contribution (1/n each)
                target_contrib = portfolio_vol / n
                
                # Sum of squared deviations from equal risk contribution
                return np.sum((contrib - target_contrib) ** 2)
            
            # Constraints
            cons = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # Weights sum to 1
                {'type': 'ineq', 'fun': lambda w: w - constraints.min_weight},  # Min weights
                {'type': 'ineq', 'fun': lambda w: constraints.max_weight - w}   # Max weights
            ]
            
            # Bounds
            bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n)]
            
            # Initial guess: equal weights
            x0 = np.ones(n) / n
            
            # Optimize
            result = optimize.minimize(
                risk_parity_objective,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=cons,
                options={'maxiter': 1000, 'ftol': 1e-9}
            )
            
            if result.success:
                weights = result.x / np.sum(result.x)  # Ensure normalization
                weight_dict = dict(zip(symbols, weights))
                
                # Calculate expected returns (assume equal for risk parity)
                expected_returns = np.ones(n) * 0.08  # 8% expected return assumption
                
                # Calculate portfolio metrics
                port_return = np.dot(weights, expected_returns)
                port_variance = np.dot(weights, np.dot(cov_matrix, weights))
                port_volatility = np.sqrt(port_variance)
                sharpe_ratio = (port_return - self.risk_free_rate) / port_volatility if port_volatility > 0 else 0
                
                return OptimizationResult(
                    weights=weight_dict,
                    expected_return=port_return,
                    expected_volatility=port_volatility,
                    sharpe_ratio=sharpe_ratio,
                    optimization_method='risk_parity',
                    constraints_satisfied=result.success,
                    optimization_score=1 / result.fun if result.fun != 0 else 0,  # Lower objective is better
                    sector_allocations=self._calculate_sector_allocations(weight_dict),
                    risk_contributions=self._calculate_risk_contributions(weights, cov_matrix, symbols),
                    timestamp=datetime.utcnow(),
                    convergence_info={'success': result.success, 'message': result.message, 'iterations': result.nit}
                )
            else:
                return self._equal_weight_optimization(symbols, constraints)
                
        except Exception as e:
            logger.error(f"Risk parity optimization error: {e}")
            return self._equal_weight_optimization(symbols, constraints)
    
    def _hierarchical_risk_parity_optimization(self, market_data: Dict[str, pd.DataFrame],
                                             constraints: PortfolioConstraints,
                                             symbols: List[str]) -> OptimizationResult:
        """Hierarchical Risk Parity (HRP) optimization"""
        try:
            # Combine return series
            returns_data = []
            for symbol in symbols:
                if symbol in market_data:
                    returns = market_data[symbol]['Close'].pct_change().dropna()
                    returns_data.append(returns)
            
            if not returns_data:
                return self._equal_weight_optimization(symbols, constraints)
            
            # Create returns matrix
            returns_df = pd.concat(returns_data, axis=1, keys=symbols).dropna()
            
            if returns_df.empty:
                return self._equal_weight_optimization(symbols, constraints)
            
            # Calculate correlation matrix
            corr_matrix = returns_df.corr()
            
            # Hierarchical clustering
            from scipy.cluster.hierarchy import linkage, dendrogram, cut_tree
            from scipy.spatial.distance import squareform
            
            # Distance matrix (1 - correlation)
            distance_matrix = np.sqrt((1 - corr_matrix) / 2)
            
            # Hierarchical clustering
            linkage_matrix = linkage(squareform(distance_matrix.values), method='ward')
            
            # Get cluster assignments
            clusters = cut_tree(linkage_matrix, n_clusters=min(5, len(symbols)))
            
            # Calculate weights using HRP algorithm
            weights = self._calculate_hrp_weights(returns_df.values, linkage_matrix, symbols)
            
            weight_dict = dict(zip(symbols, weights))
            
            # Calculate portfolio metrics
            cov_matrix = returns_df.cov().values * 252  # Annualized
            expected_returns = returns_df.mean().values * 252  # Annualized
            
            port_return = np.dot(weights, expected_returns)
            port_variance = np.dot(weights, np.dot(cov_matrix, weights))
            port_volatility = np.sqrt(port_variance)
            sharpe_ratio = (port_return - self.risk_free_rate) / port_volatility if port_volatility > 0 else 0
            
            return OptimizationResult(
                weights=weight_dict,
                expected_return=port_return,
                expected_volatility=port_volatility,
                sharpe_ratio=sharpe_ratio,
                optimization_method='hierarchical_risk_parity',
                constraints_satisfied=True,
                optimization_score=sharpe_ratio,
                sector_allocations=self._calculate_sector_allocations(weight_dict),
                risk_contributions=self._calculate_risk_contributions(weights, cov_matrix, symbols),
                timestamp=datetime.utcnow(),
                convergence_info={'clusters': clusters.flatten().tolist()}
            )
            
        except Exception as e:
            logger.error(f"HRP optimization error: {e}")
            return self._equal_weight_optimization(symbols, constraints)
    
    def _ml_enhanced_optimization(self, symbols: List[str], constraints: PortfolioConstraints,
                                current_weights: Optional[Dict[str, float]] = None) -> OptimizationResult:
        """ML-enhanced portfolio optimization"""
        try:
            # Get ML predictions for each symbol
            ml_predictions = {}
            ml_confidences = {}
            
            for symbol in symbols:
                try:
                    # Get price prediction
                    price_pred = self.ml_engine.predict_price(symbol, horizon=21)  # 1 month ahead
                    
                    # Get volatility prediction  
                    vol_pred = self.ml_engine.predict_volatility(symbol, horizon=21)
                    
                    ml_predictions[symbol] = {
                        'return': price_pred.predicted_value,
                        'volatility': vol_pred.predicted_value,
                        'confidence': (price_pred.confidence + vol_pred.confidence) / 2
                    }
                    
                    ml_confidences[symbol] = ml_predictions[symbol]['confidence']
                    
                except Exception as e:
                    logger.warning(f"ML prediction failed for {symbol}: {e}")
                    # Use default values
                    ml_predictions[symbol] = {'return': 0.08, 'volatility': 0.20, 'confidence': 0.5}
                    ml_confidences[symbol] = 0.5
            
            # Create expected returns and covariance matrix from ML predictions
            expected_returns = np.array([ml_predictions[symbol]['return'] for symbol in symbols])
            
            # Adjust expected returns by confidence
            confidences = np.array([ml_confidences[symbol] for symbol in symbols])
            expected_returns = expected_returns * confidences + 0.08 * (1 - confidences)  # Blend with market return
            
            # Create covariance matrix from volatility predictions
            volatilities = np.array([ml_predictions[symbol]['volatility'] for symbol in symbols])
            
            # Simple covariance matrix (could be enhanced with correlation predictions)
            cov_matrix = np.outer(volatilities, volatilities) * 0.3  # Assume 30% correlation
            np.fill_diagonal(cov_matrix, volatilities ** 2)
            
            # Optimize using Markowitz with ML inputs
            result = self._markowitz_optimization(expected_returns, cov_matrix, constraints, symbols)
            result.optimization_method = 'ml_enhanced'
            
            return result
            
        except Exception as e:
            logger.error(f"ML enhanced optimization error: {e}")
            return self._equal_weight_optimization(symbols, constraints)
    
    def _equal_weight_optimization(self, symbols: List[str], 
                                 constraints: PortfolioConstraints) -> OptimizationResult:
        """Equal weight optimization (fallback method)"""
        try:
            n = len(symbols)
            equal_weight = 1.0 / n
            
            # Apply constraints
            if equal_weight > constraints.max_weight:
                # Need to cap weights and redistribute
                capped_weight = constraints.max_weight
                remaining_weight = 1.0 - (capped_weight * n)
                
                if remaining_weight > 0:
                    # Redistribute remaining weight equally among non-capped assets
                    redistributed_weight = remaining_weight / n
                    final_weight = min(capped_weight + redistributed_weight, constraints.max_weight)
                else:
                    final_weight = capped_weight
                
                weights = [final_weight] * n
                # Normalize to ensure sum = 1
                total_weight = sum(weights)
                weights = [w / total_weight for w in weights]
            else:
                weights = [equal_weight] * n
            
            weight_dict = dict(zip(symbols, weights))
            
            # Estimate portfolio metrics (using historical data if available)
            try:
                market_data = self._get_market_data(symbols)
                expected_returns = np.ones(n) * 0.08  # 8% assumption
                
                if market_data:
                    # Use historical data for better estimates
                    returns_data = []
                    for symbol in symbols:
                        if symbol in market_data and not market_data[symbol].empty:
                            returns = market_data[symbol]['Close'].pct_change().dropna()
                            if not returns.empty:
                                expected_returns[symbols.index(symbol)] = returns.mean() * 252
                
                # Simple covariance estimate
                cov_matrix = np.eye(n) * 0.04  # 20% volatility assumption
                
                port_return = np.dot(weights, expected_returns)
                port_variance = np.dot(weights, np.dot(cov_matrix, weights))
                port_volatility = np.sqrt(port_variance)
                sharpe_ratio = (port_return - self.risk_free_rate) / port_volatility if port_volatility > 0 else 0
                
            except Exception:
                # Use defaults if calculation fails
                port_return = 0.08
                port_volatility = 0.15
                sharpe_ratio = (port_return - self.risk_free_rate) / port_volatility
            
            return OptimizationResult(
                weights=weight_dict,
                expected_return=port_return,
                expected_volatility=port_volatility,
                sharpe_ratio=sharpe_ratio,
                optimization_method='equal_weight',
                constraints_satisfied=True,
                optimization_score=sharpe_ratio,
                sector_allocations=self._calculate_sector_allocations(weight_dict),
                risk_contributions={symbol: 1.0/n for symbol in symbols},
                timestamp=datetime.utcnow(),
                convergence_info={'method': 'equal_weight', 'status': 'success'}
            )
            
        except Exception as e:
            logger.error(f"Equal weight optimization error: {e}")
            raise
    
    def _get_market_data(self, symbols: List[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
        """Get market data for all symbols"""
        try:
            market_data = {}
            
            for symbol in symbols:
                try:
                    data = self.data_collector.get_historical_data(symbol, period)
                    if data is not None and not data.empty:
                        market_data[symbol] = data
                except Exception as e:
                    logger.warning(f"Failed to get data for {symbol}: {e}")
            
            return market_data
            
        except Exception as e:
            logger.error(f"Market data retrieval error: {e}")
            return {}
    
    def _calculate_expected_returns(self, symbols: List[str], method: str = 'historical') -> np.ndarray:
        """Calculate expected returns for symbols"""
        try:
            expected_returns = []
            
            for symbol in symbols:
                try:
                    if method == 'ml':
                        # Use ML predictions
                        pred = self.ml_engine.predict_price(symbol, horizon=21)
                        expected_return = pred.predicted_value
                    else:
                        # Use historical returns
                        data = self.data_collector.get_historical_data(symbol, "1y")
                        if data is not None and not data.empty:
                            returns = data['Close'].pct_change().dropna()
                            expected_return = returns.mean() * 252  # Annualized
                        else:
                            expected_return = 0.08  # Default 8% return
                    
                    expected_returns.append(expected_return)
                    
                except Exception as e:
                    logger.warning(f"Expected return calculation failed for {symbol}: {e}")
                    expected_returns.append(0.08)  # Default return
            
            return np.array(expected_returns)
            
        except Exception as e:
            logger.error(f"Expected returns calculation error: {e}")
            return np.ones(len(symbols)) * 0.08
    
    def _estimate_covariance_matrix(self, market_data: Dict[str, pd.DataFrame],
                                  method: str = 'ledoit_wolf') -> np.ndarray:
        """Estimate covariance matrix using various methods"""
        try:
            # Combine return series
            returns_data = []
            symbols = list(market_data.keys())
            
            for symbol in symbols:
                if not market_data[symbol].empty:
                    returns = market_data[symbol]['Close'].pct_change().dropna()
                    returns_data.append(returns)
            
            if not returns_data:
                # Return identity matrix as fallback
                n = len(symbols)
                return np.eye(n) * 0.04  # 20% volatility
            
            # Align return series
            returns_df = pd.concat(returns_data, axis=1, keys=symbols).dropna()
            
            if returns_df.empty or len(returns_df) < 30:
                # Insufficient data, use simple correlation structure
                n = len(symbols)
                cov_matrix = np.eye(n) * 0.04  # 20% volatility
                cov_matrix[cov_matrix == 0] = 0.01  # 10% correlation
                return cov_matrix
            
            # Use specified covariance estimation method
            if method in self.covariance_estimators:
                cov_matrix = self.covariance_estimators[method](returns_df.values)
                # Annualize
                cov_matrix *= 252
            else:
                # Default: sample covariance
                cov_matrix = returns_df.cov().values * 252
            
            # Ensure positive definite
            eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
            eigenvalues = np.maximum(eigenvalues, 1e-8)  # Ensure positive eigenvalues
            cov_matrix = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
            
            return cov_matrix
            
        except Exception as e:
            logger.error(f"Covariance estimation error: {e}")
            n = len(market_data) if market_data else 1
            return np.eye(n) * 0.04
    
    def _get_sector_constraints(self, symbols: List[str], weights, 
                              constraints: PortfolioConstraints) -> List:
        """Generate sector-based constraints"""
        try:
            sector_constraints = []
            
            # Group symbols by sector
            sectors = {}
            for i, symbol in enumerate(symbols):
                sector = self.sector_mapping.get(symbol, 'Other')
                if sector not in sectors:
                    sectors[sector] = []
                sectors[sector].append(i)
            
            # Add constraint for each sector
            for sector, indices in sectors.items():
                if len(indices) > 1:  # Only constrain if multiple assets in sector
                    sector_constraint = cp.sum([weights[i] for i in indices]) <= constraints.max_sector_weight
                    sector_constraints.append(sector_constraint)
            
            return sector_constraints
            
        except Exception as e:
            logger.error(f"Sector constraints error: {e}")
            return []
    
    def _generate_views(self, symbols: List[str], expected_returns: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate views for Black-Litterman (example implementation)"""
        try:
            # Example: Generate views based on analyst sentiment or ML predictions
            # In practice, these would come from fundamental analysis or expert opinions
            
            n = len(symbols)
            views_matrix = None
            views_returns = None
            omega = None
            
            # Example view: NVDA will outperform the market by 5%
            if 'NVDA' in symbols:
                nvda_idx = symbols.index('NVDA')
                market_return = np.mean(expected_returns)
                
                views_matrix = np.zeros((1, n))
                views_matrix[0, nvda_idx] = 1  # NVDA view
                views_returns = np.array([market_return + 0.05])  # 5% outperformance
                omega = np.array([[0.01]])  # Low confidence (high uncertainty)
            
            return views_matrix, views_returns, omega
            
        except Exception as e:
            logger.error(f"Views generation error: {e}")
            return None, None, None
    
    def _calculate_hrp_weights(self, returns: np.ndarray, linkage_matrix: np.ndarray,
                             symbols: List[str]) -> np.ndarray:
        """Calculate weights using Hierarchical Risk Parity algorithm"""
        try:
            # Simplified HRP implementation
            # In practice, this would follow the full HRP algorithm
            
            n = len(symbols)
            
            # Calculate inverse variance weights for each asset
            variances = np.var(returns, axis=0)
            inv_var_weights = (1 / variances) / np.sum(1 / variances)
            
            # Apply hierarchical structure (simplified)
            # Full implementation would traverse the dendrogram
            weights = inv_var_weights
            
            return weights
            
        except Exception as e:
            logger.error(f"HRP weights calculation error: {e}")
            return np.ones(len(symbols)) / len(symbols)
    
    def _validate_and_adjust_weights(self, result: OptimizationResult,
                                   constraints: PortfolioConstraints) -> OptimizationResult:
        """Validate and adjust weights to satisfy constraints"""
        try:
            weights = list(result.weights.values())
            symbols = list(result.weights.keys())
            
            # Check and fix basic constraints
            weights = np.array(weights)
            
            # Ensure non-negative weights
            weights = np.maximum(weights, constraints.min_weight)
            
            # Ensure weights don't exceed maximum
            weights = np.minimum(weights, constraints.max_weight)
            
            # Normalize to sum to 1
            if np.sum(weights) > 0:
                weights = weights / np.sum(weights)
            else:
                weights = np.ones(len(weights)) / len(weights)
            
            # Update result
            result.weights = dict(zip(symbols, weights))
            
            # Check if constraints are satisfied
            constraints_satisfied = (
                all(w >= constraints.min_weight - 1e-6 for w in weights) and
                all(w <= constraints.max_weight + 1e-6 for w in weights) and
                abs(sum(weights) - 1.0) < 1e-6
            )
            
            result.constraints_satisfied = constraints_satisfied
            
            return result
            
        except Exception as e:
            logger.error(f"Weight validation error: {e}")
            return result
    
    def _calculate_additional_metrics(self, result: OptimizationResult, expected_returns: np.ndarray,
                                    cov_matrix: np.ndarray, symbols: List[str]) -> OptimizationResult:
        """Calculate additional portfolio metrics"""
        try:
            weights = np.array(list(result.weights.values()))
            
            # Recalculate portfolio metrics with actual weights
            result.expected_return = np.dot(weights, expected_returns)
            result.expected_volatility = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            result.sharpe_ratio = ((result.expected_return - self.risk_free_rate) / 
                                 result.expected_volatility if result.expected_volatility > 0 else 0)
            
            # Risk contributions
            result.risk_contributions = self._calculate_risk_contributions(weights, cov_matrix, symbols)
            
            # Sector allocations
            result.sector_allocations = self._calculate_sector_allocations(result.weights)
            
            return result
            
        except Exception as e:
            logger.error(f"Additional metrics calculation error: {e}")
            return result
    
    def _calculate_risk_contributions(self, weights: np.ndarray, cov_matrix: np.ndarray,
                                    symbols: List[str]) -> Dict[str, float]:
        """Calculate risk contribution of each asset"""
        try:
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            if portfolio_volatility > 0:
                # Marginal risk contributions
                marginal_contrib = np.dot(cov_matrix, weights) / portfolio_volatility
                
                # Risk contributions (weight * marginal contribution)
                risk_contrib = weights * marginal_contrib
                
                # Normalize to percentage contributions
                risk_contrib = risk_contrib / portfolio_volatility
                
                return dict(zip(symbols, risk_contrib.tolist()))
            else:
                return {symbol: 1.0/len(symbols) for symbol in symbols}
                
        except Exception as e:
            logger.error(f"Risk contributions calculation error: {e}")
            return {symbol: 1.0/len(symbols) for symbol in symbols}
    
    def _calculate_sector_allocations(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Calculate sector allocations"""
        try:
            sector_allocations = {}
            
            for symbol, weight in weights.items():
                sector = self.sector_mapping.get(symbol, 'Other')
                if sector not in sector_allocations:
                    sector_allocations[sector] = 0
                sector_allocations[sector] += weight
            
            return sector_allocations
            
        except Exception as e:
            logger.error(f"Sector allocations calculation error: {e}")
            return {}
    
    def _cache_optimization_result(self, result: OptimizationResult, symbols: List[str], method: str):
        """Cache optimization result"""
        try:
            cache_key = f"portfolio_optimization_{method}_{hash(tuple(sorted(symbols)))}"
            
            # Convert to dict for caching
            cache_data = {
                'weights': result.weights,
                'expected_return': result.expected_return,
                'expected_volatility': result.expected_volatility,
                'sharpe_ratio': result.sharpe_ratio,
                'method': result.optimization_method,
                'timestamp': result.timestamp.isoformat()
            }
            
            # Cache for 1 hour
            self.cache_manager.set(cache_key, cache_data, ttl=3600)
            
        except Exception as e:
            logger.error(f"Optimization result caching error: {e}")
    
    def compare_optimization_methods(self, symbols: List[str], 
                                   constraints: PortfolioConstraints = None) -> Dict[str, OptimizationResult]:
        """Compare different optimization methods"""
        try:
            methods = ['markowitz', 'risk_parity', 'equal_weight', 'ml_enhanced']
            results = {}
            
            for method in methods:
                try:
                    result = self.optimize_portfolio(symbols, method, constraints)
                    results[method] = result
                    logger.info(f"Method {method}: Sharpe={result.sharpe_ratio:.3f}, "
                              f"Return={result.expected_return:.3f}, Vol={result.expected_volatility:.3f}")
                except Exception as e:
                    logger.warning(f"Method {method} failed: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Method comparison error: {e}")
            return {}


# Global optimizer instance
_portfolio_optimizer: Optional[AdvancedPortfolioOptimizer] = None


def get_portfolio_optimizer() -> AdvancedPortfolioOptimizer:
    """Get the global portfolio optimizer instance"""
    global _portfolio_optimizer
    if _portfolio_optimizer is None:
        _portfolio_optimizer = AdvancedPortfolioOptimizer()
    return _portfolio_optimizer


if __name__ == "__main__":
    # Test portfolio optimization
    optimizer = AdvancedPortfolioOptimizer()
    
    # Test symbols
    test_symbols = ['NVDA', 'MSFT', 'AAPL', 'TSLA', 'GOOGL']
    
    # Test constraints
    constraints = PortfolioConstraints(
        max_weight=0.25,
        min_weight=0.05,
        max_sector_weight=0.6
    )
    
    try:
        print("Testing portfolio optimization methods...")
        
        # Test Markowitz optimization
        result = optimizer.optimize_portfolio(test_symbols, 'markowitz', constraints)
        print(f"\nMarkowitz Optimization:")
        print(f"Expected Return: {result.expected_return:.2%}")
        print(f"Expected Volatility: {result.expected_volatility:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"Weights: {result.weights}")
        
        # Test method comparison
        print(f"\nComparing optimization methods...")
        comparison = optimizer.compare_optimization_methods(test_symbols, constraints)
        
        for method, result in comparison.items():
            print(f"{method}: Sharpe={result.sharpe_ratio:.3f}")
        
    except Exception as e:
        print(f"Test failed: {e}")