"""
Tests for AgentEscrow.vy - Escrow for Agent-to-Agent Tasks

This test suite covers:
- Task creation with USDC locking
- Task claiming
- Task completion and payment release
- Cancellation
- Dispute resolution
- Deadline-based auto-release
"""

import pytest
import boa


@pytest.fixture
def agent_escrow(funded_usdc, agent_identity, deployer):
    """Deploy the AgentEscrow contract."""
    with boa.env.prank(deployer):
        return boa.load(
            "contracts/AgentEscrow.vy",
            funded_usdc.address,
            agent_identity.address
        )


class TestAgentEscrowDeployment:
    """Tests for contract deployment."""

    def test_initial_state(self, agent_escrow, funded_usdc, agent_identity, deployer):
        """Contract should initialize correctly."""
        assert agent_escrow.usdc() == funded_usdc.address
        assert agent_escrow.identityRegistry() == agent_identity.address
        assert agent_escrow.admin() == deployer
        assert agent_escrow.nextTaskId() == 1

    def test_deploy_with_zero_usdc_fails(self, agent_identity):
        """Should fail with zero USDC address."""
        with pytest.raises(boa.BoaError, match="zero USDC"):
            boa.load("contracts/AgentEscrow.vy", 
                    "0x0000000000000000000000000000000000000000",
                    agent_identity.address)

    def test_deploy_with_zero_identity_fails(self, funded_usdc):
        """Should fail with zero identity address."""
        with pytest.raises(boa.BoaError, match="zero identity"):
            boa.load("contracts/AgentEscrow.vy",
                    funded_usdc.address,
                    "0x0000000000000000000000000000000000000000")


class TestTaskCreation:
    """Tests for creating tasks."""

    def test_create_task(self, agent_escrow, agent_identity, funded_usdc, alice):
        """Should create a task with USDC locked."""
        # Register agent
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://poster-agent")
        
        amount = 100 * 10**6  # 100 USDC
        task_hash = b'\x12\x34' + b'\x00' * 30
        
        # Approve and create task
        with boa.env.prank(alice):
            funded_usdc.approve(agent_escrow.address, amount)
            task_id = agent_escrow.createTask(agent_id, amount, task_hash, 0)
        
        assert task_id == 1
        assert agent_escrow.taskPoster(task_id) == alice
        assert agent_escrow.taskPosterAgentId(task_id) == agent_id
        assert agent_escrow.taskAmount(task_id) == amount
        assert agent_escrow.taskStatus(task_id) == 0  # OPEN
        
        # USDC should be locked in escrow
        assert funded_usdc.balanceOf(agent_escrow.address) == amount

    def test_create_task_custom_deadline(self, agent_escrow, agent_identity, funded_usdc, alice):
        """Should accept custom deadline."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent")
            funded_usdc.approve(agent_escrow.address, 10 * 10**6)
            task_id = agent_escrow.createTask(agent_id, 10 * 10**6, b'\x00' * 32, 172800)  # 2 days
        
        # Deadline should be ~2 days from now
        deadline = agent_escrow.taskDeadline(task_id)
        created_at = agent_escrow.taskCreatedAt(task_id)
        assert deadline - created_at == 172800

    def test_create_task_zero_amount_fails(self, agent_escrow, agent_identity, alice):
        """Should fail with zero amount."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent")
        
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="zero amount"):
                agent_escrow.createTask(agent_id, 0, b'\x00' * 32, 0)

    def test_create_task_not_agent_owner_fails(self, agent_escrow, agent_identity, funded_usdc, alice, bob):
        """Should fail if caller is not agent owner."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://alice-agent")
        
        with boa.env.prank(bob):
            funded_usdc.approve(agent_escrow.address, 10 * 10**6)
            with pytest.raises(boa.BoaError, match="not agent owner"):
                agent_escrow.createTask(agent_id, 10 * 10**6, b'\x00' * 32, 0)

    def test_create_task_deadline_too_short_fails(self, agent_escrow, agent_identity, funded_usdc, alice):
        """Should fail if deadline is too short."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://agent")
            funded_usdc.approve(agent_escrow.address, 10 * 10**6)
            
            with pytest.raises(boa.BoaError, match="deadline too short"):
                agent_escrow.createTask(agent_id, 10 * 10**6, b'\x00' * 32, 3600)  # 1 hour


