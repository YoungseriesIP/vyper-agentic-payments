# Track A — Vyper on Arc

A step-by-step introduction to writing, deploying, and interacting with Vyper contracts on Arc. No Circle SDK required — just Vyper, Moccasin, and the chain.

## Steps

| Step | Name | What You Do |
|------|------|-------------|
| A1 | [Environment setup](a1_environment_setup/) | Install Moccasin, configure Arc testnet, fund a wallet |
| A2 | [Deploy your first Vyper contract](a2_first_contract/) | Write and deploy a USDC vault to Arc |
| A3 | [Write a test suite](a3_test_suite/) | Test the vault contract with Titanoboa |
| A4 | [Register as an ERC-8004 agent](a4_erc8004_agent/) | Register your contract in the IdentityRegistry |

## Setup

Install [Moccasin](https://cyfrin.github.io/moccasin/) and Vyper:

```bash
pip install moccasin
```

Add the ERC-8004 reference implementation and Circle SDK as dependencies in `moccasin.toml`:

```toml
[dependencies]
erc-8004-vyper = { git = "https://github.com/lufa23/erc-8004-vyper" }
circle-titanoboa-sdk = { git = "https://github.com/lufa23/circle-titanoboa-sdk" }
```

## Style

Vyper convention is `snek_case` for all identifiers. Use it throughout.
