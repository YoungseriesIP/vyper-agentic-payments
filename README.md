# vyper-agentic-payments

**Vyper smart contracts for agentic payment workflows on Circle's Arc chain, integrated with [circlekit](https://github.com/lufa23/circle-titanoboa-sdk) (Python x402 Batching SDK).**

[![Tests](https://img.shields.io/badge/tests-185%20passing-success)](./tests)
[![Vyper](https://img.shields.io/badge/vyper-0.4.x-blue)](https://vyperlang.org)
[![Arc Testnet](https://img.shields.io/badge/chain-Arc%20Testnet-purple)](https://developers.circle.com/w3s/arc)

This is the **first-ever Vyper implementation of ERC-8004** (Agent Identity, Reputation, and Validation registries) — a production-ready starter kit for building autonomous AI agent payment systems, fully integrated with Circle's x402 payment protocol via Python.

## Architecture

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
│  Layer 2: Payment (circlekit - Python x402 SDK)             │
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

## What's Included

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

### Python SDK Integration

| Component | Description |
|-----------|-------------|
| `scripts/deploy_boa.py` | Deploy contracts to Arc Testnet using titanoboa |
| `scripts/interact_boa.py` | Interact with deployed contracts |
| `examples/agent-marketplace/server.py` | Flask server with x402 paywall |
| `examples/agent-marketplace/client.py` | GatewayClient buyer agent |
| `examples/agent-marketplace/deposit.py` | Deposit USDC into Gateway |
| `tests/test_sdk_contract_integration.py` | Integration tests: SDK + contracts |
| `challenges/` | 5 hackathon challenges with verification tests |

## Quick Start

### Prerequisites

- Python 3.10+
- Vyper 0.4.x (`pip install vyper`)
- [circlekit](https://github.com/lufa23/circle-titanoboa-sdk) (Python x402 SDK)

### Installation

```bash
# Clone both repositories side-by-side
git clone https://github.com/lufa23/vyper-agentic-payments.git
git clone https://github.com/lufa23/circle-titanoboa-sdk.git

cd vyper-agentic-payments

# Install Python dependencies
pip install vyper titanoboa pytest

# Install circlekit from the local SDK
pip install -e ../circle-titanoboa-sdk

# Install integration test dependencies
pip install flask httpx pytest-asyncio
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys:
# - PRIVATE_KEY (funded wallet for deployment)
# - SELLER_ADDRESS (receives payments)
```

### Run Tests

```bash
# Run all contract tests (185 tests)
pytest tests/ -v -m "not integration and not challenge"

# Run SDK integration tests (12 tests)
pytest tests/test_sdk_contract_integration.py -v

# Run hackathon challenge verification (20 tests, fail until completed)
pytest tests/test_hackathon_challenges.py -v
```

### Deploy to Arc Testnet

```bash
# Deploy all contracts (requires funded wallet)
python scripts/deploy_boa.py

# Interact with deployed contracts
python scripts/interact_boa.py
```

## Using with circlekit (circle-titanoboa-sdk)

This project uses [circlekit](https://github.com/lufa23/circle-titanoboa-sdk), a Python SDK for Circle's x402 payment protocol. The SDK provides:

- **`GatewayClient`** — Buyer-side: deposit USDC, pay for x402-protected resources, check balances
- **`create_gateway_middleware()`** — Seller-side: framework-agnostic payment middleware
- **`PrivateKeySigner`** — EIP-712 signing for gasless payments
- **`BoaTxExecutor`** — On-chain transaction execution via titanoboa

### Server-side (accepting payments)

The SDK's middleware is framework-agnostic. Here's the Flask adapter pattern used in this project:

```python
from circlekit import create_gateway_middleware
from circlekit.x402 import PaymentInfo

gateway = create_gateway_middleware(
    seller_address="0x...",
    chain="arcTestnet",
)

def require_payment(price: str):
    """Flask adapter for circlekit's process_request()."""
    payment_header = request.headers.get("Payment-Signature")
    result = await gateway.process_request(
        payment_header=payment_header,
        path=request.path,
        price=price,
    )
    if isinstance(result, PaymentInfo):
        return result  # Payment succeeded
    # Return 402 response
    return jsonify(result["body"]), result["status"]

@app.route("/api/analyze")
def analyze():
    result = require_payment("$0.01")
    if not isinstance(result, PaymentInfo):
        return result
    return jsonify({"paid_by": result.payer, "tx": result.transaction})
```

### Client-side (making payments)

```python
from circlekit import GatewayClient

client = GatewayClient(
    chain="arcTestnet",
    private_key="0x...",
)

# Deposit USDC into Gateway (one-time setup)
await client.deposit(amount=1.0)

# Pay for a resource (gasless!)
result = await client.pay("http://localhost:4021/api/analyze")
print(result.data)  # Server response
print(result.formatted_amount)  # "0.010000"
```

## Agent Marketplace Example

A complete example showing x402 payment paywalls for AI agent services:

```bash
# Terminal 1: Start the seller server
SELLER_ADDRESS=0x... python examples/agent-marketplace/server.py

# Terminal 2: Run the buyer client
PRIVATE_KEY=0x... python examples/agent-marketplace/client.py
```

**Server endpoints:**
- `GET /` — Agent discovery (free, ERC-8004 metadata)
- `GET /health` — Health check (free)
- `GET /api/analyze` — Data analysis ($0.01, x402 paywall)
- `POST /api/generate` — Content generation ($0.05, x402 paywall)
- `POST /feedback` — Submit reputation feedback (free)

**Payment flow:**
1. Client requests paywalled endpoint -> gets 402 Payment Required
2. Client signs payment intent via EIP-712 (gasless)
3. Gateway verifies and settles the payment
4. Server returns the resource with payment receipt headers

See [examples/agent-marketplace/README.md](examples/agent-marketplace/README.md) for details.

## Hackathon Challenges

Five progressive challenges in `challenges/` let you learn the contracts hands-on:

| Challenge | Difficulty | Contract | Task |
|-----------|-----------|----------|------|
| 1 | Easy | AgentIdentity | Register an agent (mint NFT) |
| 2 | Medium | AgentReputation | Record interaction + submit feedback |
| 3 | Medium-Hard | AgentEscrow | Create task + approve completion |
| 4 | Hard | SpendingLimiter | Set up 3-tier spending limits |
| 5 | Hard (Capstone) | circlekit + AgentReputation | Pay via x402 + record on-chain reputation |

```bash
# Run verification tests (all should fail initially)
pytest tests/test_hackathon_challenges.py -v

# Complete a challenge, then verify
pytest tests/test_hackathon_challenges.py::TestChallenge1Identity -v
```

See [challenges/README.md](challenges/README.md) for full instructions.

## Contract Overview

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
# Create task with USDC locked in escrow
task_id = escrow.createTask(poster_agent, amount, description_hash, deadline)

# Worker claims the task
escrow.claimTask(task_id, worker_agent)

# Poster approves and releases payment to worker
escrow.approveCompletion(task_id)
```

### SpendingLimiter.vy (Agent Authorization)

```python
# Authorize agent with spending limits
limiter.authorizeAgent(agent, per_tx=10*10**6, daily=100*10**6)

# Agent spends on behalf of owner
limiter.spend(owner, amount, recipient)
```

## Project Structure

```
vyper-agentic-payments/
├── contracts/                # Vyper smart contracts
│   ├── interfaces/          # Interface definitions
│   ├── AgentIdentity.vy     # ERC-8004 Identity (ERC-721)
│   ├── AgentReputation.vy   # ERC-8004 Reputation
│   ├── AgentValidation.vy   # ERC-8004 Validation
│   ├── AgentEscrow.vy       # Task escrow with USDC
│   ├── SpendingLimiter.vy   # Agent spending authorization
│   ├── PaymentSplitter.vy   # Revenue distribution
│   └── SubscriptionManager.vy  # Recurring payments
├── scripts/
│   ├── deploy_boa.py        # Deploy contracts via titanoboa
│   └── interact_boa.py      # Read/write deployed contracts
├── examples/
│   └── agent-marketplace/   # x402 paywall example
│       ├── server.py        # Flask + circlekit middleware
│       ├── client.py        # GatewayClient buyer
│       └── deposit.py       # Gateway deposit script
├── challenges/              # Hackathon challenges
│   ├── challenge_1_identity/
│   ├── challenge_2_reputation/
│   ├── challenge_3_escrow/
│   ├── challenge_4_spending/
│   └── challenge_5_x402_payment/
├── tests/                   # Python test suite
│   ├── test_agent_identity.py
│   ├── test_agent_reputation.py
│   ├── test_sdk_contract_integration.py  # SDK + contract tests
│   └── test_hackathon_challenges.py      # Challenge verification
└── docs/                    # Architecture docs
```

## Arc Testnet Configuration

| Parameter | Value |
|-----------|-------|
| Chain ID | `5042002` |
| RPC | `https://rpc.testnet.arc.circle.com` |
| USDC | `0x3600000000000000000000000000000000000000` |
| Explorer | `https://explorer.testnet.arc.circle.com` |
| Faucet | `https://faucet.circle.com` |

## Resources

- [Circle Arc Documentation](https://developers.circle.com/w3s/arc)
- [x402 Protocol](https://www.x402.org/)
- [Vyper Documentation](https://docs.vyperlang.org/)
- [ERC-8004 Draft](https://eips.ethereum.org/EIPS/eip-8004)
- [circlekit SDK](https://github.com/lufa23/circle-titanoboa-sdk)

## License

MIT License - see [LICENSE](./LICENSE)

---

Built for the Circle Hackathon
