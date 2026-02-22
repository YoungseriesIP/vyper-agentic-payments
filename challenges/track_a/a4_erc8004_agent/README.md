# A4. Register Your Contract as an ERC-8004 Agent

[ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) defines a standard for on-chain agent identity and reputation. The `erc-8004-vyper` dependency provides a Vyper reference implementation with three contracts: `IdentityRegistry`, `ReputationRegistry`, and `ValidationRegistry`.

## Spec

Using the `IdentityRegistry` from the dependency added in A1:

1. Deploy an instance of `IdentityRegistry` (or use a shared testnet deployment if one is provided)
2. Call `register` to register the contract you deployed in A2 as an agent, including a metadata URI pointing to a JSON file describing what it does
3. Verify the registration by calling `ownerOf` with the returned token ID

This is the same pattern Track C contracts follow — registering contract instances as agents gives them a verifiable on-chain identity that other contracts and off-chain tooling can resolve.

## Key Functions

The `IdentityRegistry` is an ERC-721 contract. Each registered agent gets a unique token ID.

```python
import boa

# Deploy the IdentityRegistry
registry = boa.load(
    "lib/github/lufa23/erc-8004-vyper/src/identity_registry.vy",
    "AgentRegistry",  # _name
    "AGENT",          # _symbol
)

# Register an agent — mints an NFT to msg.sender, returns the token ID
agent_id = registry.register("ipfs://QmYourMetadataHash...")

# Verify ownership
owner = registry.ownerOf(agent_id)    # should equal msg.sender
uri = registry.tokenURI(agent_id)     # should equal the metadata URI

# Optional: set on-chain metadata key-value pairs
registry.setMetadata(agent_id, "description", b"A USDC vault agent")
value = registry.getMetadata(agent_id, "description")
```

## What to Implement

Fill in `challenge.py`:

1. `deploy_registry()` — deploy the IdentityRegistry and return the instance
2. `register_agent(registry, owner, metadata_uri)` — register an agent and return the token ID
3. `verify_registration(registry, agent_id, expected_owner)` — verify ownership and return the owner address

## Hints

- The IdentityRegistry constructor takes `_name: String[25]` and `_symbol: String[5]`
- `register()` mints to `msg.sender` — use `boa.env.prank(owner)` to set the caller
- Agent IDs are 1-based (first registration returns 1)
- The `register` function accepts an optional `tokenURI` string and optional metadata entries

## Checkpoint

A transaction on the block explorer showing your contract registered in the `IdentityRegistry`. The token ID and metadata URI visible on-chain.
