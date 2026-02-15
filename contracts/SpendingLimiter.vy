# @version ^0.4.0

"""
@title SpendingLimiter - Agent Authorization & Delegation
@author Vyper Agentic Payments
@notice Governs agent spending with configurable limits
@dev This contract allows humans to set guardrails for AI agent spending.

AGENTIC PATTERN:
    This contract solves the "How do I let my agent spend money safely?" problem.
    
    AI agents need to operate autonomously, but humans need control:
    - Per-transaction limits: Cap how much can be spent in one go
    - Daily limits: Cap total spending per 24-hour period
    - Total limits: Cap lifetime spending
    
    The owner (human) sets these limits, and the agent can only spend within them.
    
INTEGRATION WITH x402:
    While the x402 Batching SDK handles off-chain payments, this contract provides
    on-chain guardrails. The pattern:
    
    1. Human deposits USDC to Gateway for their agent
    2. Human configures SpendingLimiter with limits for the agent's address
    3. Before spending, agent (or a relay) checks limits on-chain
    4. If within limits, agent proceeds with x402 payment
    
    # NOTE: The agent's client code checks this contract before spending.
    # The SDK itself doesn't enforce these limits — it's an additional safety
    # layer. A production integration could wrap gateway.pay() with a limit check.

USDC on Arc Testnet: 0x3600000000000000000000000000000000000000
"""

# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACES
# ═══════════════════════════════════════════════════════════════════════════════

interface IERC20:
    def transfer(to: address, amount: uint256) -> bool: nonpayable
    def transferFrom(sender: address, recipient: address, amount: uint256) -> bool: nonpayable
    def balanceOf(account: address) -> uint256: view

# ═══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

event AgentAuthorized:
    owner: indexed(address)
    agent: indexed(address)
    perTxLimit: uint256
    dailyLimit: uint256
    totalLimit: uint256

event AgentRevoked:
    owner: indexed(address)
    agent: indexed(address)

event LimitsUpdated:
    owner: indexed(address)
    agent: indexed(address)
    perTxLimit: uint256
    dailyLimit: uint256
    totalLimit: uint256

event SpendingRecorded:
    owner: indexed(address)
    agent: indexed(address)
    amount: uint256
    recipient: address

event FundsDeposited:
    owner: indexed(address)
    amount: uint256

event FundsWithdrawn:
    owner: indexed(address)
    amount: uint256

# ═══════════════════════════════════════════════════════════════════════════════
# STATE VARIABLES
# ═══════════════════════════════════════════════════════════════════════════════

# USDC token address
usdc: public(address)

# Owner balances (funds deposited for agents to spend)
ownerBalance: public(HashMap[address, uint256])

# Agent authorization: owner -> agent -> is authorized
isAuthorized: public(HashMap[address, HashMap[address, bool]])

# Spending limits: owner -> agent -> limit values
perTxLimit: public(HashMap[address, HashMap[address, uint256]])
dailyLimit: public(HashMap[address, HashMap[address, uint256]])
totalLimit: public(HashMap[address, HashMap[address, uint256]])

# Spending tracking
totalSpent: public(HashMap[address, HashMap[address, uint256]])
dailySpent: public(HashMap[address, HashMap[address, uint256]])
lastSpendingDay: public(HashMap[address, HashMap[address, uint256]])

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTOR
# ═══════════════════════════════════════════════════════════════════════════════

@deploy
def __init__(usdc_address: address):
    """
    @notice Initialize the spending limiter
    @param usdc_address USDC token address
    """
    assert usdc_address != empty(address), "SpendingLimiter: zero address"
    self.usdc = usdc_address


# ═══════════════════════════════════════════════════════════════════════════════
# OWNER FUNCTIONS: FUND MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@external
def deposit(amount: uint256):
    """
    @notice Deposit USDC for agents to spend
    @param amount Amount to deposit (6 decimals)
    @dev Caller must have approved this contract
    """
    assert amount > 0, "SpendingLimiter: zero amount"
    
    success: bool = extcall IERC20(self.usdc).transferFrom(msg.sender, self, amount)
    assert success, "SpendingLimiter: transfer failed"
    
    self.ownerBalance[msg.sender] += amount
    
    log FundsDeposited(owner=msg.sender, amount=amount)


