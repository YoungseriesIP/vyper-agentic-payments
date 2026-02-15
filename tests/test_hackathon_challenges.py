"""
Hackathon Challenge Verification Tests

These tests verify that participants have correctly completed each challenge.
They will FAIL until the challenge templates are filled in.

Run:
  pytest tests/test_hackathon_challenges.py -v
  pytest tests/test_hackathon_challenges.py -v -k "challenge_1"
"""

import sys
from pathlib import Path

import pytest
import boa

# Mark all tests in this module as challenge
pytestmark = pytest.mark.challenge

# Add challenges directory to path
CHALLENGES_DIR = Path(__file__).resolve().parent.parent / "challenges"
sys.path.insert(0, str(CHALLENGES_DIR))


# ═══════════════════════════════════════════════════════════════════════════════
# MOCK USDC (same as conftest.py)
# ═══════════════════════════════════════════════════════════════════════════════

MOCK_USDC_SOURCE = """
# @version ^0.4.0
event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    amount: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    amount: uint256

name: public(String[64])
symbol: public(String[32])
decimals: public(uint8)
totalSupply: public(uint256)
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])

@deploy
def __init__():
    self.name = "USD Coin"
    self.symbol = "USDC"
    self.decimals = 6

@external
def mint(to: address, amount: uint256):
    self.balanceOf[to] += amount
    self.totalSupply += amount
    log Transfer(empty(address), to, amount)

@external
def transfer(to: address, amount: uint256) -> bool:
    assert self.balanceOf[msg.sender] >= amount, "Insufficient balance"
    self.balanceOf[msg.sender] -= amount
    self.balanceOf[to] += amount
    log Transfer(msg.sender, to, amount)
    return True

@external
def approve(spender: address, amount: uint256) -> bool:
    self.allowance[msg.sender][spender] = amount
    log Approval(msg.sender, spender, amount)
    return True

@external
def transferFrom(sender: address, recipient: address, amount: uint256) -> bool:
    assert self.balanceOf[sender] >= amount, "Insufficient balance"
    assert self.allowance[sender][msg.sender] >= amount, "Insufficient allowance"
    self.allowance[sender][msg.sender] -= amount
    self.balanceOf[sender] -= amount
    self.balanceOf[recipient] += amount
    log Transfer(sender, recipient, amount)
    return True
"""


# ═══════════════════════════════════════════════════════════════════════════════
# CHALLENGE 1: Agent Identity
# ═══════════════════════════════════════════════════════════════════════════════


class TestChallenge1Identity:
    """Verify Challenge 1: Register an agent."""

    @pytest.fixture
    def identity(self):
        return boa.load("contracts/AgentIdentity.vy")

    @pytest.fixture
    def agent_owner(self):
        return boa.env.generate_address("ch1_owner")

    def test_register_agent(self, identity, agent_owner):
        """Challenge 1: registerAgent() should return a valid agent ID."""
        from challenge_1_identity.challenge import register_agent

        agent_id = register_agent(
            identity,
            agent_owner,
            "ipfs://QmChallenge1TestAgent",
        )

        assert isinstance(agent_id, int)
        assert agent_id >= 1

    def test_agent_owner_is_correct(self, identity, agent_owner):
        """The registered agent should be owned by agent_owner."""
        from challenge_1_identity.challenge import register_agent

        agent_id = register_agent(identity, agent_owner, "ipfs://QmChallenge1Owner")

        assert identity.ownerOf(agent_id) == agent_owner

    def test_agent_metadata_uri(self, identity, agent_owner):
        """The agent's tokenURI should match the provided metadata URI."""
        from challenge_1_identity.challenge import register_agent

        uri = "ipfs://QmChallenge1Metadata"
        agent_id = register_agent(identity, agent_owner, uri)

        assert identity.tokenURI(agent_id) == uri

    def test_total_agents_increments(self, identity, agent_owner):
        """totalAgents should increase after registration."""
        from challenge_1_identity.challenge import register_agent

        before = identity.totalAgents()
        register_agent(identity, agent_owner, "ipfs://QmChallenge1Count")
        assert identity.totalAgents() == before + 1


# ═══════════════════════════════════════════════════════════════════════════════
# CHALLENGE 2: Reputation Feedback
# ═══════════════════════════════════════════════════════════════════════════════


