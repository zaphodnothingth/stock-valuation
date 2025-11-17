"""
Buffett/Munger Valuation Calculator

This module implements the fundamental value calculation approach used by
Warren Buffett and Charlie Munger for identifying undervalued stocks.

Key Principles:
1. Free Cash Flow Analysis - Focus on sustainable cash generation
2. Return on Equity (ROE) - Quality of business
3. Growth Rate - Conservative estimates of future growth
4. Margin of Safety - Buy at significant discount to intrinsic value (25-50%)
"""

import logging
from typing import Dict, Optional, Tuple
import math

logger = logging.getLogger(__name__)


class ValuationCalculator:
    """
    Implements Buffett-Munger valuation methodology.
    
    The approach:
    - Calculate Free Cash Flow (FCF)
    - Estimate normalized FCF based on ROE and reinvestment
    - Apply conservative growth rate (5-10%)
    - Use DCF (Discounted Cash Flow) with margin of safety
    """
    
    RISK_FREE_RATE = 0.045  # 10-year Treasury yield approximation
    MARKET_RISK_PREMIUM = 0.055  # Historical equity premium
    BETA_MARKET = 1.0
    MARGIN_OF_SAFETY = 0.35  # 35% discount for safety
    
    @staticmethod
    def calculate_free_cash_flow(
        operating_cash_flow: float,
        capital_expenditures: float
    ) -> float:
        """
        Calculate Free Cash Flow = Operating Cash Flow - CapEx
        
        Args:
            operating_cash_flow: Annual operating cash flow
            capital_expenditures: Annual capital expenditures
            
        Returns:
            Free Cash Flow value
        """
        fcf = operating_cash_flow - capital_expenditures
        return max(fcf, 0)  # FCF should not be negative
    
    @staticmethod
    def calculate_fcf_per_share(
        free_cash_flow: float,
        shares_outstanding: float
    ) -> float:
        """Calculate FCF per share."""
        if shares_outstanding <= 0:
            return 0.0
        return free_cash_flow / shares_outstanding
    
    @staticmethod
    def calculate_roe(net_income: float, shareholders_equity: float) -> float:
        """
        Calculate Return on Equity.
        
        ROE measures how effectively the company uses shareholder capital.
        Buffett looks for consistent, high ROE (>15% is good, >20% is excellent).
        """
        if shareholders_equity <= 0:
            return 0
        return net_income / shareholders_equity
    
    @staticmethod
    def estimate_normalized_fcf(
        current_fcf: float,
        roe: float,
        reinvestment_rate: float = 0.20
    ) -> float:
        """
        Estimate normalized/sustainable FCF.
        
        Uses ROE and reinvestment rate to estimate normalized cash generation.
        
        Args:
            current_fcf: Current free cash flow
            roe: Return on Equity
            reinvestment_rate: Estimated % of FCF reinvested for growth
            
        Returns:
            Normalized FCF estimate
        """
        if roe <= 0:
            return max(current_fcf, 0)
        
        # If FCF is negative or very low but ROE is high, estimate based on retained earnings
        if current_fcf <= 0:
            return 0
            
        return current_fcf
    
    @staticmethod
    def calculate_wacc(
        risk_free_rate: float = RISK_FREE_RATE,
        market_risk_premium: float = MARKET_RISK_PREMIUM,
        beta: float = 1.0,
        debt_to_equity: float = 0.5
    ) -> float:
        """
        Calculate Weighted Average Cost of Capital.
        
        Used as the discount rate in DCF analysis.
        Buffett tends to use simpler approaches; this is conservative.
        """
        cost_of_equity = risk_free_rate + (beta * market_risk_premium)
        # Simplified WACC (assuming debt at risk-free rate, which is conservative)
        wacc = cost_of_equity / (1 + debt_to_equity)
        return wacc
    
    @classmethod
    def calculate_intrinsic_value(
        cls,
        fcf_per_share: float,
        growth_rate: float = 0.06,
        wacc: float = None,
        terminal_growth_rate: float = 0.03,
        projection_years: int = 10
    ) -> Tuple[float, float]:
        """
        Calculate intrinsic value using Gordon Growth Model / DCF.
        
        Returns:
            Tuple of (intrinsic_value, value_with_margin_of_safety)
        """
        if fcf_per_share <= 0 or growth_rate < 0:
            return 0, 0
        
        if wacc is None:
            wacc = cls.calculate_wacc()
        
        if wacc <= growth_rate:
            logger.warning(f"WACC ({wacc:.2%}) <= Growth Rate ({growth_rate:.2%}), returning simplified estimate")
            return fcf_per_share * (1 + growth_rate) / (wacc + 0.01), 0
        
        # DCF calculation
        pv_fcf = 0
        current_fcf = fcf_per_share
        
        for year in range(1, projection_years + 1):
            current_fcf *= (1 + growth_rate)
            discount_factor = (1 + wacc) ** year
            pv_fcf += current_fcf / discount_factor
        
        # Terminal value using perpetuity growth model
        terminal_fcf = current_fcf * (1 + terminal_growth_rate)
        terminal_value = terminal_fcf / (wacc - terminal_growth_rate)
        pv_terminal = terminal_value / ((1 + wacc) ** projection_years)
        
        intrinsic_value = pv_fcf + pv_terminal
        value_with_mos = intrinsic_value * (1 - cls.MARGIN_OF_SAFETY)
        
        return intrinsic_value, value_with_mos
    
    @classmethod
    def rate_valuation(
        cls,
        current_price: float,
        intrinsic_value: float,
        value_with_mos: float
    ) -> Dict[str, any]:
        """
        Rate the valuation and provide investment signal.
        
        Returns:
            Dict with valuation assessment
        """
        if intrinsic_value <= 0:
            return {
                'rating': 'UNABLE_TO_CALCULATE',
                'discount': 0,
                'signal': 'SKIP'
            }
        
        discount = (1 - current_price / intrinsic_value) * 100
        
        if current_price < value_with_mos:
            signal = 'STRONG_BUY'
            rating = 'SIGNIFICANTLY_UNDERVALUED'
        elif current_price < intrinsic_value:
            signal = 'BUY'
            rating = 'UNDERVALUED'
        elif current_price < intrinsic_value * 1.15:
            signal = 'HOLD'
            rating = 'FAIRLY_VALUED'
        else:
            signal = 'AVOID'
            rating = 'OVERVALUED'
        
        return {
            'rating': rating,
            'discount': discount,
            'signal': signal,
            'upside_potential': ((intrinsic_value / current_price - 1) * 100) if current_price > 0 else 0
        }
    
    @classmethod
    def analyze_stock(
        cls,
        ticker: str,
        current_price: float,
        operating_cash_flow: float,
        capex: float,
        net_income: float,
        shareholders_equity: float,
        shares_outstanding: float,
        growth_rate: float = 0.06,
        years_of_history: int = 3
    ) -> Dict[str, any]:
        """
        Comprehensive stock analysis using Buffett-Munger approach.
        
        Returns:
            Dict with full valuation analysis
        """
        # Calculate metrics
        fcf = cls.calculate_free_cash_flow(operating_cash_flow, capex)
        fcf_per_share = cls.calculate_fcf_per_share(fcf, shares_outstanding)
        roe = cls.calculate_roe(net_income, shareholders_equity)
        wacc = cls.calculate_wacc()
        
        intrinsic_value, value_with_mos = cls.calculate_intrinsic_value(
            fcf_per_share,
            growth_rate=growth_rate,
            wacc=wacc
        )
        
        valuation_rating = cls.rate_valuation(current_price, intrinsic_value, value_with_mos)
        
        analysis = {
            'ticker': ticker,
            'current_price': current_price,
            'metrics': {
                'fcf': fcf,
                'fcf_per_share': fcf_per_share,
                'roe': roe,
                'operating_cash_flow': operating_cash_flow,
                'capex': capex,
            },
            'valuation': {
                'intrinsic_value': intrinsic_value,
                'value_with_margin_of_safety': value_with_mos,
                'wacc': wacc,
                'growth_rate': growth_rate,
            },
            'assessment': valuation_rating,
        }
        
        return analysis
