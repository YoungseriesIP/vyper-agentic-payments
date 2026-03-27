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

## How These Repos Relate

[erc-8004-vyper](https://github.com/lufa23/erc-8004-vyper) implements agent identity: ERC-721 NFTs, on-chain reputation, and validation logic. 

[circle-titanoboa-sdk](https://github.com/lufa23/circle-titanoboa-sdk) (circlekit) handles gasless USDC payments and x402 integration. 

This repo provides payment contracts and hackathon challenges that build on both.

## Tracks

| Track | Focus | Circle developer account? |
|-------|-------|-----------------------|
| **A** | Vyper basics: write, test, deploy a USDC vault on Arc | No (uses Arc Testnet + USDC faucet) |
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

1. Complete Track A first (you need a funded Arc Testnet wallet)
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

## Supported Networks

All networks below are supported by circle-titanoboa-sdk V2.

### Testnets

| Network | Chain ID | RPC | USDC Address |
|---------|----------|-----|--------------|
| Arc Testnet | `5042002` | [See providers](https://docs.arc.network/arc/tools/node-providers) | `0x3600000000000000000000000000000000000000` |
| Base Sepolia | `84532` | `https://sepolia.base.org` | `0x036CbD53842c5426634e7929541eC2318f3dCF7e` |
| Ethereum Sepolia | `11155111` | `https://sepolia.drpc.org` | `0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238` |
| Avalanche Fuji | `43113` | `https://api.avax-test.network/ext/bc/C/rpc` | `0x5425890298aed601595a70AB815c96711a31Bc65` |
| HyperEVM Testnet | `998` | `https://rpc.hyperliquid-testnet.xyz/evm` | `0x2B3370eE501B4a559b57D449569354196457D8Ab` |
| Sonic Testnet | `14601` | `https://rpc.testnet.soniclabs.com` | `0x0BA304580ee7c9a980CF72e55f5Ed2E9fd30Bc51` |
| World Chain Sepolia | `4801` | `https://worldchain-sepolia.g.alchemy.com/public` | `0x66145f38cBAC35Ca6F1Dfb4914dF98F1614aeA88` |
| Sei Atlantic Testnet | `1328` | `https://evm-rpc-testnet.sei-apis.com` | `0x4fCF1784B31630811181f670Aea7A7bEF803eaED` |
| Arbitrum Sepolia | `421614` | `https://sepolia-rollup.arbitrum.io/rpc` | `0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d` |
| Optimism Sepolia | `11155420` | `https://sepolia.optimism.io` | `0x5fd84259d66Cd46123540766Be93DFE6D43130D7` |
| Polygon Amoy | `80002` | `https://rpc-amoy.polygon.technology` | `0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582` |
| Unichain Sepolia | `1301` | `https://sepolia.unichain.org` | `0x31d0220469e10c4E71834a79b1f276d740d3768F` |

### Mainnets

| Network | Chain ID | RPC | USDC Address |
|---------|----------|-----|--------------|
| Ethereum | `1` | `https://eth.drpc.org` | `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` |
| Base | `8453` | `https://mainnet.base.org` | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| Arbitrum One | `42161` | `https://arb1.arbitrum.io/rpc` | `0xaf88d065e77c8cC2239327C5EDb3A432268e5831` |
| Polygon | `137` | `https://polygon.drpc.org` | `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359` |
| Optimism | `10` | `https://mainnet.optimism.io` | `0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85` |
| Avalanche C-Chain | `43114` | `https://api.avax.network/ext/bc/C/rpc` | `0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E` |
| Sonic | `146` | `https://rpc.soniclabs.com` | `0x29219dd400f2Bf60E5a23d13Be72B486D4038894` |
| Unichain | `130` | `https://mainnet.unichain.org` | `0x078D782b760474a361dDA0AF3839290b0EF57AD6` |
| World Chain | `480` | `https://worldchain-mainnet.g.alchemy.com/public` | `0x79A02482A880bCe3F13E09da970dC34dB4cD24D1` |
| HyperEVM | `999` | `https://rpc.hyperliquid.xyz/evm` | `0xb88339CB7199b77E23DB6E890353E22632Ba630f` |
| Sei | `1329` | `https://evm-rpc.sei-apis.com` | `0xe15fC38F6D8c56aF07bbCBe3BAf5708A2Bf42392` |

Faucet: <https://faucet.circle.com>

## Project Structure

```
vyper-agentic-payments/
├── contracts/
│   ├── Vault.vy                  # Track A: USDC vault
│   ├── AgentEscrow.vy            # Track C: task escrow
│   ├── SpendingLimiter.vy        # Track C: agent spend limits
│   ├── PaymentSplitter.vy        # Track C: revenue distribution
│   ├── SubscriptionManager.vy    # Track C: recurring payments
│   ├── PaymentChannel.vy         # Track C: payment channel (bonus)
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
