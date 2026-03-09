# C5. Payment Channel with Challenge Period

## What to Build

A Vyper bidirectional payment channel:

- `open_channel(payee, expiry)`: payer deposits USDC, sets expiry block
- Off-chain: payer signs incremental balance updates with a monotonic nonce. Nothing goes on-chain between open and close.
- `cooperative_close(channel_id, amount, payer_sig, payee_sig)`: both parties sign final state, channel closes immediately, funds split per final amount
- `unilateral_close(channel_id, amount, sig)`: one party submits latest signed state, challenge period begins
- `challenge(channel_id, higher_amount, higher_sig)`: counterparty submits a higher-nonce state to override during the challenge window
- `finalize(channel_id)`: callable after the challenge period expires with no valid challenge; splits funds per last accepted state
- `reclaim(channel_id)`: payer reclaims all funds if channel expires with no activity from payee

### Invariants

- `finalize` cannot succeed before the challenge window closes
- `reclaim` cannot succeed before `expiry`
- `higher_amount` in `challenge` must be strictly greater than the contested amount
- Signature verification uses `ecrecover`. Validate the signer matches the expected party before accepting any state update

### Scope

On Arc, with sub-second finality and USDC gas, channels make sense for sessions with hundreds to thousands of calls. For ten calls, per-call settlement is probably simpler and cheaper. Document this tradeoff in your README.

## What This Enables Beyond Vanilla x402

x402 generates one on-chain transaction per API call. An agent session with hundreds of calls generates hundreds of transactions. A payment channel collapses the entire session into two on-chain transactions (open and close) regardless of how many calls happened in between.

## Product Directions

- Long-running agent sessions (code generation, research, multi-step workflows) where per-call settlement overhead compounds
- Agent-to-agent data streaming with continuous micropayment settlement at session end
- High-frequency inference APIs where on-chain latency per call is unacceptable

## What to Implement

Fill in `challenge.py` with functions that interact with the payment channel contract. The `PaymentChannel.vy` contract is not yet implemented. This challenge is spec-only until the contract is written. See the docstrings for the target interface.

## Hints

- Use `boa.env.prank(address)` to set `msg.sender`
- Use `boa.env.time_travel(seconds=...)` to advance past the challenge period
- Signature payloads must include the channel ID, amount, and nonce to prevent replay
- USDC uses 6 decimals (1 USDC = 1_000_000)
