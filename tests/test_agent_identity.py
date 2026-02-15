"""
Tests for AgentIdentity.vy - ERC-8004 Identity Registry

This test suite covers:
- ERC-721 core functionality (mint, transfer, approve)
- ERC-8004 agent registration and management
- Edge cases and error conditions
"""

import pytest
import boa
from conftest import create_agent_metadata_uri


class TestAgentIdentityDeployment:
    """Tests for contract deployment and initialization."""

    def test_initial_state(self, agent_identity):
        """Contract should initialize with correct default values."""
        assert agent_identity.name() == "Agent Identity Registry"
        assert agent_identity.symbol() == "AGENT"
        assert agent_identity.nextTokenId() == 1
        assert agent_identity.totalAgents() == 0

    def test_supports_erc165(self, agent_identity):
        """Contract should support ERC-165 interface detection."""
        # ERC-165 interface ID - must be bytes4
        assert agent_identity.supportsInterface(b'\x01\xff\xc9\xa7') is True

    def test_supports_erc721(self, agent_identity):
        """Contract should support ERC-721 interface."""
        # ERC-721 interface ID - must be bytes4
        assert agent_identity.supportsInterface(b'\x80\xac\x58\xcd') is True

    def test_supports_erc721_metadata(self, agent_identity):
        """Contract should support ERC-721 Metadata interface."""
        # ERC-721 Metadata interface ID - must be bytes4
        assert agent_identity.supportsInterface(b'\x5b\x5e\x13\x9f') is True

    def test_does_not_support_random_interface(self, agent_identity):
        """Contract should return false for unsupported interfaces."""
        assert agent_identity.supportsInterface(b'\xde\xad\xbe\xef') is False


class TestAgentRegistration:
    """Tests for agent registration (ERC-8004 Identity Registry)."""

    def test_register_agent(self, agent_identity, alice):
        """Should successfully register a new agent."""
        metadata_uri = create_agent_metadata_uri("AliceBot")
        
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent(metadata_uri)
        
        assert agent_id == 1
        assert agent_identity.ownerOf(1) == alice
        assert agent_identity.tokenURI(1) == metadata_uri
        assert agent_identity.isActive(1) is True
        assert agent_identity.totalAgents() == 1

    def test_register_multiple_agents(self, agent_identity, alice, bob):
        """Should support registering multiple agents."""
        uri_alice = create_agent_metadata_uri("AliceBot")
        uri_bob = create_agent_metadata_uri("BobBot")
        
        with boa.env.prank(alice):
            agent_id_1 = agent_identity.registerAgent(uri_alice)
        
        with boa.env.prank(bob):
            agent_id_2 = agent_identity.registerAgent(uri_bob)
        
        assert agent_id_1 == 1
        assert agent_id_2 == 2
        assert agent_identity.ownerOf(1) == alice
        assert agent_identity.ownerOf(2) == bob
        assert agent_identity.totalAgents() == 2

    def test_same_owner_multiple_agents(self, agent_identity, alice):
        """One address can own multiple agents."""
        uri_1 = create_agent_metadata_uri("Agent1")
        uri_2 = create_agent_metadata_uri("Agent2")
        
        with boa.env.prank(alice):
            agent_identity.registerAgent(uri_1)
            agent_identity.registerAgent(uri_2)
        
        assert agent_identity.balanceOf(alice) == 2
        assert agent_identity.ownerOf(1) == alice
        assert agent_identity.ownerOf(2) == alice

    def test_agent_exists(self, agent_identity, alice):
        """agentExists should return correct status."""
        assert agent_identity.agentExists(1) is False
        
        with boa.env.prank(alice):
            agent_identity.registerAgent("ipfs://test")
        
        assert agent_identity.agentExists(1) is True
        assert agent_identity.agentExists(2) is False


