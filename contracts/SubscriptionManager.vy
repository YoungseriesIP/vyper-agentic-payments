# @version ^0.4.0

"""
@title SubscriptionManager - Recurring USDC Payments
@author vyper-agentic-payments
@license MIT
@notice Manages recurring subscription payments with pull-payment pattern
@dev Part of the Vyper Agentic Payments governance layer for Circle Arc chain

This contract enables subscription-based payment workflows:
- Service providers create subscription plans with pricing and intervals
- Subscribers authorize recurring USDC payments
- Pull-payment pattern allows service providers to charge when due
- Supports grace periods, cancellation, and plan updates
- Integrates with x402 Batching SDK for automated agent subscriptions
"""

from ethereum.ercs import IERC20

# ============================================================================
# EVENTS
# ============================================================================

event PlanCreated:
    plan_id: indexed(uint256)
    provider: indexed(address)
    price: uint256
    interval: uint256

event PlanUpdated:
    plan_id: indexed(uint256)
    new_price: uint256

event PlanDeactivated:
    plan_id: indexed(uint256)

event Subscribed:
    subscription_id: indexed(uint256)
    plan_id: indexed(uint256)
    subscriber: indexed(address)

event PaymentCharged:
    subscription_id: indexed(uint256)
    amount: uint256
    charged_at: uint256

event SubscriptionCancelled:
    subscription_id: indexed(uint256)
    cancelled_by: indexed(address)

event SubscriptionPaused:
    subscription_id: indexed(uint256)

event SubscriptionResumed:
    subscription_id: indexed(uint256)

# ============================================================================
# ENUMS & STRUCTS
# ============================================================================

# Subscription status
STATUS_NONE: constant(uint8) = 0
STATUS_ACTIVE: constant(uint8) = 1
STATUS_PAUSED: constant(uint8) = 2
STATUS_CANCELLED: constant(uint8) = 3

# ============================================================================
# CONSTANTS
# ============================================================================

MIN_INTERVAL: constant(uint256) = 3600  # 1 hour minimum
MAX_INTERVAL: constant(uint256) = 31536000  # 1 year maximum
GRACE_PERIOD: constant(uint256) = 86400 * 7  # 7 days grace period

# ============================================================================
# STORAGE
# ============================================================================

usdc: public(immutable(address))

# Plan ID counter
next_plan_id: public(uint256)

# Subscription ID counter
next_subscription_id: public(uint256)

# Plan storage
plan_provider: public(HashMap[uint256, address])
plan_price: public(HashMap[uint256, uint256])
plan_interval: public(HashMap[uint256, uint256])  # seconds between charges
plan_active: public(HashMap[uint256, bool])
plan_metadata: public(HashMap[uint256, String[256]])  # optional metadata URI

# Subscription storage
subscription_plan: public(HashMap[uint256, uint256])  # subscription -> plan
subscription_subscriber: public(HashMap[uint256, address])
subscription_status: public(HashMap[uint256, uint8])
subscription_started_at: public(HashMap[uint256, uint256])
subscription_last_charge: public(HashMap[uint256, uint256])
subscription_total_paid: public(HashMap[uint256, uint256])

# Price locked at subscription time (protects against retroactive price changes)
subscription_price: public(HashMap[uint256, uint256])

# Subscriber lookup
subscriber_to_subscription: public(HashMap[address, HashMap[uint256, uint256]])  # subscriber -> plan -> sub_id

# ============================================================================
# CONSTRUCTOR
# ============================================================================

@deploy
def __init__(_usdc: address):
    """
    @notice Deploy SubscriptionManager with USDC address
    @param _usdc USDC token address (0x3600...00 on Arc)
    """
    assert _usdc != empty(address), "zero address"
    usdc = _usdc
    self.next_plan_id = 1
    self.next_subscription_id = 1

# ============================================================================
# PLAN MANAGEMENT
# ============================================================================

@external
def create_plan(price: uint256, interval: uint256, metadata: String[256] = "") -> uint256:
    """
    @notice Create a new subscription plan
    @param price USDC amount per interval (6 decimals)
    @param interval Seconds between charges
    @param metadata Optional metadata URI
    @return Plan ID
    """
    assert price > 0, "zero price"
    assert interval >= MIN_INTERVAL, "interval too short"
    assert interval <= MAX_INTERVAL, "interval too long"
    
    plan_id: uint256 = self.next_plan_id
    self.next_plan_id = plan_id + 1
    
    self.plan_provider[plan_id] = msg.sender
    self.plan_price[plan_id] = price
    self.plan_interval[plan_id] = interval
    self.plan_active[plan_id] = True
    self.plan_metadata[plan_id] = metadata
    
    log PlanCreated(plan_id=plan_id, provider=msg.sender, price=price, interval=interval)
    
    return plan_id

