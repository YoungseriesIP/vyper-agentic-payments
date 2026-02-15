# Workshop: Building Agent Payment Systems

A hands-on guide to building autonomous AI agent payment systems using Vyper and Circle's x402 SDK.

## Prerequisites

- Python 3.10+
- Basic understanding of Ethereum/smart contracts

## Setup (10 minutes)

### 1. Clone and Install

```bash
# Clone both repositories side-by-side
git clone https://github.com/lufa23/vyper-agentic-payments.git
git clone https://github.com/lufa23/circle-titanoboa-sdk.git

cd vyper-agentic-payments

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install the project and its dependencies
pip install -e .

# Install circlekit (Python x402 SDK) from local path
pip install -e ../circle-titanoboa-sdk

# Install integration test dependencies (Flask, httpx, etc.)
pip install -e ".[integration]"
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```
PRIVATE_KEY=0x...  # Your testnet private key
```

### 3. Get Testnet USDC

1. Visit Circle's faucet
2. Request testnet USDC for Arc Testnet
3. Fund your wallet

---

## Part 1: Understanding the Contracts (20 minutes)

### AgentIdentity - The Foundation

Every agent needs an identity. Open `contracts/AgentIdentity.vy`:

```python
@external
def registerAgent(metadataURI: String[256]) -> uint256:
    """
    Register a new agent. Mints an ERC-721 NFT to the caller.

    @param metadataURI IPFS URI pointing to agent metadata
    @return agentId The unique identifier for this agent
    """
    agentId: uint256 = self.nextAgentId
    self.nextAgentId = agentId + 1

    # Mint NFT to caller
    self._mint(msg.sender, agentId)
    self.tokenURIs[agentId] = metadataURI
    self.agentActive[agentId] = True

    log AgentRegistered(agentId, msg.sender, metadataURI)
    return agentId
```

**Key concepts:**
- Agent = ERC-721 NFT
- Metadata stored on IPFS
- Owner = msg.sender

### Try it yourself:

```bash
# Run the identity tests
python -m pytest tests/test_agent_identity.py -v -k "test_register"
```

### AgentReputation - Building Trust

Agents earn reputation through feedback. Open `contracts/AgentReputation.vy`:

```python
@external
def submitFeedback(
    agentId: uint256,
    score: uint256,
    proofOfPayment: bytes32
) -> uint256:
    """
    Submit feedback for an agent. Requires prior interaction.

    @param agentId The agent to rate
    @param score Rating from 0-100
    @param proofOfPayment Transaction hash proving payment occurred
    """
    # Must have interacted with agent
    assert self.hasInteracted[agentId][msg.sender], "No interaction recorded"

    # Can only rate once
    assert not self.clientFeedbackGiven[msg.sender][agentId], "Already rated"

    # Score must be valid
    assert score <= 100, "Score must be 0-100"

    # Update reputation
    self.totalScore[agentId] += score
    self.feedbackCount[agentId] += 1
    ...
```

**Key concepts:**
- Proof-of-payment prevents fake reviews
- One feedback per client per agent
- Scores averaged over all feedback

---

## Part 2: x402 Integration (30 minutes)

### How x402 Works

```
Client                    Server                   Gateway
  │                         │                         │
  │──── GET /api/analyze ──►│                         │
  │                         │                         │
  │◄─── 402 + payment req ──│                         │
  │                         │                         │
  │───────────────────────────────── pay() ─────────►│
  │◄────────────────────────────── receipt ──────────│
  │                         │                         │
  │── GET /api/analyze ────►│                         │
  │   + payment header      │                         │
  │                         │──── verify ────────────►│
  │                         │◄─── valid ─────────────│
  │◄─── response ───────────│                         │
```

### Build Your First Paywall

Create `my_server.py`:

```python
import asyncio
import threading

from flask import Flask, jsonify, request

from circlekit import create_gateway_middleware
from circlekit.x402 import PaymentInfo

app = Flask(__name__)

gateway = create_gateway_middleware(
    seller_address="0x...",  # Set via SELLER_ADDRESS env var
    chain="arcTestnet",
)

# Background event loop for async process_request() calls
_loop = asyncio.new_event_loop()
_thread = threading.Thread(
    target=lambda: (asyncio.set_event_loop(_loop), _loop.run_forever()),
    daemon=True,
)
_thread.start()


def require_payment(price: str):
    """Flask adapter for circlekit's process_request()."""
    payment_header = request.headers.get("Payment-Signature")
    future = asyncio.run_coroutine_threadsafe(
        gateway.process_request(
            payment_header=payment_header,
            path=request.path,
            price=price,
        ),
        _loop,
    )
    result = future.result(timeout=10)
    if isinstance(result, PaymentInfo):
        return result
    return jsonify(result.get("body", result)), result.get("status", 402)


