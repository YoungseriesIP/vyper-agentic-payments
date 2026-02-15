"""
Tests for PaymentSplitter.vy - Revenue Distribution for Multi-Agent Collaboration

This test suite covers:
- Pool creation with share allocations
- USDC deposits and distribution
- Claiming payments
- Pool management (add/remove/update recipients)
"""

import pytest
import boa


@pytest.fixture
def payment_splitter(funded_usdc, deployer):
    """Deploy the PaymentSplitter contract."""
    with boa.env.prank(deployer):
        return boa.load("contracts/PaymentSplitter.vy", funded_usdc.address)


class TestPaymentSplitterDeployment:
    """Tests for contract deployment."""

    def test_initial_state(self, payment_splitter, funded_usdc):
        """Contract should initialize correctly."""
        assert payment_splitter.usdc() == funded_usdc.address
        assert payment_splitter.nextPoolId() == 1

    def test_deploy_with_zero_address_fails(self):
        """Should fail with zero USDC address."""
        with pytest.raises(boa.BoaError, match="zero address"):
            boa.load("contracts/PaymentSplitter.vy", "0x0000000000000000000000000000000000000000")


class TestPoolCreation:
    """Tests for creating payment pools."""

    def test_create_pool_single_recipient(self, payment_splitter, alice, bob):
        """Should create pool with single recipient (100%)."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob], [10000])
        
        assert pool_id == 1
        assert payment_splitter.poolOwner(pool_id) == alice
        assert payment_splitter.totalShares(pool_id) == 10000
        assert payment_splitter.shares(pool_id, bob) == 10000
        assert payment_splitter.isRecipient(pool_id, bob) is True

    def test_create_pool_multiple_recipients(self, payment_splitter, alice, bob, charlie):
        """Should create pool with multiple recipients."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool(
                [bob, charlie],
                [7000, 3000]  # 70% and 30%
            )
        
        assert pool_id == 1
        assert payment_splitter.shares(pool_id, bob) == 7000
        assert payment_splitter.shares(pool_id, charlie) == 3000

    def test_create_pool_increments_id(self, payment_splitter, alice, bob):
        """Pool IDs should increment."""
        with boa.env.prank(alice):
            pool1 = payment_splitter.createPool([bob], [10000])
            pool2 = payment_splitter.createPool([bob], [10000])
        
        assert pool1 == 1
        assert pool2 == 2
        assert payment_splitter.nextPoolId() == 3

    def test_create_pool_no_recipients_fails(self, payment_splitter, alice):
        """Should fail with no recipients."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="no recipients"):
                payment_splitter.createPool([], [])

    def test_create_pool_length_mismatch_fails(self, payment_splitter, alice, bob, charlie):
        """Should fail with mismatched lengths."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="length mismatch"):
                payment_splitter.createPool([bob, charlie], [5000])

    def test_create_pool_shares_not_10000_fails(self, payment_splitter, alice, bob, charlie):
        """Should fail if shares don't sum to 10000."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="shares must equal 10000"):
                payment_splitter.createPool([bob, charlie], [5000, 4000])

    def test_create_pool_duplicate_recipient_fails(self, payment_splitter, alice, bob):
        """Should fail with duplicate recipients."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="duplicate recipient"):
                payment_splitter.createPool([bob, bob], [5000, 5000])

    def test_create_pool_zero_shares_fails(self, payment_splitter, alice, bob, charlie):
        """Should fail with zero shares."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="zero shares"):
                payment_splitter.createPool([bob, charlie], [10000, 0])


class TestPayments:
    """Tests for deposits and claims."""

    def test_deposit(self, payment_splitter, funded_usdc, alice, bob):
        """Should accept deposits."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob], [10000])
            funded_usdc.approve(payment_splitter.address, 100 * 10**6)
            payment_splitter.deposit(pool_id, 100 * 10**6)
        
        assert payment_splitter.totalReceived(pool_id) == 100 * 10**6

    def test_deposit_to_nonexistent_pool_fails(self, payment_splitter, funded_usdc, alice):
        """Should fail depositing to non-existent pool."""
        with boa.env.prank(alice):
            funded_usdc.approve(payment_splitter.address, 100 * 10**6)
            with pytest.raises(boa.BoaError, match="pool not found"):
                payment_splitter.deposit(999, 100 * 10**6)

    def test_claim_single_recipient(self, payment_splitter, funded_usdc, alice, bob):
        """Single recipient should claim 100%."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob], [10000])
            funded_usdc.approve(payment_splitter.address, 100 * 10**6)
            payment_splitter.deposit(pool_id, 100 * 10**6)
        
        bob_balance_before = funded_usdc.balanceOf(bob)
        
        with boa.env.prank(bob):
            payment_splitter.claim(pool_id)
        
        assert funded_usdc.balanceOf(bob) == bob_balance_before + 100 * 10**6
        assert payment_splitter.claimed(pool_id, bob) == 100 * 10**6

    def test_claim_multiple_recipients(self, payment_splitter, funded_usdc, alice, bob, charlie):
        """Multiple recipients should claim proportionally."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob, charlie], [7000, 3000])
            funded_usdc.approve(payment_splitter.address, 100 * 10**6)
            payment_splitter.deposit(pool_id, 100 * 10**6)
        
        bob_balance_before = funded_usdc.balanceOf(bob)
        charlie_balance_before = funded_usdc.balanceOf(charlie)
        
        with boa.env.prank(bob):
            payment_splitter.claim(pool_id)
        
        with boa.env.prank(charlie):
            payment_splitter.claim(pool_id)
        
        assert funded_usdc.balanceOf(bob) == bob_balance_before + 70 * 10**6
        assert funded_usdc.balanceOf(charlie) == charlie_balance_before + 30 * 10**6

    def test_claim_nothing_fails(self, payment_splitter, alice, bob):
        """Should fail if nothing to claim."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob], [10000])
        
        with boa.env.prank(bob):
            with pytest.raises(boa.BoaError, match="nothing to claim"):
                payment_splitter.claim(pool_id)

    def test_claim_non_recipient_fails(self, payment_splitter, funded_usdc, alice, bob, charlie):
        """Non-recipient should not be able to claim."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob], [10000])
            funded_usdc.approve(payment_splitter.address, 100 * 10**6)
            payment_splitter.deposit(pool_id, 100 * 10**6)
        
        with boa.env.prank(charlie):
            with pytest.raises(boa.BoaError, match="not a recipient"):
                payment_splitter.claim(pool_id)

    def test_claim_for(self, payment_splitter, funded_usdc, alice, bob, charlie):
        """Anyone should be able to claim for a recipient."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob], [10000])
            funded_usdc.approve(payment_splitter.address, 100 * 10**6)
            payment_splitter.deposit(pool_id, 100 * 10**6)
        
        bob_balance_before = funded_usdc.balanceOf(bob)
        
        # Charlie claims for Bob
        with boa.env.prank(charlie):
            payment_splitter.claimFor(pool_id, bob)
        
        assert funded_usdc.balanceOf(bob) == bob_balance_before + 100 * 10**6

    def test_multiple_deposits_and_claims(self, payment_splitter, funded_usdc, alice, bob):
        """Should handle multiple deposits and partial claims."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob], [10000])
            
            funded_usdc.approve(payment_splitter.address, 200 * 10**6)
            payment_splitter.deposit(pool_id, 50 * 10**6)
        
        bob_balance_before = funded_usdc.balanceOf(bob)
        
        # Claim first deposit
        with boa.env.prank(bob):
            payment_splitter.claim(pool_id)
        
        assert funded_usdc.balanceOf(bob) == bob_balance_before + 50 * 10**6
        
        # Second deposit
        with boa.env.prank(alice):
            payment_splitter.deposit(pool_id, 100 * 10**6)
        
        # Claim second deposit
        with boa.env.prank(bob):
            payment_splitter.claim(pool_id)
        
        assert funded_usdc.balanceOf(bob) == bob_balance_before + 150 * 10**6


