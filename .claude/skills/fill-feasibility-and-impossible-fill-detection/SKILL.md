---
name: fill-feasibility-and-impossible-fill-detection
description: 'Use this skill to audit whether every simulated fill in a backtest was actually physically possible given the real historical bar it traded on, checking fill size against real traded volume and fill price against real intrabar price action. Also use it when a backtest reports fills that seem suspiciously favorable, or whenever building a backtesting engine''s order-fill logic from scratch. This skill exists because a backtest can report a clean, error-free fill on every single trade while several of those fills were, in the real historical market, actually impossible to get, which inflates results in a way that''s invisible unless the fill logic is specifically audited against real bar-level constraints.'
---

# Fill Feasibility and Impossible Fill Detection

## Why this matters

A backtest's fill logic decides, for every simulated trade, what price and size it assumes was actually achievable. It's easy to write fill logic that's internally consistent and produces clean-looking results while quietly assuming fills that the real historical market never could have provided: filling a large order entirely at one price when the bar's actual traded volume was a fraction of that size, filling a stop order exactly at the stop price when the bar's actual path may never have offered a fill there, or filling inside a spread that didn't actually exist at that moment. None of this shows up as an error in the backtest; it shows up as a result that's better than what live trading, constrained by real liquidity and real price paths, could have actually delivered.

## Do this

### Check every simulated fill's size against the actual traded volume of the bar it filled on

A fill that assumes a larger size than the instrument's actual traded volume in that bar is not a fill that could have happened; audit every trade in a backtest against real historical volume data for its fill bar, and flag any fill whose size represents an implausibly large fraction of that bar's actual volume (informed by [transaction-cost-and-market-impact-modeling](../transaction-cost-and-market-impact-modeling/SKILL.md)'s market-impact reasoning: even a fill smaller than total volume can still be unrealistic if it assumes zero price impact at a size that would realistically move the market).

### Check every stop or limit fill against the bar's actual intrabar high/low/open/close, not just against whether the close crossed the level

A naive backtest fill rule ("if the close is beyond the stop price, fill at the stop price") ignores the fact that the bar's actual path may or may not have touched that exact price, and even when the high/low did cross the stop level, the fill price achieved in reality reflects the actual path and available liquidity at that moment, not a clean, guaranteed fill at the exact stop price with zero slippage. Verify that stop and limit fill logic checks the bar's actual high/low range for whether the order level was reached at all, and applies a realistic assumption (informed by [transaction-cost-and-market-impact-modeling](../transaction-cost-and-market-impact-modeling/SKILL.md)) about the price actually achieved relative to the stop/limit level, not an idealized fill exactly at that level.

### Flag fills on bars with zero or near-zero volume, gaps, or halts as requiring special scrutiny

A bar with zero or unusually low volume, a large price gap, or a trading halt is exactly the situation where a naive fill assumption is most likely to be unrealistic; a backtest that fills orders normally through these bars without flagging them for review is likely assuming liquidity that wasn't actually there. Explicitly detect these conditions (consistent with the gap-handling discipline in [data-cleaning-and-preprocessing-pitfalls](../data-cleaning-and-preprocessing-pitfalls/SKILL.md)) and either model them with an appropriately worse fill assumption or flag them for manual review rather than filling through them silently.

### Verify fill prices are consistent with the bid-ask spread and quote data where available, not just the trade price series

Where quote-level (bid/ask) or Level 1/2 data is available, verify simulated fills respect it: a buy order shouldn't fill at or inside the historical bid, and a sell order shouldn't fill at or inside the historical ask, since real fills cross the spread. A backtest using only trade-price OHLC data without any quote data available can't check this directly, which is itself a limitation worth being explicit about (see [order-book-and-intrabar-price-path-modeling](../order-book-and-intrabar-price-path-modeling/SKILL.md) for what finer-grained data can add here), rather than silently assuming fills at prices that ignore spread entirely.

### Build automated fill-feasibility checks into the backtesting pipeline, not just a one-time manual review

Consistent with [lookahead-bias-detection-methodology](../lookahead-bias-detection-methodology/SKILL.md)'s emphasis on automated, repeatable tests, build the volume-feasibility, intrabar-range, and low-liquidity-bar checks as automated assertions that run on every backtest, flagging any trade that violates them, rather than manually eyeballing a sample of trades once and assuming the rest are fine.

## Never do this

- Never trust a fill's price and size without checking it against the actual historical bar's real traded volume and intrabar high/low range.
- Never assume a stop or limit order fills exactly at its trigger price with zero slippage just because the bar's close crossed that level; check the actual intrabar path.
- Never fill orders through zero-volume, gapped, or halted bars using the same assumptions as normal liquid bars without explicit, separate handling.
- Never ignore available bid-ask/quote data when checking fill feasibility; a fill that crosses inside the historical spread in the wrong direction wasn't actually achievable.
- Never treat fill-feasibility checking as a one-time manual review; automate it to run on every backtest.

## Verification checklist

- [ ] Every simulated fill's size has been checked against the actual historical traded volume of its fill bar, with implausibly large fills flagged
- [ ] Stop and limit fill logic checks the bar's actual intrabar high/low range for whether the order level was genuinely reached, not just whether the close crossed it
- [ ] Zero-volume, gapped, and halted bars are explicitly detected and given separate, more conservative fill handling rather than filled through normally
- [ ] Fill prices are verified against available bid-ask/quote data where it exists, checking that fills don't cross the spread in an unrealistic direction
- [ ] Fill-feasibility checks are automated to run on every backtest, not performed as a one-time manual spot check
