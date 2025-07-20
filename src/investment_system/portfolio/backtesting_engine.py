"""
Backtesting Engine
Validates investment strategies using historical data
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import yfinance as yf
import matplotlib.pyplot as plt
from quick_analysis import get_stock_analysis
from ai_prediction_engine import AIPredictionEngine
from news_sentiment_analyzer import NewsSentimentAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestingEngine:
    def __init__(self, initial_capital: float = 10000, config_file: str = "config.json"):
        """Initialize backtesting engine"""
        self.initial_capital = initial_capital
        self.config = self.load_config(config_file)
        
        # Performance tracking
        self.trades = []
        self.portfolio_value = []
        self.positions = {}
        self.cash = initial_capital
        
        # Risk metrics
        self.max_drawdown = 0
        self.peak_value = initial_capital
        
        # Strategy components
        self.ai_engine = AIPredictionEngine()
        self.news_analyzer = NewsSentimentAnalyzer()
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'commission': 0.001,  # 0.1% commission
                'max_position_size': 0.2,  # 20% max per position
                'stop_loss': -0.15,  # 15% stop loss
                'take_profit': 0.25,  # 25% take profit
                'rebalance_frequency': 7  # days
            }
    
    def get_historical_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Get historical data for backtesting"""
        logger.info(f"Fetching historical data from {start_date} to {end_date}")
        
        historical_data = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    historical_data[symbol] = hist
                    logger.debug(f"Fetched {len(hist)} days of data for {symbol}")
                else:
                    logger.warning(f"No data available for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
        
        return historical_data
    
    def generate_signals(self, symbol: str, date: datetime, hist_data: pd.DataFrame) -> Dict:
        """Generate buy/sell signals for a specific date"""
        try:
            # Get data up to current date for analysis
            current_data = hist_data[hist_data.index <= date]
            
            if len(current_data) < 50:  # Need minimum data
                return {'action': 'hold', 'confidence': 0, 'reason': 'Insufficient data'}
            
            # Technical analysis signals
            technical_signals = self.get_technical_signals(current_data)
            
            # AI prediction signals (simplified for backtesting)
            ai_signals = self.get_ai_signals(symbol, current_data)
            
            # Combine signals
            overall_signal = self.combine_signals(technical_signals, ai_signals)
            
            return overall_signal
            
        except Exception as e:
            logger.warning(f"Error generating signals for {symbol} on {date}: {e}")
            return {'action': 'hold', 'confidence': 0, 'reason': 'Error in signal generation'}
    
    def get_technical_signals(self, data: pd.DataFrame) -> Dict:
        """Get technical analysis signals"""
        try:
            current_price = data['Close'].iloc[-1]
            
            # Moving averages
            sma_20 = data['Close'].rolling(20).mean().iloc[-1]
            sma_50 = data['Close'].rolling(50).mean().iloc[-1]
            
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Volume analysis
            avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume
            
            # Price momentum
            price_change_5d = (current_price - data['Close'].iloc[-5]) / data['Close'].iloc[-5]
            price_change_20d = (current_price - data['Close'].iloc[-20]) / data['Close'].iloc[-20]
            
            # Generate signals
            signals = []
            score = 0
            
            # Moving average signals
            if current_price > sma_20 > sma_50:
                signals.append("Bullish MA alignment")
                score += 2
            elif current_price < sma_20 < sma_50:
                signals.append("Bearish MA alignment") 
                score -= 2
            
            # RSI signals
            if current_rsi < 30:
                signals.append("Oversold (RSI)")
                score += 1
            elif current_rsi > 70:
                signals.append("Overbought (RSI)")
                score -= 1
            
            # Momentum signals
            if price_change_5d > 0.05:  # 5% gain in 5 days
                signals.append("Strong momentum")
                score += 1
            elif price_change_5d < -0.05:
                signals.append("Weak momentum")
                score -= 1
            
            # Volume confirmation
            if volume_ratio > 1.5:
                signals.append("High volume confirmation")
                score += 1
            
            # Determine action
            if score >= 3:
                action = 'buy'
                confidence = min(score / 5.0, 1.0)
            elif score <= -2:
                action = 'sell'
                confidence = min(abs(score) / 5.0, 1.0)
            else:
                action = 'hold'
                confidence = 0.5
            
            return {
                'action': action,
                'confidence': confidence,
                'score': score,
                'signals': signals,
                'metrics': {
                    'rsi': current_rsi,
                    'price_vs_sma20': (current_price - sma_20) / sma_20,
                    'volume_ratio': volume_ratio,
                    'momentum_5d': price_change_5d
                }
            }
            
        except Exception as e:
            logger.warning(f"Error in technical analysis: {e}")
            return {'action': 'hold', 'confidence': 0, 'signals': []}
    
    def get_ai_signals(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Get AI-based signals (simplified for backtesting)"""
        try:
            # Use pattern recognition
            patterns = self.ai_engine.detect_patterns(data)
            
            bullish_patterns = patterns.get('bullish_patterns', 0)
            bearish_patterns = patterns.get('bearish_patterns', 0)
            
            if bullish_patterns > bearish_patterns:
                return {
                    'action': 'buy',
                    'confidence': 0.6,
                    'reason': f"AI detected {bullish_patterns} bullish patterns"
                }
            elif bearish_patterns > bullish_patterns:
                return {
                    'action': 'sell', 
                    'confidence': 0.6,
                    'reason': f"AI detected {bearish_patterns} bearish patterns"
                }
            else:
                return {
                    'action': 'hold',
                    'confidence': 0.3,
                    'reason': "No clear AI patterns"
                }
                
        except Exception as e:
            logger.warning(f"Error in AI signals: {e}")
            return {'action': 'hold', 'confidence': 0.3}
    
    def combine_signals(self, technical: Dict, ai: Dict) -> Dict:
        """Combine technical and AI signals"""
        try:
            # Weight technical analysis more heavily (70%) than AI (30%)
            tech_weight = 0.7
            ai_weight = 0.3
            
            actions = {'buy': 1, 'hold': 0, 'sell': -1}
            
            tech_score = actions.get(technical['action'], 0) * technical['confidence']
            ai_score = actions.get(ai['action'], 0) * ai['confidence']
            
            combined_score = tech_score * tech_weight + ai_score * ai_weight
            
            # Determine final action
            if combined_score > 0.3:
                action = 'buy'
                confidence = min(combined_score, 1.0)
            elif combined_score < -0.3:
                action = 'sell'
                confidence = min(abs(combined_score), 1.0)
            else:
                action = 'hold'
                confidence = abs(combined_score)
            
            return {
                'action': action,
                'confidence': confidence,
                'technical': technical,
                'ai': ai,
                'combined_score': combined_score
            }
            
        except Exception as e:
            logger.warning(f"Error combining signals: {e}")
            return {'action': 'hold', 'confidence': 0}
    
    def execute_trade(self, symbol: str, action: str, price: float, date: datetime, signal: Dict):
        """Execute a trade"""
        try:
            commission_rate = self.config.get('commission', 0.001)
            max_position_size = self.config.get('max_position_size', 0.2)
            
            if action == 'buy':
                # Calculate position size based on confidence and available cash
                target_value = min(
                    self.cash * max_position_size * signal['confidence'],
                    self.cash * 0.9  # Keep 10% cash buffer
                )
                
                if target_value < 100:  # Minimum trade size
                    return False
                
                shares = int(target_value / price)
                cost = shares * price
                commission = cost * commission_rate
                total_cost = cost + commission
                
                if total_cost <= self.cash:
                    self.cash -= total_cost
                    
                    if symbol in self.positions:
                        self.positions[symbol]['shares'] += shares
                        self.positions[symbol]['avg_price'] = (
                            (self.positions[symbol]['avg_price'] * self.positions[symbol]['shares'] + cost) /
                            (self.positions[symbol]['shares'] + shares)
                        )
                    else:
                        self.positions[symbol] = {
                            'shares': shares,
                            'avg_price': price,
                            'entry_date': date
                        }
                    
                    # Record trade
                    self.trades.append({
                        'date': date,
                        'symbol': symbol,
                        'action': 'buy',
                        'shares': shares,
                        'price': price,
                        'cost': cost,
                        'commission': commission,
                        'signal': signal,
                        'cash_after': self.cash
                    })
                    
                    logger.debug(f"BUY: {shares} shares of {symbol} at ${price:.2f}")
                    return True
            
            elif action == 'sell' and symbol in self.positions:
                position = self.positions[symbol]
                shares = position['shares']
                
                if shares > 0:
                    proceeds = shares * price
                    commission = proceeds * commission_rate
                    net_proceeds = proceeds - commission
                    
                    self.cash += net_proceeds
                    
                    # Calculate P&L
                    cost_basis = shares * position['avg_price']
                    pnl = proceeds - cost_basis - commission
                    pnl_pct = (pnl / cost_basis) * 100
                    
                    # Record trade
                    self.trades.append({
                        'date': date,
                        'symbol': symbol,
                        'action': 'sell',
                        'shares': shares,
                        'price': price,
                        'proceeds': proceeds,
                        'commission': commission,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'signal': signal,
                        'cash_after': self.cash,
                        'hold_days': (date - position['entry_date']).days
                    })
                    
                    logger.debug(f"SELL: {shares} shares of {symbol} at ${price:.2f} (P&L: ${pnl:.2f})")
                    
                    # Remove position
                    del self.positions[symbol]
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return False
    
    def check_stop_loss_take_profit(self, date: datetime, prices: Dict[str, float]):
        """Check for stop loss and take profit triggers"""
        stop_loss = self.config.get('stop_loss', -0.15)
        take_profit = self.config.get('take_profit', 0.25)
        
        for symbol in list(self.positions.keys()):
            if symbol in prices:
                position = self.positions[symbol]
                current_price = prices[symbol]
                entry_price = position['avg_price']
                
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Check stop loss
                if pnl_pct <= stop_loss:
                    signal = {
                        'action': 'sell',
                        'confidence': 1.0,
                        'reason': f'Stop loss triggered at {pnl_pct:.1%}'
                    }
                    self.execute_trade(symbol, 'sell', current_price, date, signal)
                
                # Check take profit
                elif pnl_pct >= take_profit:
                    signal = {
                        'action': 'sell',
                        'confidence': 1.0,
                        'reason': f'Take profit triggered at {pnl_pct:.1%}'
                    }
                    self.execute_trade(symbol, 'sell', current_price, date, signal)
    
    def calculate_portfolio_value(self, date: datetime, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        try:
            total_value = self.cash
            
            # Add value of all positions
            for symbol, position in self.positions.items():
                if symbol in prices:
                    total_value += position['shares'] * prices[symbol]
            
            # Track for performance metrics
            self.portfolio_value.append({
                'date': date,
                'value': total_value,
                'cash': self.cash,
                'positions_value': total_value - self.cash
            })
            
            # Update peak and drawdown
            if total_value > self.peak_value:
                self.peak_value = total_value
            else:
                current_drawdown = (self.peak_value - total_value) / self.peak_value
                self.max_drawdown = max(self.max_drawdown, current_drawdown)
            
            return total_value
            
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {e}")
            return self.cash
    
    def run_backtest(self, symbols: List[str], start_date: str, end_date: str) -> Dict:
        """Run complete backtest"""
        logger.info(f"Starting backtest: {symbols} from {start_date} to {end_date}")
        
        try:
            # Get historical data
            historical_data = self.get_historical_data(symbols, start_date, end_date)
            
            if not historical_data:
                return {'error': 'No historical data available'}
            
            # Get date range
            all_dates = set()
            for data in historical_data.values():
                all_dates.update(data.index)
            
            sorted_dates = sorted(all_dates)
            
            # Run simulation day by day
            for i, date in enumerate(sorted_dates):
                if i < 50:  # Skip first 50 days for indicator calculation
                    continue
                
                # Get current prices
                current_prices = {}
                for symbol, data in historical_data.items():
                    if date in data.index:
                        current_prices[symbol] = data.loc[date, 'Close']
                
                # Check stop loss / take profit
                self.check_stop_loss_take_profit(date, current_prices)
                
                # Generate signals for each symbol
                for symbol in symbols:
                    if symbol in historical_data and date in historical_data[symbol].index:
                        signal = self.generate_signals(symbol, date, historical_data[symbol])
                        
                        if signal['action'] in ['buy', 'sell']:
                            price = current_prices[symbol]
                            self.execute_trade(symbol, signal['action'], price, date, signal)
                
                # Calculate portfolio value
                portfolio_value = self.calculate_portfolio_value(date, current_prices)
                
                # Log progress occasionally
                if i % 100 == 0:
                    logger.debug(f"Backtest progress: {date.strftime('%Y-%m-%d')} - Portfolio: ${portfolio_value:,.2f}")
            
            # Calculate final results
            results = self.calculate_backtest_results()
            logger.info(f"Backtest complete: Final value ${results['final_value']:,.2f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {'error': str(e)}
    
    def calculate_backtest_results(self) -> Dict:
        """Calculate comprehensive backtest results"""
        try:
            if not self.portfolio_value:
                return {'error': 'No portfolio value data'}
            
            final_value = self.portfolio_value[-1]['value']
            total_return = (final_value - self.initial_capital) / self.initial_capital
            
            # Calculate daily returns
            values = [pv['value'] for pv in self.portfolio_value]
            returns = pd.Series(values).pct_change().dropna()
            
            # Performance metrics
            annualized_return = ((final_value / self.initial_capital) ** (252 / len(self.portfolio_value))) - 1
            volatility = returns.std() * np.sqrt(252)
            sharpe_ratio = (annualized_return - 0.02) / volatility if volatility > 0 else 0  # Assume 2% risk-free rate
            
            # Win rate
            winning_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
            total_trades = len([t for t in self.trades if 'pnl' in t])
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            
            # Average returns
            avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
            losing_trades = [t for t in self.trades if t.get('pnl', 0) < 0]
            avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
            
            return {
                'initial_capital': self.initial_capital,
                'final_value': final_value,
                'total_return': total_return,
                'annualized_return': annualized_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': self.max_drawdown,
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'avg_win_pct': avg_win,
                'avg_loss_pct': avg_loss,
                'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else float('inf'),
                'trades': self.trades,
                'portfolio_value_history': self.portfolio_value,
                'final_positions': self.positions,
                'cash_remaining': self.cash
            }
            
        except Exception as e:
            logger.error(f"Error calculating results: {e}")
            return {'error': str(e)}
    
    def save_backtest_results(self, results: Dict, filename: str = None):
        """Save backtest results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_results_{timestamp}.json"
        
        filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Backtest results saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving backtest results: {e}")

def run_strategy_backtest():
    """Run backtest with current strategy"""
    print("Starting Strategy Backtesting...")
    
    # Initialize backtest
    backtester = BacktestingEngine(initial_capital=10000)
    
    # Test symbols
    symbols = ['NVDA', 'MSFT', 'TSLA', 'AMZN', 'GOOGL']
    
    # Test period (1 year)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Run backtest
    results = backtester.run_backtest(symbols, start_date, end_date)
    
    # Save results
    backtester.save_backtest_results(results)
    
    # Print summary
    if 'error' not in results:
        print(f"\n=== BACKTEST RESULTS ===")
        print(f"Period: {start_date} to {end_date}")
        print(f"Initial Capital: ${results['initial_capital']:,.2f}")
        print(f"Final Value: ${results['final_value']:,.2f}")
        print(f"Total Return: {results['total_return']:.1%}")
        print(f"Annualized Return: {results['annualized_return']:.1%}")
        print(f"Volatility: {results['volatility']:.1%}")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.1%}")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Win Rate: {results['win_rate']:.1%}")
        print(f"Avg Win: {results['avg_win_pct']:.1f}%")
        print(f"Avg Loss: {results['avg_loss_pct']:.1f}%")
        
        # Performance rating
        if results['sharpe_ratio'] > 1.5:
            rating = "EXCELLENT"
        elif results['sharpe_ratio'] > 1.0:
            rating = "GOOD"
        elif results['sharpe_ratio'] > 0.5:
            rating = "FAIR"
        else:
            rating = "POOR"
        
        print(f"Strategy Rating: {rating}")
    else:
        print(f"Backtest failed: {results['error']}")

if __name__ == "__main__":
    run_strategy_backtest()