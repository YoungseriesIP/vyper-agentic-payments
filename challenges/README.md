# Hackathon Challenges

Three tracks for Circle's hackathon on Arc. All contracts deploy to Arc testnet (Chain ID: `5042002`). USDC is the native gas token. The native USDC address is `0x3600000000000000000000000000000000000000`.

> **Decimal note:** Arc's native USDC balance uses 18 decimals. The ERC-20 interface uses 6. Do not mix these.

---

## Tracks

### Track A: Vyper on Arc

Write, deploy, and interact with Vyper contracts on Arc. No Circle SDK required, just Vyper, Moccasin, and the chain.

| Step | Name | Type |
|------|------|------|
| A1 | Environment setup | Instructions only |
| A2 | Deploy your first Vyper contract | Code challenge |
| A3 | Write a test suite | Code challenge |
| A4 | Register your contract as an ERC-8004 agent | Code challenge |

### Track B: Circle Integration

Walk through Circle's products on Arc: API key, programmable wallet, contract deployment, x402 payment. Each step builds on the previous.

| Step | Name | Type |
|------|------|------|
| B1 | Get a Circle API key | Instructions only |
| B2 | Provision a Circle Programmable Wallet | Instructions only |
| B3 | Deploy a Vyper contract from your Circle Wallet | Code challenge |
| B4 | Make an x402 payment on-chain | Code challenge |

### Track C: Advanced Challenges

Five contract primitives that extend what vanilla x402 can do. Each is an independent contract; pick one or more, complete in any order.

| Step | Name | Contract |
|------|------|----------|
| C1 | SpendingLimiter | `SpendingLimiter.vy` |
| C2 | AgentEscrow with Hash-Commitment Release | `AgentEscrow.vy` |
| C3 | SubscriptionManager with On-Chain Cancellation | `SubscriptionManager.vy` |
| C4 | Atomic PaymentSplitter for Multi-Agent Workflows | `PaymentSplitter.vy` |
| C5 | Payment Channel with Challenge Period | `PaymentChannel.vy` |

---

## Directory Layout

```
challenges/
├── README.md              ← you are here
├── track_a/
│   ├── a1_environment_setup/
│   ├── a2_first_contract/
│   ├── a3_test_suite/
│   └── a4_erc8004_agent/
├── track_b/
│   ├── b1_api_key/
│   ├── b2_programmable_wallet/
│   ├── b3_deploy_from_wallet/
│   └── b4_x402_payment/
└── track_c/
    ├── c1_spending_limiter/
    ├── c2_agent_escrow/
    ├── c3_subscription_manager/
    ├── c4_payment_splitter/
    └── c5_payment_channel/
```

Each challenge directory contains:
- `README.md`: instructions, spec, and hints
- `challenge.py`: template with `TODO` placeholders (code challenges only)

---

## Prerequisites

1. **Install Moccasin and Vyper**

   ```bash
   pip install moccasin
   ```

2. **Configure dependencies** in `moccasin.toml`:

   ```toml
   [dependencies]
   erc-8004-vyper = { git = "https://github.com/lufa23/erc-8004-vyper" }
   circle-titanoboa-sdk = { git = "https://github.com/lufa23/circle-titanoboa-sdk" }
   ```

3. **Fund a wallet** from the [Arc testnet faucet](https://faucet.circle.com) (20 USDC per 2 hours per address)

4. **Verify your balance** on the [Arc block explorer](https://explorer.arc.network)

Track B also requires a [Circle Developer Console](https://console.circle.com) account (free tier is sufficient).

---

## Running Tests

```bash
# Run all challenge tests (they FAIL until you complete the TODOs)
pytest tests/test_hackathon_challenges.py -v

# Run a specific track
pytest tests/test_hackathon_challenges.py -v -k "TrackA"
pytest tests/test_hackathon_challenges.py -v -k "TrackC"
```

---

## Style

Vyper convention is `snek_case` for all identifiers. Use it throughout.

---

## Resources

- [Arc documentation](https://docs.arc.network)
- [Arc testnet faucet](https://faucet.circle.com)
- [Arc block explorer](https://explorer.arc.network)
- [Circle developer docs](https://developers.circle.com)
- [x402 protocol spec](https://x402.org)
- [Vyper documentation](https://docs.vyperlang.org)
- [Moccasin](https://cyfrin.github.io/moccasin/): Vyper project framework
- [Titanoboa](https://github.com/vyperlang/titanoboa): Vyper interpreter for local testing
- [circle-titanoboa-sdk](https://github.com/lufa23/circle-titanoboa-sdk): Python SDK for x402 with Circle Gateway
- [erc-8004-vyper](https://github.com/lufa23/erc-8004-vyper): Vyper reference implementation of ERC-8004
- [EIP-8004 spec](https://eips.ethereum.org/EIPS/eip-8004)
