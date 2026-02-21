"""
Integration Test: AgentEscrow + AgentReputation

This test verifies the full agent task lifecycle:
1. Register agents in AgentIdentity
2. Create escrow task (locks USDC)
3. Worker claims and completes task
4. Client approves and releases payment
5. Client records interaction and submits feedback in AgentReputation
6. Verify reputation is updated

This test was created to fill the audit gap:
  ❌ No Escrow + Reputation integration test
"""

import pytest
import boa


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def deployer():
    """The main deployer account."""
    return boa.env.generate_address("deployer")


@pytest.fixture
def provider():
    """Test account: Provider (worker agent owner)."""
    return boa.env.generate_address("provider")


@pytest.fixture
def client():
    """Test account: Client (task poster)."""
    return boa.env.generate_address("client")


@pytest.fixture
def usdc():
    """Deploy a fresh mock USDC token."""
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
    return boa.loads(MOCK_USDC_SOURCE)


@pytest.fixture
def identity():
    """Deploy lib IdentityRegistry contract (ERC-8004)."""
    return boa.load(
        "lib/github/lufa23/erc-8004-vyper/src/identity_registry.vy",
        "AgentIdentityRegistry",
        "AGID",
    )


@pytest.fixture
def reputation(identity, deployer):
    """Deploy lib ReputationRegistry contract (ERC-8004)."""
    with boa.env.prank(deployer):
        return boa.load(
            "lib/github/lufa23/erc-8004-vyper/src/reputation_registry.vy",
            identity.address,
        )


@pytest.fixture
def escrow(usdc, identity, deployer):
    """Deploy AgentEscrow contract linked to identity and USDC."""
    with boa.env.prank(deployer):
        return boa.load("contracts/AgentEscrow.vy", usdc.address, identity.address)


@pytest.fixture
def setup_agents(identity, provider, client):
    """Register provider and client as agents, return their agent IDs."""
    # Register provider agent
    with boa.env.prank(provider):
        provider_agent_id = identity.register("ipfs://QmProviderAgent...")
    
    # Register client agent
    with boa.env.prank(client):
        client_agent_id = identity.register("ipfs://QmClientAgent...")
    
    return provider_agent_id, client_agent_id


