# @version ^0.4.0

"""
@title PaymentSplitter - Revenue Distribution for Multi-Agent Collaboration
@author vyper-agentic-payments
@license MIT
@notice Distributes USDC payments among multiple recipients based on shares
@dev Part of the Vyper Agentic Payments governance layer for Circle Arc chain

This contract enables automatic revenue splitting for agent collaborations:
- Create payment pools with defined share allocations
- Accept USDC deposits that are automatically tracked per pool
- Recipients claim their share of accumulated payments
- Supports dynamic share updates (by pool owner)
- Integrates with x402 Batching SDK for agent payment workflows
"""

from ethereum.ercs import IERC20

# ============================================================================
# EVENTS
# ============================================================================

event PoolCreated:
    poolId: indexed(uint256)
    owner: indexed(address)
    recipientCount: uint256

event SharesUpdated:
    poolId: indexed(uint256)
    recipient: indexed(address)
    newShares: uint256

event PaymentReceived:
    poolId: indexed(uint256)
    amount: uint256
    sender: indexed(address)

event PaymentClaimed:
    poolId: indexed(uint256)
    recipient: indexed(address)
    amount: uint256

event RecipientAdded:
    poolId: indexed(uint256)
    recipient: indexed(address)
    shares: uint256

event RecipientRemoved:
    poolId: indexed(uint256)
    recipient: indexed(address)

# ============================================================================
# CONSTANTS
# ============================================================================

MAX_RECIPIENTS: constant(uint256) = 100
MAX_SHARES: constant(uint256) = 10000  # 100.00% in basis points

# ============================================================================
# STORAGE
# ============================================================================

usdc: public(immutable(address))

# Pool ID counter
nextPoolId: public(uint256)

# Pool owner (can update shares)
poolOwner: public(HashMap[uint256, address])

# Total shares in a pool (should equal MAX_SHARES for proper distribution)
totalShares: public(HashMap[uint256, uint256])

# Shares per recipient in a pool
shares: public(HashMap[uint256, HashMap[address, uint256]])

# Total USDC deposited to a pool (cumulative)
totalReceived: public(HashMap[uint256, uint256])

# USDC already claimed by recipient from a pool
claimed: public(HashMap[uint256, HashMap[address, uint256]])

# Track if recipient is part of pool (for iteration tracking)
isRecipient: public(HashMap[uint256, HashMap[address, bool]])

# ============================================================================
# CONSTRUCTOR
# ============================================================================

@deploy
def __init__(_usdc: address):
    """
    @notice Deploy PaymentSplitter with USDC address
    @param _usdc USDC token address (0x3600...00 on Arc)
    """
    assert _usdc != empty(address), "zero address"
    usdc = _usdc
    self.nextPoolId = 1

# ============================================================================
# POOL MANAGEMENT
# ============================================================================

@external
def createPool(
    recipients: DynArray[address, 100],
    shareAmounts: DynArray[uint256, 100]
) -> uint256:
    """
    @notice Create a new payment pool with share allocations
    @param recipients List of recipient addresses
    @param shareAmounts List of share amounts (in basis points)
    @return Pool ID
    """
    assert len(recipients) > 0, "no recipients"
    assert len(recipients) == len(shareAmounts), "length mismatch"
    assert len(recipients) <= MAX_RECIPIENTS, "too many recipients"
    
    poolId: uint256 = self.nextPoolId
    self.nextPoolId = poolId + 1
    
    self.poolOwner[poolId] = msg.sender
    
    totalSharesSum: uint256 = 0
    
    for i: uint256 in range(100):
        if i >= len(recipients):
            break
        
        recipient: address = recipients[i]
        shareAmount: uint256 = shareAmounts[i]
        
        assert recipient != empty(address), "zero recipient"
        assert shareAmount > 0, "zero shares"
        assert not self.isRecipient[poolId][recipient], "duplicate recipient"
        
        self.shares[poolId][recipient] = shareAmount
        self.isRecipient[poolId][recipient] = True
        totalSharesSum += shareAmount
    
    assert totalSharesSum == MAX_SHARES, "shares must equal 10000"
    self.totalShares[poolId] = totalSharesSum
    
    log PoolCreated(poolId=poolId, owner=msg.sender, recipientCount=len(recipients))
    
    return poolId

@external
def updateShares(poolId: uint256, recipient: address, newShares: uint256):
    """
    @notice Update shares for a recipient (pool owner only)
    @dev This can break the MAX_SHARES invariant - use carefully
    @param poolId The pool ID
    @param recipient The recipient to update
    @param newShares New share amount
    """
    assert self.poolOwner[poolId] == msg.sender, "not pool owner"
    assert self.isRecipient[poolId][recipient], "not a recipient"
    
    oldShares: uint256 = self.shares[poolId][recipient]
    self.shares[poolId][recipient] = newShares
    self.totalShares[poolId] = self.totalShares[poolId] - oldShares + newShares
    
    log SharesUpdated(poolId=poolId, recipient=recipient, newShares=newShares)