# Free endpoint
@app.route("/")
def index():
    return jsonify({"status": "ok"})


# Paywalled endpoint - $0.01 per request
@app.route("/api/hello")
def hello():
    result = require_payment("$0.01")
    if not isinstance(result, PaymentInfo):
        return result
    return jsonify({
        "message": "Hello, paying customer!",
        "paid_amount": result.amount,
    })


if __name__ == "__main__":
    app.run(port=3000)
```

### Create the Client

Create `my_client.py`:

```python
import asyncio
from circlekit import GatewayClient


async def main():
    async with GatewayClient(
        chain="arcTestnet",
        private_key="0x...",  # Set via PRIVATE_KEY env var
    ) as gateway:
        # Check balance
        balances = await gateway.get_balances()
        print("Balance:", balances.gateway.formatted_available)

        # Make paid request
        result = await gateway.pay("http://localhost:3000/api/hello")
        print("Response:", result.data)


asyncio.run(main())
```

### Run it:

```bash
# Terminal 1
python my_server.py

# Terminal 2
python my_client.py
```

---

## Part 3: Full Agent Workflow (30 minutes)

Let's build a complete agent that:
1. Registers identity
2. Offers services
3. Collects payments
4. Builds reputation

### Step 1: Deploy Contracts

```bash
# Deploy to Arc Testnet (requires funded wallet)
python scripts/deploy_boa.py
```

### Step 2: Register Your Agent

Using titanoboa to interact with the deployed contract:

```python
import boa
import json

# Load deployment info
with open("deployments.json") as f:
    deployments = json.load(f)

address = deployments["5042002"]["AgentIdentity"]["address"]

# Load the contract
identity = boa.load_partial("contracts/AgentIdentity.vy").at(address)

# Register your agent
agent_id = identity.registerAgent("ipfs://QmYourAgentMetadata...")
print(f"Agent registered with ID: {agent_id}")
```

### Step 3: Offer Services

Update your server to record interactions:

```python
@app.route("/api/analyze")
def analyze():
    result = require_payment("$0.01")
    if not isinstance(result, PaymentInfo):
        return result

    # Record interaction on-chain
    reputation.recordInteraction(agent_id, result.payer)

    # Do the work
    analysis = analyze_text(request.args.get("text", ""))

    return jsonify(analysis)
```

### Step 4: Build Reputation

After clients receive service, they can submit feedback:

```python
# Client-side
reputation.submitFeedback(
    agent_id,
    85,  # Score out of 100
    payment_tx_hash,
)
```

---

## Part 4: Advanced Patterns (20 minutes)

### Pattern 1: Agent Escrow

For larger tasks, use escrow:

```python
# Client creates task
task_id = escrow.createTask(
    workerAgentId,
    50_000000,  # 50 USDC
    task_hash,
    deadline
)

# Worker claims and completes
escrow.claimTask(task_id, myAgentId)
escrow.completeTask(task_id)

# Client approves
escrow.approveCompletion(task_id)  # Releases USDC
```

### Pattern 2: Spending Limits

Delegate spending to agents safely:

```python
# Owner authorizes agent
limiter.authorizeAgent(
    agentAddress,
    per_transaction=10_000000,  # 10 USDC
    daily_limit=100_000000,      # 100 USDC
    total_limit=1000_000000      # 1000 USDC
)

# Agent spends on behalf of owner
limiter.spend(ownerAddress, 5_000000, recipient, usdc)
```

### Pattern 3: Revenue Sharing

Split payments among collaborators:

```python
# Create splitter with shares
splitter = PaymentSplitter.deploy(
    [agent1, agent2, agent3],
    [50, 30, 20]  # 50%, 30%, 20%
)

# Revenue deposited
usdc.transfer(splitter.address, 100_000000)

# Each withdraws their share
splitter.withdraw(agent1)  # Gets 50 USDC
```

---

## Exercises

### Exercise 1: Custom Paywall Pricing
Modify the server to charge different prices based on request complexity.

### Exercise 2: Reputation-Based Pricing
Adjust prices based on agent reputation tier.

### Exercise 3: Subscription Model
Use SubscriptionManager for recurring API access.

---

## Resources

- [Full example code](../examples/agent-marketplace/)
- [Contract documentation](./contracts/)
- [x402 Protocol spec](https://www.x402.org/)
- [Circle Arc docs](https://developers.circle.com/w3s/arc)

---

## Q&A

Common questions:

**Q: How do I get testnet USDC?**
A: Use Circle's faucet or bridge from Sepolia.

**Q: Can agents interact with each other?**
A: Yes! Use AgentEscrow for agent-to-agent tasks.

**Q: How is gas handled?**
A: x402 Gateway handles gas - users only need USDC.

**Q: Is this production-ready?**
A: Contracts are tested but not audited. Use on testnet first.