class TestChallenge2Reputation:
    """Verify Challenge 2: Record interaction + submit feedback."""

    @pytest.fixture
    def deployer(self):
        return boa.env.generate_address("ch2_deployer")

    @pytest.fixture
    def identity(self):
        return boa.load("contracts/AgentIdentity.vy")

    @pytest.fixture
    def reputation(self, identity, deployer):
        with boa.env.prank(deployer):
            return boa.load("contracts/AgentReputation.vy", identity.address)

    @pytest.fixture
    def agent_owner(self):
        return boa.env.generate_address("ch2_agent_owner")

    @pytest.fixture
    def client(self):
        return boa.env.generate_address("ch2_client")

    @pytest.fixture
    def agent_id(self, identity, agent_owner):
        with boa.env.prank(agent_owner):
            return identity.registerAgent("ipfs://QmChallenge2Agent")

    def test_submit_feedback(self, reputation, identity, agent_id, agent_owner, client):
        """Challenge 2: submitFeedback() should return a valid feedback ID."""
        from challenge_2_reputation.challenge import submit_feedback

        proof = b"\xfe\xed" + b"\x00" * 30
        feedback_id = submit_feedback(
            reputation, identity, agent_id, agent_owner, client, 90, proof
        )

        assert isinstance(feedback_id, int)
        assert feedback_id >= 0

    def test_feedback_score_recorded(self, reputation, identity, agent_id, agent_owner, client):
        """Average score should reflect the submitted feedback."""
        from challenge_2_reputation.challenge import submit_feedback

        proof = b"\xca\xfe" + b"\x00" * 30
        submit_feedback(reputation, identity, agent_id, agent_owner, client, 75, proof)

        assert reputation.getAverageScore(agent_id) == 7500  # 75 * 100

    def test_client_has_rated(self, reputation, identity, agent_id, agent_owner, client):
        """hasClientRated should return True after feedback."""
        from challenge_2_reputation.challenge import submit_feedback

        proof = b"\xba\xbe" + b"\x00" * 30
        submit_feedback(reputation, identity, agent_id, agent_owner, client, 80, proof)

        assert reputation.hasClientRated(agent_id, client) is True

    def test_interaction_recorded(self, reputation, identity, agent_id, agent_owner, client):
        """hasClientInteracted should return True after recording."""
        from challenge_2_reputation.challenge import submit_feedback

        proof = b"\xde\xad" + b"\x00" * 30
        submit_feedback(reputation, identity, agent_id, agent_owner, client, 95, proof)

        assert reputation.hasClientInteracted(agent_id, client) is True


# ═══════════════════════════════════════════════════════════════════════════════
# CHALLENGE 3: Escrow Task
# ═══════════════════════════════════════════════════════════════════════════════


class TestChallenge3Escrow:
    """Verify Challenge 3: Create and complete an escrow task."""

    @pytest.fixture
    def deployer(self):
        return boa.env.generate_address("ch3_deployer")

    @pytest.fixture
    def usdc(self):
        return boa.loads(MOCK_USDC_SOURCE)

    @pytest.fixture
    def identity(self):
        return boa.load("contracts/AgentIdentity.vy")

    @pytest.fixture
    def escrow(self, usdc, identity, deployer):
        with boa.env.prank(deployer):
            return boa.load("contracts/AgentEscrow.vy", usdc.address, identity.address)

    @pytest.fixture
    def poster(self):
        return boa.env.generate_address("ch3_poster")

    @pytest.fixture
    def worker(self):
        return boa.env.generate_address("ch3_worker")

    @pytest.fixture
    def agents(self, identity, poster, worker):
        with boa.env.prank(poster):
            poster_id = identity.registerAgent("ipfs://QmPoster")
        with boa.env.prank(worker):
            worker_id = identity.registerAgent("ipfs://QmWorker")
        return poster_id, worker_id

    @pytest.fixture
    def funded_poster(self, usdc, poster):
        usdc.mint(poster, 1000 * 10**6)
        return poster

    def test_create_and_complete_task(self, escrow, usdc, funded_poster, worker, agents):
        """Challenge 3: Task should complete and release USDC to worker."""
        from challenge_3_escrow.challenge import create_and_complete_task

        poster_agent_id, worker_agent_id = agents
        amount = 50 * 10**6
        description_hash = b"\x01" + b"\x00" * 31
        deadline = 86400 * 7

        task_id = create_and_complete_task(
            escrow, usdc, funded_poster, poster_agent_id,
            worker, worker_agent_id, amount, description_hash, deadline,
        )

        assert isinstance(task_id, int)
        assert task_id >= 0

    def test_usdc_transferred_to_worker(self, escrow, usdc, funded_poster, worker, agents):
        """Worker should receive USDC after task completion."""
        from challenge_3_escrow.challenge import create_and_complete_task

        poster_agent_id, worker_agent_id = agents
        amount = 25 * 10**6

        worker_before = usdc.balanceOf(worker)

        create_and_complete_task(
            escrow, usdc, funded_poster, poster_agent_id,
            worker, worker_agent_id, amount,
            b"\x02" + b"\x00" * 31, 86400 * 7,
        )

        assert usdc.balanceOf(worker) == worker_before + amount

    def test_escrow_balance_zero_after_completion(self, escrow, usdc, funded_poster, worker, agents):
        """Escrow should have zero USDC after task completion."""
        from challenge_3_escrow.challenge import create_and_complete_task

        poster_agent_id, worker_agent_id = agents
        amount = 30 * 10**6

        create_and_complete_task(
            escrow, usdc, funded_poster, poster_agent_id,
            worker, worker_agent_id, amount,
            b"\x03" + b"\x00" * 31, 86400 * 7,
        )

        assert usdc.balanceOf(escrow.address) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# CHALLENGE 4: Spending Limits
