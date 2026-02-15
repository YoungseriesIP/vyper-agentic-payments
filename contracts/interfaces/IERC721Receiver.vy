# @version ^0.4.0

"""
@title IERC721Receiver Interface
@author Vyper Agentic Payments
@notice Interface for contracts that want to receive ERC-721 tokens via safeTransferFrom
@dev Implementing contracts must return the selector to confirm the transfer
"""

# The selector for onERC721Received: bytes4(keccak256("onERC721Received(address,address,uint256,bytes)"))
# = 0x150b7a02

@external
def onERC721Received(
    operator: address,
    from_addr: address,
    tokenId: uint256,
    data: Bytes[1024]
) -> bytes4:
    ...
