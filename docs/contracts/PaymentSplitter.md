# PaymentSplitter.vy

Revenue distribution for multi-agent collaboration.

## Overview

This contract distributes USDC payments among multiple recipients based on shares. It enables automatic revenue splitting for agent collaborations.

## Features

- Create payment pools with defined share allocations
- Accept USDC deposits tracked per pool
- Recipients claim their share of accumulated payments
- Dynamic share updates by pool owner
- Pull-payment pattern for safe withdrawals

## Key Functions

### Pool Management

```vyper
@external
def createPool(recipients: DynArray[address, 100], shares: DynArray[uint256, 100]) -> uint256

@external
def updateShares(poolId: uint256, recipient: address, newShares: uint256)

@external
def addRecipient(poolId: uint256, recipient: address, shares: uint256)

@external
def removeRecipient(poolId: uint256, recipient: address)
```

### Payments

```vyper
@external
def deposit(poolId: uint256, amount: uint256)

@external
def claim(poolId: uint256)

@external
def claimableAmount(poolId: uint256, recipient: address) -> uint256
```

### Query Functions

```vyper
@view
def getPoolInfo(poolId: uint256) -> (address, uint256, uint256)

@view
def getShares(poolId: uint256, recipient: address) -> uint256

@view
def getTotalReceived(poolId: uint256) -> uint256
```

## Events

| Event | Description |
|-------|-------------|
| `PoolCreated` | New payment pool created |
| `SharesUpdated` | Recipient's shares changed |
| `PaymentReceived` | USDC deposited to pool |
| `PaymentClaimed` | Recipient withdrew funds |
| `RecipientAdded` | New recipient added |
| `RecipientRemoved` | Recipient removed |

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `MAX_RECIPIENTS` | 100 | Maximum recipients per pool |
| `MAX_SHARES` | 10000 | 100.00% in basis points |

## Usage Example

```python
import boa

splitter = boa.load("contracts/PaymentSplitter.vy", usdc_address)

# Create pool: Agent A gets 60%, Agent B gets 40%
recipients = [agent_a, agent_b]
shares = [6000, 4000]  # Basis points (60% + 40% = 100%)
pool_id = splitter.createPool(recipients, shares)

# Revenue comes in
usdc.approve(splitter.address, 100 * 10**6)
splitter.deposit(pool_id, 100 * 10**6)

# Agent A claims their share ($60)
with boa.env.prank(agent_a):
    splitter.claim(pool_id)  # Receives 60 USDC

# Agent B claims their share ($40)
with boa.env.prank(agent_b):
    splitter.claim(pool_id)  # Receives 40 USDC
```

## Multi-Agent Collaboration Use Case

When agents work together on a task:

1. Create a pool with all participating agents
2. Set shares based on contribution (e.g., orchestrator: 20%, workers: 80% split)
3. Client pays into the pool
4. Each agent claims their share independently

## Integration with x402

The pool address can be set as the `payTo` address in x402:

```typescript
const paywall = createPaywall({
  payTo: splitterPoolAddress,  // Revenue goes to pool
  amount: '100000'             // $0.10 per request
});
```

## Security Considerations

- Only pool owner can update shares
- Pull-payment pattern prevents reentrancy
- Shares must not exceed MAX_SHARES
- Recipients must be non-zero addresses
