---
name: sharia-screening
description: Screen stocks and companies for Sharia compliance using AAOIFI Standard No. 21. Performs qualitative sector analysis and quantitative financial ratio checks (debt, cash, impure income). Outputs compliant/non-compliant verdict with purification ratio.
---

# Sharia Screening

Screen stocks, ETFs, and companies for Sharia compliance based on AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) Standard No. 21.

## When to Use

- User asks if a stock or company is halal / Sharia-compliant
- User wants to screen their portfolio for compliance
- User asks about AAOIFI screening criteria
- User wants to calculate the purification amount for a holding

## How It Works

### Step 1: Identify the Company

Get the ticker symbol or company name from the user. If screening multiple stocks, collect all tickers.

### Step 2: Qualitative Screening (Business Activity)

The company's **core business** must NOT be in any prohibited sector:

| #   | Prohibited Sector              | Examples                                    |
| --- | ------------------------------ | ------------------------------------------- |
| 1   | Alcohol                        | Breweries, distributors, bars               |
| 2   | Gambling                       | Casinos, betting platforms, lotteries       |
| 3   | Conventional Banking/Insurance | Interest-based banks, conventional insurers |
| 4   | Weapons & Defense              | Arms manufacturing (controversial weapons)  |
| 5   | Tobacco                        | Cigarette manufacturers                     |
| 6   | Adult Entertainment            | Pornography, adult content                  |
| 7   | Pork & Non-Halal Food          | Pork production, non-halal food processing  |
| 8   | Interest-Based Finance         | Payday lending, credit card issuers         |

If the company's core business is in a prohibited sector → **Automatically Non-Compliant**.

### Step 3: Quantitative Screening (Financial Ratios)

Apply three AAOIFI financial ratio tests:

| Ratio                   | Formula                                           | Threshold |
| ----------------------- | ------------------------------------------------- | --------- |
| **Debt Ratio**          | Interest-bearing debt ÷ Market cap                | < 30%     |
| **Cash Ratio**          | (Cash + interest-bearing securities) ÷ Market cap | < 30%     |
| **Impure Income Ratio** | Non-permissible income ÷ Total revenue            | < 5%      |

All three must pass for compliance.

Run the screening:

```bash
python scripts/screen_stock.py --ticker AAPL
python scripts/screen_stock.py --ticker AAPL MSFT TSLA --json
```

### Step 4: Purification Calculation

For compliant stocks with some impure income (< 5%), calculate the **purification amount** — the portion of dividends/gains that must be donated to charity:

```
Purification % = Non-permissible income / Total revenue
Purification Amount = Dividends received × Purification %
```

### Step 5: Present Results

For each stock, present:

1. **Company Name & Ticker**
2. **Qualitative Result** — Sector analysis (Pass/Fail)
3. **Quantitative Ratios** — Each ratio with actual value and threshold
4. **Overall Verdict** — Compliant / Non-Compliant / Needs Review
5. **Purification Ratio** — If applicable
6. **Notes** — Any caveats or areas requiring scholarly opinion

## Screening Methodologies

This skill uses **AAOIFI** by default. The user may also request:

- **DJIM (Dow Jones Islamic Market)** — Similar but uses total assets as denominator
- **S&P Sharia** — Slightly different thresholds
- **MSCI Islamic** — Uses total assets, 33.33% thresholds

Refer to `references/screening_criteria.md` for comparison across methodologies.

## Important Notes

- Financial data may be delayed or from the most recent quarterly/annual filing
- Screening results are **point-in-time** — companies can move in/out of compliance
- When data is unavailable, flag the stock as **"Needs Review"** rather than guessing
- Always recommend the user consult a Sharia advisory board for significant investment decisions
- Some sectors are partially permissible (e.g., airlines, hotels) — flag these for review

## Output Format

Default output is a formatted table/report. Use `--json` for JSON output. When screening multiple tickers, output a summary table with per-stock verdicts.
