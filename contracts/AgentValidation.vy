# @version ^0.4.0

"""
@title AgentValidation - ERC-8004 Validation Registry (First Vyper Implementation)
@author Vyper Agentic Payments
@notice On-chain validation registry for verifying agent work quality
@dev This contract provides a generic interface for independent validation
     of agent work. It supports multiple validation methods.

AGENTIC PATTERN:
    This contract solves the "Is this work legitimate?" problem. When agents
    complete tasks (especially in escrow scenarios), there needs to be a way
    to verify the quality/correctness of their work. This registry supports:
    
    1. TRUSTED JUDGES: Human or AI validators with authority to approve/reject
    2. STAKED VALIDATORS: Validators who stake tokens, lose stake for bad validations
    3. CRYPTOGRAPHIC PROOFS: zkML proofs, TEE attestations, etc.
    
INTEGRATION WITH ESCROW:
    AgentEscrow.vy can query this contract to check if work has been validated
    before releasing payment. The flow:
    1. Agent completes task
    2. Validator (or client) requests validation
    3. Validator submits result (approved/rejected with evidence)
    4. Escrow checks validation status before releasing funds

VALIDATION LIFECYCLE:
    NONE (0) -> PENDING (1) -> APPROVED (2) or REJECTED (3)
    
See: https://eips.ethereum.org/EIPS/eip-8004
"""

# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACES
# ═══════════════════════════════════════════════════════════════════════════════

interface IAgentIdentity:
    def agentExists(tokenId: uint256) -> bool: view

# ═══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

event ValidationRequested:
    validationId: indexed(uint256)
    agentId: indexed(uint256)
    requester: indexed(address)
    taskHash: bytes32

event ValidationSubmitted:
    validationId: indexed(uint256)
    validator: indexed(address)
    approved: bool
    evidenceURI: String[256]

event ValidatorAdded:
    validator: indexed(address)
    validatorType: uint8

event ValidatorRemoved:
    validator: indexed(address)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Validation statuses
STATUS_NONE: constant(uint8) = 0
STATUS_PENDING: constant(uint8) = 1
STATUS_APPROVED: constant(uint8) = 2
STATUS_REJECTED: constant(uint8) = 3

# Validator types
VALIDATOR_TRUSTED_JUDGE: constant(uint8) = 1
VALIDATOR_STAKED: constant(uint8) = 2
VALIDATOR_CRYPTOGRAPHIC: constant(uint8) = 3

# ═══════════════════════════════════════════════════════════════════════════════
# STATE VARIABLES
# ═══════════════════════════════════════════════════════════════════════════════

# Reference to AgentIdentity contract
identityRegistry: public(address)

# Admin
admin: public(address)

# Validation counter
nextValidationId: public(uint256)

# Validation request storage
validationAgent: public(HashMap[uint256, uint256])       # validationId -> agentId
validationRequester: public(HashMap[uint256, address])   # validationId -> requester
validationTaskHash: public(HashMap[uint256, bytes32])    # validationId -> task hash
validationStatus: public(HashMap[uint256, uint8])        # validationId -> status
validationTimestamp: public(HashMap[uint256, uint256])   # validationId -> request timestamp
validationValidator: public(HashMap[uint256, address])   # validationId -> validator who submitted result
validationEvidence: public(HashMap[uint256, String[256]]) # validationId -> evidence URI

# Approved validators
isValidator: public(HashMap[address, bool])
validatorType: public(HashMap[address, uint8])

# Track validations per agent (for querying)
agentValidationCount: public(HashMap[uint256, uint256])

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTOR
# ═══════════════════════════════════════════════════════════════════════════════

@deploy
def __init__(identity_registry: address):
    """
    @notice Initialize the Validation Registry
    @param identity_registry Address of the AgentIdentity contract
    """
    assert identity_registry != empty(address), "AgentValidation: zero address"
    self.identityRegistry = identity_registry
    self.admin = msg.sender
    self.nextValidationId = 1


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@external
def addValidator(validator: address, validator_type: uint8):
    """
    @notice Add an approved validator
    @param validator The validator address
    @param validator_type Type: 1=Trusted Judge, 2=Staked, 3=Cryptographic
    """
    assert msg.sender == self.admin, "AgentValidation: not admin"
    assert validator != empty(address), "AgentValidation: zero address"
    assert validator_type >= 1 and validator_type <= 3, "AgentValidation: invalid type"
    
    self.isValidator[validator] = True
    self.validatorType[validator] = validator_type
    
    log ValidatorAdded(validator=validator, validatorType=validator_type)