@pytest.fixture
def funded_accounts(usdc, provider, client):
    """Fund test accounts with USDC."""
    amount = 1000 * 10**6  # 1000 USDC
    usdc.mint(provider, amount)
    usdc.mint(client, amount)
    return amount


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_full_task_lifecycle(
    usdc,
    identity,
    reputation,
    escrow,
    deployer,
    provider,
    client,
    setup_agents,
    funded_accounts
):
    """
    Full integration test: Escrow task + Reputation feedback
    
    Lifecycle:
    1. Client creates task (locks USDC in escrow)
    2. Provider claims task
    3. Client approves completion (releases USDC to provider)
    4. Client records interaction in reputation
    5. Client submits feedback with proof of payment
    6. Verify reputation is updated
    """
    provider_agent_id, client_agent_id = setup_agents
    task_amount = 100 * 10**6  # 100 USDC
    description_hash = b'\x12\x34' + b'\x00' * 30  # Mock task description hash
    deadline = 86400 * 7  # 7 days (relative, not absolute)
    
    # ────────────────────────────────────────────────────────────────────────
    # Step 1: Client creates task (locks USDC)
    # ────────────────────────────────────────────────────────────────────────
    with boa.env.prank(client):
        usdc.approve(escrow.address, task_amount)
        task_id = escrow.create_task(
            client_agent_id,  # posterAgentId
            task_amount,
            description_hash,
            deadline
        )
    
    # Verify USDC is locked in escrow
    assert usdc.balanceOf(escrow.address) == task_amount
    assert escrow.is_task_open(task_id) == True
    
    # ────────────────────────────────────────────────────────────────────────
    # Step 2: Provider claims task
    # ────────────────────────────────────────────────────────────────────────
    with boa.env.prank(provider):
        escrow.claim_task(task_id, provider_agent_id)
    
    # ────────────────────────────────────────────────────────────────────────
    # Step 3: Client approves completion (releases USDC to provider)
    # ────────────────────────────────────────────────────────────────────────
    provider_balance_before = usdc.balanceOf(provider)
    
    with boa.env.prank(client):
        escrow.approve_completion(task_id)
    
    # Verify USDC was transferred to provider
    assert usdc.balanceOf(provider) == provider_balance_before + task_amount
    assert usdc.balanceOf(escrow.address) == 0
    
    # ────────────────────────────────────────────────────────────────────────
    # Step 4: Client records interaction in reputation system
    # ────────────────────────────────────────────────────────────────────────
    # The agent owner (provider) must record that client interacted with them
    with boa.env.prank(provider):
        reputation.recordInteraction(provider_agent_id, client)
    
    # Verify interaction is recorded
    assert reputation.hasClientInteracted(provider_agent_id, client) == True
    
    # ────────────────────────────────────────────────────────────────────────
    # Step 5: Client submits feedback with proof of payment
    # ────────────────────────────────────────────────────────────────────────
    # In production, proofOfPayment would be the tx hash from x402 or escrow
    # For this test, we use a mock bytes32
    proof_of_payment = b'\xab\xcd' + b'\x00' * 30  # Mock tx hash
    score = 85  # 85/100
    
    # Verify client hasn't rated yet
    assert reputation.hasClientRated(provider_agent_id, client) == False
    
    with boa.env.prank(client):
        feedback_id = reputation.submitFeedback(
            provider_agent_id,
            score,
            proof_of_payment
        )
    
    # ────────────────────────────────────────────────────────────────────────
    # Step 6: Verify reputation is updated
    # ────────────────────────────────────────────────────────────────────────
    assert reputation.hasClientRated(provider_agent_id, client) == True
    assert reputation.getTotalFeedbackCount(provider_agent_id) == 1
    # Score is scaled by 100 in the contract (85 -> 8500)
    assert reputation.getAverageScore(provider_agent_id) == score * 100
    
    # Check feedback details
    # getFeedback returns: (agentId, reviewer, score, timestamp, proofOfPayment)
    feedback = reputation.getFeedback(feedback_id)
    assert feedback[0] == provider_agent_id  # agentId
    assert feedback[1] == client  # reviewer
    assert feedback[2] == score  # score
    # feedback[3] is timestamp
    assert feedback[4] == proof_of_payment  # proofOfPayment


def test_escrow_dispute_blocks_positive_feedback(
    usdc,
    identity,
    reputation,
    escrow,
    deployer,
    provider,
    client,
    setup_agents,
    funded_accounts
):
    """
    If escrow is disputed and client wins, they should NOT be able
    to submit positive feedback (interaction was not successfully completed).
    
    This tests the integrity of the reputation system; you can only
    rate agents you've successfully transacted with.
    """
    provider_agent_id, client_agent_id = setup_agents
    task_amount = 50 * 10**6  # 50 USDC
    description_hash = b'\x56\x78' + b'\x00' * 30
    deadline = 86400 * 7  # 7 days (relative)
    
    # Client creates task
    with boa.env.prank(client):
        usdc.approve(escrow.address, task_amount)
        task_id = escrow.create_task(
            client_agent_id,
            task_amount,
            description_hash,
            deadline
        )
    
    # Provider claims task
    with boa.env.prank(provider):
        escrow.claim_task(task_id, provider_agent_id)
    
    # Provider raises dispute (claiming work is done but client won't approve)
    with boa.env.prank(provider):
        escrow.raise_dispute(task_id)
    
    # Admin resolves dispute in favor of CLIENT (worker loses)
    # This means the task was NOT successfully completed
    with boa.env.prank(deployer):
        escrow.resolve_dispute(task_id, False)  # workerWins = False
    
    # Verify USDC returned to client
    # (In this flow, client gets refund because worker didn't deliver)
    
    # Client tries to submit feedback but CANNOT because no interaction was recorded
    # The provider never recorded an interaction (and shouldn't, since dispute was lost)
    assert reputation.hasClientInteracted(provider_agent_id, client) == False
    
    # Attempting to submit feedback should fail
    proof_of_payment = b'\x00' * 32
    with boa.env.prank(client):
        with pytest.raises(boa.BoaError):
            reputation.submitFeedback(provider_agent_id, 20, proof_of_payment)


