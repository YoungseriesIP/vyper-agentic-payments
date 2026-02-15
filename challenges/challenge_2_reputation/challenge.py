"""
Challenge 2: Reputation Feedback (Medium)

Record an interaction and submit feedback for an agent.

Instructions:
  1. Record the interaction (as agent owner)
  2. Submit feedback with score and proof-of-payment (as client)
  3. Return the feedback_id

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "challenge_2"
"""

import boa


def submit_feedback(
    reputation,
    identity,
    agent_id: int,
    agent_owner: str,
    client: str,
    score: int,
    proof_of_payment: bytes,
) -> int:
    """
    Record interaction and submit feedback for an agent.

    Args:
        reputation: Deployed AgentReputation contract instance
        identity: Deployed AgentIdentity contract instance
        agent_id: The agent's token ID
        agent_owner: Address of the agent owner (can record interactions)
        client: Address of the client submitting feedback
        score: Feedback score (0-100)
        proof_of_payment: 32-byte proof (e.g., tx hash)

    Returns:
        feedback_id: The ID of the submitted feedback
    """
    # TODO: Step 1 — Use boa.env.prank(agent_owner) to record the interaction
    #       Call reputation.recordInteraction(agent_id, client)

    # TODO: Step 2 — Use boa.env.prank(client) to submit feedback
    #       Call reputation.submitFeedback(agent_id, score, proof_of_payment)
    #       Return the feedback_id

    raise NotImplementedError("Complete this challenge!")
