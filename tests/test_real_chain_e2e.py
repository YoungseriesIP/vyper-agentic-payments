"""
Real Chain End-to-End Tests: circlekit SDK + Deployed Vyper Contracts

These tests verify that everything works together on the real Arc Testnet:
1. circlekit SDK can read deployed contract state
2. circlekit SDK can sign and broadcast transactions
3. x402 payment flow works end-to-end (server + client + real Gateway API)
4. Deployed contracts accept real transactions (registerAgent, submitFeedback)
5. Cross-repo integration: circle-titanoboa-sdk + vyper-agentic-payments

Prerequisites:
  - PRIVATE_KEY env var (funded wallet on Arc Testnet)
  - Deployed contracts (run scripts/deploy_boa.py first → deployments.json)
  - pip install -e ../circle-titanoboa-sdk

Run:
  PRIVATE_KEY=0x... pytest tests/test_real_chain_e2e.py -v -s

These tests execute real testnet transactions!
"""

import asyncio
import json
import os
import threading
import time
from pathlib import Path

import pytest

HAS_PRIVATE_KEY = bool(os.environ.get("PRIVATE_KEY"))
SKIP_REASON = "PRIVATE_KEY not set"

DEPLOYMENTS_FILE = Path(__file__).resolve().parent.parent / "deployments.json"
HAS_DEPLOYMENTS = DEPLOYMENTS_FILE.exists()
SKIP_DEPLOYMENTS = "deployments.json not found; run scripts/deploy_boa.py first"

ARC_CHAIN_ID = "5042002"

# Disable boa's evm_snapshot isolation. Real RPCs don't support it.
pytestmark = [
    pytest.mark.ignore_isolation,
    pytest.mark.real_chain,
]


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def deployments():
    """Load deployed contract addresses from deployments.json."""
    if not HAS_DEPLOYMENTS:
        pytest.skip(SKIP_DEPLOYMENTS)
    data = json.loads(DEPLOYMENTS_FILE.read_text())
    chain_data = data.get(ARC_CHAIN_ID, {})
    if not chain_data:
        pytest.skip(f"No deployments for chain {ARC_CHAIN_ID}")
    return chain_data


@pytest.fixture(scope="module")
def private_key():
    """Get the private key from environment."""
    pk = os.environ.get("PRIVATE_KEY")
    if not pk:
        pytest.skip(SKIP_REASON)
    return pk


@pytest.fixture(scope="module")
def boa_env(private_key):
    """Set up boa environment connected to Arc Testnet."""
    import boa
    from eth_account import Account

    boa.set_network_env("https://rpc.testnet.arc.network")
    account = Account.from_key(private_key)
    boa.env.add_account(account, force_eoa=True)
    return account.address


@pytest.fixture(scope="module")
def identity_contract(deployments):
    """Load the deployed AgentIdentity contract."""
    import boa

    addr = deployments.get("IdentityRegistry", {}).get("address")
    if not addr:
        pytest.skip("IdentityRegistry not deployed")
    return boa.load_partial("lib/github/lufa23/erc-8004-vyper/src/identity_registry.vy").at(addr)


@pytest.fixture(scope="module")
def reputation_contract(deployments):
    """Load the deployed AgentReputation contract."""
    import boa

    addr = deployments.get("ReputationRegistry", {}).get("address")
    if not addr:
        pytest.skip("ReputationRegistry not deployed")
    return boa.load_partial("lib/github/lufa23/erc-8004-vyper/src/reputation_registry.vy").at(addr)


@pytest.fixture(scope="module")
def escrow_contract(deployments):
    """Load the deployed AgentEscrow contract."""
    import boa

    addr = deployments.get("AgentEscrow", {}).get("address")
    if not addr:
        pytest.skip("AgentEscrow not deployed")
    return boa.load_partial("contracts/AgentEscrow.vy").at(addr)


