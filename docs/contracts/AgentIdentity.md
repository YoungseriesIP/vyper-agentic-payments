# AgentIdentity

ERC-721 NFT registry for AI agent identities. Implements ERC-8004 Identity Registry.

## Overview

AgentIdentity allows developers to:
- Register AI agents as NFTs
- Store metadata URIs (typically IPFS)
- Transfer agent ownership
- Activate/deactivate agents

## Contract Details

- **File**: `contracts/AgentIdentity.vy`
- **Tests**: 39 passing
- **Dependencies**: None

## Functions

### Registration

#### `registerAgent(metadataURI: String[256]) -> uint256`

Register a new agent. Mints an ERC-721 NFT to the caller.

```python
agent_id = identity.registerAgent("ipfs://QmAgentMetadata...")
# Returns: uint256 (the agent ID, which equals the token ID)
```

**Parameters:**
- `metadataURI`: IPFS or HTTP URI pointing to agent metadata JSON

**Returns:** The agent ID (token ID)

**Events:**
- `AgentRegistered(agentId, owner, tokenURI)`
- `Transfer(address(0), owner, agentId)`

---

### Metadata

#### `updateAgentURI(agentId: uint256, newURI: String[256])`

Update an agent's metadata URI. Only callable by agent owner.

```python
identity.updateAgentURI(1, "ipfs://QmNewMetadata...")
```

**Access:** Agent owner only

**Events:**
- `AgentUpdated(agentId, newTokenURI)`

---

#### `tokenURI(agentId: uint256) -> String[256]`

Get the metadata URI for an agent.

```python
uri = identity.tokenURI(1)
# Returns: "ipfs://QmAgentMetadata..."
```

---

### Status

#### `setAgentStatus(agentId: uint256, active: bool)`

Activate or deactivate an agent. Only callable by agent owner.

```python
identity.setAgentStatus(1, False)  # Deactivate
identity.setAgentStatus(1, True)   # Reactivate
```

**Access:** Agent owner only

**Events:**
- `AgentStatusChanged(agentId, active)`

---

#### `isAgentActive(agentId: uint256) -> bool`

Check if an agent is active.

```python
active = identity.isAgentActive(1)  # True or False
```

---

### Queries

#### `agentExists(agentId: uint256) -> bool`

Check if an agent exists.

```python
exists = identity.agentExists(1)  # True or False
```

---

#### `totalAgents() -> uint256`

Get total number of registered agents.

```python
total = identity.totalAgents()  # e.g., 42
```

---

#### `getAgentOwner(agentId: uint256) -> address`

Get the owner of an agent. Alias for `ownerOf`.

```python
owner = identity.getAgentOwner(1)
# Returns: 0x123...
```

---

### ERC-721 Standard

#### `ownerOf(tokenId: uint256) -> address`

Get owner of token.

#### `balanceOf(owner: address) -> uint256`

Get number of tokens owned.

#### `transferFrom(from: address, to: address, tokenId: uint256)`

Transfer token between addresses.

#### `safeTransferFrom(from: address, to: address, tokenId: uint256)`

Safe transfer with receiver check.

#### `approve(to: address, tokenId: uint256)`

Approve address to transfer specific token.

#### `setApprovalForAll(operator: address, approved: bool)`

Approve operator for all tokens.

#### `getApproved(tokenId: uint256) -> address`

Get approved address for token.

#### `isApprovedForAll(owner: address, operator: address) -> bool`

Check if operator is approved for all owner's tokens.

---

## Events

```python
event AgentRegistered:
    agentId: indexed(uint256)
    owner: indexed(address)
    tokenURI: String[256]

event AgentUpdated:
    agentId: indexed(uint256)
    newTokenURI: String[256]

event AgentStatusChanged:
    agentId: indexed(uint256)
    active: bool

# ERC-721 events
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
```

## Metadata Format

Agent metadata should follow this JSON schema:

```json
{
  "name": "My AI Agent",
  "description": "An autonomous AI agent for task completion",
  "image": "ipfs://QmImageHash...",
  "attributes": [
    {
      "trait_type": "capability",
      "value": "text_analysis"
    },
    {
      "trait_type": "version",
      "value": "1.0.0"
    }
  ],
  "external_url": "https://myagent.example.com"
}
```

## Usage Examples

### Register an Agent

```python
import boa

identity = boa.load("contracts/AgentIdentity.vy")

# Register agent with IPFS metadata
agent_id = identity.registerAgent("ipfs://QmAgentMetadata...")

print(f"Agent registered with ID: {agent_id}")
print(f"Owner: {identity.ownerOf(agent_id)}")
```

### Transfer Ownership

```python
# Current owner transfers to new owner
identity.transferFrom(current_owner, new_owner, agent_id)

# Verify transfer
assert identity.ownerOf(agent_id) == new_owner
```

### Check Agent Status

```python
# Check if agent exists and is active
if identity.agentExists(agent_id) and identity.isAgentActive(agent_id):
    print("Agent is active and ready")
else:
    print("Agent not available")
```

## Security Considerations

1. **Ownership validation** - Always verify `ownerOf` before interacting
2. **Active status** - Check `isAgentActive` before using agent services
3. **Metadata immutability** - Consider IPFS for immutable metadata
4. **Transfer implications** - Ownership transfer moves all agent rights
