# Architecture Overview

This document describes the architecture of the vyper-agentic-payments project.

## System Layers

The system is organized into 5 distinct layers:

### Layer 0: Blockchain (Arc Testnet)

The foundation layer is Circle's Arc Testnet:

- **Chain ID**: 5042002
- **RPC**: https://rpc.testnet.arc.circle.com
- **Native USDC**: 0x3600000000000000000000000000000000000000
- **Block Explorer**: https://explorer.testnet.arc.circle.com

Arc is optimized for payments with:
- Fast finality (~2 seconds)
- Low transaction costs
- Native USDC integration

### Layer 1: Settlement (Circle Gateway)

The x402 Gateway handles payment settlement:

```
┌─────────────────────────────────────────────────────────┐
│                    Circle Gateway                        │
│                                                          │
│  deposit() ──→ Balance ──→ pay() ──→ Settlement         │
│                   ↑                        │             │
│                   │     Gasless USDC       ↓             │
│                   └─────────────────── Batched Txs      │
└─────────────────────────────────────────────────────────┘
```

Benefits:
- **Gasless payments** - Users don't need ETH
- **Batched transactions** - Lower costs
- **Instant settlement** - No waiting for confirmations

### Layer 2: Payment Protocol (x402 SDK)

The x402 Batching SDK provides payment APIs:

**Client-side (Buyer):**
```typescript
import { GatewayClient } from '@circlefin/x402-batching/client';

const gateway = new GatewayClient({
  chain: 'arcTestnet',
  privateKey: PRIVATE_KEY,
});

// Check if endpoint accepts x402
const supports = await gateway.supports(url);

// Pay and get response
const result = await gateway.pay<ResponseType>(url);
```

**Server-side (Seller):**
```typescript
import { createGatewayMiddleware } from '@circlefin/x402-batching/server';

const gateway = createGatewayMiddleware({
  sellerAddress: SELLER_WALLET,
});

// Paywall an endpoint
app.get('/api/analyze', 
  gateway.require('$0.01'), 
  handleAnalyze
);
```

### Layer 3: Governance (Vyper Contracts)

The governance layer handles:

#### AgentEscrow
Task-based payments with escrow:
```
Client ──→ createTask(amount, deadline) ──→ USDC locked
                    │
Worker ──→ claimTask() ──→ completeTask()
                    │
Client ──→ approveCompletion() ──→ USDC released to worker
                    │
         OR dispute() ──→ Admin resolution
```

#### SpendingLimiter
Authorization with limits:
```
Owner ──→ authorizeAgent(limits) ──→ Agent can spend
                    │
Agent ──→ spend(amount) ──→ Limits enforced
                    │
              Daily reset at midnight UTC
```

#### PaymentSplitter
Revenue distribution:
```
Payment ──→ deposit() ──→ Proportional allocation
                    │
Payee 1 ──→ withdraw() ──→ Their share
Payee 2 ──→ withdraw() ──→ Their share
```

#### SubscriptionManager
Recurring payments:
```
Subscriber ──→ subscribe(plan) ──→ First payment
                    │
              (time passes)
                    │
Anyone ──→ processPayment() ──→ Next payment if due
```

### Layer 4: Trust (ERC-8004 Contracts)

The trust layer establishes agent identity and reputation:

#### AgentIdentity (ERC-721)
```
Developer ──→ registerAgent(metadata) ──→ NFT minted
                    │
              agentId = tokenId
                    │
              Transferable ownership
```

#### AgentReputation
```
Agent ──→ recordInteraction(client) ──→ Interaction logged
                    │
Client ──→ submitFeedback(score, proof) ──→ Reputation updated
                    │
              Average score calculated
              Tier assigned (Bronze → Platinum)
```

#### AgentValidation
```
Admin ──→ addValidator(address) ──→ Trusted validator
                    │
Validator ──→ validateTask(taskId, success) ──→ Validation recorded
                    │
              Can trigger escrow release
```

## Data Flow

### Payment Flow

```
1. Client discovers agent via AgentIdentity
2. Client checks reputation via AgentReputation
3. Client creates task via AgentEscrow (USDC locked)
4. Agent completes work off-chain
5. Client approves, USDC released
6. Client submits feedback with payment proof
7. Agent reputation updated
```

### x402 Payment Flow

```
1. Client requests /api/analyze
2. Server returns 402 + x402 payment details
3. Client calls gateway.pay(url)
4. Gateway batches payment to seller
5. Server validates payment header
6. Server returns response
7. Client receives result + payment receipt
```

## Contract Interactions

```
┌─────────────────┐     queries      ┌──────────────────┐
│ AgentReputation │◄────────────────│ External Clients │
└────────┬────────┘                  └────────┬─────────┘
         │                                    │
         │ checks                             │ uses
         ▼                                    ▼
┌─────────────────┐     validates    ┌──────────────────┐
│  AgentIdentity  │◄────────────────│   AgentEscrow    │
└─────────────────┘                  └──────────────────┘
         ▲                                    │
         │                                    │
         │ references                         │ can trigger
         │                                    ▼
┌─────────────────┐                  ┌──────────────────┐
│ AgentValidation │─────────────────►│  PaymentSplitter │
└─────────────────┘     splits to    └──────────────────┘
```

## Security Model

### Access Control

| Contract | Admin Functions | Agent Functions | Public Functions |
|----------|----------------|-----------------|------------------|
| AgentIdentity | pause, updateURI | register | view |
| AgentReputation | updateRegistry | recordInteraction | submitFeedback |
| AgentEscrow | resolveDispute | completeTask | createTask, approve |
| SpendingLimiter | - | spend | authorize, deposit |
| PaymentSplitter | addPayee | - | deposit, withdraw |
| SubscriptionManager | createPlan | - | subscribe, process |

### Invariants

1. **USDC Conservation** - Total deposits = Total withdrawals + locked
2. **One Feedback Per Client** - Client can only rate agent once
3. **Escrow Safety** - Funds locked until completion or dispute resolution
4. **Spending Limits** - Daily/per-tx/total limits enforced atomically

## Gas Optimization

Vyper provides significant gas savings:

| Operation | Solidity (est.) | Vyper (actual) | Savings |
|-----------|-----------------|----------------|---------|
| registerAgent | ~150k | ~95k | 37% |
| submitFeedback | ~80k | ~55k | 31% |
| createTask | ~120k | ~75k | 38% |

Key optimizations:
- Packed storage slots
- Minimal dynamic arrays
- Direct mapping access
- No inheritance overhead

## Testing Strategy

```
tests/
├── conftest.py              # Shared fixtures
├── test_agent_identity.py   # Identity tests (39)
├── test_agent_reputation.py # Reputation tests (28)
├── test_agent_validation.py # Validation tests (20)
├── test_agent_escrow.py     # Escrow tests (24)
├── test_spending_limiter.py # Limiter tests (20)
├── test_payment_splitter.py # Splitter tests (27)
├── test_subscription_manager.py # Subscription tests (27)
└── test_integration_escrow_reputation.py # Integration (4)
```

Each test file covers:
- Happy path scenarios
- Edge cases
- Revert conditions
- Access control
- Integration points
