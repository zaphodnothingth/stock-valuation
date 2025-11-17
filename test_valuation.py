"""
Unit tests for stock valuation components.
"""

import unittest
from unittest.mock import Mock, patch
from src.valuation_calculator import ValuationCalculator
from src.data_fetcher import DataFetcher
from src.recommender import StockRecommender


class TestValuationCalculator(unittest.TestCase):
    """Test ValuationCalculator methods."""
    
    def setUp(self):
        self.calc = ValuationCalculator()
    
    def test_free_cash_flow_positive(self):
        """Test FCF calculation with positive values."""
        fcf = self.calc.calculate_free_cash_flow(
            operating_cash_flow=1000,
            capital_expenditures=200
        )
        self.assertEqual(fcf, 800)
    
    def test_free_cash_flow_negative_becomes_zero(self):
        """Test FCF doesn't go negative."""
        fcf = self.calc.calculate_free_cash_flow(
            operating_cash_flow=100,
            capital_expenditures=200
        )
        self.assertEqual(fcf, 0)
    
    def test_fcf_per_share(self):
        """Test FCF per share calculation."""
        fcf_ps = self.calc.calculate_fcf_per_share(
            free_cash_flow=1000,
            shares_outstanding=100
        )
        self.assertEqual(fcf_ps, 10.0)
    
    def test_fcf_per_share_zero_shares(self):
        """Test FCF per share with zero shares."""
        fcf_ps = self.calc.calculate_fcf_per_share(
            free_cash_flow=1000,
            shares_outstanding=0
        )
        self.assertEqual(fcf_ps, 0.0)
    
    def test_return_on_equity(self):
        """Test ROE calculation."""
        roe = self.calc.calculate_roe(
            net_income=1000,
            shareholders_equity=10000
        )
        self.assertAlmostEqual(roe, 0.1)  # 10%
    
    def test_return_on_equity_zero_equity(self):
        """Test ROE with zero equity."""
        roe = self.calc.calculate_roe(
            net_income=1000,
            shareholders_equity=0
        )
        self.assertEqual(roe, 0)
    
    def test_wacc_calculation(self):
        """Test WACC calculation."""
        wacc = self.calc.calculate_wacc(
            risk_free_rate=0.03,
            market_risk_premium=0.06,
            beta=1.0,
            debt_to_equity=0.5
        )
        # Should be positive and reasonable
        self.assertGreater(wacc, 0)
        self.assertLess(wacc, 0.2)
    
    def test_intrinsic_value_positive_fcf(self):
        """Test intrinsic value calculation."""
        intrinsic, with_mos = self.calc.calculate_intrinsic_value(
            fcf_per_share=5.0,
            growth_rate=0.06,
            wacc=0.08,
            terminal_growth_rate=0.03,
            projection_years=10
        )
        # Intrinsic value should be positive
        self.assertGreater(intrinsic, 0)
        # Value with margin of safety should be less than intrinsic
        self.assertLess(with_mos, intrinsic)
    
    def test_intrinsic_value_zero_fcf(self):
        """Test intrinsic value with zero FCF."""
        intrinsic, with_mos = self.calc.calculate_intrinsic_value(
            fcf_per_share=0,
            growth_rate=0.06,
            wacc=0.08
        )
        self.assertEqual(intrinsic, 0)
        self.assertEqual(with_mos, 0)
    
    def test_rate_valuation_undervalued(self):
        """Test valuation rating for undervalued stock."""
        rating = self.calc.rate_valuation(
            current_price=50,
            intrinsic_value=100,
            value_with_mos=65
        )
        self.assertEqual(rating['signal'], 'STRONG_BUY')
        self.assertEqual(rating['rating'], 'SIGNIFICANTLY_UNDERVALUED')
        self.assertGreater(rating['discount'], 0)
    
    def test_rate_valuation_fairly_valued(self):
        """Test valuation rating for fairly valued stock."""
        rating = self.calc.rate_valuation(
            current_price=100,
            intrinsic_value=100,
            value_with_mos=65
        )
        self.assertEqual(rating['signal'], 'HOLD')
        self.assertEqual(rating['rating'], 'FAIRLY_VALUED')
    
    def test_rate_valuation_overvalued(self):
        """Test valuation rating for overvalued stock."""
        rating = self.calc.rate_valuation(
            current_price=130,
            intrinsic_value=100,
            value_with_mos=65
        )
        self.assertEqual(rating['signal'], 'AVOID')
        self.assertEqual(rating['rating'], 'OVERVALUED')
    
    def test_analyze_stock_complete(self):
        """Test complete stock analysis."""
        analysis = self.calc.analyze_stock(
            ticker='TEST',
            current_price=50,
            operating_cash_flow=10000,
            capex=2000,
            net_income=5000,
            shareholders_equity=50000,
            shares_outstanding=1000,
            growth_rate=0.06
        )
        
        # Check structure
        self.assertEqual(analysis['ticker'], 'TEST')
        self.assertEqual(analysis['current_price'], 50)
        self.assertIn('metrics', analysis)
        self.assertIn('valuation', analysis)
        self.assertIn('assessment', analysis)
        
        # Check values are reasonable
        self.assertGreater(analysis['metrics']['fcf'], 0)
        self.assertGreater(analysis['valuation']['intrinsic_value'], 0)


