# Challenges

This repo is the Vyper track for Circle's hackathon on Arc. Three tracks: a Vyper onboarding track, a Circle product integration track, and an advanced track with five contract primitives to build.

All contracts deploy to Arc testnet (Chain ID: `5042002`). USDC is the native gas token. The native USDC address is `0x3600000000000000000000000000000000000000`.

> **Decimal note:** Arc's native USDC balance uses 18 decimals. The ERC-20 interface uses 6. Do not mix these.

---

## Track A: Vyper on Arc

A step-by-step introduction to writing, deploying, and interacting with Vyper contracts on Arc. No Circle SDK required here, just Vyper, Moccasin, and the chain.

This track uses [Moccasin](https://cyfrin.github.io/moccasin/) as the project framework. Add the ERC-8004 reference implementation and the Circle SDK as dependencies in `moccasin.toml`:

```toml
[dependencies]
erc-8004-vyper = { git = "https://github.com/lufa23/erc-8004-vyper" }
circle-titanoboa-sdk = { git = "https://github.com/lufa23/circle-titanoboa-sdk" }
```

**Style note:** Vyper convention is `snek_case` for all identifiers. Use it throughout.

---

### A1. Environment setup

- Install Moccasin and Vyper
- Configure Arc testnet in `moccasin.toml`
- Fund a wallet from the [Arc testnet faucet](https://faucet.circle.com) (20 USDC per 2 hours per address)
- Verify your balance on the [Arc block explorer](https://explorer.arc.network)

**Checkpoint:** Your wallet has a non-zero USDC balance on Arc.

---

### A2. Deploy your first Vyper contract

Write and deploy a minimal Vyper contract to Arc testnet. The contract should:

- Accept a USDC deposit from a caller
- Store the depositor's address and amount
- Allow only the depositor to withdraw their balance

**Checkpoint:** A deployed contract address on Arc. A deposit and withdrawal transaction visible on the block explorer.

---

### A3. Write a test suite

Using Titanoboa or Moccasin's testing utilities, write a test suite for your A2 contract covering:

- Successful deposit and withdrawal
- Withdrawal by a non-depositor reverts
- Correct balance accounting after multiple deposits

**Checkpoint:** A passing test suite in your repo.

---

### A4. Register your contract as an ERC-8004 agent

[ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) defines a standard for on-chain agent identity and reputation. The `erc-8004-vyper` repo provides a Vyper reference implementation with three contracts: `IdentityRegistry`, `ReputationRegistry`, and `ValidationRegistry`.

Using the `IdentityRegistry` from the dependency you added in the setup step:

- Deploy an instance of `IdentityRegistry` (or use a shared testnet deployment if one is provided)
- Call `register` to register the contract you deployed in A2 as an agent, including a metadata URI pointing to a JSON file describing what it does
- Verify the registration by calling `ownerOf` with the returned token ID

This is the same pattern Track C contracts will follow. Registering contract instances as agents gives them a verifiable on-chain identity that other contracts and off-chain tooling can resolve.

**Checkpoint:** A transaction on the block explorer showing your contract registered in the `IdentityRegistry`. The token ID and metadata URI visible on-chain.

---

## Track B: Circle Integration

A checklist-style track covering the full Circle product stack on Arc. Each step builds on the previous. The goal is to touch every relevant Circle product in sequence, ending with a live x402 payment on-chain using `circle-titanoboa-sdk` ([`circlekit`](https://github.com/lufa23/circle-titanoboa-sdk)).

You will need a Circle developer account. The free tier is sufficient for all steps.

---

### B1. Get a Circle API key

- Create an account on the [Circle Developer Console](https://console.circle.com)
- Generate an API key
- Confirm access to the Arc testnet environment

**Checkpoint:** A working API key in the Circle Developer Console.

---

### B2. Provision a Circle Programmable Wallet

- Create a Developer-Controlled Wallet on Arc testnet via the Console or the Circle API
- Fund it from your Track A faucet wallet
- Confirm the balance in the Console and on the [Arc block explorer](https://explorer.arc.network)

**Checkpoint:** A Circle Programmable Wallet with a USDC balance, visible in both the Console and the explorer.

---

### B3. Deploy a Vyper contract from your Circle Wallet

Use `circlekit`'s `CircleWalletSigner` and `CircleTxExecutor` to sign and broadcast the deployment from your Developer-Controlled Wallet. Set `CIRCLE_API_KEY` and `CIRCLE_ENTITY_SECRET` in your environment.

```python
from circlekit import GatewayClient
from circlekit.wallets import CircleWalletSigner, CircleTxExecutor
import boa

signer = CircleWalletSigner(wallet_id="...", wallet_address="0x...")
tx_executor = CircleTxExecutor(wallet_id="...", wallet_address="0x...")

client = GatewayClient(chain="arcTestnet", signer=signer, tx_executor=tx_executor)

boa.set_network_env("https://arc-testnet.drpc.org")
contract = boa.load("contracts/Vault.vy")  # your A2 contract
```

- Deploy the contract from A2 with your Circle Wallet as the deployer
- Confirm the deployment transaction on the block explorer

**Checkpoint:** A deployed contract whose deployer address matches your Circle Wallet.

---

### B4. Make an x402 payment on-chain

Set up a local x402-protected endpoint using `circlekit`'s server middleware, then pay it from your Circle Wallet using `GatewayClient`.

**Server side**: protect an endpoint with `create_gateway_middleware`:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from circlekit import create_gateway_middleware

app = FastAPI()
gateway = create_gateway_middleware(
    seller_address="0xYourCircleWalletAddress",
    chain="arcTestnet",
)

@app.get("/api/data")
async def data(request: Request):
    result = await gateway.process_request(
        payment_header=request.headers.get("PAYMENT-SIGNATURE"),
        path=request.url.path,
        price="$0.01",
    )
    if isinstance(result, dict):
        resp = JSONResponse(result["body"], status_code=result["status"])
        for k, v in result.get("headers", {}).items():
            resp.headers[k] = v
        return resp
    resp = JSONResponse({"data": "protected content", "paid_by": result.payer})
    for k, v in result.response_headers.items():
        resp.headers[k] = v
    return resp
```

**Client side**: pay from your Circle Wallet:

```python
import asyncio
from circlekit import GatewayClient
from circlekit.wallets import CircleWalletSigner

signer = CircleWalletSigner(wallet_id="...", wallet_address="0x...")
client = GatewayClient(chain="arcTestnet", signer=signer)

async def main():
    result = await client.pay("http://localhost:8000/api/data")
    print(f"Got: {result.data}")
    print(f"Paid: {result.formatted_amount} USDC")
    await client.close()

asyncio.run(main())
```

**Checkpoint:** An on-chain x402 payment transaction initiated from your Circle Wallet, confirmed on the Arc block explorer.

---

## Track C: Advanced Challenges

Five contract primitives. Each one extends what vanilla x402 can do. Pick one or more.

The ERC-8004 Vyper reference implementation is available as a Moccasin dependency (see Track A setup). Import and extend it where relevant. Each challenge is an independent contract; you don't need to complete them in order.

Circle integration is optional in this track. If you want to wire up a Circle Programmable Wallet as the agent, use the patterns from Track B.

For each challenge, include a short section in your README explaining what your contract enforces that a purely SDK-level or application-layer approach does not.

---

### C1. SpendingLimiter

**What to build:**

A Vyper contract that sits between an agent wallet and its USDC. It enforces:

- A rolling 24-hour budget
- A per-recipient cap
- An allowlist of recipient addresses

All three on every outgoing transfer, at the contract layer. If the daily cap is hit, outgoing transfers halt until the owner co-signs a resumption. The agent cannot unilaterally resume.

Key functions: `authorize_spend(recipient, amount)`, `set_limit(agent, amount, window)`, `emergency_pause(agent)`, `resume(agent)`.

One design decision to document: what happens when an agent is at 49.9 USDC of a 50 USDC daily cap and tries to transfer 1.5 USDC? Full revert, or partial fill? Either is defensible. Document your choice.

**What this enables beyond vanilla x402:**

x402 enforces payment at the protocol layer but has no opinion on how much an agent is allowed to spend. That enforcement lives in application code today: a runtime setting, an SDK config, a server-side check. A SpendingLimiter moves that constraint on-chain, independent of whatever the agent code does or whatever state the runtime is in.

**Product directions:**

- Corporate expense controls for autonomous agents with per-department budgets
- Consumer agent products where a user sets weekly spending limits
- Treasury management for multi-agent systems where individual agents draw from a shared pool with hard caps

---

### C2. AgentEscrow with Hash-Commitment Release

**What to build:**

A Vyper escrow factory. Each job gets its own contract instance deployed via the factory. The job contract:

- Holds a payer's USDC deposit against a `bytes32` hash of the agreed output specification
- Accepts a `bytes32` delivery hash from the provider
- Releases funds to the provider when a designated verifier confirms the match
- Returns funds to the payer (minus a small non-refundable work fee) on rejection
- Returns funds to the payer in full if the verifier takes no action within N blocks

Key functions: `deposit(job_id, payee, amount, spec_hash)`, `submit_delivery(job_id, delivery_hash)`, `confirm_release(job_id)`, `challenge(job_id)`, `force_release(job_id)`, `arbiter_resolve(job_id, release)`.

The verifier can be a multisig, an oracle, or a second AI agent. The contract enforces only that funds cannot move without the verification step completing or the timeout expiring.

**What this enables beyond vanilla x402:**

x402 settles payment on delivery of an HTTP response. It has no mechanism to verify the quality or correctness of what was delivered. This contract holds payment in escrow until a verification step completes. The trust problem moves from "did the server respond?" to "did the server deliver what was agreed?"

**Product directions:**

- Bounty boards where agents post tasks, other agents complete them, and a verifier adjudicates
- Data labeling pipelines with payment gated on quality checks
- Multi-step agent workflows where each step's output is an input to the next, and payment for each step is conditional on the next step accepting it

---

### C3. SubscriptionManager with On-Chain Cancellation

**What to build:**

A Vyper subscription contract where:

- Subscriber calls `subscribe(provider, amount_per_period, period)` and pre-funds N intervals
- Anyone can call `settle(subscriber, provider)` once `block.timestamp >= last_settled + interval`. No trusted scheduler, no cron job, no keeper network required
- `cancel(provider)` returns `balance - pro_rata_owed` to the subscriber in the same transaction, calculated on-chain
- Provider can only `withdraw()` accrued settled intervals, never future ones
- `add_metered_charge(subscriber, units)` lets the provider bill usage above the flat rate at a per-unit price set at subscription creation

Edge cases to handle and document:

- Balance runs out mid-period: `settle` reverts, emit `InsufficientBalance`
- Subscriber tops up after a missed period: no retroactive settlement, only forward from next valid window
- Provider never calls `settle`: subscriber can cancel and recover full remaining balance

**What this enables beyond vanilla x402:**

x402 is per-call. There is no native concept of a recurring relationship, a billing period, or a refundable balance. This contract adds those: predictable revenue for providers, cancellation rights for subscribers, and metered billing for variable usage, all enforced on-chain.

**Product directions:**

- SaaS-style billing for AI APIs where agents hold subscriptions rather than paying per call
- Agent-to-agent service agreements with defined billing periods
- Data feed subscriptions where agents pay for continuous access to a stream

---

### C4. Atomic PaymentSplitter for Multi-Agent Workflows

**What to build:**

A Vyper PaymentSplitter where:

- Recipients and shares in basis points are set at deploy time (shares must sum to exactly 10000)
- `distribute(amount)` sends each recipient their proportional share atomically in one transaction
- A pull variant: `accrue(amount)` increments each recipient's claimable balance; recipients call `claim()` themselves. This avoids the failure mode where one recipient is a contract that reverts on receive
- Owner can update shares behind a timelock: `propose_split_update(new_recipients, new_shares)` queues a change for N blocks; the change cannot apply mid-session
- One event per recipient per distribution with the exact amount sent

Document explicitly where the remainder goes when `amount` does not divide evenly. Assign it to the first recipient or a treasury address. Either is fine. Ambiguity is not.

**What this enables beyond vanilla x402:**

x402 sends payment to one address. Splitting that payment across multiple recipients (a platform fee, a provider, a referrer) requires either multiple transactions or an intermediary. This contract makes multi-party splits atomic and auditable in a single on-chain transaction.

**Product directions:**

- Orchestrator agents that coordinate specialist sub-agents and distribute payment in proportion to contribution
- Royalty splits for AI-generated content across model provider, fine-tuner, and infrastructure
- Revenue sharing in multi-vendor agent marketplaces

---

### C5. Payment Channel with Challenge Period

**What to build:**

A Vyper bidirectional payment channel:

- `open_channel(payee, expiry)`: payer deposits USDC, sets expiry block
- Off-chain: payer signs incremental balance updates with a monotonic nonce. Nothing goes on-chain between open and close.
- `cooperative_close(channel_id, amount, payer_sig, payee_sig)`: both parties sign final state, channel closes immediately, funds split per final amount
- `unilateral_close(channel_id, amount, sig)`: one party submits latest signed state, challenge period begins
- `challenge(channel_id, higher_amount, higher_sig)`: counterparty submits a higher-nonce state to override during the challenge window
- `finalize(channel_id)`: callable after the challenge period expires with no valid challenge; splits funds per last accepted state
- `reclaim(channel_id)`: payer reclaims all funds if channel expires with no activity from payee

Invariants to enforce: `finalize` cannot succeed before the challenge window closes. `reclaim` cannot succeed before `expiry`. `higher_amount` in `challenge` must be strictly greater than the contested amount. Signature verification uses `ecrecover`. Validate the signer matches the expected party before accepting any state update.

**What this enables beyond vanilla x402:**

x402 generates one on-chain transaction per API call. An agent session with hundreds of calls generates hundreds of transactions. A payment channel collapses the entire session into two on-chain transactions (open and close) regardless of how many calls happened in between.

Scope this in your README: on Arc, with sub-second finality and USDC gas, channels make sense for sessions with hundreds to thousands of calls. For ten calls, per-call settlement is probably simpler and cheaper.

**Product directions:**

- Long-running agent sessions (code generation, research, multi-step workflows) where per-call settlement overhead compounds
- Agent-to-agent data streaming with continuous micropayment settlement at session end
- High-frequency inference APIs where on-chain latency per call is unacceptable

---

## Submission

- Public GitHub repo
- Vyper contracts deployable to Arc testnet (Chain ID: `5042002`)
- Test suite covering the edge cases in the challenge spec
- For Track B: a video showing a transaction executed via the Circle Developer Console and confirmed on the Arc block explorer
- For Track C: a short section in your README explaining what your contract enforces that a purely SDK-level or application-layer approach does not

---

## Resources

- [Arc documentation](https://docs.arc.network)
- [Arc testnet faucet](https://faucet.circle.com)
- [Arc block explorer](https://explorer.arc.network)
- [Circle developer docs](https://developers.circle.com)
- [Circle developer console](https://console.circle.com)
- [x402 protocol spec](https://x402.org)
- [Vyper documentation](https://docs.vyperlang.org)
- [Moccasin](https://cyfrin.github.io/moccasin/): Vyper project framework, used for dependency management and deployment
- [Titanoboa](https://github.com/vyperlang/titanoboa): Vyper interpreter, useful for local testing
- [circle-titanoboa-sdk](https://github.com/lufa23/circle-titanoboa-sdk): Python SDK for x402 with Circle Gateway, built for the Vyper ecosystem
- [erc-8004-vyper](https://github.com/lufa23/erc-8004-vyper): Vyper reference implementation of ERC-8004: Trustless Agents
- [EIP-8004 spec](https://eips.ethereum.org/EIPS/eip-8004)
