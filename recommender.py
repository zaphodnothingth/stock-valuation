"""
Stock recommendation engine.

Uses Buffett-Munger valuation to rank and recommend undervalued stocks.
"""

import logging
from typing import List, Dict, Optional
import pandas as pd
from valuation_calculator import ValuationCalculator
from data_fetcher import DataFetcher
from pathlib import Path

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
            
            # Use sector-aware growth rate from calculator (ignore fetcher's fixed rate)
            analysis = self.calculator.analyze_stock(
                ticker=ticker,
                current_price=metrics['current_price'],
                operating_cash_flow=metrics['operating_cash_flow'],
                capex=metrics['capex'],
                net_income=metrics['net_income'],
                shareholders_equity=metrics['total_equity'],
                shares_outstanding=metrics['shares_outstanding'],
                operating_income=metrics.get('operating_income'),
                invested_capital=metrics.get('invested_capital'),
                growth_rate=None,  # Let calculator use sector-aware rate
            )
            
            # Add quality metrics
            analysis['quality_metrics'] = {
                'fcf_yield': (analysis['metrics']['fcf_per_share'] / metrics['current_price'] * 100)
                    if metrics['current_price'] > 0 else 0,
                'pe_ratio': (metrics['current_price'] / (metrics['net_income'] / metrics['shares_outstanding']))
                    if metrics['net_income'] > 0 else 0,
                'roe_percent': analysis['metrics']['roe'] * 100,
                'roic_percent': (analysis['metrics']['roic'] * 100) if analysis['metrics']['roic'] else None,
            }
            
            # Check if it's a value trap - flag for potential exclusion
            is_value_trap = analysis['value_trap_flag']['is_trap']
            
            # Special handling for exceptional ROE businesses
            # These may look overvalued by DCF but are justified by moat + durability
            exceptional_quality = analysis['quality']['quality'] == 'EXCEPTIONAL'
            
            # Add recommendation score (0-100)
            # Value traps get severe penalty; exceptional quality gets boost
            analysis['recommendation_score'] = self._calculate_score(
                analysis, is_value_trap, exceptional_quality
            )
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return None
    
    def _calculate_score(self, analysis: Dict, is_value_trap: bool = False, 
                         exceptional_quality: bool = False) -> float:
        """
        Calculate a recommendation score (0-100) where higher = better.
        
        Improved scoring that favors quality:
        - Value trap severity (penalize heavily)
        - Business quality/ROE (30%)
        - Valuation discount (30%)
        - Signal strength (20%)
        - FCF sustainability (20%)
        - Exceptional quality: Allow premium valuations (Berkshire principle)
        """
        score = 0
        
        # CRITICAL: Value trap detection - penalize severely
        if is_value_trap:
            base_score = 20  # Max 20/100 for value traps
            trap_score = analysis['value_trap_flag']['trap_score']
            score += max(0, base_score * (1 - trap_score))
            logger.debug(f"{analysis['ticker']}: VALUE TRAP DETECTED - Score capped at ~{score:.1f}")
            return score
        
        # EXCEPTIONAL QUALITY: Buffett's principle - pay for quality
        # Exceptional ROE (40%+) businesses can trade at premium (like Visa, Mastercard)
        if exceptional_quality:
            roe = analysis['quality_metrics']['roe_percent']
            
            # For exceptional quality, valuation is less important than moat durability
            # Score based on: quality (heavy), signal (moderate), reasonableness (light)
            score += 35  # High base for exceptional quality
            
            # Signal quality
            signal = analysis['assessment']['signal']
            if signal == 'STRONG_BUY':
                score += 20
            elif signal == 'BUY':
                score += 15
            elif signal == 'HOLD':
                score += 5
            
            # FCF sustainability for exceptional businesses
            fcf_yield = analysis['quality_metrics']['fcf_yield']
            if 3 <= fcf_yield <= 10:  # Exceptional biz can have higher yields
                score += 25
            elif 2 < fcf_yield < 3 or 10 < fcf_yield <= 15:
                score += 15
            elif fcf_yield <= 2:
                score += 5
            
            return min(score, 100)
        
        # NORMAL QUALITY: Conservative scoring
        # Business quality assessment (30 points max)
        roe = analysis['quality_metrics']['roe_percent']
        roic = analysis['quality_metrics']['roic_percent']
        
        primary_return = roic if roic else roe
        
        if primary_return >= 25:
            quality_score = 30
        elif primary_return >= 20:
            quality_score = 28
        elif primary_return >= 15:
            quality_score = 22
        elif primary_return >= 12:
            quality_score = 15
        elif primary_return >= 8:
            quality_score = 8
        else:
            quality_score = 2
        
        score += quality_score
        
        # Valuation discount (30 points max)
        # Reasonable discounts warrant investment; extreme ones are suspicious
        discount = analysis['assessment']['discount']
        if 25 <= discount <= 60:
            discount_score = 30
        elif 15 < discount < 25 or 60 < discount <= 80:
            discount_score = 20
        elif 0 < discount <= 15:
            discount_score = 10
        elif discount > 80:
            discount_score = 5
            logger.debug(f"{analysis['ticker']}: Extreme discount ({discount:.1f}%) - suspicious")
        else:
            discount_score = 0
        
        score += discount_score
        
        # Signal strength (20 points max)
        signal = analysis['assessment']['signal']
        if signal == 'STRONG_BUY':
            score += 20
        elif signal == 'BUY':
            score += 15
        elif signal == 'HOLD':
            score += 5
        else:
            score += 0
        
        # FCF sustainability (20 points max)
        fcf_yield = analysis['quality_metrics']['fcf_yield']
        
        if 3 <= fcf_yield <= 8:
            fcf_score = 20
        elif 2 < fcf_yield < 3 or 8 < fcf_yield <= 12:
            fcf_score = 12
        elif fcf_yield <= 2:
            fcf_score = 5
        elif fcf_yield > 12:
            fcf_score = 3
            logger.debug(f"{analysis['ticker']}: High FCF yield ({fcf_yield:.1f}%) - may not be sustainable")
        else:
            fcf_score = 0
        
        score += fcf_score
        
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
            # Determine display rating (check for value trap)
            is_trap = analysis['value_trap_flag']['is_trap']
            display_rating = "VALUE_TRAP" if is_trap else analysis['assessment']['rating']
            
            row = {
                'Ticker': analysis['ticker'],
                'Price': f"${analysis['current_price']:.2f}",
                'Intrinsic Value': f"${analysis['valuation']['intrinsic_value']:.2f}",
                'MOS Value': f"${analysis['valuation']['value_with_margin_of_safety']:.2f}",
                'discount_percent': analysis['assessment']['discount'],
                'Discount': f"{analysis['assessment']['discount']:.1f}%",
                'Upside': f"{analysis['assessment']['upside_potential']:.1f}%",
                'Rating': display_rating,
                'Signal': analysis['assessment']['signal'],
                'Quality': analysis['quality']['quality'],
                'ROE': f"{analysis['quality_metrics']['roe_percent']:.1f}%",
                'ROIC': f"{analysis['quality_metrics']['roic_percent']:.1f}%" if analysis['quality_metrics']['roic_percent'] else "N/A",
                'FCF Yield': f"{analysis['quality_metrics']['fcf_yield']:.2f}%",
                'Growth Rate': f"{analysis['valuation']['growth_rate']:.1f}%",
                'Sector': analysis['valuation']['sector'],
                'recommendation_score': analysis['recommendation_score'],
                'Score': f"{analysis['recommendation_score']:.1f}",
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def print_recommendations(self, df: pd.DataFrame, show_all_columns: bool = False):
        """Pretty print recommendations."""
        print("\n" + "="*140)
        print("TOP UNDERVALUED STOCKS - Improved Buffett/Munger Analysis".center(140))
        print("="*140 + "\n")
        
        if show_all_columns:
            print(df.to_string(index=False))
        else:
            display_cols = ['Ticker', 'Price', 'Intrinsic Value', 'MOS Value', 'Discount', 
                          'Upside', 'Quality', 'ROE', 'FCF Yield', 'Sector', 'Rating', 'Signal', 'Score']
            cols_to_show = [c for c in display_cols if c in df.columns]
            print(df[cols_to_show].to_string(index=False))
        
        print("\n" + "="*140)
        print("Legend:")
        print("  MOS Value = Value with quality-adjusted Margin of Safety")
        print("  Discount = How much stock is discounted from intrinsic value")
        print("  Quality = EXCEPTIONAL (ROE >40% - network effects/moat) | EXCELLENT (>20%) | GOOD (>15%) | ADEQUATE (>10%) | POOR (<10%)")
        print("  Rating: SIGNIFICANTLY_UNDERVALUED | UNDERVALUED | FAIRLY_VALUED | OVERVALUED | VALUE_TRAP")
        print("  VALUE_TRAP = High FCF yield with low ROE (unsustainable cash generation)")
        print("  Signal: STRONG_BUY | BUY | HOLD | AVOID")
        print("  ROE = Return on Equity (>15% good, >20% excellent, >40% exceptional)")
        print("  FCF Yield = Free Cash Flow as % of stock price (3-8% is healthy)")
        print("  Sector = Industry classification with quality-appropriate growth expectations")
        print("="*140 + "\n")


def get_sp500_tickers() -> List[str]:
    """Get S&P 500 tickers for analysis."""
    import requests
    # If a local cached file exists, prefer it (offline-friendly)
    cache = Path('data/sp500.txt')
    if cache.exists():
        try:
            with cache.open() as f:
                tickers = [l.strip().upper().replace('.', '-') for l in f if l.strip()]
                if tickers:
                    return tickers
        except Exception:
            logger.debug('Failed to read local S&P500 cache; falling back to web fetch')
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    # Primary: pandas.read_html (fast when lxml/html5lib installed)
    try:
        tables = pd.read_html(url)
        df = tables[0]
        tickers = df['Symbol'].tolist()
        tickers = [t.replace('.', '-') for t in tickers]
        return tickers
    except Exception as e:
        msg = str(e)
        logger.debug(f"pandas.read_html failed for S&P500: {msg}")
        if "Missing optional dependency" in msg or "lxml" in msg:
            logger.error("HTML parser dependency missing (lxml/html5lib). Install requirements: pip install -r requirements.txt")

    # Secondary fallback: parse with requests + BeautifulSoup (if installed)
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', {'id': 'constituents'}) or soup.find('table', {'class': 'wikitable'})
        if table:
            rows = table.find_all('tr')
            tickers = []
            for r in rows[1:]:
                cols = r.find_all(['td', 'th'])
                if not cols:
                    continue
                # First column in the standard Wikipedia S&P table is the ticker symbol
                sym = cols[0].get_text(strip=True)
                if sym:
                    tickers.append(sym.replace('.', '-'))
            if tickers:
                return tickers
    except Exception as e:
        logger.debug(f"BeautifulSoup fallback failed for S&P500: {e}")
        if isinstance(e, ImportError):
            logger.error("BeautifulSoup not installed. Install with: pip install beautifulsoup4")

    logger.error("Could not fetch S&P 500 list automatically; returning fallback sample list")
    return [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
        'JNJ', 'V', 'WMT', 'JPM', 'MA',
        'PG', 'UNH', 'HD', 'DIS', 'NFLX',
        'IBM', 'T', 'VZ', 'KO', 'PEP'
    ]


def get_russell3000_tickers() -> List[str]:
    """Get Russell 3000 tickers (comprehensive US market: ~3000 largest companies).
    
    Prefers local cached file (data/russell3000.txt) for fully offline operation.
    
    To update the cache:
    1. Download from: https://www.kibot.com/Historical_Data/Russell_3000_Historical_Tick_Data.aspx
    2. Save HTML page to data/Russell_3000_Historical_Tick_Data.html
    3. Run: python3 -c "
        import re; from pathlib import Path
        html = Path('data/Russell 3000 Historical Tick Data.html').read_text()
        tickers = sorted(set(re.findall(r'>([A-Z]{1,5})<', html)))
        common = {'HTML', 'BODY', 'FORM', 'DIV', 'SPAN', 'TYPE', 'NAME', 'HREF', 'STYLE', 'CLASS', 'DATA', 'TEXT'}
        tickers = [t for t in tickers if t not in common and len(t) <= 5]
        Path('data/russell3000.txt').write_text('\\n'.join(tickers))
    "
    """
    cache = Path('data/russell3000.txt')
    if cache.exists():
        try:
            with cache.open() as f:
                tickers = [l.strip().upper().replace('.', '-') for l in f if l.strip()]
                if tickers:
                    return tickers
        except Exception:
            logger.debug('Failed to read local Russell 3000 cache')

    logger.warning('Russell 3000 cache not found at data/russell3000.txt')
    logger.warning('Download from: https://www.kibot.com/Historical_Data/Russell_3000_Historical_Tick_Data.aspx')
    # Fallback: return a representative sample
    return []


def get_russell2000_tickers() -> List[str]:
    """Get Russell 2000 tickers (small/mid-cap subset of Russell 3000).
    
    Prefers local cached file (data/russell2000.txt) if present.
    Otherwise falls back to Russell 3000 full universe.
    """
    cache = Path('data/russell2000.txt')
    if cache.exists():
        try:
            with cache.open() as f:
                tickers = [l.strip().upper().replace('.', '-') for l in f if l.strip()]
                if tickers:
                    return tickers
        except Exception:
            logger.debug('Failed to read local Russell2000 cache')

    # Fall back to Russell 3000 (full universe)
    r3000 = get_russell3000_tickers()
    if r3000:
        return r3000
    
    logger.warning('Could not fetch Russell tickers; returning empty list')
    return []


def get_nasdaq100_tickers() -> List[str]:
    """Fetch Nasdaq-100 tickers from Wikipedia where possible; fallback to a small sample."""
    url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    # Prefer local cache if available
    cache = Path('data/nasdaq100.txt')
    if cache.exists():
        try:
            with cache.open() as f:
                tickers = [l.strip().upper().replace('.', '-') for l in f if l.strip()]
                if tickers:
                    return tickers
        except Exception:
            logger.debug('Failed to read local Nasdaq100 cache; falling back to web fetch')

    try:
        tables = pd.read_html(url)
        for t in tables:
            cols = [c.lower() for c in t.columns.astype(str)]
            if any('ticker' in c or 'symbol' in c for c in cols):
                col_candidates = [c for c in t.columns if 'ticker' in str(c).lower() or 'symbol' in str(c).lower()]
                if col_candidates:
                    col = col_candidates[0]
                    tickers = t[col].astype(str).tolist()
                    tickers = [s.strip().replace('.', '-') for s in tickers if s and isinstance(s, str)]
                    return tickers
    except Exception as e:
        msg = str(e)
        logger.debug(f"pandas.read_html failed for Nasdaq-100: {msg}")
        if "Missing optional dependency" in msg or "lxml" in msg:
            logger.error("HTML parser dependency missing (lxml/html5lib). Install requirements: pip install -r requirements.txt")
        # Try BeautifulSoup fallback
        try:
            import requests
            from bs4 import BeautifulSoup
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            table = soup.find('table', {'class': 'wikitable'}) or soup.find('table')
            if table:
                rows = table.find_all('tr')
                tickers = []
                for r in rows[1:]:
                    cols = r.find_all(['td', 'th'])
                    if not cols:
                        continue
                    sym = cols[0].get_text(strip=True)
                    if sym:
                        tickers.append(sym.replace('.', '-'))
                if tickers:
                    return tickers
        except Exception as e:
            logger.debug(f"BeautifulSoup fallback failed for Nasdaq-100: {e}")
            logger.warning('Could not fetch Nasdaq-100 tickers automatically; returning fallback sample list')

    return [
        'AAPL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'GOOGL', 'META', 'PYPL', 'INTC', 'AMD'
    ]


def get_all_market_tickers() -> List[str]:
    """Combine several universes to produce a broader market list.

    Currently combines S&P 500, Russell 2000 and Nasdaq-100 (de-duplicated).
    This produces a wide opportunity cone without attempting to fetch every single stock on the exchanges.
    """
    sp = []
    r2 = []
    nq = []
    try:
        sp = get_sp500_tickers()
    except Exception as e:
        logger.debug(f"SP500 fetch failed in aggregator: {e}")
    try:
        r2 = get_russell2000_tickers()
    except Exception as e:
        logger.debug(f"Russell2000 fetch failed in aggregator: {e}")
    try:
        nq = get_nasdaq100_tickers()
    except Exception as e:
        logger.debug(f"Nasdaq100 fetch failed in aggregator: {e}")

    combined = list(dict.fromkeys([t.upper() for t in (sp or []) + (r2 or []) + (nq or [])]))
    return combined