class TestAgentMetadataManagement:
    """Tests for updating agent metadata."""

    def test_update_agent_uri(self, agent_identity, alice):
        """Owner should be able to update agent metadata URI."""
        original_uri = create_agent_metadata_uri("OriginalBot")
        new_uri = create_agent_metadata_uri("UpdatedBot")
        
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent(original_uri)
            agent_identity.updateAgentURI(agent_id, new_uri)
        
        assert agent_identity.tokenURI(agent_id) == new_uri

    def test_update_uri_not_owner_fails(self, agent_identity, alice, bob):
        """Non-owner should not be able to update agent metadata."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
        
        with boa.env.prank(bob):
            with pytest.raises(boa.BoaError, match="not owner"):
                agent_identity.updateAgentURI(agent_id, "ipfs://hacked")


class TestAgentStatus:
    """Tests for agent active/inactive status."""

    def test_agent_active_by_default(self, agent_identity, alice):
        """Newly registered agents should be active by default."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
        
        assert agent_identity.isActive(agent_id) is True

    def test_deactivate_agent(self, agent_identity, alice):
        """Owner should be able to deactivate their agent."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.setAgentStatus(agent_id, False)
        
        assert agent_identity.isActive(agent_id) is False

    def test_reactivate_agent(self, agent_identity, alice):
        """Owner should be able to reactivate their agent."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.setAgentStatus(agent_id, False)
            agent_identity.setAgentStatus(agent_id, True)
        
        assert agent_identity.isActive(agent_id) is True

    def test_set_status_not_owner_fails(self, agent_identity, alice, bob):
        """Non-owner should not be able to change agent status."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
        
        with boa.env.prank(bob):
            with pytest.raises(boa.BoaError, match="not owner"):
                agent_identity.setAgentStatus(agent_id, False)

    def test_is_active_nonexistent_agent_fails(self, agent_identity):
        """isActive should revert for nonexistent agent."""
        with pytest.raises(boa.BoaError, match="nonexistent"):
            agent_identity.isActive(999)


class TestERC721Core:
    """Tests for core ERC-721 functionality."""

    def test_balance_of(self, agent_identity, alice, bob):
        """balanceOf should return correct token count."""
        assert agent_identity.balanceOf(alice) == 0
        
        with boa.env.prank(alice):
            agent_identity.registerAgent("ipfs://1")
            agent_identity.registerAgent("ipfs://2")
        
        with boa.env.prank(bob):
            agent_identity.registerAgent("ipfs://3")
        
        assert agent_identity.balanceOf(alice) == 2
        assert agent_identity.balanceOf(bob) == 1

    def test_balance_of_zero_address_fails(self, agent_identity):
        """balanceOf should revert for zero address."""
        with pytest.raises(boa.BoaError, match="zero address"):
            agent_identity.balanceOf("0x0000000000000000000000000000000000000000")

    def test_owner_of_nonexistent_fails(self, agent_identity):
        """ownerOf should revert for nonexistent token."""
        with pytest.raises(boa.BoaError, match="nonexistent"):
            agent_identity.ownerOf(999)

    def test_token_uri_nonexistent_fails(self, agent_identity):
        """tokenURI should revert for nonexistent token."""
        with pytest.raises(boa.BoaError, match="nonexistent"):
            agent_identity.tokenURI(999)


class TestERC721Transfers:
    """Tests for ERC-721 transfer functionality."""

    def test_transfer_from(self, agent_identity, alice, bob):
        """Owner should be able to transfer their agent."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.transferFrom(alice, bob, agent_id)
        
        assert agent_identity.ownerOf(agent_id) == bob
        assert agent_identity.balanceOf(alice) == 0
        assert agent_identity.balanceOf(bob) == 1

    def test_transfer_clears_approval(self, agent_identity, alice, bob, charlie):
        """Transfer should clear existing approval."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.approve(charlie, agent_id)
            assert agent_identity.getApproved(agent_id) == charlie
            
            agent_identity.transferFrom(alice, bob, agent_id)
        
        # Approval should be cleared
        assert agent_identity.getApproved(agent_id) == "0x0000000000000000000000000000000000000000"

    def test_transfer_not_owner_fails(self, agent_identity, alice, bob, charlie):
        """Non-owner without approval should not transfer."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
        
        with boa.env.prank(bob):
            with pytest.raises(boa.BoaError, match="not authorized"):
                agent_identity.transferFrom(alice, charlie, agent_id)

    def test_transfer_to_zero_address_fails(self, agent_identity, alice):
        """Transfer to zero address should fail."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            
            with pytest.raises(boa.BoaError, match="zero address"):
                agent_identity.transferFrom(alice, "0x0000000000000000000000000000000000000000", agent_id)


class TestERC721Approvals:
    """Tests for ERC-721 approval functionality."""

    def test_approve(self, agent_identity, alice, bob):
        """Owner should be able to approve another address."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.approve(bob, agent_id)
        
        assert agent_identity.getApproved(agent_id) == bob

    def test_approved_can_transfer(self, agent_identity, alice, bob, charlie):
        """Approved address should be able to transfer."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.approve(bob, agent_id)
        
        with boa.env.prank(bob):
            agent_identity.transferFrom(alice, charlie, agent_id)
        
        assert agent_identity.ownerOf(agent_id) == charlie

    def test_get_approved_nonexistent_fails(self, agent_identity):
        """getApproved should revert for nonexistent token."""
        with pytest.raises(boa.BoaError, match="nonexistent"):
            agent_identity.getApproved(999)

    def test_set_approval_for_all(self, agent_identity, alice, operator):
        """Should be able to set operator approval for all tokens."""
        with boa.env.prank(alice):
            agent_identity.setApprovalForAll(operator, True)
        
        assert agent_identity.isApprovedForAll(alice, operator) is True

    def test_operator_can_transfer(self, agent_identity, alice, bob, operator):
        """Operator should be able to transfer any of owner's tokens."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.setApprovalForAll(operator, True)
        
        with boa.env.prank(operator):
            agent_identity.transferFrom(alice, bob, agent_id)
        
        assert agent_identity.ownerOf(agent_id) == bob

    def test_operator_can_approve(self, agent_identity, alice, bob, operator):
        """Operator should be able to approve on behalf of owner."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.setApprovalForAll(operator, True)
        
        with boa.env.prank(operator):
            agent_identity.approve(bob, agent_id)
        
        assert agent_identity.getApproved(agent_id) == bob

    def test_revoke_operator_approval(self, agent_identity, alice, bob, operator):
        """Should be able to revoke operator approval."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.setApprovalForAll(operator, True)
            agent_identity.setApprovalForAll(operator, False)
        
        assert agent_identity.isApprovedForAll(alice, operator) is False
        
        with boa.env.prank(operator):
            with pytest.raises(boa.BoaError, match="not authorized"):
                agent_identity.transferFrom(alice, bob, agent_id)

    def test_approve_self_fails(self, agent_identity, alice):
        """Should not be able to approve self as operator."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="approve to caller"):
                agent_identity.setApprovalForAll(alice, True)


class TestSafeTransfer:
    """Tests for safeTransferFrom functionality."""

    def test_safe_transfer_to_eoa(self, agent_identity, alice, bob):
        """safeTransferFrom should work for EOA recipients."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.safeTransferFrom(alice, bob, agent_id)
        
        assert agent_identity.ownerOf(agent_id) == bob

    def test_safe_transfer_to_receiver_contract(self, agent_identity, alice, erc721_receiver):
        """safeTransferFrom should work for contracts implementing IERC721Receiver."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.safeTransferFrom(alice, erc721_receiver.address, agent_id)
        
        assert agent_identity.ownerOf(agent_id) == erc721_receiver.address
        assert erc721_receiver.received_count() == 1
        assert erc721_receiver.last_token_id() == agent_id

    def test_safe_transfer_to_bad_receiver_fails(self, agent_identity, alice, bad_receiver):
        """safeTransferFrom should fail for contracts that don't properly implement receiver."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            
            with pytest.raises(boa.BoaError, match="unsafe recipient"):
                agent_identity.safeTransferFrom(alice, bad_receiver.address, agent_id)

    def test_safe_transfer_with_data(self, agent_identity, alice, erc721_receiver):
        """safeTransferFrom should pass data to receiver."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.safeTransferFrom(alice, erc721_receiver.address, agent_id, b"hello")
        
        assert agent_identity.ownerOf(agent_id) == erc721_receiver.address


class TestAgentOwnershipAfterTransfer:
    """Tests to ensure agent-specific functions work correctly after transfer."""

    def test_new_owner_can_update_uri(self, agent_identity, alice, bob):
        """New owner should be able to update agent URI after transfer."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://original")
            agent_identity.transferFrom(alice, bob, agent_id)
        
        with boa.env.prank(bob):
            agent_identity.updateAgentURI(agent_id, "ipfs://updated")
        
        assert agent_identity.tokenURI(agent_id) == "ipfs://updated"

    def test_old_owner_cannot_update_after_transfer(self, agent_identity, alice, bob):
        """Previous owner should not be able to update agent after transfer."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://original")
            agent_identity.transferFrom(alice, bob, agent_id)
        
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="not owner"):
                agent_identity.updateAgentURI(agent_id, "ipfs://hacked")

    def test_new_owner_can_change_status(self, agent_identity, alice, bob):
        """New owner should be able to change agent status after transfer."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://test")
            agent_identity.transferFrom(alice, bob, agent_id)
        
        with boa.env.prank(bob):
            agent_identity.setAgentStatus(agent_id, False)
        
        assert agent_identity.isActive(agent_id) is False
