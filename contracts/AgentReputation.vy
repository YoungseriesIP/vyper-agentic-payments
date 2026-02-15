# @version ^0.4.0

"""
@title AgentReputation - ERC-8004 Reputation Registry (First Vyper Implementation)
@author Vyper Agentic Payments
@notice On-chain reputation registry for AI agents following ERC-8004
@dev This contract tracks agent reputation through authorized feedback.
     
AGENTIC PATTERN:
    This contract solves the "Can I trust this agent?" problem. In agentic
    commerce, agents need verifiable reputation that:
    - Is tamper-proof (on-chain, not in a centralized database)
    - Is portable (follows the agent across platforms)
    - Is linked to real economic activity (proof-of-payment from x402)
    
INTEGRATION WITH x402 BATCHING SDK:
    When a client pays an agent via the x402 Batching SDK:
    1. Client calls gateway.pay() → receives PayResult with 'transaction' field
    2. This transaction hash serves as proof-of-payment
    3. Client submits feedback to this contract with the hash as proofOfPayment
    4. Future clients can verify the feedback is backed by real economic activity
    
    # ASSUMPTION: The 'transaction' field from PayResult (burn intent hash) is
    # suitable as on-chain proof. This may be a settlement tx hash instead.
    # TODO: Verify with Circle team the exact format of this proof.

SCORING:
    - Scores are 0-100 (percentage scale)
    - On-chain aggregation: sum of scores, count of feedback
    - Average = totalScore / feedbackCount (computed off-chain or via view)
    - Tiers: Unrated (0), Bronze (1-25), Silver (26-50), Gold (51-75), Platinum (76-100)

See: https://eips.ethereum.org/EIPS/eip-8004
"""

# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACES
# ═══════════════════════════════════════════════════════════════════════════════

interface IAgentIdentity:
    def ownerOf(tokenId: uint256) -> address: view
    def agentExists(tokenId: uint256) -> bool: view

# ═══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

event FeedbackSubmitted:
    agentId: indexed(uint256)
    client: indexed(address)
    score: uint8
    proofOfPayment: bytes32
    feedbackId: uint256

event InteractionRecorded:
    agentId: indexed(uint256)
    client: indexed(address)
    timestamp: uint256

event IdentityRegistryUpdated:
    oldRegistry: address
    newRegistry: address

# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTS (using separate mappings in Vyper)
# ═══════════════════════════════════════════════════════════════════════════════

# Feedback is stored across multiple mappings keyed by feedbackId
# feedbackAgent[id] = agentId
# feedbackClient[id] = client address
# feedbackScore[id] = score (0-100)
# feedbackTimestamp[id] = block.timestamp
# feedbackProof[id] = proof of payment hash
# feedbackTags[id] = encoded tags (as bytes32)

# ═══════════════════════════════════════════════════════════════════════════════
# STATE VARIABLES
# ═══════════════════════════════════════════════════════════════════════════════

# Reference to AgentIdentity contract for agent verification
identityRegistry: public(address)

# Admin who can update the identity registry reference
admin: public(address)

# Interaction tracking: agentId -> client -> has interacted
# Only clients who have interacted can submit feedback
hasInteracted: public(HashMap[uint256, HashMap[address, bool]])

# Aggregated scores per agent
totalScore: public(HashMap[uint256, uint256])  # Sum of all scores
feedbackCount: public(HashMap[uint256, uint256])  # Number of feedbacks

# Feedback storage (by ID)
nextFeedbackId: public(uint256)
feedbackAgent: HashMap[uint256, uint256]
feedbackClient: HashMap[uint256, address]
feedbackScore: HashMap[uint256, uint8]
feedbackTimestamp: HashMap[uint256, uint256]
feedbackProof: HashMap[uint256, bytes32]

# Track which agents a client has given feedback to (prevent duplicates)
clientFeedbackGiven: HashMap[address, HashMap[uint256, bool]]

