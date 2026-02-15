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

# Install Python dependencies
pip install vyper titanoboa pytest

# Install circlekit (Python x402 SDK) from local path
pip install -e ../circle-titanoboa-sdk

# Install integration test dependencies
pip install flask httpx pytest-asyncio
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

Create `my-server.ts`:

```typescript
import express from 'express';
import { createGatewayMiddleware } from '@circlefin/x402-batching/server';

const app = express();

// Create payment middleware
const gateway = createGatewayMiddleware({
  sellerAddress: process.env.SELLER_ADDRESS!,
});

// Free endpoint
app.get('/', (req, res) => {
  res.json({ status: 'ok' });
});

// Paywalled endpoint - $0.01 per request
app.get('/api/hello', 
  gateway.require('$0.01'), 
  (req, res) => {
    // req.payment contains payment details
    res.json({ 
      message: 'Hello, paying customer!',
      paidAmount: req.payment.amount,
    });
  }
);

app.listen(3000, () => {
  console.log('Server running on http://localhost:3000');
});
```

### Create the Client

Create `my-client.ts`:

```typescript
import { GatewayClient } from '@circlefin/x402-batching/client';

async function main() {
  // Initialize client
  const gateway = new GatewayClient({
    chain: 'arcTestnet',
    privateKey: process.env.PRIVATE_KEY!,
  });

  // Check balance
  const balances = await gateway.getBalances();
  console.log('Balance:', balances);

  // Make paid request
  const result = await gateway.pay<{ message: string }>(
    'http://localhost:3000/api/hello'
  );

  console.log('Response:', result);
}

main();
```

### Run it:

```bash
# Terminal 1
npx ts-node my-server.ts

# Terminal 2
npx ts-node my-client.ts
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
# Compile contracts
npm run compile

# Deploy (requires funded wallet)
npm run deploy
```

### Step 2: Register Your Agent

Create `register-agent.ts`:

```typescript
import { createPublicClient, createWalletClient, http } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { readFileSync } from 'fs';

const artifact = JSON.parse(
  readFileSync('artifacts/AgentIdentity.json', 'utf-8')
);

async function main() {
  const deployments = JSON.parse(
    readFileSync('deployments.json', 'utf-8')
  );
  
  const address = deployments['5042002']['AgentIdentity'].address;
  
  // Create clients...
  // Call registerAgent with your metadata
  
  console.log('Agent registered!');
}
```

### Step 3: Offer Services

Update your server to record interactions:

```typescript
app.get('/api/analyze',
  gateway.require('$0.01'),
  async (req, res) => {
    // Record interaction on-chain
    await recordInteraction(agentId, req.payment.payer);
    
    // Do the work
    const result = analyzeText(req.query.text);
    
    res.json(result);
  }
);
```

### Step 4: Build Reputation

After clients receive service, they can submit feedback:

```typescript
// Client-side
await submitFeedback(
  agentId,
  85, // Score out of 100
  paymentTxHash
);
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
