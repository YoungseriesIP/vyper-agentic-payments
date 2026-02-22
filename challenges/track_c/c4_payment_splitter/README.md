# C4. Atomic PaymentSplitter for Multi-Agent Workflows

## What to Build

A Vyper PaymentSplitter where:

- Recipients and shares in basis points are set at deploy time (shares must sum to exactly 10000)
- `distribute(amount)` sends each recipient their proportional share atomically in one transaction
- A pull variant: `accrue(amount)` increments each recipient's claimable balance; recipients call `claim()` themselves — avoids the failure mode where one recipient is a contract that reverts on receive
- Owner can update shares behind a timelock: `propose_split_update(new_recipients, new_shares)` queues a change for N blocks; the change cannot apply mid-session
- One event per recipient per distribution with the exact amount sent

### Design Decision

Document explicitly where the remainder goes when `amount` does not divide evenly. Assign it to the first recipient or a treasury address. Either is fine. Ambiguity is not.

## What This Enables Beyond Vanilla x402

x402 sends payment to one address. Splitting that payment across multiple recipients — a platform fee, a provider, a referrer — requires either multiple transactions or an intermediary. This contract makes multi-party splits atomic and auditable in a single on-chain transaction.

## Product Directions

- Orchestrator agents that coordinate specialist sub-agents and distribute payment in proportion to contribution
- Royalty splits for AI-generated content across model provider, fine-tuner, and infrastructure
- Revenue sharing in multi-vendor agent marketplaces

## Why Vyper

Fixed-size arrays make the recipient list tamper-resistant at compile time. Dynamic arrays in Solidity allow a compromised owner to append recipients after deployment.

## What to Implement

Fill in `challenge.py` with functions that interact with `contracts/PaymentSplitter.vy`. See the docstrings for the exact interface.

## Hints

- Shares are in basis points: 5000 = 50%, 2500 = 25%, etc.
- Use `boa.env.prank(address)` to set `msg.sender`
- USDC uses 6 decimals (1 USDC = 1_000_000)
- Read `contracts/PaymentSplitter.vy` before coding
