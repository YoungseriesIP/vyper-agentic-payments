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
    # The SDK itself doesn't enforce these limits; it's an additional safety
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
    per_tx_limit: uint256
    daily_limit: uint256
    total_limit: uint256

event AgentRevoked:
    owner: indexed(address)
    agent: indexed(address)

event LimitsUpdated:
    owner: indexed(address)
    agent: indexed(address)
    per_tx_limit: uint256
    daily_limit: uint256
    total_limit: uint256

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
owner_balance: public(HashMap[address, uint256])

# Agent authorization: owner -> agent -> is authorized
is_authorized: public(HashMap[address, HashMap[address, bool]])

# Spending limits: owner -> agent -> limit values
per_tx_limit: public(HashMap[address, HashMap[address, uint256]])
daily_limit: public(HashMap[address, HashMap[address, uint256]])
total_limit: public(HashMap[address, HashMap[address, uint256]])

# Spending tracking
total_spent: public(HashMap[address, HashMap[address, uint256]])
daily_spent: public(HashMap[address, HashMap[address, uint256]])
last_spending_day: public(HashMap[address, HashMap[address, uint256]])

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
    
    self.owner_balance[msg.sender] += amount
    
    log FundsDeposited(owner=msg.sender, amount=amount)


@external
def withdraw(amount: uint256):
    """
    @notice Withdraw USDC back to owner
    @param amount Amount to withdraw
    """
    assert amount > 0, "SpendingLimiter: zero amount"
    assert self.owner_balance[msg.sender] >= amount, "SpendingLimiter: insufficient balance"
    
    self.owner_balance[msg.sender] -= amount
    
    success: bool = extcall IERC20(self.usdc).transfer(msg.sender, amount)
    assert success, "SpendingLimiter: transfer failed"
    
    log FundsWithdrawn(owner=msg.sender, amount=amount)


# ═══════════════════════════════════════════════════════════════════════════════
# OWNER FUNCTIONS: AGENT AUTHORIZATION
# ═══════════════════════════════════════════════════════════════════════════════

