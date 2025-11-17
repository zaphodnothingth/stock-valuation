"""
Buffett/Munger Valuation Calculator

This module implements the fundamental value calculation approach used by
Warren Buffett and Charlie Munger for identifying undervalued stocks.

Key Principles:
1. Free Cash Flow Analysis - Focus on sustainable cash generation
2. Return on Equity (ROE) & ROIC - Quality of business
3. Growth Rate - Conservative, sector-adjusted estimates
4. Margin of Safety - Varies based on business quality (not one-size-fits-all)
5. Quality Screening - Avoid value traps (cheap but declining)
"""

import logging
from typing import Dict, Optional, Tuple
import math

logger = logging.getLogger(__name__)

# Sector-specific characteristics for growth estimation
SECTOR_PROFILES = {
    # Ticker patterns -> (growth_rate, roe_threshold, sector_description)
    'TELECOM': {
        'tickers': ['T', 'VZ', 'VOX'],
        'base_growth': 0.02,  # Mature, declining industry
        'min_roe': 0.10,      # Lower expectations
        'description': 'Telecom - mature, regulated, declining'
    },
    'UTILITIES': {
        'tickers': ['NEE', 'DUK', 'SO'],
        'base_growth': 0.025,  # Regulatory constraints
        'min_roe': 0.08,
        'description': 'Utilities - stable, regulated, low growth'
    },
    'TECH_LARGE': {
        'tickers': ['AAPL', 'MSFT', 'GOOGL', 'NVDA'],
        'base_growth': 0.08,  # Mature, high valuation already
        'min_roe': 0.15,
        'description': 'Tech giants - strong moats, but mature valuations'
    },
    'NETWORK': {
        'tickers': ['V', 'MA'],  # NEW: Network payment processors
        'base_growth': 0.12,  # Higher growth justified: pricing power + network effects
        'min_roe': 0.40,      # These have exceptional ROE
        'description': 'Network processors - high moat, pricing power, minimal capex'
    },
    'FINTECH': {
        'tickers': ['PYPL'],
        'base_growth': 0.10,  # More conservative than network (has competition)
        'min_roe': 0.20,
        'description': 'Fintech - network effects, but more competitive'
    },
    'CONSUMER': {
        'tickers': ['PG', 'KO', 'PEP', 'WMT', 'MCD'],
        'base_growth': 0.03,  # Saturated markets
        'min_roe': 0.12,
        'description': 'Consumer staples - mature, limited growth'
    },
    'HEALTHCARE': {
        'tickers': ['JNJ', 'UNH', 'ABT'],
        'base_growth': 0.05,  # Regulatory headwinds, slower growth
        'min_roe': 0.12,
        'description': 'Healthcare - regulatory headwinds, slower growth'
    },
    'RETAIL': {
        'tickers': ['HD', 'MCD', 'SBUX'],
        'base_growth': 0.03,  # Saturated, cyclical
        'min_roe': 0.15,
        'description': 'Retail/Discretionary - mature, saturated'
    },
    'INDUSTRIALS': {
        'tickers': ['BA', 'IBM'],
        'base_growth': 0.03,  # Cyclical, mature
        'min_roe': 0.10,
        'description': 'Industrials - cyclical, tied to economy'
    },
    'MEDIA': {
        'tickers': ['DIS', 'NFLX'],
        'base_growth': 0.04,  # Streaming saturation, cord-cutting
        'min_roe': 0.12,
        'description': 'Media/Entertainment - secular headwinds'
    },
    'SOCIAL_MEDIA': {
        'tickers': ['META'],
        'base_growth': 0.12,  # AI growth opportunity
        'min_roe': 0.15,
        'description': 'Social Media - AI growth opportunity but uncertainty'
    },
}


