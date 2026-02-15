"""
Tests for AgentReputation.vy - ERC-8004 Reputation Registry

This test suite covers:
- Interaction recording
- Feedback submission with x402 proof-of-payment
- Reputation scoring and tiers
- Access control and edge cases
"""

import pytest
import boa


class TestAgentReputationDeployment:
    """Tests for contract deployment and initialization."""

    def test_initial_state(self, agent_reputation, agent_identity, deployer):
        """Contract should initialize with correct default values."""
        assert agent_reputation.identityRegistry() == agent_identity.address
        assert agent_reputation.admin() == deployer
        assert agent_reputation.nextFeedbackId() == 1

    def test_deploy_with_zero_address_fails(self):
        """Should fail to deploy with zero address for identity registry."""
        with pytest.raises(boa.BoaError, match="zero address"):
            boa.load("contracts/AgentReputation.vy", "0x0000000000000000000000000000000000000000")


class TestAdminFunctions:
    """Tests for admin-only functions."""

    def test_update_identity_registry(self, agent_reputation, deployer, alice):
        """Admin should be able to update identity registry."""
        new_registry = alice  # Using alice as a placeholder address
        
        with boa.env.prank(deployer):
            agent_reputation.updateIdentityRegistry(new_registry)
        
        assert agent_reputation.identityRegistry() == new_registry

    def test_update_identity_registry_not_admin_fails(self, agent_reputation, alice, bob):
        """Non-admin should not be able to update identity registry."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="not admin"):
                agent_reputation.updateIdentityRegistry(bob)

    def test_transfer_admin(self, agent_reputation, deployer, alice):
        """Admin should be able to transfer admin role."""
        with boa.env.prank(deployer):
            agent_reputation.transferAdmin(alice)
        
        assert agent_reputation.admin() == alice

    def test_transfer_admin_not_admin_fails(self, agent_reputation, alice, bob):
        """Non-admin should not be able to transfer admin role."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="not admin"):
                agent_reputation.transferAdmin(bob)


class TestInteractionRecording:
    """Tests for recording interactions between clients and agents."""

    def test_record_interaction(self, agent_reputation, agent_identity, alice, charlie):
        """Should successfully record an interaction."""
        # First register an agent
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        # Record interaction for charlie
        agent_reputation.recordInteraction(agent_id, charlie)
        
        assert agent_reputation.hasClientInteracted(agent_id, charlie) is True

    def test_record_interaction_by_self(self, agent_reputation, agent_identity, alice, charlie):
        """Client should be able to record their own interaction."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
        
        assert agent_reputation.hasClientInteracted(agent_id, charlie) is True

    def test_record_interaction_nonexistent_agent_fails(self, agent_reputation, charlie):
        """Should fail to record interaction for nonexistent agent."""
        with pytest.raises(boa.BoaError, match="agent not found"):
            agent_reputation.recordInteraction(999, charlie)

    def test_has_not_interacted_by_default(self, agent_reputation, agent_identity, alice, charlie):
        """Client should not have interacted by default."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        assert agent_reputation.hasClientInteracted(agent_id, charlie) is False


