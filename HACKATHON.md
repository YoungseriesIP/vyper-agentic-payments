# Circle Hackathon Submission

## vyper-agentic-payments

**The first-ever Vyper implementation of ERC-8004 for autonomous AI agent payments.**

---

## Project Overview

This project provides a complete smart contract infrastructure for AI agents to:
- **Process payments** via Circle's x402 Batching SDK
- **Manage complex workflows** with escrow, subscriptions, and spending limits

### Why Vyper?

1. **Security by design** - Vyper's simplicity reduces attack surface
2. **Gas efficiency** - Optimized for frequent micropayments
3. **Readability** - Python-like syntax for rapid development
4. **Circle compatibility** - Works seamlessly with Arc chain

---

## Technical Highlights

### Contracts Delivered

| Contract | Lines | Functions | Tests |
|----------|-------|-----------|-------|
| AgentEscrow | 245 | 12 | 24 |
| SpendingLimiter | 198 | 11 | 20 |
| PaymentSplitter | 267 | 15 | 27 |
| SubscriptionManager | 312 | 16 | 27 |

### x402 Integration

The project includes a complete Python integration with Circle's x402 Batching SDK via [circlekit](https://github.com/lufa23/circle-titanoboa-sdk):

```python
# Server-side paywall (Flask + circlekit)
gateway = create_gateway_middleware(seller_address=SELLER, chain="arcTestnet")

@app.route("/api/analyze")
def analyze():
    result = require_payment("$0.01")
    if not isinstance(result, PaymentInfo):
        return result
    return jsonify({"data": "analysis result", "paid_by": result.payer})

# Client-side payment
async with GatewayClient(chain="arcTestnet", private_key=KEY) as client:
    result = await client.pay("http://localhost:4021/api/analyze")
```

### Deployment

```bash
# Deploy to Arc Testnet via titanoboa
python scripts/deploy_boa.py

# Deploy contracts with dependency management
```

---

## Demo Scenarios

### 1. Agent Marketplace

An AI agent sells sentiment analysis services:

1. Client discovers agent, pays $0.01 via x402
2. Agent delivers analysis
3. Gasless payment settled through Circle Gateway

### 2. Multi-Agent Collaboration

Three agents collaborate on a task:

1. Lead agent creates escrow task for $50 USDC
2. Worker agents claim subtasks
3. PaymentSplitter distributes: 60% lead, 40% workers

### 3. Agent Authorization

Enterprise deploys AI agents with spending controls:

1. Treasury authorizes agent with $100/day limit
2. Agent autonomously pays for API calls
3. SpendingLimiter enforces limits automatically
4. Enterprise maintains full visibility

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │         examples/agent-marketplace/                     │ │
│  │  server.py (Flask + x402)  <->  client.py (Gateway)    │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    SMART CONTRACT LAYER                      │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐        │
│  │ AgentEscrow │ │SpendingLimiter│ │PaymentSplitter │       │
│  │  (Tasks)    │ │  (Limits)     │ │  (Revenue)     │       │
│  └─────────────┘ └──────────────┘ └────────────────┘        │
│  ┌────────────────────┐                                      │
│  │SubscriptionManager │                                      │
│  │  (Recurring)       │                                      │
│  └────────────────────┘                                      │
├─────────────────────────────────────────────────────────────┤
│                    SETTLEMENT LAYER                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              x402 Batching SDK + Gateway                │ │
│  │  GatewayClient.pay() → batched USDC → Arc settlement   │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    INFRASTRUCTURE                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Arc Testnet (5042002) + USDC (0x360...000)            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
vyper-agentic-payments/
├── contracts/                 # Vyper smart contracts
│   ├── AgentEscrow.vy        # Task payment escrow
│   ├── SpendingLimiter.vy    # Agent spending controls
│   ├── PaymentSplitter.vy    # Revenue distribution
│   ├── SubscriptionManager.vy # Recurring payments
│   └── Vault.vy              # USDC deposit vault
├── tests/                     # Python tests
├── scripts/                   # Python tooling
│   ├── deploy_boa.py         # Deploy via titanoboa
│   └── interact_boa.py       # Contract interaction
├── examples/
│   └── agent-marketplace/    # x402 integration demo
│       ├── server.py         # Flask + x402 paywall
│       ├── client.py         # GatewayClient buyer
│       └── deposit.py        # Gateway deposit
├── challenges/                # 5 hackathon challenges
├── docs/                      # Documentation
└── README.md
```

---

## What We Learned

1. **Vyper + Circle = Perfect Match** - Gas efficiency matters for micropayments
2. **x402 SDK is Production-Ready** - Seamless integration
3. **Arc Testnet Works** - Fast finality, low fees
4. **ERC-8004 Needs Vyper** - First implementation demonstrates viability

---

## Future Roadmap

- [ ] Mainnet deployment on Arc
- [ ] Agent-to-agent direct payments
- [ ] Reputation staking for quality assurance
- [ ] Multi-chain agent identity bridging
- [ ] DAO governance for validator selection

---

## Team

**Luca Fumagalli** - Solo developer
- Vyper smart contracts
- Python SDK integration
- Testing & documentation

---

## Contact

- GitHub: [@lufa23](https://github.com/lufa23)
- Repository: [vyper-agentic-payments](https://github.com/lufa23/vyper-agentic-payments)

---

## License

MIT License - Open source, free to use and extend.

---

*Built for the Circle Hackathon*
