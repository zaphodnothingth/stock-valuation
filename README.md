# Stock Valuation Service

Identifies undervalued stocks using Warren Buffett & Charlie Munger's fundamental analysis principles.

## What It Does

Analyzes **Free Cash Flow**, **Return on Equity**, and **Intrinsic Value** using DCF (Discounted Cash Flow) to score and rank investment opportunities.

Data source: Yahoo Finance (free, no API key required).

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Done. You get ranked undervalued stocks from a curated list of 30 companies.

## Documentation

| Doc | Purpose |
|-----|---------|
| **[Quickstart](docs/quickstart.md)** | Copy/paste commands for common scenarios |
| **[Usage](docs/usage.md)** | Full CLI reference: all flags and options |
| **[Methodology](docs/methodology.md)** | How the valuation model works (formulas, scoring, quality tiers) |
| **[Architecture](docs/architecture.md)** | Code structure, modules, data flow |
| **[Status](docs/status.md)** | Test results, system validation, known limitations |

## Installation

```bash
python 3.8+
pip install -r requirements.txt
```

## TODO
1. take into account chronically undervalued stocks as non-buys.  
1. how would shorting Mötley fool suggested sells perform?
1. UI?
1. vitality index for growth stocks only?
    a. 3M's identity as an innovator is best evaluated by its own New Product Vitality Index (NPVI) developed in the 1980s. This percentage measures the contribution of products launched in the past five years to overall revenue. The indicator met the company's long-term "30% rule" nearly a decade ago but fell to 10% in 2024, and that's after excluding the healthcare spinoff with a dismal vitality index score of just 2%.

## Disclaimer

Educational and research purposes only. Not financial advice. Consult a financial advisor before investing.

---

**Copyright**: All rights reserved | **Status**: Production-ready