@external
def update_plan_price(plan_id: uint256, new_price: uint256):
    """
    @notice Update plan price (provider only)
    @dev Only affects new subscriptions; existing subscriptions retain their locked-in price
    @param plan_id The plan ID
    @param new_price New USDC price
    """
    assert self.plan_provider[plan_id] == msg.sender, "not provider"
    assert new_price > 0, "zero price"
    
    self.plan_price[plan_id] = new_price
    
    log PlanUpdated(plan_id=plan_id, new_price=new_price)

@external
def deactivate_plan(plan_id: uint256):
    """
    @notice Deactivate a plan (no new subscriptions)
    @param plan_id The plan ID
    """
    assert self.plan_provider[plan_id] == msg.sender, "not provider"
    
    self.plan_active[plan_id] = False
    
    log PlanDeactivated(plan_id=plan_id)

# ============================================================================
# SUBSCRIPTION MANAGEMENT
# ============================================================================

@external
def subscribe(plan_id: uint256) -> uint256:
    """
    @notice Subscribe to a plan and pay first interval
    @dev Locks in the current plan price for all future charges
    @param plan_id The plan ID to subscribe to
    @return Subscription ID
    """
    assert self.plan_active[plan_id], "plan not active"
    assert self.plan_provider[plan_id] != empty(address), "plan not found"
    assert self.subscriber_to_subscription[msg.sender][plan_id] == 0, "already subscribed"
    
    subscription_id: uint256 = self.next_subscription_id
    self.next_subscription_id = subscription_id + 1
    
    price: uint256 = self.plan_price[plan_id]
    
    # Transfer first payment
    success: bool = extcall IERC20(usdc).transferFrom(msg.sender, self.plan_provider[plan_id], price)
    assert success, "payment failed"
    
    # Create subscription
    self.subscription_plan[subscription_id] = plan_id
    self.subscription_subscriber[subscription_id] = msg.sender
    self.subscription_status[subscription_id] = STATUS_ACTIVE
    self.subscription_started_at[subscription_id] = block.timestamp
    self.subscription_last_charge[subscription_id] = block.timestamp
    self.subscription_price[subscription_id] = price
    self.subscription_total_paid[subscription_id] = price

    self.subscriber_to_subscription[msg.sender][plan_id] = subscription_id
    
    log Subscribed(subscription_id=subscription_id, plan_id=plan_id, subscriber=msg.sender)
    log PaymentCharged(subscription_id=subscription_id, amount=price, charged_at=block.timestamp)
    
    return subscription_id

@external
def charge(subscription_id: uint256):
    """
    @notice Charge a subscription for the next interval
    @dev Can be called by anyone. Uses the price locked at subscription time.
    @param subscription_id The subscription ID
    """
    assert self.subscription_status[subscription_id] == STATUS_ACTIVE, "not active"
    
    plan_id: uint256 = self.subscription_plan[subscription_id]
    interval: uint256 = self.plan_interval[plan_id]
    last_charge: uint256 = self.subscription_last_charge[subscription_id]
    
    assert block.timestamp >= last_charge + interval, "not due yet"
    
    subscriber: address = self.subscription_subscriber[subscription_id]
    provider: address = self.plan_provider[plan_id]
    price: uint256 = self.subscription_price[subscription_id]
    
    # Transfer payment
    success: bool = extcall IERC20(usdc).transferFrom(subscriber, provider, price)
    assert success, "payment failed"
    
    self.subscription_last_charge[subscription_id] = block.timestamp
    self.subscription_total_paid[subscription_id] += price
    
    log PaymentCharged(subscription_id=subscription_id, amount=price, charged_at=block.timestamp)

