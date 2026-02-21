# @version ^0.4.0

"""
@title AgentEscrow - Escrow for Agent-to-Agent Task Payments
@author Vyper Agentic Payments
@notice Secure escrow system for agent task payments with dispute resolution
@dev This contract holds USDC in escrow while agents complete tasks.

AGENTIC PATTERN:
    This contract solves the "How do I trust this agent will pay me?" problem.
    In agent-to-agent commerce:
    
    1. Agent A (poster) wants work done, locks USDC in escrow
    2. Agent B (worker) claims the task and does the work
    3. Three resolution paths:
       a) Agent A approves → funds release to Agent B
       b) Timeout expires → funds refund to Agent A (poster)
       c) Dispute → requires validation from AgentValidation.vy
    
INTEGRATION WITH OTHER CONTRACTS:
    - AgentIdentity.vy: Verifies agent IDs are valid
    - AgentReputation.vy: Can trigger reputation feedback on completion
    - AgentValidation.vy: Provides dispute resolution via validators

TASK LIFECYCLE:
    OPEN (0) → CLAIMED (1) → COMPLETED (2) or DISPUTED (3) or CANCELLED (4)
    
USDC on Arc Testnet: 0x3600000000000000000000000000000000000000
"""

# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACES
# ═══════════════════════════════════════════════════════════════════════════════

interface IERC20:
    def transfer(to: address, amount: uint256) -> bool: nonpayable
    def transferFrom(sender: address, recipient: address, amount: uint256) -> bool: nonpayable
    def balanceOf(account: address) -> uint256: view

interface IAgentIdentity:
    def agentExists(tokenId: uint256) -> bool: view
    def ownerOf(tokenId: uint256) -> address: view

# ═══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

event TaskCreated:
    taskId: indexed(uint256)
    poster: indexed(address)
    posterAgentId: uint256
    amount: uint256
    deadline: uint256

event TaskClaimed:
    taskId: indexed(uint256)
    worker: indexed(address)
    workerAgentId: uint256

event TaskCompleted:
    taskId: indexed(uint256)
    worker: indexed(address)
    amount: uint256

event TaskCancelled:
    taskId: indexed(uint256)
    poster: indexed(address)
    amount: uint256

event TaskDisputed:
    taskId: indexed(uint256)
    disputer: indexed(address)

event DisputeResolved:
    taskId: indexed(uint256)
    winner: indexed(address)
    amount: uint256

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Task statuses
STATUS_OPEN: constant(uint8) = 0
STATUS_CLAIMED: constant(uint8) = 1
STATUS_COMPLETED: constant(uint8) = 2
STATUS_DISPUTED: constant(uint8) = 3
STATUS_CANCELLED: constant(uint8) = 4

# Minimum time before auto-release (7 days in seconds)
MIN_DEADLINE: constant(uint256) = 86400  # 1 day minimum
DEFAULT_DEADLINE: constant(uint256) = 604800  # 7 days

# ═══════════════════════════════════════════════════════════════════════════════
# STATE VARIABLES
# ═══════════════════════════════════════════════════════════════════════════════

# External contract references
usdc: public(address)
identityRegistry: public(address)

# Admin for dispute resolution
admin: public(address)

# Task counter
nextTaskId: public(uint256)

# Task storage
taskPoster: public(HashMap[uint256, address])
taskPosterAgentId: public(HashMap[uint256, uint256])
taskWorker: public(HashMap[uint256, address])
taskWorkerAgentId: public(HashMap[uint256, uint256])
taskAmount: public(HashMap[uint256, uint256])
taskStatus: public(HashMap[uint256, uint8])
taskDeadline: public(HashMap[uint256, uint256])
taskCreatedAt: public(HashMap[uint256, uint256])
taskClaimedAt: public(HashMap[uint256, uint256])
taskDescriptionHash: public(HashMap[uint256, bytes32])

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTOR
# ═══════════════════════════════════════════════════════════════════════════════

@deploy
def __init__(usdc_address: address, identity_registry: address):
    """
    @notice Initialize the escrow contract
    @param usdc_address USDC token address (0x3600... on Arc Testnet)
    @param identity_registry AgentIdentity contract address
    """
    assert usdc_address != empty(address), "AgentEscrow: zero USDC address"
    assert identity_registry != empty(address), "AgentEscrow: zero identity address"
    
    self.usdc = usdc_address
    self.identityRegistry = identity_registry
    self.admin = msg.sender
    self.nextTaskId = 1


# ═══════════════════════════════════════════════════════════════════════════════
# TASK CREATION
# ═══════════════════════════════════════════════════════════════════════════════