@external
def withdraw(amount: uint256):
    """
    @notice Withdraw USDC back to owner
    @param amount Amount to withdraw
    """
    assert amount > 0, "SpendingLimiter: zero amount"
    assert self.ownerBalance[msg.sender] >= amount, "SpendingLimiter: insufficient balance"
    
    self.ownerBalance[msg.sender] -= amount
    
    success: bool = extcall IERC20(self.usdc).transfer(msg.sender, amount)
    assert success, "SpendingLimiter: transfer failed"
    
    log FundsWithdrawn(owner=msg.sender, amount=amount)


# ═══════════════════════════════════════════════════════════════════════════════
# OWNER FUNCTIONS: AGENT AUTHORIZATION
# ═══════════════════════════════════════════════════════════════════════════════

@external
def authorizeAgent(
    agent: address,
    per_tx_limit: uint256,
    daily_limit: uint256,
    total_limit: uint256
):
    """
    @notice Authorize an agent with spending limits
    @param agent The agent address to authorize
    @param per_tx_limit Maximum amount per transaction (0 = no limit)
    @param daily_limit Maximum daily spending (0 = no limit)
    @param total_limit Maximum lifetime spending (0 = no limit)
    """
    assert agent != empty(address), "SpendingLimiter: zero address"
    assert agent != msg.sender, "SpendingLimiter: cannot authorize self"
    
    self.isAuthorized[msg.sender][agent] = True
    self.perTxLimit[msg.sender][agent] = per_tx_limit
    self.dailyLimit[msg.sender][agent] = daily_limit
    self.totalLimit[msg.sender][agent] = total_limit
    
    log AgentAuthorized(
        owner=msg.sender,
        agent=agent,
        perTxLimit=per_tx_limit,
        dailyLimit=daily_limit,
        totalLimit=total_limit
    )


@external
def revokeAgent(agent: address):
    """
    @notice Revoke agent authorization
    @param agent The agent to revoke
    """
    self.isAuthorized[msg.sender][agent] = False
    
    log AgentRevoked(owner=msg.sender, agent=agent)


@external
def updateLimits(
    agent: address,
    per_tx_limit: uint256,
    daily_limit: uint256,
    total_limit: uint256
):
    """
    @notice Update agent spending limits
    @param agent The agent to update
    @param per_tx_limit New per-transaction limit
    @param daily_limit New daily limit
    @param total_limit New total limit
    """
    assert self.isAuthorized[msg.sender][agent], "SpendingLimiter: not authorized"
    
    self.perTxLimit[msg.sender][agent] = per_tx_limit
    self.dailyLimit[msg.sender][agent] = daily_limit
    self.totalLimit[msg.sender][agent] = total_limit
    
    log LimitsUpdated(
        owner=msg.sender,
        agent=agent,
        perTxLimit=per_tx_limit,
        dailyLimit=daily_limit,
        totalLimit=total_limit
    )


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT FUNCTIONS: SPENDING
# ═══════════════════════════════════════════════════════════════════════════════

