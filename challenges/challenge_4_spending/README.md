# Challenge 4: Spending Limits (Hard)

Authorize an agent and execute a spend with 3-tier limits using `SpendingLimiter.vy`.

## Goal

Fill in `challenge.py` to:
1. Deposit USDC into the SpendingLimiter
2. Authorize an agent with per-transaction, daily, and total limits
3. Execute a spend as the authorized agent

## What You Need to Know

- `SpendingLimiter.vy` enforces three tiers of spending limits:
  - **Per-transaction limit**: Max amount per single spend
  - **Daily limit**: Max total spent in a rolling 24-hour window
  - **Total limit**: Max cumulative spend across all time
- Only the contract owner can deposit funds and authorize agents
- Authorized agents can call `spend()` up to their limits

## Key Functions

```python
# Owner deposits USDC into the limiter
usdc.approve(limiter.address, amount)
limiter.deposit(amount)

# Owner authorizes an agent with limits
limiter.authorizeAgent(
    agent_address,
    per_tx_limit,   # Max per transaction
    daily_limit,    # Max per 24h
    total_limit,    # Max cumulative
)

# Agent spends from owner's balance
limiter.spend(owner_address, spend_amount, recipient)

# Check remaining limits
remaining = limiter.getRemainingLimits(agent_address)
# Returns: (per_tx_remaining, daily_remaining, total_remaining)
```

## Hints

- The owner must `approve()` + `deposit()` USDC before agents can spend
- All amounts use USDC 6-decimal format (1 USDC = 1_000_000)
- `spend()` must be called by the authorized agent (use `boa.env.prank`)
- The spend amount must be ≤ all three limits simultaneously
- Check `tests/test_spending_limiter.py` for more examples
