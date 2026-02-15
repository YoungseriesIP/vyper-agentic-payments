# Agent Marketplace Example

An AI agent offering paid API services via Circle Gateway x402 micropayments.

This example demonstrates the full ERC-8004 agentic payment flow:
1. **Agent Discovery** — Clients query agent capabilities (free)
2. **Reputation Check** — Clients verify agent quality (simulated, would read from AgentReputation.vy)
3. **x402 Payment** — Clients pay for services via gasless micropayments
4. **Service Delivery** — Agent provides the paid service
5. **Reputation Feedback** — Clients rate the agent (simulated, would write to AgentReputation.vy)

## Prerequisites

- Node.js >= 18
- Cloudsmith token (for `@circlefin/x402-batching`)
- EVM private key for the client (buyer)
- Testnet USDC on Arc Testnet

### Get Testnet USDC

1. Go to [faucet.circle.com](https://faucet.circle.com)
2. Select "Arc Testnet"
3. Enter your wallet address
4. Request USDC

## Setup

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```
# Seller's wallet address (receives payments)
SELLER_ADDRESS=0xYourSellerAddressHere

# Buyer's private key (for client.ts)
PRIVATE_KEY=0xYourPrivateKeyHere

# Server port (optional, default 4021)
PORT=4021
```

### 2. Install Dependencies

From the repo root:
```bash
npm install
```

### 3. Deposit USDC to Gateway (One-Time Setup)

The buyer must deposit USDC into Gateway before making gasless payments:

```bash
PRIVATE_KEY=0x... python deposit.py --amount 1
```

Expected output:
```
=== Deposit USDC into Gateway Wallet ===

Account: 0x...
Chain: Arc Testnet

1. Checking balances...
   Wallet USDC: 10.000000
   Gateway Available: 0.000000

2. Depositing 1 USDC...
   ✅ Tx: 0x...

3. Updated balances:
   Wallet USDC: 9.000000
   Gateway Available: 1.000000

✅ Done! You can now make gasless payments.
```

## Running the Example

You'll need **two terminals**.

### Terminal 1: Start the Agent Server

```bash
SELLER_ADDRESS=0x... npx tsx server.ts
```

Expected output:
```
╔════════════════════════════════════════════════════════════════╗
║        Agent Marketplace - x402 Seller Example                 ║
╚════════════════════════════════════════════════════════════════╝

Server:    http://localhost:4021
Agent:     DataAnalyzer-v1
Seller:    0x...

Endpoints:
  GET  /              - Agent info (free)
  GET  /health        - Health check (free)
  GET  /api/analyze   - Data analysis ($0.01)
  POST /api/generate  - Content generation ($0.05)
  POST /feedback      - Submit reputation feedback (free)
```

### Terminal 2: Run the Buyer Client

```bash
PRIVATE_KEY=0x... npx tsx client.ts
```

Expected output:
```
╔════════════════════════════════════════════════════════════════╗
║        Agent Marketplace - x402 Buyer Client                   ║
╚════════════════════════════════════════════════════════════════╝

1. Creating Gateway client...
   Address: 0x...
   Chain: Arc Testnet

2. Checking balances...
   Wallet USDC:  9.000000
   Gateway:      1.000000 available

3. Discovering agent...
   Agent: DataAnalyzer-v1
   Capabilities: data-analysis, content-generation, summarization
   x402 Support: ✅ Yes

4. Checking agent reputation...
   📝 [SIMULATED] Would query AgentReputation.vy on-chain

5. Checking x402 support...
   ✅ Server supports Gateway batching

6. Paying for /api/analyze ($0.01)...
   ✅ Paid 0.010000 USDC (gasless!)
   Transaction: 0x...

   Response from agent:
   - Summary: Analysis complete. Key findings indicate positive trends.
   - Confidence: 87%
   - Insights: 3 found

7. Submitting reputation feedback...
   ✅ Feedback submitted

8. Updated balances...
   Gateway: 0.990000 available

╔════════════════════════════════════════════════════════════════╗
║                        Complete!                               ║
╚════════════════════════════════════════════════════════════════╝
```

## Testing Without a Client

Test the free endpoints:
```bash
# Agent info
curl http://localhost:4021/ | jq .

# Health check
curl http://localhost:4021/health | jq .
```

Test the paywall (should return 402):
```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:4021/api/analyze
# Expected: HTTP 402
```

## What's Real vs. Simulated

| Feature | Status | Notes |
|---------|--------|-------|
| x402 Payment Negotiation | ✅ Real | HTTP 402 → sign → retry with Payment-Signature |
| Gasless USDC Transfer | ✅ Real | No gas fees for payments |
| Gateway Balance | ✅ Real | On-chain balance in Gateway contract |
| Agent Discovery | 📝 Simulated | Would read from AgentIdentity.vy on-chain |
| Reputation Query | 📝 Simulated | Would read from AgentReputation.vy on-chain |
| Feedback Submission | 📝 Simulated | Would write to AgentReputation.vy on-chain |

## Connecting to On-Chain Contracts

To make this fully on-chain, you would:

1. **Deploy AgentIdentity.vy** to Arc Testnet
2. **Register the agent** with `registerAgent(tokenURI)`
3. **Read agent info** from `tokenURI(agentId)` instead of hardcoded metadata
4. **Deploy AgentReputation.vy** linked to AgentIdentity
5. **Record interactions** with `recordInteraction(agentId, clientAddress)`
6. **Submit feedback** with `submitFeedback(agentId, score, comment, proofOfPayment)`

See `scripts/deploy.ts` for deployment instructions.

## Extending This Example

Ideas for hackathon projects:

- **Dynamic Pricing**: Use on-chain reputation to adjust prices (higher reputation = higher prices)
- **Multi-Agent Pipeline**: One agent orchestrates others, splitting payments via PaymentSplitter.vy
- **Subscription Tier**: Use SubscriptionManager.vy to offer monthly plans with x402 overage billing
- **Cross-Chain Agents**: Accept payments on any Gateway-supported chain, withdraw to any other

See [HACKATHON.md](../../HACKATHON.md) for more project ideas.