@external
def removeValidator(validator: address):
    """
    @notice Remove a validator
    @param validator The validator address to remove
    """
    assert msg.sender == self.admin, "AgentValidation: not admin"
    
    self.isValidator[validator] = False
    self.validatorType[validator] = 0
    
    log ValidatorRemoved(validator=validator)


@external
def transferAdmin(new_admin: address):
    """
    @notice Transfer admin role
    @param new_admin The new admin address
    """
    assert msg.sender == self.admin, "AgentValidation: not admin"
    assert new_admin != empty(address), "AgentValidation: zero address"
    self.admin = new_admin


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION REQUEST
# ═══════════════════════════════════════════════════════════════════════════════

@external
def requestValidation(agentId: uint256, taskHash: bytes32) -> uint256:
    """
    @notice Request validation for an agent's completed task
    @param agentId The agent whose work needs validation
    @param taskHash Hash identifying the task/work to validate
    @return The validation request ID
    @dev Anyone can request validation. The taskHash should uniquely identify
         the work being validated (could be IPFS hash of work, commitment, etc.)
    """
    assert self._agentExists(agentId), "AgentValidation: agent not found"
    assert taskHash != empty(bytes32), "AgentValidation: empty task hash"
    
    validationId: uint256 = self.nextValidationId
    self.nextValidationId = validationId + 1
    
    self.validationAgent[validationId] = agentId
    self.validationRequester[validationId] = msg.sender
    self.validationTaskHash[validationId] = taskHash
    self.validationStatus[validationId] = STATUS_PENDING
    self.validationTimestamp[validationId] = block.timestamp
    
    self.agentValidationCount[agentId] += 1
    
    log ValidationRequested(
        validationId=validationId,
        agentId=agentId,
        requester=msg.sender,
        taskHash=taskHash
    )
    
    return validationId


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION SUBMISSION
# ═══════════════════════════════════════════════════════════════════════════════

@external
def submitValidation(validationId: uint256, approved: bool, evidenceURI: String[256]):
    """
    @notice Submit a validation result
    @param validationId The validation request ID
    @param approved True if work is approved, False if rejected
    @param evidenceURI URI pointing to validation evidence/reasoning
    @dev Only approved validators can submit results.
         Validation can only be submitted for pending requests.
    """
    assert self.isValidator[msg.sender], "AgentValidation: not validator"
    assert validationId > 0 and validationId < self.nextValidationId, "AgentValidation: invalid id"
    assert self.validationStatus[validationId] == STATUS_PENDING, "AgentValidation: not pending"
    
    if approved:
        self.validationStatus[validationId] = STATUS_APPROVED
    else:
        self.validationStatus[validationId] = STATUS_REJECTED
    
    self.validationValidator[validationId] = msg.sender
    self.validationEvidence[validationId] = evidenceURI
    
    log ValidationSubmitted(
        validationId=validationId,
        validator=msg.sender,
        approved=approved,
        evidenceURI=evidenceURI
    )


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@external
@view
def getValidationStatus(validationId: uint256) -> uint8:
    """
    @notice Get the status of a validation request
    @param validationId The validation ID
    @return Status: 0=None, 1=Pending, 2=Approved, 3=Rejected
    """
    return self.validationStatus[validationId]


@external
@view
def isValidationApproved(validationId: uint256) -> bool:
    """
    @notice Check if a validation was approved
    @param validationId The validation ID
    @return True if approved
    """
    return self.validationStatus[validationId] == STATUS_APPROVED


@external
@view
def getValidationDetails(validationId: uint256) -> (uint256, address, bytes32, uint8, address, String[256]):
    """
    @notice Get full details of a validation request
    @param validationId The validation ID
    @return Tuple of (agentId, requester, taskHash, status, validator, evidenceURI)
    """
    assert validationId > 0 and validationId < self.nextValidationId, "AgentValidation: invalid id"
    
    return (
        self.validationAgent[validationId],
        self.validationRequester[validationId],
        self.validationTaskHash[validationId],
        self.validationStatus[validationId],
        self.validationValidator[validationId],
        self.validationEvidence[validationId]
    )


@external
@view
def getAgentValidationCount(agentId: uint256) -> uint256:
    """
    @notice Get the number of validation requests for an agent
    @param agentId The agent ID
    @return The count of validation requests
    """
    return self.agentValidationCount[agentId]


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@internal
@view
def _agentExists(agentId: uint256) -> bool:
    """
    @notice Check if an agent exists
    @param agentId The agent ID
    @return True if the agent exists
    """
    return staticcall IAgentIdentity(self.identityRegistry).agentExists(agentId)
