# @version ^0.4.0

"""
@title AgentIdentity - ERC-8004 Identity Registry (First Vyper Implementation)
@author Vyper Agentic Payments
@notice On-chain identity registry for autonomous AI agents following ERC-8004
@dev This is the FIRST Vyper implementation of the ERC-8004 standard.
     Each agent gets a portable, censorship-resistant identity as an ERC-721 NFT.
     The tokenURI resolves to a registration JSON containing:
     - name, description, image
     - services array (A2A, MCP, web endpoints)
     - x402Support: true/false (for Circle x402 Batching SDK compatibility)
     - active: true/false

AGENTIC PATTERN:
    This contract solves the "Who is this agent?" problem. Before an agent can
    participate in agentic commerce (paying for services, earning reputation),
    it needs a verifiable on-chain identity. This identity is:
    - Portable: The NFT can move between wallets/owners
    - Composable: Other contracts can query agent metadata
    - Decentralized: No central authority controls registration
    
INTEGRATION WITH x402:
    The registration JSON can include x402Support=true to indicate the agent
    supports gasless micropayments via Circle's x402 Batching SDK. Discovery
    services can filter for x402-compatible agents.

See: https://eips.ethereum.org/EIPS/eip-8004
"""

# ═══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    tokenId: indexed(uint256)

event Approval:
    owner: indexed(address)
    approved: indexed(address)
    tokenId: indexed(uint256)

event ApprovalForAll:
    owner: indexed(address)
    operator: indexed(address)
    approved: bool

event AgentRegistered:
    agentId: indexed(uint256)
    owner: indexed(address)
    tokenURI: String[512]

event AgentUpdated:
    agentId: indexed(uint256)
    newTokenURI: String[512]

event AgentStatusChanged:
    agentId: indexed(uint256)
    active: bool

# ═══════════════════════════════════════════════════════════════════════════════
# STATE VARIABLES
# ═══════════════════════════════════════════════════════════════════════════════

# ERC-721 Core State
name: public(String[64])
symbol: public(String[32])

# Token ownership: tokenId -> owner
owners: HashMap[uint256, address]

# Owner balances: address -> count
balances: HashMap[address, uint256]

# Token approvals: tokenId -> approved address
tokenApprovals: HashMap[uint256, address]

# Operator approvals: owner -> operator -> approved
operatorApprovals: HashMap[address, HashMap[address, bool]]

# ERC-8004 Extensions
# Token URIs: tokenId -> URI string (points to registration JSON)
tokenURIs: HashMap[uint256, String[512]]

# Agent active status: tokenId -> is active
agentActive: HashMap[uint256, bool]

# Counter for token IDs (also serves as total agent count)
nextTokenId: public(uint256)

# ERC-165 interface IDs
IERC165_INTERFACE_ID: constant(bytes4) = 0x01ffc9a7
IERC721_INTERFACE_ID: constant(bytes4) = 0x80ac58cd
IERC721_METADATA_INTERFACE_ID: constant(bytes4) = 0x5b5e139f
IERC721_RECEIVER_SELECTOR: constant(bytes4) = 0x150b7a02

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTOR
# ═══════════════════════════════════════════════════════════════════════════════

@deploy
def __init__():
    """
    @notice Initialize the Agent Identity Registry
    """
    self.name = "Agent Identity Registry"
    self.symbol = "AGENT"
    self.nextTokenId = 1  # Start from 1, 0 is reserved as "no agent"


# ═══════════════════════════════════════════════════════════════════════════════
# ERC-165: INTERFACE SUPPORT
# ═══════════════════════════════════════════════════════════════════════════════

