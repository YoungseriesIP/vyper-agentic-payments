"""
Challenge 4: Spending Limits (Hard)

Authorize an agent and execute a spend with 3-tier limits.

Instructions:
  1. Deposit USDC into the SpendingLimiter (as owner)
  2. Authorize an agent with per-tx, daily, and total limits (as owner)
  3. Execute a spend (as the authorized agent)

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "challenge_4"
"""

import boa


def setup_and_spend(
    limiter,
    usdc,
    owner: str,
    agent: str,
    deposit_amount: int,
    per_tx_limit: int,
    daily_limit: int,
    total_limit: int,
    spend_amount: int,
    recipient: str,
) -> None:
    """
    Set up spending limits and execute a spend.

    Args:
        limiter: Deployed SpendingLimiter contract instance
        usdc: Deployed mock USDC contract instance
        owner: Address of the limiter owner (deployer)
        agent: Address of the agent being authorized
        deposit_amount: USDC to deposit into the limiter
        per_tx_limit: Max USDC per single transaction
        daily_limit: Max USDC per 24-hour period
        total_limit: Max cumulative USDC spend
        spend_amount: Amount to spend in this call
        recipient: Address receiving the spent USDC
    """
    # TODO: Step 1 — As owner, approve limiter to spend deposit_amount USDC
    #       usdc.approve(limiter.address, deposit_amount)

    # TODO: Step 2 — As owner, deposit USDC into the limiter
    #       limiter.deposit(deposit_amount)

    # TODO: Step 3 — As owner, authorize the agent with 3-tier limits
    #       limiter.authorizeAgent(agent, per_tx_limit, daily_limit, total_limit)

    # TODO: Step 4 — As agent, execute the spend
    #       limiter.spend(owner, spend_amount, recipient)

    raise NotImplementedError("Complete this challenge!")
