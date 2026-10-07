---
name: futures-roll-and-contract-mechanics
description: 'Use this skill when building, backtesting, or reviewing any futures strategy, in addition to the general checks elsewhere in this repo and the continuous-contract notes in market-data-sourcing. Also use it when a user''s futures backtest behaves strangely around specific dates, which is a common symptom of roll mechanics being modeled incorrectly. This skill exists because trading through a contract roll is a genuinely distinct mechanical event a futures strategy has to actually handle, not just a data-adjustment detail to get right once when building the historical series.'
---

# Futures Roll and Contract Mechanics

## Why this matters

[market-data-sourcing](../market-data-sourcing/SKILL.md) covers how a continuous futures contract series gets built for backtesting purposes; this skill covers the fact that a live futures strategy actually has to execute a real roll (closing a position in an expiring contract and opening one in the next), which is a genuine trading event with its own costs, timing decisions, and risks, not just a data-construction detail that disappears once the historical series exists.

## Do this

### Model the actual mechanics and cost of executing a roll, not just the price-series adjustment used for backtesting

A live roll involves actually trading two contracts (closing the expiring one, opening the next), which incurs real transaction costs, real timing risk (the roll doesn't happen instantaneously at a single price), and a real decision about when relative to expiry to execute it. A backtest that only handles the roll via a price-series adjustment method (back-adjusted, ratio-adjusted, as covered in [market-data-sourcing](../market-data-sourcing/SKILL.md)) without separately modeling the actual cost and execution risk of the roll trade itself is understating a real, recurring cost that [transaction-cost-and-market-impact-modeling](../transaction-cost-and-market-impact-modeling/SKILL.md) applies to every trade, including roll trades specifically.

### Understand and account for contango/backwardation effects on a held futures position's roll yield

A futures curve in contango (further-dated contracts priced higher than near-dated ones) or backwardation (the reverse) creates a real, systematic roll yield effect for a position held continuously through rolls: a long position in a contangoed market tends to lose value on each roll (selling a cheaper near contract, buying a pricier far one) independent of the underlying spot price's direction, and the reverse in backwardation. This roll yield is a real, structural component of a continuously-held futures position's return that needs to be explicitly understood and modeled, not conflated with or hidden inside the strategy's apparent price-based edge.

### Decide roll timing deliberately, and understand the liquidity and price-impact tradeoffs involved

Rolling too close to expiry risks reduced liquidity and wider spreads in the expiring contract as open interest migrates to the next contract; rolling too early gives up basis that might have been captured by holding the expiring contract longer. Decide the actual roll timing rule deliberately, informed by the specific contract's typical liquidity migration pattern, rather than defaulting to an arbitrary fixed number of days before expiry without checking whether that's actually a good time to roll for the specific instrument.

### Check margin and expiry mechanics specific to the actual contract being traded, including delivery risk for physically-settled contracts

Futures contracts vary in margin requirements, expiry timing, and settlement mechanism (cash-settled versus physically-settled), and a strategy needs to explicitly account for these, especially the real risk of accidentally holding a physically-settled contract through expiry and being assigned physical delivery obligations, which is a real, costly, and avoidable failure mode if roll timing and expiry awareness aren't handled deliberately.

### Verify backtested roll assumptions against actual historical roll behavior for the specific contract, not a generic assumption

Different futures contracts (equity index futures, agricultural commodities, energy products) have different typical liquidity migration patterns and roll conventions; a generic "roll five days before expiry" assumption that works fine for one contract type may be poorly suited to another. Check the actual historical volume/open-interest migration pattern for the specific contract being traded before finalizing a roll timing assumption, rather than applying a one-size-fits-all rule across different futures products.

## Never do this

- Never model a futures roll only via the price-series adjustment method used for historical backtesting without separately accounting for the real transaction cost and execution risk of actually trading the roll live.
- Never conflate a continuously-held futures position's contango/backwardation-driven roll yield with the strategy's apparent price-based edge; understand and model roll yield as its own distinct component.
- Never default to an arbitrary, unexamined fixed roll-timing rule without checking the actual liquidity migration pattern for the specific contract being traded.
- Never leave delivery-risk exposure unmanaged for a physically-settled contract; explicitly track expiry and roll timing to avoid accidental physical delivery assignment.
- Never apply the same roll-timing assumption across genuinely different futures products without verifying it against each specific contract's actual historical roll behavior.

## Verification checklist

- [ ] The real transaction cost and execution risk of actually trading a roll are modeled explicitly, separate from the price-series adjustment method used for backtesting
- [ ] Contango/backwardation-driven roll yield is understood and modeled as a distinct component of a continuously-held position's return, not conflated with the strategy's price-based edge
- [ ] Roll timing is a deliberate decision informed by the specific contract's actual liquidity migration pattern, not an arbitrary unexamined fixed rule
- [ ] Margin and expiry/settlement mechanics for the specific contract are understood, with explicit handling to avoid accidental physical delivery assignment on physically-settled contracts
- [ ] Roll timing assumptions have been checked against actual historical roll/liquidity-migration behavior for the specific contract, not applied generically across different futures products
