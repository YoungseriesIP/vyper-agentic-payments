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

## Data Flow

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

## Security Model

### Access Control

| Contract | Admin Functions | Agent Functions | Public Functions |
|----------|----------------|-----------------|------------------|
| AgentEscrow | resolveDispute | completeTask | createTask, approve |
| SpendingLimiter | - | spend | authorize, deposit |
| PaymentSplitter | addPayee | - | deposit, withdraw |
| SubscriptionManager | createPlan | - | subscribe, process |

### Invariants

1. **USDC Conservation** - Total deposits = Total withdrawals + locked
2. **Escrow Safety** - Funds locked until completion or dispute resolution
3. **Spending Limits** - Daily/per-tx/total limits enforced atomically

## Gas Optimization

Vyper provides significant gas savings:

| Operation | Solidity (est.) | Vyper (actual) | Savings |
|-----------|-----------------|----------------|---------|
| createTask | ~120k | ~75k | 38% |

Key optimizations:
- Packed storage slots
- Minimal dynamic arrays
- Direct mapping access
- No inheritance overhead

## Testing Strategy

```
tests/
├── conftest.py                  # Shared fixtures
├── test_agent_escrow.py         # Escrow tests
├── test_spending_limiter.py     # Limiter tests
├── test_payment_splitter.py     # Splitter tests
├── test_subscription_manager.py # Subscription tests
└── test_hackathon_challenges.py # Challenge verification tests
```

Each test file covers:
- Happy path scenarios
- Edge cases
- Revert conditions
- Access control
- Integration points
