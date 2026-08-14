"""
A3. Write a Test Suite

Write tests for the Vault contract from A2.

Instructions:
  1. Test successful deposit and withdrawal
  2. Test that a non-depositor cannot withdraw
  3. Test correct balance accounting after multiple deposits

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "A3"
"""

import boa


def test_deposit_and_withdraw(vault, usdc, depositor: str):
    """
    Test the happy path: deposit USDC, then withdraw the full balance.

    After withdrawal the vault balance for the depositor should be zero
    and the depositor's USDC balance should be restored.

    Args:
        vault: Deployed Vault contract instance.
        usdc: Deployed USDC token contract instance (depositor already funded).
        depositor: Funded address to deposit and withdraw.
    """
    # Implement: deposit some USDC, withdraw it all, assert balances are correct
    amount = 100 * 10**6
    initial_balance = usdc.balanceOf(depositor)
    with boa.env.prank(depositor):
        usdc.approve(vault.address, amount)
        vault.deposit(amount)
    assert vault.balances(depositor) == amount
    with boa.env.prank(depositor):
        vault.withdraw(amount)
    assert vault.balances(depositor) == 0
    assert usdc.balanceOf(depositor) == initial_balance


def test_non_depositor_reverts(vault, usdc, depositor: str, non_depositor: str):
    """
    Test that a non-depositor cannot withdraw another user's funds.

    Deposit USDC as depositor, then attempt to withdraw as non_depositor.
    The withdrawal must revert.

    Args:
        vault: Deployed Vault contract instance.
        usdc: Deployed USDC token contract instance (depositor already funded).
        depositor: Address that deposits USDC.
        non_depositor: Address that attempts an unauthorized withdrawal.
    """
    # Implement: deposit as depositor, then use boa.reverts() to assert
    # that non_depositor cannot withdraw
    amount = 100 * 10**6
    with boa.env.prank(depositor):
        usdc.approve(vault.address, amount)
        vault.deposit(amount)
    with boa.env.prank(non_depositor):
        with boa.reverts():
            vault.withdraw(amount)


def test_multiple_deposits(vault, usdc, depositor: str):
    """
    Test that the vault correctly accumulates multiple deposits.

    Deposit USDC twice as the same depositor. The vault balance should
    equal the sum of both deposits.

    Args:
        vault: Deployed Vault contract instance.
        usdc: Deployed USDC token contract instance (depositor already funded).
        depositor: Address making both deposits.
    """
    # Implement: deposit twice, assert vault.balances(depositor) equals the sum
    amount = 100 * 10**6
    with boa.env.prank(depositor):
        usdc.approve(vault.address, amount)
        vault.deposit(amount)
        usdc.approve(vault.address, amount)
        vault.deposit(amount)
    assert vault.balances(depositor) == amount * 2
