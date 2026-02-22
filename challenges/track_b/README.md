# Track B — Circle Integration

A checklist-style track covering the full Circle product stack on Arc. Each step builds on the previous. The goal is to touch every relevant Circle product in sequence, ending with a live x402 payment on-chain using [`circlekit`](https://github.com/lufa23/circle-titanoboa-sdk).

You will need a Circle developer account. The free tier is sufficient for all steps.

## Steps

| Step | Name | Type |
|------|------|------|
| B1 | [Get a Circle API key](b1_api_key/) | Instructions only |
| B2 | [Provision a Circle Programmable Wallet](b2_programmable_wallet/) | Instructions only |
| B3 | [Deploy a Vyper contract from your Circle Wallet](b3_deploy_from_wallet/) | Runnable script |
| B4 | [Make an x402 payment on-chain](b4_x402_payment/) | Runnable script |

## Prerequisites

- A funded wallet on Arc testnet (complete Track A1 first)
- A [Circle Developer Console](https://console.circle.com) account (free tier)
- The `circlekit` SDK installed:

```bash
pip install -e ../circle-titanoboa-sdk
```

## Environment Variables

B3 and B4 require these environment variables:

```bash
export CIRCLE_API_KEY="your-api-key-from-b1"
export CIRCLE_ENTITY_SECRET="your-entity-secret"
```
