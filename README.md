# vyper-agentic-payments

**Vyper smart contracts for agentic payment workflows on Circle's Arc chain, integrated with Circle's x402 Batching SDK.**

[![Tests](https://img.shields.io/badge/tests-185%20passing-success)](./tests)
[![Vyper](https://img.shields.io/badge/vyper-0.4.x-blue)](https://vyperlang.org)
[![Arc Testnet](https://img.shields.io/badge/chain-Arc%20Testnet-purple)](https://developers.circle.com/w3s/arc)

> 🎉 **Complete Implementation** - 7 contracts, 185 tests, TypeScript SDK integration, and deployment scripts ready for Circle Hackathon!

This is the **first-ever Vyper implementation of ERC-8004** (Agent Identity, Reputation, and Validation registries) — a production-ready starter kit for building autonomous AI agent payment systems.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Trust (ERC-8004 - Vyper)                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │AgentIdentity │ │AgentReputation│ │AgentValidation│       │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Governance (Vyper)                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ AgentEscrow  │ │SpendingLimiter│ │PaymentSplitter│       │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌────────────────────┐                                     │
│  │SubscriptionManager │                                     │
│  └────────────────────┘                                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Payment (x402 Batching SDK)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ GatewayClient → deposit() → pay() → gasless USDC txs  │  │
│  └───────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Settlement (Circle Gateway)                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 0: Chain (Arc Testnet - Chain ID: 5042002)           │
│  USDC: 0x3600000000000000000000000000000000000000            │
└─────────────────────────────────────────────────────────────┘
```

## 📦 What's Included

### Smart Contracts (7 total, 185 tests)

| Contract | Purpose | Tests |
|----------|---------|-------|
| `AgentIdentity.vy` | ERC-721 NFT registry for agent identities | 39 |
| `AgentReputation.vy` | On-chain reputation with proof-of-payment | 28 |
| `AgentValidation.vy` | Validator-based task verification | 20 |
| `AgentEscrow.vy` | USDC escrow for agent-to-agent tasks | 24 |
| `SpendingLimiter.vy` | Agent authorization with spending limits | 20 |
| `PaymentSplitter.vy` | Revenue distribution for multi-agent work | 27 |
| `SubscriptionManager.vy` | Recurring USDC payments | 27 |

### TypeScript Integration

| Component | Description |
|-----------|-------------|
| `scripts/compile-vyper.ts` | Compile Vyper contracts to JSON artifacts |
| `scripts/deploy-viem.ts` | Deploy contracts using viem |
| `scripts/deploy.ts` | Deploy using Circle Smart Contract Platform |
| `scripts/interact.ts` | Interact with deployed contracts |
| `scripts/setup-wallet.ts` | Setup Circle developer wallet |
| `examples/agent-marketplace/` | Full x402 paywall example |

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- Vyper 0.4.x

### Installation

```bash
# Clone the repository
git clone https://github.com/lufa23/vyper-agentic-payments.git
cd vyper-agentic-payments

# Install Node.js dependencies
npm install

# Install Python dependencies
pip install vyper titanoboa pytest
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys:
# - PRIVATE_KEY (for deployment)
# - CIRCLE_API_KEY (optional, for Circle SDK)
```

### Compile & Deploy

```bash
# Compile all Vyper contracts
npm run compile

# Deploy to Arc Testnet
npm run deploy

# Interact with contracts
npm run interact
```

### Run Tests

```bash
# Run all Python tests
npm run test

# Or run specific test file
python -m pytest tests/test_agent_identity.py -v
```

## 🌐 Agent Marketplace Example

A complete example showing x402 payment paywalls for AI agent services:

```bash
cd examples/agent-marketplace

# Start the server (seller)
npx ts-node server.ts

# In another terminal, run the client (buyer)
npx ts-node client.ts
```

**Server endpoints:**
- `GET /` - Health check (free)
- `GET /api/analyze?text=...` - Sentiment analysis ($0.01)
- `GET /api/generate?prompt=...` - Text generation ($0.05)

**How it works:**
1. Client requests paywalled endpoint → gets 402 Payment Required
2. Client pays via x402 Gateway (gasless USDC)
3. Server validates payment, returns response
4. All verifiable on-chain!

See [examples/agent-marketplace/README.md](examples/agent-marketplace/README.md) for details.

## 📝 Contract Overview

### AgentIdentity.vy (ERC-8004 Identity)

```python
# Register an agent (mints NFT to sender)
agent_id = identity.registerAgent("ipfs://QmAgentMetadata...")

# Check agent status
is_active = identity.isAgentActive(agent_id)
owner = identity.ownerOf(agent_id)
```

### AgentReputation.vy (ERC-8004 Reputation)

```python
# Record client interaction (called by agent owner)
reputation.recordInteraction(agent_id, client_address)

# Submit feedback with x402 payment proof
feedback_id = reputation.submitFeedback(agent_id, score=85, proof=tx_hash)

# Query reputation (score is scaled by 100)
avg_score = reputation.getAverageScore(agent_id)  # 8500 = 85.00
tier = reputation.getReputationTier(agent_id)  # 0-4
```

### AgentEscrow.vy (Task Payments)

```python
# Create task with USDC locked
task_id = escrow.createTask(worker_agent, amount, deadline, task_hash)

# Worker completes task
escrow.completeTask(task_id)

# Client confirms and releases payment
escrow.approveCompletion(task_id)
```

### SpendingLimiter.vy (Agent Authorization)

```python
# Authorize agent with spending limits
limiter.authorizeAgent(agent, per_tx=10*10**6, daily=100*10**6)

# Agent spends on behalf of owner
limiter.spend(owner, amount, recipient, token)
```

## 🔧 Project Structure

```
vyper-agentic-payments/
├── contracts/               # Vyper smart contracts
│   ├── interfaces/         # Interface definitions
│   ├── AgentIdentity.vy    # ERC-8004 Identity
│   ├── AgentReputation.vy  # ERC-8004 Reputation
│   ├── AgentValidation.vy  # ERC-8004 Validation
│   ├── AgentEscrow.vy      # Task escrow
│   ├── SpendingLimiter.vy  # Agent authorization
│   ├── PaymentSplitter.vy  # Revenue distribution
│   └── SubscriptionManager.vy # Recurring payments
├── scripts/                 # TypeScript deployment scripts
│   ├── compile-vyper.ts    # Compile contracts
│   ├── deploy-viem.ts      # Deploy with viem
│   ├── deploy.ts           # Deploy with Circle SDK
│   └── interact.ts         # Contract interaction
├── examples/
│   └── agent-marketplace/  # x402 paywall example
│       ├── server.ts       # Express + x402 middleware
│       ├── client.ts       # GatewayClient consumer
│       └── deposit.ts      # Gateway deposit script
├── tests/                   # Python test suite
├── artifacts/               # Compiled contract artifacts
└── deployments.json         # Deployed addresses
```

## 🌐 Arc Testnet Configuration

| Parameter | Value |
|-----------|-------|
| Chain ID | `5042002` |
| RPC | `https://rpc.testnet.arc.circle.com` |
| USDC | `0x3600000000000000000000000000000000000000` |
| Explorer | `https://explorer.testnet.arc.circle.com` |

## 📚 Resources

- [Circle Arc Documentation](https://developers.circle.com/w3s/arc)
- [x402 Protocol](https://www.x402.org/)
- [Vyper Documentation](https://docs.vyperlang.org/)
- [ERC-8004 Draft](https://eips.ethereum.org/EIPS/eip-8004)

## 🤝 Contributing

Contributions welcome! Check [AUDIT_REPORT.md](./AUDIT_REPORT.md) for current status and improvement areas.

## 📄 License

MIT License - see [LICENSE](./LICENSE)

---

Built for the Circle Hackathon 🚀
