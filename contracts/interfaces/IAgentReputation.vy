# @version ^0.4.0

"""
@title IAgentReputation Interface
@author Vyper Agentic Payments
@notice Interface for cross-contract agent reputation reads (ERC-8004)
@dev Other contracts can query agent reputation scores on-chain
"""

@external
@view
def getAverageScore(agentId: uint256) -> uint256:
    """
    @notice Get the average reputation score for an agent
    @param agentId The agent ID
    @return The average score (0-100, scaled by 100 for precision)
    """
    ...

@external
@view
def getTotalFeedbackCount(agentId: uint256) -> uint256:
    """
    @notice Get the total number of feedback entries for an agent
    @param agentId The agent ID
    @return The count of feedback entries
    """
    ...

@external
@view
def hasInteracted(agentId: uint256, client: address) -> bool:
    """
    @notice Check if a client has interacted with an agent
    @param agentId The agent ID
    @param client The client address to check
    @return True if the client has verified interaction
    """
    ...

@external
@view
def getReputationTier(agentId: uint256) -> uint8:
    """
    @notice Get the reputation tier for an agent
    @param agentId The agent ID
    @return Tier: 0=Unrated, 1=Bronze, 2=Silver, 3=Gold, 4=Platinum
    """
    ...
