# Usage

Complete reference for all CLI options.

## Basic Commands

### Default Analysis
```bash
python main.py
```
Analyzes a curated default list of 30 well-known stocks.

### Specific Stocks
```bash
python main.py AAPL MSFT GOOGL AMZN TSLA JNJ V WMT JPM
```

## Universe Flags

### S&P 500 (503 stocks)
```bash
python main.py --sp500
```
All large-cap companies. Takes 5–10 minutes.

### Russell 2000 (272 stocks)
```bash
python main.py --russell2000
```
Small and mid-cap companies. Falls back to Russell 3000 if cache unavailable.

### Russell 3000 (3,559 stocks)
```bash
python main.py --russell3000
```
Comprehensive US market coverage. Takes 15–25 minutes. Requires local cache in `cache/russell3000.txt`.

### Nasdaq-100 (89 stocks)
```bash
python main.py --nasdaq100
```
Large-cap tech and growth leaders.

### Combined Universe (795 stocks)
```bash
python main.py --all
```
S&P 500 + Russell 2000 + Nasdaq-100, de-duplicated.

## Modifiers

### Limit Results
```bash
python main.py --sp500 --limit 100
python main.py --russell3000 --limit 500
```
Analyze only the first N stocks (useful for quick testing).

### Verbose Logging
```bash
python main.py --verbose
# or
python main.py -v
```
Print debug logs to console and file.

## Output

### Console
Prints top 15 recommendations with ticker, price, intrinsic value, MOS value, discount, upside, signal, ROE, FCF yield, and score.

### Files
- `stock_recommendations.csv` — CSV export of top 15 for Excel/Pandas
- `valuation_analysis.log` — Detailed processing log with per-stock analysis

## Examples

```bash
# Analyze top 50 S&P 500 stocks with debug output
python main.py --sp500 --limit 50 --verbose

# Quick test on specific names
python main.py AAPL MSFT GOOGL

# Full Russell 3000 (overnight run)
python main.py --russell3000
```

## Installation

```bash
pip install -r requirements.txt
```

Requires Python 3.8+, yfinance, pandas, numpy, python-dotenv.
