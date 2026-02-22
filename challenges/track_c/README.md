# Track C — Advanced Challenges

Five contract primitives. Each one extends what vanilla x402 can do. Pick one or more.

The ERC-8004 Vyper reference implementation is available as a Moccasin dependency (see Track A setup). Import and extend it where relevant. Each challenge is an independent contract — you don't need to complete them in order.

Circle integration is optional in this track. If you want to wire up a Circle Programmable Wallet as the agent, use the patterns from Track B.

For each challenge, include a short section in your README explaining what your contract enforces that a purely SDK-level or application-layer approach does not.

## Challenges

| Step | Name | Contract |
|------|------|----------|
| C1 | [SpendingLimiter](c1_spending_limiter/) | `SpendingLimiter.vy` |
| C2 | [AgentEscrow with Hash-Commitment Release](c2_agent_escrow/) | `AgentEscrow.vy` |
| C3 | [SubscriptionManager with On-Chain Cancellation](c3_subscription_manager/) | `SubscriptionManager.vy` |
| C4 | [Atomic PaymentSplitter for Multi-Agent Workflows](c4_payment_splitter/) | `PaymentSplitter.vy` |
| C5 | [Payment Channel with Challenge Period](c5_payment_channel/) | `PaymentChannel.vy` |

## Style

Vyper convention is `snek_case` for all identifiers. Use it throughout.
