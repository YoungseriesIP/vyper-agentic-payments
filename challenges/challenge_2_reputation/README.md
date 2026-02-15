# Challenge 2: Reputation Feedback (Medium)

Record an interaction and submit feedback for an agent using `AgentReputation.vy`.

## Goal

Fill in `challenge.py` to:
1. Record that a client interacted with an agent
2. Submit a feedback score with a proof-of-payment

## What You Need to Know

- Feedback requires a **prior interaction** (prevents fake reviews)
- Only the agent owner can call `recordInteraction()`
- Only a client who interacted can call `submitFeedback()`
- Scores are 0-100, stored scaled by 100 (e.g., 85 → 8500)
- `proofOfPayment` is a `bytes32` (transaction hash from x402 payment)

## Key Functions

```python
# Agent owner records that client interacted with their agent
reputation.recordInteraction(agent_id, client_address)

# Client submits feedback
feedback_id = reputation.submitFeedback(agent_id, score, proof_of_payment)

# Read reputation
avg = reputation.getAverageScore(agent_id)  # Scaled by 100
tier = reputation.getReputationTier(agent_id)  # 0-4
```

## Hints

- `recordInteraction` must be called by the agent owner (use `boa.env.prank`)
- `submitFeedback` must be called by the client (use `boa.env.prank`)
- `proof_of_payment` must be exactly 32 bytes
- Check `tests/test_agent_reputation.py` for more examples
