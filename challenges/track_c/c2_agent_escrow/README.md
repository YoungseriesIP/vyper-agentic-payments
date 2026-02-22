# C2. AgentEscrow with Hash-Commitment Release

## What to Build

A Vyper escrow factory. Each job gets its own contract instance deployed via the factory. The job contract:

- Holds a payer's USDC deposit against a `bytes32` hash of the agreed output specification
- Accepts a `bytes32` delivery hash from the provider
- Releases funds to the provider when a designated verifier confirms the match
- Returns funds to the payer (minus a small non-refundable work fee) on rejection
- Returns funds to the payer in full if the verifier takes no action within N blocks

### Key Functions

- `deposit(job_id, payee, amount, spec_hash)` — payer deposits USDC and sets the agreed spec hash
- `submit_delivery(job_id, delivery_hash)` — provider submits a hash of their deliverable
- `confirm_release(job_id)` — verifier confirms the delivery matches, releasing funds to provider
- `challenge(job_id)` — verifier or payer challenges the delivery
- `force_release(job_id)` — callable after timeout expires with no verifier action; releases funds to provider
- `arbiter_resolve(job_id, release)` — arbiter makes a final decision on a challenged job

The verifier can be a multisig, an oracle, or a second AI agent. The contract enforces only that funds cannot move without the verification step completing or the timeout expiring.

## What This Enables Beyond Vanilla x402

x402 settles payment on delivery of an HTTP response. It has no mechanism to verify the quality or correctness of what was delivered. This contract holds payment in escrow until a verification step completes — the trust problem moves from "did the server respond?" to "did the server deliver what was agreed?"

## Product Directions

- Bounty boards where agents post tasks, other agents complete them, and a verifier adjudicates
- Data labeling pipelines with payment gated on quality checks
- Multi-step agent workflows where each step's output is an input to the next, and payment for each step is conditional on the next step accepting it

## Why Vyper

Escrow state machines — locked, submitted, verified, disputed, settled — must have no reachable invalid state. Vyper's lack of inheritance means there is no parent contract introducing state you did not write.

## What to Implement

Fill in `challenge.py` with functions that interact with `contracts/AgentEscrow.vy`. See the docstrings for the exact interface.

## Hints

- `spec_hash` and `delivery_hash` are `bytes32` — use `b'\x01' + b'\x00' * 31` for test values
- Use `boa.env.prank(address)` to switch between payer, provider, and verifier
- USDC uses 6 decimals (1 USDC = 1_000_000)
- Read `contracts/AgentEscrow.vy` before coding
