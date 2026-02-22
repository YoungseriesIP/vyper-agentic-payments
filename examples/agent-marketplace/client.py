"""
Agent Marketplace - Buyer Client

An AI agent client that discovers agents, pays for services, and provides feedback.
This demonstrates the full ERC-8004 agent lifecycle:

1. Create GatewayClient
2. Check balances
3. Discover agent (free endpoint)
4. Check reputation (simulated)
5. Check x402 support
6. Pay for service (gasless!)
7. Submit feedback
8. Check final balances

Requires: PRIVATE_KEY with USDC deposited in Gateway
Requires: Server running at SERVER_URL (default: http://localhost:4021)

Usage:
  1. Start server: SELLER_ADDRESS=0x... python examples/agent-marketplace/server.py
  2. Run client:   PRIVATE_KEY=0x... python examples/agent-marketplace/client.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:4021")

if not PRIVATE_KEY:
    print("Error: PRIVATE_KEY environment variable is required")
    print("Usage: PRIVATE_KEY=0x... python examples/agent-marketplace/client.py")
    print("\nGet testnet USDC from: https://faucet.circle.com")
    sys.exit(1)


# ============================================================================
# MAIN
# ============================================================================


async def main() -> None:
    from circlekit import GatewayClient

    print()
    print("=" * 64)
    print("  Agent Marketplace - x402 Buyer Client (circlekit)")
    print("=" * 64)
    print()

    # ──────────────────────────────────────────────────────────────────────
    # 1. Create Gateway Client
    # ──────────────────────────────────────────────────────────────────────
    print("1. Creating Gateway client...")

    async with GatewayClient(chain="arcTestnet", private_key=PRIVATE_KEY) as gateway:
        print(f"   Address: {gateway.address}")
        print(f"   Chain:   {gateway.chain_name}")

        # ──────────────────────────────────────────────────────────────────
        # 2. Check Balances
        # ──────────────────────────────────────────────────────────────────
        print("\n2. Checking balances...")

        balances = await gateway.get_balances()
        print(f"   Wallet USDC:  {balances.wallet.formatted}")
        print(f"   Gateway:      {balances.gateway.formatted_available} available")

        if float(balances.gateway.formatted_available) < 0.01:
            print("\n   Insufficient Gateway balance")
            print("   Run: python examples/agent-marketplace/deposit.py --amount 1")
            return

        # ──────────────────────────────────────────────────────────────────
        # 3. Discover Agent (ERC-8004 pattern)
        # ──────────────────────────────────────────────────────────────────
        print("\n3. Discovering agent...")

        import httpx

        async with httpx.AsyncClient() as http_client:
            info_response = await http_client.get(f"{SERVER_URL}/")

        if info_response.status_code != 200:
            print(f"   Failed to fetch agent info: {info_response.status_code}")
            print("   Make sure server is running")
            return

        agent_info = info_response.json()
        agent = agent_info["agent"]

        print(f"   Agent:        {agent['name']}")
        print(f"   Description:  {agent['description']}")
        print(f"   Capabilities: {', '.join(agent['capabilities'])}")
        print(
            f"   Pricing:      analyze={agent['pricing']['analyze']}, "
            f"generate={agent['pricing']['generate']}"
        )
        print(f"   x402 Support: {'Yes' if agent['x402Support'] else 'No'}")

        # ──────────────────────────────────────────────────────────────────
        # 4. Check Reputation (simulated)
        # ──────────────────────────────────────────────────────────────────
        print("\n4. Checking agent reputation...")
        print("   [SIMULATED] Would query AgentReputation.vy on-chain")
        print("   Average Score: 85/100")
        print("   Tier: Gold")
        print("   Total Feedbacks: 42")

        # ──────────────────────────────────────────────────────────────────
        # 5. Check x402 Support
        # ──────────────────────────────────────────────────────────────────
        print("\n5. Checking x402 support...")

        analyze_url = f"{SERVER_URL}/api/analyze"
        support = await gateway.supports(analyze_url)

        if support.supported:
            print("   Server supports Gateway batching")
        else:
            print(f"   Server does NOT support Gateway batching: {support.error}")
            return

        # ──────────────────────────────────────────────────────────────────
        # 6. Pay for Analysis Service (Gasless!)
        # ──────────────────────────────────────────────────────────────────
        print("\n6. Paying for /api/analyze ($0.01)...")

        try:
            result = await gateway.pay(analyze_url)

            print(f"   Paid {result.formatted_amount} USDC (gasless!)")
            print(f"   Transaction: {result.transaction}")
            print()
            print("   Response from agent:")
            print(f"   - Summary:    {result.data['result']['summary']}")
            print(f"   - Confidence: {result.data['result']['confidence'] * 100:.0f}%")
            print(f"   - Insights:   {len(result.data['result']['insights'])} found")
        except Exception as e:
            print(f"   Payment failed: {e}")
            return

        # ──────────────────────────────────────────────────────────────────
        # 7. Submit Feedback (simulated)
        # ──────────────────────────────────────────────────────────────────
        print("\n7. Submitting reputation feedback...")

        async with httpx.AsyncClient() as http_client:
            feedback_response = await http_client.post(
                f"{SERVER_URL}/feedback",
                json={
                    "score": 90,
                    "comment": "Great analysis, very insightful!",
                    "proofOfPayment": result.transaction,
                },
            )

        if feedback_response.status_code == 200:
            print("   Feedback submitted")
            print("   [SIMULATED] Would write to AgentReputation.vy on-chain")
            print("   Score: 90/100")
            print(f"   Proof of Payment: {result.transaction}")

        # ──────────────────────────────────────────────────────────────────
        # 8. Final Balances
        # ──────────────────────────────────────────────────────────────────
        print("\n8. Updated balances...")

        new_balances = await gateway.get_balances()
        print(f"   Wallet USDC:  {new_balances.wallet.formatted}")
        print(f"   Gateway:      {new_balances.gateway.formatted_available} available")

    print()
    print("=" * 64)
    print("  Complete!")
    print("=" * 64)
    print()


if __name__ == "__main__":
    asyncio.run(main())
