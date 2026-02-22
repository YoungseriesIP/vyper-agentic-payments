# A2. Deploy Your First Vyper Contract

Write and deploy a minimal Vyper contract to Arc testnet.

## Spec

The contract (`contracts/Vault.vy`) should:

- Accept a USDC deposit from a caller
- Store the depositor's address and amount
- Allow only the depositor to withdraw their balance

## Key Functions

```python
import boa

# Deploy the vault with a USDC token address
vault = boa.load("contracts/Vault.vy", usdc.address)

# Deposit: caller approves vault, then deposits
usdc.approve(vault.address, amount)
vault.deposit(amount)

# Withdraw: only the original depositor can withdraw
vault.withdraw(amount)

# Check balance
vault.balances(depositor_address)  # returns uint256
```

## What to Implement

Fill in `challenge.py`:

1. `deploy_vault(usdc_address)` — deploy the Vault contract and return the instance
2. `deposit(vault, usdc, depositor, amount)` — approve and deposit USDC into the vault
3. `withdraw(vault, depositor, amount)` — withdraw USDC from the vault

## Hints

- Use `boa.env.prank(address)` to set `msg.sender`
- The depositor must call `usdc.approve(vault.address, amount)` before depositing
- USDC uses 6 decimals on the ERC-20 interface (1 USDC = 1_000_000)
- Read `contracts/Vault.vy` before coding

## Checkpoint

A deployed contract address on Arc. A deposit and withdrawal transaction visible on the block explorer.