# Constants for reputation tiers
TIER_UNRATED: constant(uint8) = 0
TIER_BRONZE: constant(uint8) = 1
TIER_SILVER: constant(uint8) = 2
TIER_GOLD: constant(uint8) = 3
TIER_PLATINUM: constant(uint8) = 4

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTOR
# ═══════════════════════════════════════════════════════════════════════════════

@deploy
def __init__(identity_registry: address):
    """
    @notice Initialize the Agent Reputation Registry
    @param identity_registry Address of the AgentIdentity contract
    """
    assert identity_registry != empty(address), "AgentReputation: zero address"
    self.identityRegistry = identity_registry
    self.admin = msg.sender
    self.nextFeedbackId = 1


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@external
def updateIdentityRegistry(new_registry: address):
    """
    @notice Update the reference to the AgentIdentity contract
    @param new_registry The new AgentIdentity contract address
    @dev Only admin can call this
    """
    assert msg.sender == self.admin, "AgentReputation: not admin"
    assert new_registry != empty(address), "AgentReputation: zero address"
    
    old_registry: address = self.identityRegistry
    self.identityRegistry = new_registry
    
    log IdentityRegistryUpdated(old_registry, new_registry)


@external
def transferAdmin(new_admin: address):
    """
    @notice Transfer admin role to a new address
    @param new_admin The new admin address
    """
    assert msg.sender == self.admin, "AgentReputation: not admin"
    assert new_admin != empty(address), "AgentReputation: zero address"
    self.admin = new_admin


# ═══════════════════════════════════════════════════════════════════════════════
# INTERACTION RECORDING
# ═══════════════════════════════════════════════════════════════════════════════

@external
def recordInteraction(agentId: uint256, client: address):
    """
    @notice Record that a client has interacted with an agent
    @param agentId The agent ID from AgentIdentity
    @param client The client address that interacted
    @dev This should be called by the agent's service or a trusted relayer
         after a successful x402 payment. In production, you might want
         to restrict who can call this (e.g., only the agent owner).
         
    For hackathon purposes, we keep it permissionless but in production:
    - Could require msg.sender == agent owner
    - Could require a signed message from the agent
    - Could integrate with a trusted oracle
    """
    # Verify agent exists
    assert self._agentExists(agentId), "AgentReputation: agent not found"
    assert client != empty(address), "AgentReputation: zero address"
    
    # Record the interaction
    self.hasInteracted[agentId][client] = True
    
    log InteractionRecorded(agentId, client, block.timestamp)


@external
def recordInteractionBySelf(agentId: uint256):
    """
    @notice Client records their own interaction (for testing/demo)
    @param agentId The agent ID they interacted with
    @dev In production, this would need proper authorization
    """
    assert self._agentExists(agentId), "AgentReputation: agent not found"
    
    self.hasInteracted[agentId][msg.sender] = True
    
    log InteractionRecorded(agentId, msg.sender, block.timestamp)


# ═══════════════════════════════════════════════════════════════════════════════
# FEEDBACK SUBMISSION
# ═══════════════════════════════════════════════════════════════════════════════