@external
def createTask(
    posterAgentId: uint256,
    amount: uint256,
    descriptionHash: bytes32,
    deadline: uint256
) -> uint256:
    """
    @notice Create a new task with USDC locked in escrow
    @param posterAgentId The agent ID of the task poster
    @param amount USDC amount to lock (6 decimals)
    @param descriptionHash Hash of task description (IPFS hash)
    @param deadline Seconds from now until auto-release (0 for default 7 days)
    @return The new task ID
    @dev Caller must have approved this contract to spend `amount` USDC
    """
    assert amount > 0, "AgentEscrow: zero amount"
    assert self._agentExists(posterAgentId), "AgentEscrow: agent not found"
    assert self._isAgentOwner(posterAgentId, msg.sender), "AgentEscrow: not agent owner"
    
    # Calculate deadline
    actual_deadline: uint256 = deadline
    if actual_deadline == 0:
        actual_deadline = DEFAULT_DEADLINE
    assert actual_deadline >= MIN_DEADLINE, "AgentEscrow: deadline too short"
    
    # Transfer USDC to escrow
    success: bool = extcall IERC20(self.usdc).transferFrom(msg.sender, self, amount)
    assert success, "AgentEscrow: transfer failed"
    
    # Create task
    taskId: uint256 = self.nextTaskId
    self.nextTaskId = taskId + 1
    
    self.taskPoster[taskId] = msg.sender
    self.taskPosterAgentId[taskId] = posterAgentId
    self.taskAmount[taskId] = amount
    self.taskStatus[taskId] = STATUS_OPEN
    self.taskDeadline[taskId] = block.timestamp + actual_deadline
    self.taskCreatedAt[taskId] = block.timestamp
    self.taskDescriptionHash[taskId] = descriptionHash
    
    log TaskCreated(
        taskId=taskId,
        poster=msg.sender,
        posterAgentId=posterAgentId,
        amount=amount,
        deadline=block.timestamp + actual_deadline
    )
    
    return taskId


# ═══════════════════════════════════════════════════════════════════════════════
# TASK CLAIMING
# ═══════════════════════════════════════════════════════════════════════════════

@external
def claimTask(taskId: uint256, workerAgentId: uint256):
    """
    @notice Claim an open task as a worker
    @param taskId The task to claim
    @param workerAgentId The agent ID of the worker
    """
    assert taskId > 0 and taskId < self.nextTaskId, "AgentEscrow: invalid task"
    assert self.taskStatus[taskId] == STATUS_OPEN, "AgentEscrow: task not open"
    assert self._agentExists(workerAgentId), "AgentEscrow: agent not found"
    assert self._isAgentOwner(workerAgentId, msg.sender), "AgentEscrow: not agent owner"
    assert workerAgentId != self.taskPosterAgentId[taskId], "AgentEscrow: cannot claim own task"
    
    self.taskWorker[taskId] = msg.sender
    self.taskWorkerAgentId[taskId] = workerAgentId
    self.taskStatus[taskId] = STATUS_CLAIMED
    self.taskClaimedAt[taskId] = block.timestamp
    
    log TaskClaimed(taskId=taskId, worker=msg.sender, workerAgentId=workerAgentId)


# ═══════════════════════════════════════════════════════════════════════════════
# TASK COMPLETION
# ═══════════════════════════════════════════════════════════════════════════════

@external
def approveCompletion(taskId: uint256):
    """
    @notice Poster approves task completion, releasing funds to worker
    @param taskId The task to approve
    @dev Only the poster can approve. Releases full amount to worker.
    """
    assert taskId > 0 and taskId < self.nextTaskId, "AgentEscrow: invalid task"
    assert self.taskStatus[taskId] == STATUS_CLAIMED, "AgentEscrow: task not claimed"
    assert msg.sender == self.taskPoster[taskId], "AgentEscrow: not poster"
    
    amount: uint256 = self.taskAmount[taskId]
    worker: address = self.taskWorker[taskId]
    
    self.taskStatus[taskId] = STATUS_COMPLETED
    self.taskAmount[taskId] = 0
    
    success: bool = extcall IERC20(self.usdc).transfer(worker, amount)
    assert success, "AgentEscrow: transfer failed"
    
    log TaskCompleted(taskId=taskId, worker=worker, amount=amount)


@external
def refundAfterDeadline(taskId: uint256):
    """
    @notice Refund poster after deadline if worker has not delivered
    @param taskId The task to refund
    @dev Only the poster can call. Only works if deadline has passed.
    """
    assert taskId > 0 and taskId < self.nextTaskId, "AgentEscrow: invalid task"
    assert self.taskStatus[taskId] == STATUS_CLAIMED, "AgentEscrow: task not claimed"
    assert msg.sender == self.taskPoster[taskId], "AgentEscrow: not poster"
    assert block.timestamp >= self.taskDeadline[taskId], "AgentEscrow: deadline not reached"

    amount: uint256 = self.taskAmount[taskId]

    self.taskStatus[taskId] = STATUS_CANCELLED
    self.taskAmount[taskId] = 0

    success: bool = extcall IERC20(self.usdc).transfer(msg.sender, amount)
    assert success, "AgentEscrow: transfer failed"

    log TaskCancelled(taskId=taskId, poster=msg.sender, amount=amount)


# ═══════════════════════════════════════════════════════════════════════════════
# CANCELLATION
# ═══════════════════════════════════════════════════════════════════════════════

