# @version ^0.4.0

"""
@title IERC20 Interface
@author Vyper Agentic Payments
@notice Standard ERC-20 interface for interacting with USDC on Arc
@dev USDC contract on Arc Testnet: 0x3600000000000000000000000000000000000000
"""

@external
@view
def name() -> String[64]:
    ...

@external
@view
def symbol() -> String[32]:
    ...

@external
@view
def decimals() -> uint8:
    ...

@external
@view
def totalSupply() -> uint256:
    ...

@external
@view
def balanceOf(account: address) -> uint256:
    ...

@external
@view
def allowance(owner: address, spender: address) -> uint256:
    ...

@external
def transfer(to: address, amount: uint256) -> bool:
    ...

@external
def approve(spender: address, amount: uint256) -> bool:
    ...

@external
def transferFrom(sender: address, recipient: address, amount: uint256) -> bool:
    ...
