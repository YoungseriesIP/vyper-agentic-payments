# C1. SpendingLimiter

## What to Build

A Vyper contract that sits between an agent wallet and its USDC. It enforces:

- A rolling 24-hour budget
- A per-recipient cap
- An allowlist of recipient addresses

All three on every outgoing transfer, at the contract layer. If the daily cap is hit, outgoing transfers halt until the owner co-signs a resumption — the agent cannot unilaterally resume.

### Key Functions

- `authorize_spend(recipient, amount)` — agent requests a transfer; contract checks all three constraints
- `set_limit(agent, amount, window)` — owner configures the rolling budget for an agent
- `emergency_pause(agent)` — owner halts all outgoing transfers for an agent immediately
- `resume(agent)` — owner co-signs to resume transfers after a pause or cap hit

### Design Decision

What happens when an agent is at 49.9 USDC of a 50 USDC daily cap and tries to transfer 1.5 USDC? Full revert, or partial fill? Either is defensible. Document your choice in your README.

## What This Enables Beyond Vanilla x402

x402 enforces payment at the protocol layer but has no opinion on how much an agent is allowed to spend. That enforcement lives in application code today — a runtime setting, an SDK config, a server-side check. A SpendingLimiter moves that constraint on-chain, independent of whatever the agent code does or whatever state the runtime is in.

## Product Directions

- Corporate expense controls for autonomous agents with per-department budgets
- Consumer agent products where a user sets weekly spending limits
- Treasury management for multi-agent systems where individual agents draw from a shared pool with hard caps

## What to Implement

Fill in `challenge.py` with functions that interact with `contracts/SpendingLimiter.vy`. See the docstrings for the exact interface.

## Hints

- Use `boa.env.prank(address)` to set `msg.sender`
- USDC uses 6 decimals (1 USDC = 1_000_000)
- Read `contracts/SpendingLimiter.vy` before coding
