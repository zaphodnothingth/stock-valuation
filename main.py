"""
Stock Valuation Service - Main Entry Point

Usage:
    python main.py                    # Analyze default list of stocks
    python main.py AAPL MSFT GOOGL   # Analyze specific stocks
    python main.py --sp500           # Analyze S&P 500 stocks (large dataset)
"""

import logging
import sys
from pathlib import Path
from recommender import StockRecommender, get_sp500_tickers

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
    if '--sp500' in sys.argv:
        logger.info("Fetching S&P 500 stocks...")
        tickers = get_sp500_tickers()
        logger.info(f"Analyzing {len(tickers)} S&P 500 stocks (this may take several minutes)...")
    elif len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        # Analyze user-specified stocks
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
    
    # Run analysis
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
