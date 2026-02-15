# SpendingLimiter.vy

Agent authorization and delegation with configurable spending limits.

## Overview

This contract allows humans to set guardrails for AI agent spending. Agents can spend within defined limits without requiring approval for each transaction.

## Agentic Pattern

Solves the "How do I let my agent spend money safely?" problem:

- **Per-transaction limits** - Cap how much can be spent in one go
- **Daily limits** - Cap total spending per 24-hour period  
- **Total limits** - Cap lifetime spending

The owner (human) sets limits, and the agent operates within them autonomously.

## Integration with x402

While x402 handles off-chain payments, this contract provides on-chain guardrails:

1. Human deposits USDC to Gateway for their agent
2. Human configures SpendingLimiter with limits
3. Before spending, agent checks limits on-chain
4. If within limits, agent proceeds with x402 payment

## Key Functions

### Authorization

```vyper
@external
def authorizeAgent(agent: address, perTxLimit: uint256, dailyLimit: uint256, totalLimit: uint256)

@external
def revokeAgent(agent: address)

@external
def updateLimits(agent: address, perTxLimit: uint256, dailyLimit: uint256, totalLimit: uint256)
```

### Spending

```vyper
@external
def spend(amount: uint256, recipient: address)

@external
def deposit(amount: uint256)

@external
def withdraw(amount: uint256)
```

### Query Functions

```vyper
@view
def getAgentLimits(owner: address, agent: address) -> (uint256, uint256, uint256)

@view
def getRemainingDaily(owner: address, agent: address) -> uint256

@view
def getRemainingTotal(owner: address, agent: address) -> uint256

@view
def canSpend(owner: address, agent: address, amount: uint256) -> bool
```

## Events

| Event | Description |
|-------|-------------|
| `AgentAuthorized` | Agent granted spending rights |
| `AgentRevoked` | Agent's authorization removed |
| `LimitsUpdated` | Spending limits changed |
| `SpendingRecorded` | Agent spent funds |
| `FundsDeposited` | Owner deposited USDC |
| `FundsWithdrawn` | Owner withdrew USDC |

## Usage Example

```python
import boa

limiter = boa.load("contracts/SpendingLimiter.vy", usdc_address)

# Owner deposits USDC
usdc.approve(limiter.address, 1000 * 10**6)
limiter.deposit(1000 * 10**6)

# Authorize agent with limits
limiter.authorizeAgent(
    agent_address,
    10 * 10**6,    # $10 per transaction
    100 * 10**6,   # $100 per day
    500 * 10**6    # $500 total lifetime
)

# Agent spends (from agent's context)
with boa.env.prank(agent_address):
    limiter.spend(5 * 10**6, recipient_address)

# Check remaining
remaining_daily = limiter.getRemainingDaily(owner, agent_address)
```

## Daily Reset

Daily limits reset 24 hours after the first spend of the day. The contract tracks `lastDayStart` per owner-agent pair.

## Security Considerations

- Only owner can authorize/revoke agents
- Only authorized agents can spend from owner's balance
- Limits are enforced per-spend
- Owner can withdraw funds at any time
- Owner can revoke agent instantly