class TestFeedbackSubmission:
    """Tests for submitting reputation feedback."""

    def test_submit_feedback(self, agent_reputation, agent_identity, alice, charlie):
        """Should successfully submit feedback after interaction."""
        # Register agent
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        # Record interaction
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
        
        # Submit feedback
        proof = b'\x12\x34' + b'\x00' * 30  # 32 bytes proof of payment
        with boa.env.prank(charlie):
            feedback_id = agent_reputation.submitFeedback(agent_id, 85, proof)
        
        assert feedback_id == 1
        assert agent_reputation.feedbackCount(agent_id) == 1
        assert agent_reputation.totalScore(agent_id) == 85

    def test_submit_feedback_without_interaction_fails(self, agent_reputation, agent_identity, alice, charlie):
        """Should fail to submit feedback without prior interaction."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        proof = b'\x00' * 32
        with boa.env.prank(charlie):
            with pytest.raises(boa.BoaError, match="no interaction"):
                agent_reputation.submitFeedback(agent_id, 85, proof)

    def test_submit_feedback_score_over_100_fails(self, agent_reputation, agent_identity, alice, charlie):
        """Should fail if score is over 100."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
        
        proof = b'\x00' * 32
        with boa.env.prank(charlie):
            with pytest.raises(boa.BoaError, match="score must be 0-100"):
                agent_reputation.submitFeedback(agent_id, 101, proof)

    def test_cannot_submit_feedback_twice(self, agent_reputation, agent_identity, alice, charlie):
        """Client should only be able to submit one feedback per agent."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
            agent_reputation.submitFeedback(agent_id, 85, b'\x00' * 32)
        
        with boa.env.prank(charlie):
            with pytest.raises(boa.BoaError, match="already rated"):
                agent_reputation.submitFeedback(agent_id, 90, b'\x00' * 32)

    def test_feedback_stores_proof_of_payment(self, agent_reputation, agent_identity, alice, charlie):
        """Feedback should store the proof of payment hash."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
        
        # Create a recognizable proof hash
        proof = b'\xab\xcd' * 16  # 32 bytes
        with boa.env.prank(charlie):
            feedback_id = agent_reputation.submitFeedback(agent_id, 75, proof)
        
        # Retrieve and verify
        result = agent_reputation.getFeedback(feedback_id)
        assert result[0] == agent_id  # agentId
        assert result[1] == charlie   # client
        assert result[2] == 75        # score
        assert result[4] == proof     # proofOfPayment


class TestReputationScoring:
    """Tests for reputation score calculations."""

    def test_average_score_single_feedback(self, agent_reputation, agent_identity, alice, charlie):
        """Average should equal the single score."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
            agent_reputation.submitFeedback(agent_id, 80, b'\x00' * 32)
        
        # Average is scaled by 100 for precision
        assert agent_reputation.getAverageScore(agent_id) == 8000  # 80.00

    def test_average_score_multiple_feedbacks(self, agent_reputation, agent_identity, alice, bob, charlie):
        """Average should be calculated correctly across multiple feedbacks."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        # Charlie gives 80
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
            agent_reputation.submitFeedback(agent_id, 80, b'\x00' * 32)
        
        # Bob gives 60
        with boa.env.prank(bob):
            agent_reputation.recordInteractionBySelf(agent_id)
            agent_reputation.submitFeedback(agent_id, 60, b'\x00' * 32)
        
        # Average: (80 + 60) / 2 = 70, scaled by 100 = 7000
        assert agent_reputation.getAverageScore(agent_id) == 7000

    def test_average_score_no_feedback(self, agent_reputation, agent_identity, alice):
        """Average should be 0 when no feedback exists."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        assert agent_reputation.getAverageScore(agent_id) == 0

    def test_total_feedback_count(self, agent_reputation, agent_identity, alice, bob, charlie):
        """Feedback count should increment correctly."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        assert agent_reputation.getTotalFeedbackCount(agent_id) == 0
        
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
            agent_reputation.submitFeedback(agent_id, 80, b'\x00' * 32)
        
        assert agent_reputation.getTotalFeedbackCount(agent_id) == 1
        
        with boa.env.prank(bob):
            agent_reputation.recordInteractionBySelf(agent_id)
            agent_reputation.submitFeedback(agent_id, 60, b'\x00' * 32)
        
        assert agent_reputation.getTotalFeedbackCount(agent_id) == 2


