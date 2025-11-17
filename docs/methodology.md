# Methodology

How the valuation model works.

## Core Approach

Uses **Discounted Cash Flow (DCF)** analysis with principles from Warren Buffett and Charlie Munger:

1. **Free Cash Flow (FCF)** — Real cash available after capital investments
2. **Return on Equity (ROE)** — Quality of management's capital allocation
3. **Intrinsic Value** — DCF projection over 10 years + terminal value
4. **Margin of Safety** — 35% discount for downside protection

## Key Formulas

### Free Cash Flow
```
FCF = Operating Cash Flow - Capital Expenditures
```
Represents genuine cash a company generates after reinvestment.

### Return on Equity (ROE)
```
ROE = Net Income / Shareholders' Equity
```
Quality metric: >15% good, >20% excellent, >40% exceptional (network effects / moat).

### Intrinsic Value (DCF)
```
Intrinsic Value = PV(FCF Years 1–10) + PV(Terminal Value)
```
Where:
- Present Value uses WACC as discount rate
- Terminal Value = Year 10 FCF × (1 + growth rate) / (WACC − growth rate)
- Growth rate: typically 6% (conservative)
- Terminal growth: 2.5% (perpetual)

### Cost of Capital (WACC)
```
WACC = Risk-Free Rate + (Beta × Market Risk Premium)
```
Defaults:
- Risk-Free Rate: 4.5% (10-year Treasury)
- Market Risk Premium: 5.5%
- Beta: 1.0 (market average)

### Margin of Safety
```
Safe Entry Price = Intrinsic Value × 0.65
                 = Intrinsic Value × (1 − 0.35)
```
Provides 35% downside cushion.

## Quality Tiers

Stocks are classified by ROE:

| Tier | ROE | Description |
|------|-----|-------------|
| **EXCEPTIONAL** | >40% | Network effects, moat (Visa, Mastercard, Berkshire) — premium valuations justified |
| **EXCELLENT** | 20–40% | High-quality franchises |
| **GOOD** | 15–20% | Solid operators |
| **ADEQUATE** | 10–15% | Average quality |
| **POOR** | 8–10% | Below average |
| **WEAK** | <8% | Marginal operators |

## Valuation Signals

| Price vs. MOS Value | Signal | Meaning |
|-----|--------|---------|
| < MOS Value | **STRONG_BUY** | >35% discount, significant opportunity |
| < Intrinsic Value | **BUY** | Good opportunity |
| ≈ Intrinsic Value | **HOLD** | Fairly valued |
| > Intrinsic Value | **AVOID** | Overvalued |
| High yield + low ROE | **VALUE_TRAP** | Unsustainable cash generation (penalized) |

## Recommendation Scoring (0–100)

Composite score based on:

| Component | Weight | Scoring |
|-----------|--------|---------|
| **Discount** | 40% | >50% = 40 pts |
| **ROE Quality** | 30% | >25% = 30 pts |
| **FCF Yield** | 20% | >10% = 20 pts |
| **Signal Strength** | 10% | STRONG_BUY = 10 pts |

**Special cases**:
- **Value Traps**: Capped at ~20 pts (high yield + low ROE flagged as unsustainable)
- **Exceptional Quality**: Allow premium valuations (Buffett principle — pay for durability and moat)

## Sector-Specific Growth Rates

Growth rate varies by industry stability and maturity:

| Sector | Growth Rate |
|--------|------------|
| **Telecoms** | 2% |
| **Utilities** | 3% |
| **Retail** | 3% |
| **Financials** | 4% |
| **Consumer** | 5% |
| **Industrials** | 5% |
| **Healthcare** | 6% |
| **Tech (Large)** | 8% |
| **Tech (Growth)** | 10% |
| **Networks (V, MA)** | 12% |

## Value Trap Detection

Stocks are flagged as value traps if:
- **FCF Yield** > 10% (suggests unsustainable high payouts)
- **ROE** < 8% (low quality capital deployment)

These are penalized heavily in scoring and signal "AVOID".

## Assumptions & Defaults

Edit `valuation_calculator.py` to customize:

- **Projection Period**: 10 years
- **Terminal Growth**: 2.5%
- **Margin of Safety**: 35%
- **Risk-Free Rate**: 4.5%
- **Market Risk Premium**: 5.5%
- **Base Growth Rate**: 6%

## Limitations

1. **Data Availability**: Yahoo Finance may have incomplete or delayed data
2. **Growth Estimates**: Conservative defaults, not forward-looking
3. **Interest Rate Sensitivity**: WACC changes with rates; valuations move inversely
4. **Survivor Bias**: Only existing traded companies analyzed
5. **Historical Bias**: Past metrics don't predict future performance
6. **Currency**: Assumes USD; international stocks may have FX risk

## References

- Buffett, W. (2022). *Berkshire Hathaway Letters to Shareholders*
- Munger, C. (2021). *Charlie Munger's Investment Philosophy*
- Graham, B. (2006). *The Intelligent Investor* – Revised Edition
- Damodaran, A. (2012). *Investment Valuation: Tools and Techniques*
