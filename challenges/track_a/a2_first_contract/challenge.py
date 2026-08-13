"""
A2. Deploy Your First Vyper Contract

Deploy a USDC vault, deposit funds, and withdraw them.

Instructions:
  1. Deploy contracts/Vault.vy with the USDC token address
  2. Approve the vault and deposit USDC as the depositor
  3. Withdraw USDC as the depositor

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "A2"
"""

import boa


def deploy_vault(usdc_address: str):
    """
    Deploy the Vault contract.

    Args:
        usdc_address: Address of the USDC token contract.

    Returns:
        The deployed Vault contract instance.
    """
    # Implement: deploy contracts/Vault.vy with usdc_address as constructor arg
    return boa.load("contracts/Vault.vy", usdc_address)


def deposit(vault, usdc, depositor: str, amount: int):
    """
    Deposit USDC into the vault.

    Args:
        vault: Deployed Vault contract instance.
        usdc: Deployed USDC token contract instance.
        depositor: Address making the deposit.
        amount: USDC amount in raw units (6 decimals).
    """
    # Implement: as depositor, approve vault then call vault.deposit(amount)
    with boa.env.prank(depositor): usdc.approve(vault.address, amount); vault.deposit(amount)


def withdraw(vault, depositor: str, amount: int):
    """
    Withdraw USDC from the vault.

    Args:
        vault: Deployed Vault contract instance.
        depositor: Address making the withdrawal.
        amount: USDC amount in raw units (6 decimals).
    """
    # Implement: as depositor, call vault.withdraw(amount)
    with boa.env.prank(depositor): vault.withdraw(amount)
