"""
C5. Payment Channel with Challenge Period

A Vyper bidirectional payment channel that collapses an entire agent session
into two on-chain transactions (open and close), with off-chain signed balance
updates in between.

NOTE: contracts/PaymentChannel.vy does not exist yet. This challenge is
spec-only. Implement the contract first, then fill in these functions.

Key functions per challenges.md spec:
  - open_channel(payee, expiry)
  - cooperative_close(channel_id, amount, payer_sig, payee_sig)
  - unilateral_close(channel_id, amount, sig)
  - challenge(channel_id, higher_amount, higher_sig)
  - finalize(channel_id)
  - reclaim(channel_id)

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "C5"
"""

import boa


def open_channel(channel, usdc, payer: str, payee: str, deposit: int, expiry: int) -> int:
    """
    Payer opens a channel by depositing USDC and setting an expiry block.

    Args:
        channel: Deployed PaymentChannel contract instance.
        usdc: Deployed USDC token contract instance.
        payer: Address opening and funding the channel.
        payee: Address of the counterparty.
        deposit: USDC amount to lock in the channel (6 decimals).
        expiry: Block number after which payer can reclaim if no activity.

    Returns:
        channel_id: The ID of the opened channel.
    """
    # Implement: as payer, approve channel contract then open with payee and expiry
    raise NotImplementedError("Open a payment channel with USDC deposit")


def cooperative_close(
    channel,
    channel_id: int,
    amount: int,
    payer_sig: bytes,
    payee_sig: bytes,
):
    """
    Both parties sign the final state. Channel closes immediately and
    funds split per the final amount.

    Args:
        channel: Deployed PaymentChannel contract instance.
        channel_id: The channel ID.
        amount: Final amount owed to payee.
        payer_sig: Payer's signature over the final state.
        payee_sig: Payee's signature over the final state.
    """
    # Implement: submit both signatures to close the channel immediately
    raise NotImplementedError("Close the channel cooperatively with both signatures")


def unilateral_close(channel, closer: str, channel_id: int, amount: int, sig: bytes):
    """
    One party submits the latest signed state. A challenge period begins.

    Args:
        channel: Deployed PaymentChannel contract instance.
        closer: Address initiating the unilateral close.
        channel_id: The channel ID.
        amount: Amount from the latest signed state.
        sig: Signature from the counterparty over this state.
    """
    # Implement: as closer, submit the latest signed state to begin challenge period
    raise NotImplementedError("Initiate unilateral close with the latest signed state")


def challenge(channel, challenger: str, channel_id: int, higher_amount: int, higher_sig: bytes):
    """
    Counterparty submits a higher-nonce state to override during the
    challenge window. higher_amount must be strictly greater than the
    contested amount.

    Args:
        channel: Deployed PaymentChannel contract instance.
        challenger: Address submitting the challenge.
        channel_id: The channel ID.
        higher_amount: Amount from a higher-nonce state.
        higher_sig: Signature over the higher-nonce state.
    """
    # Implement: as challenger, submit a higher-nonce state during the challenge window
    raise NotImplementedError("Challenge with a higher-nonce signed state")


def finalize(channel, channel_id: int):
    """
    Finalize the channel after the challenge period expires with no valid
    challenge. Splits funds per the last accepted state.

    Cannot succeed before the challenge window closes.

    Args:
        channel: Deployed PaymentChannel contract instance.
        channel_id: The channel ID.
    """
    # Implement: call finalize after the challenge period has elapsed
    raise NotImplementedError("Finalize the channel after the challenge window")


def reclaim(channel, payer: str, channel_id: int):
    """
    Payer reclaims all funds if the channel expires with no activity from payee.

    Cannot succeed before the expiry block.

    Args:
        channel: Deployed PaymentChannel contract instance.
        payer: Address of the channel payer.
        channel_id: The channel ID.
    """
    # Implement: as payer, reclaim funds after channel expiry
    raise NotImplementedError("Reclaim all funds after channel expiry")