@external
def addRecipient(poolId: uint256, recipient: address, shareAmount: uint256):
    """
    @notice Add a new recipient to the pool (pool owner only)
    @param poolId The pool ID
    @param recipient New recipient address
    @param shareAmount Share amount for new recipient
    """
    assert self.poolOwner[poolId] == msg.sender, "not pool owner"
    assert recipient != empty(address), "zero recipient"
    assert not self.isRecipient[poolId][recipient], "already recipient"
    assert shareAmount > 0, "zero shares"
    
    self.shares[poolId][recipient] = shareAmount
    self.isRecipient[poolId][recipient] = True
    self.totalShares[poolId] += shareAmount
    
    log RecipientAdded(poolId=poolId, recipient=recipient, shares=shareAmount)

@external
def removeRecipient(poolId: uint256, recipient: address):
    """
    @notice Remove a recipient from the pool (pool owner only)
    @dev Recipient should claim before removal
    @param poolId The pool ID
    @param recipient Recipient to remove
    """
    assert self.poolOwner[poolId] == msg.sender, "not pool owner"
    assert self.isRecipient[poolId][recipient], "not a recipient"
    
    shareAmount: uint256 = self.shares[poolId][recipient]
    self.totalShares[poolId] -= shareAmount
    self.shares[poolId][recipient] = 0
    self.isRecipient[poolId][recipient] = False
    
    log RecipientRemoved(poolId=poolId, recipient=recipient)

# ============================================================================
# PAYMENTS
# ============================================================================

@external
def deposit(poolId: uint256, amount: uint256):
    """
    @notice Deposit USDC to a payment pool
    @param poolId The pool ID
    @param amount Amount of USDC to deposit
    """
    assert amount > 0, "zero amount"
    assert self.poolOwner[poolId] != empty(address), "pool not found"
    
    # Transfer USDC from sender to this contract
    success: bool = extcall IERC20(usdc).transferFrom(msg.sender, self, amount)
    assert success, "transfer failed"
    
    self.totalReceived[poolId] += amount
    
    log PaymentReceived(poolId=poolId, amount=amount, sender=msg.sender)

@external
def claim(poolId: uint256):
    """
    @notice Claim your share of accumulated payments
    @param poolId The pool ID
    """
    assert self.isRecipient[poolId][msg.sender], "not a recipient"
    
    claimable: uint256 = self._pendingPayment(poolId, msg.sender)
    assert claimable > 0, "nothing to claim"
    
    self.claimed[poolId][msg.sender] += claimable
    
    success: bool = extcall IERC20(usdc).transfer(msg.sender, claimable)
    assert success, "transfer failed"
    
    log PaymentClaimed(poolId=poolId, recipient=msg.sender, amount=claimable)

@external
def claimFor(poolId: uint256, recipient: address):
    """
    @notice Claim on behalf of a recipient (anyone can trigger)
    @param poolId The pool ID
    @param recipient The recipient to claim for
    """
    assert self.isRecipient[poolId][recipient], "not a recipient"
    
    claimable: uint256 = self._pendingPayment(poolId, recipient)
    assert claimable > 0, "nothing to claim"
    
    self.claimed[poolId][recipient] += claimable
    
    success: bool = extcall IERC20(usdc).transfer(recipient, claimable)
    assert success, "transfer failed"
    
    log PaymentClaimed(poolId=poolId, recipient=recipient, amount=claimable)

# ============================================================================
# VIEW FUNCTIONS
# ============================================================================

@view
@external
def pendingPayment(poolId: uint256, recipient: address) -> uint256:
    """
    @notice Get pending payment for a recipient
    @param poolId The pool ID
    @param recipient The recipient address
    @return Amount of USDC claimable
    """
    return self._pendingPayment(poolId, recipient)

@view
@internal
def _pendingPayment(poolId: uint256, recipient: address) -> uint256:
    """
    @notice Internal: Calculate pending payment
    """
    if not self.isRecipient[poolId][recipient]:
        return 0
    
    if self.totalShares[poolId] == 0:
        return 0
    
    # Calculate total owed based on shares
    totalOwed: uint256 = (self.totalReceived[poolId] * self.shares[poolId][recipient]) // self.totalShares[poolId]
    
    # Subtract already claimed
    alreadyClaimed: uint256 = self.claimed[poolId][recipient]
    
    if totalOwed <= alreadyClaimed:
        return 0
    
    return totalOwed - alreadyClaimed

@view
@external
def getPoolInfo(poolId: uint256) -> (address, uint256, uint256):
    """
    @notice Get pool information
    @param poolId The pool ID
    @return (owner, totalShares, totalReceived)
    """
    return (
        self.poolOwner[poolId],
        self.totalShares[poolId],
        self.totalReceived[poolId]
    )

@view
@external
def getRecipientInfo(poolId: uint256, recipient: address) -> (uint256, uint256, uint256, bool):
    """
    @notice Get recipient information in a pool
    @param poolId The pool ID
    @param recipient The recipient address
    @return (shares, claimed, pending, isRecipient)
    """
    return (
        self.shares[poolId][recipient],
        self.claimed[poolId][recipient],
        self._pendingPayment(poolId, recipient),
        self.isRecipient[poolId][recipient]
    )

@view
@external
def getSharePercentage(poolId: uint256, recipient: address) -> uint256:
    """
    @notice Get recipient's share as percentage (basis points)
    @param poolId The pool ID
    @param recipient The recipient address
    @return Share percentage in basis points (e.g., 5000 = 50%)
    """
    if self.totalShares[poolId] == 0:
        return 0
    return (self.shares[poolId][recipient] * MAX_SHARES) // self.totalShares[poolId]