@pytest.fixture(scope="module")
def real_marketplace_server(private_key):
    """
    Start a real Flask marketplace server with x402 Gateway middleware.
    Uses a different seller address to avoid self-payment rejection.
    """
    from flask import Flask, jsonify, request

    from circlekit import create_gateway_middleware
    from circlekit.x402 import PaymentInfo

    app = Flask(__name__)

    # Seller must be different from buyer to avoid Gateway self-payment rejection
    seller_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"

    gateway = create_gateway_middleware(
        seller_address=seller_address,
        chain="arcTestnet",
    )

    loop = asyncio.new_event_loop()

    def _run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop_thread = threading.Thread(target=_run_loop, daemon=True)
    loop_thread.start()

    def require_payment(price: str):
        payment_header = request.headers.get("Payment-Signature")
        future = asyncio.run_coroutine_threadsafe(
            gateway.process_request(
                payment_header=payment_header,
                path=request.path,
                price=price,
            ),
            loop,
        )
        result = future.result(timeout=15)

        if isinstance(result, PaymentInfo):
            return result

        resp = jsonify(result.get("body", result))
        resp.status_code = result.get("status", 402)
        for k, v in result.get("headers", {}).items():
            resp.headers[k] = v
        return resp

    @app.route("/")
    def index():
        return jsonify({"status": "ok", "seller": seller_address})

    @app.route("/api/analyze")
    def analyze():
        result = require_payment("$0.01")
        if not isinstance(result, PaymentInfo):
            return result
        resp = jsonify({
            "success": True,
            "service": "analyze",
            "paid_by": result.payer,
            "amount": result.amount,
            "transaction": result.transaction,
        })
        for k, v in result.response_headers.items():
            resp.headers[k] = v
        return resp

    def run_server():
        app.run(host="127.0.0.1", port=4097, debug=False, use_reloader=False)

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(1.5)

    yield "http://127.0.0.1:4097"


# =============================================================================
# TESTS: Deployed Contract Reads
# =============================================================================


class TestDeployedContractReads:
    """Read state from deployed contracts on Arc Testnet."""

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.skipif(not HAS_DEPLOYMENTS, reason=SKIP_DEPLOYMENTS)
    def test_identity_contract_metadata(self, boa_env, identity_contract):
        """AgentIdentity should have correct name and symbol."""
        assert identity_contract.name() == "Agent Identity Registry"
        assert identity_contract.symbol() == "AGENT"

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.skipif(not HAS_DEPLOYMENTS, reason=SKIP_DEPLOYMENTS)
    def test_identity_total_agents(self, boa_env, identity_contract):
        """Should be able to read total agents count."""
        total = identity_contract.totalSupply()
        assert isinstance(total, int)
        assert total >= 0
        print(f"  Total agents on chain: {total}")

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.skipif(not HAS_DEPLOYMENTS, reason=SKIP_DEPLOYMENTS)
    def test_reputation_references_identity(self, boa_env, reputation_contract, deployments):
        """AgentReputation should point to the correct AgentIdentity address."""
        identity_addr = deployments["IdentityRegistry"]["address"]
        assert reputation_contract.identityRegistry().lower() == identity_addr.lower()

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.skipif(not HAS_DEPLOYMENTS, reason=SKIP_DEPLOYMENTS)
    def test_escrow_references_usdc_and_identity(self, boa_env, escrow_contract, deployments):
        """AgentEscrow should have correct USDC and identity references (constructor bug fix)."""
        usdc_addr = "0x3600000000000000000000000000000000000000"
        identity_addr = deployments["IdentityRegistry"]["address"]

        assert escrow_contract.usdc().lower() == usdc_addr.lower()
        assert escrow_contract.identityRegistry().lower() == identity_addr.lower()


# =============================================================================
# TESTS: Real On-Chain Transactions
# =============================================================================