class TestPoolManagement:
    """Tests for pool management functions."""

    def test_update_shares(self, payment_splitter, alice, bob, charlie):
        """Pool owner should be able to update shares."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob, charlie], [7000, 3000])
            payment_splitter.updateShares(pool_id, bob, 6000)
        
        assert payment_splitter.shares(pool_id, bob) == 6000
        assert payment_splitter.totalShares(pool_id) == 9000  # 6000 + 3000

    def test_update_shares_non_owner_fails(self, payment_splitter, alice, bob, charlie):
        """Non-owner should not be able to update shares."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob, charlie], [7000, 3000])
        
        with boa.env.prank(bob):
            with pytest.raises(boa.BoaError, match="not pool owner"):
                payment_splitter.updateShares(pool_id, charlie, 5000)

    def test_add_recipient(self, payment_splitter, alice, bob, charlie, operator):
        """Pool owner should be able to add recipients."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob, charlie], [7000, 3000])
            payment_splitter.addRecipient(pool_id, operator, 2000)
        
        assert payment_splitter.isRecipient(pool_id, operator) is True
        assert payment_splitter.shares(pool_id, operator) == 2000
        assert payment_splitter.totalShares(pool_id) == 12000

    def test_add_existing_recipient_fails(self, payment_splitter, alice, bob, charlie):
        """Should fail adding existing recipient."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob, charlie], [7000, 3000])
            with pytest.raises(boa.BoaError, match="already recipient"):
                payment_splitter.addRecipient(pool_id, bob, 1000)

    def test_remove_recipient(self, payment_splitter, alice, bob, charlie):
        """Pool owner should be able to remove recipients."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob, charlie], [7000, 3000])
            payment_splitter.removeRecipient(pool_id, charlie)
        
        assert payment_splitter.isRecipient(pool_id, charlie) is False
        assert payment_splitter.shares(pool_id, charlie) == 0
        assert payment_splitter.totalShares(pool_id) == 7000


class TestViewFunctions:
    """Tests for view functions."""

    def test_pending_payment(self, payment_splitter, funded_usdc, alice, bob, charlie):
        """pendingPayment should return correct amount."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob, charlie], [6000, 4000])
            funded_usdc.approve(payment_splitter.address, 100 * 10**6)
            payment_splitter.deposit(pool_id, 100 * 10**6)
        
        assert payment_splitter.pendingPayment(pool_id, bob) == 60 * 10**6
        assert payment_splitter.pendingPayment(pool_id, charlie) == 40 * 10**6

    def test_get_pool_info(self, payment_splitter, funded_usdc, alice, bob):
        """getPoolInfo should return correct values."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob], [10000])
            funded_usdc.approve(payment_splitter.address, 50 * 10**6)
            payment_splitter.deposit(pool_id, 50 * 10**6)
        
        owner, total_shares, total_received = payment_splitter.getPoolInfo(pool_id)
        
        assert owner == alice
        assert total_shares == 10000
        assert total_received == 50 * 10**6

    def test_get_recipient_info(self, payment_splitter, funded_usdc, alice, bob):
        """getRecipientInfo should return correct values."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob], [10000])
            funded_usdc.approve(payment_splitter.address, 100 * 10**6)
            payment_splitter.deposit(pool_id, 100 * 10**6)
        
        with boa.env.prank(bob):
            payment_splitter.claim(pool_id)
        
        shares, claimed, pending, is_recipient = payment_splitter.getRecipientInfo(pool_id, bob)
        
        assert shares == 10000
        assert claimed == 100 * 10**6
        assert pending == 0
        assert is_recipient is True

    def test_get_share_percentage(self, payment_splitter, alice, bob, charlie):
        """getSharePercentage should return correct percentage."""
        with boa.env.prank(alice):
            pool_id = payment_splitter.createPool([bob, charlie], [7500, 2500])
        
        assert payment_splitter.getSharePercentage(pool_id, bob) == 7500
        assert payment_splitter.getSharePercentage(pool_id, charlie) == 2500