class TestReputationTiers:
    """Tests for reputation tier calculation."""

    def test_tier_unrated(self, agent_reputation, agent_identity, alice):
        """Agent with no feedback should be Unrated (tier 0)."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        assert agent_reputation.getReputationTier(agent_id) == 0  # UNRATED

    def test_tier_bronze(self, agent_reputation, agent_identity, alice, charlie):
        """Agent with average 1-25 should be Bronze (tier 1)."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
            agent_reputation.submitFeedback(agent_id, 20, b'\x00' * 32)
        
        assert agent_reputation.getReputationTier(agent_id) == 1  # BRONZE

    def test_tier_silver(self, agent_reputation, agent_identity, alice, charlie):
        """Agent with average 26-50 should be Silver (tier 2)."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
            agent_reputation.submitFeedback(agent_id, 40, b'\x00' * 32)
        
        assert agent_reputation.getReputationTier(agent_id) == 2  # SILVER

    def test_tier_gold(self, agent_reputation, agent_identity, alice, charlie):
        """Agent with average 51-75 should be Gold (tier 3)."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
            agent_reputation.submitFeedback(agent_id, 70, b'\x00' * 32)
        
        assert agent_reputation.getReputationTier(agent_id) == 3  # GOLD

    def test_tier_platinum(self, agent_reputation, agent_identity, alice, charlie):
        """Agent with average 76-100 should be Platinum (tier 4)."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
            agent_reputation.submitFeedback(agent_id, 95, b'\x00' * 32)
        
        assert agent_reputation.getReputationTier(agent_id) == 4  # PLATINUM


class TestFeedbackRetrieval:
    """Tests for retrieving feedback details."""

    def test_get_feedback_details(self, agent_reputation, agent_identity, alice, charlie):
        """Should retrieve all feedback details correctly."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
        
        proof = b'\xde\xad\xbe\xef' + b'\x00' * 28
        with boa.env.prank(charlie):
            feedback_id = agent_reputation.submitFeedback(agent_id, 88, proof)
        
        result = agent_reputation.getFeedback(feedback_id)
        
        assert result[0] == agent_id  # agentId
        assert result[1] == charlie   # client
        assert result[2] == 88        # score
        assert result[3] > 0          # timestamp (should be non-zero)
        assert result[4] == proof     # proofOfPayment

    def test_get_feedback_invalid_id_fails(self, agent_reputation):
        """Should fail for invalid feedback ID."""
        with pytest.raises(boa.BoaError, match="invalid id"):
            agent_reputation.getFeedback(0)
        
        with pytest.raises(boa.BoaError, match="invalid id"):
            agent_reputation.getFeedback(999)

    def test_has_client_rated(self, agent_reputation, agent_identity, alice, bob, charlie):
        """Should correctly track which clients have rated."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        # Charlie hasn't rated yet
        assert agent_reputation.hasClientRated(agent_id, charlie) is False
        
        # Charlie rates
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent_id)
            agent_reputation.submitFeedback(agent_id, 80, b'\x00' * 32)
        
        # Charlie has now rated
        assert agent_reputation.hasClientRated(agent_id, charlie) is True
        
        # Bob hasn't rated
        assert agent_reputation.hasClientRated(agent_id, bob) is False


class TestMultiAgentScenarios:
    """Tests for scenarios with multiple agents."""

    def test_independent_agent_scores(self, agent_reputation, agent_identity, alice, bob, charlie):
        """Each agent should have independent reputation scores."""
        # Register two agents
        with boa.env.prank(alice):
            agent1 = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(bob):
            agent2 = agent_identity.registerAgent("ipfs://agent2")
        
        # Charlie rates agent1 high
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent1)
            agent_reputation.submitFeedback(agent1, 90, b'\x00' * 32)
        
        # Charlie rates agent2 low
        with boa.env.prank(charlie):
            agent_reputation.recordInteractionBySelf(agent2)
            agent_reputation.submitFeedback(agent2, 30, b'\x00' * 32)
        
        # Scores should be independent
        assert agent_reputation.getAverageScore(agent1) == 9000  # 90.00
        assert agent_reputation.getAverageScore(agent2) == 3000  # 30.00
        
        # Tiers should be independent
        assert agent_reputation.getReputationTier(agent1) == 4  # Platinum
        assert agent_reputation.getReputationTier(agent2) == 2  # Silver
