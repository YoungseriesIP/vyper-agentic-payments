# @version ^0.4.0

"""
@title IERC721 Interface
@author Vyper Agentic Payments
@notice Standard ERC-721 interface for NFT functionality
@dev Used by AgentIdentity.vy for agent identity NFTs
"""

@external
@view
def balanceOf(owner: address) -> uint256:
    ...

@external
@view
def ownerOf(tokenId: uint256) -> address:
    ...

@external
@view
def getApproved(tokenId: uint256) -> address:
    ...

@external
@view
def isApprovedForAll(owner: address, operator: address) -> bool:
    ...

@external
def approve(to: address, tokenId: uint256):
    ...

@external
def setApprovalForAll(operator: address, approved: bool):
    ...

@external
def transferFrom(from_addr: address, to: address, tokenId: uint256):
    ...

@external
def safeTransferFrom(from_addr: address, to: address, tokenId: uint256):
    ...

@external
def safeTransferFrom(from_addr: address, to: address, tokenId: uint256, data: Bytes[1024]):
    ...
