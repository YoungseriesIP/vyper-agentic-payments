"""
A4. Register Your Contract as an ERC-8004 Agent

Deploy an IdentityRegistry and register an agent with a metadata URI.

Instructions:
  1. Deploy the IdentityRegistry from the erc-8004-vyper dependency
  2. Register an agent by calling register() with a metadata URI
  3. Verify the registration by checking ownerOf()

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "A4"
"""

import boa

IDENTITY_REGISTRY_PATH = (
    "lib/github/lufa23/erc-8004-vyper/src/identity_registry.vy"
)


def deploy_registry():
    """
    Deploy the ERC-8004 IdentityRegistry contract.

    Returns:
        The deployed IdentityRegistry contract instance.
    """
    # Implement: deploy identity_registry.vy with a name and symbol
    raise NotImplementedError("Deploy the IdentityRegistry with boa.load()")


def register_agent(registry, owner: str, metadata_uri: str) -> int:
    """
    Register an agent in the IdentityRegistry.

    Args:
        registry: Deployed IdentityRegistry contract instance.
        owner: Address that will own the agent NFT.
        metadata_uri: URI pointing to the agent's metadata JSON.

    Returns:
        agent_id: The newly minted token ID.
    """
    # Implement: as owner, call registry.register(metadata_uri) and return the ID
    raise NotImplementedError("Call register() as the owner")


def verify_registration(registry, agent_id: int, expected_owner: str) -> str:
    """
    Verify that an agent is registered and owned by the expected address.

    Args:
        registry: Deployed IdentityRegistry contract instance.
        agent_id: The token ID to verify.
        expected_owner: The address that should own the agent.

    Returns:
        The owner address from ownerOf().
    """
    # Implement: call registry.ownerOf(agent_id) and assert it matches expected_owner
    raise NotImplementedError("Verify ownership with ownerOf()")