# ═══════════════════════════════════════════════════════════════════════════════


class TestChallenge4Spending:
    """Verify Challenge 4: Authorize agent and spend with 3-tier limits."""

    @pytest.fixture
    def deployer(self):
        return boa.env.generate_address("ch4_deployer")

    @pytest.fixture
    def usdc(self):
        return boa.loads(MOCK_USDC_SOURCE)

    @pytest.fixture
    def limiter(self, usdc, deployer):
        with boa.env.prank(deployer):
            return boa.load("contracts/SpendingLimiter.vy", usdc.address)

    @pytest.fixture
    def owner(self):
        return boa.env.generate_address("ch4_owner")

    @pytest.fixture
    def agent(self):
        return boa.env.generate_address("ch4_agent")

    @pytest.fixture
    def recipient(self):
        return boa.env.generate_address("ch4_recipient")

    @pytest.fixture
    def funded_owner(self, usdc, owner):
        usdc.mint(owner, 1000 * 10**6)
        return owner

    def test_setup_and_spend(self, limiter, usdc, funded_owner, agent, recipient):
        """Challenge 4: Agent should successfully spend within limits."""
        from challenge_4_spending.challenge import setup_and_spend

        setup_and_spend(
            limiter, usdc, funded_owner, agent,
            deposit_amount=100 * 10**6,
            per_tx_limit=50 * 10**6,
            daily_limit=100 * 10**6,
            total_limit=1000 * 10**6,
            spend_amount=25 * 10**6,
            recipient=recipient,
        )

        # Should not raise — if we get here, the spend succeeded

    def test_recipient_received_usdc(self, limiter, usdc, funded_owner, agent, recipient):
        """Recipient should receive the spent USDC."""
        from challenge_4_spending.challenge import setup_and_spend

        recipient_before = usdc.balanceOf(recipient)

        setup_and_spend(
            limiter, usdc, funded_owner, agent,
            deposit_amount=100 * 10**6,
            per_tx_limit=50 * 10**6,
            daily_limit=100 * 10**6,
            total_limit=1000 * 10**6,
            spend_amount=25 * 10**6,
            recipient=recipient,
        )

        assert usdc.balanceOf(recipient) == recipient_before + 25 * 10**6

    def test_owner_balance_decreased(self, limiter, usdc, funded_owner, agent, recipient):
        """Owner's balance in the limiter should decrease after spend."""
        from challenge_4_spending.challenge import setup_and_spend

        setup_and_spend(
            limiter, usdc, funded_owner, agent,
            deposit_amount=100 * 10**6,
            per_tx_limit=50 * 10**6,
            daily_limit=100 * 10**6,
            total_limit=1000 * 10**6,
            spend_amount=25 * 10**6,
            recipient=recipient,
        )

        assert limiter.ownerBalance(funded_owner) == 75 * 10**6

    def test_total_spent_tracked(self, limiter, usdc, funded_owner, agent, recipient):
        """totalSpent should reflect the spend amount."""
        from challenge_4_spending.challenge import setup_and_spend

        setup_and_spend(
            limiter, usdc, funded_owner, agent,
            deposit_amount=100 * 10**6,
            per_tx_limit=50 * 10**6,
            daily_limit=100 * 10**6,
            total_limit=1000 * 10**6,
            spend_amount=25 * 10**6,
            recipient=recipient,
        )

        assert limiter.totalSpent(funded_owner, agent) == 25 * 10**6
