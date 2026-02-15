# AgentReputation

On-chain reputation system for AI agents with proof-of-payment feedback. Implements ERC-8004 Reputation Registry.

## Overview

AgentReputation enables:
- Recording client-agent interactions
- Submitting feedback with payment proof
- Calculating reputation scores and tiers
- Querying agent reputation history

## Contract Details

- **File**: `contracts/AgentReputation.vy`
- **Tests**: 28 passing
- **Dependencies**: AgentIdentity

## Constructor

```python
def __init__(identityRegistry: address):
    """
    @param identityRegistry Address of the AgentIdentity contract
    """
```

## Functions

### Interactions

#### `recordInteraction(agentId: uint256, client: address)`

Record that a client interacted with an agent. Must be called by agent owner.

```python
# Agent owner records client interaction
reputation.recordInteraction(agent_id, client_address)
```

**Access:** Agent owner only

**Events:**
- `InteractionRecorded(agentId, client, timestamp)`

---

#### `recordInteractionBySelf(agentId: uint256)`

Record interaction where caller is the client.

```python
# Client records their own interaction
reputation.recordInteractionBySelf(agent_id)
```

**Access:** Anyone (caller becomes the client)

---

#### `hasClientInteracted(agentId: uint256, client: address) -> bool`

Check if a client has interacted with an agent.

```python
has_interacted = reputation.hasClientInteracted(agent_id, client)
```

---

### Feedback

#### `submitFeedback(agentId: uint256, score: uint256, proofOfPayment: bytes32) -> uint256`

Submit feedback for an agent. Requires prior interaction.

```python
# Submit feedback with score and payment proof
feedback_id = reputation.submitFeedback(
    agent_id,
    85,  # Score out of 100
    payment_tx_hash  # bytes32 proof of payment
)
```

**Requirements:**
- Client must have interacted with agent
- Client can only submit one feedback per agent
- Score must be 0-100

**Returns:** Feedback ID

**Events:**
- `FeedbackSubmitted(agentId, client, score, proofOfPayment, feedbackId)`

---

#### `hasClientRated(agentId: uint256, client: address) -> bool`

Check if a client has already rated an agent.

```python
has_rated = reputation.hasClientRated(agent_id, client)
```

---

### Queries

#### `getAverageScore(agentId: uint256) -> uint256`

Get agent's average reputation score. **Scaled by 100.**

```python
avg_score = reputation.getAverageScore(agent_id)
# Returns 8500 for average of 85.00
actual_score = avg_score / 100  # 85.00
```

**Note:** Score is scaled by 100 for precision (e.g., 85.00 = 8500)

---

#### `getTotalFeedbackCount(agentId: uint256) -> uint256`

Get total number of feedbacks received.

```python
count = reputation.getTotalFeedbackCount(agent_id)  # e.g., 42
```

---

#### `getReputationTier(agentId: uint256) -> uint256`

Get agent's reputation tier based on average score.

```python
tier = reputation.getReputationTier(agent_id)
# 0 = Unrated (no feedback)
# 1 = Bronze (0-49)
# 2 = Silver (50-69)
# 3 = Gold (70-89)
# 4 = Platinum (90-100)
```

---

#### `getFeedback(feedbackId: uint256) -> tuple`

Get details of a specific feedback.

```python
feedback = reputation.getFeedback(feedback_id)
# Returns: (agentId, reviewer, score, timestamp, proofOfPayment)
```

---

#### `getFeedbackByAgent(agentId: uint256, index: uint256) -> uint256`

Get feedback ID for an agent by index.

```python
# Get first feedback for agent
feedback_id = reputation.getFeedbackByAgent(agent_id, 0)
```

---

### Admin

#### `updateIdentityRegistry(newRegistry: address)`

Update the identity registry address. Admin only.

```python
reputation.updateIdentityRegistry(new_identity_address)
```

**Access:** Admin only

**Events:**
- `IdentityRegistryUpdated(oldRegistry, newRegistry)`

---

## Events

```python
event InteractionRecorded:
    agentId: indexed(uint256)
    client: indexed(address)
    timestamp: uint256

event FeedbackSubmitted:
    agentId: indexed(uint256)
    client: indexed(address)
    score: uint256
    proofOfPayment: bytes32
    feedbackId: uint256

event IdentityRegistryUpdated:
    oldRegistry: indexed(address)
    newRegistry: indexed(address)
```

## Reputation Tiers

| Tier | Name | Score Range | Meaning |
|------|------|-------------|---------|
| 0 | Unrated | - | No feedback yet |
| 1 | Bronze | 0-49 | Poor reputation |
| 2 | Silver | 50-69 | Average reputation |
| 3 | Gold | 70-89 | Good reputation |
| 4 | Platinum | 90-100 | Excellent reputation |

## Usage Examples

### Complete Workflow

```python
import boa

# Load contracts
identity = boa.load("contracts/AgentIdentity.vy")
reputation = boa.load("contracts/AgentReputation.vy", identity.address)

# Agent owner registers agent
with boa.env.prank(agent_owner):
    agent_id = identity.registerAgent("ipfs://...")

# Client interacts with agent (off-chain)
# ...payment and service happens via x402...

# Agent owner records the interaction
with boa.env.prank(agent_owner):
    reputation.recordInteraction(agent_id, client)

# Client submits feedback
with boa.env.prank(client):
    feedback_id = reputation.submitFeedback(
        agent_id,
        85,  # Score
        b'\xab\xcd' + b'\x00' * 30  # Payment proof
    )

# Query reputation
avg_score = reputation.getAverageScore(agent_id)  # 8500
tier = reputation.getReputationTier(agent_id)  # 3 (Gold)
```

### Integrate with x402

```typescript
// After successful x402 payment
const paymentProof = ethers.utils.id(transactionHash);

// Submit feedback on-chain
await reputation.submitFeedback(
  agentId,
  85,
  paymentProof
);
```

## Security Considerations

1. **Interaction requirement** - Prevents fake reviews from non-clients
2. **One feedback per client** - Prevents spam ratings
3. **Proof of payment** - Creates audit trail back to actual transaction
4. **Score scaling** - Avoid floating point, use integer math
