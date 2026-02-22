"""
Tests for SubscriptionManager.vy - Recurring USDC Payments

This test suite covers:
- Plan creation and management
- Subscription creation and first payment
- Charging subscriptions
- Pause, resume, and cancel
- View functions and status checks
"""

import pytest
import boa


@pytest.fixture
def subscription_manager(funded_usdc, deployer):
    """Deploy the SubscriptionManager contract."""
    with boa.env.prank(deployer):
        return boa.load("contracts/SubscriptionManager.vy", funded_usdc.address)


# Constants from contract
STATUS_NONE = 0
STATUS_ACTIVE = 1
STATUS_PAUSED = 2
STATUS_CANCELLED = 3

HOUR = 3600
DAY = 86400
WEEK = 604800
MONTH = 2592000  # 30 days


class TestSubscriptionManagerDeployment:
    """Tests for contract deployment."""

    def test_initial_state(self, subscription_manager, funded_usdc):
        """Contract should initialize correctly."""
        assert subscription_manager.usdc() == funded_usdc.address
        assert subscription_manager.next_plan_id() == 1
        assert subscription_manager.next_subscription_id() == 1

    def test_deploy_with_zero_address_fails(self):
        """Should fail with zero USDC address."""
        with pytest.raises(boa.BoaError, match="zero address"):
            boa.load("contracts/SubscriptionManager.vy", "0x0000000000000000000000000000000000000000")


class TestPlanCreation:
    """Tests for creating subscription plans."""

    def test_create_plan(self, subscription_manager, alice):
        """Should create a plan successfully."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "ipfs://metadata")
        
        assert plan_id == 1
        assert subscription_manager.plan_provider(plan_id) == alice
        assert subscription_manager.plan_price(plan_id) == 10 * 10**6
        assert subscription_manager.plan_interval(plan_id) == MONTH
        assert subscription_manager.plan_active(plan_id) is True
        assert subscription_manager.plan_metadata(plan_id) == "ipfs://metadata"

    def test_create_plan_increments_id(self, subscription_manager, alice):
        """Plan IDs should increment."""
        with boa.env.prank(alice):
            plan1 = subscription_manager.create_plan(5 * 10**6, WEEK, "")
            plan2 = subscription_manager.create_plan(10 * 10**6, MONTH, "")
        
        assert plan1 == 1
        assert plan2 == 2

    def test_create_plan_zero_price_fails(self, subscription_manager, alice):
        """Should fail with zero price."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="zero price"):
                subscription_manager.create_plan(0, MONTH, "")

    def test_create_plan_interval_too_short_fails(self, subscription_manager, alice):
        """Should fail with interval less than 1 hour."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="interval too short"):
                subscription_manager.create_plan(10 * 10**6, 60, "")  # 1 minute

    def test_create_plan_interval_too_long_fails(self, subscription_manager, alice):
        """Should fail with interval more than 1 year."""
        with boa.env.prank(alice):
            with pytest.raises(boa.BoaError, match="interval too long"):
                subscription_manager.create_plan(10 * 10**6, 31536001, "")  # 1 year + 1 sec


class TestPlanManagement:
    """Tests for plan management functions."""

    def test_update_plan_price(self, subscription_manager, alice):
        """Provider should be able to update price."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
            subscription_manager.update_plan_price(plan_id, 15 * 10**6)
        
        assert subscription_manager.plan_price(plan_id) == 15 * 10**6

    def test_update_plan_price_non_provider_fails(self, subscription_manager, alice, bob):
        """Non-provider should not be able to update price."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
        
        with boa.env.prank(bob):
            with pytest.raises(boa.BoaError, match="not provider"):
                subscription_manager.update_plan_price(plan_id, 15 * 10**6)

    def test_deactivate_plan(self, subscription_manager, alice):
        """Provider should be able to deactivate plan."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
            subscription_manager.deactivate_plan(plan_id)
        
        assert subscription_manager.plan_active(plan_id) is False


class TestSubscriptions:
    """Tests for subscription management."""

    def test_subscribe(self, subscription_manager, funded_usdc, alice, bob):
        """Should create subscription and pay first interval."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
        
        alice_balance_before = funded_usdc.balanceOf(alice)
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
        
        assert sub_id == 1
        assert subscription_manager.subscription_plan(sub_id) == plan_id
        assert subscription_manager.subscription_subscriber(sub_id) == bob
        assert subscription_manager.subscription_status(sub_id) == STATUS_ACTIVE
        assert subscription_manager.subscription_total_paid(sub_id) == 10 * 10**6
        
        # Provider received payment
        assert funded_usdc.balanceOf(alice) == alice_balance_before + 10 * 10**6

    def test_subscribe_inactive_plan_fails(self, subscription_manager, funded_usdc, alice, bob):
        """Should fail subscribing to inactive plan."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
            subscription_manager.deactivate_plan(plan_id)
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            with pytest.raises(boa.BoaError, match="plan not active"):
                subscription_manager.subscribe(plan_id)

    def test_subscribe_already_subscribed_fails(self, subscription_manager, funded_usdc, alice, bob):
        """Should fail if already subscribed to same plan."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 20 * 10**6)
            subscription_manager.subscribe(plan_id)
            
            with pytest.raises(boa.BoaError, match="already subscribed"):
                subscription_manager.subscribe(plan_id)


class TestCharging:
    """Tests for charging subscriptions."""

    def test_charge_when_due(self, subscription_manager, funded_usdc, alice, bob):
        """Should charge subscription when due."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, HOUR, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 100 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
        
        alice_balance_before = funded_usdc.balanceOf(alice)
        
        # Fast forward 1 hour
        boa.env.time_travel(seconds=HOUR + 1)
        
        # Anyone can charge
        subscription_manager.charge(sub_id)
        
        assert subscription_manager.subscription_total_paid(sub_id) == 20 * 10**6
        assert funded_usdc.balanceOf(alice) == alice_balance_before + 10 * 10**6

    def test_charge_not_due_fails(self, subscription_manager, funded_usdc, alice, bob):
        """Should fail if not due yet."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, HOUR, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 100 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
        
        # Try to charge immediately
        with pytest.raises(boa.BoaError, match="not due yet"):
            subscription_manager.charge(sub_id)

    def test_charge_inactive_fails(self, subscription_manager, funded_usdc, alice, bob):
        """Should fail charging inactive subscription."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, HOUR, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 100 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
            subscription_manager.cancel(sub_id)
        
        boa.env.time_travel(seconds=HOUR + 1)
        
        with pytest.raises(boa.BoaError, match="not active"):
            subscription_manager.charge(sub_id)


