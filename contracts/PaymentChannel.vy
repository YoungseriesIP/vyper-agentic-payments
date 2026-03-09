# @version ^0.4.0

"""
@title PaymentChannel - Bidirectional USDC Payment Channel with Challenge Period
@author Vyper Agentic Payments
@notice Off-chain micropayments settled in two on-chain transactions
@dev Collapses an entire agent session into open + close, regardless of call count.

AGENTIC PATTERN:
    x402 generates one on-chain transaction per API call. An agent session
    with hundreds of calls generates hundreds of transactions. A payment
    channel collapses the entire session into two on-chain transactions
    (open and close) regardless of how many calls happened in between.

CHANNEL LIFECYCLE:
    OPEN (0) → CHALLENGED (1) → CLOSED (2)

    Happy path:  open_channel → cooperative_close
    Dispute path: open_channel → unilateral_close → [challenge] → finalize
    Expiry path:  open_channel → reclaim (after expiry)

INVARIANTS:
    - finalize cannot succeed before the challenge window closes
    - reclaim cannot succeed before expiry
    - higher_amount in challenge must be strictly greater than the contested amount
    - Signature verification uses ecrecover. Validate the signer matches
      the expected party before accepting any state update

USDC on Arc Testnet: 0x3600000000000000000000000000000000000000
"""

# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACES
# ═══════════════════════════════════════════════════════════════════════════════

interface IERC20:
    def transfer(to: address, amount: uint256) -> bool: nonpayable
    def transferFrom(sender: address, recipient: address, amount: uint256) -> bool: nonpayable
    def balanceOf(account: address) -> uint256: view

# ═══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

event ChannelOpened:
    channel_id: indexed(uint256)
    payer: indexed(address)
    payee: indexed(address)
    balance: uint256
    expiry: uint256

event ChannelCooperativelyClosed:
    channel_id: indexed(uint256)
    payer_amount: uint256
    payee_amount: uint256

event UnilateralCloseInitiated:
    channel_id: indexed(uint256)
    initiator: indexed(address)
    amount: uint256
    challenge_deadline: uint256

event ChannelChallenged:
    channel_id: indexed(uint256)
    challenger: indexed(address)
    higher_amount: uint256

event ChannelFinalized:
    channel_id: indexed(uint256)
    payer_amount: uint256
    payee_amount: uint256

event ChannelReclaimed:
    channel_id: indexed(uint256)
    payer: indexed(address)
    amount: uint256

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Channel statuses
STATUS_OPEN: constant(uint8) = 0
STATUS_CHALLENGED: constant(uint8) = 1
STATUS_CLOSED: constant(uint8) = 2

# Blocks after unilateral close before finalization is allowed
CHALLENGE_PERIOD: constant(uint256) = 100

# Minimum USDC deposit to open a channel (1 USDC)
MIN_DEPOSIT: constant(uint256) = 1_000_000

# ═══════════════════════════════════════════════════════════════════════════════
# STATE VARIABLES
# ═══════════════════════════════════════════════════════════════════════════════

# USDC token address
usdc: public(address)

# Channel counter
next_channel_id: public(uint256)

# Channel participants
channel_payer: public(HashMap[uint256, address])
channel_payee: public(HashMap[uint256, address])

# Channel funds
channel_balance: public(HashMap[uint256, uint256])

# Expiry block after which payer can reclaim unspent funds
channel_expiry: public(HashMap[uint256, uint256])

# Channel status (OPEN / CHALLENGED / CLOSED)
channel_status: public(HashMap[uint256, uint8])

# Challenge state: proposed payee amount and deadline block
channel_challenge_amount: public(HashMap[uint256, uint256])
channel_challenge_deadline: public(HashMap[uint256, uint256])

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTOR
# ═══════════════════════════════════════════════════════════════════════════════

@deploy
def __init__(usdc_address: address):
    """
    @notice Initialize the payment channel contract
    @param usdc_address USDC token address (0x3600... on Arc Testnet)
    """
    assert usdc_address != empty(address), "PaymentChannel: zero address"
    self.usdc = usdc_address
    self.next_channel_id = 1

# ═══════════════════════════════════════════════════════════════════════════════
# CHANNEL OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@external
def open_channel(payee: address, expiry: uint256) -> uint256:
    """
    @notice Open a payment channel by depositing USDC
    @param payee The counterparty who will receive payments
    @param expiry Block number after which payer can reclaim unspent funds
    @return The new channel ID
    @dev Caller (payer) must have approved this contract to spend USDC.
         Deposit amount must be >= MIN_DEPOSIT.
    """
    return 0


@external
def cooperative_close(channel_id: uint256, amount: uint256, payer_sig: Bytes[65], payee_sig: Bytes[65]):
    """
    @notice Close a channel cooperatively with both parties' signatures
    @param channel_id The channel to close
    @param amount Amount owed to the payee (remainder returns to payer)
    @param payer_sig Payer's signature over the final state
    @param payee_sig Payee's signature over the final state
    @dev Both signatures must validate against the channel's payer and payee.
         Channel closes immediately; no challenge period needed.
    """
    pass


@external
def unilateral_close(channel_id: uint256, amount: uint256, sig: Bytes[65]):
    """
    @notice Initiate a unilateral close with a signed state
    @param channel_id The channel to close
    @param amount Amount owed to the payee per the submitted state
    @param sig Signature from the counterparty over the submitted state
    @dev Starts the challenge period. Either party can call this with
         a valid signature from the other party.
    """
    pass


@external
def challenge(channel_id: uint256, higher_amount: uint256, higher_sig: Bytes[65]):
    """
    @notice Challenge a unilateral close with a higher-amount signed state
    @param channel_id The channel being challenged
    @param higher_amount A strictly higher amount than the current challenge amount
    @param higher_sig Signature validating the higher amount
    @dev Must be called before the challenge deadline expires.
         higher_amount must be strictly greater than channel_challenge_amount.
    """
    pass


@external
def finalize(channel_id: uint256):
    """
    @notice Finalize a channel after the challenge period expires
    @param channel_id The channel to finalize
    @dev Can only be called after the challenge deadline has passed with
         no successful challenge. Splits funds per the last accepted state:
         payee receives challenge_amount, payer receives the remainder.
    """
    pass


@external
def reclaim(channel_id: uint256):
    """
    @notice Reclaim all funds from an expired channel with no payee activity
    @param channel_id The channel to reclaim
    @dev Only the payer can call. Only works after the channel expiry block
         if the channel is still in OPEN status (no close has been initiated).
    """
    pass
