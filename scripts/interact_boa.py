"""
interact_boa.py

Interact with deployed Vyper contracts on Arc Testnet using titanoboa.

Prerequisites:
  - Deployed contracts (run deploy_boa.py first)
  - PRIVATE_KEY environment variable

Usage:
  python scripts/interact_boa.py
"""

import json
import os
import sys
from pathlib import Path

import boa
from dotenv import load_dotenv
from eth_account import Account

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DEPLOYMENTS_FILE = PROJECT_ROOT / "deployments.json"

ARC_TESTNET_RPC = os.getenv("ARC_TESTNET_RPC", "https://arc-testnet.drpc.org")
ARC_TESTNET_CHAIN_ID = str(int(os.getenv("ARC_TESTNET_CHAIN_ID", "5042002")))


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def load_deployments() -> dict:
    if not DEPLOYMENTS_FILE.exists():
        print("Error: deployments.json not found. Run deploy_boa.py first.")
        sys.exit(1)
    return json.loads(DEPLOYMENTS_FILE.read_text())


def load_contract(contract_name: str, address: str):
    """Load a deployed contract using boa.load_partial().at()."""
    contract_path = CONTRACTS_DIR / f"{contract_name}.vy"
    return boa.load_partial(str(contract_path)).at(address)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    print("=" * 64)
    print("  Interact with Deployed Contracts (titanoboa)")
    print("=" * 64)
    print()

    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        print("Error: PRIVATE_KEY is required.")
        sys.exit(1)

    # Configure boa for Arc Testnet
    boa.set_network_env(ARC_TESTNET_RPC)
    account = Account.from_key(private_key)
    boa.env.add_account(account, force_eoa=True)

    deployments = load_deployments()
    chain_deployments = deployments.get(ARC_TESTNET_CHAIN_ID, {})

    if not chain_deployments:
        print(f"No deployments found for chain {ARC_TESTNET_CHAIN_ID}")
        sys.exit(1)

    print("Deployed contracts:")
    for name, info in chain_deployments.items():
        print(f"  {name}: {info['address']}")

    print()
    print("=" * 64)
    print("  INTERACTION COMPLETE")
    print("=" * 64)


if __name__ == "__main__":
    main()
