# Challenge 5: x402 Payment + On-Chain Reputation (Hard - Capstone)

Bridge off-chain gasless payment with on-chain reputation feedback. This capstone ties together the `circlekit` SDK (Challenge 5 original) and `AgentReputation.vy` (Challenge 2) into a single end-to-end flow.

## Goal

Fill in `challenge.py` to:
1. Make an x402 gasless payment using `GatewayClient`
2. Check that the endpoint supports x402 Gateway batching
3. Convert the settlement tx hash (hex string) into `bytes32`
4. Record an on-chain interaction via `AgentReputation`
5. Submit on-chain feedback with the tx hash as proof-of-payment
6. Return combined off-chain + on-chain results

## The Bridge: tx hash to bytes32

The novel part of this challenge is converting a settlement transaction hash (a hex string like `"0xa1b2c3..."`) into a `bytes32` value that can be stored on-chain as proof-of-payment.

```python
# The tx hash from gateway.pay() is a hex string
tx_hash = result.transaction  # "0xa1b2c3d4..."

# Strip "0x" prefix and convert to raw bytes
proof = bytes.fromhex(tx_hash[2:])  # → b'\xa1\xb2\xc3\xd4...' (32 bytes)

# This bytes32 goes into submitFeedback() as proofOfPayment
```

This links off-chain economic activity (x402 payment) to on-chain reputation state.

## What You Need to Know

- **x402 payment** (off-chain): `GatewayClient` handles the full 402 negotiation flow
- **On-chain reputation** (titanoboa): `recordInteraction()` + `submitFeedback()` on `AgentReputation.vy`
- **The bridge**: `bytes.fromhex()` converts the hex tx hash to `bytes32` proof
- The test uses a **mocked Gateway** — no real USDC or gas is spent
- Review Challenge 2 for `boa.env.prank()` patterns and reputation contract usage

## Key Functions

### GatewayClient (off-chain payment)

```python
from circlekit import GatewayClient

async with GatewayClient(chain="arcTestnet", private_key="0x...") as gateway:
    support = await gateway.supports(f"{server_url}/api/analyze")
    # support.supported → True/False

    result = await gateway.pay(f"{server_url}/api/analyze")
    # result.data → server JSON response (dict)
    # result.formatted_amount → "0.010000"
    # result.transaction → "0xabc..." (settlement tx hash)

    gateway.address  # "0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf"
```

### AgentReputation (on-chain state)

```python
import boa

# Record that client interacted with agent (required before feedback)
with boa.env.prank(agent_owner):
    reputation.recordInteraction(agent_id, client)

# Submit feedback with proof-of-payment
with boa.env.prank(client):
    feedback_id = reputation.submitFeedback(agent_id, score, proof)

# Query state
reputation.hasClientInteracted(agent_id, client)  # → True
reputation.hasClientRated(agent_id, client)        # → True
reputation.getAverageScore(agent_id)               # → score * 100
reputation.getFeedback(feedback_id)                # → (agentId, client, score, timestamp, proof)
```

## Hints

- This challenge is **async** — the function signature is `async def`
- Use `async with GatewayClient(...) as gateway:` so the client cleans up automatically
- The URL to pay is `f"{server_url}/api/analyze"`
- `result.transaction` gives you the hex string to convert to `bytes32`
- Use `boa.env.prank()` for both `recordInteraction` and `submitFeedback` (different callers!)
- Check Challenge 2's `challenge.py` for the on-chain interaction pattern
