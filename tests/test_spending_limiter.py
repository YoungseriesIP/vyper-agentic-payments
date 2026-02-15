"""
Tests for SpendingLimiter.vy - Agent Authorization & Delegation

This test suite covers:
- Fund deposits and withdrawals
- Agent authorization and revocation
- Spending limit enforcement
- Daily/total limit tracking
"""

import pytest
import boa


@pytest.fixture
def spending_limiter(funded_usdc, deployer):
    """Deploy the SpendingLimiter contract."""
    with boa.env.prank(deployer):
        return boa.load("contracts/SpendingLimiter.vy", funded_usdc.address)


@pytest.fixture
def agent():
    """A designated agent address."""
    return boa.env.generate_address("agent")


class TestSpendingLimiterDeployment:
    """Tests for contract deployment."""

    def test_initial_state(self, spending_limiter, funded_usdc):
        """Contract should initialize correctly."""
        assert spending_limiter.usdc() == funded_usdc.address

    def test_deploy_with_zero_address_fails(self):
        """Should fail with zero USDC address."""
        with pytest.raises(boa.BoaError, match="zero address"):
            boa.load("contracts/SpendingLimiter.vy", "0x0000000000000000000000000000000000000000")


class TestFundManagement:
    """Tests for deposit and withdrawal."""

    def test_deposit(self, spending_limiter, funded_usdc, alice):
        """Owner should be able to deposit USDC."""
        amount = 100 * 10**6
        
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, amount)
            spending_limiter.deposit(amount)
        
        assert spending_limiter.ownerBalance(alice) == amount
        assert funded_usdc.balanceOf(spending_limiter.address) == amount

    def test_withdraw(self, spending_limiter, funded_usdc, alice):
        """Owner should be able to withdraw USDC."""
        amount = 100 * 10**6
        
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, amount)
            spending_limiter.deposit(amount)
        
        balance_before = funded_usdc.balanceOf(alice)
        
        with boa.env.prank(alice):
            spending_limiter.withdraw(50 * 10**6)
        
        assert spending_limiter.ownerBalance(alice) == 50 * 10**6
        assert funded_usdc.balanceOf(alice) == balance_before + 50 * 10**6

    def test_withdraw_insufficient_balance_fails(self, spending_limiter, funded_usdc, alice):
        """Should fail if insufficient balance."""
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, 10 * 10**6)
            spending_limiter.deposit(10 * 10**6)
        
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="insufficient balance"):
                spending_limiter.withdraw(20 * 10**6)

    def test_deposit_zero_fails(self, spending_limiter, alice):
        """Should fail with zero amount."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="zero amount"):
                spending_limiter.deposit(0)


class TestAgentAuthorization:
    """Tests for agent authorization."""

    def test_authorize_agent(self, spending_limiter, alice, agent):
        """Owner should be able to authorize an agent."""
        with boa.env.prank(alice):
            spending_limiter.authorizeAgent(
                agent,
                10 * 10**6,   # 10 USDC per tx
                100 * 10**6,  # 100 USDC daily
                1000 * 10**6  # 1000 USDC total
            )
        
        assert spending_limiter.isAuthorized(alice, agent) is True
        assert spending_limiter.perTxLimit(alice, agent) == 10 * 10**6
        assert spending_limiter.dailyLimit(alice, agent) == 100 * 10**6
        assert spending_limiter.totalLimit(alice, agent) == 1000 * 10**6

    def test_authorize_self_fails(self, spending_limiter, alice):
        """Should not be able to authorize self."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="cannot authorize self"):
                spending_limiter.authorizeAgent(alice, 10**6, 10**6, 10**6)

    def test_revoke_agent(self, spending_limiter, alice, agent):
        """Owner should be able to revoke agent."""
        with boa.env.prank(alice):
            spending_limiter.authorizeAgent(agent, 10**6, 10**6, 10**6)
            spending_limiter.revokeAgent(agent)
        
        assert spending_limiter.isAuthorized(alice, agent) is False

    def test_update_limits(self, spending_limiter, alice, agent):
        """Owner should be able to update limits."""
        with boa.env.prank(alice):
            spending_limiter.authorizeAgent(agent, 10**6, 10**6, 10**6)
            spending_limiter.updateLimits(agent, 20**6, 200**6, 2000**6)
        
        assert spending_limiter.perTxLimit(alice, agent) == 20**6


