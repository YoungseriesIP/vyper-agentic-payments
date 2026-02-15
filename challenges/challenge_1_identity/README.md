# Challenge 1: Agent Identity (Easy)

Register an AI agent on-chain using the `AgentIdentity.vy` ERC-721 contract.

## Goal

Fill in `challenge.py` to register an agent and verify it was created.

## What You Need to Know

- `AgentIdentity.vy` is an ERC-721 (NFT) contract
- Each agent gets a unique `agentId` (token ID)
- `registerAgent(metadataURI)` mints an NFT to `msg.sender`
- The `metadataURI` points to off-chain metadata (IPFS hash)

## Key Functions

```python
# Register a new agent — returns agentId (uint256)
agent_id = identity.registerAgent("ipfs://QmYourMetadata...")

# Read agent info
owner = identity.ownerOf(agent_id)
uri = identity.tokenURI(agent_id)
total = identity.totalAgents()
```

## Hints

- Use `boa.env.prank(address)` to set `msg.sender`
- The function returns the new agent's ID
- Check `tests/test_agent_identity.py` for more examples
