# Smart Contract Documentation

This directory contains detailed documentation for each smart contract.

## Contracts Overview

| Contract | Description | Key Features |
|----------|-------------|--------------|
| [AgentIdentity](./AgentIdentity.md) | ERC-721 NFT registry for agents | Identity, ownership, metadata |
| [AgentReputation](./AgentReputation.md) | On-chain reputation system | Feedback, scores, tiers |
| [AgentValidation](./AgentValidation.md) | Third-party validation | Validators, task verification |
| [AgentEscrow](./AgentEscrow.md) | Task payment escrow | Lock, complete, dispute |
| [SpendingLimiter](./SpendingLimiter.md) | Agent authorization | Limits, delegation |
| [PaymentSplitter](./PaymentSplitter.md) | Revenue distribution | Shares, withdrawals |
| [SubscriptionManager](./SubscriptionManager.md) | Recurring payments | Plans, billing cycles |

## Contract Dependencies

```
AgentIdentity (standalone)
     │
     ├──────────────┬──────────────┐
     ▼              ▼              ▼
AgentReputation  AgentValidation  AgentEscrow
                                      │
                                      ▼
                               PaymentSplitter

SpendingLimiter (standalone)
SubscriptionManager (standalone)
```

## Deployment Order

When deploying, respect dependencies:

1. **AgentIdentity** - Deploy first (no dependencies)
2. **SpendingLimiter** - Deploy anytime (no dependencies)
3. **PaymentSplitter** - Deploy anytime (no dependencies)
4. **SubscriptionManager** - Deploy anytime (no dependencies)
5. **AgentReputation** - Deploy after AgentIdentity
6. **AgentValidation** - Deploy after AgentIdentity
7. **AgentEscrow** - Deploy after AgentIdentity, needs USDC address

## Common Patterns

### Admin Pattern

Most contracts use a simple admin pattern:

```python
admin: public(address)

@external
def __init__():
    self.admin = msg.sender

@internal
def _onlyAdmin():
    assert msg.sender == self.admin, "Not admin"

@external
def adminFunction():
    self._onlyAdmin()
    # Admin-only logic
```

### Reentrancy Guard

Contracts handling USDC use a reentrancy guard:

```python
reentrancy_lock: bool

@internal
def _lock():
    assert not self.reentrancy_lock, "Reentrant call"
    self.reentrancy_lock = True

@internal
def _unlock():
    self.reentrancy_lock = False

@external
def withdraw():
    self._lock()
    # Transfer tokens
    self._unlock()
```

### ERC-20 Interface

All contracts interacting with USDC use this interface:

```python
interface IERC20:
    def transfer(to: address, amount: uint256) -> bool: nonpayable
    def transferFrom(sender: address, recipient: address, amount: uint256) -> bool: nonpayable
    def approve(spender: address, amount: uint256) -> bool: nonpayable
    def balanceOf(account: address) -> uint256: view
    def allowance(owner: address, spender: address) -> uint256: view
```

## Events

All contracts emit events for key actions:

```python
# Example events from AgentIdentity
event AgentRegistered:
    agentId: indexed(uint256)
    owner: indexed(address)
    tokenURI: String[256]

event AgentUpdated:
    agentId: indexed(uint256)
    newTokenURI: String[256]

event AgentStatusChanged:
    agentId: indexed(uint256)
    active: bool
```

## Error Messages

Contracts use descriptive revert messages:

| Pattern | Example |
|---------|---------|
| Contract prefix | `"AgentIdentity: not owner"` |
| State checks | `"AgentEscrow: task not active"` |
| Auth checks | `"SpendingLimiter: not authorized"` |
| Limit checks | `"SpendingLimiter: exceeds daily limit"` |

## Testing

Each contract has comprehensive tests:

```bash
# Run all tests for a contract
python -m pytest tests/test_agent_identity.py -v

# Run specific test
python -m pytest tests/test_agent_identity.py::test_register_agent -v

# Run with coverage
python -m pytest tests/test_agent_identity.py --cov=contracts
```
