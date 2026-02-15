# @version ^0.4.0

"""
@title IAgentIdentity Interface
@author Vyper Agentic Payments
@notice Interface for cross-contract agent identity lookups (ERC-8004)
@dev Other contracts can use this to verify agent existence and get metadata
"""

@external
@view
def ownerOf(tokenId: uint256) -> address:
    """
    @notice Get the owner of an agent identity
    @param tokenId The agent ID (token ID)
    @return The owner address of this agent
    """
    ...

@external
@view
def tokenURI(tokenId: uint256) -> String[512]:
    """
    @notice Get the metadata URI for an agent
    @param tokenId The agent ID
    @return The URI pointing to the agent's registration JSON
    """
    ...

@external
@view
def isActive(tokenId: uint256) -> bool:
    """
    @notice Check if an agent is currently active
    @param tokenId The agent ID
    @return True if the agent is active
    """
    ...

@external
@view
def agentExists(tokenId: uint256) -> bool:
    """
    @notice Check if an agent ID exists
    @param tokenId The agent ID to check
    @return True if the agent exists
    """
    ...

@external
@view
def totalAgents() -> uint256:
    """
    @notice Get the total number of registered agents
    @return The total count of agents
    """
    ...
