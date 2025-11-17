# Stock Valuation Service - Quick Reference

## Status: ✅ Complete & Tested

**All 18 unit tests passing. End-to-end working with live data.**

---

## What This Does

Identifies **undervalued stocks** using Warren Buffett & Charlie Munger's fundamental analysis approach:
- Analyzes Free Cash Flow (FCF)
- Calculates Return on Equity (ROE)
- Computes intrinsic value using DCF (Discounted Cash Flow)
- Applies 35% margin of safety
- Scores and ranks opportunities

**Data Source**: Yahoo Finance (`yfinance`) — free, no API key needed.

---

## Quick Start

### Installation (one-time)
```bash
cd /home/zaphod/gits/stock-valuation
pip install -r requirements.txt
```

### Usage

**Run on default 30 stocks:**
```bash
python main.py
```

**Analyze specific tickers:**
```bash
python main.py AAPL MSFT GOOGL AMZN TSLA JPM JNJ
```

**Analyze all S&P 500 (5-10 min):**
```bash
python main.py --sp500
```

**Verbose logging:**
```bash
python main.py -v
```

**Run tests:**
```bash
python -m unittest test_valuation -v
```

---

## Output

### Console Display
```
Ticker   Price Intrinsic Value MOS Value Discount Upside    Signal         ROE    FCF Yield Score
   HD $362.36      $647.21    $420.68    44.0%   78.6%  STRONG_BUY      42.7%    4.95%     95.0
  PEP $145.85      $309.89    $201.43    52.9%  112.5%  STRONG_BUY      13.4%    5.89%     80.0
```

### CSV Export
- **File**: `stock_recommendations.csv`
- **Contents**: Top 15 recommendations with all metrics
- **Format**: Ready for Excel/Pandas analysis

### Detailed Log
- **File**: `valuation_analysis.log`
- **Contains**: Processing steps for each stock, debug info

---

## Methodology

### Key Metrics
| Metric | Formula | What It Means |
|--------|---------|---------------|
| FCF | Operating Cash Flow - CapEx | Real cash generated after investments |
| FCF/Share | FCF ÷ Shares Outstanding | Cash per share available for value |
| ROE | Net Income ÷ Shareholders' Equity | Quality of capital deployment |
| Intrinsic Value | DCF (10yr projection) + Terminal Value | True economic value |
| MOS Value | Intrinsic Value × 0.65 | Safe entry price (35% discount) |

### Valuation Signals

| Current Price vs. MOS Value | Signal | Meaning |
|-----|--------|---------|
| < MOS Value | **STRONG_BUY** | Significant opportunity (>35% discount) |
| < Intrinsic Value | **BUY** | Good opportunity |
| ≈ Intrinsic Value | **HOLD** | Fairly valued |
| > Intrinsic Value | **AVOID** | Overvalued |

### Scoring (0-100)
- **40%** Discount to intrinsic value (bigger discount = higher score)
- **30%** ROE quality (>25% excellent, >20% very good, >15% good)
- **20%** FCF yield (>10% excellent)
- **10%** Investment signal strength (STRONG_BUY > BUY > HOLD > AVOID)

---

## Architecture

| File | Purpose |
|------|---------|
| `valuation_calculator.py` | Core DCF & Buffett valuation logic |
| `data_fetcher.py` | Pulls financial data from Yahoo Finance, extracts metrics |
| `recommender.py` | Scores/ranks stocks, formats output |
| `main.py` | CLI entry point, orchestrates analysis |
| `test_valuation.py` | 18 unit + integration tests |
| `README.md` | Full documentation |

---

## Example Output (Latest Run)

**Top Recommendations:**
1. **HD** (Home Depot) - Score: 95.0 - STRONG_BUY
   - 44% discount to intrinsic value
   - ROE: 42.7% (Exceptional)
   - FCF Yield: 4.95%

2. **PEP** (PepsiCo) - Score: 80.0 - STRONG_BUY
   - 52.9% discount to intrinsic value
   - ROE: 13.4%
   - FCF Yield: 5.89%

3. **GOOGL** (Google) - Score: 75.0 - STRONG_BUY
   - 70.5% discount to intrinsic value
   - Upside potential: 239.4%

---

## Data Quality

**Stocks Analyzed**: 30 default + customizable  
**Success Rate**: ~87% (26/30 successful on recent run)  
**Skipped Reasons**: Missing financial data (BA, MCD, SBUX — typically newer or special structure)

---

## Assumptions & Customization

### Current Defaults (edit `valuation_calculator.py`)
- **Growth Rate**: 6% (conservative)
- **Margin of Safety**: 35%
- **Risk-Free Rate**: 4.5%
- **Market Risk Premium**: 5.5%
- **Projection Period**: 10 years

### Environment (`.env`)
Optional for future API expansions (Finnhub, AlphaVantage, Robinhood credentials)

---

## Limitations

1. **Data Availability**: Some tickers may lack full financial history
2. **Growth Estimates**: Uses conservative defaults; not forward-looking
3. **Market Changes**: WACC changes with interest rates (affects valuations)
4. **Not Trading Advice**: Educational tool only — consult financial advisor
5. **Survivor Bias**: Only analyzes currently trading companies

---

## Next Steps (If Desired)

- [ ] Add Robinhood integration for live account data
- [ ] Industry-specific growth rates (Tech, Healthcare, Retail, etc.)
- [ ] Debt/leverage screening
- [ ] Multi-year historical averaging
- [ ] Flask API wrapper for programmatic access
- [ ] Slack/Email alerts when stocks cross thresholds

---

## Files in Project

```
stock-valuation/
├── valuation_calculator.py      (DCF & valuation logic)
├── data_fetcher.py              (Yahoo Finance integration)
├── recommender.py               (Scoring & ranking)
├── main.py                      (CLI entry point)
├── test_valuation.py            (18 unit tests)
├── requirements.txt             (Dependencies)
├── .env.example                 (Optional config template)
├── README.md                    (Full documentation)
├── stock_recommendations.csv    (Output: top 15 stocks)
├── valuation_analysis.log       (Detailed processing log)
└── QUICKSTART.md               (This file)
```

---

## Support

**Errors?** Check `valuation_analysis.log` for details.  
**Want different stocks?** Pass ticker list: `python main.py TSLA NVDA AMD`  
**Want to modify logic?** Edit constants in `valuation_calculator.py` (growth_rate, MOS, etc.)

---

**Status**: Production-ready. Fully tested. No external dependencies (yfinance is free and stable).