class TestDataFetcher(unittest.TestCase):
    """Test DataFetcher methods."""
    
    def setUp(self):
        self.fetcher = DataFetcher(cache_enabled=True)
    
    def test_cache_functionality(self):
        """Test that caching works."""
        # Mock yfinance
        with patch('data_fetcher.yf.Ticker') as mock_ticker:
            mock_stock = Mock()
            mock_stock.info = {'currentPrice': 100}
            mock_ticker.return_value = mock_stock
            
            # First call - should fetch
            result1 = self.fetcher.get_stock_info('TEST')
            self.assertEqual(result1['currentPrice'], 100)
            
            # Second call - should use cache
            result2 = self.fetcher.get_stock_info('TEST')
            self.assertEqual(result2['currentPrice'], 100)
            # Verify mock was only called once (cached second time)
            self.assertEqual(mock_ticker.call_count, 1)
    
    def test_cache_disabled(self):
        """Test that cache can be disabled."""
        fetcher_no_cache = DataFetcher(cache_enabled=False)
        
        with patch('data_fetcher.yf.Ticker') as mock_ticker:
            mock_stock = Mock()
            mock_stock.info = {'currentPrice': 100}
            mock_ticker.return_value = mock_stock
            
            # Both calls should fetch
            fetcher_no_cache.get_stock_info('TEST')
            fetcher_no_cache.get_stock_info('TEST')
            
            # Mock should be called twice (no caching)
            self.assertEqual(mock_ticker.call_count, 2)


class TestStockRecommender(unittest.TestCase):
    """Test StockRecommender methods."""
    
    def setUp(self):
        self.recommender = StockRecommender()
    
    def test_score_calculation_high_value(self):
        """Test score calculation for good opportunity."""
        mock_analysis = {
            'ticker': 'TEST',
            'current_price': 50,
            'assessment': {
                'discount': 40,  # 40% discount
                'signal': 'STRONG_BUY',
                'upside_potential': 100
            },
            'quality_metrics': {
                'roe_percent': 25,  # Excellent ROE
                'fcf_yield': 0.10,  # 10% FCF yield
            }
        }
        
        score = self.recommender._calculate_score(mock_analysis)
        self.assertGreater(score, 75)  # Should score high
    
    def test_score_calculation_low_value(self):
        """Test score calculation for poor opportunity."""
        mock_analysis = {
            'ticker': 'TEST',
            'current_price': 100,
            'assessment': {
                'discount': -20,  # 20% premium (overvalued)
                'signal': 'AVOID',
                'upside_potential': -50
            },
            'quality_metrics': {
                'roe_percent': 3,  # Poor ROE
                'fcf_yield': 0.01,  # 1% FCF yield
            }
        }
        
        score = self.recommender._calculate_score(mock_analysis)
        self.assertLess(score, 25)  # Should score low


class TestIntegration(unittest.TestCase):
    """Integration tests with mock data."""
    
    def test_end_to_end_analysis(self):
        """Test complete analysis flow with mocked data."""
        recommender = StockRecommender()
        
        with patch.object(recommender.fetcher, 'get_metrics') as mock_get_metrics:
            mock_get_metrics.return_value = {
                'ticker': 'TEST',
                'current_price': 50,
                'shares_outstanding': 1000,
                'operating_cash_flow': 10000,
                'capex': 2000,
                'free_cash_flow': 8000,
                'net_income': 5000,
                'total_equity': 50000,
                'growth_rate': 0.06,
            }
            
            analysis = recommender.analyze_stock('TEST')
            
            self.assertIsNotNone(analysis)
            self.assertEqual(analysis['ticker'], 'TEST')
            self.assertIn('recommendation_score', analysis)
            self.assertGreater(analysis['recommendation_score'], 0)


if __name__ == '__main__':
    unittest.main()
