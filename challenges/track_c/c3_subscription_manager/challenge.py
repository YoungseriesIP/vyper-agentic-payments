"""
C3. SubscriptionManager with On-Chain Cancellation

A Vyper subscription contract where subscribers pre-fund N intervals,
anyone can settle once the period elapses, cancellation returns pro-rata
balance, and providers can add metered charges.

The existing contracts/SubscriptionManager.vy provides a starting point
with plan creation, subscribe, charge, and cancel. This challenge extends
it with pro-rata cancellation refunds, metered billing, and the edge cases
documented in challenges.md.

Key functions per challenges.md spec:
  - subscribe(provider, amount_per_period, period)
  - settle(subscriber, provider)
  - cancel(provider)
  - withdraw()
  - add_metered_charge(subscriber, units)

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "C3"
"""

import boa


def subscribe(
    manager,
    usdc,
    subscriber: str,
    provider: str,
    amount_per_period: int,
    period: int,
    num_periods: int,
):
    """
    Subscriber creates a subscription and pre-funds N intervals.

    Args:
        manager: Deployed SubscriptionManager contract instance.
        usdc: Deployed USDC token contract instance.
        subscriber: Address subscribing to the service.
        provider: Address of the service provider.
        amount_per_period: USDC per interval in raw units (6 decimals).
        period: Interval duration in seconds.
        num_periods: Number of intervals to pre-fund.
    """
    # Implement: as subscriber, approve USDC for num_periods * amount_per_period,
    # then call subscribe with the provider, amount, and period
    raise NotImplementedError("Create and pre-fund the subscription")


def settle(manager, caller: str, subscriber: str, provider: str):
    """
    Settle one elapsed interval. Callable by anyone once
    block.timestamp >= last_settled + interval.

    Args:
        manager: Deployed SubscriptionManager contract instance.
        caller: Address triggering the settlement (can be anyone).
        subscriber: Address of the subscriber.
        provider: Address of the provider.
    """
    # Implement: as caller, trigger settlement for the subscriber/provider pair
    raise NotImplementedError("Settle one elapsed interval")


def cancel(manager, subscriber: str, provider: str):
    """
    Subscriber cancels and receives balance - pro_rata_owed in the same
    transaction, calculated on-chain.

    Args:
        manager: Deployed SubscriptionManager contract instance.
        subscriber: Address cancelling the subscription.
        provider: Address of the provider.
    """
    # Implement: as subscriber, cancel and verify the pro-rata refund
    raise NotImplementedError("Cancel and receive the pro-rata refund")


def withdraw(manager, provider: str):
    """
    Provider withdraws accrued settled intervals. Cannot withdraw future
    (unsettled) intervals.

    Args:
        manager: Deployed SubscriptionManager contract instance.
        provider: Address of the provider withdrawing.
    """
    # Implement: as provider, withdraw only the accrued settled balance
    raise NotImplementedError("Withdraw accrued settled balance")


def add_metered_charge(manager, provider: str, subscriber: str, units: int):
    """
    Provider bills usage above the flat rate at the per-unit price set
    at subscription creation.

    Args:
        manager: Deployed SubscriptionManager contract instance.
        provider: Address of the provider adding the charge.
        subscriber: Address of the subscriber being charged.
        units: Number of usage units to bill.
    """
    # Implement: as provider, add a metered charge for the subscriber
    raise NotImplementedError("Add a metered usage charge")