@external
def authorize_agent(
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
    
    self.is_authorized[msg.sender][agent] = True
    self.per_tx_limit[msg.sender][agent] = per_tx_limit
    self.daily_limit[msg.sender][agent] = daily_limit
    self.total_limit[msg.sender][agent] = total_limit
    
    log AgentAuthorized(
        owner=msg.sender,
        agent=agent,
        per_tx_limit=per_tx_limit,
        daily_limit=daily_limit,
        total_limit=total_limit
    )


@external
def revoke_agent(agent: address):
    """
    @notice Revoke agent authorization
    @param agent The agent to revoke
    """
    self.is_authorized[msg.sender][agent] = False
    
    log AgentRevoked(owner=msg.sender, agent=agent)


@external
def update_limits(
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
    assert self.is_authorized[msg.sender][agent], "SpendingLimiter: not authorized"
    
    self.per_tx_limit[msg.sender][agent] = per_tx_limit
    self.daily_limit[msg.sender][agent] = daily_limit
    self.total_limit[msg.sender][agent] = total_limit
    
    log LimitsUpdated(
        owner=msg.sender,
        agent=agent,
        per_tx_limit=per_tx_limit,
        daily_limit=daily_limit,
        total_limit=total_limit
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
    assert self.is_authorized[owner][msg.sender], "SpendingLimiter: not authorized"
    assert amount > 0, "SpendingLimiter: zero amount"
    assert recipient != empty(address), "SpendingLimiter: zero recipient"
    
    # Check per-transaction limit
    per_tx: uint256 = self.per_tx_limit[owner][msg.sender]
    if per_tx > 0:
        assert amount <= per_tx, "SpendingLimiter: exceeds per-tx limit"
    
    # Reset daily spending if new day
    current_day: uint256 = block.timestamp // 86400
    if current_day > self.last_spending_day[owner][msg.sender]:
        self.daily_spent[owner][msg.sender] = 0
        self.last_spending_day[owner][msg.sender] = current_day
    
    # Check daily limit
    daily: uint256 = self.daily_limit[owner][msg.sender]
    if daily > 0:
        assert self.daily_spent[owner][msg.sender] + amount <= daily, "SpendingLimiter: exceeds daily limit"
    
    # Check total limit
    total: uint256 = self.total_limit[owner][msg.sender]
    if total > 0:
        assert self.total_spent[owner][msg.sender] + amount <= total, "SpendingLimiter: exceeds total limit"
    
    # Check owner balance
    assert self.owner_balance[owner] >= amount, "SpendingLimiter: insufficient balance"
    
    # Update tracking
    self.daily_spent[owner][msg.sender] += amount
    self.total_spent[owner][msg.sender] += amount
    self.owner_balance[owner] -= amount
    
    # Transfer
    success: bool = extcall IERC20(self.usdc).transfer(recipient, amount)
    assert success, "SpendingLimiter: transfer failed"
    
    log SpendingRecorded(owner=owner, agent=msg.sender, amount=amount, recipient=recipient)


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@external
@view
def can_spend(owner: address, agent: address, amount: uint256) -> bool:
    """
    @notice Check if agent can spend a given amount
    @param owner The owner
    @param agent The agent
    @param amount The amount to check
    @return True if the spend would succeed
    """
    if not self.is_authorized[owner][agent]:
        return False
    
    # Check per-tx limit
    per_tx: uint256 = self.per_tx_limit[owner][agent]
    if per_tx > 0 and amount > per_tx:
        return False
    
    # Check daily limit (considering potential reset)
    current_day: uint256 = block.timestamp // 86400
    daily_spent: uint256 = self.daily_spent[owner][agent]
    if current_day > self.last_spending_day[owner][agent]:
        daily_spent = 0
    
    daily: uint256 = self.daily_limit[owner][agent]
    if daily > 0 and daily_spent + amount > daily:
        return False
    
    # Check total limit
    total: uint256 = self.total_limit[owner][agent]
    if total > 0 and self.total_spent[owner][agent] + amount > total:
        return False
    
    # Check balance
    if self.owner_balance[owner] < amount:
        return False
    
    return True


@external
@view
def get_remaining_limits(owner: address, agent: address) -> (uint256, uint256, uint256):
    """
    @notice Get remaining spending limits for an agent
    @param owner The owner
    @param agent The agent
    @return Tuple of (remainingDaily, remainingTotal, owner_balance)
    """
    # Calculate remaining daily (considering potential reset)
    current_day: uint256 = block.timestamp // 86400
    daily_spent: uint256 = self.daily_spent[owner][agent]
    if current_day > self.last_spending_day[owner][agent]:
        daily_spent = 0
    
    daily: uint256 = self.daily_limit[owner][agent]
    remaining_daily: uint256 = 0
    if daily > 0:
        if daily > daily_spent:
            remaining_daily = daily - daily_spent
    else:
        remaining_daily = max_value(uint256)  # No limit
    
    # Calculate remaining total
    total: uint256 = self.total_limit[owner][agent]
    remaining_total: uint256 = 0
    if total > 0:
        if total > self.total_spent[owner][agent]:
            remaining_total = total - self.total_spent[owner][agent]
    else:
        remaining_total = max_value(uint256)  # No limit
    
    return (remaining_daily, remaining_total, self.owner_balance[owner])


@external
@view
def get_agent_limits(owner: address, agent: address) -> (uint256, uint256, uint256, bool):
    """
    @notice Get configured limits for an agent
    @param owner The owner
    @param agent The agent
    @return Tuple of (per_tx_limit, daily_limit, total_limit, is_authorized)
    """
    return (
        self.per_tx_limit[owner][agent],
        self.daily_limit[owner][agent],
        self.total_limit[owner][agent],
        self.is_authorized[owner][agent]
    )
