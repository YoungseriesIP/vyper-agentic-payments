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
    planId: indexed(uint256)
    provider: indexed(address)
    price: uint256
    interval: uint256

event PlanUpdated:
    planId: indexed(uint256)
    newPrice: uint256

event PlanDeactivated:
    planId: indexed(uint256)

event Subscribed:
    subscriptionId: indexed(uint256)
    planId: indexed(uint256)
    subscriber: indexed(address)

event PaymentCharged:
    subscriptionId: indexed(uint256)
    amount: uint256
    chargedAt: uint256

event SubscriptionCancelled:
    subscriptionId: indexed(uint256)
    cancelledBy: indexed(address)

event SubscriptionPaused:
    subscriptionId: indexed(uint256)

event SubscriptionResumed:
    subscriptionId: indexed(uint256)

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
nextPlanId: public(uint256)

# Subscription ID counter
nextSubscriptionId: public(uint256)

# Plan storage
planProvider: public(HashMap[uint256, address])
planPrice: public(HashMap[uint256, uint256])
planInterval: public(HashMap[uint256, uint256])  # seconds between charges
planActive: public(HashMap[uint256, bool])
planMetadata: public(HashMap[uint256, String[256]])  # optional metadata URI

# Subscription storage
subscriptionPlan: public(HashMap[uint256, uint256])  # subscription -> plan
subscriptionSubscriber: public(HashMap[uint256, address])
subscriptionStatus: public(HashMap[uint256, uint8])
subscriptionStartedAt: public(HashMap[uint256, uint256])
subscriptionLastCharge: public(HashMap[uint256, uint256])
subscriptionTotalPaid: public(HashMap[uint256, uint256])

# Subscriber lookup
subscriberToSubscription: public(HashMap[address, HashMap[uint256, uint256]])  # subscriber -> plan -> subId

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
    self.nextPlanId = 1
    self.nextSubscriptionId = 1

# ============================================================================
# PLAN MANAGEMENT
# ============================================================================

@external
def createPlan(price: uint256, interval: uint256, metadata: String[256] = "") -> uint256:
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
    
    planId: uint256 = self.nextPlanId
    self.nextPlanId = planId + 1
    
    self.planProvider[planId] = msg.sender
    self.planPrice[planId] = price
    self.planInterval[planId] = interval
    self.planActive[planId] = True
    self.planMetadata[planId] = metadata
    
    log PlanCreated(planId=planId, provider=msg.sender, price=price, interval=interval)
    
    return planId

@external
def updatePlanPrice(planId: uint256, newPrice: uint256):
    """
    @notice Update plan price (provider only)
    @dev Affects future charges, not existing subscriptions until renewal
    @param planId The plan ID
    @param newPrice New USDC price
    """
    assert self.planProvider[planId] == msg.sender, "not provider"
    assert newPrice > 0, "zero price"
    
    self.planPrice[planId] = newPrice
    
    log PlanUpdated(planId=planId, newPrice=newPrice)

@external
def deactivatePlan(planId: uint256):
    """
    @notice Deactivate a plan (no new subscriptions)
    @param planId The plan ID
    """
    assert self.planProvider[planId] == msg.sender, "not provider"
    
    self.planActive[planId] = False
    
    log PlanDeactivated(planId=planId)

# ============================================================================
# SUBSCRIPTION MANAGEMENT
# ============================================================================

@external
def subscribe(planId: uint256) -> uint256:
    """
    @notice Subscribe to a plan and pay first interval
    @param planId The plan ID to subscribe to
    @return Subscription ID
    """
    assert self.planActive[planId], "plan not active"
    assert self.planProvider[planId] != empty(address), "plan not found"
    assert self.subscriberToSubscription[msg.sender][planId] == 0, "already subscribed"
    
    subscriptionId: uint256 = self.nextSubscriptionId
    self.nextSubscriptionId = subscriptionId + 1
    
    price: uint256 = self.planPrice[planId]
    
    # Transfer first payment
    success: bool = extcall IERC20(usdc).transferFrom(msg.sender, self.planProvider[planId], price)
    assert success, "payment failed"
    
    # Create subscription
    self.subscriptionPlan[subscriptionId] = planId
    self.subscriptionSubscriber[subscriptionId] = msg.sender
    self.subscriptionStatus[subscriptionId] = STATUS_ACTIVE
    self.subscriptionStartedAt[subscriptionId] = block.timestamp
    self.subscriptionLastCharge[subscriptionId] = block.timestamp
    self.subscriptionTotalPaid[subscriptionId] = price
    
    self.subscriberToSubscription[msg.sender][planId] = subscriptionId
    
    log Subscribed(subscriptionId=subscriptionId, planId=planId, subscriber=msg.sender)
    log PaymentCharged(subscriptionId=subscriptionId, amount=price, chargedAt=block.timestamp)
    
    return subscriptionId

@external
def charge(subscriptionId: uint256):
    """
    @notice Charge a subscription for the next interval
    @dev Can be called by anyone, but payment goes to plan provider
    @param subscriptionId The subscription ID
    """
    assert self.subscriptionStatus[subscriptionId] == STATUS_ACTIVE, "not active"
    
    planId: uint256 = self.subscriptionPlan[subscriptionId]
    interval: uint256 = self.planInterval[planId]
    lastCharge: uint256 = self.subscriptionLastCharge[subscriptionId]
    
    assert block.timestamp >= lastCharge + interval, "not due yet"
    
    subscriber: address = self.subscriptionSubscriber[subscriptionId]
    provider: address = self.planProvider[planId]
    price: uint256 = self.planPrice[planId]
    
    # Transfer payment
    success: bool = extcall IERC20(usdc).transferFrom(subscriber, provider, price)
    assert success, "payment failed"
    
    self.subscriptionLastCharge[subscriptionId] = block.timestamp
    self.subscriptionTotalPaid[subscriptionId] += price
    
    log PaymentCharged(subscriptionId=subscriptionId, amount=price, chargedAt=block.timestamp)

