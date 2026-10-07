---
name: transaction-cost-and-market-impact-modeling
description: 'Use this skill whenever a backtest models commissions, slippage, or spread, and especially whenever those costs are modeled as a flat, simplistic assumption rather than tied to the actual instrument and venue being traded. Also use it whenever a user asks "how much does slippage matter" or reports a strategy''s edge disappearing once costs are accounted for more realistically. This skill exists because unrealistic cost assumptions are one of the most common, and most avoidable, reasons a backtest looks profitable while a live version of the same strategy is not.'
---

# Transaction Cost and Market Impact Modeling

## Why this matters

A strategy's edge has to be large enough to survive the real cost of implementing it: commissions, the bid-ask spread, slippage from the time a decision is made to the time it's actually filled, and market impact from the strategy's own trading moving the price against itself. A backtest that models these costs as a token flat assumption, or skips them almost entirely, is measuring a strategy that doesn't exist; the version that trades in the real world pays real costs on every single trade, and those costs compound over a strategy's full trading history in a way a token assumption doesn't capture.

## Do this

### Model costs specific to the actual instrument, venue, and order type being used, not a generic flat assumption

Spread and slippage assumptions that are realistic for a highly liquid futures contract are wildly unrealistic for a thin small-cap stock or an illiquid altcoin, and a market order's realistic cost is different from a limit order's. Build cost assumptions from the actual, specific instrument and order type the strategy uses, ideally informed by real historical spread and volume data for that instrument, rather than applying one flat cost assumption across every instrument and situation a strategy might trade.

### Model market impact as a function of order size relative to available liquidity, not as a constant

Larger orders move the price against the trader more than smaller ones, and that relationship is a function of the order's size relative to the instrument's actual liquidity (average daily volume, order book depth), not a fixed cost per trade. A strategy that backtests fine at a small notional size can have its edge substantially eroded at a larger size purely from market impact, and that size-dependence needs to be modeled explicitly, especially before scaling a strategy up in capital.

### Stress-test cost assumptions at 1.5x, 2x, and 3x the base assumption, and treat 2x survival as the real bar

Even a reasonably realistic cost assumption has uncertainty in it, and costs in live trading tend to be worse than backtest assumptions, not better, especially during the exact volatile or illiquid conditions when a strategy might most need to trade. Explicitly re-run the backtest with costs increased to 1.5x, 2x, and 3x the base assumption. A strategy whose profitability survives to 2x costs has a real margin of safety; a strategy that only survives at the exact base assumption and disappears at 1.5x was living on a razor's edge that live trading conditions are likely to cross.

### Model the actual time lag between signal generation and fill, not an instantaneous fill at the signal price

A backtest that assumes a trade fills instantly at the exact price that generated the signal (the same bar's close, for instance) is assuming away a real source of cost: the time between deciding to trade and actually getting filled, during which the price can move. Model a realistic delay (even a single bar's lag for a slower strategy, or an explicit latency assumption for a faster one) and the resulting price difference, rather than assuming perfect, instantaneous execution at the signal price.

### Account for financing costs, borrow costs, and funding rates where they apply

Leveraged positions, short positions, and perpetual futures/crypto positions all carry ongoing costs beyond the initial trade: margin interest, stock borrow fees for shorts, and funding rate payments for perpetual futures, all of which accumulate over a position's holding period and can matter enormously for longer-held or leveraged strategies. These are a real, ongoing cost of the strategy's actual implementation and need to be modeled explicitly rather than treated as a rounding error.

## Never do this

- Never model transaction costs as a single flat assumption applied uniformly across every instrument, venue, and order type a strategy trades.
- Never model market impact as a fixed per-trade cost independent of order size relative to the instrument's actual liquidity.
- Never skip stress-testing cost assumptions upward (at minimum 1.5x, 2x, and 3x); a strategy that hasn't been checked at higher cost levels has an unknown, not a known, margin of safety.
- Never assume instantaneous, perfect fills at the exact signal price; model a realistic lag and its price impact.
- Never omit financing, borrow, or funding costs for leveraged, short, or perpetual-futures/crypto positions, especially for strategies with longer holding periods.

## Verification checklist

- [ ] Transaction costs are modeled specific to the actual instrument, venue, and order type, not as one generic flat assumption
- [ ] Market impact is modeled as a function of order size relative to the instrument's actual liquidity, not a fixed cost per trade
- [ ] The backtest has been stress-tested at 1.5x, 2x, and 3x the base cost assumption, and profitability at 2x is treated as the real bar for a margin of safety
- [ ] A realistic lag between signal generation and fill is modeled, with its resulting price impact, rather than assuming instantaneous execution at the signal price
- [ ] Financing, borrow, or funding costs are modeled explicitly for any leveraged, short, or perpetual-futures/crypto position
