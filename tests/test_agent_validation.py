"""
Tests for AgentValidation.vy - ERC-8004 Validation Registry

This test suite covers:
- Validator management
- Validation requests
- Validation submission
- Status tracking
"""

import pytest
import boa


@pytest.fixture
def agent_validation(agent_identity, deployer):
    """Deploy the AgentValidation contract."""
    with boa.env.prank(deployer):
        return boa.load("contracts/AgentValidation.vy", agent_identity.address)


@pytest.fixture
def validator(deployer):
    """A designated validator address."""
    return boa.env.generate_address("validator")


class TestAgentValidationDeployment:
    """Tests for contract deployment."""

    def test_initial_state(self, agent_validation, agent_identity, deployer):
        """Contract should initialize correctly."""
        assert agent_validation.identityRegistry() == agent_identity.address
        assert agent_validation.admin() == deployer
        assert agent_validation.nextValidationId() == 1

    def test_deploy_with_zero_address_fails(self):
        """Should fail to deploy with zero address."""
        with pytest.raises(boa.BoaError, match="zero address"):
            boa.load("contracts/AgentValidation.vy", "0x0000000000000000000000000000000000000000")


class TestValidatorManagement:
    """Tests for adding/removing validators."""

    def test_add_validator(self, agent_validation, deployer, validator):
        """Admin should be able to add a validator."""
        with boa.env.prank(deployer):
            agent_validation.addValidator(validator, 1)  # Trusted Judge
        
        assert agent_validation.isValidator(validator) is True
        assert agent_validation.validatorType(validator) == 1

    def test_add_validator_all_types(self, agent_validation, deployer):
        """Should support all validator types."""
        v1 = boa.env.generate_address("v1")
        v2 = boa.env.generate_address("v2")
        v3 = boa.env.generate_address("v3")
        
        with boa.env.prank(deployer):
            agent_validation.addValidator(v1, 1)  # Trusted Judge
            agent_validation.addValidator(v2, 2)  # Staked
            agent_validation.addValidator(v3, 3)  # Cryptographic
        
        assert agent_validation.validatorType(v1) == 1
        assert agent_validation.validatorType(v2) == 2
        assert agent_validation.validatorType(v3) == 3

    def test_add_validator_invalid_type_fails(self, agent_validation, deployer, validator):
        """Should fail with invalid validator type."""
        with boa.env.prank(deployer):
            with pytest.raises(boa.BoaError, match="invalid type"):
                agent_validation.addValidator(validator, 0)
            
            with pytest.raises(boa.BoaError, match="invalid type"):
                agent_validation.addValidator(validator, 4)

    def test_add_validator_not_admin_fails(self, agent_validation, alice, validator):
        """Non-admin should not be able to add validators."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="not admin"):
                agent_validation.addValidator(validator, 1)

    def test_remove_validator(self, agent_validation, deployer, validator):
        """Admin should be able to remove a validator."""
        with boa.env.prank(deployer):
            agent_validation.addValidator(validator, 1)
            agent_validation.removeValidator(validator)
        
        assert agent_validation.isValidator(validator) is False
        assert agent_validation.validatorType(validator) == 0

    def test_transfer_admin(self, agent_validation, deployer, alice):
        """Admin should be able to transfer admin role."""
        with boa.env.prank(deployer):
            agent_validation.transferAdmin(alice)
        
        assert agent_validation.admin() == alice


class TestValidationRequest:
    """Tests for requesting validation."""

    def test_request_validation(self, agent_validation, agent_identity, alice, charlie):
        """Should successfully request validation."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        task_hash = b'\x12\x34' + b'\x00' * 30
        with boa.env.prank(charlie):
            validation_id = agent_validation.requestValidation(agent_id, task_hash)
        
        assert validation_id == 1
        assert agent_validation.validationAgent(validation_id) == agent_id
        assert agent_validation.validationRequester(validation_id) == charlie
        assert agent_validation.validationTaskHash(validation_id) == task_hash
        assert agent_validation.validationStatus(validation_id) == 1  # PENDING

    def test_request_validation_increments_count(self, agent_validation, agent_identity, alice, charlie):
        """Agent validation count should increment."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        assert agent_validation.getAgentValidationCount(agent_id) == 0
        
        with boa.env.prank(charlie):
            agent_validation.requestValidation(agent_id, b'\x11' * 32)
            agent_validation.requestValidation(agent_id, b'\x22' * 32)
        
        assert agent_validation.getAgentValidationCount(agent_id) == 2

    def test_request_validation_nonexistent_agent_fails(self, agent_validation, charlie):
        """Should fail for nonexistent agent."""
        with boa.env.prank(charlie):
            with pytest.raises(boa.BoaError, match="agent not found"):
                agent_validation.requestValidation(999, b'\x00' * 32)

    def test_request_validation_empty_hash_fails(self, agent_validation, agent_identity, alice, charlie):
        """Should fail with empty task hash."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            with pytest.raises(boa.BoaError, match="empty task hash"):
                agent_validation.requestValidation(agent_id, b'\x00' * 32)


