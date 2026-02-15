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

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DEPLOYMENTS_FILE = PROJECT_ROOT / "deployments.json"

ARC_TESTNET_RPC = os.getenv("ARC_TESTNET_RPC", "https://rpc.testnet.arc.circle.com")
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
    boa.env.add_account(boa.env.generate_address("user"), private_key)

    deployments = load_deployments()
    chain_deployments = deployments.get(ARC_TESTNET_CHAIN_ID, {})

    if not chain_deployments:
        print(f"No deployments found for chain {ARC_TESTNET_CHAIN_ID}")
        sys.exit(1)

    print("Deployed contracts:")
    for name, info in chain_deployments.items():
        print(f"  {name}: {info['address']}")

    # ─────────────────────────────────────────────────────────────────────────
    # Read from AgentIdentity
    # ─────────────────────────────────────────────────────────────────────────
    identity_info = chain_deployments.get("AgentIdentity")
    if identity_info:
        print()
        print("=" * 64)
        print("  AgentIdentity Contract")
        print("=" * 64)
        print()

        identity = load_contract("AgentIdentity", identity_info["address"])

        name = identity.name()
        symbol = identity.symbol()
        total_agents = identity.totalAgents()

        print(f"  Name:         {name}")
        print(f"  Symbol:       {symbol}")
        print(f"  Total Agents: {total_agents}")

        # Register a new agent
        print()
        print("  Registering a new agent...")
        metadata_uri = f"ipfs://QmExample{__import__('time').time_ns()}"

        try:
            agent_id = identity.registerAgent(metadata_uri)
            print(f"  Agent ID: {agent_id}")
            print(f"  New Total Agents: {identity.totalAgents()}")
        except Exception as e:
            print(f"  Registration failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Read from AgentReputation
    # ─────────────────────────────────────────────────────────────────────────
    reputation_info = chain_deployments.get("AgentReputation")
    if reputation_info:
        print()
        print("=" * 64)
        print("  AgentReputation Contract")
        print("=" * 64)
        print()

        reputation = load_contract("AgentReputation", reputation_info["address"])

        registry_addr = reputation.identityRegistry()
        print(f"  Identity Registry: {registry_addr}")

        try:
            avg_score = reputation.getAverageScore(1)
            print(f"  Agent 1 Average Score: {avg_score / 100}")
        except Exception:
            print("  Agent 1 not found or no feedback yet")

    print()
    print("=" * 64)
    print("  INTERACTION COMPLETE")
    print("=" * 64)


if __name__ == "__main__":
    main()