class TestTaskClaiming:
    """Tests for claiming tasks."""

    def test_claim_task(self, agent_escrow, agent_identity, funded_usdc, alice, bob):
        """Worker should be able to claim an open task."""
        # Alice creates task
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, 50 * 10**6)
            task_id = agent_escrow.createTask(alice_agent, 50 * 10**6, b'\x00' * 32, 0)
        
        # Bob claims task
        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)
        
        assert agent_escrow.taskWorker(task_id) == bob
        assert agent_escrow.taskWorkerAgentId(task_id) == bob_agent
        assert agent_escrow.taskStatus(task_id) == 1  # CLAIMED

    def test_claim_own_task_fails(self, agent_escrow, agent_identity, funded_usdc, alice):
        """Should not be able to claim own task."""
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, 50 * 10**6)
            task_id = agent_escrow.createTask(agent_id, 50 * 10**6, b'\x00' * 32, 0)
        
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="cannot claim own task"):
                agent_escrow.claimTask(task_id, agent_id)

    def test_claim_already_claimed_fails(self, agent_escrow, agent_identity, funded_usdc, alice, bob, charlie):
        """Should not be able to claim already claimed task."""
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, 50 * 10**6)
            task_id = agent_escrow.createTask(alice_agent, 50 * 10**6, b'\x00' * 32, 0)
        
        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)
        
        with boa.env.prank(charlie):
            charlie_agent = agent_identity.registerAgent("ipfs://charlie")
            with pytest.raises(boa.BoaError, match="task not open"):
                agent_escrow.claimTask(task_id, charlie_agent)


class TestTaskCompletion:
    """Tests for task completion and payment release."""

    def test_approve_completion(self, agent_escrow, agent_identity, funded_usdc, alice, bob):
        """Poster should be able to approve and release payment."""
        amount = 75 * 10**6
        
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, amount)
            task_id = agent_escrow.createTask(alice_agent, amount, b'\x00' * 32, 0)
        
        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)
        
        bob_balance_before = funded_usdc.balanceOf(bob)
        
        with boa.env.prank(alice):
            agent_escrow.approveCompletion(task_id)
        
        assert agent_escrow.taskStatus(task_id) == 2  # COMPLETED
        assert agent_escrow.taskAmount(task_id) == 0
        assert funded_usdc.balanceOf(bob) == bob_balance_before + amount

    def test_approve_not_poster_fails(self, agent_escrow, agent_identity, funded_usdc, alice, bob, charlie):
        """Only poster can approve completion."""
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, 50 * 10**6)
            task_id = agent_escrow.createTask(alice_agent, 50 * 10**6, b'\x00' * 32, 0)
        
        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)
        
        with boa.env.prank(charlie):
            with pytest.raises(boa.BoaError, match="not poster"):
                agent_escrow.approveCompletion(task_id)


class TestCancellation:
    """Tests for task cancellation."""

    def test_cancel_open_task(self, agent_escrow, agent_identity, funded_usdc, alice):
        """Poster should be able to cancel open task."""
        amount = 100 * 10**6
        
        with boa.env.prank(alice):
            agent_id = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, amount)
            task_id = agent_escrow.createTask(agent_id, amount, b'\x00' * 32, 0)
        
        alice_balance_before = funded_usdc.balanceOf(alice)
        
        with boa.env.prank(alice):
            agent_escrow.cancelTask(task_id)
        
        assert agent_escrow.taskStatus(task_id) == 4  # CANCELLED
        assert funded_usdc.balanceOf(alice) == alice_balance_before + amount

    def test_cancel_claimed_task_fails(self, agent_escrow, agent_identity, funded_usdc, alice, bob):
        """Cannot cancel already claimed task."""
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, 50 * 10**6)
            task_id = agent_escrow.createTask(alice_agent, 50 * 10**6, b'\x00' * 32, 0)
        
        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)
        
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="task not open"):
                agent_escrow.cancelTask(task_id)


class TestDeadlineRefund:
    """Tests for deadline-based poster refund."""

    def test_refund_after_deadline(self, agent_escrow, agent_identity, funded_usdc, alice, bob):
        """Poster gets refunded after deadline."""
        amount = 50 * 10**6

        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, amount)
            # Use minimum deadline (1 day)
            task_id = agent_escrow.createTask(alice_agent, amount, b'\x00' * 32, 86400)

        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)

        # Fast forward past deadline
        boa.env.time_travel(seconds=86401)

        alice_balance_before = funded_usdc.balanceOf(alice)

        with boa.env.prank(alice):
            agent_escrow.refundAfterDeadline(task_id)

        assert agent_escrow.taskStatus(task_id) == 4  # CANCELLED
        assert funded_usdc.balanceOf(alice) == alice_balance_before + amount

    def test_refund_before_deadline_fails(self, agent_escrow, agent_identity, funded_usdc, alice, bob):
        """Cannot refund before deadline."""
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, 50 * 10**6)
            task_id = agent_escrow.createTask(alice_agent, 50 * 10**6, b'\x00' * 32, 86400)

        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)

        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="deadline not reached"):
                agent_escrow.refundAfterDeadline(task_id)