@external
def cancel(subscriptionId: uint256):
    """
    @notice Cancel a subscription
    @dev Can be cancelled by subscriber or provider
    @param subscriptionId The subscription ID
    """
    subscriber: address = self.subscriptionSubscriber[subscriptionId]
    planId: uint256 = self.subscriptionPlan[subscriptionId]
    provider: address = self.planProvider[planId]
    
    assert msg.sender == subscriber or msg.sender == provider, "not authorized"
    assert self.subscriptionStatus[subscriptionId] != STATUS_CANCELLED, "already cancelled"
    
    self.subscriptionStatus[subscriptionId] = STATUS_CANCELLED
    self.subscriberToSubscription[subscriber][planId] = 0
    
    log SubscriptionCancelled(subscriptionId=subscriptionId, cancelledBy=msg.sender)

@external
def pause(subscriptionId: uint256):
    """
    @notice Pause a subscription (subscriber only)
    @param subscriptionId The subscription ID
    """
    assert self.subscriptionSubscriber[subscriptionId] == msg.sender, "not subscriber"
    assert self.subscriptionStatus[subscriptionId] == STATUS_ACTIVE, "not active"
    
    self.subscriptionStatus[subscriptionId] = STATUS_PAUSED
    
    log SubscriptionPaused(subscriptionId=subscriptionId)

@external
def resume(subscriptionId: uint256):
    """
    @notice Resume a paused subscription (subscriber only)
    @param subscriptionId The subscription ID
    """
    assert self.subscriptionSubscriber[subscriptionId] == msg.sender, "not subscriber"
    assert self.subscriptionStatus[subscriptionId] == STATUS_PAUSED, "not paused"
    
    self.subscriptionStatus[subscriptionId] = STATUS_ACTIVE
    
    log SubscriptionResumed(subscriptionId=subscriptionId)

# ============================================================================
# VIEW FUNCTIONS
# ============================================================================

@view
@external
def isDue(subscriptionId: uint256) -> bool:
    """
    @notice Check if subscription payment is due
    @param subscriptionId The subscription ID
    @return True if payment can be charged
    """
    if self.subscriptionStatus[subscriptionId] != STATUS_ACTIVE:
        return False
    
    planId: uint256 = self.subscriptionPlan[subscriptionId]
    interval: uint256 = self.planInterval[planId]
    lastCharge: uint256 = self.subscriptionLastCharge[subscriptionId]
    
    return block.timestamp >= lastCharge + interval

@view
@external
def isOverdue(subscriptionId: uint256) -> bool:
    """
    @notice Check if subscription is overdue (past grace period)
    @param subscriptionId The subscription ID
    @return True if subscription is overdue
    """
    if self.subscriptionStatus[subscriptionId] != STATUS_ACTIVE:
        return False
    
    planId: uint256 = self.subscriptionPlan[subscriptionId]
    interval: uint256 = self.planInterval[planId]
    lastCharge: uint256 = self.subscriptionLastCharge[subscriptionId]
    
    return block.timestamp > lastCharge + interval + GRACE_PERIOD

@view
@external
def nextChargeTime(subscriptionId: uint256) -> uint256:
    """
    @notice Get next charge timestamp
    @param subscriptionId The subscription ID
    @return Timestamp when next charge is due
    """
    planId: uint256 = self.subscriptionPlan[subscriptionId]
    interval: uint256 = self.planInterval[planId]
    lastCharge: uint256 = self.subscriptionLastCharge[subscriptionId]
    
    return lastCharge + interval

@view
@external
def getPlanInfo(planId: uint256) -> (address, uint256, uint256, bool, String[256]):
    """
    @notice Get plan information
    @param planId The plan ID
    @return (provider, price, interval, isActive, metadata)
    """
    return (
        self.planProvider[planId],
        self.planPrice[planId],
        self.planInterval[planId],
        self.planActive[planId],
        self.planMetadata[planId]
    )

@view
@external
def getSubscriptionInfo(subscriptionId: uint256) -> (uint256, address, uint8, uint256, uint256, uint256):
    """
    @notice Get subscription information
    @param subscriptionId The subscription ID
    @return (planId, subscriber, status, startedAt, lastCharge, totalPaid)
    """
    return (
        self.subscriptionPlan[subscriptionId],
        self.subscriptionSubscriber[subscriptionId],
        self.subscriptionStatus[subscriptionId],
        self.subscriptionStartedAt[subscriptionId],
        self.subscriptionLastCharge[subscriptionId],
        self.subscriptionTotalPaid[subscriptionId]
    )

@view
@external
def getSubscriptionId(subscriber: address, planId: uint256) -> uint256:
    """
    @notice Get subscription ID for a subscriber and plan
    @param subscriber The subscriber address
    @param planId The plan ID
    @return Subscription ID (0 if not subscribed)
    """
    return self.subscriberToSubscription[subscriber][planId]
