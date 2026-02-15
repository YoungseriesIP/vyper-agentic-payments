# SubscriptionManager.vy

Recurring USDC payments with pull-payment pattern.

## Overview

This contract manages subscription-based payment workflows. Service providers create plans, subscribers authorize recurring payments, and providers charge when due.

## Features

- Create subscription plans with pricing and intervals
- Subscribers authorize recurring USDC payments
- Pull-payment pattern for provider-initiated charges
- Grace periods for late payments
- Cancellation and pause support

## Key Functions

### Plan Management

```vyper
@external
def createPlan(price: uint256, interval: uint256, name: String[64]) -> uint256

@external
def updatePlanPrice(planId: uint256, newPrice: uint256)

@external
def deactivatePlan(planId: uint256)
```

### Subscription Management

```vyper
@external
def subscribe(planId: uint256) -> uint256

@external
def cancel(subscriptionId: uint256)

@external
def pause(subscriptionId: uint256)

@external
def resume(subscriptionId: uint256)
```

### Billing

```vyper
@external
def charge(subscriptionId: uint256)

@view
def canCharge(subscriptionId: uint256) -> bool

@view
def nextChargeTime(subscriptionId: uint256) -> uint256
```

### Query Functions

```vyper
@view
def getPlan(planId: uint256) -> (address, uint256, uint256, bool)

@view
def getSubscription(subscriptionId: uint256) -> (uint256, address, uint256, uint8)

@view
def isSubscriptionActive(subscriptionId: uint256) -> bool
```

## Events

| Event | Description |
|-------|-------------|
| `PlanCreated` | New subscription plan |
| `PlanUpdated` | Plan price changed |
| `PlanDeactivated` | Plan no longer available |
| `Subscribed` | New subscription started |
| `PaymentCharged` | Recurring payment collected |
| `SubscriptionCancelled` | Subscription ended |
| `SubscriptionPaused` | Subscription paused |
| `SubscriptionResumed` | Subscription resumed |

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `MIN_INTERVAL` | 3600 | 1 hour minimum |
| `MAX_INTERVAL` | 31536000 | 1 year maximum |
| `GRACE_PERIOD` | 604800 | 7 days grace |

## Subscription Status

| Status | Value | Description |
|--------|-------|-------------|
| `STATUS_NONE` | 0 | Not subscribed |
| `STATUS_ACTIVE` | 1 | Active subscription |
| `STATUS_PAUSED` | 2 | Temporarily paused |
| `STATUS_CANCELLED` | 3 | Permanently cancelled |

## Usage Example

```python
import boa

sub_mgr = boa.load("contracts/SubscriptionManager.vy", usdc_address)

# Provider creates a monthly plan for $10
plan_id = sub_mgr.createPlan(
    10 * 10**6,   # $10 per month
    30 * 86400,   # 30 days interval
    "Pro Plan"
)

# Subscriber approves USDC spending
usdc.approve(sub_mgr.address, 10 * 10**6 * 12)  # 12 months

# Subscriber signs up
with boa.env.prank(subscriber):
    sub_id = sub_mgr.subscribe(plan_id)

# First charge happens on subscribe
# Provider charges again after interval
boa.env.time_travel(30 * 86400)  # Fast-forward 30 days

with boa.env.prank(provider):
    sub_mgr.charge(sub_id)  # Collects $10
```

## Integration with x402

Subscriptions can be used with x402 for hybrid billing:

1. **Base subscription** - Monthly fee via SubscriptionManager
2. **Overage billing** - x402 micropayments for usage beyond quota

```python
# Check subscription status before allowing service access
if sub_mgr.isSubscriptionActive(sub_id):
    # Allow access
    pass
else:
    # Require x402 payment or redirect to subscribe
    pass
```

## Grace Period

After the billing interval, there's a 7-day grace period:

- Days 1-30: Normal billing period
- Days 31-37: Grace period (still can charge)
- Day 38+: Subscription lapses, cannot charge

## Security Considerations

- Only provider can charge subscriptions
- Only subscriber can cancel/pause
- USDC approval required before subscribe
- Failed charges don't auto-cancel (grace period applies)
- Provider cannot change price for existing subscriptions
