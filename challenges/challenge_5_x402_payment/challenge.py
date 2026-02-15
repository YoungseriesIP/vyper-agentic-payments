"""
Challenge 5: x402 Payment + On-Chain Reputation (Hard - Capstone)

Bridge off-chain gasless payment with on-chain state mutation. This capstone
challenge combines circlekit's GatewayClient (off-chain x402 payment) with
titanoboa contract interaction (on-chain reputation feedback), converting a
settlement transaction hash into bytes32 proof-of-payment stored on-chain.

Instructions:
  1. Make an x402 gasless payment using GatewayClient
  2. Check x402 support and pay for the resource
  3. Convert the settlement tx hash (hex string) to bytes32
  4. Record an on-chain interaction via AgentReputation
  5. Submit on-chain feedback with the tx hash as proof-of-payment
  6. Return combined off-chain + on-chain results

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "Challenge5"

Requires:
  pip install -e ../circle-titanoboa-sdk
  pip install flask httpx pytest-asyncio
"""

import boa


async def pay_and_record_reputation(
    server_url: str,
    private_key: str,
    reputation,
    identity,
    agent_id: int,
    agent_owner,
    client,
    score: int,
) -> dict:
    """
    Pay for an x402-protected resource, then record on-chain reputation feedback.

    This function bridges off-chain payment (circlekit GatewayClient) with
    on-chain state (AgentReputation contract via titanoboa). The key insight
    is converting the settlement tx hash string into a bytes32 proof.

    Args:
        server_url: Base URL of the seller server (e.g. "http://127.0.0.1:4099")
        private_key: Hex-encoded private key (e.g. "0x0000...0001")
        reputation: AgentReputation contract instance (boa)
        identity: AgentIdentity contract instance (boa)
        agent_id: ID of a pre-registered agent to rate
        agent_owner: Address that owns the agent
        client: Address acting as the client (for on-chain feedback)
        score: Feedback score 0-100

    Returns:
        dict with keys:
            "payer"       — Wallet address (str)
            "amount"      — Formatted payment amount (str, e.g. "0.010000")
            "tx"          — Settlement transaction hash (str)
            "data"        — JSON response body from the server (dict)
            "supported"   — Whether supports() confirmed x402 is available (bool)
            "feedback_id" — On-chain feedback ID (int)
            "proof"       — bytes32 proof-of-payment stored on-chain (bytes)
    """
    # TODO: Step 1 — Import GatewayClient and make the x402 payment
    #       You'll need: from circlekit import GatewayClient
    #       Create a client with chain="arcTestnet" and the provided private_key
    #       Use `async with` for automatic cleanup

    # TODO: Step 2 — Convert the settlement tx hash to bytes32
    #       The tx hash is a hex string like "0xabc123..."
    #       Strip the "0x" prefix and use bytes.fromhex() to get raw bytes
    #       This becomes your proof-of-payment for on-chain storage

    # TODO: Step 3 — Record the interaction on-chain
    #       Use boa.env.prank(agent_owner) to call
    #       reputation.recordInteraction(agent_id, client)

    # TODO: Step 4 — Submit feedback on-chain with the proof
    #       Use boa.env.prank(client) to call
    #       reputation.submitFeedback(agent_id, score, proof)
    #       This returns a feedback_id

    # TODO: Step 5 — Return combined results dict with all 7 keys:
    #       payer, amount, tx, data, supported, feedback_id, proof

    raise NotImplementedError("Complete this challenge!")
