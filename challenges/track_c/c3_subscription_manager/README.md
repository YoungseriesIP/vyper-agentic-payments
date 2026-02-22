# C3. SubscriptionManager with On-Chain Cancellation

## What to Build

A Vyper subscription contract where:

- Subscriber calls `subscribe(provider, amount_per_period, period)` and pre-funds N intervals
- Anyone can call `settle(subscriber, provider)` once `block.timestamp >= last_settled + interval` — no trusted scheduler, no cron job, no keeper network required
- `cancel(provider)` returns `balance - pro_rata_owed` to the subscriber in the same transaction, calculated on-chain
- Provider can only `withdraw()` accrued settled intervals, never future ones
- `add_metered_charge(subscriber, units)` lets the provider bill usage above the flat rate at a per-unit price set at subscription creation

### Edge Cases to Handle and Document

- **Balance runs out mid-period:** `settle` reverts, emit `InsufficientBalance`
- **Subscriber tops up after a missed period:** no retroactive settlement, only forward from next valid window
- **Provider never calls `settle`:** subscriber can cancel and recover full remaining balance

## What This Enables Beyond Vanilla x402

x402 is per-call. There is no native concept of a recurring relationship, a billing period, or a refundable balance. This contract adds those: predictable revenue for providers, cancellation rights for subscribers, and metered billing for variable usage — all enforced on-chain.

## Product Directions

- SaaS-style billing for AI APIs where agents hold subscriptions rather than paying per call
- Agent-to-agent service agreements with defined billing periods
- Data feed subscriptions where agents pay for continuous access to a stream

## Why Vyper

`amount_per_period * n_periods` overflows in a subscription contract that runs for years without checked arithmetic. Vyper's overflow protection is on by default.

## What to Implement

Fill in `challenge.py` with functions that interact with `contracts/SubscriptionManager.vy`. See the docstrings for the exact interface.

## Hints

- Use `boa.env.prank(address)` to set `msg.sender`
- Use `boa.env.time_travel(seconds=...)` to advance `block.timestamp` for settlement tests
- USDC uses 6 decimals (1 USDC = 1_000_000)
- Read `contracts/SubscriptionManager.vy` before coding
