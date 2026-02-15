"""
Deposit USDC into the Gateway Wallet contract.

This is a prerequisite for using Circle Gateway batched payments.
The buyer must have a USDC balance in the Gateway contract to pay for resources.

Usage:
  1. Get Testnet USDC from https://faucet.circle.com (Use Arc Testnet)
  2. Set PRIVATE_KEY environment variable
  3. Run: python examples/agent-marketplace/deposit.py --amount 0.5

Options:
  --amount, -a   Amount of USDC to deposit (default: 0.5)
  --help, -h     Show this help message

Requires: Funded wallet on Arc Testnet with USDC
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deposit USDC into Gateway Wallet")
    parser.add_argument(
        "--amount", "-a",
        default=os.getenv("DEPOSIT_AMOUNT", "0.5"),
        help="Amount of USDC to deposit (default: 0.5)",
    )
    return parser.parse_args()


async def main() -> None:
    from circlekit import GatewayClient

    args = parse_args()
    deposit_amount = args.amount

    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        print("Error: PRIVATE_KEY environment variable is required")
        print("Usage: PRIVATE_KEY=0x... python examples/agent-marketplace/deposit.py")
        print("\nGet testnet USDC from: https://faucet.circle.com")
        sys.exit(1)

    print("\n=== Deposit USDC into Gateway Wallet ===\n")

    async with GatewayClient(chain="arcTestnet", private_key=private_key) as gateway:
        print(f"Account: {gateway.address}")
        print(f"Chain:   {gateway.chain_name}")

        print("\n1. Checking balances...")
        before = await gateway.get_balances()
        print(f"   Wallet USDC:      {before.wallet.formatted}")
        print(f"   Gateway Available: {before.gateway.formatted_available}")

        if float(before.wallet.formatted) < float(deposit_amount):
            print("\n   Insufficient USDC balance.")
            print("   Get tokens from: https://faucet.circle.com")
            return

        print(f"\n2. Depositing {deposit_amount} USDC...")
        result = await gateway.deposit(deposit_amount)
        print(f"   Tx: {result.deposit_tx_hash}")

        print("\n3. Updated balances:")
        after = await gateway.get_balances()
        print(f"   Wallet USDC:      {after.wallet.formatted}")
        print(f"   Gateway Available: {after.gateway.formatted_available}")

        print("\nDone! You can now make gasless payments.\n")


if __name__ == "__main__":
    asyncio.run(main())