@external
def spend(owner: address, amount: uint256, recipient: address):
    """
    @notice Agent spends from owner's balance
    @param owner The owner whose funds to spend
    @param amount Amount to spend
    @param recipient Address to send USDC to
    @dev Only authorized agents can call this
    """
    assert self.isAuthorized[owner][msg.sender], "SpendingLimiter: not authorized"
    assert amount > 0, "SpendingLimiter: zero amount"
    assert recipient != empty(address), "SpendingLimiter: zero recipient"
    
    # Check per-transaction limit
    per_tx: uint256 = self.perTxLimit[owner][msg.sender]
    if per_tx > 0:
        assert amount <= per_tx, "SpendingLimiter: exceeds per-tx limit"
    
    # Reset daily spending if new day
    current_day: uint256 = block.timestamp // 86400
    if current_day > self.lastSpendingDay[owner][msg.sender]:
        self.dailySpent[owner][msg.sender] = 0
        self.lastSpendingDay[owner][msg.sender] = current_day
    
    # Check daily limit
    daily: uint256 = self.dailyLimit[owner][msg.sender]
    if daily > 0:
        assert self.dailySpent[owner][msg.sender] + amount <= daily, "SpendingLimiter: exceeds daily limit"
    
    # Check total limit
    total: uint256 = self.totalLimit[owner][msg.sender]
    if total > 0:
        assert self.totalSpent[owner][msg.sender] + amount <= total, "SpendingLimiter: exceeds total limit"
    
    # Check owner balance
    assert self.ownerBalance[owner] >= amount, "SpendingLimiter: insufficient balance"
    
    # Update tracking
    self.dailySpent[owner][msg.sender] += amount
    self.totalSpent[owner][msg.sender] += amount
    self.ownerBalance[owner] -= amount
    
    # Transfer
    success: bool = extcall IERC20(self.usdc).transfer(recipient, amount)
    assert success, "SpendingLimiter: transfer failed"
    
    log SpendingRecorded(owner=owner, agent=msg.sender, amount=amount, recipient=recipient)


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@external
@view
def canSpend(owner: address, agent: address, amount: uint256) -> bool:
    """
    @notice Check if agent can spend a given amount
    @param owner The owner
    @param agent The agent
    @param amount The amount to check
    @return True if the spend would succeed
    """
    if not self.isAuthorized[owner][agent]:
        return False
    
    # Check per-tx limit
    per_tx: uint256 = self.perTxLimit[owner][agent]
    if per_tx > 0 and amount > per_tx:
        return False
    
    # Check daily limit (considering potential reset)
    current_day: uint256 = block.timestamp // 86400
    daily_spent: uint256 = self.dailySpent[owner][agent]
    if current_day > self.lastSpendingDay[owner][agent]:
        daily_spent = 0
    
    daily: uint256 = self.dailyLimit[owner][agent]
    if daily > 0 and daily_spent + amount > daily:
        return False
    
    # Check total limit
    total: uint256 = self.totalLimit[owner][agent]
    if total > 0 and self.totalSpent[owner][agent] + amount > total:
        return False
    
    # Check balance
    if self.ownerBalance[owner] < amount:
        return False
    
    return True


@external
@view
def getRemainingLimits(owner: address, agent: address) -> (uint256, uint256, uint256):
    """
    @notice Get remaining spending limits for an agent
    @param owner The owner
    @param agent The agent
    @return Tuple of (remainingDaily, remainingTotal, ownerBalance)
    """
    # Calculate remaining daily (considering potential reset)
    current_day: uint256 = block.timestamp // 86400
    daily_spent: uint256 = self.dailySpent[owner][agent]
    if current_day > self.lastSpendingDay[owner][agent]:
        daily_spent = 0
    
    daily: uint256 = self.dailyLimit[owner][agent]
    remaining_daily: uint256 = 0
    if daily > 0:
        if daily > daily_spent:
            remaining_daily = daily - daily_spent
    else:
        remaining_daily = max_value(uint256)  # No limit
    
    # Calculate remaining total
    total: uint256 = self.totalLimit[owner][agent]
    remaining_total: uint256 = 0
    if total > 0:
        if total > self.totalSpent[owner][agent]:
            remaining_total = total - self.totalSpent[owner][agent]
    else:
        remaining_total = max_value(uint256)  # No limit
    
    return (remaining_daily, remaining_total, self.ownerBalance[owner])


@external
@view
def getAgentLimits(owner: address, agent: address) -> (uint256, uint256, uint256, bool):
    """
    @notice Get configured limits for an agent
    @param owner The owner
    @param agent The agent
    @return Tuple of (perTxLimit, dailyLimit, totalLimit, isAuthorized)
    """
    return (
        self.perTxLimit[owner][agent],
        self.dailyLimit[owner][agent],
        self.totalLimit[owner][agent],
        self.isAuthorized[owner][agent]
    )