class TestSpending:
    """Tests for agent spending."""

    def test_spend_within_limits(self, spending_limiter, funded_usdc, alice, agent, charlie):
        """Agent should be able to spend within limits."""
        # Setup
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, 100 * 10**6)
            spending_limiter.deposit(100 * 10**6)
            spending_limiter.authorizeAgent(agent, 50 * 10**6, 100 * 10**6, 1000 * 10**6)
        
        charlie_balance_before = funded_usdc.balanceOf(charlie)
        
        # Agent spends
        with boa.env.prank(agent):
            spending_limiter.spend(alice, 25 * 10**6, charlie)
        
        assert funded_usdc.balanceOf(charlie) == charlie_balance_before + 25 * 10**6
        assert spending_limiter.ownerBalance(alice) == 75 * 10**6
        assert spending_limiter.totalSpent(alice, agent) == 25 * 10**6

    def test_spend_exceeds_per_tx_limit_fails(self, spending_limiter, funded_usdc, alice, agent, charlie):
        """Should fail if exceeds per-tx limit."""
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, 100 * 10**6)
            spending_limiter.deposit(100 * 10**6)
            spending_limiter.authorizeAgent(agent, 10 * 10**6, 100 * 10**6, 1000 * 10**6)
        
        with boa.env.prank(agent):
            with pytest.raises(boa.BoaError, match="exceeds per-tx limit"):
                spending_limiter.spend(alice, 20 * 10**6, charlie)

    def test_spend_exceeds_daily_limit_fails(self, spending_limiter, funded_usdc, alice, agent, charlie):
        """Should fail if exceeds daily limit."""
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, 100 * 10**6)
            spending_limiter.deposit(100 * 10**6)
            spending_limiter.authorizeAgent(agent, 50 * 10**6, 30 * 10**6, 1000 * 10**6)
        
        with boa.env.prank(agent):
            spending_limiter.spend(alice, 20 * 10**6, charlie)
        
        with boa.env.prank(agent):
            with pytest.raises(boa.BoaError, match="exceeds daily limit"):
                spending_limiter.spend(alice, 20 * 10**6, charlie)  # Would exceed 30 daily

    def test_spend_exceeds_total_limit_fails(self, spending_limiter, funded_usdc, alice, agent, charlie):
        """Should fail if exceeds total limit."""
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, 100 * 10**6)
            spending_limiter.deposit(100 * 10**6)
            spending_limiter.authorizeAgent(agent, 50 * 10**6, 100 * 10**6, 30 * 10**6)  # 30 total
        
        with boa.env.prank(agent):
            spending_limiter.spend(alice, 20 * 10**6, charlie)
        
        with boa.env.prank(agent):
            with pytest.raises(boa.BoaError, match="exceeds total limit"):
                spending_limiter.spend(alice, 20 * 10**6, charlie)  # Would exceed 30 total

    def test_spend_unauthorized_fails(self, spending_limiter, funded_usdc, alice, agent, charlie):
        """Unauthorized agent cannot spend."""
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, 100 * 10**6)
            spending_limiter.deposit(100 * 10**6)
        
        with boa.env.prank(agent):
            with pytest.raises(boa.BoaError, match="not authorized"):
                spending_limiter.spend(alice, 10 * 10**6, charlie)

    def test_daily_limit_resets(self, spending_limiter, funded_usdc, alice, agent, charlie):
        """Daily limit should reset after 24 hours."""
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, 100 * 10**6)
            spending_limiter.deposit(100 * 10**6)
            spending_limiter.authorizeAgent(agent, 50 * 10**6, 30 * 10**6, 1000 * 10**6)
        
        # Spend up to daily limit
        with boa.env.prank(agent):
            spending_limiter.spend(alice, 30 * 10**6, charlie)
        
        # Should fail now
        with boa.env.prank(agent):
            with pytest.raises(boa.BoaError, match="exceeds daily limit"):
                spending_limiter.spend(alice, 1 * 10**6, charlie)
        
        # Fast forward 1 day
        boa.env.time_travel(seconds=86401)
        
        # Should work again
        with boa.env.prank(agent):
            spending_limiter.spend(alice, 30 * 10**6, charlie)


class TestViewFunctions:
    """Tests for view functions."""

    def test_can_spend(self, spending_limiter, funded_usdc, alice, agent):
        """canSpend should return correct result."""
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, 100 * 10**6)
            spending_limiter.deposit(100 * 10**6)
            spending_limiter.authorizeAgent(agent, 50 * 10**6, 100 * 10**6, 1000 * 10**6)
        
        assert spending_limiter.canSpend(alice, agent, 40 * 10**6) is True
        assert spending_limiter.canSpend(alice, agent, 60 * 10**6) is False  # Exceeds per-tx

    def test_get_remaining_limits(self, spending_limiter, funded_usdc, alice, agent, charlie):
        """getRemainingLimits should return correct values."""
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, 100 * 10**6)
            spending_limiter.deposit(100 * 10**6)
            spending_limiter.authorizeAgent(agent, 50 * 10**6, 80 * 10**6, 200 * 10**6)
        
        with boa.env.prank(agent):
            spending_limiter.spend(alice, 30 * 10**6, charlie)
        
        result = spending_limiter.getRemainingLimits(alice, agent)
        
        assert result[0] == 50 * 10**6   # remaining daily (80 - 30)
        assert result[1] == 170 * 10**6  # remaining total (200 - 30)
        assert result[2] == 70 * 10**6   # owner balance (100 - 30)

    def test_get_agent_limits(self, spending_limiter, alice, agent):
        """getAgentLimits should return configured limits."""
        with boa.env.prank(alice):
            spending_limiter.authorizeAgent(agent, 10 * 10**6, 100 * 10**6, 1000 * 10**6)
        
        result = spending_limiter.getAgentLimits(alice, agent)
        
        assert result[0] == 10 * 10**6    # perTxLimit
        assert result[1] == 100 * 10**6   # dailyLimit
        assert result[2] == 1000 * 10**6  # totalLimit
        assert result[3] is True          # isAuthorized


class TestNoLimits:
    """Tests for zero limit (no limit) behavior."""

    def test_no_per_tx_limit(self, spending_limiter, funded_usdc, alice, agent, charlie):
        """Zero per-tx limit means no limit."""
        charlie_balance_before = funded_usdc.balanceOf(charlie)
        
        with boa.env.prank(alice):
            funded_usdc.approve(spending_limiter.address, 100 * 10**6)
            spending_limiter.deposit(100 * 10**6)
            spending_limiter.authorizeAgent(agent, 0, 0, 0)  # No limits
        
        # Should be able to spend any amount up to balance
        with boa.env.prank(agent):
            spending_limiter.spend(alice, 100 * 10**6, charlie)
        
        assert funded_usdc.balanceOf(charlie) == charlie_balance_before + 100 * 10**6
