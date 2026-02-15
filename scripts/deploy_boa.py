"""
deploy_boa.py

Deploy Vyper contracts to Arc Testnet using titanoboa.
No compilation step needed — boa.load() compiles and deploys in one call.

Fixes the constructor arg bug in deploy-viem.ts:
  AgentEscrow expects (usdc_address, identity_registry), NOT the reverse.

Prerequisites:
  - PRIVATE_KEY environment variable (with 0x prefix)
  - Funded wallet with testnet ETH for gas

Usage:
  python scripts/deploy_boa.py                    # Deploy all contracts
  python scripts/deploy_boa.py AgentIdentity      # Deploy specific contract
"""

import json
import os
import sys
from pathlib import Path

import boa
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DEPLOYMENTS_FILE = PROJECT_ROOT / "deployments.json"

ARC_TESTNET_RPC = os.getenv("ARC_TESTNET_RPC", "https://rpc.testnet.arc.circle.com")
ARC_TESTNET_CHAIN_ID = int(os.getenv("ARC_TESTNET_CHAIN_ID", "5042002"))
USDC_ADDRESS = os.getenv("USDC_ADDRESS", "0x3600000000000000000000000000000000000000")

# Contract deployment order (respecting dependencies)
DEPLOY_ORDER = [
    "AgentIdentity",
    "AgentReputation",
    "AgentValidation",
    "AgentEscrow",
    "SpendingLimiter",
    "PaymentSplitter",
    "SubscriptionManager",
]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def load_deployments() -> dict:
    if DEPLOYMENTS_FILE.exists():
        return json.loads(DEPLOYMENTS_FILE.read_text())
    return {}


def save_deployments(deployments: dict) -> None:
    DEPLOYMENTS_FILE.write_text(json.dumps(deployments, indent=2))


def get_constructor_args(contract_name: str, deployments: dict, chain_id: str) -> list:
    """
    Return constructor arguments for a contract.

    IMPORTANT: AgentEscrow takes (usdc_address, identity_registry) in that order.
    The original deploy-viem.ts had this backwards (identity first, then USDC).
    """
    args = []

    if contract_name == "AgentEscrow":
        # FIXED: usdc_address comes FIRST, then identity_registry
        args.append(USDC_ADDRESS)
        identity_addr = deployments.get(chain_id, {}).get("AgentIdentity", {}).get("address")
        if not identity_addr:
            raise ValueError("AgentEscrow requires AgentIdentity to be deployed first")
        args.append(identity_addr)

    elif contract_name in ("AgentReputation", "AgentValidation"):
        identity_addr = deployments.get(chain_id, {}).get("AgentIdentity", {}).get("address")
        if not identity_addr:
            raise ValueError(f"{contract_name} requires AgentIdentity to be deployed first")
        args.append(identity_addr)

    elif contract_name in ("SpendingLimiter", "PaymentSplitter", "SubscriptionManager"):
        args.append(USDC_ADDRESS)

    return args


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    print("=" * 64)
    print("  Deploy Vyper Contracts (titanoboa + Arc Testnet)")
    print("=" * 64)
    print()

    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        print("Error: PRIVATE_KEY is required. Set it in your .env file.")
        sys.exit(1)

    # Configure boa for Arc Testnet
    boa.set_network_env(ARC_TESTNET_RPC)
    boa.env.add_account(boa.env.generate_address("deployer"), private_key)

    print(f"RPC:      {ARC_TESTNET_RPC}")
    print(f"Chain ID: {ARC_TESTNET_CHAIN_ID}")
    print()

    # Determine which contracts to deploy
    target = sys.argv[1] if len(sys.argv) > 1 else None
    contracts_to_deploy = [target] if target else DEPLOY_ORDER

    deployments = load_deployments()
    chain_id = str(ARC_TESTNET_CHAIN_ID)

    if chain_id not in deployments:
        deployments[chain_id] = {}

    print(f"Deploying: {', '.join(contracts_to_deploy)}")
    print()

    for contract_name in contracts_to_deploy:
        contract_path = CONTRACTS_DIR / f"{contract_name}.vy"
        if not contract_path.exists():
            print(f"  [SKIP] {contract_name}.vy not found")
            continue

        try:
            print(f"  Deploying {contract_name}...")

            args = get_constructor_args(contract_name, deployments, chain_id)

            # boa.load() compiles + deploys in one step — no artifacts needed
            contract = boa.load(str(contract_path), *args)

            print(f"    Deployed at: {contract.address}")

            deployments[chain_id][contract_name] = {
                "address": contract.address,
                "deployedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            }
            save_deployments(deployments)

        except Exception as e:
            print(f"    Failed: {e}")

    # Summary
    print()
    print("=" * 64)
    print("  DEPLOYMENT SUMMARY")
    print("=" * 64)
    print()

    for name, info in deployments.get(chain_id, {}).items():
        print(f"  {name}: {info['address']}")

    print(f"\nDeployments saved to: {DEPLOYMENTS_FILE}")


if __name__ == "__main__":
    main()