@external
def submitFeedback(
    agentId: uint256,
    score: uint8,
    proofOfPayment: bytes32
) -> uint256:
    """
    @notice Submit reputation feedback for an agent
    @param agentId The agent ID to rate
    @param score Rating from 0 to 100
    @param proofOfPayment Transaction hash from x402 payment (or empty for demo)
    @return The feedback ID
    @dev Only clients who have interacted with the agent can submit feedback.
         Each client can only submit one feedback per agent.
         
    INTEGRATION WITH x402:
        The proofOfPayment should be the transaction hash returned by
        gateway.pay() in the PayResult. This links reputation to real
        economic activity on Circle Gateway.
    """
    # Validate inputs
    assert self._agentExists(agentId), "AgentReputation: agent not found"
    assert score <= 100, "AgentReputation: score must be 0-100"
    
    # Verify client has interacted with this agent
    assert self.hasInteracted[agentId][msg.sender], "AgentReputation: no interaction"
    
    # Check client hasn't already given feedback for this agent
    assert not self.clientFeedbackGiven[msg.sender][agentId], "AgentReputation: already rated"
    
    # Create feedback record
    feedbackId: uint256 = self.nextFeedbackId
    self.nextFeedbackId = feedbackId + 1
    
    self.feedbackAgent[feedbackId] = agentId
    self.feedbackClient[feedbackId] = msg.sender
    self.feedbackScore[feedbackId] = score
    self.feedbackTimestamp[feedbackId] = block.timestamp
    self.feedbackProof[feedbackId] = proofOfPayment
    
    # Update aggregates
    self.totalScore[agentId] += convert(score, uint256)
    self.feedbackCount[agentId] += 1
    
    # Mark that this client has given feedback
    self.clientFeedbackGiven[msg.sender][agentId] = True
    
    log FeedbackSubmitted(agentId, msg.sender, score, proofOfPayment, feedbackId)
    
    return feedbackId


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW FUNCTIONS: REPUTATION QUERIES
# ═══════════════════════════════════════════════════════════════════════════════

@external
@view
def getAverageScore(agentId: uint256) -> uint256:
    """
    @notice Get the average reputation score for an agent
    @param agentId The agent ID
    @return Average score (0-100), multiplied by 100 for precision
            e.g., 7550 = 75.50 average score
    @dev Returns 0 if no feedback exists
    """
    count: uint256 = self.feedbackCount[agentId]
    if count == 0:
        return 0
    
    # Multiply by 100 first for precision (gives us 2 decimal places)
    return (self.totalScore[agentId] * 100) // count


@external
@view
def getTotalFeedbackCount(agentId: uint256) -> uint256:
    """
    @notice Get the total number of feedback entries for an agent
    @param agentId The agent ID
    @return The count of feedback entries
    """
    return self.feedbackCount[agentId]


@external
@view
def getReputationTier(agentId: uint256) -> uint8:
    """
    @notice Get the reputation tier for an agent
    @param agentId The agent ID
    @return Tier: 0=Unrated, 1=Bronze, 2=Silver, 3=Gold, 4=Platinum
    """
    count: uint256 = self.feedbackCount[agentId]
    if count == 0:
        return TIER_UNRATED
    
    avg: uint256 = self.totalScore[agentId] // count
    
    if avg <= 25:
        return TIER_BRONZE
    elif avg <= 50:
        return TIER_SILVER
    elif avg <= 75:
        return TIER_GOLD
    else:
        return TIER_PLATINUM


@external
@view
def getFeedback(feedbackId: uint256) -> (uint256, address, uint8, uint256, bytes32):
    """
    @notice Get details of a specific feedback entry
    @param feedbackId The feedback ID
    @return Tuple of (agentId, client, score, timestamp, proofOfPayment)
    """
    assert feedbackId > 0 and feedbackId < self.nextFeedbackId, "AgentReputation: invalid id"
    
    return (
        self.feedbackAgent[feedbackId],
        self.feedbackClient[feedbackId],
        self.feedbackScore[feedbackId],
        self.feedbackTimestamp[feedbackId],
        self.feedbackProof[feedbackId]
    )


@external
@view
def hasClientInteracted(agentId: uint256, client: address) -> bool:
    """
    @notice Check if a client has interacted with an agent
    @param agentId The agent ID
    @param client The client address to check
    @return True if the client has verified interaction
    """
    return self.hasInteracted[agentId][client]


@external
@view
def hasClientRated(agentId: uint256, client: address) -> bool:
    """
    @notice Check if a client has already rated an agent
    @param agentId The agent ID
    @param client The client address
    @return True if already rated
    """
    return self.clientFeedbackGiven[client][agentId]


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@internal
@view
def _agentExists(agentId: uint256) -> bool:
    """
    @notice Check if an agent exists in the identity registry
    @param agentId The agent ID to check
    @return True if the agent exists
    """
    return staticcall IAgentIdentity(self.identityRegistry).agentExists(agentId)
