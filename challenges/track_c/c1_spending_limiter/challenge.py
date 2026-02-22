"""
C1. SpendingLimiter

Enforce rolling 24-hour budgets, per-recipient caps, and an allowlist of
recipient addresses on every outgoing USDC transfer at the contract layer.

The existing contracts/SpendingLimiter.vy provides a starting point with
per-tx, daily, and total limits. This challenge extends it with per-recipient
caps, an allowlist, emergency_pause, and owner-cosigned resume.

Key functions per challenges.md spec:
  - authorize_spend(recipient, amount)
  - set_limit(agent, amount, window)
  - emergency_pause(agent)
  - resume(agent)

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "C1"
"""

import boa


def authorize_spend(limiter, agent: str, recipient: str, amount: int):
    """
    Agent requests an outgoing USDC transfer. The contract checks:
      1. Recipient is on the allowlist
      2. Amount is within per-recipient cap
      3. Amount fits within the rolling 24-hour budget
      4. Agent is not paused

    Args:
        limiter: Deployed SpendingLimiter contract instance.
        agent: Address of the authorized agent.
        recipient: Address to receive USDC.
        amount: USDC amount in raw units (6 decimals).
    """
    # Implement: as agent, call the spend function with recipient and amount checks
    raise NotImplementedError("Call the spending function with all three constraint checks")


def set_limit(limiter, owner: str, agent: str, amount: int, window: int):
    """
    Owner configures the rolling budget for an agent.

    Args:
        limiter: Deployed SpendingLimiter contract instance.
        owner: Address of the limiter owner.
        agent: Address of the agent to configure.
        amount: Maximum USDC spend within the window (6 decimals).
        window: Rolling window duration in seconds (e.g., 86400 for 24 hours).
    """
    # Implement: as owner, call the limit configuration function
    raise NotImplementedError("Configure the rolling budget for the agent")


def emergency_pause(limiter, owner: str, agent: str):
    """
    Owner halts all outgoing transfers for an agent immediately.

    Args:
        limiter: Deployed SpendingLimiter contract instance.
        owner: Address of the limiter owner.
        agent: Address of the agent to pause.
    """
    # Implement: as owner, pause the agent so authorize_spend reverts
    raise NotImplementedError("Pause all outgoing transfers for the agent")


def resume(limiter, owner: str, agent: str):
    """
    Owner co-signs to resume transfers after a pause or daily cap hit.
    The agent cannot unilaterally resume.

    Args:
        limiter: Deployed SpendingLimiter contract instance.
        owner: Address of the limiter owner.
        agent: Address of the agent to resume.
    """
    # Implement: as owner, resume the agent so authorize_spend works again
    raise NotImplementedError("Resume outgoing transfers for the agent")