@external
@view
def supportsInterface(interfaceId: bytes4) -> bool:
    """
    @notice Query if a contract implements an interface
    @param interfaceId The interface identifier
    @return True if the interface is supported
    """
    return interfaceId in [
        IERC165_INTERFACE_ID,
        IERC721_INTERFACE_ID,
        IERC721_METADATA_INTERFACE_ID
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# ERC-721: CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@external
@view
def balanceOf(owner: address) -> uint256:
    """
    @notice Count all agents owned by an address
    @param owner The address to query
    @return The number of agents owned
    """
    assert owner != empty(address), "ERC721: zero address"
    return self.balances[owner]


@external
@view
def ownerOf(tokenId: uint256) -> address:
    """
    @notice Get the owner of an agent
    @param tokenId The agent ID
    @return The owner address
    """
    owner: address = self.owners[tokenId]
    assert owner != empty(address), "ERC721: nonexistent token"
    return owner


@external
@view
def getApproved(tokenId: uint256) -> address:
    """
    @notice Get the approved address for an agent
    @param tokenId The agent ID
    @return The approved address (or zero if none)
    """
    assert self.owners[tokenId] != empty(address), "ERC721: nonexistent token"
    return self.tokenApprovals[tokenId]


@external
@view
def isApprovedForAll(owner: address, operator: address) -> bool:
    """
    @notice Check if an operator is approved for all of owner's agents
    @param owner The owner address
    @param operator The operator address
    @return True if approved for all
    """
    return self.operatorApprovals[owner][operator]


@external
def approve(to: address, tokenId: uint256):
    """
    @notice Approve an address to transfer an agent
    @param to The address to approve
    @param tokenId The agent ID
    """
    owner: address = self.owners[tokenId]
    assert owner != empty(address), "ERC721: nonexistent token"
    assert msg.sender == owner or self.operatorApprovals[owner][msg.sender], "ERC721: not authorized"
    
    self.tokenApprovals[tokenId] = to
    log Approval(owner, to, tokenId)


@external
def setApprovalForAll(operator: address, approved: bool):
    """
    @notice Set or revoke operator approval for all of caller's agents
    @param operator The operator address
    @param approved True to approve, false to revoke
    """
    assert operator != msg.sender, "ERC721: approve to caller"
    self.operatorApprovals[msg.sender][operator] = approved
    log ApprovalForAll(msg.sender, operator, approved)


@external
def transferFrom(from_addr: address, to: address, tokenId: uint256):
    """
    @notice Transfer an agent from one address to another
    @param from_addr The current owner
    @param to The new owner
    @param tokenId The agent ID
    """
    self._transfer(from_addr, to, tokenId)


@external
def safeTransferFrom(from_addr: address, to: address, tokenId: uint256, data: Bytes[1024] = b""):
    """
    @notice Safely transfer an agent, checking if receiver can handle ERC-721
    @param from_addr The current owner
    @param to The new owner
    @param tokenId The agent ID
    @param data Additional data to pass to receiver
    """
    self._transfer(from_addr, to, tokenId)
    self._checkOnERC721Received(from_addr, to, tokenId, data)


# ═══════════════════════════════════════════════════════════════════════════════
# ERC-721 METADATA
# ═══════════════════════════════════════════════════════════════════════════════

@external
@view
def tokenURI(tokenId: uint256) -> String[512]:
    """
    @notice Get the metadata URI for an agent
    @param tokenId The agent ID
    @return The URI pointing to the agent's registration JSON
    @dev The registration JSON follows ERC-8004 schema:
         {
           "name": "Agent Name",
           "description": "What this agent does",
           "image": "ipfs://...",
           "services": [
             {"type": "A2A", "endpoint": "...", "version": "1.0"},
             {"type": "x402", "endpoint": "...", "version": "2.0"}
           ],
           "x402Support": true,
           "active": true
         }
    """
    assert self.owners[tokenId] != empty(address), "ERC721: nonexistent token"
    return self.tokenURIs[tokenId]


# ═══════════════════════════════════════════════════════════════════════════════
# ERC-8004: AGENT REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════════

@external
def registerAgent(metadataURI: String[512]) -> uint256:
    """
    @notice Register a new agent identity (mint an agent NFT)
    @param metadataURI URI pointing to the agent's registration JSON
    @return The new agent ID (token ID)
    @dev Permissionless - anyone can register an agent.
         The caller becomes the owner of the agent identity.
         
    Registration JSON should include:
    - name: Human-readable agent name
    - description: What the agent does
    - services: Array of service endpoints the agent offers
    - x402Support: Boolean indicating x402 Batching SDK compatibility
    - active: Boolean indicating if agent is accepting work
    """
    agentId: uint256 = self.nextTokenId
    self.nextTokenId = agentId + 1
    
    # Mint the token to the caller
    self._mint(msg.sender, agentId)
    
    # Set the metadata URI
    self.tokenURIs[agentId] = metadataURI
    
    # Agent is active by default
    self.agentActive[agentId] = True
    
    log AgentRegistered(agentId, msg.sender, metadataURI)
    
    return agentId


@external
def updateAgentURI(agentId: uint256, newURI: String[512]):
    """
    @notice Update an agent's metadata URI
    @param agentId The agent ID to update
    @param newURI The new metadata URI
    @dev Only the owner can update their agent's metadata
    """
    assert self.owners[agentId] == msg.sender, "AgentIdentity: not owner"
    self.tokenURIs[agentId] = newURI
    log AgentUpdated(agentId, newURI)


@external
def setAgentStatus(agentId: uint256, active: bool):
    """
    @notice Set an agent's active status
    @param agentId The agent ID
    @param active True to activate, false to deactivate
    @dev Only the owner can change status.
         Inactive agents should not be discovered for new work.
    """
    assert self.owners[agentId] == msg.sender, "AgentIdentity: not owner"
    self.agentActive[agentId] = active
    log AgentStatusChanged(agentId, active)


@external
@view
def isActive(agentId: uint256) -> bool:
    """
    @notice Check if an agent is currently active
    @param agentId The agent ID
    @return True if the agent is active and accepting work
    """
    assert self.owners[agentId] != empty(address), "AgentIdentity: nonexistent agent"
    return self.agentActive[agentId]


@external
@view
def agentExists(agentId: uint256) -> bool:
    """
    @notice Check if an agent ID exists
    @param agentId The agent ID to check
    @return True if the agent exists
    """
    return self.owners[agentId] != empty(address)


@external
@view
def totalAgents() -> uint256:
    """
    @notice Get the total number of registered agents
    @return The total count of agents (nextTokenId - 1 since we start at 1)
    """
    if self.nextTokenId == 1:
        return 0
    return self.nextTokenId - 1


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@internal
def _mint(to: address, tokenId: uint256):
    """
    @notice Internal function to mint a new token
    @param to The address to mint to
    @param tokenId The token ID to mint
    """
    assert to != empty(address), "ERC721: mint to zero address"
    assert self.owners[tokenId] == empty(address), "ERC721: token exists"
    
    self.balances[to] += 1
    self.owners[tokenId] = to
    
    log Transfer(empty(address), to, tokenId)


@internal
def _transfer(from_addr: address, to: address, tokenId: uint256):
    """
    @notice Internal function to transfer a token
    @param from_addr The current owner
    @param to The new owner
    @param tokenId The token ID
    """
    owner: address = self.owners[tokenId]
    assert owner != empty(address), "ERC721: nonexistent token"
    assert owner == from_addr, "ERC721: transfer from incorrect owner"
    assert to != empty(address), "ERC721: transfer to zero address"
    
    # Check authorization
    assert (
        msg.sender == owner or
        self.tokenApprovals[tokenId] == msg.sender or
        self.operatorApprovals[owner][msg.sender]
    ), "ERC721: not authorized"
    
    # Clear approval
    self.tokenApprovals[tokenId] = empty(address)
    
    # Update balances
    self.balances[from_addr] -= 1
    self.balances[to] += 1
    
    # Transfer ownership
    self.owners[tokenId] = to
    
    log Transfer(from_addr, to, tokenId)


@internal
def _checkOnERC721Received(from_addr: address, to: address, tokenId: uint256, data: Bytes[1024]):
    """
    @notice Check if the receiver implements onERC721Received
    @param from_addr The sender address
    @param to The receiver address
    @param tokenId The token ID
    @param data Additional data
    @dev Only checks if `to` is a contract (has code)
    """
    if to.codesize > 0:
        returnValue: bytes4 = extcall IERC721Receiver(to).onERC721Received(msg.sender, from_addr, tokenId, data)
        assert returnValue == IERC721_RECEIVER_SELECTOR, "ERC721: unsafe recipient"


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE IMPORTS (for extcall)
# ═══════════════════════════════════════════════════════════════════════════════

interface IERC721Receiver:
    def onERC721Received(operator: address, from_addr: address, tokenId: uint256, data: Bytes[1024]) -> bytes4: nonpayable
