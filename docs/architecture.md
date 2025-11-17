# Architecture

Code structure and data flow.

## Project Structure

```
stock-valuation/
├── README.md                    # Landing page
├── requirements.txt             # Dependencies
├── main.py                      # CLI entry point
├── valuation_calculator.py      # Core DCF & scoring
├── data_fetcher.py              # Yahoo Finance integration
├── recommender.py               # Analysis orchestration
├── test_valuation.py            # Unit & integration tests
├── cache/                       # Tracked ticker caches
│   ├── sp500.txt
│   ├── nasdaq100.txt
│   ├── russell2000.txt
│   └── russell3000.txt
└── docs/                        # Documentation
    ├── quickstart.md            # Copy/paste commands
    ├── usage.md                 # CLI reference
    ├── methodology.md           # Valuation model
    ├── architecture.md          # This file
    └── status.md                # Test results
```

## Module Overview

### `main.py`
Entry point. Parses CLI arguments, dispatches to `StockRecommender`, formats output.

**Key functions**:
- Argument parsing (`--sp500`, `--russell3000`, `--limit`, `--verbose`)
- Load tickers from universe flags
- Call `recommender.analyze_universe()`
- Export results to CSV and log

### `valuation_calculator.py`
Core valuation engine.

**Key classes**:
- `ValuationCalculator` — DCF, intrinsic value, scoring

**Key methods**:
- `analyze_stock()` — Single stock analysis
- `calculate_intrinsic_value()` — DCF projection
- `calculate_score()` — 0–100 recommendation score
- `get_sector_growth_rate()` — Sector-aware growth rates

**Config** (edit to customize):
- Growth rates by sector
- WACC components (risk-free rate, market risk premium)
- Margin of safety (35%)
- Quality tiers (ROE thresholds)

### `data_fetcher.py`
Fetches and caches financial data from Yahoo Finance.

**Key class**:
- `DataFetcher` — Retrieves metrics

**Key methods**:
- `get_metrics()` — Extract FCF, ROE, shares, price for a ticker
- Pulls: operating cash flow, capex, net income, equity, shares outstanding
- Warns if CapEx is $0 or ROE seems low (data quality issues)

**Limitations**:
- Relies on Yahoo Finance; some tickers may lack full history
- Quarterly vs. annual data confusion (flagged in logs)

### `recommender.py`
Analysis orchestration and ranking.

**Key class**:
- `StockRecommender` — Coordinates analysis

**Key methods**:
- `analyze_stock()` — Per-stock analysis using calculator + fetcher
- `analyze_universe()` — Batch analysis & ranking
- `_calculate_score()` — Special handling for value traps & exceptional quality
- `print_recommendations()` — Format output

**Ticker functions** (cache-first, fallback to web):
- `get_sp500_tickers()` — 503 stocks
- `get_russell2000_tickers()` — 272 stocks (fallback to R3000)
- `get_russell3000_tickers()` — 3,559 stocks
- `get_nasdaq100_tickers()` — 89 stocks
- `get_all_market_tickers()` — Combined de-duplicated

### `test_valuation.py`
Unit and integration tests.

**Coverage**:
- FCF calculations
- ROE metrics
- Intrinsic value computation
- Valuation ratings & signals
- Score calculations
- Value trap detection
- Data fetching & caching
- Full end-to-end workflows

Run with:
```bash
python -m unittest test_valuation -v
```

## Data Flow

```
1. CLI args → main.py
2. Parse universe flag (--sp500, --russell3000, etc.)
3. Load tickers from cache/
4. For each ticker:
   a. data_fetcher.get_metrics() → financial data
   b. valuation_calculator.analyze_stock() → DCF & scoring
   c. recommender._calculate_score() → 0–100 rating
5. Sort by score, export top 15
6. Save to CSV + log
```

## Caching Strategy

**Ticker caches** (tracked in `cache/`):
- `cache/sp500.txt` — 503 S&P 500 tickers
- `cache/russell2000.txt` — 272 Russell 2000 tickers
- `cache/russell3000.txt` — 3,559 Russell 3000 tickers
- `cache/nasdaq100.txt` — 89 Nasdaq-100 tickers

**Priority**:
1. Check `cache/` (preferred — local, fast)
2. Fall back to `data/` if present
3. Fall back to web scrape (Wikipedia, etc.) if available
4. Return empty with warning if all fail

**Philosophy**: Offline-first. No external dependencies or API calls required if caches exist.

## Quality Levels & Penalties

### Value Trap Detection
If FCF yield >10% AND ROE <8%, stock is flagged and score capped at ~20/100.

### Exceptional Quality Boost
If ROE >40%, stock gets premium valuation allowance (can trade above intrinsic value; Buffett principle).

### Normal Quality Scoring
Standard 0–100 composite based on discount, ROE, FCF yield, signal.

## Output Format

### Console
ASCII table with top 15 recommendations:
- Ticker, Price, Intrinsic Value, MOS Value
- Discount %, Upside %, Quality tier, ROE, FCF Yield
- Rating (STRONG_BUY, BUY, HOLD, AVOID, VALUE_TRAP)
- Score (0–100)

### CSV (`stock_recommendations.csv`)
Same fields as console, importable to Excel/Pandas.

### Log (`valuation_analysis.log`)
- Per-stock processing details
- Warnings (CapEx=$0, low ROE, etc.)
- Debug output if `--verbose`

## Configuration

**Environment** (optional `.env`):
- Future: API keys for Finnhub, AlphaVantage, Robinhood
- Currently unused (yfinance needs no auth)

**Code constants** (edit in `valuation_calculator.py`):
- Sector growth rates
- WACC components
- Quality tier thresholds
- Margin of safety
- Projection years

## Testing Strategy

**Unit tests** cover:
- Individual calculation functions
- Edge cases (zero values, negative ROE, etc.)
- Data validation

**Integration tests** cover:
- Full analysis pipeline (fetch → calculate → score)
- CSV export
- Ranking logic

Run tests:
```bash
python -m unittest test_valuation -v
```

## Future Extensibility

**Easy wins**:
- Add more sector-specific growth rates
- Implement multi-year historical averaging
- Add debt ratio screening

**Medium work**:
- Flask API wrapper for programmatic access
- Sector filtering (`--sector TECH`)
- Dividend analysis

**Major features**:
- Robinhood broker integration
- Machine learning for growth prediction
- Portfolio optimization

## Dependencies

See `requirements.txt`:
- `yfinance` — Yahoo Finance data (free)
- `pandas` — Data manipulation
- `numpy` — Numerical operations
- `python-dotenv` — Environment variables
- `lxml`, `html5lib`, `beautifulsoup4` — HTML parsing (fallbacks)

All free and stable.