class ValuationCalculator:
    """
    Implements improved Buffett-Munger valuation methodology.
    
    The approach:
    - Calculate Free Cash Flow (FCF) and ROIC
    - Sector-specific growth rates (not one-size-fits-all)
    - Quality-adjusted margin of safety (better businesses warrant higher prices)
    - Value trap detection (high FCF yield + low ROE = red flag)
    - Use DCF with risk-adjusted discounting
    """
    
    RISK_FREE_RATE = 0.045  # 10-year Treasury yield approximation
    MARKET_RISK_PREMIUM = 0.055  # Historical equity premium
    BETA_MARKET = 1.0
    
    # Quality-adjusted margin of safety
    # High quality (ROE >20%, ROIC >15%) can warrant lower MOS
    # Low quality (ROE <10%) needs higher MOS
    MARGIN_OF_SAFETY_HIGH_QUALITY = 0.20    # 20% for excellent businesses
    MARGIN_OF_SAFETY_MEDIUM_QUALITY = 0.35  # 35% for good businesses  
    MARGIN_OF_SAFETY_LOW_QUALITY = 0.50     # 50% for mediocre businesses
    MARGIN_OF_SAFETY_POOR_QUALITY = 0.65    # 65% for poor businesses
    
    # Value trap thresholds
    VALUE_TRAP_FCF_YIELD_MIN = 0.15  # >15% FCF yield is suspicious
    VALUE_TRAP_ROE_MAX = 0.10         # <10% ROE is concerning
    VALUE_TRAP_SCORE_THRESHOLD = 0.5  # >0.5 = likely value trap
    
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
    def calculate_roic(
        nopat: float,
        invested_capital: float
    ) -> float:
        """
        Calculate Return on Invested Capital (NOPAT / Invested Capital).
        
        ROIC is often more useful than ROE because it:
        - Includes both equity and debt financing
        - Shows returns on all capital employed, not just equity
        - Better captures competitive moat durability
        
        ROIC > WACC indicates the business creates value.
        ROIC > 15% is excellent, >10% is good.
        """
        if invested_capital <= 0:
            return 0
        return nopat / invested_capital
    
    @staticmethod
    def estimate_nopat(
        operating_income: float,
        tax_rate: float = 0.21
    ) -> float:
        """
        Estimate Net Operating Profit After Tax.
        
        NOPAT = Operating Income * (1 - Tax Rate)
        Used for ROIC calculation.
        """
        if operating_income <= 0:
            return 0
        return operating_income * (1 - tax_rate)
    
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
    def get_sector_growth_rate(ticker: str) -> Tuple[float, str]:
        """
        Determine sector-appropriate growth rate based on ticker/sector.
        
        Returns:
            Tuple of (growth_rate, sector_name)
        """
        ticker_upper = ticker.upper()
        
        for sector, profile in SECTOR_PROFILES.items():
            if ticker_upper in profile['tickers']:
                return profile['base_growth'], sector
        
        # Default: use conservative growth rate
        # (assumes mature company or unfamiliar ticker)
        return 0.04, 'UNKNOWN'
    
    @classmethod
    def calculate_quality_rating(
        cls,
        roe: float,
        roic: float = None,
        fcf_per_share: float = None,
        current_price: float = None
    ) -> Dict[str, any]:
        """
        Assess business quality based on return metrics.
        
        High ROE (>40%) gets special treatment:
        - These are exceptional businesses (network effects, pricing power)
        - Deserve lower MOS (can trade at premium)
        - Example: Visa, Mastercard
        
        Returns:
            Dict with quality rating and margin of safety
        """
        # Use ROE as primary metric if ROIC not available
        primary_return = roic if roic is not None and roic > 0 else roe
        
        # Special category for exceptional ROE businesses
        if primary_return >= 0.40:
            quality = 'EXCEPTIONAL'
            mos = 0.15  # Can pay 85% of IV for these (justified by moat)
        elif primary_return >= 0.25:
            quality = 'EXCELLENT'
            mos = cls.MARGIN_OF_SAFETY_HIGH_QUALITY
        elif primary_return >= 0.20:
            quality = 'EXCELLENT'
            mos = cls.MARGIN_OF_SAFETY_HIGH_QUALITY
        elif primary_return >= 0.15:
            quality = 'GOOD'
            mos = cls.MARGIN_OF_SAFETY_HIGH_QUALITY
        elif primary_return >= 0.10:
            quality = 'ADEQUATE'
            mos = cls.MARGIN_OF_SAFETY_MEDIUM_QUALITY
        elif primary_return >= 0.08:
            quality = 'POOR'
            mos = cls.MARGIN_OF_SAFETY_LOW_QUALITY
        else:
            quality = 'WEAK'
            mos = cls.MARGIN_OF_SAFETY_POOR_QUALITY
        
        return {
            'quality': quality,
            'return_metric': primary_return,
            'margin_of_safety': mos
        }
    
    @classmethod
    def detect_value_trap(
        cls,
        roe: float,
        fcf_per_share: float,
        current_price: float,
        growth_rate: float
    ) -> Dict[str, any]:
        """
        Detect potential value traps:
        - High FCF yield (>15%) with low ROE (<10%)
        - Suggests cash generation from declining business
        - Danger: dividend can't be sustained, business deteriorating
        
        Returns:
            Dict with value trap analysis
        """
        if current_price <= 0:
            return {'is_trap': False, 'trap_score': 0, 'reasons': []}
        
        fcf_yield = fcf_per_share / current_price if fcf_per_share > 0 else 0
        trap_score = 0
        reasons = []
        
        # Signal 1: Unusually high FCF yield
        if fcf_yield > cls.VALUE_TRAP_FCF_YIELD_MIN:
            trap_score += 0.4
            reasons.append(f"Very high FCF yield ({fcf_yield:.1%}) - may not be sustainable")
        
        # Signal 2: Low ROE (poor capital efficiency)
        if roe < cls.VALUE_TRAP_ROE_MAX:
            trap_score += 0.3
            reasons.append(f"Low ROE ({roe:.1%}) - weak capital efficiency")
        
        # Signal 3: Very low growth + high yield = mature/declining
        if growth_rate <= 0.03 and fcf_yield > 0.10:
            trap_score += 0.3
            reasons.append("Low growth + high yield profile suggests secular decline")
        
        is_trap = trap_score >= cls.VALUE_TRAP_SCORE_THRESHOLD
        
        return {
            'is_trap': is_trap,
            'trap_score': trap_score,
            'fcf_yield': fcf_yield,
            'reasons': reasons
        }
    
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
        ticker: str = None,
        growth_rate: float = None,
        wacc: float = None,
        terminal_growth_rate: float = 0.025,
        projection_years: int = 10
    ) -> Tuple[float, float]:
        """
        Calculate intrinsic value using Gordon Growth Model / DCF.
        
        Now uses sector-aware growth rates if ticker provided.
        Conservative approach: terminal growth capped at 2.5% (below long-term GDP).
        
        Args:
            fcf_per_share: Free cash flow per share
            ticker: Stock ticker (used for sector-specific growth rate)
            growth_rate: Override growth rate (if None, use sector default)
            wacc: Discount rate (if None, calculated)
            terminal_growth_rate: Long-term growth rate (capped at 2.5%)
            projection_years: Years to project
            
        Returns:
            Tuple of (intrinsic_value, value_with_margin_of_safety)
        """
        if fcf_per_share <= 0:
            return 0, 0
        
        # Determine growth rate from sector if not provided
        if growth_rate is None:
            if ticker:
                growth_rate, _ = cls.get_sector_growth_rate(ticker)
            else:
                growth_rate = 0.03  # Conservative default (was 0.04)
        
        # Ensure growth doesn't exceed reasonable bounds
        # Cap at 8% (rarely justified for mature businesses)
        growth_rate = min(max(growth_rate, 0.0), 0.08)
        
        # Terminal growth capped at 2.5% (below long-term GDP growth of ~3%)
        # This is more conservative than before (was 3%)
        terminal_growth_rate = min(terminal_growth_rate, 0.025)
        
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
        
        # Don't apply MOS here - let caller decide based on quality
        return intrinsic_value, intrinsic_value
    
    @classmethod
    def rate_valuation(
        cls,
        current_price: float,
        intrinsic_value: float,
        quality_rating: Dict,
        value_trap_analysis: Dict
    ) -> Dict[str, any]:
        """
        Rate the valuation with quality-aware margin of safety.
        
        Args:
            current_price: Current stock price
            intrinsic_value: Calculated intrinsic value
            quality_rating: Quality assessment dict
            value_trap_analysis: Value trap detection dict
            
        Returns:
            Dict with valuation assessment
        """
        if intrinsic_value <= 0:
            return {
                'rating': 'UNABLE_TO_CALCULATE',
                'discount': 0,
                'signal': 'SKIP'
            }
        
        # Apply quality-adjusted margin of safety
        mos = quality_rating['margin_of_safety']
        value_with_mos = intrinsic_value * (1 - mos)
        
        discount = (1 - current_price / intrinsic_value) * 100
        upside = ((intrinsic_value / current_price - 1) * 100) if current_price > 0 else 0
        
        # Flag value traps regardless of discount
        if value_trap_analysis['is_trap']:
            return {
                'rating': 'VALUE_TRAP',
                'discount': discount,
                'signal': 'AVOID',
                'upside_potential': upside,
                'quality': quality_rating['quality'],
                'warning': 'High FCF yield with low ROE - unsustainable'
            }
        
        # Normal valuation rating
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
            'upside_potential': upside,
            'quality': quality_rating['quality'],
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
        operating_income: float = None,
        invested_capital: float = None,
        growth_rate: float = None,
        years_of_history: int = 3
    ) -> Dict[str, any]:
        """
        Comprehensive stock analysis using improved Buffett-Munger approach.
        
        Key improvements:
        - Sector-aware growth rates
        - Quality-adjusted margin of safety
        - Value trap detection
        - ROIC calculation for better quality assessment
        
        Returns:
            Dict with full valuation analysis
        """
        # Calculate metrics
        fcf = cls.calculate_free_cash_flow(operating_cash_flow, capex)
        fcf_per_share = cls.calculate_fcf_per_share(fcf, shares_outstanding)
        roe = cls.calculate_roe(net_income, shareholders_equity)
        
        # Calculate ROIC if data available
        roic = None
        if operating_income and invested_capital:
            nopat = cls.estimate_nopat(operating_income)
            roic = cls.calculate_roic(nopat, invested_capital)
        
        # Get sector-specific growth rate if not provided
        if growth_rate is None:
            growth_rate, sector = cls.get_sector_growth_rate(ticker)
        else:
            _, sector = cls.get_sector_growth_rate(ticker)
        
        wacc = cls.calculate_wacc()
        
        # Calculate intrinsic value with sector-aware growth
        intrinsic_value, _ = cls.calculate_intrinsic_value(
            fcf_per_share,
            ticker=ticker,
            growth_rate=growth_rate,
            wacc=wacc
        )
        
        # Assess business quality
        quality_rating = cls.calculate_quality_rating(roe, roic, fcf_per_share, current_price)
        
        # Detect value traps
        value_trap_analysis = cls.detect_value_trap(roe, fcf_per_share, current_price, growth_rate)
        
        # Generate valuation rating
        valuation_rating = cls.rate_valuation(
            current_price,
            intrinsic_value,
            quality_rating,
            value_trap_analysis
        )
        
        # Apply quality-adjusted MOS for value_with_mos
        mos = quality_rating['margin_of_safety']
        value_with_mos = intrinsic_value * (1 - mos)
        
        analysis = {
            'ticker': ticker,
            'current_price': current_price,
            'metrics': {
                'fcf': fcf,
                'fcf_per_share': fcf_per_share,
                'roe': roe,
                'roic': roic,
                'operating_cash_flow': operating_cash_flow,
                'capex': capex,
            },
            'valuation': {
                'intrinsic_value': intrinsic_value,
                'value_with_margin_of_safety': value_with_mos,
                'wacc': wacc,
                'growth_rate': growth_rate,
                'sector': sector,
            },
            'quality': quality_rating,
            'value_trap_flag': value_trap_analysis,
            'assessment': valuation_rating,
        }
        
        return analysis
