"""
Stock recommendation engine.

Uses Buffett-Munger valuation to rank and recommend undervalued stocks.
"""

import logging
from typing import List, Dict, Optional
import pandas as pd
from valuation_calculator import ValuationCalculator
from data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


class StockRecommender:
    """
    Recommends undervalued stocks based on comprehensive analysis.
    """
    
    def __init__(self):
        """Initialize the recommender."""
        self.calculator = ValuationCalculator()
        self.fetcher = DataFetcher()
        self.analyses = []
    
    def analyze_stock(self, ticker: str) -> Optional[Dict]:
        """
        Perform complete analysis on a single stock.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Analysis dict or None if unable to analyze
        """
        try:
            metrics = self.fetcher.get_metrics(ticker)
            if not metrics:
                logger.warning(f"No metrics for {ticker}")
                return None
            
            # Validate minimum requirements
            if (metrics['operating_cash_flow'] <= 0 or 
                metrics['net_income'] <= 0 or 
                metrics['total_equity'] <= 0):
                logger.warning(f"Insufficient financial data for {ticker}")
                return None
            
            analysis = self.calculator.analyze_stock(
                ticker=ticker,
                current_price=metrics['current_price'],
                operating_cash_flow=metrics['operating_cash_flow'],
                capex=metrics['capex'],
                net_income=metrics['net_income'],
                shareholders_equity=metrics['total_equity'],
                shares_outstanding=metrics['shares_outstanding'],
                growth_rate=metrics['growth_rate'],
            )
            
            # Add quality metrics
            analysis['quality_metrics'] = {
                'fcf_yield': (analysis['metrics']['fcf_per_share'] / metrics['current_price'] * 100)
                    if metrics['current_price'] > 0 else 0,
                'pe_ratio': (metrics['current_price'] / (metrics['net_income'] / metrics['shares_outstanding']))
                    if metrics['net_income'] > 0 else 0,
                'roe_percent': analysis['metrics']['roe'] * 100,
            }
            
            # Add recommendation score (0-100)
            analysis['recommendation_score'] = self._calculate_score(analysis)
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return None
    
    def _calculate_score(self, analysis: Dict) -> float:
        """
        Calculate a recommendation score (0-100) where higher = better.
        
        Based on:
        - Discount to intrinsic value (40%)
        - ROE quality (30%)
        - FCF yield (20%)
        - Investment signal (10%)
        """
        score = 0
        
        # Discount factor (40 points max)
        discount = analysis['assessment']['discount']
        if discount > 50:
            score += 40
        elif discount > 35:
            score += 35
        elif discount > 25:
            score += 25
        elif discount > 15:
            score += 15
        elif discount > 0:
            score += 5
        
        # ROE quality (30 points max)
        roe = analysis['quality_metrics']['roe_percent']
        if roe >= 25:
            score += 30
        elif roe >= 20:
            score += 25
        elif roe >= 15:
            score += 20
        elif roe >= 10:
            score += 10
        elif roe >= 5:
            score += 5
        
        # FCF yield (20 points max)
        fcf_yield = analysis['quality_metrics']['fcf_yield']
        if fcf_yield >= 0.10:  # 10% or more
            score += 20
        elif fcf_yield >= 0.07:
            score += 15
        elif fcf_yield >= 0.05:
            score += 10
        elif fcf_yield >= 0.03:
            score += 5
        
        # Signal strength (10 points max)
        signal = analysis['assessment']['signal']
        if signal == 'STRONG_BUY':
            score += 10
        elif signal == 'BUY':
            score += 7
        elif signal == 'HOLD':
            score += 3
        
        return min(score, 100)
    
    def analyze_universe(self, tickers: List[str], top_n: int = 10) -> pd.DataFrame:
        """
        Analyze a universe of stocks and return top recommendations.
        
        Args:
            tickers: List of ticker symbols to analyze
            top_n: Number of top recommendations to return
            
        Returns:
            DataFrame with top recommendations sorted by score
        """
        logger.info(f"Analyzing {len(tickers)} stocks...")
        
        self.analyses = []
        successful = 0
        
        for ticker in tickers:
            analysis = self.analyze_stock(ticker)
            if analysis:
                self.analyses.append(analysis)
                successful += 1
                logger.info(f"✓ {ticker} - Score: {analysis['recommendation_score']:.1f}")
            else:
                logger.debug(f"✗ {ticker}")
        
        logger.info(f"Successfully analyzed {successful}/{len(tickers)} stocks")
        
        # Convert to DataFrame
        df = self._analyses_to_dataframe(self.analyses)
        
        if len(df) == 0:
            logger.warning("No successful analyses to rank")
            return df
        
        # Sort by recommendation score (descending) and then by discount
        if 'recommendation_score' in df.columns and 'discount_percent' in df.columns:
            df = df.sort_values(['recommendation_score', 'discount_percent'], ascending=[False, False])
        
        return df.head(top_n)
    
    def _analyses_to_dataframe(self, analyses: List[Dict]) -> pd.DataFrame:
        """Convert analysis results to DataFrame for easy viewing."""
        rows = []
        for analysis in analyses:
            row = {
                'Ticker': analysis['ticker'],
                'Price': f"${analysis['current_price']:.2f}",
                'Intrinsic Value': f"${analysis['valuation']['intrinsic_value']:.2f}",
                'MOS Value': f"${analysis['valuation']['value_with_margin_of_safety']:.2f}",
                'discount_percent': analysis['assessment']['discount'],
                'Discount': f"{analysis['assessment']['discount']:.1f}%",
                'Upside': f"{analysis['assessment']['upside_potential']:.1f}%",
                'Rating': analysis['assessment']['rating'],
                'Signal': analysis['assessment']['signal'],
                'ROE': f"{analysis['quality_metrics']['roe_percent']:.1f}%",
                'FCF Yield': f"{analysis['quality_metrics']['fcf_yield']:.2f}%",
                'recommendation_score': analysis['recommendation_score'],
                'Score': f"{analysis['recommendation_score']:.1f}",
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def print_recommendations(self, df: pd.DataFrame, show_all_columns: bool = False):
        """Pretty print recommendations."""
        print("\n" + "="*120)
        print("TOP UNDERVALUED STOCKS - Buffett/Munger Analysis".center(120))
        print("="*120 + "\n")
        
        if show_all_columns:
            print(df.to_string(index=False))
        else:
            display_cols = ['Ticker', 'Price', 'Intrinsic Value', 'MOS Value', 'Discount', 
                          'Upside', 'Rating', 'Signal', 'ROE', 'FCF Yield', 'Score']
            cols_to_show = [c for c in display_cols if c in df.columns]
            print(df[cols_to_show].to_string(index=False))
        
        print("\n" + "="*120)
        print("Legend:")
        print("  MOS Value = Value with 35% Margin of Safety")
        print("  Discount = How much stock is discounted from intrinsic value")
        print("  Rating: SIGNIFICANTLY_UNDERVALUED | UNDERVALUED | FAIRLY_VALUED | OVERVALUED")
        print("  Signal: STRONG_BUY | BUY | HOLD | AVOID")
        print("  ROE = Return on Equity (>15% good, >20% excellent)")
        print("  FCF Yield = Free Cash Flow as % of stock price")
        print("="*120 + "\n")


def get_sp500_tickers() -> List[str]:
    """Get S&P 500 tickers for analysis."""
    import requests
    try:
        # Fetch S&P 500 list from Wikipedia
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        tickers = df['Symbol'].tolist()
        # Clean up any special characters
        tickers = [t.replace('.', '-') for t in tickers]
        return tickers
    except Exception as e:
        logger.error(f"Could not fetch S&P 500 list: {e}")
        # Return some well-known stocks as fallback
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
            'JNJ', 'V', 'WMT', 'JPM', 'MA',
            'PG', 'UNH', 'HD', 'DIS', 'NFLX',
            'IBM', 'T', 'VZ', 'KO', 'PEP'
        ]
