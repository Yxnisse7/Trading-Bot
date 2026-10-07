---
name: zakat-calculator
description: Calculate Islamic zakat obligations on wealth. Supports cash, gold, silver, stocks, crypto, business inventory, and receivables. Uses live metal prices for nisab threshold and outputs detailed per-category breakdowns.
---

# Zakat Calculator

Calculate a user's annual zakat obligation based on Islamic jurisprudence (fiqh al-zakat).

## When to Use

- User asks to calculate zakat on their wealth or assets
- User wants to know if they meet the nisab threshold
- User needs a breakdown of zakatable vs non-zakatable assets
- User asks about zakat on specific asset types (crypto, stocks, gold, etc.)

## How It Works

### Step 1: Gather Asset Information

Ask the user for their assets across these categories:

| Category             | Examples                                       | Zakatable?     |
| -------------------- | ---------------------------------------------- | -------------- |
| Cash & Bank Balances | Savings, checking, cash on hand                | Yes            |
| Gold                 | Jewelry (investment), coins, bars              | Yes            |
| Silver               | Jewelry (investment), coins, bars              | Yes            |
| Stocks & Investments | Shares, mutual funds, ETFs                     | Yes (market value) |
| Cryptocurrency       | BTC, ETH, stablecoins, etc.                    | Yes (market value) |
| Business Inventory   | Trade goods held for sale                      | Yes (market value) |
| Receivables          | Money owed to the user (expected to be repaid) | Yes            |
| Rental Income        | Accumulated rental income                      | Yes            |
| Personal Residence   | Primary home                                   | No             |
| Personal Vehicle     | Daily-use car                                  | No             |
| Personal Items       | Clothing, electronics, furniture               | No             |

### Step 2: Gather Liabilities

Ask for deductions:

- Outstanding debts due within the year
- Immediate expenses / bills payable
- Loans owed to others

### Step 3: Determine Nisab

The nisab is the minimum wealth threshold. There are two standards:

- **Gold Nisab**: 87.48 grams of gold (≈ 3 oz)
- **Silver Nisab**: 612.36 grams of silver (≈ 21.5 oz)

Use the **silver nisab** by default (more conservative — benefits more recipients), but let the user choose gold if preferred.

Run the script to fetch live prices:

```bash
python scripts/calculate_zakat.py --nisab --currency USD
```

### Step 4: Calculate Zakat

If **net zakatable wealth ≥ nisab**, zakat is due at **2.5%** of total net zakatable wealth.

Run the full calculation:

```bash
python scripts/calculate_zakat.py \
  --cash 15000 \
  --gold-grams 50 \
  --silver-grams 0 \
  --stocks 25000 \
  --crypto 10000 \
  --business-inventory 0 \
  --receivables 5000 \
  --debts 8000 \
  --currency USD \
  --nisab-standard silver
```

### Step 5: Present Results

Present the output in a clear, formatted breakdown:

1. **Asset Summary** — Per-category values
2. **Total Zakatable Wealth** — Sum of all zakatable assets
3. **Deductions** — Total liabilities
4. **Net Zakatable Wealth** — After deductions
5. **Nisab Check** — Whether threshold is met
6. **Zakat Due** — 2.5% of net zakatable wealth (or $0 if below nisab)

## Important Notes

- Zakat is calculated on wealth held for **one full lunar year** (hawl)
- The 2.5% rate applies to most wealth types; agricultural produce and livestock have different rates (not covered here)
- Scholars differ on whether **personal-use gold jewelry** is zakatable — note this to the user
- For **stocks**, use the full market value of shares held for investment. For shares held for trading, include the full market value
- For **crypto**, use current market value at time of calculation
- Always remind the user that this is a **tool for estimation** and they should consult a qualified scholar for complex situations
- Reference `references/zakat_rules.md` for detailed scholarly opinions and edge cases

## Output Format

Always output the result as a structured breakdown. If the user wants JSON, use the script's `--json` flag. Otherwise, format as a readable table or list.