class TestValidationSubmission:
    """Tests for submitting validation results."""

    def test_submit_validation_approved(self, agent_validation, agent_identity, deployer, alice, charlie, validator):
        """Validator should be able to approve validation."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            validation_id = agent_validation.requestValidation(agent_id, b'\x12' * 32)
        
        with boa.env.prank(deployer):
            agent_validation.addValidator(validator, 1)
        
        with boa.env.prank(validator):
            agent_validation.submitValidation(validation_id, True, "ipfs://evidence")
        
        assert agent_validation.validationStatus(validation_id) == 2  # APPROVED
        assert agent_validation.isValidationApproved(validation_id) is True
        assert agent_validation.validationValidator(validation_id) == validator
        assert agent_validation.validationEvidence(validation_id) == "ipfs://evidence"

    def test_submit_validation_rejected(self, agent_validation, agent_identity, deployer, alice, charlie, validator):
        """Validator should be able to reject validation."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            validation_id = agent_validation.requestValidation(agent_id, b'\x12' * 32)
        
        with boa.env.prank(deployer):
            agent_validation.addValidator(validator, 1)
        
        with boa.env.prank(validator):
            agent_validation.submitValidation(validation_id, False, "ipfs://rejection-reason")
        
        assert agent_validation.validationStatus(validation_id) == 3  # REJECTED
        assert agent_validation.isValidationApproved(validation_id) is False

    def test_submit_validation_not_validator_fails(self, agent_validation, agent_identity, alice, charlie):
        """Non-validator should not be able to submit."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            validation_id = agent_validation.requestValidation(agent_id, b'\x12' * 32)
        
        with boa.env.prank(charlie):
            with pytest.raises(boa.BoaError, match="not validator"):
                agent_validation.submitValidation(validation_id, True, "ipfs://evidence")

    def test_submit_validation_twice_fails(self, agent_validation, agent_identity, deployer, alice, charlie, validator):
        """Should not be able to submit validation twice."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        with boa.env.prank(charlie):
            validation_id = agent_validation.requestValidation(agent_id, b'\x12' * 32)
        
        with boa.env.prank(deployer):
            agent_validation.addValidator(validator, 1)
        
        with boa.env.prank(validator):
            agent_validation.submitValidation(validation_id, True, "ipfs://evidence")
        
        with boa.env.prank(validator):
            with pytest.raises(boa.BoaError, match="not pending"):
                agent_validation.submitValidation(validation_id, False, "ipfs://change")

    def test_submit_validation_invalid_id_fails(self, agent_validation, deployer, validator):
        """Should fail for invalid validation ID."""
        with boa.env.prank(deployer):
            agent_validation.addValidator(validator, 1)
        
        with boa.env.prank(validator):
            with pytest.raises(boa.BoaError, match="invalid id"):
                agent_validation.submitValidation(0, True, "ipfs://evidence")
            
            with pytest.raises(boa.BoaError, match="invalid id"):
                agent_validation.submitValidation(999, True, "ipfs://evidence")


class TestValidationQueries:
    """Tests for querying validation data."""

    def test_get_validation_status(self, agent_validation, agent_identity, alice, charlie):
        """Should return correct status."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        # Non-existent validation
        assert agent_validation.getValidationStatus(999) == 0  # NONE
        
        # Pending validation
        with boa.env.prank(charlie):
            validation_id = agent_validation.requestValidation(agent_id, b'\x12' * 32)
        
        assert agent_validation.getValidationStatus(validation_id) == 1  # PENDING

    def test_get_validation_details(self, agent_validation, agent_identity, deployer, alice, charlie, validator):
        """Should return all validation details."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent1")
        
        task_hash = b'\xab\xcd' * 16
        with boa.env.prank(charlie):
            validation_id = agent_validation.requestValidation(agent_id, task_hash)
        
        with boa.env.prank(deployer):
            agent_validation.addValidator(validator, 2)
        
        with boa.env.prank(validator):
            agent_validation.submitValidation(validation_id, True, "ipfs://proof")
        
        result = agent_validation.getValidationDetails(validation_id)
        
        assert result[0] == agent_id           # agentId
        assert result[1] == charlie            # requester
        assert result[2] == task_hash          # taskHash
        assert result[3] == 2                  # status (APPROVED)
        assert result[4] == validator          # validator
        assert result[5] == "ipfs://proof"     # evidenceURI

    def test_get_validation_details_invalid_id_fails(self, agent_validation):
        """Should fail for invalid ID."""
        with pytest.raises(boa.BoaError, match="invalid id"):
            agent_validation.getValidationDetails(0)
        
        with pytest.raises(boa.BoaError, match="invalid id"):
            agent_validation.getValidationDetails(999)
