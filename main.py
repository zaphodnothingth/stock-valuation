"""
Stock Valuation Service - Main Entry Point

Usage:
    python main.py                           # Analyze default list of stocks
    python main.py AAPL MSFT GOOGL          # Analyze specific stocks
    python main.py --sp500                   # Analyze S&P 500 stocks (503 tickers)
    python main.py --russell2000             # Analyze Russell 2000 (272 tickers, or falls back to Russell 3000)
    python main.py --russell3000             # Analyze Russell 3000 (comprehensive US market, 3559 tickers)
    python main.py --nasdaq100               # Analyze Nasdaq-100 (large-cap tech/growth, 89 tickers)
    python main.py --all                     # Analyze all universes combined (de-duplicated)
    python main.py --sp500 --limit 50        # Limit analysis to first N stocks
    python main.py --verbose                 # Enable debug output
"""

import logging
import sys
from pathlib import Path
from src.recommender import StockRecommender, get_sp500_tickers, get_russell3000_tickers, get_russell2000_tickers, get_nasdaq100_tickers, get_all_market_tickers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('valuation_analysis.log')
    ]
)
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    for handler in logging.root.handlers:
        handler.setLevel(level)


def main():
    """Main entry point."""
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    setup_logging(verbose)
    # Determine which stocks to analyze
    # Flags supported: --sp500, --russell2000, --russell3000, --nasdaq100, --all, or a list of tickers
    limit = None
    if '--limit' in sys.argv:
        try:
            idx = sys.argv.index('--limit')
            limit = int(sys.argv[idx + 1])
            logger.info(f"Limiting universe to first {limit} tickers")
        except Exception:
            logger.warning("Invalid --limit usage; ignoring limit")

    if '--sp500' in sys.argv:
        logger.info("Fetching S&P 500 stocks...")
        tickers = get_sp500_tickers()
        logger.info(f"Analyzing {len(tickers)} S&P 500 stocks (this may take several minutes)...")
    elif '--russell3000' in sys.argv:
        logger.info("Fetching Russell 3000 stocks (comprehensive US market)...")
        tickers = get_russell3000_tickers()
        if not tickers:
            logger.error("Russell 3000 cache not found. Download from: https://www.kibot.com/Historical_Data/Russell_3000_Historical_Tick_Data.aspx")
            sys.exit(1)
        logger.info(f"Analyzing {len(tickers)} Russell 3000 stocks (this will take a long time)...")
    elif '--russell2000' in sys.argv:
        logger.info("Fetching Russell 2000 stocks (small/mid-cap universe)...")
        tickers = get_russell2000_tickers()
        if not tickers:
            logger.info("Russell 2000 not found; using Russell 3000 as fallback")
            from recommender import get_russell3000_tickers
            tickers = get_russell3000_tickers()
        logger.info(f"Analyzing {len(tickers)} Russell tickers (this may take several minutes)...")
    elif '--nasdaq100' in sys.argv:
        logger.info("Fetching Nasdaq-100 stocks (large-cap tech/growth leaders)...")
        tickers = get_nasdaq100_tickers()
        logger.info(f"Analyzing {len(tickers)} Nasdaq-100 stocks (this may take several minutes)...")
    elif '--all' in sys.argv:
        logger.info("Fetching a broad market universe (S&P500 + Russell + Nasdaq-100)...")
        tickers = get_all_market_tickers()
        logger.info(f"Analyzing {len(tickers)} market tickers (this may take a long time)...")
    elif len([a for a in sys.argv[1:] if not a.startswith('--')]) > 0:
        # Analyze user-specified stocks (allow mixing flags)
        tickers = [arg.upper() for arg in sys.argv[1:] if not arg.startswith('--')]
    else:
        # Default: analyze a curated list of well-known stocks
        logger.info("Using default stock list...")
        tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
            'JNJ', 'V', 'WMT', 'JPM', 'MA',
            'PG', 'UNH', 'HD', 'DIS', 'NFLX',
            'NVDA', 'META', 'PYPL', 'INTC', 'AMD',
            'BA', 'IBM', 'T', 'VZ', 'KO',
            'PEP', 'MCD', 'NKE', 'SBUX', 'ABT'
        ]

    # Apply optional limit
    if limit and isinstance(tickers, (list, tuple)):
        tickers = tickers[:limit]    # Run analysis
    try:
        recommender = StockRecommender()
        logger.info(f"\nStarting analysis of {len(tickers)} stocks...\n")
        
        # Analyze and get recommendations
        recommendations = recommender.analyze_universe(tickers, top_n=15)
        
        # Display results
        if len(recommendations) > 0:
            recommender.print_recommendations(recommendations)
            
            # Save to CSV
            output_file = 'stock_recommendations.csv'
            recommendations.to_csv(output_file, index=False)
            logger.info(f"Results saved to {output_file}")
        else:
            logger.warning("No recommendations generated. Check data availability.")
    
    except KeyboardInterrupt:
        logger.info("\nAnalysis cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=verbose)
        sys.exit(1)


if __name__ == '__main__':
    main()
