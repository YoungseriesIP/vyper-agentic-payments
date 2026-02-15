"""
Integration Test: circlekit SDK + Vyper Contracts

Tests the full stack: Flask server with x402 middleware, GatewayClient
payments, and Vyper contract interactions in the boa VM.

This mirrors the pattern from circle-titanoboa-sdk/tests/test_circlekit_integration.py
but adds contract interactions (deploy, register agents, record payment, feedback).

Run:
  pytest tests/test_sdk_contract_integration.py -v

Requires:
  pip install -e ../circle-titanoboa-sdk
  pip install flask httpx pytest-asyncio
"""

import os
import sys
import threading
import time

import pytest

# Mark all tests in this module as integration
pytestmark = pytest.mark.integration


# ═══════════════════════════════════════════════════════════════════════════════
# CONTRACT HELPERS (boa VM — no network needed)
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
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def server_thread():
    """Start a Flask server with x402 middleware in a background thread."""
    from flask import Flask, jsonify, request

    from circlekit import create_gateway_middleware

    app = Flask(__name__)
    gateway = create_gateway_middleware(
        seller_address="0x1234567890123456789012345678901234567890",
        chain="arcTestnet",
    )

    @app.route("/")
    def index():
        return jsonify({"status": "ok", "sdk": "circlekit-py"})

    @app.route("/health")
    def health():
        return jsonify({"healthy": True})

    @app.route("/api/analyze")
    @gateway.require("$0.01")
    def analyze(payment):
        return jsonify({
            "success": True,
            "service": "analyze",
            "paid_by": payment.payer,
            "amount": payment.amount,
        })

    @app.route("/api/generate", methods=["POST"])
    @gateway.require("$0.05")
    def generate(payment):
        return jsonify({
            "success": True,
            "service": "generate",
            "paid_by": payment.payer,
            "amount": payment.amount,
        })

    @app.route("/feedback", methods=["POST"])
    def feedback():
        body = request.get_json(silent=True) or {}
        return jsonify({"success": True, "feedback": body})

    def run_server():
        app.run(host="127.0.0.1", port=4098, debug=False, use_reloader=False)

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(1)

    yield "http://127.0.0.1:4098"


@pytest.fixture(scope="module")
def contracts():
    """Deploy all contracts in the boa VM (no network)."""
    import boa

    deployer = boa.env.generate_address("integration_deployer")

    usdc = boa.loads(MOCK_USDC_SOURCE)

    with boa.env.prank(deployer):
        identity = boa.load("contracts/AgentIdentity.vy")
        reputation = boa.load("contracts/AgentReputation.vy", identity.address)
        validation = boa.load("contracts/AgentValidation.vy", identity.address)
        # FIXED arg order: usdc_address first, then identity_registry
        escrow = boa.load("contracts/AgentEscrow.vy", usdc.address, identity.address)

    return {
        "usdc": usdc,
        "identity": identity,
        "reputation": reputation,
        "validation": validation,
        "escrow": escrow,
        "deployer": deployer,
    }


