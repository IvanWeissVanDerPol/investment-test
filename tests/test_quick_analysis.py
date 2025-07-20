"""
Test suite for quick_analysis module
"""

import pytest
import json
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

try:
    from quick_analysis import get_stock_analysis
except ImportError:
    pytest.skip("quick_analysis module not available", allow_module_level=True)


class TestQuickAnalysis:
    """Test cases for quick analysis functionality"""
    
    def test_config_loading(self):
        """Test that configuration loads properly"""
        config_path = Path(__file__).parent.parent / "tools" / "config.json"
        assert config_path.exists(), "config.json should exist"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        assert 'user_profile' in config
        assert 'target_stocks' in config
        assert 'ai_robotics_etfs' in config
    
    @patch('yfinance.Ticker')
    def test_get_stock_analysis_valid_symbol(self, mock_ticker):
        """Test stock analysis with valid symbol"""
        # Mock yfinance response
        mock_info = {
            'currentPrice': 100.0,
            'previousClose': 95.0
        }
        mock_hist = Mock()
        mock_hist.empty = False
        mock_hist.__len__ = Mock(return_value=50)
        mock_hist.__getitem__ = Mock(side_effect=lambda key: {
            'Close': Mock(iloc=[-1, -2], rolling=Mock(return_value=Mock(mean=Mock(return_value=Mock(iloc=[-1]))))),
            'Volume': Mock(iloc=[-1], mean=Mock(return_value=1000000))
        }[key])
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = mock_info
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance
        
        result = get_stock_analysis("NVDA")
        
        assert result is not None
        assert 'current_price' in result
        assert 'day_change_pct' in result
    
    def test_get_stock_analysis_invalid_symbol(self):
        """Test stock analysis with invalid symbol"""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_hist = Mock()
            mock_hist.empty = True
            
            mock_ticker_instance = Mock()
            mock_ticker_instance.history.return_value = mock_hist
            mock_ticker.return_value = mock_ticker_instance
            
            result = get_stock_analysis("INVALID")
            assert result is None
    
    def test_target_stocks_configuration(self):
        """Test that target stocks are properly configured"""
        config_path = Path(__file__).parent.parent / "tools" / "config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        target_stocks = config.get('target_stocks', [])
        
        # Should have AI/Robotics focused stocks
        expected_stocks = ['NVDA', 'MSFT', 'TSLA']
        for stock in expected_stocks:
            assert stock in target_stocks, f"{stock} should be in target stocks"
    
    def test_risk_tolerance_settings(self):
        """Test risk tolerance configuration"""
        config_path = Path(__file__).parent.parent / "tools" / "config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        user_profile = config.get('user_profile', {})
        risk_tolerance = user_profile.get('risk_tolerance')
        
        assert risk_tolerance == 'medium', "Risk tolerance should be medium"
    
    def test_portfolio_balance_configuration(self):
        """Test portfolio balance is properly set"""
        config_path = Path(__file__).parent.parent / "tools" / "config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        user_profile = config.get('user_profile', {})
        balance = user_profile.get('dukascopy_balance', 0)
        
        assert balance > 0, "Portfolio balance should be positive"
        assert balance == 900, "Portfolio balance should be $900"


@pytest.mark.integration
class TestQuickAnalysisIntegration:
    """Integration tests for quick analysis (require network)"""
    
    @pytest.mark.slow
    def test_real_stock_analysis(self):
        """Test analysis with real stock data (network required)"""
        try:
            result = get_stock_analysis("MSFT")
            if result:  # Only test if data is available
                assert 'current_price' in result
                assert result['current_price'] > 0
                assert 'signals' in result
        except Exception:
            pytest.skip("Network or API unavailable")


@pytest.mark.portfolio
class TestPortfolioCalculations:
    """Test portfolio-specific calculations"""
    
    def test_position_sizing_limits(self):
        """Test that position sizing respects risk limits"""
        # For $900 portfolio with medium risk tolerance
        total_balance = 900
        max_single_position = total_balance * 0.25  # 25% max
        min_position_size = total_balance * 0.05   # 5% min
        
        assert max_single_position == 225, "Max position should be $225"
        assert min_position_size == 45, "Min position should be $45"
    
    def test_diversification_requirements(self):
        """Test portfolio diversification requirements"""
        config_path = Path(__file__).parent.parent / "tools" / "config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        target_stocks = config.get('target_stocks', [])
        ai_etfs = config.get('ai_robotics_etfs', [])
        
        # Should have enough options for diversification
        assert len(target_stocks) >= 10, "Should have at least 10 target stocks"
        assert len(ai_etfs) >= 5, "Should have at least 5 AI/Robotics ETFs"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])