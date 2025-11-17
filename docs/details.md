# Stock Valuation Service - Buffett/Munger Approach

A Python service that recommends undervalued stocks using the fundamental valuation principles of Warren Buffett and Charlie Munger.

## Overview

This service analyzes stocks based on:

1. **Free Cash Flow (FCF)** - Sustainable cash generation after capital investments
2. **Return on Equity (ROE)** - Quality of capital allocation
3. **Intrinsic Value** - True economic value using DCF (Discounted Cash Flow) analysis
4. **Margin of Safety** - 35% discount to intrinsic value for risk protection

The approach prioritizes:
- Companies with strong, consistent FCF generation
- High ROE (>15% good, >20% excellent)
- Minimal debt and strong balance sheets
- Long-term value over short-term price movements

## Key Metrics

- **Intrinsic Value**: Calculated using 10-year DCF projection with terminal value
- **Margin of Safety Value**: Intrinsic value discounted by 35% (conservative buffer)
- **Discount**: How much the current price is below intrinsic value
- **Upside Potential**: Expected return if stock reaches intrinsic value
- **Recommendation Score**: 0-100 rating combining all factors

## Installation

```bash
pip install -r requirements.txt
```

**Requirements:**
- Python 3.8+
- yfinance (Yahoo Finance data)
- pandas (data analysis)
- numpy (numerical operations)
- python-dotenv (environment variable management)

## Usage

### Basic Usage - Default Stock List

```bash
python main.py
```

Analyzes a curated list of 30 well-known stocks and displays top 15 recommendations.

### Analyze Specific Stocks

```bash
python main.py AAPL MSFT GOOGL AMZN TSLA
```

Analyzes only the specified tickers.

### Universe Flags - Analyze Market Segments

#### S&P 500 (503 large-cap stocks)
```bash
python main.py --sp500
```
Analyzes all 500 S&P 500 stocks (may take 5-10 minutes).

#### Russell 2000 (272 small/mid-cap stocks)
```bash
python main.py --russell2000
```
Analyzes small and mid-cap companies (1-2 minutes).

#### Russell 3000 (3,559 comprehensive US market)
```bash
python main.py --russell3000
```
Analyzes the entire US stock market universe (10-20 minutes). **Requires** `data/russell3000.txt` cache. To update:
1. Download from https://www.kibot.com/Historical_Data/Russell_3000_Historical_Tick_Data.aspx
2. Extract using the documented method in `recommender.py`'s `get_russell3000_tickers()` function

#### Nasdaq-100 (89 large-cap tech/growth leaders)
```bash
python main.py --nasdaq100
```
Analyzes top Nasdaq stocks, with emphasis on tech sector (1-2 minutes).

#### Combined Market Analysis (795 stocks)
```bash
python main.py --all
```
Analyzes S&P 500, Russell 2000, and Nasdaq-100 combined with de-duplication (5-10 minutes).

### Limit Stocks for Faster Testing

```bash
python main.py --sp500 --limit 100
python main.py --russell3000 --limit 500
python main.py --all --limit 200
```

Limits analysis to the first N stocks (useful for quick testing).

### Verbose Logging

```bash
python main.py -v
```

Shows detailed logging for debugging.

## Output

### Console Output

Displays top 15 recommendations with:
- **Ticker**: Stock symbol
- **Price**: Current market price
- **Intrinsic Value**: Calculated fair value
- **MOS Value**: Margin of Safety value (35% discount)
- **Discount**: % below intrinsic value
- **Upside**: Expected return to intrinsic value
- **Rating**: SIGNIFICANTLY_UNDERVALUED | UNDERVALUED | FAIRLY_VALUED | OVERVALUED
- **Signal**: STRONG_BUY | BUY | HOLD | AVOID
- **ROE**: Return on Equity (%)
- **FCF Yield**: Free Cash Flow as % of stock price
- **Score**: 0-100 recommendation rating

### CSV Output

Results are saved to `stock_recommendations.csv` for further analysis.

### Log File

Detailed logging is saved to `valuation_analysis.log`.

## Architecture

### `valuation_calculator.py`
Core valuation logic implementing:
- FCF calculations
- ROE analysis
- WACC (cost of capital) estimation
- DCF-based intrinsic value
- Margin of safety analysis

### `data_fetcher.py`
Fetches financial data using:
- Yahoo Finance (yfinance) - Free, comprehensive data
- Quarterly financial statements (cash flow, income, balance sheet)
- Caching to minimize API calls

### `recommender.py`
Recommendation engine:
- Analyzes individual stocks
- Scores opportunities (0-100)
- Ranks portfolio of stocks
- Formats results for display

### `main.py`
CLI entry point with:
- Command-line argument parsing
- Batch analysis
- Progress tracking
- Results formatting and export

### `test_valuation.py`
Unit tests covering:
- Valuation calculations
- Data fetching
- Recommendation scoring
- Integration tests

## Recommendation Logic

Scores are calculated based on:

| Factor | Weight | Scoring |
|--------|--------|---------|
| Discount to Intrinsic Value | 40% | >50% discount = 40 pts |
| ROE Quality | 30% | >25% ROE = 30 pts |
| FCF Yield | 20% | >10% yield = 20 pts |
| Investment Signal | 10% | STRONG_BUY = 10 pts |

### Investment Signals

- **STRONG_BUY**: Price < MOS Value (significant opportunity)
- **BUY**: Price < Intrinsic Value (good opportunity)
- **HOLD**: Price near Intrinsic Value (fairly valued)
- **AVOID**: Price > Intrinsic Value (overvalued)

## Valuation Methodology

