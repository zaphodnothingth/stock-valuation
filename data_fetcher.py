"""
Data fetcher for stock financial metrics.

Supports multiple data sources:
- Yahoo Finance (yfinance) - Free, comprehensive
- Can be extended with Finnhub, Alpha Vantage, or Robinhood APIs
"""

import yfinance as yf
import pandas as pd
import logging
from typing import Dict, Optional, List
import time

logger = logging.getLogger(__name__)


def _estimate_capex_from_balance_sheet(balance_sheet, latest_cf, ticker: str) -> float:
    """
    Estimate CapEx from balance sheet changes when cash flow data is missing.
    
    CapEx = (Current PPE + Current Depreciation) - (Prior PPE + Prior Depreciation)
    This is a fallback when CapEx line is missing or zero.
    """
    try:
        if balance_sheet is None or balance_sheet.empty or len(balance_sheet.columns) < 2:
            return 0
        
        current_bs = balance_sheet.iloc[:, 0]
        prior_bs = balance_sheet.iloc[:, 1]
        
        # Get PPE (Property, Plant & Equipment)
        ppe_current = current_bs.get('Property Plant Equipment', 0) or 0
        ppe_prior = prior_bs.get('Property Plant Equipment', 0) or 0
        
        # If no PPE, try alternative names
        if not ppe_current:
            ppe_current = current_bs.get('Property Plant and Equipment Net', 0) or 0
        if not ppe_prior:
            ppe_prior = prior_bs.get('Property Plant and Equipment Net', 0) or 0
        
        # Get accumulated depreciation (also typically listed)
        acc_depr_current = abs(current_bs.get('Accumulated Depreciation', 0) or 0)
        acc_depr_prior = abs(prior_bs.get('Accumulated Depreciation', 0) or 0)
        
        # Estimate: If PPE increased, that's likely CapEx
        ppe_increase = max(ppe_current - ppe_prior, 0)
        
        if ppe_increase > 0:
            logger.debug(f"{ticker}: Estimated CapEx from PPE change: ${ppe_increase/1e9:.2f}B")
            return ppe_increase
        
        return 0
    except Exception as e:
        logger.debug(f"Error estimating CapEx from balance sheet: {e}")
        return 0


