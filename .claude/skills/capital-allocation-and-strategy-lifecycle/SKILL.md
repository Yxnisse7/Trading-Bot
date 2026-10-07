---
name: capital-allocation-and-strategy-lifecycle
description: 'Use this skill when deciding how much capital a new strategy should start with, when to increase or decrease that allocation based on live results, and when to retire a strategy entirely. Also use it when a user asks "how much should I allocate to this" or has a strategy that''s been quietly underperforming for a while without a clear decision about whether to keep running it. This skill exists because a strategy''s capital allocation is a decision that needs to keep being revisited as real evidence accumulates, not a one-time decision made at launch and left alone regardless of how the strategy actually performs.'
---

# Capital Allocation and Strategy Lifecycle

## Why this matters

A strategy that passed every validation step in this repo still starts live trading with genuine remaining uncertainty about how well it will actually perform, and that uncertainty should be reflected directly in how much capital it starts with and how that allocation changes as real evidence accumulates. Treating capital allocation as a single decision made at launch, rather than an evolving process informed by the live track record, means either overcommitting to a strategy before it's earned that confidence, or leaving a genuinely working strategy under-allocated indefinitely because nobody revisited the original decision.

## Do this

### Start new strategies at a reduced allocation relative to what full conviction would eventually justify

A strategy moving from a successful forward test ([paper-trading-and-forward-test-protocol](../paper-trading-and-forward-test-protocol/SKILL.md)) into live capital still has less real-world evidence behind it than one with a longer live track record, and should start with a smaller allocation than its eventual target, specifically to limit the cost of being wrong about a strategy that looked good in validation but doesn't hold up with real capital behind it.

### Define explicit, predetermined criteria for scaling allocation up as live evidence accumulates

Decide in advance what live track record (a minimum number of trades, a minimum duration, performance statistically consistent with the resampled backtest distribution per [live-vs-backtest-drift-monitoring](../live-vs-backtest-drift-monitoring/SKILL.md)) justifies increasing a strategy's allocation toward its eventual target, and follow that predetermined process rather than scaling up based on a recent hot streak or scaling up impatiently before enough real evidence has accumulated.

### Define explicit, predetermined criteria for reducing allocation or retiring a strategy, separate from just "it lost money"

A strategy losing money over some period isn't automatically a reason to kill it, since a real edge can have losing stretches consistent with its own resampled distribution; but a strategy showing statistically significant drift from its expected distribution, or whose original hypothesis has a clear, specific reason to no longer hold (a structural market change that removes the mechanism the strategy was designed around), is a different and more serious situation. Define in advance what specific evidence justifies reducing or retiring a strategy, tied to the statistical monitoring framework, not a vague, after-the-fact gut call made while frustrated about a losing stretch.

### Revisit allocation decisions on a regular schedule, not only when something looks obviously wrong

Set a periodic review cadence (quarterly, for instance) where every live strategy's allocation is explicitly reconsidered against its accumulated track record, rather than only revisiting allocation when a strategy's performance has already become alarming enough to force the question. A strategy that's quietly been performing well above expectations deserves a deliberate decision about whether to scale it up, just as much as an underperforming one deserves a deliberate decision about scaling down.

### Treat a retired strategy's process and data as a resource, not a closed chapter

When a strategy is retired, document why (specifically, tied to the evidence that justified the decision) and preserve its code, logs, and performance history rather than discarding them. A retired strategy's full history is useful both for understanding what kinds of edges tend to decay and how, and as a reference if market conditions later shift back toward something the strategy was designed for.

## Never do this

- Never allocate a new strategy at full target size immediately upon moving from forward test to live capital; start reduced and scale up based on accumulating live evidence.
- Never scale a strategy's allocation up based on a recent hot streak without checking it against predetermined criteria tied to a meaningful track record.
- Never treat a losing stretch alone as automatic grounds for retiring a strategy without checking whether that stretch is statistically consistent with its own resampled expected distribution.
- Never leave a strategy's allocation unreviewed indefinitely; set and follow a periodic review cadence for every live strategy, not just the ones that look obviously troubled.
- Never discard a retired strategy's code, logs, and performance history; preserve them as a documented reference.

## Verification checklist

- [ ] New strategies start at a reduced allocation relative to their eventual target, not full size immediately upon going live
- [ ] Explicit, predetermined criteria exist for scaling a strategy's allocation up as live evidence accumulates, and scaling decisions follow those criteria rather than a recent hot streak
- [ ] Explicit, predetermined criteria exist for reducing or retiring a strategy, tied to statistical drift monitoring rather than a losing stretch alone
- [ ] Every live strategy's allocation is revisited on a regular, predetermined review cadence, not only when performance looks alarming
- [ ] Retired strategies' code, logs, and performance history are documented and preserved, not discarded
