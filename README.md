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

## Disclaimer

Educational and research purposes only. Not financial advice. Consult a financial advisor before investing.

---

**Copyright**: All rights reserved | **Status**: Production-ready