class TestDisputeResolution:
    """Tests for dispute handling."""

    def test_raise_dispute(self, agent_escrow, agent_identity, funded_usdc, alice, bob):
        """Either party can raise dispute."""
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, 50 * 10**6)
            task_id = agent_escrow.createTask(alice_agent, 50 * 10**6, b'\x00' * 32, 0)
        
        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)
        
        with boa.env.prank(alice):
            agent_escrow.raiseDispute(task_id)
        
        assert agent_escrow.taskStatus(task_id) == 3  # DISPUTED

    def test_resolve_dispute_worker_wins(self, agent_escrow, agent_identity, funded_usdc, alice, bob, deployer):
        """Admin can resolve dispute in favor of worker."""
        amount = 50 * 10**6
        
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, amount)
            task_id = agent_escrow.createTask(alice_agent, amount, b'\x00' * 32, 0)
        
        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)
        
        with boa.env.prank(alice):
            agent_escrow.raiseDispute(task_id)
        
        bob_balance_before = funded_usdc.balanceOf(bob)
        
        with boa.env.prank(deployer):  # Admin
            agent_escrow.resolveDispute(task_id, True)  # Worker wins
        
        assert agent_escrow.taskStatus(task_id) == 2  # COMPLETED
        assert funded_usdc.balanceOf(bob) == bob_balance_before + amount

    def test_resolve_dispute_poster_wins(self, agent_escrow, agent_identity, funded_usdc, alice, bob, deployer):
        """Admin can resolve dispute in favor of poster."""
        amount = 50 * 10**6
        
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, amount)
            task_id = agent_escrow.createTask(alice_agent, amount, b'\x00' * 32, 0)
        
        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)
        
        with boa.env.prank(bob):
            agent_escrow.raiseDispute(task_id)
        
        alice_balance_before = funded_usdc.balanceOf(alice)
        
        with boa.env.prank(deployer):
            agent_escrow.resolveDispute(task_id, False)  # Poster wins
        
        assert funded_usdc.balanceOf(alice) == alice_balance_before + amount

    def test_resolve_dispute_not_admin_fails(self, agent_escrow, agent_identity, funded_usdc, alice, bob, charlie):
        """Only admin can resolve disputes."""
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, 50 * 10**6)
            task_id = agent_escrow.createTask(alice_agent, 50 * 10**6, b'\x00' * 32, 0)
        
        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)
            agent_escrow.raiseDispute(task_id)
        
        with boa.env.prank(charlie):
            with pytest.raises(boa.BoaError, match="not admin"):
                agent_escrow.resolveDispute(task_id, True)


class TestViewFunctions:
    """Tests for view functions."""

    def test_get_task_details(self, agent_escrow, agent_identity, funded_usdc, alice, bob):
        """Should return all task details."""
        amount = 100 * 10**6
        
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, amount)
            task_id = agent_escrow.createTask(alice_agent, amount, b'\x00' * 32, 0)
        
        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)
        
        result = agent_escrow.getTaskDetails(task_id)
        
        assert result[0] == alice        # poster
        assert result[1] == alice_agent  # posterAgentId
        assert result[2] == bob          # worker
        assert result[3] == bob_agent    # workerAgentId
        assert result[4] == amount       # amount
        assert result[5] == 1            # status (CLAIMED)

    def test_is_task_open(self, agent_escrow, agent_identity, funded_usdc, alice, bob):
        """Should correctly report if task is open."""
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, 50 * 10**6)
            task_id = agent_escrow.createTask(alice_agent, 50 * 10**6, b'\x00' * 32, 0)
        
        assert agent_escrow.isTaskOpen(task_id) is True
        
        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)
        
        assert agent_escrow.isTaskOpen(task_id) is False

    def test_can_refund_after_deadline(self, agent_escrow, agent_identity, funded_usdc, alice, bob):
        """Should correctly report if deadline refund is possible."""
        with boa.env.prank(alice):
            alice_agent = agent_identity.registerAgent("ipfs://alice")
            funded_usdc.approve(agent_escrow.address, 50 * 10**6)
            task_id = agent_escrow.createTask(alice_agent, 50 * 10**6, b'\x00' * 32, 86400)

        with boa.env.prank(bob):
            bob_agent = agent_identity.registerAgent("ipfs://bob")
            agent_escrow.claimTask(task_id, bob_agent)

        assert agent_escrow.canRefundAfterDeadline(task_id) is False

        boa.env.time_travel(seconds=86401)

        assert agent_escrow.canRefundAfterDeadline(task_id) is True