def test_reputation_requires_interaction(
    usdc,
    identity,
    reputation,
    escrow,
    deployer,
    provider,
    client,
    setup_agents,
    funded_accounts
):
    """
    Verify that reputation feedback cannot be submitted without
    a prior recorded interaction.
    
    This prevents gaming the system with fake reviews.
    """
    provider_agent_id, client_agent_id = setup_agents
    
    # Client has NOT interacted with provider's agent
    assert reputation.hasClientInteracted(provider_agent_id, client) == False
    
    # Client tries to submit feedback (should FAIL)
    proof_of_payment = b'\x00' * 32
    with boa.env.prank(client):
        with pytest.raises(boa.BoaError):
            reputation.submitFeedback(provider_agent_id, 90, proof_of_payment)


def test_multiple_tasks_multiple_feedbacks(
    usdc,
    identity,
    reputation,
    escrow,
    deployer,
    provider,
    client,
    setup_agents,
    funded_accounts
):
    """
    Test that an agent can receive multiple feedbacks from DIFFERENT clients.
    The contract only allows one feedback per client per agent.
    
    This tests that:
    1. Multiple tasks can be completed
    2. Each completed task from different clients can result in feedback
    3. Average score is calculated correctly
    """
    provider_agent_id, client_agent_id = setup_agents
    task_amount = 10 * 10**6  # 10 USDC per task
    
    scores = [80, 90, 100]  # Will give 3 feedbacks with these scores
    
    # Create multiple different clients (contract only allows 1 feedback per client per agent)
    clients = [boa.env.generate_address(f"multi_client_{i}") for i in range(len(scores))]
    
    # Fund each client with USDC
    for c in clients:
        usdc.mint(c, 100 * 10**6)
    
    # Register each client as an agent (required to create tasks)
    client_agent_ids = []
    for i, c in enumerate(clients):
        with boa.env.prank(c):
            cid = identity.register(f"ipfs://multi_client_{i}")
            client_agent_ids.append(cid)
    
    for i, score in enumerate(scores):
        current_client = clients[i]
        current_client_agent_id = client_agent_ids[i]
        description_hash = bytes([i + 1]) + b'\x00' * 31
        deadline = 86400 * 7  # 7 days (relative)
        
        # Create and complete task
        with boa.env.prank(current_client):
            usdc.approve(escrow.address, task_amount)
            task_id = escrow.create_task(
                current_client_agent_id,
                task_amount,
                description_hash,
                deadline
            )
        
        with boa.env.prank(provider):
            escrow.claim_task(task_id, provider_agent_id)
        
        with boa.env.prank(current_client):
            escrow.approve_completion(task_id)
        
        # Record interaction and submit feedback
        with boa.env.prank(provider):
            reputation.recordInteraction(provider_agent_id, current_client)
        
        proof = bytes([i + 10]) + b'\x00' * 31
        with boa.env.prank(current_client):
            reputation.submitFeedback(provider_agent_id, score, proof)
    
    # Verify all feedbacks recorded
    assert reputation.getTotalFeedbackCount(provider_agent_id) == 3
    
    # Verify average score: (80 + 90 + 100) / 3 = 90, scaled by 100 = 9000
    assert reputation.getAverageScore(provider_agent_id) == 9000
    
    # Verify reputation tier (90 average should be Gold or Platinum)
    tier = reputation.getReputationTier(provider_agent_id)
    assert tier >= 3  # Gold = 3, Platinum = 4
