# Smart Contract Documentation

This directory contains detailed documentation for each smart contract.

## Contracts Overview

| Contract | Description | Key Features |
|----------|-------------|--------------|
| [AgentEscrow](./AgentEscrow.md) | Task payment escrow | Lock, complete, dispute |
| [SpendingLimiter](./SpendingLimiter.md) | Agent authorization | Limits, delegation |
| [PaymentSplitter](./PaymentSplitter.md) | Revenue distribution | Shares, withdrawals |
| [SubscriptionManager](./SubscriptionManager.md) | Recurring payments | Plans, billing cycles |

## Deployment Order

All contracts require a USDC address. They can be deployed in any order:

1. **AgentEscrow** - Requires USDC address + IdentityRegistry address
2. **SpendingLimiter** - Requires USDC address
3. **PaymentSplitter** - Requires USDC address
4. **SubscriptionManager** - Requires USDC address

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

## Error Messages

Contracts use descriptive revert messages:

| Pattern | Example |
|---------|---------|
| Contract prefix | `"AgentEscrow: not poster"` |
| State checks | `"AgentEscrow: task not active"` |
| Auth checks | `"SpendingLimiter: not authorized"` |
| Limit checks | `"SpendingLimiter: exceeds daily limit"` |

## Testing

Each contract has comprehensive tests:

```bash
# Run all tests for a contract
python -m pytest tests/test_agent_escrow.py -v

# Run all tests
python -m pytest tests/ -v
```