class DataFetcher:
    """
    Fetches financial data for stocks from various sources.
    
    Primary source: Yahoo Finance (yfinance)
    - No API key required
    - Comprehensive financial data
    - Reliable for fundamental analysis
    """
    
    def __init__(self, cache_enabled: bool = True):
        """
        Initialize DataFetcher.
        
        Args:
            cache_enabled: Cache stock info to reduce API calls
        """
        self.cache_enabled = cache_enabled
        self.stock_cache = {}
        self.data_cache = {}
    
    def get_stock_info(self, ticker: str, force_refresh: bool = False) -> Dict:
        """
        Get comprehensive stock information including financials.
        
        Args:
            ticker: Stock ticker symbol
            force_refresh: Ignore cache and fetch fresh data
            
        Returns:
            Dict with stock information
        """
        if self.cache_enabled and ticker in self.stock_cache and not force_refresh:
            return self.stock_cache[ticker]
        
        try:
            logger.info(f"Fetching info for {ticker}...")
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if self.cache_enabled:
                self.stock_cache[ticker] = info
            
            return info
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return {}
    
    def get_financial_statements(
        self, 
        ticker: str, 
        quarters: int = 4
    ) -> Dict[str, any]:
        """
        Get financial statements (cash flow, income, balance sheet).
        
        Args:
            ticker: Stock ticker symbol
            quarters: Number of quarters to fetch
            
        Returns:
            Dict with financial data
        """
        try:
            logger.info(f"Fetching financial statements for {ticker}...")
            stock = yf.Ticker(ticker)
            
            # Get most recent quarter data
            cash_flow = stock.quarterly_cash_flow
            income_stmt = stock.quarterly_income_stmt
            balance_sheet = stock.quarterly_balance_sheet
            
            if cash_flow is None or income_stmt is None or balance_sheet is None:
                logger.warning(f"Missing financial data for {ticker}")
                return {}
            
            return {
                'cash_flow': cash_flow,
                'income_stmt': income_stmt,
                'balance_sheet': balance_sheet,
            }
        except Exception as e:
            logger.error(f"Error fetching financial statements for {ticker}: {e}")
            return {}
    
    def extract_metrics(self, ticker: str, info: Dict, financials: Dict) -> Optional[Dict]:
        """
        Extract key metrics for valuation analysis.
        
        Args:
            ticker: Stock ticker
            info: Stock info dict from yfinance
            financials: Financial statements dict
            
        Returns:
            Dict with extracted metrics or None if insufficient data
        """
        try:
            # Price and shares from info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            shares_outstanding = info.get('sharesOutstanding', 0)
            
            # Initialize from info dict
            operating_cash_flow = info.get('operatingCashflow', 0) or 0
            capex = info.get('capitalExpenditures', 0) or 0
            free_cash_flow = info.get('freeCashflow', 0) or 0
            net_income = 0
            total_equity = 0
            
            # Extract from financial statements (more reliable)
            if financials and 'cash_flow' in financials:
                cf_df = financials['cash_flow']
                if cf_df is not None and len(cf_df.columns) > 0:
                    try:
                        latest_cf = cf_df.iloc[:, 0]
                        # Try multiple common naming variations
                        operating_cash_flow = operating_cash_flow or (
                            latest_cf.get('Operating Cash Flow') or
                            latest_cf.get('Net Cash From Operating Activities') or
                            0
                        )
                        
                        # CapEx extraction - try multiple field names
                        # Note: CapEx is typically negative in cash flow, so we take abs()
                        capex_candidates = [
                            latest_cf.get('Capital Expenditures'),
                            latest_cf.get('Purchases of Property Plant and Equipment'),
                            latest_cf.get('Capital Allocation'),
                            latest_cf.get('Purchase of Property Plant and Equipment'),
                        ]
                        
                        for capex_val in capex_candidates:
                            if capex_val and capex_val != 0:
                                capex = abs(float(capex_val))
                                break
                        
                        # If still zero, try extracting from balance sheet changes
                        if not capex or capex == 0:
                            capex = _estimate_capex_from_balance_sheet(
                                financials.get('balance_sheet'), latest_cf, ticker
                            )
                    except Exception as e:
                        logger.debug(f"Error extracting CapEx for {ticker}: {e}")
                        pass
            
            if financials and 'income_stmt' in financials:
                inc_df = financials['income_stmt']
                if inc_df is not None and len(inc_df.columns) > 0:
                    try:
                        latest_inc = inc_df.iloc[:, 0]
                        # Use the most reliable net income field
                        net_income = (
                            latest_inc.get('Net Income') or
                            latest_inc.get('Net Income Common Stockholders') or
                            latest_inc.get('Net Income From Continuing Operation Net Minority Interest') or
                            0
                        )
                    except Exception:
                        pass
            
            if financials and 'balance_sheet' in financials:
                bs_df = financials['balance_sheet']
                if bs_df is not None and len(bs_df.columns) > 0:
                    try:
                        latest_bs = bs_df.iloc[:, 0]
                        # Try multiple equity field names
                        total_equity = (
                            latest_bs.get('Stockholders Equity') or
                            latest_bs.get('Common Stock Equity') or
                            latest_bs.get('Total Equity Gross Minority Interest') or
                            0
                        )
                    except Exception:
                        pass
            
            # Validate data - must have all required positive values
            if (current_price <= 0 or shares_outstanding <= 0 or
                operating_cash_flow <= 0 or net_income <= 0 or total_equity <= 0):
                logger.debug(f"Insufficient data for {ticker}: "
                            f"price={current_price}, shares={shares_outstanding}, "
                            f"ocf={operating_cash_flow}, ni={net_income}, eq={total_equity}")
                return None
            
            # Data quality warnings
            fcf = operating_cash_flow - capex
            fcf_yield = (fcf / shares_outstanding) / current_price if current_price > 0 else 0
            roe_calc = net_income / total_equity if total_equity > 0 else 0
            
            # Flag: CapEx is zero or missing (likely data error)
            if capex == 0 or capex < operating_cash_flow * 0.01:
                logger.warning(f"{ticker}: CapEx is zero or suspiciously low "
                             f"(OCF: ${operating_cash_flow/1e9:.2f}B, CapEx: ${capex/1e9:.2f}B). "
                             f"This may indicate missing or unreliable data.")
            
            # Flag: FCF yield is unreasonably high (>20%)
            if fcf_yield > 0.20:
                logger.warning(f"{ticker}: Very high FCF yield ({fcf_yield:.1%}). "
                             f"This may indicate unsustainable cash generation or data error.")
            
            # Flag: FCF is more than OCF (shouldn't happen if CapEx is positive)
            if fcf > operating_cash_flow and capex > 0:
                logger.warning(f"{ticker}: FCF exceeds OCF (CapEx appears negative). "
                             f"Data validation issue detected.")
            
            # Flag: Unusually low ROE for asset-light businesses (likely quarterly data)
            # Example: Visa/Mastercard have 40-50% ROE, if showing <20%, likely quarterly data
            if roe_calc < 0.15 and fcf_yield > 0.03 and capex == 0:
                logger.warning(f"{ticker}: ROE appears unusually low ({roe_calc:.1%}) "
                             f"with high FCF yield ({fcf_yield:.1%}). Likely quarterly data issue. "
                             f"Consider data as unreliable.")
            
            # Growth rate estimate - conservative default
            growth_rate = 0.06  # 6% default (will be overridden by sector rates)
            
            metrics = {
                'ticker': ticker,
                'current_price': float(current_price),
                'shares_outstanding': float(shares_outstanding),
                'operating_cash_flow': float(operating_cash_flow),
                'capex': float(capex),
                'free_cash_flow': float(free_cash_flow),
                'net_income': float(net_income),
                'total_equity': float(total_equity),
                'growth_rate': growth_rate,
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error extracting metrics for {ticker}: {e}")
            return None
    
    def get_metrics(self, ticker: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get complete metrics for a stock.
        
        Args:
            ticker: Stock ticker symbol
            force_refresh: Ignore cache
            
        Returns:
            Dict with metrics or None if unable to fetch
        """
        if self.cache_enabled and ticker in self.data_cache and not force_refresh:
            return self.data_cache[ticker]
        
        info = self.get_stock_info(ticker, force_refresh=force_refresh)
        if not info:
            return None
        
        financials = self.get_financial_statements(ticker)
        metrics = self.extract_metrics(ticker, info, financials)
        
        if self.cache_enabled and metrics:
            self.data_cache[ticker] = metrics
        
        return metrics
    
    def batch_get_metrics(self, tickers: List[str], delay: float = 0.1) -> Dict[str, Dict]:
        """
        Fetch metrics for multiple stocks with rate limiting.
        
        Args:
            tickers: List of ticker symbols
            delay: Delay between requests (seconds)
            
        Returns:
            Dict mapping tickers to metrics
        """
        results = {}
        for ticker in tickers:
            try:
                metrics = self.get_metrics(ticker)
                if metrics:
                    results[ticker] = metrics
                    logger.info(f"✓ {ticker}")
                else:
                    logger.warning(f"✗ {ticker} - No data")
            except Exception as e:
                logger.error(f"✗ {ticker} - {e}")
            
            time.sleep(delay)
        
        return results