@external
def cancelTask(taskId: uint256):
    """
    @notice Cancel an open task and return funds to poster
    @param taskId The task to cancel
    @dev Only works for OPEN tasks (not yet claimed)
    """
    assert taskId > 0 and taskId < self.nextTaskId, "AgentEscrow: invalid task"
    assert self.taskStatus[taskId] == STATUS_OPEN, "AgentEscrow: task not open"
    assert msg.sender == self.taskPoster[taskId], "AgentEscrow: not poster"
    
    amount: uint256 = self.taskAmount[taskId]
    
    self.taskStatus[taskId] = STATUS_CANCELLED
    self.taskAmount[taskId] = 0
    
    success: bool = extcall IERC20(self.usdc).transfer(msg.sender, amount)
    assert success, "AgentEscrow: transfer failed"
    
    log TaskCancelled(taskId=taskId, poster=msg.sender, amount=amount)


# ═══════════════════════════════════════════════════════════════════════════════
# DISPUTE RESOLUTION
# ═══════════════════════════════════════════════════════════════════════════════

@external
def raiseDispute(taskId: uint256):
    """
    @notice Raise a dispute on a claimed task
    @param taskId The task to dispute
    @dev Either poster or worker can raise a dispute
    """
    assert taskId > 0 and taskId < self.nextTaskId, "AgentEscrow: invalid task"
    assert self.taskStatus[taskId] == STATUS_CLAIMED, "AgentEscrow: task not claimed"
    assert msg.sender == self.taskPoster[taskId] or msg.sender == self.taskWorker[taskId], "AgentEscrow: not party"
    
    self.taskStatus[taskId] = STATUS_DISPUTED
    
    log TaskDisputed(taskId=taskId, disputer=msg.sender)


@external
def resolveDispute(taskId: uint256, workerWins: bool):
    """
    @notice Admin resolves a dispute
    @param taskId The disputed task
    @param workerWins True to release funds to worker, False to refund poster
    @dev Only admin can resolve disputes.
         Production integration: replace admin-only resolution with
         AgentValidation.isValidationApproved() queries to enable
         decentralized dispute resolution via registered validators.
    """
    assert msg.sender == self.admin, "AgentEscrow: not admin"
    assert taskId > 0 and taskId < self.nextTaskId, "AgentEscrow: invalid task"
    assert self.taskStatus[taskId] == STATUS_DISPUTED, "AgentEscrow: not disputed"
    
    amount: uint256 = self.taskAmount[taskId]
    winner: address = empty(address)
    
    if workerWins:
        winner = self.taskWorker[taskId]
    else:
        winner = self.taskPoster[taskId]
    
    self.taskStatus[taskId] = STATUS_COMPLETED
    self.taskAmount[taskId] = 0
    
    success: bool = extcall IERC20(self.usdc).transfer(winner, amount)
    assert success, "AgentEscrow: transfer failed"
    
    log DisputeResolved(taskId=taskId, winner=winner, amount=amount)


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@external
def transferAdmin(new_admin: address):
    """
    @notice Transfer admin role
    @param new_admin The new admin address
    """
    assert msg.sender == self.admin, "AgentEscrow: not admin"
    assert new_admin != empty(address), "AgentEscrow: zero address"
    self.admin = new_admin


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@external
@view
def getTaskDetails(taskId: uint256) -> (address, uint256, address, uint256, uint256, uint8, uint256):
    """
    @notice Get all task details
    @param taskId The task ID
    @return Tuple of (poster, posterAgentId, worker, workerAgentId, amount, status, deadline)
    """
    assert taskId > 0 and taskId < self.nextTaskId, "AgentEscrow: invalid task"
    
    return (
        self.taskPoster[taskId],
        self.taskPosterAgentId[taskId],
        self.taskWorker[taskId],
        self.taskWorkerAgentId[taskId],
        self.taskAmount[taskId],
        self.taskStatus[taskId],
        self.taskDeadline[taskId]
    )


@external
@view
def isTaskOpen(taskId: uint256) -> bool:
    """
    @notice Check if a task is open for claiming
    @param taskId The task ID
    @return True if open
    """
    if taskId == 0 or taskId >= self.nextTaskId:
        return False
    return self.taskStatus[taskId] == STATUS_OPEN


@external
@view
def canRefundAfterDeadline(taskId: uint256) -> bool:
    """
    @notice Check if poster can reclaim funds after deadline
    @param taskId The task ID
    @return True if refundable
    """
    if taskId == 0 or taskId >= self.nextTaskId:
        return False
    if self.taskStatus[taskId] != STATUS_CLAIMED:
        return False
    return block.timestamp >= self.taskDeadline[taskId]


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@internal
@view
def _agentExists(agentId: uint256) -> bool:
    """Check if an agent exists."""
    return staticcall IAgentIdentity(self.identityRegistry).agentExists(agentId)


@internal
@view
def _isAgentOwner(agentId: uint256, account: address) -> bool:
    """Check if account owns the agent."""
    owner: address = staticcall IAgentIdentity(self.identityRegistry).ownerOf(agentId)
    return owner == account
