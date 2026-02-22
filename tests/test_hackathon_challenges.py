"""
Hackathon Challenge Verification Tests

These tests verify that participants have correctly completed each challenge.
All tests expect NotImplementedError until the challenge templates are filled in.

Run:
  pytest tests/test_hackathon_challenges.py -v
  pytest tests/test_hackathon_challenges.py -v -k "TrackA"
  pytest tests/test_hackathon_challenges.py -v -k "TrackC"
"""

import sys
from pathlib import Path

import pytest
import boa

try:
    import circlekit  # noqa: F401
    HAS_CIRCLEKIT = True
except ImportError:
    HAS_CIRCLEKIT = False

try:
    import fastapi  # noqa: F401
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

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

IDENTITY_REGISTRY_PATH = (
    "lib/github/lufa23/erc-8004-vyper/src/identity_registry.vy"
)


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK A2: Deploy Your First Vyper Contract
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrackA2:
    """Verify A2: Deploy vault, deposit, withdraw."""

    @pytest.fixture
    def usdc(self):
        return boa.loads(MOCK_USDC_SOURCE)

    @pytest.fixture
    def depositor(self, usdc):
        addr = boa.env.generate_address("a2_depositor")
        usdc.mint(addr, 1000 * 10**6)
        return addr

    def test_deploy_vault(self, usdc):
        """deploy_vault() should raise NotImplementedError."""
        from track_a.a2_first_contract.challenge import deploy_vault

        with pytest.raises(NotImplementedError):
            deploy_vault(usdc.address)

    def test_deposit(self, usdc, depositor):
        """deposit() should raise NotImplementedError."""
        from track_a.a2_first_contract.challenge import deposit

        vault = boa.load("contracts/Vault.vy", usdc.address)
        with pytest.raises(NotImplementedError):
            deposit(vault, usdc, depositor, 50 * 10**6)

    def test_withdraw(self, usdc, depositor):
        """withdraw() should raise NotImplementedError."""
        from track_a.a2_first_contract.challenge import withdraw

        vault = boa.load("contracts/Vault.vy", usdc.address)
        with pytest.raises(NotImplementedError):
            withdraw(vault, depositor, 50 * 10**6)


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK A3: Write a Test Suite
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrackA3:
    """Verify A3: Test stubs for the vault contract."""

    @pytest.fixture
    def usdc(self):
        return boa.loads(MOCK_USDC_SOURCE)

    @pytest.fixture
    def vault(self, usdc):
        return boa.load("contracts/Vault.vy", usdc.address)

    @pytest.fixture
    def depositor(self, usdc):
        addr = boa.env.generate_address("a3_depositor")
        usdc.mint(addr, 1000 * 10**6)
        return addr

    @pytest.fixture
    def non_depositor(self):
        return boa.env.generate_address("a3_non_depositor")

    def test_deposit_and_withdraw(self, vault, usdc, depositor):
        """test_deposit_and_withdraw() should raise NotImplementedError."""
        from track_a.a3_test_suite.challenge import test_deposit_and_withdraw

        with pytest.raises(NotImplementedError):
            test_deposit_and_withdraw(vault, usdc, depositor)

    def test_non_depositor_reverts(self, vault, usdc, depositor, non_depositor):
        """test_non_depositor_reverts() should raise NotImplementedError."""
        from track_a.a3_test_suite.challenge import test_non_depositor_reverts

        with pytest.raises(NotImplementedError):
            test_non_depositor_reverts(vault, usdc, depositor, non_depositor)

    def test_multiple_deposits(self, vault, usdc, depositor):
        """test_multiple_deposits() should raise NotImplementedError."""
        from track_a.a3_test_suite.challenge import test_multiple_deposits

        with pytest.raises(NotImplementedError):
            test_multiple_deposits(vault, usdc, depositor)


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK A4: Register as ERC-8004 Agent
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrackA4:
    """Verify A4: Deploy IdentityRegistry, register, verify."""

    @pytest.fixture
    def owner(self):
        return boa.env.generate_address("a4_owner")

    def test_deploy_registry(self):
        """deploy_registry() should raise NotImplementedError."""
        from track_a.a4_erc8004_agent.challenge import deploy_registry

        with pytest.raises(NotImplementedError):
            deploy_registry()

    def test_register_agent(self, owner):
        """register_agent() should raise NotImplementedError."""
        from track_a.a4_erc8004_agent.challenge import register_agent

        with pytest.raises(NotImplementedError):
            register_agent(None, owner, "ipfs://QmTestA4")

    def test_verify_registration(self, owner):
        """verify_registration() should raise NotImplementedError."""
        from track_a.a4_erc8004_agent.challenge import verify_registration

        with pytest.raises(NotImplementedError):
            verify_registration(None, 1, owner)


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK B3: Deploy from Circle Wallet
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not HAS_CIRCLEKIT, reason="circlekit not installed")
class TestTrackB3:
    """Verify B3: Circle Wallet signer and deployment."""

    def test_create_signer(self):
        """create_signer() should raise NotImplementedError."""
        from track_b.b3_deploy_from_wallet.challenge import create_signer

        with pytest.raises(NotImplementedError):
            create_signer("test-wallet-id", "0x1234567890123456789012345678901234567890")

    def test_create_tx_executor(self):
        """create_tx_executor() should raise NotImplementedError."""
        from track_b.b3_deploy_from_wallet.challenge import create_tx_executor

        with pytest.raises(NotImplementedError):
            create_tx_executor("test-wallet-id", "0x1234567890123456789012345678901234567890")

    def test_deploy_vault_from_circle_wallet(self):
        """deploy_vault_from_circle_wallet() should raise NotImplementedError."""
        from track_b.b3_deploy_from_wallet.challenge import deploy_vault_from_circle_wallet

        with pytest.raises(NotImplementedError):
            deploy_vault_from_circle_wallet(None, None)


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK B4: x402 Payment
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(
    not HAS_CIRCLEKIT or not HAS_FASTAPI,
    reason="circlekit or fastapi not installed",
)
class TestTrackB4:
    """Verify B4: x402 server and client payment."""

    def test_create_server_app(self):
        """create_server_app() should raise NotImplementedError."""
        from track_b.b4_x402_payment.challenge import create_server_app

        with pytest.raises(NotImplementedError):
            create_server_app("0x1234567890123456789012345678901234567890")

    @pytest.mark.asyncio
    async def test_pay_for_resource(self):
        """pay_for_resource() should raise NotImplementedError."""
        from track_b.b4_x402_payment.challenge import pay_for_resource

        with pytest.raises(NotImplementedError):
            await pay_for_resource(
                "http://localhost:8000",
                "test-wallet-id",
                "0x1234567890123456789012345678901234567890",
            )


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK C1: SpendingLimiter
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrackC1:
    """Verify C1: SpendingLimiter challenge functions."""

    @pytest.fixture
    def usdc(self):
        return boa.loads(MOCK_USDC_SOURCE)

    @pytest.fixture
    def limiter(self, usdc):
        return boa.load("contracts/SpendingLimiter.vy", usdc.address)

    @pytest.fixture
    def owner(self):
        return boa.env.generate_address("c1_owner")

    @pytest.fixture
    def agent(self):
        return boa.env.generate_address("c1_agent")

    @pytest.fixture
    def recipient(self):
        return boa.env.generate_address("c1_recipient")

    def test_authorize_spend(self, limiter, agent, recipient):
        """authorize_spend() should raise NotImplementedError."""
        from track_c.c1_spending_limiter.challenge import authorize_spend

        with pytest.raises(NotImplementedError):
            authorize_spend(limiter, agent, recipient, 10 * 10**6)

    def test_set_limit(self, limiter, owner, agent):
        """set_limit() should raise NotImplementedError."""
        from track_c.c1_spending_limiter.challenge import set_limit

        with pytest.raises(NotImplementedError):
            set_limit(limiter, owner, agent, 50 * 10**6, 86400)

    def test_emergency_pause(self, limiter, owner, agent):
        """emergency_pause() should raise NotImplementedError."""
        from track_c.c1_spending_limiter.challenge import emergency_pause

        with pytest.raises(NotImplementedError):
            emergency_pause(limiter, owner, agent)

    def test_resume(self, limiter, owner, agent):
        """resume() should raise NotImplementedError."""
        from track_c.c1_spending_limiter.challenge import resume

        with pytest.raises(NotImplementedError):
            resume(limiter, owner, agent)


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK C2: AgentEscrow
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrackC2:
    """Verify C2: AgentEscrow with hash-commitment release.

    Uses a dummy address for the IdentityRegistry constructor arg since
    challenge functions raise NotImplementedError before touching the contract.
    """

    @pytest.fixture
    def usdc(self):
        return boa.loads(MOCK_USDC_SOURCE)

    @pytest.fixture
    def escrow(self, usdc):
        dummy_registry = boa.env.generate_address("c2_dummy_registry")
        return boa.load("contracts/AgentEscrow.vy", usdc.address, dummy_registry)

    @pytest.fixture
    def payer(self, usdc):
        addr = boa.env.generate_address("c2_payer")
        usdc.mint(addr, 1000 * 10**6)
        return addr

    @pytest.fixture
    def payee(self):
        return boa.env.generate_address("c2_payee")

    @pytest.fixture
    def verifier(self):
        return boa.env.generate_address("c2_verifier")

    @pytest.fixture
    def arbiter(self):
        return boa.env.generate_address("c2_arbiter")

    def test_deposit(self, escrow, usdc, payer, payee):
        """deposit() should raise NotImplementedError."""
        from track_c.c2_agent_escrow.challenge import deposit

        spec_hash = b"\x01" + b"\x00" * 31
        with pytest.raises(NotImplementedError):
            deposit(escrow, usdc, payer, payee, 50 * 10**6, spec_hash)

    def test_submit_delivery(self, escrow, payee):
        """submit_delivery() should raise NotImplementedError."""
        from track_c.c2_agent_escrow.challenge import submit_delivery

        delivery_hash = b"\x02" + b"\x00" * 31
        with pytest.raises(NotImplementedError):
            submit_delivery(escrow, payee, 1, delivery_hash)

    def test_confirm_release(self, escrow, verifier):
        """confirm_release() should raise NotImplementedError."""
        from track_c.c2_agent_escrow.challenge import confirm_release

        with pytest.raises(NotImplementedError):
            confirm_release(escrow, verifier, 1)

    def test_challenge(self, escrow, payer):
        """challenge() should raise NotImplementedError."""
        from track_c.c2_agent_escrow.challenge import challenge

        with pytest.raises(NotImplementedError):
            challenge(escrow, payer, 1)

    def test_force_release(self, escrow):
        """force_release() should raise NotImplementedError."""
        from track_c.c2_agent_escrow.challenge import force_release

        with pytest.raises(NotImplementedError):
            force_release(escrow, 1)

    def test_arbiter_resolve(self, escrow, arbiter):
        """arbiter_resolve() should raise NotImplementedError."""
        from track_c.c2_agent_escrow.challenge import arbiter_resolve

        with pytest.raises(NotImplementedError):
            arbiter_resolve(escrow, arbiter, 1, True)


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK C3: SubscriptionManager
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrackC3:
    """Verify C3: SubscriptionManager with on-chain cancellation."""

    @pytest.fixture
    def usdc(self):
        return boa.loads(MOCK_USDC_SOURCE)

    @pytest.fixture
    def manager(self, usdc):
        return boa.load("contracts/SubscriptionManager.vy", usdc.address)

    @pytest.fixture
    def subscriber(self, usdc):
        addr = boa.env.generate_address("c3_subscriber")
        usdc.mint(addr, 1000 * 10**6)
        return addr

    @pytest.fixture
    def provider(self):
        return boa.env.generate_address("c3_provider")

    def test_subscribe(self, manager, usdc, subscriber, provider):
        """subscribe() should raise NotImplementedError."""
        from track_c.c3_subscription_manager.challenge import subscribe

        with pytest.raises(NotImplementedError):
            subscribe(manager, usdc, subscriber, provider, 10 * 10**6, 86400, 3)

    def test_settle(self, manager, subscriber, provider):
        """settle() should raise NotImplementedError."""
        from track_c.c3_subscription_manager.challenge import settle

        caller = boa.env.generate_address("c3_settler")
        with pytest.raises(NotImplementedError):
            settle(manager, caller, subscriber, provider)

    def test_cancel(self, manager, subscriber, provider):
        """cancel() should raise NotImplementedError."""
        from track_c.c3_subscription_manager.challenge import cancel

        with pytest.raises(NotImplementedError):
            cancel(manager, subscriber, provider)

    def test_withdraw(self, manager, provider):
        """withdraw() should raise NotImplementedError."""
        from track_c.c3_subscription_manager.challenge import withdraw

        with pytest.raises(NotImplementedError):
            withdraw(manager, provider)

    def test_add_metered_charge(self, manager, provider, subscriber):
        """add_metered_charge() should raise NotImplementedError."""
        from track_c.c3_subscription_manager.challenge import add_metered_charge

        with pytest.raises(NotImplementedError):
            add_metered_charge(manager, provider, subscriber, 100)


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK C4: PaymentSplitter
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrackC4:
    """Verify C4: Atomic PaymentSplitter for multi-agent workflows."""

    @pytest.fixture
    def usdc(self):
        return boa.loads(MOCK_USDC_SOURCE)

    @pytest.fixture
    def splitter(self, usdc):
        return boa.load("contracts/PaymentSplitter.vy", usdc.address)

    @pytest.fixture
    def sender(self, usdc):
        addr = boa.env.generate_address("c4_sender")
        usdc.mint(addr, 1000 * 10**6)
        return addr

    @pytest.fixture
    def owner(self):
        return boa.env.generate_address("c4_owner")

    @pytest.fixture
    def recipient(self):
        return boa.env.generate_address("c4_recipient")

    def test_distribute(self, splitter, usdc, sender):
        """distribute() should raise NotImplementedError."""
        from track_c.c4_payment_splitter.challenge import distribute

        with pytest.raises(NotImplementedError):
            distribute(splitter, usdc, sender, 100 * 10**6)

    def test_accrue(self, splitter, usdc, sender):
        """accrue() should raise NotImplementedError."""
        from track_c.c4_payment_splitter.challenge import accrue

        with pytest.raises(NotImplementedError):
            accrue(splitter, usdc, sender, 100 * 10**6)

    def test_claim(self, splitter, recipient):
        """claim() should raise NotImplementedError."""
        from track_c.c4_payment_splitter.challenge import claim

        with pytest.raises(NotImplementedError):
            claim(splitter, recipient)

    def test_propose_split_update(self, splitter, owner):
        """propose_split_update() should raise NotImplementedError."""
        from track_c.c4_payment_splitter.challenge import propose_split_update

        recipients = [boa.env.generate_address("c4_r1"), boa.env.generate_address("c4_r2")]
        shares = [6000, 4000]
        with pytest.raises(NotImplementedError):
            propose_split_update(splitter, owner, recipients, shares)


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK C5: Payment Channel
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrackC5:
    """Verify C5: Payment channel with challenge period.

    NOTE: contracts/PaymentChannel.vy does not exist yet.
    These tests verify the challenge functions raise NotImplementedError.
    No contract fixtures are created.
    """

    def test_open_channel(self):
        """open_channel() should raise NotImplementedError."""
        from track_c.c5_payment_channel.challenge import open_channel

        with pytest.raises(NotImplementedError):
            open_channel(None, None, "payer", "payee", 100 * 10**6, 1000)

    def test_cooperative_close(self):
        """cooperative_close() should raise NotImplementedError."""
        from track_c.c5_payment_channel.challenge import cooperative_close

        with pytest.raises(NotImplementedError):
            cooperative_close(None, 1, 50 * 10**6, b"\x00" * 65, b"\x00" * 65)

    def test_unilateral_close(self):
        """unilateral_close() should raise NotImplementedError."""
        from track_c.c5_payment_channel.challenge import unilateral_close

        with pytest.raises(NotImplementedError):
            unilateral_close(None, "closer", 1, 50 * 10**6, b"\x00" * 65)

    def test_challenge(self):
        """challenge() should raise NotImplementedError."""
        from track_c.c5_payment_channel.challenge import challenge

        with pytest.raises(NotImplementedError):
            challenge(None, "challenger", 1, 60 * 10**6, b"\x00" * 65)

    def test_finalize(self):
        """finalize() should raise NotImplementedError."""
        from track_c.c5_payment_channel.challenge import finalize

        with pytest.raises(NotImplementedError):
            finalize(None, 1)

    def test_reclaim(self):
        """reclaim() should raise NotImplementedError."""
        from track_c.c5_payment_channel.challenge import reclaim

        with pytest.raises(NotImplementedError):
            reclaim(None, "payer", 1)
