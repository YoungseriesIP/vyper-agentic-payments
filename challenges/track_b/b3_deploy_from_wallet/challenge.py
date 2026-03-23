"""
B3. Deploy a Vyper Contract from Your Circle Wallet

Use CircleWalletSigner and CircleTxExecutor to deploy contracts/Vault.vy
from a Developer-Controlled Wallet on Arc Testnet.

Environment variables required:
  CIRCLE_API_KEY
  CIRCLE_ENTITY_SECRET

Run:
  python challenges/track_b/b3_deploy_from_wallet/challenge.py
"""

import os

import boa
from circlekit import GatewayClient
from circlekit.wallets import CircleWalletSigner, CircleTxExecutor

ARC_TESTNET_RPC = os.getenv("ARC_TESTNET_RPC", "")
ARC_USDC_ADDRESS = "0x3600000000000000000000000000000000000000"


def create_signer(wallet_id: str, wallet_address: str) -> CircleWalletSigner:
    """
    Create a CircleWalletSigner for transaction signing.

    Args:
        wallet_id: Circle wallet UUID from B2.
        wallet_address: On-chain address of the Circle wallet.

    Returns:
        A configured CircleWalletSigner instance.
    """
    # Implement: return CircleWalletSigner(wallet_id=..., wallet_address=...)
    raise NotImplementedError("Create a CircleWalletSigner with your wallet credentials")


def create_tx_executor(wallet_id: str, wallet_address: str) -> CircleTxExecutor:
    """
    Create a CircleTxExecutor for transaction broadcasting.

    Args:
        wallet_id: Circle wallet UUID from B2.
        wallet_address: On-chain address of the Circle wallet.

    Returns:
        A configured CircleTxExecutor instance.
    """
    # Implement: return CircleTxExecutor(wallet_id=..., wallet_address=...)
    raise NotImplementedError("Create a CircleTxExecutor with your wallet credentials")


def deploy_vault_from_circle_wallet(
    signer: CircleWalletSigner,
    tx_executor: CircleTxExecutor,
):
    """
    Deploy contracts/Vault.vy to Arc Testnet from your Circle Wallet.

    Steps:
      1. Create a GatewayClient with the signer and tx_executor
      2. Set the network to Arc Testnet RPC
      3. Deploy contracts/Vault.vy with the Arc USDC address

    Args:
        signer: A configured CircleWalletSigner.
        tx_executor: A configured CircleTxExecutor.

    Returns:
        The deployed Vault contract instance.
    """
    # Implement:
    #   client = GatewayClient(chain="arcTestnet", signer=signer, tx_executor=tx_executor)
    #   boa.set_network_env(ARC_TESTNET_RPC)
    #   contract = boa.load("contracts/Vault.vy", ARC_USDC_ADDRESS)
    #   return contract
    raise NotImplementedError("Configure boa with the Circle signer and deploy Vault.vy")


if __name__ == "__main__":
    wallet_id = os.environ.get("CIRCLE_WALLET_ID", "")
    wallet_address = os.environ.get("CIRCLE_WALLET_ADDRESS", "")

    assert wallet_id, "Set CIRCLE_WALLET_ID environment variable"
    assert wallet_address, "Set CIRCLE_WALLET_ADDRESS environment variable"

    signer = create_signer(wallet_id, wallet_address)
    tx_executor = create_tx_executor(wallet_id, wallet_address)
    contract = deploy_vault_from_circle_wallet(signer, tx_executor)

    print(f"Vault deployed at: {contract.address}")
    print(f"Deployer: {wallet_address}")
