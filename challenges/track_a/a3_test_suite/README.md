# A3. Write a Test Suite

Using Titanoboa or Moccasin's testing utilities, write a test suite for your A2 vault contract.

## What to Test

Your tests must cover:

1. **Successful deposit and withdrawal**: depositor deposits USDC, then withdraws the full balance. Vault balance returns to zero, depositor balance is restored.

2. **Withdrawal by a non-depositor reverts**: a different address attempts to withdraw from a depositor's balance. The transaction must revert.

3. **Correct balance accounting after multiple deposits**: the same depositor deposits twice. The vault tracks the cumulative balance correctly.

## What to Implement

Fill in `challenge.py` with three test functions:

- `test_deposit_and_withdraw(vault, usdc, depositor)`: happy path
- `test_non_depositor_reverts(vault, usdc, depositor, non_depositor)`: access control
- `test_multiple_deposits(vault, usdc, depositor)`: cumulative accounting

Each function receives pre-deployed contract instances and funded addresses. See the docstrings in `challenge.py` for the exact interface.

## Hints

- Use `boa.env.prank(address)` to set `msg.sender`
- Use `boa.reverts()` as a context manager to assert a transaction reverts
- The depositor must `approve` the vault before each deposit
- USDC uses 6 decimals (1 USDC = 1_000_000)

## Checkpoint

A passing test suite in your repo.