@external
def cancel(subscription_id: uint256):
    """
    @notice Cancel a subscription
    @dev Can be cancelled by subscriber or provider
    @param subscription_id The subscription ID
    """
    subscriber: address = self.subscription_subscriber[subscription_id]
    plan_id: uint256 = self.subscription_plan[subscription_id]
    provider: address = self.plan_provider[plan_id]
    
    assert msg.sender == subscriber or msg.sender == provider, "not authorized"
    assert self.subscription_status[subscription_id] != STATUS_CANCELLED, "already cancelled"
    
    self.subscription_status[subscription_id] = STATUS_CANCELLED
    self.subscriber_to_subscription[subscriber][plan_id] = 0
    
    log SubscriptionCancelled(subscription_id=subscription_id, cancelled_by=msg.sender)

@external
def pause(subscription_id: uint256):
    """
    @notice Pause a subscription (subscriber only)
    @param subscription_id The subscription ID
    """
    assert self.subscription_subscriber[subscription_id] == msg.sender, "not subscriber"
    assert self.subscription_status[subscription_id] == STATUS_ACTIVE, "not active"
    
    self.subscription_status[subscription_id] = STATUS_PAUSED
    
    log SubscriptionPaused(subscription_id=subscription_id)

@external
def resume(subscription_id: uint256):
    """
    @notice Resume a paused subscription (subscriber only)
    @param subscription_id The subscription ID
    """
    assert self.subscription_subscriber[subscription_id] == msg.sender, "not subscriber"
    assert self.subscription_status[subscription_id] == STATUS_PAUSED, "not paused"
    
    self.subscription_status[subscription_id] = STATUS_ACTIVE
    
    log SubscriptionResumed(subscription_id=subscription_id)

# ============================================================================
# VIEW FUNCTIONS
# ============================================================================

@view
@external
def is_due(subscription_id: uint256) -> bool:
    """
    @notice Check if subscription payment is due
    @param subscription_id The subscription ID
    @return True if payment can be charged
    """
    if self.subscription_status[subscription_id] != STATUS_ACTIVE:
        return False
    
    plan_id: uint256 = self.subscription_plan[subscription_id]
    interval: uint256 = self.plan_interval[plan_id]
    last_charge: uint256 = self.subscription_last_charge[subscription_id]
    
    return block.timestamp >= last_charge + interval

@view
@external
def is_overdue(subscription_id: uint256) -> bool:
    """
    @notice Check if subscription is overdue (past grace period)
    @param subscription_id The subscription ID
    @return True if subscription is overdue
    """
    if self.subscription_status[subscription_id] != STATUS_ACTIVE:
        return False
    
    plan_id: uint256 = self.subscription_plan[subscription_id]
    interval: uint256 = self.plan_interval[plan_id]
    last_charge: uint256 = self.subscription_last_charge[subscription_id]
    
    return block.timestamp > last_charge + interval + GRACE_PERIOD

@view
@external
def next_charge_time(subscription_id: uint256) -> uint256:
    """
    @notice Get next charge timestamp
    @param subscription_id The subscription ID
    @return Timestamp when next charge is due
    """
    plan_id: uint256 = self.subscription_plan[subscription_id]
    interval: uint256 = self.plan_interval[plan_id]
    last_charge: uint256 = self.subscription_last_charge[subscription_id]
    
    return last_charge + interval

@view
@external
def get_plan_info(plan_id: uint256) -> (address, uint256, uint256, bool, String[256]):
    """
    @notice Get plan information
    @param plan_id The plan ID
    @return (provider, price, interval, is_active, metadata)
    """
    return (
        self.plan_provider[plan_id],
        self.plan_price[plan_id],
        self.plan_interval[plan_id],
        self.plan_active[plan_id],
        self.plan_metadata[plan_id]
    )

@view
@external
def get_subscription_info(subscription_id: uint256) -> (uint256, address, uint8, uint256, uint256, uint256, uint256):
    """
    @notice Get subscription information
    @param subscription_id The subscription ID
    @return (plan_id, subscriber, status, started_at, last_charge, total_paid, price)
    """
    return (
        self.subscription_plan[subscription_id],
        self.subscription_subscriber[subscription_id],
        self.subscription_status[subscription_id],
        self.subscription_started_at[subscription_id],
        self.subscription_last_charge[subscription_id],
        self.subscription_total_paid[subscription_id],
        self.subscription_price[subscription_id]
    )

@view
@external
def get_subscription_id(subscriber: address, plan_id: uint256) -> uint256:
    """
    @notice Get subscription ID for a subscriber and plan
    @param subscriber The subscriber address
    @param plan_id The plan ID
    @return Subscription ID (0 if not subscribed)
    """
    return self.subscriber_to_subscription[subscriber][plan_id]