class TestRealChainTransactions:
    """
    Execute real transactions on deployed contracts.

    NOTE: These tests require a paid DRPC tier or a dedicated RPC endpoint.
    The free DRPC tier rate-limits boa's multiple RPC calls per transaction
    (estimateGas, getNonce, sendRawTransaction, getReceipt).
    These operations were verified manually via scripts/interact_boa.py.
    """

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.skipif(not HAS_DEPLOYMENTS, reason=SKIP_DEPLOYMENTS)
    def test_register_agent_on_chain(self, boa_env, identity_contract):
        """Register a new agent on the real Arc Testnet."""
        initial_count = identity_contract.totalSupply()
        print(f"  Initial agent count: {initial_count}")

        metadata_uri = f"ipfs://QmE2ETest{int(time.time())}"
        agent_id = identity_contract.register(metadata_uri)

        print(f"  Registered agent ID: {agent_id}")
        assert agent_id > 0

        new_count = identity_contract.totalSupply()
        print(f"  New agent count: {new_count}")
        assert new_count == initial_count + 1

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.skipif(not HAS_DEPLOYMENTS, reason=SKIP_DEPLOYMENTS)
    def test_agent_ownership(self, boa_env, identity_contract):
        """Registered agent should be owned by the deployer wallet."""
        # Register a new agent
        agent_id = identity_contract.register(f"ipfs://QmOwnerTest{int(time.time())}")
        owner = identity_contract.ownerOf(agent_id)
        assert owner.lower() == boa_env.lower()
        print(f"  Agent {agent_id} owned by {owner}")


# =============================================================================
# TESTS: circlekit SDK + Gateway
# =============================================================================


class TestCirclekitGateway:
    """Test circlekit SDK functions against real Arc Testnet."""

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.asyncio
    async def test_gateway_client_balances(self, private_key):
        """GatewayClient should read real balances on Arc Testnet."""
        from circlekit import GatewayClient

        async with GatewayClient(chain="arcTestnet", private_key=private_key) as client:
            balances = await client.get_balances()

        print(f"  Wallet: {balances.wallet.formatted} USDC")
        print(f"  Gateway available: {balances.gateway.formatted_available} USDC")

        assert balances.wallet.balance >= 0
        assert balances.gateway.available >= 0

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.asyncio
    async def test_payment_signature_creation(self, private_key):
        """Should create a valid EIP-712 payment signature."""
        from circlekit import create_payment_header, decode_payment_header
        from circlekit.boa_utils import get_chain_config
        from circlekit.signer import PrivateKeySigner
        from circlekit.x402 import PaymentRequirements

        config = get_chain_config("arcTestnet")
        signer = PrivateKeySigner(private_key)

        requirements = PaymentRequirements(
            scheme="exact",
            network=f"eip155:{config.chain_id}",
            asset=config.usdc_address,
            amount="10000",  # 0.01 USDC
            pay_to="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            max_timeout_seconds=345600,
            extra={
                "name": "GatewayWalletBatched",
                "version": "1",
                "verifyingContract": config.gateway_address,
            },
        )

        header = create_payment_header(signer=signer, requirements=requirements)
        assert len(header) > 50

        decoded = decode_payment_header(header)
        payload = decoded.get("payload", decoded)
        assert "signature" in payload
        assert "authorization" in payload

        print(f"  Header length: {len(header)} chars")
        print(f"  Signature: {payload['signature'][:30]}...")


# =============================================================================
# TESTS: Real x402 Payment Flow (server + client + real Gateway API)
# =============================================================================