class TestCancelPauseResume:
    """Tests for cancel, pause, resume."""

    def test_subscriber_cancel(self, subscription_manager, funded_usdc, alice, bob):
        """Subscriber should be able to cancel."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
            subscription_manager.cancel(sub_id)
        
        assert subscription_manager.subscription_status(sub_id) == STATUS_CANCELLED

    def test_provider_cancel(self, subscription_manager, funded_usdc, alice, bob):
        """Provider should be able to cancel."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
        
        with boa.env.prank(alice):
            subscription_manager.cancel(sub_id)
        
        assert subscription_manager.subscription_status(sub_id) == STATUS_CANCELLED

    def test_unauthorized_cancel_fails(self, subscription_manager, funded_usdc, alice, bob, charlie):
        """Unauthorized user should not be able to cancel."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
        
        with boa.env.prank(charlie):
            with pytest.raises(boa.BoaError, match="not authorized"):
                subscription_manager.cancel(sub_id)

    def test_pause(self, subscription_manager, funded_usdc, alice, bob):
        """Subscriber should be able to pause."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
            subscription_manager.pause(sub_id)
        
        assert subscription_manager.subscription_status(sub_id) == STATUS_PAUSED

    def test_resume(self, subscription_manager, funded_usdc, alice, bob):
        """Subscriber should be able to resume."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
            subscription_manager.pause(sub_id)
            subscription_manager.resume(sub_id)
        
        assert subscription_manager.subscription_status(sub_id) == STATUS_ACTIVE


class TestViewFunctions:
    """Tests for view functions."""

    def test_is_due(self, subscription_manager, funded_usdc, alice, bob):
        """isDue should return correct status."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, HOUR, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
        
        assert subscription_manager.is_due(sub_id) is False
        
        boa.env.time_travel(seconds=HOUR + 1)
        
        assert subscription_manager.is_due(sub_id) is True

    def test_is_overdue(self, subscription_manager, funded_usdc, alice, bob):
        """isOverdue should return correct status after grace period."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, HOUR, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
        
        # 1 hour later - due but not overdue
        boa.env.time_travel(seconds=HOUR + 1)
        assert subscription_manager.is_due(sub_id) is True
        assert subscription_manager.is_overdue(sub_id) is False
        
        # 7 days later - overdue
        boa.env.time_travel(seconds=DAY * 7 + 1)
        assert subscription_manager.is_overdue(sub_id) is True

    def test_next_charge_time(self, subscription_manager, funded_usdc, alice, bob):
        """nextChargeTime should return correct timestamp."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, HOUR, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
        
        last_charge = subscription_manager.subscription_last_charge(sub_id)
        expected = last_charge + HOUR
        
        assert subscription_manager.next_charge_time(sub_id) == expected

    def test_get_plan_info(self, subscription_manager, alice):
        """getPlanInfo should return correct values."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "ipfs://test")
        
        provider, price, interval, active, metadata = subscription_manager.get_plan_info(plan_id)
        
        assert provider == alice
        assert price == 10 * 10**6
        assert interval == MONTH
        assert active is True
        assert metadata == "ipfs://test"

    def test_get_subscription_info(self, subscription_manager, funded_usdc, alice, bob):
        """getSubscriptionInfo should return correct values."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
        
        plan, subscriber, status, started, last_charge, total_paid = subscription_manager.get_subscription_info(sub_id)
        
        assert plan == plan_id
        assert subscriber == bob
        assert status == STATUS_ACTIVE
        assert total_paid == 10 * 10**6

    def test_get_subscription_id(self, subscription_manager, funded_usdc, alice, bob):
        """getSubscriptionId should return correct ID."""
        with boa.env.prank(alice):
            plan_id = subscription_manager.create_plan(10 * 10**6, MONTH, "")
        
        assert subscription_manager.get_subscription_id(bob, plan_id) == 0
        
        with boa.env.prank(bob):
            funded_usdc.approve(subscription_manager.address, 10 * 10**6)
            sub_id = subscription_manager.subscribe(plan_id)
        
        assert subscription_manager.get_subscription_id(bob, plan_id) == sub_id
