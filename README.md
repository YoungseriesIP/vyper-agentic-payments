<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="vyper-logo-dark.png">
    <img src="vyper-logo.png" width="140" alt="Vyper logo">
  </picture>
</p>

# vyper-agentic-payments

Vyper smart contracts and hackathon challenges for agentic payment workflows on Circle's Arc chain.

[![Vyper](https://img.shields.io/badge/vyper-0.4.x-blue)](https://vyperlang.org)
[![Arc Testnet](https://img.shields.io/badge/chain-Arc%20Testnet-purple)](https://developers.circle.com/w3s/arc)

## Tracks

| Track | Focus | Needs Circle account? |
|-------|-------|-----------------------|
| **A** | Vyper basics: write, test, deploy a vault | No |
| **B** | Circle integration: API key, programmable wallet, x402 payment | Yes |
| **C** | Advanced payment primitives: escrow, limits, splits, subscriptions | Optional |

## Quick Start

```bash
git clone https://github.com/lufa23/vyper-agentic-payments.git
git clone https://github.com/lufa23/circle-titanoboa-sdk.git

cd vyper-agentic-payments
python -m venv .venv && source .venv/bin/activate

pip install -e .
pip install -e ../circle-titanoboa-sdk
```

Run tests:

```bash
pytest tests/ -q
```

Start here: `challenges/track_a/`

## Track A: Vyper Basics

Install the toolchain, write a USDC vault contract, build a test suite, and register an ERC-8004 agent identity on Arc Testnet. The identity registry is already deployed; you just call it.

No Circle account needed. A1-A3 run locally in titanoboa; A4 deploys to Arc Testnet.

| Challenge | What you do |
|-----------|-------------|
| A1 | Environment setup |
| A2 | Write your first contract (`Vault.vy`) |
| A3 | Build a test suite |
| A4 | Register an ERC-8004 agent on Arc |

Entry point: [challenges/track_a/README.md](challenges/track_a/README.md)

## Track B: Circle Integration

Connect to Circle's infrastructure: get an API key, provision a programmable wallet, deploy a contract from it, and make an x402 payment on-chain.

You need all of these before B3/B4 will work:

1. Complete Track A first (you need a funded Arc testnet wallet)
2. Create a free Circle developer account at <https://console.circle.com>
3. From the Console: generate a `CIRCLE_API_KEY` and `CIRCLE_ENTITY_SECRET`
4. Copy `.env.example` to `.env` and fill in both values

Steps are sequential. Do them in order:

| Challenge | What you do |
|-----------|-------------|
| B1 | Get your Circle API key |
| B2 | Provision a programmable wallet |
| B3 | Deploy a contract from your Circle wallet |
| B4 | Make an x402 payment on-chain |

Entry point: [challenges/track_b/README.md](challenges/track_b/README.md)

## Track C: Advanced Payment Primitives

Four payment contracts with working scaffolds. Each challenge gives you a starting-point contract and a spec to extend. Circle integration is optional.

| Contract | Scaffold provides | Challenge: extend it with |
|----------|-------------------|---------------------------|
| `SpendingLimiter.vy` | Per-tx, daily, total limits | Per-recipient caps, allowlist, `emergency_pause`, `resume` |
| `AgentEscrow.vy` | Task creation, claiming, approval, disputes | Hash-commitment verification, challenge period, arbiter resolution |
| `SubscriptionManager.vy` | Plan creation, subscribe, charge, cancel | Pro-rata refund on cancel, price-lock at subscribe time, metered billing |
| `PaymentSplitter.vy` | Pool factory with pull-based claims | Atomic push distribution, timelock on share updates |

| Challenge | Contract |
|-----------|----------|
| C1 | `SpendingLimiter.vy` |
| C2 | `AgentEscrow.vy` |
| C3 | `SubscriptionManager.vy` |
| C4 | `PaymentSplitter.vy` |
| C5 | Payment channel (bonus) |

The scaffold contracts have known issues by design; finding and fixing them is part of the challenge.

Entry point: [challenges/track_c/README.md](challenges/track_c/README.md)

## Arc Testnet

| Parameter | Value |
|-----------|-------|
| Chain ID | `5042002` |
| RPC | `https://rpc.testnet.arc.circle.com` |
| USDC | `0x3600000000000000000000000000000000000000` |
| Explorer | <https://explorer.testnet.arc.circle.com> |
| Faucet | <https://faucet.circle.com> |

## Project Structure

```
vyper-agentic-payments/
├── contracts/
│   ├── Vault.vy                  # Track A: USDC vault
│   ├── AgentEscrow.vy            # Track C: task escrow
│   ├── SpendingLimiter.vy        # Track C: agent spend limits
│   ├── PaymentSplitter.vy        # Track C: revenue distribution
│   ├── SubscriptionManager.vy    # Track C: recurring payments
│   └── interfaces/
│       ├── IERC20.vy
│       ├── IERC721.vy
│       └── IERC721Receiver.vy
├── challenges/
│   ├── track_a/                  # A1-A4: Vyper basics
│   ├── track_b/                  # B1-B4: Circle integration
│   └── track_c/                  # C1-C5: Payment primitives
├── tests/
│   ├── conftest.py
│   ├── test_agent_escrow.py
│   ├── test_spending_limiter.py
│   ├── test_subscription_manager.py
│   ├── test_payment_splitter.py
│   ├── test_hackathon_challenges.py
│   └── test_sdk_contract_integration.py
├── examples/
│   └── agent-marketplace/
│       ├── server.py             # FastAPI server with x402 paywall
│       ├── client.py             # GatewayClient buyer agent
│       └── deposit.py            # Deposit USDC into Gateway
├── scripts/
│   ├── deploy_boa.py             # Deploy to Arc Testnet via titanoboa
│   └── interact_boa.py           # Interact with deployed contracts
├── lib/                          # ERC-8004 external dependency (git submodule)
├── moccasin.toml
└── pyproject.toml
```

## Resources

- [Circle Arc docs](https://developers.circle.com/w3s/arc)
- [x402 protocol](https://www.x402.org/)
- [Vyper docs](https://docs.vyperlang.org/)
- [ERC-8004 spec](https://eips.ethereum.org/EIPS/eip-8004)
- [circlekit SDK](https://github.com/lufa23/circle-titanoboa-sdk)
- [Moccasin](https://cyfrin.github.io/moccasin/)

## License

MIT - see [LICENSE](./LICENSE)

---

*This is an unaudited reference implementation provided for educational and development purposes only. It is not production-ready software. Use at your own risk. The authors accept no liability for any losses or damages arising from its use or deployment.*