### Free Cash Flow
```
FCF = Operating Cash Flow - Capital Expenditures
```

### Return on Equity
```
ROE = Net Income / Shareholders' Equity
```

### Cost of Capital (WACC)
```
WACC = Risk-Free Rate + (Beta × Market Risk Premium)
```

Defaults:
- Risk-Free Rate: 4.5% (10-year Treasury)
- Market Risk Premium: 5.5%
- Beta: 1.0 (market average)

### Intrinsic Value (DCF)
```
Intrinsic Value = PV(FCF Years 1-10) + PV(Terminal Value)

Where:
- Terminal Value uses Gordon Growth Model with 3% perpetual growth
- Discount rate = WACC
- Growth rate typically 6% (conservative)
```

### Margin of Safety
```
Safe Entry Price = Intrinsic Value × (1 - 0.35)
= Intrinsic Value × 0.65
```

## Running Tests

```bash
python -m pytest test_valuation.py -v
```

Or use unittest:

```bash
python test_valuation.py
```

Coverage includes:
- ✓ FCF calculations
- ✓ ROE analysis
- ✓ Intrinsic value computation
- ✓ Valuation ratings
- ✓ Score calculations
- ✓ Data caching
- ✓ Integration workflows

## Data Sources

### Ticker Lists (Cached Locally)

The system uses pre-cached ticker lists for offline operation and reliability:

| Universe | Count | Source | Cache File |
|----------|-------|--------|-----------|
| S&P 500 | 503 | GitHub datasets repo | `data/sp500.txt` |
| Nasdaq-100 | 89 | Curated list | `data/nasdaq100.txt` |
| Russell 3000 | 3,559 | kibot.com HTML extract | `data/russell3000.txt` |

**Note on Russell 3000**: To update, download the HTML from https://www.kibot.com/Historical_Data/Russell_3000_Historical_Tick_Data.aspx and save to `data/Russell_3000_Historical_Tick_Data.html`, then run the extraction documented in `recommender.py`'s `get_russell3000_tickers()` function.

### Primary: Yahoo Finance (yfinance)
- Free, no API key required
- Comprehensive financial data
- Quarterly and annual statements
- Real-time stock prices

### Alternative Sources (Future)
- Finnhub API (more detailed metrics)
- Alpha Vantage (extended history)
- Robinhood API (alternative broker data)
- SEC EDGAR (official filings)

## Limitations & Considerations

1. **Data Quality**: Relies on Yahoo Finance data accuracy
2. **Growth Estimates**: Uses conservative 6% default (adjust per industry)
3. **Currency**: Assumes USD pricing
4. **Survivorship Bias**: Only analyzes currently trading stocks
5. **Market Conditions**: Valuation changes with interest rates (WACC)
6. **Individual Analysis**: Should supplement (not replace) personal research

## Configuration

Create `.env` file for optional customization:

```bash
# Growth rate assumptions by industry
TECH_GROWTH_RATE=0.08
HEALTHCARE_GROWTH_RATE=0.06
RETAIL_GROWTH_RATE=0.03
```

## Future Enhancements

We organize upcoming work into prioritized groups so the roadmap is actionable.

Major Planned Features (next priority):
- [ ] Sector filtering and subgroup analysis — allow users to run the model on specific sectors (e.g., Technology, Financials, Healthcare), and support sector-based growth assumptions and weighting. This is a major feature that will enable targeted opportunity cones and sector rotation strategies.
- [ ] Industry-specific growth rate adjustments — more granular, data-driven growth assumptions per industry/subsector.

Short-term Enhancements (nice wins, few-day sprints):
- [ ] Multi-year historical average metrics — smooth noisy year-to-year inputs using multi-year averages.
- [ ] Dividend analysis and reinvestment — display dividend yields and flag unsustainable payouts (won't change FCF-based valuation logic).
- [ ] Debt ratio and leverage analysis — integrate balance-sheet risk metrics into scoring.

Medium-term Enhancements (multi-week):
- [ ] Competitor comparison — peer-group valuation adjustments and relative scoring.
- [ ] Sector rotation strategies — implement presets and filters to support sector-focused analysis.
- [ ] Real-time alerts for crossed thresholds — webhook/email alerts for price/quality threshold crossings.

Long-term / Ambitious (research + infra):
- [ ] Portfolio construction optimizer — build mean-variance / Kelly-inspired portfolio sizing based on our scores.
- [ ] Machine learning for growth prediction — experiment with ML signals to refine growth inputs (research-grade).
- [ ] Robinhood / broker integration for live trading (optional) — place orders from recommendations (requires careful risk controls).

Other Nice-to-haves:
- [ ] International universes and non-US exchanges
- [ ] Extended small/mid-cap universes (Russell 2000 integration)
- [ ] More data sources (Finnhub, Alpha Vantage, SEC EDGAR)

If you'd like, I can start the sector-filtering feature next (it will involve: adding sector lookup, CLI flags like `--sector TECH`, filtering utilities, and UI/CSV output support). 

## References

- Buffett, W. (2022). Berkshire Hathaway Letters to Shareholders
- Munger, C. (2021). Charlie Munger's Investment Philosophy
- Graham, B. (2006). The Intelligent Investor - Revised Edition
- Damodaran, A. (2012). Investment Valuation: Tools and Techniques

## Disclaimer

This tool is for educational and research purposes only. It is not financial advice. 
Consult a qualified financial advisor before making investment decisions. Past performance 
does not guarantee future results. Stock market investments carry risk of loss.

## License

MIT License - Feel free to use and modify for personal or commercial use.

---

**Author**: AI Stock Analysis Agent  
**Created**: 2025  
**Status**: Beta
