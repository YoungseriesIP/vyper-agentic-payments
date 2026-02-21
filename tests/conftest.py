"""
Shared test fixtures for Vyper Agentic Payments contracts.

This module provides:
- Mock USDC token for testing USDC interactions
- Common test accounts
- Contract deployment helpers
"""

import pytest
import boa


# ═══════════════════════════════════════════════════════════════════════════════
# MOCK USDC TOKEN
# ═══════════════════════════════════════════════════════════════════════════════

MOCK_USDC_SOURCE = """
# @version ^0.4.0
\"\"\"
@title Mock USDC Token for Testing
@notice A simple ERC-20 token that mimics USDC for testing purposes
@dev Includes a mint() function for easy test setup
\"\"\"

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
    self.decimals = 6  # USDC uses 6 decimals

@external
def mint(to: address, amount: uint256):
    \"\"\"Mint tokens to an address (for testing only)\"\"\"
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
# MOCK ERC721 RECEIVER
# ═══════════════════════════════════════════════════════════════════════════════

MOCK_ERC721_RECEIVER_SOURCE = """
# @version ^0.4.0
\"\"\"
@title Mock ERC721 Receiver for Testing
@notice A contract that can receive ERC-721 tokens
\"\"\"

received_count: public(uint256)
last_token_id: public(uint256)
last_operator: public(address)
last_from: public(address)

# Return the correct selector to accept the transfer
ERC721_RECEIVED: constant(bytes4) = 0x150b7a02

@external
def onERC721Received(
    operator: address,
    from_addr: address,
    tokenId: uint256,
    data: Bytes[1024]
) -> bytes4:
    self.received_count += 1
    self.last_token_id = tokenId
    self.last_operator = operator
    self.last_from = from_addr
    return ERC721_RECEIVED
"""


MOCK_BAD_RECEIVER_SOURCE = """
# @version ^0.4.0
\"\"\"
@title Mock Bad ERC721 Receiver for Testing
@notice A contract that rejects ERC-721 tokens
\"\"\"

@external
def onERC721Received(
    operator: address,
    from_addr: address,
    tokenId: uint256,
    data: Bytes[1024]
) -> bytes4:
    # Return wrong selector to reject the transfer
    return 0xdeadbeef
"""


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True, scope="module")
def reset_boa_env():
    """Reset boa VM state before each test module to prevent cross-file contamination."""
    boa.reset_env()
    yield


@pytest.fixture
def deployer():
    """The main deployer account."""
    return boa.env.generate_address("deployer")


@pytest.fixture
def alice():
    """Test account: Alice (agent owner)."""
    return boa.env.generate_address("alice")


@pytest.fixture
def bob():
    """Test account: Bob (another agent owner)."""
    return boa.env.generate_address("bob")


@pytest.fixture
def charlie():
    """Test account: Charlie (client/reviewer)."""
    return boa.env.generate_address("charlie")


@pytest.fixture
def operator():
    """Test account: Operator (approved for all)."""
    return boa.env.generate_address("operator")


@pytest.fixture
def usdc():
    """Deploy a fresh mock USDC token."""
    return boa.loads(MOCK_USDC_SOURCE)


@pytest.fixture
def erc721_receiver():
    """Deploy a mock ERC721 receiver that accepts tokens."""
    return boa.loads(MOCK_ERC721_RECEIVER_SOURCE)


@pytest.fixture
def bad_receiver():
    """Deploy a mock ERC721 receiver that rejects tokens."""
    return boa.loads(MOCK_BAD_RECEIVER_SOURCE)


@pytest.fixture
def agent_identity():
    """Deploy the lib IdentityRegistry contract (ERC-8004)."""
    return boa.load(
        "lib/github/lufa23/erc-8004-vyper/src/identity_registry.vy",
        "AgentIdentityRegistry",
        "AGID",
    )


@pytest.fixture
def agent_reputation(agent_identity, deployer):
    """Deploy the lib ReputationRegistry contract (ERC-8004)."""
    with boa.env.prank(deployer):
        return boa.load(
            "lib/github/lufa23/erc-8004-vyper/src/reputation_registry.vy",
            agent_identity.address,
        )


@pytest.fixture
def funded_usdc(usdc, alice, bob, charlie):
    """USDC token with funded test accounts (1000 USDC each)."""
    amount = 1000 * 10**6  # 1000 USDC with 6 decimals
    usdc.mint(alice, amount)
    usdc.mint(bob, amount)
    usdc.mint(charlie, amount)
    return usdc


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_agent_metadata_uri(agent_name: str, x402_support: bool = True) -> str:
    """Create a mock IPFS URI for agent metadata."""
    # In a real scenario, this would be an IPFS hash
    # For testing, we use a deterministic URI based on the name
    return f"ipfs://Qm{agent_name.replace(' ', '')}MetadataHash12345"
