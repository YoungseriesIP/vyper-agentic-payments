"""
C4. Atomic PaymentSplitter for Multi-Agent Workflows

A Vyper PaymentSplitter where recipients and shares in basis points are
set at deploy time, distribute() sends proportional shares atomically,
accrue()/claim() provides a pull variant, and share updates are timelocked.

The existing contracts/PaymentSplitter.vy provides a starting point with
pool creation, deposit, and claim. This challenge extends it with atomic
distribute(), timelocked share updates, and remainder handling.

Key functions per challenges.md spec:
  - distribute(amount)
  - accrue(amount)
  - claim()
  - propose_split_update(new_recipients, new_shares)

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "C4"
"""

import boa


def distribute(splitter, usdc, sender: str, amount: int):
    """
    Send each recipient their proportional share atomically in one transaction.
    One event per recipient per distribution with the exact amount sent.

    Args:
        splitter: Deployed PaymentSplitter contract instance.
        usdc: Deployed USDC token contract instance.
        sender: Address sending USDC to be distributed.
        amount: Total USDC amount to split (6 decimals).
    """
    # Implement: as sender, approve splitter then call distribute(amount)
    raise NotImplementedError("Distribute USDC proportionally to all recipients")


def accrue(splitter, usdc, sender: str, amount: int):
    """
    Increment each recipient's claimable balance without transferring.
    Recipients call claim() themselves to withdraw.

    Args:
        splitter: Deployed PaymentSplitter contract instance.
        usdc: Deployed USDC token contract instance.
        sender: Address depositing USDC.
        amount: Total USDC amount to accrue (6 decimals).
    """
    # Implement: as sender, approve splitter then call accrue(amount)
    raise NotImplementedError("Accrue USDC to recipient balances")


def claim(splitter, recipient: str):
    """
    Recipient withdraws their accrued claimable balance.

    Args:
        splitter: Deployed PaymentSplitter contract instance.
        recipient: Address claiming their share.
    """
    # Implement: as recipient, call claim() to withdraw accrued balance
    raise NotImplementedError("Claim accrued balance as recipient")


def propose_split_update(
    splitter,
    owner: str,
    new_recipients: list,
    new_shares: list,
):
    """
    Owner queues a share update behind a timelock. The change cannot apply
    mid-session — it takes effect after N blocks.

    Args:
        splitter: Deployed PaymentSplitter contract instance.
        owner: Address of the splitter owner.
        new_recipients: List of new recipient addresses.
        new_shares: List of new share amounts in basis points (must sum to 10000).
    """
    # Implement: as owner, propose a new split that takes effect after the timelock
    raise NotImplementedError("Propose a timelocked share update")