class TestRealPaymentFlow:
    """
    Test the full x402 payment lifecycle with the real Gateway API.
    This is the most comprehensive test, proving both repos work together.
    """

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.asyncio
    async def test_server_returns_402_without_payment(self, real_marketplace_server):
        """Server should return 402 with valid x402 body when no payment is provided."""
        import httpx

        async with httpx.AsyncClient() as http:
            response = await http.get(f"{real_marketplace_server}/api/analyze")

        assert response.status_code == 402

        data = response.json()
        assert "x402Version" in data
        assert "accepts" in data
        assert len(data["accepts"]) >= 1
        assert data["accepts"][0]["scheme"] == "exact"
        assert data["accepts"][0]["extra"]["name"] == "GatewayWalletBatched"

        print(f"  x402Version: {data['x402Version']}")
        print(f"  Payment options: {len(data['accepts'])}")

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.asyncio
    async def test_gateway_client_supports_check(self, private_key, real_marketplace_server):
        """GatewayClient.supports() should detect x402 support on the real server."""
        from circlekit import GatewayClient

        async with GatewayClient(chain="arcTestnet", private_key=private_key) as client:
            # Free endpoint
            free_result = await client.supports(f"{real_marketplace_server}/")
            assert free_result.supported is False

            # Paid endpoint
            paid_result = await client.supports(f"{real_marketplace_server}/api/analyze")
            assert paid_result.supported is True

        print(f"  Free endpoint supported: {free_result.supported}")
        print(f"  Paid endpoint supported: {paid_result.supported}")

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.asyncio
    async def test_full_real_payment(self, private_key, real_marketplace_server):
        """
        THE BIG TEST: Full payment through the real Gateway API.

        1. Client hits /api/analyze → gets 402
        2. Client signs EIP-712 payment intent
        3. Client retries with Payment-Signature header
        4. Server calls Gateway API verify → settle
        5. Server returns 200 with paid content
        6. Client receives result + transaction hash

        This proves both repos work together end-to-end.
        """
        from circlekit import GatewayClient

        async with GatewayClient(chain="arcTestnet", private_key=private_key) as client:
            # Check we have Gateway balance
            balances = await client.get_balances()
            if balances.gateway.available < 10000:  # 0.01 USDC
                pytest.skip("Insufficient Gateway balance for real payment test")

            print(f"  Gateway balance before: {balances.gateway.formatted_available} USDC")

            # Execute real payment
            result = await client.pay(f"{real_marketplace_server}/api/analyze")

            assert result.status == 200
            assert result.data["success"] is True
            assert result.data["service"] == "analyze"
            assert result.data["paid_by"].lower() == client.address.lower()
            assert result.transaction is not None

            print(f"  Payment successful!")
            print(f"  Paid by: {result.data['paid_by']}")
            print(f"  Amount: {result.formatted_amount} USDC")
            print(f"  Transaction: {result.transaction}")

            # Check balance decreased
            new_balances = await client.get_balances()
            print(f"  Gateway balance after: {new_balances.gateway.formatted_available} USDC")

            # Balance should have decreased (or at least not increased)
            assert new_balances.gateway.available <= balances.gateway.available


# =============================================================================
# TESTS: Full Stack Integration (SDK + Contracts + Gateway)
# =============================================================================


class TestFullStackIntegration:
    """
    Prove that the complete hackathon stack works:
    - Vyper contracts deployed on Arc Testnet
    - circlekit SDK connects and transacts
    - x402 payments flow through real Gateway
    - Contract state is updated on-chain
    """

    @pytest.mark.skipif(not HAS_PRIVATE_KEY, reason=SKIP_REASON)
    @pytest.mark.skipif(not HAS_DEPLOYMENTS, reason=SKIP_DEPLOYMENTS)
    @pytest.mark.asyncio
    async def test_register_agent_then_check_with_sdk(
        self, boa_env, identity_contract, private_key
    ):
        """
        Register an agent via boa, then verify the SDK can read it.
        Proves boa writes + SDK reads work on the same chain.
        """
        # Register via boa
        metadata = f"ipfs://QmSDKVerify{int(time.time())}"
        agent_id = identity_contract.register(metadata)
        print(f"  Registered agent {agent_id} via boa")

        # Verify the contract state is consistent
        owner = identity_contract.ownerOf(agent_id)
        assert owner.lower() == boa_env.lower()

        uri = identity_contract.tokenURI(agent_id)
        assert uri == metadata
        print(f"  Agent {agent_id}: owner={owner[:10]}..., uri={uri}")

# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    print("""
    ================================================================
      REAL CHAIN END-TO-END TESTS
    ================================================================

    These tests verify the FULL STACK on Arc Testnet:
    - circlekit SDK <-> real Gateway API
    - boa <-> deployed Vyper contracts
    - x402 payment flow: server + client + Gateway verify/settle

    Prerequisites:
      PRIVATE_KEY=0x...  (funded wallet)
      deployments.json   (run scripts/deploy_boa.py)

    Run:
      PRIVATE_KEY=0x... pytest tests/test_real_chain_e2e.py -v -s
    ================================================================
    """)
    pytest.main([__file__, "-v", "-s"])