@pytest.fixture(scope="module")
def test_accounts():
    """Generate test accounts."""
    import boa

    return {
        "provider": boa.env.generate_address("sdk_provider"),
        "client": boa.env.generate_address("sdk_client"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: HTTP + x402
# ═══════════════════════════════════════════════════════════════════════════════


class TestHTTPEndpoints:
    """Test the Flask server HTTP endpoints."""

    def test_free_endpoint_returns_200(self, server_thread):
        """Free endpoint should return 200."""
        import httpx

        response = httpx.get(f"{server_thread}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["sdk"] == "circlekit-py"

    def test_health_endpoint_returns_200(self, server_thread):
        """Health endpoint should return 200."""
        import httpx

        response = httpx.get(f"{server_thread}/health")
        assert response.status_code == 200
        assert response.json()["healthy"] is True

    def test_paid_endpoint_returns_402(self, server_thread):
        """Paid endpoint without payment should return 402 with x402 body."""
        import httpx

        response = httpx.get(f"{server_thread}/api/analyze")
        assert response.status_code == 402

        data = response.json()
        assert "x402Version" in data
        assert data["x402Version"] == 2
        assert "accepts" in data
        assert len(data["accepts"]) >= 1
        assert data["accepts"][0]["scheme"] == "exact"
        assert data["accepts"][0]["extra"]["name"] == "GatewayWalletBatched"

    @pytest.mark.asyncio
    async def test_gateway_client_can_pay(self, server_thread):
        """GatewayClient.pay() should complete full 402 negotiation."""
        from circlekit import GatewayClient

        client = GatewayClient(
            chain="arcTestnet",
            private_key="0x0000000000000000000000000000000000000000000000000000000000000001",
        )

        result = await client.pay(f"{server_thread}/api/analyze")

        assert result.status == 200
        assert result.data["success"] is True
        assert result.data["paid_by"] == client.address
        assert result.formatted_amount == "$0.010000"

        await client.close()

    @pytest.mark.asyncio
    async def test_payment_info_contains_payer_address(self, server_thread):
        """Payment response should include correct payer address."""
        from circlekit import GatewayClient

        client = GatewayClient(
            chain="arcTestnet",
            private_key="0x0000000000000000000000000000000000000000000000000000000000000001",
        )

        result = await client.pay(f"{server_thread}/api/analyze")
        assert result.data["paid_by"] == client.address

        await client.close()

    @pytest.mark.asyncio
    async def test_gateway_client_supports_check(self, server_thread):
        """Client.supports() should detect x402 support on paid vs free endpoints."""
        from circlekit import GatewayClient

        client = GatewayClient(
            chain="arcTestnet",
            private_key="0x0000000000000000000000000000000000000000000000000000000000000001",
        )

        # Free endpoint
        free_result = await client.supports(f"{server_thread}/")
        assert free_result.supported is True
        assert free_result.requirements is None

        # Paid endpoint
        paid_result = await client.supports(f"{server_thread}/api/analyze")
        assert paid_result.supported is True
        assert paid_result.requirements is not None

        await client.close()


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Contract deployment & correctness
# ═══════════════════════════════════════════════════════════════════════════════


class TestContractDeployment:
    """Verify contracts deploy correctly with proper constructor args."""

    def test_deploy_order_and_constructor_args(self, contracts):
        """All contracts should deploy successfully with correct args."""
        assert contracts["identity"].address is not None
        assert contracts["reputation"].address is not None
        assert contracts["validation"].address is not None
        assert contracts["escrow"].address is not None

    def test_escrow_has_correct_references(self, contracts):
        """AgentEscrow should reference USDC and identity (not swapped)."""
        escrow = contracts["escrow"]
        usdc = contracts["usdc"]
        identity = contracts["identity"]

        assert escrow.usdc() == usdc.address
        assert escrow.identityRegistry() == identity.address

    def test_reputation_references_identity(self, contracts):
        """AgentReputation should reference the correct identity registry."""
        assert contracts["reputation"].identityRegistry() == contracts["identity"].address

    def test_validation_references_identity(self, contracts):
        """AgentValidation should reference the correct identity registry."""
        assert contracts["validation"].identityRegistry() == contracts["identity"].address


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Payment → Reputation flow
# ═══════════════════════════════════════════════════════════════════════════════


class TestPaymentReputationFlow:
    """Test proof-of-payment flowing from x402 payment to reputation contract."""

    def test_proof_of_payment_to_reputation(self, contracts, test_accounts):
        """Payment proof can be recorded in reputation after interaction."""
        import boa

        identity = contracts["identity"]
        reputation = contracts["reputation"]
        provider = test_accounts["provider"]
        client = test_accounts["client"]

        # Register provider as agent
        with boa.env.prank(provider):
            provider_agent_id = identity.registerAgent("ipfs://QmIntegrationProvider")

        # Record interaction (server would do this after payment)
        with boa.env.prank(provider):
            reputation.recordInteraction(provider_agent_id, client)

        assert reputation.hasClientInteracted(provider_agent_id, client) is True

        # Client submits feedback with mock proof-of-payment (tx hash from x402)
        proof_of_payment = b"\xab\xcd" + b"\x00" * 30
        with boa.env.prank(client):
            feedback_id = reputation.submitFeedback(provider_agent_id, 85, proof_of_payment)

        # Verify
        assert reputation.hasClientRated(provider_agent_id, client) is True
        assert reputation.getTotalFeedbackCount(provider_agent_id) == 1
        assert reputation.getAverageScore(provider_agent_id) == 8500  # 85 * 100

        feedback = reputation.getFeedback(feedback_id)
        assert feedback[4] == proof_of_payment

    def test_full_agent_lifecycle(self, contracts):
        """Full lifecycle: register → escrow task → pay → feedback → verify."""
        import boa

        identity = contracts["identity"]
        reputation = contracts["reputation"]
        escrow = contracts["escrow"]
        usdc = contracts["usdc"]

        # Use fresh accounts to avoid shared state with other tests
        worker = boa.env.generate_address("lifecycle_worker")
        poster = boa.env.generate_address("lifecycle_poster")

        # Register both as agents
        with boa.env.prank(worker):
            worker_agent_id = identity.registerAgent("ipfs://QmLifecycleWorker")
        with boa.env.prank(poster):
            poster_agent_id = identity.registerAgent("ipfs://QmLifecyclePoster")

        # Fund poster with USDC
        usdc.mint(poster, 100 * 10**6)

        # Create escrow task
        task_amount = 10 * 10**6  # 10 USDC
        description_hash = b"\x99\x88" + b"\x00" * 30
        deadline = 86400 * 7

        with boa.env.prank(poster):
            usdc.approve(escrow.address, task_amount)
            task_id = escrow.createTask(poster_agent_id, task_amount, description_hash, deadline)

        assert usdc.balanceOf(escrow.address) == task_amount

        # Worker claims and poster approves
        with boa.env.prank(worker):
            escrow.claimTask(task_id, worker_agent_id)

        worker_balance_before = usdc.balanceOf(worker)
        with boa.env.prank(poster):
            escrow.approveCompletion(task_id)

        assert usdc.balanceOf(worker) == worker_balance_before + task_amount

        # Record interaction and submit feedback
        with boa.env.prank(worker):
            reputation.recordInteraction(worker_agent_id, poster)

        proof_of_payment = b"\x99\x88" + b"\x00" * 30
        with boa.env.prank(poster):
            feedback_id = reputation.submitFeedback(worker_agent_id, 90, proof_of_payment)

        assert reputation.hasClientRated(worker_agent_id, poster) is True
        assert reputation.getTotalFeedbackCount(worker_agent_id) == 1
        assert reputation.getAverageScore(worker_agent_id) == 9000  # 90 * 100
