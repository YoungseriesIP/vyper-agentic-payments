"""
Challenge 1: Agent Identity (Easy)

Register an AI agent on the AgentIdentity contract.

Instructions:
  1. Use boa.env.prank() to act as the agent_owner
  2. Call identity.registerAgent() with a metadata URI
  3. Return the agent_id

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "challenge_1"
"""

import boa


def register_agent(identity, agent_owner: str, metadata_uri: str) -> int:
    """
    Register an agent on the AgentIdentity contract.

    Args:
        identity: Deployed AgentIdentity contract instance
        agent_owner: Address that will own the agent NFT
        metadata_uri: IPFS URI for the agent's metadata

    Returns:
        agent_id: The newly minted agent's token ID
    """
    # TODO: Use boa.env.prank(agent_owner) to impersonate the owner
    # TODO: Call identity.registerAgent(metadata_uri)
    # TODO: Return the agent_id
    raise NotImplementedError("Complete this challenge!")
